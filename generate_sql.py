from pydantic import BaseModel
from typing import List, Optional, Dict
from agent.agent import  create_react_agent_graph
from langchain_core.messages import AIMessage, ToolMessage
import logging
import json
from datetime import datetime
import os
import asyncio
from utils.schema_utils import get_schemas_from_json, Schema
from langchain_core.runnables import Runnable
from tools.sql_tool import sql_format

# 创建logs目录（如果不存在）
os.makedirs('logs', exist_ok=True)
# 创建test目录（如果不存在）
os.makedirs('test', exist_ok=True)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/text_to_sql_generate_sql_{datetime.now().strftime("%Y%m%d")}.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class QueryRequest(BaseModel):
    question: str
    top_k: Optional[int] = 5
    dialect: Optional[str] = "SQLite"

class QueryResponse(BaseModel):
    sql_query: Optional[str] = None
    result: Optional[str] = None
    error: Optional[str] = None
    steps: List[dict] = []

    def get_format_sql_query(self) -> Optional[str]:
        if not self.sql_query:
            return self.sql_query
        sql = self.sql_query.strip()
        if sql.startswith("```sql") and sql.endswith("```"):
            sql = sql[7:-3].strip()
        elif sql.startswith("```") and sql.endswith("```"):
            sql = sql[3:-3].strip()
        sql = sql.replace("\n", " ")
        return sql.strip()

async def process_query(request: QueryRequest, schema: Optional[Schema] = None, agent_graph: Optional[Runnable] = None):
    try:
        logger.info(f"Received query request: {json.dumps(request.model_dump(), ensure_ascii=False)}")

        enhanced_input = request.question
        if schema is not None:
            schema_info_text = schema.to_text()
            if schema_info_text:
                enhanced_input = f"Database schema:\n{schema_info_text}\n\nUser question:\n{request.question}"

        graph = agent_graph 
        if graph is None:
            raise ValueError("react agent graph 未初始化")

        initial_state = {
            "input": enhanced_input,
            "top_k": request.top_k,
            "dialect": request.dialect,
            "messages": []
        }

        response = QueryResponse(steps=[])
        sql_query = None
        result = None

        for step in graph.stream(initial_state, stream_mode=["values"]):
            message = step[1]["messages"]
            if len(message) > 0:
                message = message[-1]

            step_info = {
                "type": message.__class__.__name__,
                "content": str(message)
            }

            if isinstance(message, AIMessage):
                if message.tool_calls:
                    for action in message.tool_calls:
                        if action.get("name") == "sql_db_query":
                            sql_query = action.get("args", {}).get("query")
                            if sql_query and sql_query.strip().endswith(';'):
                                sql_query = sql_query.strip()[:-1]
                if message.response_metadata.get("finish_reason") == "stop":
                    result = message.content
            elif isinstance(message, ToolMessage):
                result = message.content

            response.steps.append(step_info)

        response.sql_query = sql_query
        response.result = result

        logger.info(f"Query response: {json.dumps(response.model_dump(), ensure_ascii=False)}")
        return response

    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error processing query: {error_msg}")
        return QueryResponse(error=error_msg)

def generate_query():
    dataset = {}
    current_dataset = None
    current_db = None
    question = None
    gold_sql = None
    
    with open("test/dev.sql", "r", encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
                
            if line.startswith("Question"):
                # 解析新的数据集名称
                parts = line.split("|||")
                if len(parts) >= 2:
                    current_db = parts[1].strip()
                    question = parts[0].split(":", 1)[1].strip()
                    # 如果已经有数据集在处理中，保存它
                    current_dataset = dataset.get(current_db, None)
                    if current_dataset:
                        current_dataset['question'].append(question)
                    else:
                        dataset[current_db] = {
                            'question': [question],
                            'gold_sql': []
                        }
                
            elif line.startswith("SQL:"):
                gold_sql = line.split(":", 1)[1].strip()
                # 如果黄金标准SQL以分号结尾，则去掉分号
                if gold_sql.endswith(';'):
                    gold_sql = gold_sql[:-1]
                if current_db:
                    # 如果已经有数据集在处理中，保存它
                    current_dataset = dataset.get(current_db, None)
                    if current_dataset:
                        current_dataset['gold_sql'].append(gold_sql)
                    current_db = None
                    question = None
                    gold_sql = None 
    return dataset

async def run():
    dbs_env = os.getenv("EVAL_DBS", "concert_singer").split(",")
    dbs = [db.strip() for db in dbs_env if db.strip()]
    eval_limit = int(os.getenv("EVAL_LIMIT", "0"))

    schemas, db_names, tables = get_schemas_from_json("test/tables.json")
    dataset = generate_query()

    for db_name in dbs:
        if db_name not in dataset:
            logger.warning(f"未在数据集中找到 {db_name}，跳过。")
            continue

        schema_data = schemas.get(db_name)
        table_meta = tables.get(db_name)
        if not schema_data or not table_meta:
            logger.warning(f"未在 tables.json 中找到 {db_name} 的 schema 信息，跳过。")
            continue

        schema = Schema(schema_data, table_meta)
        react_graph = create_react_agent_graph(db_name)

        gold_examples: List[str] = []
        pred_examples: List[str] = []
        errors: List[str] = []

        gold_path = f"test/gold_example_{db_name}.txt"
        pred_path = f"test/pred_example_{db_name}.txt"

        # 清空输出文件
        open(gold_path, "w", encoding="utf-8").close()
        open(pred_path, "w", encoding="utf-8").close()

        questions = dataset[db_name]["question"]
        golds = dataset[db_name]["gold_sql"]

        for i, (question, gold_sql) in enumerate(zip(questions, golds)):
            logger.info(f"\n处理问题 {i + 1}/{len(questions)}")
            logger.info(f"Question: {question}")

            response = await process_query(QueryRequest(question=question), schema, react_graph)

            if response.sql_query and response.sql_query.strip().endswith(';'):
                response.sql_query = response.sql_query.strip()[:-1]

            logger.info(f"Generated SQL: {response.sql_query}")

            if response.error:
                logger.info(f"Error: {response.error}")
                errors.append(f"问题: {question}\n错误: {response.error}\n")
                pred_examples.append("SELECT 'ERROR' AS result\n")
            else:
                formatted_sql = response.get_format_sql_query()
                if not formatted_sql:
                    pred_examples.append("SELECT 'ERROR' AS result\n")
                else:
                    pred_examples.append(f"{formatted_sql}\n")

            gold_examples.append(f"{gold_sql}\t{db_name}\n")

            if eval_limit and (i + 1) >= eval_limit:
                logger.info(f"\n已达到评测上限 {eval_limit} 条，提前结束。")
                break

        if gold_examples:
            with open(gold_path, "w", encoding="utf-8") as f:
                f.writelines(gold_examples)

        if pred_examples:
            with open(pred_path, "w", encoding="utf-8") as f:
                f.writelines(pred_examples)

        if errors:
            error_path = f"test/errors_{db_name}.log"
            with open(error_path, "w", encoding="utf-8") as f:
                f.writelines(errors)
            logger.info(f"\n处理过程中出现 {len(errors)} 个错误，详情请查看 {error_path}")
        else:
            logger.info("\n所有问题处理完成，没有错误")

        logger.info(f"\n处理完成! 结果已写入:")
        logger.info(f"- 黄金标准: {gold_path}")
        logger.info(f"- 预测结果: {pred_path}")

if __name__ == "__main__":
    asyncio.run(run())