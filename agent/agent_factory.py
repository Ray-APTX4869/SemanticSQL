from langchain_core.runnables import Runnable 
import logging

logger = logging.getLogger(__name__)


def create_agent(db_name: str, use_graphrag: bool = False) -> Runnable:
    """
    统一的 Agent 创建入口
    
    Args:
        db_name: 数据库名称
        use_graphrag: 是否使用 GraphRAG 增强（默认 False）
    
    Returns:
        创建好的 ReAct Agent
    """
    if use_graphrag:
        logger.info(f" 创建 GraphRAG 增强模式 Agent (数据库: {db_name})")
        from agent.agent_graphrag import create_graphrag_agent
        return create_graphrag_agent(db_name)
    else:
        logger.info(f" 创建标准模式 Agent (数据库: {db_name})")
        from agent.agent import create_react_agent_graph
        return create_react_agent_graph(db_name)