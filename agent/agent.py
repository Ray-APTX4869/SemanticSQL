# from langchain_openai import ChatOpenAI
from langchain.chat_models import init_chat_model
from langgraph.prebuilt import create_react_agent
from utils.prompt import SYSTEM_PREFIX
import yaml
from dotenv import load_dotenv
import os
from pydantic import BaseModel
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
from langchain_community.utilities.sql_database import SQLDatabase
from utils.schema_utils import engine

import faiss
from langchain_community.docstore.in_memory import InMemoryDocstore
from langchain_community.vectorstores import FAISS
from langchain_core.example_selectors import SemanticSimilarityExampleSelector
from langchain_openai import OpenAIEmbeddings
from langchain_core.prompts import (
    ChatPromptTemplate,
    FewShotPromptTemplate,
    MessagesPlaceholder,
    PromptTemplate,
    SystemMessagePromptTemplate,
)
from agent.state import AgentState
from typing import Dict, Any
from langchain_core.runnables import Runnable
# react agent配置
class reactAgentConfig(BaseModel):
    username: str
    task_type: str = "sql_to_text" 
    verbose: bool = True
    handle_parsing_errors: bool = True
    max_iterations: int = 5

# 加载配置
with open("config.yaml", "r",encoding="utf-8") as f:
    config = yaml.safe_load(f)
# 加载环境变量
load_dotenv()
# 初始化llm
# llm = ChatOpenAI(model=os.getenv("model"), 
#                  api_key=os.getenv("api_key"), 
#                  base_url=os.getenv("base_url"), 
#                  max_tokens=config["max_tokens"], 
#                  temperature=config["temperature"])
## parameter "temperature" is not supported by the model, so we need to remove it
# llm = init_chat_model(model=os.getenv("model"), 
#                       api_key=os.getenv("api_key"), 
#                       base_url=os.getenv("base_url"), 
#                       max_tokens=config["max_tokens"], 
#                       temperature=config["temperature"])

llm = init_chat_model(model=os.getenv("model"), 
                      api_key=os.getenv("api_key"), 
                      base_url=os.getenv("base_url"), 
                      max_tokens=config["max_tokens"])
# # 初始化数据库
# db = SQLDatabase(engine)
# # 初始化工具
# toolkit = SQLDatabaseToolkit(db=db, llm=llm)
# 初始化系统提示
# prompt_template = hub.pull("langchain-ai/sql-agent-system-prompt")
# assert len(prompt_template.messages) == 1
# system_message = prompt_template.format(dialect=toolkit.dialect, top_k=5)

# # 使用LangGraph的create_react_agent构建agent
# react_agent_graph = create_react_agent(
#     model=llm,
#     tools=toolkit.get_tools(),
#     prompt=system_message,
#     config_schema=reactAgentConfig
# )


embeddings = OpenAIEmbeddings(model="text-embedding-3-large",
                              base_url=os.getenv("base_url"),
                              openai_api_key=os.getenv("api_key"))

# embedding_dim = len(embeddings.embed_query("hello world"))
# index = faiss.IndexFlatL2(embedding_dim)

# vector_store = FAISS(
#     embedding_function=embeddings,
#     index=index,
#     docstore=InMemoryDocstore(),
#     index_to_docstore_id={},
# )

# few shot examples
# examples = [{"input": "List the first name of all the professionals along with the description of the treatment they have done .", "query": "select distinct t1.first_name ,  t3.treatment_type_description from professionals as t1 join treatments as t2 on t1.professional_id  =  t2.professional_id join treatment_types as t3 on t2.treatment_type_code  =  t3.treatment_type_code"},
#            {"input": "Find the number of professionals who have not treated any dogs . ", "query": "select count(*) from professionals where professional_id not in ( select professional_id from treatments )"},
#            {"input": "Which owners live in the state whose name contains the substring 'North ' ? List his first name , last name and email address. ", "query": "select first_name ,  last_name ,  email_address from owners where state like '%north%'"},
#            {"input": "What are the emails of the professionals living in either the state of Hawaii or the state of Wisconsin ?", "query": "select email_address from professionals where state  =  'hawaii' or state  =  'wisconsin'"},
#            {"input": "List the cost of each treatment and the corresponding treatment type description .", "query": "select t1.cost_of_treatment ,  t2.treatment_type_description from treatments as t1 join treatment_types as t2 on t1.treatment_type_code  =  t2.treatment_type_code"},
#            ]

