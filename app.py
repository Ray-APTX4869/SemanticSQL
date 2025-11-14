import streamlit as st
from agent.agent import create_react_agent_graph
from utils.schema_utils import get_schemas_from_json, Schema
from utils.prompt import prompt, build_prompt
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage,ToolMessage
from generate_sql import QueryResponse


# Streamlit UI
st.title("🧠 Text to SQL 查询助手")
st.markdown("输入文本问题，自动生成 SQL 并查询数据库。")

user_input = st.text_input("请输入您的问题，例如：'Which airports do not have departing or arriving flights?'")
db_name = st.text_input("请输入数据库名称，例如：'flight_2'")
# print(prompt_val.messages.pretty_print())

# 使用 session_state 管理一次性执行，避免因 Streamlit 重跑导致的重复执行/GeneratorExit
if "run_query" not in st.session_state:
    st.session_state.run_query = False
 
st.button(
    "生成 SQL",
    key="generate_sql_btn",
    on_click=lambda: st.session_state.__setitem__("run_query", True),
)
 
if st.session_state.run_query:
    with st.spinner("正在生成 SQL..."):
        try:
            # 读取schema
            schemas, db_names, tables = get_schemas_from_json("test/tables.json")
 
            if not db_name or db_name not in db_names:
                print(f'db_name: {db_name} not in db_names, use default db_name: flight_2')
                db_name = "flight_2"
 
            schema = Schema(schemas[db_name], tables[db_name])
            schema_info_text = schema.to_text()
 
            enhanced_input = (
                f"Database schema:\n{schema_info_text}\n\nUser question:\n{user_input}"
                if schema_info_text else user_input
            )
            # 创建react agent graph
            react_agent_graph = create_react_agent_graph(db_name)
            # 初始化状态
            initial_state = {"input": enhanced_input, "top_k": 5, "dialect": "SQLite", "messages": []}
            i = 0
            for step in react_agent_graph.stream(initial_state, stream_mode=["values"]):
                message = step[1]["messages"]
                if len(message) > 0:
                    message = message[-1]
                print(f'-------------step: {i}')
                i += 1
                if isinstance(message, AIMessage):
                    # 处理动作（如调用工具）
                    for action in message.tool_calls:
                        st.text(f"执行动作: {action.get('name')}，输入: {action.get('args')}")
                        if action.get('name') == 'sql_db_query':
                            sql_query = action.get('args', {}).get('query')
                            # 如果SQL查询以分号结尾，则去掉分号
                            if sql_query and sql_query.strip().endswith(';'):
                                sql_query = sql_query.strip()[:-1]
                                response = QueryResponse(steps=[])
                                response.sql_query = sql_query
                                st.text(f"执行动作SQL查询: {response.get_format_sql_query()}")
                    if message.response_metadata.get("finish_reason") == "stop":
                        st.success("查询成功，结果如下：")
                        st.text(message.content)
                elif isinstance(message, ToolMessage):
                    # 处理观察结果
                    st.text(f"观察结果: {message.content}")
                st.text(message)
        except GeneratorExit:
            # Streamlit 触发重跑会终止生成器，忽略该异常以避免报错
            pass
        finally:
            # 本次执行结束，复位标志
            st.session_state.run_query = False