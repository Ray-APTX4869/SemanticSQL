# SemanticSQL

> LLM-driven semantic-to-SQL orchestration engine with human-in-the-loop control

SemanticSQL 是一个将自然语言描述自动转化为可执行 SQL 查询的智能代理系统。项目基于 LangChain 生态构建，支持多种数据库驱动、流式交互界面及批量评测流程，适合在简历中突出端到端 LLM 应用落地的技术能力。

## 核心亮点

- **语义解析到 SQL 自动化**：利用检索增强提示（GraphRAG + FAISS）与 Few-shot Prompt Template，将业务问题映射为高质量 SQL。
- **多代理工作流**：`agent/` 模块封装决策代理、人工确认环节以及错误恢复策略，便于扩展和集成。
- **流式可视化界面**：通过 Streamlit 快速搭建 Demo，展示 SQL 生成、人工确认与结果渲染的全链路。
- **离线评测与日志体系**：`generate_sql.py` + `logs/` 记录每次生成过程，可对照黄金 SQL 评估准确率。
- **可插拔数据库连接**：以 SQLAlchemy 为抽象层，可平滑切换到 PostgreSQL / MySQL / SQLite 等不同数据源。

## 目录结构速览

```
SemanticSQL/
├── app.py                 # Streamlit 主入口
├── app_chains.py          # LangGraph 状态机工作流
├── agent/                 # Agent 逻辑（多模态链路、人工确认）
├── tools/sql_tool.py      # SQL 执行与安全控制
├── utils/                 # Prompt、Schema 解析、GraphRAG 辅助
├── test_database/         # 示例数据库（SQLite）
├── test/                  # Gold / Pred SQL 以及评测报告
├── logs/                  # 运行日志
├── config.yaml            # 全局配置
├── requirements.txt
└── README.md
```

## 快速开始

1. **克隆仓库**
   ```bash
   git clone https://github.com/Ray-APTX4869/SemanticSQL.git
   cd SemanticSQL
   ```
2. **创建虚拟环境（推荐）**
   ```bash
   python -m venv .venv
   source .venv/bin/activate       # Linux / macOS
   # 或
   .\.venv\Scripts\activate        # Windows
   ```
3. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```
4. **配置 LLM 与数据库**
   - 在根目录创建 `.env`，写入：
     ```
     model=your-llm-id
     api_key=your-api-key
     base_url=https://api.openai.com/v1
     ```
   - 根据实际数据源调整 `config.yaml` 中的 `db_url`（默认指向内置 SQLite 示例库）。

## 运行方式

- **可视化体验**
  ```bash
  streamlit run app.py
  ```
  浏览器访问 `http://localhost:8501`，输入自然语言问题，审阅模型生成的 SQL，并选择是否执行。

- **批量评测**
  ```bash
  python generate_sql.py
  ```
  读取 `test/dev.sql` 中的问答对，生成预测 SQL，与 `test/gold_*` 文件对比，并写入日志。

## 技术栈

- LLM Orchestration：LangChain、LangGraph、FAISS、GraphRAG
- 前端交互：Streamlit
- 数据访问：SQLAlchemy、SQLite / PostgreSQL / MySQL（可扩展）
- 日志与评测：Python logging、Spider Eval 工具链

## 简历要点参考

- 设计并实现 “语义检索 + Few-shot Prompt + 人工确认” 的 SQL 生成流水线，显著提升结果可解释性与安全性。
- 集成多种数据库后端，通过配置驱动方式快速切换环境，支持本地示例库与生产数据库。
- 构建批量评测框架，自动化记录预测 SQL、误差日志和准确率指标，为模型调优提供数据依据。

## 许可证

本项目遵循 [Apache License 2.0](LICENSE)。