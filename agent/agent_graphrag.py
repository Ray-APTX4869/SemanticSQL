"""
GraphRAG 增强的 Agent 模块
使用图检索技术智能选择相关的 Schema
"""
from langchain.chat_models import init_chat_model
from langgraph.prebuilt import create_react_agent
from utils.prompt import SYSTEM_PREFIX
import yaml
from dotenv import load_dotenv
import os
from pydantic import BaseModel
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.example_selectors import SemanticSimilarityExampleSelector
from langchain_core.prompts import (
    ChatPromptTemplate,
    FewShotPromptTemplate,
    MessagesPlaceholder,
    PromptTemplate,
    SystemMessagePromptTemplate,
)
from agent.state import AgentState
from langchain_core.runnables import Runnable
import logging

logger = logging.getLogger(__name__)

# React agent 配置
class reactAgentConfig(BaseModel):
    username: str
    task_type: str = "sql_to_text" 
    verbose: bool = True
    handle_parsing_errors: bool = True
    max_iterations: int = 5

# 加载配置
with open("config.yaml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

load_dotenv()

# 初始化 LLM
llm = init_chat_model(
    model=os.getenv("model"), 
    api_key=os.getenv("api_key"), 
    base_url=os.getenv("base_url"), 
    max_tokens=config["max_tokens"]
)

# 初始化 Embeddings
embeddings = OpenAIEmbeddings(
    model="text-embedding-3-large",
    base_url=os.getenv("base_url"),
    openai_api_key=os.getenv("api_key")
)

# Few-shot Examples（与主分支保持一致）
examples = [
    {
        "input": "Database schema:\n breeds: breed_code, breed_name\n charges: charge_id, charge_type, charge_amount\n sizes: size_code, size_description\n treatment_types: treatment_type_code, treatment_type_description\n owners: owner_id, first_name, last_name, street, city, state, zip_code, email_address, home_phone, cell_number\n dogs: dog_id, owner_id, abandoned_yn, breed_code, size_code, name, age, date_of_birth, gender, weight, date_arrived, date_adopted, date_departed\n professionals: professional_id, role_code, first_name, street, city, state, zip_code, last_name, email_address, home_phone, cell_number\n treatments: treatment_id, dog_id, professional_id, treatment_type_code, date_of_treatment, cost_of_treatment\n\nUser question: List the first name of all the professionals along with the description of the treatment they have done .", 
        "query": "select distinct t1.first_name ,  t3.treatment_type_description from professionals as t1 join treatments as t2 on t1.professional_id  =  t2.professional_id join treatment_types as t3 on t2.treatment_type_code  =  t3.treatment_type_code"
    },
    {
        "input": "Database schema:\n breeds: breed_code, breed_name\n charges: charge_id, charge_type, charge_amount\n sizes: size_code, size_description\n treatment_types: treatment_type_code, treatment_type_description\n owners: owner_id, first_name, last_name, street, city, state, zip_code, email_address, home_phone, cell_number\n dogs: dog_id, owner_id, abandoned_yn, breed_code, size_code, name, age, date_of_birth, gender, weight, date_arrived, date_adopted, date_departed\n professionals: professional_id, role_code, first_name, street, city, state, zip_code, last_name, email_address, home_phone, cell_number\n treatments: treatment_id, dog_id, professional_id, treatment_type_code, date_of_treatment, cost_of_treatment\n\nUser question: Find the number of professionals who have not treated any dogs . ", 
        "query": "select count(*) from professionals where professional_id not in ( select professional_id from treatments )"
    },
    {
        "input": "Database schema:\n breeds: breed_code, breed_name\n charges: charge_id, charge_type, charge_amount\n sizes: size_code, size_description\n treatment_types: treatment_type_code, treatment_type_description\n owners: owner_id, first_name, last_name, street, city, state, zip_code, email_address, home_phone, cell_number\n dogs: dog_id, owner_id, abandoned_yn, breed_code, size_code, name, age, date_of_birth, gender, weight, date_arrived, date_adopted, date_departed\n professionals: professional_id, role_code, first_name, street, city, state, zip_code, last_name, email_address, home_phone, cell_number\n treatments: treatment_id, dog_id, professional_id, treatment_type_code, date_of_treatment, cost_of_treatment\n\nUser question: Which owners live in the state whose name contains the substring 'North ' ? List his first name , last name and email address. ", 
        "query": "select first_name ,  last_name ,  email_address from owners where state like '%north%'"
    },
    {
        "input": "Database schema:\n breeds: breed_code, breed_name\n charges: charge_id, charge_type, charge_amount\n sizes: size_code, size_description\n treatment_types: treatment_type_code, treatment_type_description\n owners: owner_id, first_name, last_name, street, city, state, zip_code, email_address, home_phone, cell_number\n dogs: dog_id, owner_id, abandoned_yn, breed_code, size_code, name, age, date_of_birth, gender, weight, date_arrived, date_adopted, date_departed\n professionals: professional_id, role_code, first_name, street, city, state, zip_code, last_name, email_address, home_phone, cell_number\n treatments: treatment_id, dog_id, professional_id, treatment_type_code, date_of_treatment, cost_of_treatment\n\nUser question: What are the emails of the professionals living in either the state of Hawaii or the state of Wisconsin ?", 
        "query": "select email_address from professionals where state  =  'hawaii' or state  =  'wisconsin'"
    },
    {
        "input": "Database schema:\n breeds: breed_code, breed_name\n charges: charge_id, charge_type, charge_amount\n sizes: size_code, size_description\n treatment_types: treatment_type_code, treatment_type_description\n owners: owner_id, first_name, last_name, street, city, state, zip_code, email_address, home_phone, cell_number\n dogs: dog_id, owner_id, abandoned_yn, breed_code, size_code, name, age, date_of_birth, gender, weight, date_arrived, date_adopted, date_departed\n professionals: professional_id, role_code, first_name, street, city, state, zip_code, last_name, email_address, home_phone, cell_number\n treatments: treatment_id, dog_id, professional_id, treatment_type_code, date_of_treatment, cost_of_treatment\n\nUser question: List the cost of each treatment and the corresponding treatment type description .", 
        "query": "select t1.cost_of_treatment ,  t2.treatment_type_description from treatments as t1 join treatment_types as t2 on t1.treatment_type_code  =  t2.treatment_type_code"
    },
]

# 语义相似度 Example Selector
example_selector = SemanticSimilarityExampleSelector.from_examples(
    examples,
    embeddings,
    FAISS,
    k=1,
    input_keys=["input"],
)

# Few-shot Prompt
few_shot_prompt = FewShotPromptTemplate(
    example_selector=example_selector,
    example_prompt=PromptTemplate.from_template(
        "User input: {input}\nSQL query: {query}"
    ),
    input_variables=["input", "dialect", "top_k"],
    prefix=SYSTEM_PREFIX,
    suffix="User input: {input}\nSQL query: ",
)

# 完整 Prompt
full_prompt = ChatPromptTemplate.from_messages(
    [
        SystemMessagePromptTemplate(prompt=few_shot_prompt),
        ("human", "{input}"),
        MessagesPlaceholder("messages"),
    ]
)


def create_graphrag_agent(db_name: str) -> Runnable:
    """
    创建使用 GraphRAG 增强的 ReAct Agent
    
    """
    logger.info(f"初始化 GraphRAG Agent (数据库: {db_name})")
    
    # 创建数据库连接
    db = SQLDatabase.from_uri(f"sqlite:///test_database/{db_name}/{db_name}.sqlite")
    
    # 初始化工具
    toolkit = SQLDatabaseToolkit(db=db, llm=llm)
    
    # 创建 ReAct Agent
    agent = create_react_agent(
        model=llm,
        tools=toolkit.get_tools(),
        prompt=full_prompt,
        state_schema=AgentState,
        config_schema=reactAgentConfig
    )
    
    logger.info(f"GraphRAG Agent 创建成功")
    return agent