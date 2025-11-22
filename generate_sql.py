from pydantic import BaseModel
from typing import List, Optional, Dict
from agent.agent_factory import create_agent  # ✅ 使用工厂方法
from langchain_core.messages import AIMessage, ToolMessage
import logging
import json
from datetime import datetime
import os
import asyncio
from utils.schema_utils import get_schemas_from_json, Schema
from langchain_core.runnables import Runnable
from tools.sql_tool import sql_format

os.makedirs('logs', exist_ok=True)
os.makedirs('test', exist_ok=True)

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
    graphrag_metadata: Optional[Dict] = None  # ✅ 新增：GraphRAG 检索元数据

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


async def process_query(request: QueryRequest, schema: Optional[Schema] = None, 
                        agent_graph: Optional[Runnable] = None,
                        db_name: str = None,
                        use_graphrag: bool = False, top_k: int = 5,use_full_schema = False) -> QueryResponse:
    """
    处理查询请求
    
    Args:
        request: 查询请求
        schema: 数据库 Schema
        agent_graph: Agent 图
        db_name: 数据库名称
        use_graphrag: 是否使用 GraphRAG
    """
    try:
        logger.info(f"Received query request: {json.dumps(request.model_dump(), ensure_ascii=False)}")
        
        graphrag_metadata = None
        
        # ========== GraphRAG 检索 Schema ==========Z
        if use_graphrag and db_name:
            from utils.graphrag import GraphRAGRetriever  # ✅ 延迟导入
            
            logger.info(f"[GraphRAG] 启用检索 (数据库: {db_name})")
            
            try:
                # ✅ 只对当前数据库初始化
                graphrag_retriever = GraphRAGRetriever(
                    tables_json_path="test/tables.json",
                    db_filter=[db_name]  # ✅ 只加载当前数据库
                )
                
                relevant_schema, metadata = graphrag_retriever.retrieve_relevant_schema(
                    db_id=db_name,
                    question=request.question,
                    use_full_schema=use_full_schema,
                    top_k=top_k
                )
                
                graphrag_metadata = metadata
                
                if relevant_schema:
                    schema_info_text = relevant_schema
                    logger.info(f"[成功] GraphRAG 检索: {metadata.get('retrieved_tables', 0)} 个表")
                else:
                    schema_info_text = schema.to_text() if schema else ""
                    logger.warning("[警告] GraphRAG 检索失败，使用完整 Schema")
                    
            except Exception as e:
                logger.error(f"[错误] GraphRAG 异常: {str(e)}，回退到完整 Schema")
                schema_info_text = schema.to_text() if schema else ""
                graphrag_metadata = {"error": str(e), "mode": "fallback"}
        else:
            schema_info_text = schema.to_text() if schema else ""
            logger.info(f"[标准] 使用完整 Schema")
        
        # ========== 构建增强输入 ==========
        if schema_info_text:
            enhanced_input = f"Database schema:\n{schema_info_text}\n\nUser question:\n{request.question}"
        else:
            enhanced_input = request.question

        # ========== 初始化 Agent ==========
        graph = agent_graph 
        if graph is None:
            raise ValueError("Agent graph 未初始化")

        initial_state = {
            "input": enhanced_input,
            "top_k": request.top_k,
            "dialect": request.dialect,
            "messages": []
        }

        # ========== 执行推理 ==========
        response = QueryResponse(steps=[], graphrag_metadata=graphrag_metadata)
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
    """从 dev.sql 读取测试数据"""
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
                parts = line.split("|||")
                if len(parts) >= 2:
                    current_db = parts[1].strip()
                    question = parts[0].split(":", 1)[1].strip()
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
                if gold_sql.endswith(';'):
                    gold_sql = gold_sql[:-1]
                if current_db:
                    current_dataset = dataset.get(current_db, None)
                    if current_dataset:
                        current_dataset['gold_sql'].append(gold_sql)
                    current_db = None
                    question = None
                    gold_sql = None 
    return dataset


async def run():
    """运行评测脚本"""
    # ========== 配置 ==========
    dbs_env = os.getenv("EVAL_DBS", "flight_2").split(",")
    dbs = [db.strip() for db in dbs_env if db.strip()]
    top_k = int(os.getenv("top_k_tables: 5", "5"))
    eval_limit = int(os.getenv("EVAL_LIMIT", "0"))
    use_graphrag = os.getenv("USE_GRAPHRAG", "true").lower() == "true"  
    use_full_schema = os.getenv("USE_FULL_SCHEMA", "false").lower() == "false"

    logger.info(f"{'='*50}")
    logger.info(f" 开始评测")
    logger.info(f" 数据库: {', '.join(dbs)}")
    logger.info(f" GraphRAG: {'启用' if use_graphrag else '禁用'}")
    logger.info(f"{'='*50}")

    # ========== 加载 Schema ==========
    schemas, db_names, tables = get_schemas_from_json("test/tables.json")
    dataset = generate_query()

    for db_name in dbs:
        if db_name not in dataset:
            logger.warning(f"⚠️ 未在数据集中找到 {db_name}，跳过")
            continue

        schema_data = schemas.get(db_name)
        table_meta = tables.get(db_name)
        if not schema_data or not table_meta:
            logger.warning(f"⚠️ 未找到 {db_name} 的 Schema 信息，跳过")
            continue

        schema = Schema(schema_data, table_meta)
        
        # ✅ 使用工厂方法创建 Agent
        react_graph = create_agent(db_name, use_graphrag=use_graphrag)

        gold_examples: List[str] = []
        pred_examples: List[str] = []
        errors: List[str] = []

        gold_path = f"test/gold_example_{db_name}.txt"
        pred_path = f"test/pred_example_{db_name}.txt"

        open(gold_path, "w", encoding="utf-8").close()
        open(pred_path, "w", encoding="utf-8").close()

        questions = dataset[db_name]["question"]
        golds = dataset[db_name]["gold_sql"]

        for i, (question, gold_sql) in enumerate(zip(questions, golds)):
            logger.info(f"\n{'='*50}")
            logger.info(f" 问题 {i + 1}/{len(questions)}")
            logger.info(f"Question: {question}")
            logger.info(f"{'='*50}")

            response = await process_query(
                QueryRequest(question=question), 
                schema, 
                react_graph,
                db_name=db_name,
                use_graphrag=use_graphrag,
                top_k=top_k
            )

            if response.sql_query and response.sql_query.strip().endswith(';'):
                response.sql_query = response.sql_query.strip()[:-1]

            logger.info(f"Generated SQL: {response.sql_query}")
            
            # ✅ 输出 GraphRAG 元数据
            if response.graphrag_metadata:
                metadata = response.graphrag_metadata
                if metadata.get("mode") == "semantic_retrieval":
                    logger.info(f" GraphRAG 检索详情:")
                    logger.info(f"   - 相关表: {', '.join(metadata.get('relevant_tables', []))}")
                    logger.info(f"   - 检索率: {metadata.get('retrieved_tables', 0)}/{metadata.get('total_tables', 0)}")

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
                logger.info(f"\n✋ 已达到评测上限 {eval_limit} 条")
                break

        # ========== 写入结果 ==========
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
            logger.info(f"\n⚠️ 出现 {len(errors)} 个错误，详情: {error_path}")
        else:
            logger.info("\n 所有问题处理完成，无错误")

        logger.info(f"\n{'='*50}")
        logger.info(f"处理完成!")
        logger.info(f"- 黄金标准: {gold_path}")
        logger.info(f"- 预测结果: {pred_path}")
        logger.info(f"{'='*50}")


if __name__ == "__main__":
    asyncio.run(run())