#examples = [{"input":"Database schema:\n breeds: breed_code, breed_name\n charges: charge_id, charge_type, charge_amount\n sizes: size_code, size_description\n treatment_types: treatment_type_code, treatment_type_description\n owners: owner_id, first_name, last_name, street, city, state, zip_code, email_address, home_phone, cell_number\n dogs: dog_id, owner_id, abandoned_yn, breed_code, size_code, name, age, date_of_birth, gender, weight, date_arrived, date_adopted, date_departed\n professionals: professional_id, role_code, first_name, street, city, state, zip_code, last_name, email_address, home_phone, cell_number\n treatments: treatment_id, dog_id, professional_id, treatment_type_code, date_of_treatment, cost_of_treatment\n\nUser question: List the first name of all the professionals along with the description of the treatment they have done .", "query": "select distinct t1.first_name ,  t3.treatment_type_description from professionals as t1 join treatments as t2 on t1.professional_id  =  t2.professional_id join treatment_types as t3 on t2.treatment_type_code  =  t3.treatment_type_code"},
#            {"input":"Database schema:\n breeds: breed_code, breed_name\n charges: charge_id, charge_type, charge_amount\n sizes: size_code, size_description\n treatment_types: treatment_type_code, treatment_type_description\n owners: owner_id, first_name, last_name, street, city, state, zip_code, email_address, home_phone, cell_number\n dogs: dog_id, owner_id, abandoned_yn, breed_code, size_code, name, age, date_of_birth, gender, weight, date_arrived, date_adopted, date_departed\n professionals: professional_id, role_code, first_name, street, city, state, zip_code, last_name, email_address, home_phone, cell_number\n treatments: treatment_id, dog_id, professional_id, treatment_type_code, date_of_treatment, cost_of_treatment\n\nUser question: Find the number of professionals who have not treated any dogs . ", "query": "select count(*) from professionals where professional_id not in ( select professional_id from treatments )"},
#            {"input":"Database schema:\n breeds: breed_code, breed_name\n charges: charge_id, charge_type, charge_amount\n sizes: size_code, size_description\n treatment_types: treatment_type_code, treatment_type_description\n owners: owner_id, first_name, last_name, street, city, state, zip_code, email_address, home_phone, cell_number\n dogs: dog_id, owner_id, abandoned_yn, breed_code, size_code, name, age, date_of_birth, gender, weight, date_arrived, date_adopted, date_departed\n professionals: professional_id, role_code, first_name, street, city, state, zip_code, last_name, email_address, home_phone, cell_number\n treatments: treatment_id, dog_id, professional_id, treatment_type_code, date_of_treatment, cost_of_treatment\n\nUser question: Which owners live in the state whose name contains the substring 'North ' ? List his first name , last name and email address. ", "query": "select first_name ,  last_name ,  email_address from owners where state like '%north%'"},
#            {"input":"Database schema:\n breeds: breed_code, breed_name\n charges: charge_id, charge_type, charge_amount\n sizes: size_code, size_description\n treatment_types: treatment_type_code, treatment_type_description\n owners: owner_id, first_name, last_name, street, city, state, zip_code, email_address, home_phone, cell_number\n dogs: dog_id, owner_id, abandoned_yn, breed_code, size_code, name, age, date_of_birth, gender, weight, date_arrived, date_adopted, date_departed\n professionals: professional_id, role_code, first_name, street, city, state, zip_code, last_name, email_address, home_phone, cell_number\n treatments: treatment_id, dog_id, professional_id, treatment_type_code, date_of_treatment, cost_of_treatment\n\nUser question: What are the emails of the professionals living in either the state of Hawaii or the state of Wisconsin ?", "query": "select email_address from professionals where state  =  'hawaii' or state  =  'wisconsin'"},
#            {"input":"Database schema:\n breeds: breed_code, breed_name\n charges: charge_id, charge_type, charge_amount\n sizes: size_code, size_description\n treatment_types: treatment_type_code, treatment_type_description\n owners: owner_id, first_name, last_name, street, city, state, zip_code, email_address, home_phone, cell_number\n dogs: dog_id, owner_id, abandoned_yn, breed_code, size_code, name, age, date_of_birth, gender, weight, date_arrived, date_adopted, date_departed\n professionals: professional_id, role_code, first_name, street, city, state, zip_code, last_name, email_address, home_phone, cell_number\n treatments: treatment_id, dog_id, professional_id, treatment_type_code, date_of_treatment, cost_of_treatment\n\nUser question: List the cost of each treatment and the corresponding treatment type description .", "query": "select t1.cost_of_treatment ,  t2.treatment_type_description from treatments as t1 join treatment_types as t2 on t1.treatment_type_code  =  t2.treatment_type_code"},
#           ]


