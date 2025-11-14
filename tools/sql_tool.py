from langchain_core.tools import tool
from sqlalchemy import text
import pandas as pd
from utils.schema_utils import engine
import re


@tool("sql_runner")
def run_sql(query: str) -> str:
    """
    Execute SQL query and return the result as a markdown table.
    """
    try:
        with engine.connect() as conn:
            # 清理SQL查询，去除代码块标记
            if query.startswith('```sql') and query.endswith('```'):
                query = query[7:-3].strip()
            elif query.startswith('```') and query.endswith('```'):
                query = query[3:-3].strip()
            
            # 执行SQL查询
            df = pd.read_sql_query(query, conn)
            
            # 将结果转换为Markdown表格格式
            if len(df) == 0:
                return "查询结果为空"
            
            # 将DataFrame转换为markdown表格字符串
            markdown_table = df.head(10).to_markdown(index=False)
            return markdown_table
    except Exception as e:
        return f"[ERROR]: {str(e)}"
    

# 格式化SQL查询结果为单行 SQL 语句
def sql_format(file_name: str):
    """
    将文件中的每个 SQL 语句（可能为多行）合并为一行，并以换行分隔各语句。
    通过检测以 SELECT/WITH/INSERT/UPDATE/DELETE 开头的行来分割语句。
    """
    with open(f"test/{file_name}.txt", 'r', encoding='utf-8') as f:
        lines = f.readlines()

    statements = []
    current_parts = []

    def finalize_current():
        if not current_parts:
            return
        stmt = ' '.join(current_parts)
        # 去除行内注释与多余空白
        stmt = re.sub(r'--.*', '', stmt)
        stmt = re.sub(r'/\\*.*?\\*/', '', stmt, flags=re.DOTALL)
        stmt = re.sub(r'\s+', ' ', stmt).strip()
        # 去除末尾分号
        if stmt.endswith(';'):
            stmt = stmt[:-1].strip()
        if stmt:
            statements.append(stmt)

    for raw in lines:
        line = raw.rstrip()
        if not line:
            continue
        # 跳过 markdown 代码块标记
        if line.startswith('```'):
            continue
        # 如果检测到新语句起始且当前已收集内容，则先收尾当前语句
        if re.match(r'^(SELECT|WITH|INSERT|UPDATE|DELETE)\b', line, flags=re.IGNORECASE) and current_parts:
            finalize_current()
            current_parts = [line]
        else:
            current_parts.append(line)

    # 处理最后一条语句
    finalize_current()

    # 以换行分隔输出，每条 SQL 占一行
    if statements:
        with open(f"test/{file_name}_format.txt", "w", encoding='utf-8') as f:
            f.write('\n'.join(statements) + '\n')
    return True
