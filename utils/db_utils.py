# utils/db_utils.py
import os
import json
from pathlib import Path
from typing import List, Dict

def get_databases_from_json(tables_json_path: str, db_root_path: str) -> List[Dict[str, str]]:
    """
    从 tables.json 读取数据库列表
    
    Args:
        tables_json_path: tables.json 文件路径
        db_root_path: 数据库根目录路径
        
    Returns:
        List[Dict]: 包含数据库信息的列表
    """
    databases = []
    
    if not os.path.exists(tables_json_path):
        print(f"警告: tables.json 文件不存在: {tables_json_path}")
        return databases
    
    with open(tables_json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    for db in data:
        db_id = db['db_id']
        
        # 尝试找到对应的 .sqlite 文件
        db_folder = os.path.join(db_root_path, db_id)
        
        if os.path.exists(db_folder):
            sqlite_files = list(Path(db_folder).glob("*.sqlite"))
            
            if sqlite_files:
                db_file = sqlite_files[0]
                databases.append({
                    'name': db_id,
                    'path': str(db_file),
                    'display_name': f"{db_id} ({db_file.name})",
                    'table_count': len(db.get('table_names_original', []))
                })
            else:
                databases.append({
                    'name': db_id,
                    'path': None,
                    'display_name': f"{db_id} (⚠️ 未找到 .sqlite 文件)",
                    'table_count': len(db.get('table_names_original', []))
                })
        else:
            databases.append({
                'name': db_id,
                'path': None,
                'display_name': f"{db_id} (⚠️ 目录不存在)",
                'table_count': len(db.get('table_names_original', []))
            })
    
    # ✅ 按数据库名称首字母排序
    databases.sort(key=lambda x: x['name'].lower())
    
    return databases

def get_database_path(db_root_path: str, db_name: str) -> str:
    """
    根据数据库名称获取其 .sqlite 文件路径
    
    Args:
        db_root_path: 数据库根目录路径
        db_name: 数据库名称
        
    Returns:
        str: 数据库文件的完整路径，如果未找到则返回 None
    """
    db_folder = os.path.join(db_root_path, db_name)
    
    if not os.path.exists(db_folder):
        return None
    
    # 查找 .sqlite 文件
    sqlite_files = list(Path(db_folder).glob("*.sqlite"))
    
    if sqlite_files:
        return str(sqlite_files[0])
    
    return None


# ✅ 保留旧函数（兼容性）
def get_available_databases(db_root_path: str) -> List[Dict[str, str]]:
    """
    ⚠️ 已弃用：请使用 get_databases_from_json()
    """
    databases = []
    
    if not os.path.exists(db_root_path):
        print(f"警告: 数据库根目录不存在: {db_root_path}")
        return databases
    
    for item in os.listdir(db_root_path):
        item_path = os.path.join(db_root_path, item)
        
        if os.path.isdir(item_path):
            sqlite_files = list(Path(item_path).glob("*.sqlite"))
            
            if sqlite_files:
                db_file = sqlite_files[0]
                databases.append({
                    'name': item,
                    'path': str(db_file),
                    'display_name': f"{item} ({db_file.name})"
                })
    
    databases.sort(key=lambda x: x['name'])
    return databases