examples = [
    # Example 1: COUNT(*)
    {
        "input": "Database schema:\n singers: singer_id, name, country, song_name, song_release_year, age, is_male\n\nUser question: How many singers do we have?",
        "query": "select count(*) from singers"
    },
    
    # Example 2: EXCEPT 集合操作（简单版）
    {
        "input": "Database schema:\n airlines: uid, airline, abbreviation, country\n flights: flightno, sourceairport, destairport, airline\n\nUser question: Find airlines that have flights from CVO but not from APG.",
        "query": "select t1.airline from airlines as t1 join flights as t2 on t1.uid = t2.airline where t2.sourceairport = \"cvo\" except select t1.airline from airlines as t1 join flights as t2 on t1.uid = t2.airline where t2.sourceairport = \"apg\""
    },
    
    # Example 3: NOT IN + UNION
    {
        "input": "Database schema:\n airports: airportcode, airportname, city, country\n flights: flightno, sourceairport, destairport\n\nUser question: Find airports that have no flights (neither as source nor destination).",
        "query": "select airportname from airports where airportcode not in (select sourceairport from flights union select destairport from flights)"
    },
    
    # Example 4: 避免不必要的 JOIN
    {
        "input": "Database schema:\n flights: flightno, sourceairport, destairport, airline\n airports: airportcode, airportname, city\n\nUser question: How many flights go to ATO airport?",
        "query": "select count(*) from flights where destairport = \"ato\""
    },
    
    # Example 5: GROUP BY + HAVING
    {
        "input": "Database schema:\n airlines: uid, airline, abbreviation, country\n flights: flightno, airline\n\nUser question: List airlines that have more than 10 flights.",
        "query": "select t1.airline from airlines as t1 join flights as t2 on t1.uid = t2.airline group by t1.airline having count(*) > 10"
    },
    
    # Example 6: LIKE 模糊匹配
    {
        "input": "Database schema:\n owners: owner_id, first_name, last_name, state, email_address\n\nUser question: Which owners live in states whose name contains the substring 'North'? List their first name, last name and email address.",
        "query": "select first_name, last_name, email_address from owners where state like '%north%'"
    },
    
    # Example 7: OR 多条件
    {
        "input": "Database schema:\n professionals: professional_id, first_name, last_name, state, email_address\n\nUser question: What are the emails of the professionals living in either Hawaii or Wisconsin?",
        "query": "select email_address from professionals where state = \"hawaii\" or state = \"wisconsin\""
    },
    
    # Example 8: DISTINCT + 多表 JOIN
    {
        "input": "Database schema:\n professionals: professional_id, role_code, first_name\n treatments: treatment_id, professional_id, treatment_type_code\n treatment_types: treatment_type_code, treatment_type_description\n\nUser question: List the first name of all the professionals along with the description of the treatment they have done.",
        "query": "select distinct t1.first_name, t3.treatment_type_description from professionals as t1 join treatments as t2 on t1.professional_id = t2.professional_id join treatment_types as t3 on t2.treatment_type_code = t3.treatment_type_code"
    },
    
    # 🆕 Example 9: INTERSECT 的正确用法（完整查询的交集）
    {
        "input": "Database schema:\n stadium: stadium_id, location, name, capacity, highest, lowest, average\n concert: concert_id, concert_name, theme, stadium_id, year\n\nUser question: Show the stadium name and location that had concerts in both 2014 and 2015.",
        "query": "select t2.name, t2.location from concert as t1 join stadium as t2 on t1.stadium_id = t2.stadium_id where t1.year = 2014 intersect select t2.name, t2.location from concert as t1 join stadium as t2 on t1.stadium_id = t2.stadium_id where t1.year = 2015"
    },
    
    # 🆕 Example 10: EXCEPT 的正确用法（完整查询的差集）
    {
        "input": "Database schema:\n stadium: stadium_id, location, name, capacity\n concert: concert_id, stadium_id, year\n\nUser question: Show stadium names that had concerts in 2014 but not in 2015.",
        "query": "select t2.name from concert as t1 join stadium as t2 on t1.stadium_id = t2.stadium_id where t1.year = 2014 except select t2.name from concert as t1 join stadium as t2 on t1.stadium_id = t2.stadium_id where t1.year = 2015"
    },
    
    # 🆕 Example 11: INTERSECT 的另一个例子（强化理解）
    {
        "input": "Database schema:\n airlines: uid, airline, abbreviation, country\n flights: flightno, sourceairport, destairport, airline\n\nUser question: Find airlines that have flights from both CVO and APG airports.",
        "query": "select t1.airline from airlines as t1 join flights as t2 on t1.uid = t2.airline where t2.sourceairport = \"cvo\" intersect select t1.airline from airlines as t1 join flights as t2 on t1.uid = t2.airline where t2.sourceairport = \"apg\""
    }
]


