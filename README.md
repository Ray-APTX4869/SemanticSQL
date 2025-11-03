# Text to SQL Agent

一个基于 Langchain 和 Streamlit 的自然语言转 SQL 查询Agent助手 Demo，能够将用户的自然语言问题自动转换为 SQL 查询并执行。

## 功能特点

- 支持自然语言输入，自动生成对应的 SQL 查询
- 提供友好的 Web 界面，使用 Streamlit 构建
- 支持 PostgreSQL 数据库（可基于sqlalchemy支持的数据库类型进行拓展，包括MySQL、PostgreSQL、SQLite、Oracle等）
- 提供查询执行确认机制，确保 SQL 安全性
- 可视化展示查询执行过程

## 环境要求

- Python 3.10+
- PostgreSQL 数据库和内置sqlite数据库
- 其他依赖包（见 requirements.txt）

## 安装步骤

1. 克隆项目到本地：
```bash
git clone https://github.com/botasky11/text_to_sql_agent_6000R.git
cd text_to_sql_agent_6000R
```

2. 创建并激活虚拟环境（推荐）：
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
.\venv\Scripts\activate  # Windows
```

3. 安装依赖包：
```bash
pip install -r requirements.txt
```

4. 配置环境变量：
   创建 `.env` 文件并添加以下配置：
   ```bash
   # LLM API配置
   model=your_model_name        # 例如：gpt-3.5-turbo
   api_key=your_api_key        # 你的API密钥
   base_url=your_base_url      # API基础URL（如果使用自定义API端点）
   ```

5. 配置数据库连接：
   
   a. 创建 `config.yaml` 文件并配置数据库连接信息：
   ```yaml
   db_url: "postgresql+psycopg2://username:password@localhost:5432/database_name"
   max_tokens: 20000
   temperature: 0.2
   model_path: "defog/sqlcoder-7b-2"
   ```

   b. 数据库连接URL格式说明：
   - `postgresql+psycopg2://`: 数据库驱动类型
   - `username`: 数据库用户名
   - `password`: 数据库密码
   - `localhost`: 数据库主机地址
   - `5432`: 数据库端口号
   - `database_name`: 数据库名称

   c. 确保数据库已正确安装并运行：
   ```bash
   # 检查PostgreSQL服务状态
   sudo service postgresql status  # Linux
   # 或
   brew services list  # MacOS
   ```

   d. 创建数据库和用户（如果尚未创建）：
   ```sql
   CREATE DATABASE database_name;
   CREATE USER username WITH PASSWORD 'password';
   GRANT ALL PRIVILEGES ON DATABASE database_name TO username;
   ```

## 运行应用

1. 启动 Streamlit 应用：
```bash
streamlit run app.py
```

2. 在浏览器中访问：`http://localhost:8501`

## 使用说明

1. 在输入框中输入自然语言问题，例如："每个产品的总销量是多少？"
2. 点击"生成 SQL"按钮
3. 系统会显示生成的 SQL 查询
4. 确认是否执行 SQL 查询
5. 查看查询结果

## 项目结构

```
text_to_sql_agent_6000R/
├── app.py              # 主应用文件
├── app_chains.py       # 基于 LangChain 的应用实现
├── agent/             # Agent 相关代码
│   ├── agent.py
│   └── agent_chains.py
├── utils/             # 工具函数
│   ├── schema_utils.py
│   └── prompt.py
├── .env              # 环境变量配置文件
├── config.yaml       # 数据库和模型配置文件
└── requirements.txt    # 项目依赖
```

## 测试数据库（test_database）

项目内置 `test_database` 目录，包含多套示例数据库（每个子目录是一套独立的 SQLite 数据库），便于本地体验与评测：

- 每个子目录通常包含：
  - `.sqlite`：SQLite 数据文件
  - `schema.sql`：该数据库的建表与 schema 定义
- 示例：`test_database/concert_singer/concert_singer.sqlite`

使用方式（将应用连接到某个测试数据库）：

1. 在 `config.yaml` 里设置 `db_url` 指向目标 SQLite 文件。例如：
   ```yaml
   db_url: "sqlite:///test_database/customers_and_orders/customers_and_orders.sqlite"
   # 或使用绝对路径（推荐）
   # db_url: "sqlite:////Users/yourname/path/text_to_sql_agent_6000R/test_database/concert_singer/concert_singer.sqlite"
   ```
