from pydantic import BaseModel
from typing import List, Optional, Dict
from agent.agent_factory import create_agent
from langchain_core.messages import AIMessage, ToolMessage
import logging
import json
from datetime import datetime
import os
import sqlparse
import re
import asyncio
from utils.schema_utils import get_schemas_from_json, Schema
from langchain_core.runnables import Runnable
from tools.sql_tool import sql_format
import yaml
from collections import defaultdict  # ✅ 新增：用于 Token 统计

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


def load_config(config_path: str = "config.yaml") -> Dict:
    """从 YAML 文件加载配置"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        logger.info(f"[配置] 成功加载配置文件: {config_path}")
        return config
    except FileNotFoundError:
        logger.warning(f"[配置] 未找到配置文件 {config_path}，使用默认值")
        return {}
    except Exception as e:
        logger.error(f"[配置] 加载失败: {str(e)}，使用默认值")
        return {}


class QueryRequest(BaseModel):
    question: str
    top_k: Optional[int] = 5
    dialect: Optional[str] = "SQLite"


class QueryResponse(BaseModel):
    sql_query: Optional[str] = None
    result: Optional[str] = None
    error: Optional[str] = None
    steps: List[dict] = []
    graphrag_metadata: Optional[Dict] = None
    token_usage: Optional[Dict] = None  # ✅ 新增：Token 使用信息

    
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
                        use_graphrag: bool = False, 
                        top_k: int = 5,
                        use_full_schema: bool = False,
                        tables_json_path: str = "test/tables.json") -> QueryResponse:
    """
    处理查询请求
    
    Args:
        request: 查询请求
        schema: 数据库 Schema
        agent_graph: Agent 图
        db_name: 数据库名称
        use_graphrag: 是否使用 GraphRAG
        top_k: GraphRAG 检索的表数量
        use_full_schema: 是否使用完整 Schema（GraphRAG 失败时的回退策略）
        tables_json_path: tables.json 路径
    """
    try:
        logger.info(f"Received query request: {json.dumps(request.model_dump(), ensure_ascii=False)}")
        
        graphrag_metadata = None
        
        # ========== GraphRAG 检索 Schema ==========
        if use_graphrag and db_name:
            from utils.graphrag import GraphRAGRetriever
            
            logger.info(f"[GraphRAG] 启用检索 (数据库: {db_name}, top_k={top_k})")
            
            try:
                graphrag_retriever = GraphRAGRetriever(
                    tables_json_path=tables_json_path,
                    db_filter=[db_name]
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
        
        # ✅ 新增：Token 统计
        total_token_usage = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0
        }

        for step in graph.stream(initial_state, stream_mode=["values"]):
            message = step[1]["messages"]
            if len(message) > 0:
                message = message[-1]

            step_info = {
                "type": message.__class__.__name__,
                "content": str(message)
            }

            if isinstance(message, AIMessage):
                # ✅ 新增：收集 Token 使用信息
                if hasattr(message, 'response_metadata') and message.response_metadata:
                    usage = message.response_metadata.get('token_usage') or message.response_metadata.get('usage')
                    if usage:
                        if isinstance(usage, dict):
                            # 兼容不同 LLM 的 token 字段名
                            prompt_tokens = usage.get("prompt_tokens", 0) or usage.get("input_tokens", 0) or 0
                            completion_tokens = usage.get("completion_tokens", 0) or usage.get("output_tokens", 0) or 0
                            
                            total_token_usage["prompt_tokens"] += prompt_tokens
                            total_token_usage["completion_tokens"] += completion_tokens
                            total_token_usage["total_tokens"] = (
                                total_token_usage["prompt_tokens"] + 
                                total_token_usage["completion_tokens"]
                            )
                
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
        response.token_usage = total_token_usage  # ✅ 新增：设置 Token 使用信息

        logger.info(f"Query response: {json.dumps(response.model_dump(), ensure_ascii=False)}")
        
        # ✅ 新增：输出 Token 使用信息
        if total_token_usage["total_tokens"] > 0:
            logger.info(f"Token usage: Prompt={total_token_usage['prompt_tokens']}, "
                       f"Completion={total_token_usage['completion_tokens']}, "
                       f"Total={total_token_usage['total_tokens']}")
        
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
    # ========== 加载配置 ==========
    config = load_config("config.yaml")
    
    # ========== 从配置读取参数 ==========
    graphrag_config = config.get("graphrag", {})
    database_config = config.get("database", {})
    dbs_env = config.get("eval_dbs", "concert_singer").split(",")
    #dbs_env = os.getenv("EVAL_DBS", "concert_singer").split(",")
    dbs = [db.strip() for db in dbs_env if db.strip()]
    eval_limit = int(os.getenv("EVAL_LIMIT", "0"))
    
    use_graphrag = os.getenv("USE_GRAPHRAG")
    if use_graphrag is None:
        use_graphrag = graphrag_config.get("enabled", False)
    else:
        use_graphrag = use_graphrag.lower() == "true"
    
    use_full_schema = os.getenv("USE_FULL_SCHEMA")
    if use_full_schema is None:
        use_full_schema = graphrag_config.get("use_full_schema", False)
    else:
        use_full_schema = use_full_schema.lower() == "true"
    
    top_k = int(os.getenv("TOP_K_TABLES", graphrag_config.get("top_k_tables", 5)))
    
    tables_json_path = database_config.get("tables_json_path", "test/tables.json")

    # ========== 输出配置信息 ==========
    logger.info(f"{'='*50}")
    logger.info(f" 开始评测")
    logger.info(f"{'='*50}")
    logger.info(f" 数据库: {', '.join(dbs)}")
    logger.info(f" GraphRAG 配置:")
    logger.info(f"   - 启用: {use_graphrag}")
    logger.info(f"   - Top-K 表数: {top_k}")
    logger.info(f"   - 使用完整 Schema: {use_full_schema}")
    logger.info(f"   - Tables JSON: {tables_json_path}")
    logger.info(f" 评测限制: {eval_limit if eval_limit > 0 else '无限制'}")
    logger.info(f"{'='*50}\n")

    # ✅ 新增：Token 统计（按难度级别）
    from evaluation import Evaluator
    from process_sql import get_schema, Schema as SchemaFromProcess, get_sql
    
    token_stats = defaultdict(lambda: {
        "total_queries": 0,
        "total_prompt_tokens": 0,
        "total_completion_tokens": 0,
        "total_tokens": 0,
        "queries": []
    })
    
    evaluator = Evaluator()

    # ========== 加载 Schema ==========
    schemas, db_names, tables = get_schemas_from_json(tables_json_path)
    dataset = generate_query()

    for db_name in dbs:
        if db_name not in dataset:
            logger.warning(f"未在数据集中找到 {db_name}，跳过")
            continue

        schema_data = schemas.get(db_name)
        table_meta = tables.get(db_name)
        if not schema_data or not table_meta:
            logger.warning(f"未找到 {db_name} 的 Schema 信息，跳过")
            continue

        schema = Schema(schema_data, table_meta)
        
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
                top_k=top_k,
                use_full_schema=use_full_schema,
                tables_json_path=tables_json_path
            )

            # ✅ 新增：评估难度级别并统计 Token
            try:
                db_path = f"test_database/{db_name}/{db_name}.sqlite"
                if os.path.exists(db_path):
                    gold_schema = SchemaFromProcess(get_schema(db_path))
                    gold_sql_dict = get_sql(gold_schema, gold_sql)
                    hardness = evaluator.eval_hardness(gold_sql_dict)
                else:
                    hardness = "unknown"
            except Exception as e:
                logger.warning(f"无法评估难度级别: {e}")
                hardness = "unknown"
            
            # ✅ 新增：累积 Token 统计
            if response.token_usage and response.token_usage.get("total_tokens", 0) > 0:
                token_stats[hardness]["total_queries"] += 1
                token_stats[hardness]["total_prompt_tokens"] += response.token_usage.get("prompt_tokens", 0)
                token_stats[hardness]["total_completion_tokens"] += response.token_usage.get("completion_tokens", 0)
                token_stats[hardness]["total_tokens"] += response.token_usage.get("total_tokens", 0)
                token_stats[hardness]["queries"].append({
                    "question": question,
                    "tokens": response.token_usage.get("total_tokens", 0),
                    "prompt_tokens": response.token_usage.get("prompt_tokens", 0),
                    "completion_tokens": response.token_usage.get("completion_tokens", 0)
                })

            if response.sql_query and response.sql_query.strip().endswith(';'):
                response.sql_query = response.sql_query.strip()[:-1]

            logger.info(f"Generated SQL: {response.sql_query}")
            
            # 输出 GraphRAG 元数据
            if response.graphrag_metadata:
                metadata = response.graphrag_metadata
                mode = metadata.get("mode", "unknown")
                
                if mode == "hybrid_retrieval":
                    logger.info(f" GraphRAG 检索详情:")
                    logger.info(f"   - 模式: 混合检索 (Keyword + Embedding)")
                    logger.info(f"   - 相关表: {', '.join(metadata.get('relevant_tables', []))}")
                    logger.info(f"   - 检索率: {metadata.get('retrieved_tables', 0)}/{metadata.get('total_tables', 0)}")
                    
                    weights = metadata.get('weights', {})
                    logger.info(f"   - 权重: Keyword={weights.get('keyword', 0.4)}, Embedding={weights.get('embedding', 0.6)}")
                    
                    scores = metadata.get('scores', {})
                    top_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:3]
                    for table, score in top_scores:
                        logger.info(f"      {table}: {score:.4f}")
                        
                elif mode == "full_schema":
                    logger.info(f" Schema 模式: 完整 Schema")
                elif mode == "fallback":
                    logger.info(f" Schema 模式: 回退到完整 Schema (原因: {metadata.get('reason', '未知')})")

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
                logger.info(f"\n 已达到评测上限 {eval_limit} 条")
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
            logger.info(f"\n 出现 {len(errors)} 个错误，详情: {error_path}")
        else:
            logger.info("\n所有问题处理完成，无错误")

        # ✅ 新增：输出 Token 统计报告
        logger.info(f"\n{'='*80}")
        logger.info(f"Token 使用统计报告 - {db_name}")
        logger.info(f"{'='*80}")
        
        for hardness in ['easy', 'medium', 'hard', 'extra', 'unknown']:
            if hardness in token_stats and token_stats[hardness]["total_queries"] > 0:
                stats = token_stats[hardness]
                avg_prompt = stats["total_prompt_tokens"] / stats["total_queries"]
                avg_completion = stats["total_completion_tokens"] / stats["total_queries"]
                avg_total = stats["total_tokens"] / stats["total_queries"]
                
                logger.info(f"\n【{hardness.upper()}】")
                logger.info(f"  查询数量: {stats['total_queries']}")
                logger.info(f"  总 Token: {stats['total_tokens']:,}")
                logger.info(f"  平均 Token: {avg_total:.1f}")
                logger.info(f"  平均 Prompt Tokens: {avg_prompt:.1f}")
                logger.info(f"  平均 Completion Tokens: {avg_completion:.1f}")
        
        # 总计
        all_stats = {
            "total_queries": sum(s["total_queries"] for s in token_stats.values()),
            "total_tokens": sum(s["total_tokens"] for s in token_stats.values()),
            "total_prompt_tokens": sum(s["total_prompt_tokens"] for s in token_stats.values()),
            "total_completion_tokens": sum(s["total_completion_tokens"] for s in token_stats.values()),
        }
        
        if all_stats["total_queries"] > 0:
            logger.info(f"\n【总计】")
            logger.info(f"  查询数量: {all_stats['total_queries']}")
            logger.info(f"  总 Token: {all_stats['total_tokens']:,}")
            logger.info(f"  平均 Token: {all_stats['total_tokens'] / all_stats['total_queries']:.1f}")
            logger.info(f"  总 Prompt Tokens: {all_stats['total_prompt_tokens']:,}")
            logger.info(f"  总 Completion Tokens: {all_stats['total_completion_tokens']:,}")
        
        logger.info(f"{'='*80}")

        # ✅ 新增：保存 Token 统计到 JSON
        token_stats_file = f"test/token_stats_{db_name}.json"
        with open(token_stats_file, 'w', encoding='utf-8') as f:
            stats_dict = {
                k: {
                    "total_queries": v["total_queries"],
                    "total_prompt_tokens": v["total_prompt_tokens"],
                    "total_completion_tokens": v["total_completion_tokens"],
                    "total_tokens": v["total_tokens"],
                    "avg_tokens": v["total_tokens"] / v["total_queries"] if v["total_queries"] > 0 else 0,
                    "avg_prompt_tokens": v["total_prompt_tokens"] / v["total_queries"] if v["total_queries"] > 0 else 0,
                    "avg_completion_tokens": v["total_completion_tokens"] / v["total_queries"] if v["total_queries"] > 0 else 0
                }
                for k, v in token_stats.items() if v["total_queries"] > 0
            }
            json.dump(stats_dict, f, indent=2, ensure_ascii=False)
        logger.info(f"Token 统计已保存到: {token_stats_file}\n")

        logger.info(f"\n{'='*50}")
        logger.info(f" 处理完成!")
        logger.info(f"- 黄金标准: {gold_path}")
        logger.info(f"- 预测结果: {pred_path}")
        logger.info(f"- Token 统计: {token_stats_file}")
        logger.info(f"{'='*50}")


if __name__ == "__main__":
    asyncio.run(run())