example_selector = SemanticSimilarityExampleSelector.from_examples(
    examples,
    embeddings,
    FAISS,
    k=2,
    input_keys=["input"],
)


few_shot_prompt = FewShotPromptTemplate(
    example_selector=example_selector,
    example_prompt=PromptTemplate.from_template(
        "User input: {input}\nSQL query: {query}"
    ),
    input_variables=["input", "dialect", "top_k"],
    prefix=SYSTEM_PREFIX,
    suffix="User input: {input}\nSQL query: ",
)

# few_shot_prompt = FewShotPromptTemplate(
#     examples=examples,
#     example_prompt=PromptTemplate.from_template(
#         "User input: {input}\nSQL query: {query}"
#     ),
#     input_variables=["input", "dialect", "top_k"],
#     prefix=SYSTEM_PREFIX,
#     suffix="User input: {input}\nSQL query: ",
# )

full_prompt = ChatPromptTemplate.from_messages(
    [
        SystemMessagePromptTemplate(prompt=few_shot_prompt),
        ("human", "{input}"),
        MessagesPlaceholder("messages"),
    ]
)

# prompt_val = full_prompt.invoke(
#     {
#         "input": "How many arists are there",
#         "top_k": 5,
#         "dialect": "SQLite",
#         "agent_scratchpad": [],
#     }   
# )

# react_agent_graph = create_react_agent(
#     model=llm,
#     tools=toolkit.get_tools(),
#     prompt=full_prompt,
#     state_schema=AgentState,
#     config_schema=reactAgentConfig
# )

def create_react_agent_graph(db_name: str) -> Runnable:
    # 根据db_name获取数据库
    db = SQLDatabase.from_uri(f"sqlite:///test_database/{db_name}/{db_name}.sqlite")
    # 初始化工具
    toolkit = SQLDatabaseToolkit(db=db, llm=llm)
    # 初始化agent
    return create_react_agent(
        model=llm,
        tools=toolkit.get_tools(),
        prompt=full_prompt,
        state_schema=AgentState,
        config_schema=reactAgentConfig
    )