2. 启动应用或运行离线脚本时，将使用该数据库进行 schema 解析与 SQL 执行。

小贴士：`db_url` 可替换为任意 sqlalchemy 支持的数据库连接串（如 PostgreSQL/MySQL 等）。

## 批量生成 SQL 与评测（generate_sql.py）

`generate_sql.py` 用于离线批量生成 SQL，并与标准答案进行对照输出，便于快速评测模型表现：

- 输入：`test/dev.sql` 中的问答对，格式为成对出现的行：
  - `Question ... ||| <db_name>`
  - `SQL: <gold_sql>`（黄金标准）
- 目标库选择：脚本内的 `db_name` 参数（默认 `flight_2`）决定本次评测使用的数据库名称，应与 `test_database/<db_name>` 对应，并确保 `config.yaml` 的 `db_url` 指向该库的 `.sqlite` 文件。
- 输出：
  - `test/gold_example_<db_name>.txt`：黄金标准 SQL 列表
  - `test/pred_example_<db_name>.txt`：模型生成的 SQL 列表
  - `test/errors.log`：可选，运行过程中产生的错误摘要
  - `logs/text_to_sql_generate_sql_YYYYMMDD.log`：详细运行日志

使用步骤：

1. 配置 LLM 接入：在 `.env` 中填写 `model`、`api_key`、`base_url`（如需）。
2. 在 `config.yaml` 中设置 `db_url` 指向要评测的 SQLite 数据库（见上文）。
3. 打开 `generate_sql.py`，根据需要设置：
   - `db_name`：与 `test_database` 中的数据库目录同名，例如 `concert_singer`、`flight_2` 等。
   - 可选：请求参数 `top_k`（默认 5）、`dialect`（默认 `SQLite`）在代码的 `QueryRequest` 中定义，可按需调整。
4. 运行：
   ```bash
   python generate_sql.py
   ```
5. 查看输出文件位于 `test/` 目录下，以及日志位于 `logs/` 目录。

注意：脚本会确保生成 SQL 末尾不包含分号，以便后续对齐评测。

## 开发说明

- `app.py`: 使用基础的 LangChain，Streamlit 实现
- `app_chains.py`: 使用 LangGraph 有状态实现，提供human-in-loop 更强大的交互功能

### Few-shot 示例（agent/agent.py）

在 `agent/agent.py` 中预置了若干条 few-shot 示例（“自然语言输入 → SQL” 对）。这些示例通过语义相似度动态检索的方式被拼接进系统提示，帮助模型学习期望的 SQL 书写风格与结构，从而提升生成的稳定性与准确性。

- 机制：
  - 使用 `OpenAIEmbeddings`（`text-embedding-3-large`）对用户输入与示例进行向量化。
  - 借助 `FAISS` 与 `SemanticSimilarityExampleSelector`，从示例集中按语义相似度选取最多 `k=5` 条最相关示例。
  - 选出的示例与系统前缀 `SYSTEM_PREFIX` 一起组成 `FewShotPromptTemplate`，作为 Agent 的系统提示输入模型。

- 作用：
  - 提升 SQL 生成的一致性，减少聚合、连接、排序等常见模式的逻辑错误。
  - 对齐输出风格（如 `ORDER BY ... NULLS LAST`、`LIMIT` 用法等），更贴近期望的查询模板。

- 自定义与调整：
  - 在 `agent/agent.py` 的 `examples` 列表中添加/修改你领域内的高质量示例即可定制行为。
  - 通过 `k` 参数控制每次纳入提示的示例条数（当前为 `k=5`）。
  - 如需临时关闭 few-shot，可将系统提示改为仅使用 `SYSTEM_PREFIX`（不拼接示例），或将示例列表清空。

- 依赖与配置：
  - 需要在 `.env` 中配置 `api_key` 以使用嵌入模型；`model`/`base_url` 按你的 LLM 服务配置。

## 注意事项

- 确保数据库连接信息正确配置
- 建议在开发环境中使用测试数据库
- 注意 SQL 注入风险，建议添加适当的输入验证
- 请妥善保管 API 密钥，不要将其提交到版本控制系统中
- 建议使用环境变量或配置文件来管理敏感信息
- 确保数据库用户具有适当的权限
- 定期备份数据库

## 贡献指南

欢迎提交 Issue 和 Pull Request 来帮助改进项目。

## 许可证

[添加许可证信息]