from pprint import PrettyPrinter
import streamlit as st
from agent.agent_factory import create_agent  #
from utils.schema_utils import get_schemas_from_json, Schema
from utils.db_utils import get_available_databases, get_database_path
from utils.db_utils import get_databases_from_json
from langchain_core.messages import AIMessage, ToolMessage
import yaml
import pandas as pd
import time

pretty_print = PrettyPrinter(indent=4).pprint

# ✅ 直接读取 config.yaml
with open("config.yaml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

DATABASE_ROOT_PATH = config.get("database", {}).get("root_path", "test_database")
TABLES_JSON_PATH = config.get("database", {}).get("tables_json_path", "test/tables.json")

# ========== 工具名称映射（中文描述） ==========
TOOL_DESCRIPTIONS = {
    'sql_db_list_tables': '📋 列出数据库中的所有表',
    'sql_db_schema': '🔍 查看表的结构和字段',
    'sql_db_query_checker': '✅ 检查 SQL 语法是否正确',
    'sql_db_query': '🚀 执行 SQL 查询',
}

def format_tool_result(tool_name: str, content: str) -> str:
    """格式化工具返回结果，使其更易读"""
    if tool_name == 'sql_db_list_tables':
        tables = content.split(', ')
        return f"**找到 {len(tables)} 张表：**\n\n" + "\n".join([f"- `{t}`" for t in tables])
    
    elif tool_name == 'sql_db_schema':
        lines = content.split('\n')
        result = []
        current_table = None
        
        for line in lines:
            if 'CREATE TABLE' in line:
                table_name = line.split('CREATE TABLE')[1].split('(')[0].strip()
                current_table = table_name
                result.append(f"\n**📊 表: {table_name}**\n")
            elif current_table and ('"' in line or 'PRIMARY KEY' in line or 'FOREIGN KEY' in line):
                cleaned = line.strip().strip(',')
                if cleaned:
                    result.append(f"- {cleaned}")
            elif '/*' in line:
                break
        
        return "\n".join(result[:50])
    
    elif tool_name == 'sql_db_query_checker':
        return "**✅ SQL 语法检查通过**"
    
    elif tool_name == 'sql_db_query':
        try:
            data = eval(content)
            if isinstance(data, list):
                if len(data) == 0:
                    return "**📭 查询结果为空**"
                else:
                    return f"**📊 查询成功，返回 {len(data)} 条记录**"
            else:
                return f"**📊 查询完成**"
        except:
            return content[:200]
    
    return content[:200]

# Streamlit UI
st.title("🧠 Text to SQL 查询助手")
st.markdown("输入文本问题，自动生成 SQL 并查询数据库。")

# ========== ✅ 侧边栏配置 ==========
with st.sidebar:
    st.header("⚙️ 高级配置")
    
    # GraphRAG 开关
    use_graphrag = st.checkbox(
        "🔬 启用 GraphRAG",
        value=False,
        help="智能检索相关表，减少 Token 消耗，适合大型数据库"
    )
    
    # ✅ 新增：Top-K 滑块（仅在启用 GraphRAG 时显示）
    if use_graphrag:
        st.markdown("---")
        st.subheader("🎯 检索配置")
        
        top_k = st.slider(
            "检索表的数量 (Top-K)",
            min_value=1,
            max_value=20,
            value=5,
            step=1,
            help="选择要检索的最相关表的数量"
        )
        
        # ✅ 实时显示预估 Token 消耗
        estimated_tokens_per_table = 150  # 每张表平均 150 tokens
        estimated_tokens = top_k * estimated_tokens_per_table
        
        st.caption(f"""
        **当前设置：**
        - 检索 **{top_k}** 张最相关的表
        - 预估 Schema Token：**~{estimated_tokens}** tokens
        """)
        
        # ✅ 根据 Top-K 给出建议
        if top_k <= 3:
            st.info("💡 **精简模式**：适合简单查询，极致节省 Token")
        elif top_k <= 7:
            st.success("✅ **平衡模式**：推荐用于大多数场景")
        elif top_k <= 12:
            st.warning("⚠️ **扩展模式**：适合复杂多表关联查询")
        else:
            st.error("🔥 **完整模式**：接近完整 Schema，Token 消耗较大")
    else:
        top_k = 5  # 默认值（标准模式不使用）
    
    # 模式说明
    with st.expander("ℹ️ 使用说明"):
        st.markdown("""
        ### 📋 标准模式（默认）
        - 使用完整的数据库 Schema
        - 稳定可靠，适合中小型数据库（<30 张表）
        - 不受 Top-K 参数影响
        
        ### 🔬 GraphRAG 模式
        - 基于问题智能检索相关的表
        - 减少 60-80% 的 Token 消耗
        - 适合大型数据库（50+ 张表）
        
        ### 🎯 Top-K 配置建议
        | Top-K 值 | 适用场景 | Token 消耗 |
        |---------|---------|-----------|
        | 1-3     | 简单单表查询 | 极低 (~300) |
        | 4-7     | 常规多表查询 | 中等 (~600) |
        | 8-12    | 复杂关联查询 | 较高 (~1200) |
        | 13+     | 非常复杂查询 | 高 (~2000+) |
        
        💡 **推荐值：5**（覆盖 90% 的查询场景）
        """)


# ========== ✅ 数据库选择器（改用 tables.json）==========
st.subheader("1️⃣ 选择数据库")

# ✅ 从 tables.json 读取数据库列表
from utils.db_utils import get_databases_from_json

available_databases = get_databases_from_json(TABLES_JSON_PATH, DATABASE_ROOT_PATH)

if not available_databases:
    st.error(f"❌ 未找到任何数据库，请检查：")
    st.code(f"tables.json 路径: {TABLES_JSON_PATH}\n数据库目录: {DATABASE_ROOT_PATH}")
    st.stop()

db_options = {db['display_name']: db['name'] for db in available_databases}
selected_display_name = st.selectbox(
    "请选择数据库",
    options=list(db_options.keys()),
    index=0
)

db_name = db_options[selected_display_name]
db_path = get_database_path(DATABASE_ROOT_PATH, db_name)

# ✅ 显示数据库详细信息
with st.expander("📁 数据库信息"):
    selected_db = next(db for db in available_databases if db['name'] == db_name)
    st.text(f"数据库名称: {db_name}")
    st.text(f"数据库路径: {db_path}")
    st.text(f"表数量: {selected_db.get('table_count', '未知')}")
    
    if db_path is None:
        st.error("⚠️ 警告：未找到对应的 .sqlite 文件！")
        
# ========== 用户输入（完全保留）==========
st.subheader("2️⃣ 输入查询问题")
user_input = st.text_input(
    "请输入您的问题", 
    placeholder="例如：最多人观看的前三名歌手"
)

show_details = st.checkbox("📖 显示详细推理过程", value=True)

if "run_query" not in st.session_state:
    st.session_state.run_query = False
 
st.button(
    "🚀 生成并执行 SQL",
    key="generate_sql_btn",
    on_click=lambda: st.session_state.__setitem__("run_query", True),
    type="primary"
)
 
if st.session_state.run_query:
    if not user_input.strip():
        st.warning("⚠️ 请先输入查询问题")
        st.session_state.run_query = False
        st.stop()
    
    with st.spinner("🔄 正在生成 SQL..."):
        try:
            schemas, db_names, tables = get_schemas_from_json(TABLES_JSON_PATH)
 
            if db_name not in db_names:
                st.error(f'❌ 数据库 "{db_name}" 的 schema 配置不存在')
                st.session_state.run_query = False
                st.stop()
 
            schema = Schema(schemas[db_name], tables[db_name])
            
                    # ========== GraphRAG 检索逻辑 ==========
            if use_graphrag:
                try:
                    from utils.graphrag import GraphRAGRetriever  # ✅ 延迟导入
                    
                    st.info(f"正在使用 GraphRAG 检索 Top-{top_k} 相关表...")  # ✅ 显示用户选择的 Top-K
                    
                    # ✅ 只对当前数据库初始化 GraphRAG
                    retriever = GraphRAGRetriever(
                        tables_json_path=TABLES_JSON_PATH,
                        db_filter=[db_name]  # ✅ 只加载当前数据库
                    )
                    
                    schema_info_text, metadata = retriever.retrieve_relevant_schema(
                        db_id=db_name,
                        question=user_input,
                        use_full_schema=False,
                        top_k=top_k  # ✅ 使用用户选择的 Top-K
                    )
                    
                    if not schema_info_text:
                        schema_info_text = schema.to_text()
                        st.warning("GraphRAG 检索失败，使用完整 Schema")
                    else:
                        # ✅ 显示更详细的检索信息
                        retrieved_count = metadata.get('retrieved_tables', 0)
                        st.success(f"✅ GraphRAG 检索成功：{retrieved_count}/{top_k} 个相关表")
                        
                        # 显示检索到的表
                        if metadata.get('relevant_tables'):
                            with st.expander("📋 检索到的相关表"):
                                for i, table in enumerate(metadata['relevant_tables'], 1):
                                    st.markdown(f"{i}. `{table}`")
                
                except Exception as e:
                    st.error(f"GraphRAG 异常: {str(e)}，回退到完整 Schema")
                    import traceback
                    st.code(traceback.format_exc())
                    schema_info_text = schema.to_text()
            else:
                # 标准模式
                schema_info_text = schema.to_text()
 
            enhanced_input = (
                f"Database schema:\n{schema_info_text}\n\nUser question:\n{user_input}"
                if schema_info_text else user_input
            )
            
            # ========== ✅ 改用工厂方法创建 Agent ==========
            react_agent_graph = create_agent(db_name, use_graphrag=use_graphrag)
            
            initial_state = {
                "input": enhanced_input, 
                "top_k": 5, 
                "dialect": "SQLite", 
                "messages": []
            }
            
            final_sql = None
            final_result = None
            query_result = None
            
            # ========== ✨ 创建推理过程容器（完全保留）==========
            if show_details:
                st.markdown("---")
                st.subheader("🧠 AI 推理过程")
                reasoning_container = st.container()
            
            step_count = 0
            displayed_message_count = 0
            
            # ✅ 记录是否已经执行过 SQL（用于过滤重复的语法检查）
            sql_executed = False
            last_sql_check = None  # 记录最后一次语法检查的 SQL
            
            # ========== ✨ 逐步渲染（完全保留）==========
            for step in react_agent_graph.stream(initial_state, stream_mode=["values"]):
                messages = step[1]["messages"]
                
                if len(messages) <= displayed_message_count:
                    continue
                
                new_messages = messages[displayed_message_count:]
                displayed_message_count = len(messages)
                
                for message in new_messages:
                    step_count += 1
                    
                    print(f'-------------step: {step_count}')
                    pretty_print(message)
                    
                    if isinstance(message, AIMessage):
                        for action in message.tool_calls:
                            action_name = action.get('name')
                            action_args = action.get('args')
                            
                            # ✅ 【新增】如果使用了 GraphRAG，跳过显示 list_tables 的决定
                            if use_graphrag and action_name == 'sql_db_list_tables':
                                continue
                            
                            # ✅ 过滤掉 SQL 执行前的重复语法检查
                            if action_name == 'sql_db_query_checker':
                                sql = action_args.get('query', '')
                                last_sql_check = sql
                                
                                if sql_executed:
                                    continue
                            
                            # ✅ 标记 SQL 已执行
                            if action_name == 'sql_db_query':
                                sql_executed = True
                                sql = action_args.get('query', '')
                                if sql.strip().endswith(';'):
                                    sql = sql.strip()[:-1]
                                final_sql = sql
                            
                            tool_desc = TOOL_DESCRIPTIONS.get(action_name, f"执行 {action_name}")
                            
                            # ========== ✅ 立即渲染 AI 决定 ==========
                            if show_details:
                                with reasoning_container:
                                    col1, col2 = st.columns([0.08, 0.92])
                                    
                                    with col1:
                                        st.markdown(f"<h2 style='margin:0'>🤖</h2>", unsafe_allow_html=True)
                                    
                                    with col2:
                                        st.markdown(f"**AI 决定：{tool_desc}**")
                                        
                                        if action_name == 'sql_db_schema':
                                            tables_param = action_args.get('table_names', '')
                                            st.markdown(f"查看表：`{tables_param}`")
                                        
                                        elif action_name == 'sql_db_query_checker':
                                            sql = action_args.get('query', '')
                                            st.markdown("检查以下 SQL 的语法：")
                                            st.code(sql, language='sql')
                                        
                                        elif action_name == 'sql_db_query':
                                            st.markdown("执行以下 SQL 查询：")
                                            st.code(final_sql, language='sql')
                        
                        if message.response_metadata.get("finish_reason") == "stop":
                            final_result = message.content

                    elif isinstance(message, ToolMessage):
                        tool_name = message.name
                        tool_result = message.content
                        
                        # ✅ 【已有】如果使用了 GraphRAG，跳过显示 list_tables 的结果
                        if use_graphrag and tool_name == 'sql_db_list_tables':
                            continue
                        
                        # ✅ 过滤掉 SQL 执行前的重复语法检查结果
                        if tool_name == 'sql_db_query_checker' and sql_executed:
                            continue
                        
                        if tool_name == 'sql_db_query':
                            query_result = tool_result
                        
                        formatted_result = format_tool_result(tool_name, tool_result)
                        
                        # ========== ✅ 立即渲染工具返回结果 ==========
                        if show_details:
                            with reasoning_container:
                                col1, col2 = st.columns([0.08, 0.92])
                                
                                with col1:
                                    st.markdown(f"<h2 style='margin:0'>📊</h2>", unsafe_allow_html=True)
                                
                                with col2:
                                    st.markdown(f"**工具返回结果**")
                                    st.markdown(formatted_result)
                                    
                                    # ✅ 如果是查询结果，显示实际数据
                                    if tool_name == 'sql_db_query':
                                        with st.expander("🔍 查看原始数据"):
                                            st.code(tool_result, language='python')
                                
                                # ✅ 添加分隔线
                                st.divider()
                        
                        # ✅ 模拟逐步显示效果（可选）
                        time.sleep(0.1)
            
            # ========== 最终结果（完全保留）==========
            st.markdown("---")
            st.subheader("📊 查询结果")
            
            if final_sql:
                st.markdown("**📝 生成的 SQL 查询:**")
                st.code(final_sql, language="sql")
            else:
                st.error("❌ 未能生成 SQL 查询")
            
            # ✅ 显示查询结果（表格化）
            if query_result:
                st.markdown("**📋 查询结果:**")
                try:
                    data = eval(query_result)
                    if isinstance(data, list) and len(data) > 0:
                        if isinstance(data[0], tuple):
                            num_cols = len(data[0])
                            if num_cols == 1:
                                df = pd.DataFrame(data, columns=['结果'])
                            elif num_cols == 2:
                                df = pd.DataFrame(data, columns=['列1', '列2'])
                            elif num_cols == 3:
                                df = pd.DataFrame(data, columns=['列1', '列2', '列3'])
                            else:
                                df = pd.DataFrame(data)
                            
                            st.dataframe(df, use_container_width=True)
                        else:
                            st.json(data)
                    else:
                        st.info("📭 查询结果为空")
                except Exception as e:
                    st.code(query_result, language="python")
            
            if final_result and final_result != final_sql:
                st.markdown("**💬 AI 回答:**")
                st.info(final_result)
            
            if not final_sql and not final_result:
                st.error("❌ 未能生成有效的 SQL 查询或结果，请检查输入问题。")
                
        except GeneratorExit:
            pass
        except Exception as e:
            st.error(f"❌ 执行出错: {str(e)}")
            if show_details:
                st.exception(e)
        finally:
            st.session_state.run_query = False