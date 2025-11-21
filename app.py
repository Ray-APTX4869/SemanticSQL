from pprint import PrettyPrinter
import streamlit as st
from agent.agent import create_react_agent_graph
from utils.schema_utils import get_schemas_from_json, Schema
from langchain_core.messages import AIMessage, ToolMessage

pretty_print = PrettyPrinter(indent=4).pprint

# Streamlit UI
st.title("🧠 Text to SQL 查询助手")
st.markdown("输入文本问题，自动生成 SQL 并查询数据库。")

# 用户输入
user_input = st.text_input("请输入您的问题", placeholder="例如：最多人观看的前三名歌手")
db_name = st.text_input("请输入数据库名称", placeholder="例如：concert_singer")

# 添加详细过程显示开关
show_details = st.checkbox("显示详细推理过程", value=False)

# 使用 session_state 管理一次性执行
if "run_query" not in st.session_state:
    st.session_state.run_query = False
 
st.button(
    "生成 SQL",
    key="generate_sql_btn",
    on_click=lambda: st.session_state.__setitem__("run_query", True),
)
 
if st.session_state.run_query:
    with st.spinner("🔄 正在生成 SQL..."):
        try:
            # 读取schema
            schemas, db_names, tables = get_schemas_from_json("test/tables.json")
 
            if not db_name or db_name not in db_names:
                st.warning(f'⚠️ 数据库 "{db_name}" 不存在，使用默认数据库: flight_2')
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
            initial_state = {
                "input": enhanced_input, 
                "top_k": 5, 
                "dialect": "SQLite", 
                "messages": []
            }
            
            # 用于存储结果
            final_sql = None
            final_result = None
            query_result = None
            
            # 详细过程容器（仅在开启时显示）
            if show_details:
                details_expander = st.expander("📋 详细推理过程", expanded=True)
            
            step_count = 0
            displayed_message_count = 0  # ✅ 记录已显示的消息数量
            
            # 遍历所有步骤
            for step in react_agent_graph.stream(initial_state, stream_mode=["values"]):
                messages = step[1]["messages"]
                
                # ✅ 只处理新增的消息
                if len(messages) <= displayed_message_count:
                    continue
                
                # ✅ 获取所有新消息
                new_messages = messages[displayed_message_count:]
                displayed_message_count = len(messages)
                
                # ✅ 遍历所有新消息
                for message in new_messages:
                    step_count += 1
                    
                    # 打印到控制台（调试用）
                    print(f'-------------step: {step_count}')
                    pretty_print(message)
                    
                    # ========== 只在开启详细模式时显示 ==========
                    if show_details:
                        with details_expander:
                            st.markdown(f"**步骤 {step_count}:** `{message.__class__.__name__}`")
                    
                    # 处理 AI 消息
                    if isinstance(message, AIMessage):
                        # 提取工具调用
                        for action in message.tool_calls:
                            action_name = action.get('name')
                            action_args = action.get('args')
                            
                            # 只在详细模式显示
                            if show_details:
                                with details_expander:
                                    st.text(f"🔧 执行动作: {action_name}")
                                    st.json(action_args)
                            
                            # 捕获 SQL 查询
                            if action_name == 'sql_db_query':
                                sql_query = action_args.get('query', '')
                                # 清理 SQL（去掉分号）
                                if sql_query.strip().endswith(';'):
                                    sql_query = sql_query.strip()[:-1]
                                final_sql = sql_query
                        
                        # 检查是否完成
                        if message.response_metadata.get("finish_reason") == "stop":
                            final_result = message.content
                    
                    # 处理工具消息
                    elif isinstance(message, ToolMessage):
                        # 捕获查询结果
                        if message.name == 'sql_db_query':
                            query_result = message.content
                        
                        # 只在详细模式显示
                        if show_details:
                            with details_expander:
                                st.text(f"📊 观察结果 ({message.name}):")
                                # 限制显示长度，避免界面过长
                                content_preview = message.content[:500] if len(message.content) > 500 else message.content
                                st.code(content_preview, language="python")
            
            # ========== 始终显示最终结果 ==========
            st.markdown("---")
            
            # 显示生成的 SQL
            if final_sql:
                st.subheader("📝 生成的 SQL 查询")
                st.code(final_sql, language="sql")
            else:
                st.error("❌ 未能生成 SQL 查询")
            
            # 显示查询结果（原始数据）
            if query_result:
                st.subheader("📊 查询结果")
                st.code(query_result, language="python")
            
            # 显示 AI 的最终回答
            if final_result:
                st.subheader("✅ AI 回答")
                st.success(final_result)
            
            # 错误处理
            if not final_sql and not final_result:
                st.error("❌ 未能生成有效的 SQL 查询或结果，请检查输入问题。")
                
        except GeneratorExit:
            # Streamlit 触发重跑会终止生成器，忽略该异常
            pass
        except Exception as e:
            st.error(f"❌ 执行出错: {str(e)}")
            if show_details:
                st.exception(e)
        finally:
            # 本次执行结束，复位标志
            st.session_state.run_query = False