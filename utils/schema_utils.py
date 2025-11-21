import streamlit as st
import yaml
from sqlalchemy import create_engine, text
import pandas as pd
import json
import sqlite3


# 加载配置
with open("config.yaml", "r",encoding="utf-8") as f:
    config = yaml.safe_load(f)

engine = create_engine(config["db_url"])

# 提取数据库 Schema
@st.cache_data
def extract_schema():
    with engine.connect() as conn:
        table_names = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")).fetchall()
        schema = ""
        for table in table_names:
            table_name = table[0]
            columns = conn.execute(text(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table_name}'")).fetchall()
            col_info = ", ".join([f"{col[0]} ({col[1]})" for col in columns])
            schema += f"表 {table_name} 包含字段: {col_info}\n"
        return schema

# 执行 SQL
def execute_sql(sql_query):
    with engine.connect() as conn:
        result = conn.execute(text(sql_query))
        df = pd.DataFrame(result.fetchall(), columns=result.keys())
    return df


class Schema:
    """
    Simple schema which maps table&column to a unique identifier
    """
    def __init__(self, schema, table):
        self._schema = schema
        self._table = table
        self._idMap = self._map(self._schema, self._table)

    @property
    def schema(self):
        return self._schema

    @property
    def idMap(self):
        return self._idMap

    def _map(self, schema, table):
        column_names_original = table['column_names_original']
        table_names_original = table['table_names_original']
        #print 'column_names_original: ', column_names_original
        #print 'table_names_original: ', table_names_original
        for i, (tab_id, col) in enumerate(column_names_original):
            if tab_id == -1:
                idMap = {'*': i}
            else:
                key = table_names_original[tab_id].lower()
                val = col.lower()
                idMap[key + "." + val] = i

        for i, tab in enumerate(table_names_original):
            key = tab.lower()
            idMap[key] = i

        return idMap
    
    def to_text(self):
        schema_info_text = ""
        if self._schema:
            try:
                lines = []
                for table_name, columns in self._schema.items():
                    if isinstance(columns, (list, tuple)):
                        cols_str = ", ".join(columns)
                    elif isinstance(columns, dict):
                        cols_str = ", ".join(columns.keys())
                    else:
                        cols_str = str(columns)
                    lines.append(f"{table_name}: {cols_str}")
                schema_info_text = "\n".join(lines)
            except Exception as _:
                schema_info_text = ""
        return schema_info_text
    
    def to_json(self):
        return json.dumps(self._schema, ensure_ascii=False)

def get_schema(db):
    """
    Get database's schema, which is a dict with table name as key
    and list of column names as value
    :param db: database path
    :return: schema dict
    """

    schema = {}
    conn = sqlite3.connect(db)
    cursor = conn.cursor()

    # fetch table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [str(table[0].lower()) for table in cursor.fetchall()]

    # fetch table info
    for table in tables:
        cursor.execute("PRAGMA table_info({})".format(table))
        schema[table] = [str(col[1].lower()) for col in cursor.fetchall()]

    return schema

def get_schema_from_json_one(fpath):
    with open(fpath) as f:
        data = json.load(f)

    schema = {}
    for entry in data:
        table = str(entry['table'].lower())
        cols = [str(col['column_name'].lower()) for col in entry['col_data']]
        schema[table] = cols

    return schema


def get_schemas_from_json(fpath):
    with open(fpath) as f:
        data = json.load(f)
    db_names = [db['db_id'] for db in data]

    tables = {}
    schemas = {}
    for db in data:
        db_id = db['db_id']
        schema = {} #{'table': [col.lower, ..., ]} * -> __all__
        column_names_original = db['column_names_original']
        table_names_original = db['table_names_original']
        tables[db_id] = {'column_names_original': column_names_original, 'table_names_original': table_names_original}
        for i, tabn in enumerate(table_names_original):
            table = str(tabn.lower())
            cols = [str(col.lower()) for td, col in column_names_original if td == i]
            schema[table] = cols
        schemas[db_id] = schema

    return schemas, db_names, tables


if __name__ == '__main__':
    
    sql = "SELECT name ,  country ,  age FROM singer ORDER BY age DESC"
    db_id = "flight_2"
    table_file = "test/tables.json"
    
    schemas, db_names, tables = get_schemas_from_json(table_file)
    schema = schemas[db_id]
    table = tables[db_id]
    schema = Schema(schema, table)
    print(f"dbnames: {db_names}")
    print(f"schema: {schema.to_text()}")