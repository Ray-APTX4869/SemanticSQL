"""
GraphRAG module for Text-to-SQL task
构建数据库 schema 的图结构,并基于用户问题检索相关的 schema 信息

优化内容：
1. 延迟加载：只在需要时加载指定数据库
2. 使用 Keyword Matching + Embedding 混合检索
3. 移除 Emoji，解决 Windows GBK 编码问题
"""
import json
import networkx as nx
from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict
import numpy as np
from langchain_openai import OpenAIEmbeddings
import os
from dotenv import load_dotenv
import logging
from sklearn.metrics.pairwise import cosine_similarity
import re

load_dotenv()
logger = logging.getLogger(__name__)


class SchemaGraph:
    """数据库 Schema 图结构"""
    
    def __init__(self, db_id: str, tables_data: Dict, embeddings: OpenAIEmbeddings):
        self.db_id = db_id
        self.graph = nx.DiGraph()
        self.tables = {}
        self.columns = {}
        self.foreign_keys = []
        self.embeddings = embeddings
        
        # 存储 Embedding 向量
        self.table_embeddings = {}
        self.column_embeddings = {}
        
        self._build_graph(tables_data)
        self._compute_embeddings()
    
    def _build_graph(self, tables_data: Dict):
        """从 tables.json 数据构建图结构"""
        column_names_original = tables_data.get('column_names_original', [])
        table_names_original = tables_data.get('table_names_original', [])
        foreign_keys = tables_data.get('foreign_keys', [])
        
        # 添加表节点
        for i, table_name in enumerate(table_names_original):
            table_name_lower = table_name.lower()
            self.graph.add_node(f"table_{i}", 
                              type="table", 
                              name=table_name_lower,
                              original_name=table_name)
            self.tables[table_name_lower] = {
                'id': i,
                'name': table_name_lower,
                'original_name': table_name,
                'columns': []
            }
        
        # 添加列节点和边
        for col_idx, (table_id, col_name) in enumerate(column_names_original):
            if table_id == -1:
                continue
            
            table_name = table_names_original[table_id].lower()
            col_name_lower = col_name.lower()
            col_node_id = f"col_{col_idx}"
            
            self.graph.add_node(col_node_id,
                              type="column",
                              name=col_name_lower,
                              original_name=col_name,
                              table_id=table_id)
            
            self.graph.add_edge(f"table_{table_id}", col_node_id, 
                              relation="has_column")
            
            if table_name not in self.columns:
                self.columns[table_name] = []
            self.columns[table_name].append({
                'id': col_idx,
                'name': col_name_lower,
                'original_name': col_name
            })
            self.tables[table_name]['columns'].append(col_name_lower)
        
        # 添加外键关系
        for fk in foreign_keys:
            col1_idx, col2_idx = fk
            col1_info = column_names_original[col1_idx]
            col2_info = column_names_original[col2_idx]
            
            table1_id, col1_name = col1_info
            table2_id, col2_name = col2_info
            
            if table1_id != -1 and table2_id != -1:
                table1_name = table_names_original[table1_id].lower()
                table2_name = table_names_original[table2_id].lower()
                
                self.graph.add_edge(f"table_{table1_id}", f"table_{table2_id}",
                                  relation="foreign_key",
                                  from_column=col1_name.lower(),
                                  to_column=col2_name.lower())
                
                self.foreign_keys.append({
                    'from_table': table1_name,
                    'from_column': col1_name.lower(),
                    'to_table': table2_name,
                    'to_column': col2_name.lower()
                })
    
    def _compute_embeddings(self):
        """计算所有表名和列名的 Embedding 向量"""
        logger.info(f"[计算] {self.db_id} 数据库的 Schema Embeddings...")
        
        # 计算表名 Embeddings
        table_texts = []
        table_names = []
        for table_name, table_info in self.tables.items():
            # 将表名和列名组合成文本
            text = f"{table_name} columns: {', '.join(table_info['columns'])}"
            table_texts.append(text)
            table_names.append(table_name)
        
        if table_texts:
            table_vecs = self.embeddings.embed_documents(table_texts)
            for name, vec in zip(table_names, table_vecs):
                self.table_embeddings[name] = np.array(vec)
        
        logger.info(f"[完成] {len(self.table_embeddings)} 个表的 Embeddings")
    
    def _compute_keyword_scores(self, question: str) -> Dict[str, float]:
        """
        基于关键词匹配计算分数
        
        匹配规则：
        1. 表名精确匹配：1.0
        2. 表名部分匹配：0.7
        3. 列名精确匹配：0.8
        4. 列名部分匹配：0.5
        """
        question_lower = question.lower()
        # 提取所有单词（去除标点）
        question_words = set(re.findall(r'\b\w+\b', question_lower))
        
        scores = {}
        
        for table_name, table_info in self.tables.items():
            score = 0.0
            
            # 1. 表名匹配
            table_words = set(re.findall(r'\b\w+\b', table_name))
            
            # 精确匹配（整个表名出现在问题中）
            if table_name in question_lower:
                score += 1.0
            # 部分匹配（表名的任意单词出现）
            elif table_words & question_words:
                score += 0.7
            
            # 2. 列名匹配
            column_match_scores = []
            for col in table_info['columns']:
                col_words = set(re.findall(r'\b\w+\b', col))
                
                if col in question_lower:
                    column_match_scores.append(0.8)
                elif col_words & question_words:
                    column_match_scores.append(0.5)
            
            # 取最高的列匹配分数
            if column_match_scores:
                score += max(column_match_scores)
            
            scores[table_name] = score
        
        # 归一化到 [0, 1]
        max_score = max(scores.values()) if scores else 1.0
        if max_score > 0:
            scores = {k: v / max_score for k, v in scores.items()}
        
        return scores
    
    def get_relevant_tables_hybrid(self, question: str, top_k: int = 5,
                                   keyword_weight: float = 0.4,
                                   embedding_weight: float = 0.6) -> Tuple[List[str], Dict[str, float]]:
        """
        使用 Keyword + Embedding 混合检索获取相关表
        
        Args:
            question: 用户问题
            top_k: 返回前 K 个表
            keyword_weight: 关键词匹配权重
            embedding_weight: Embedding 语义权重
        """
        logger.info(f"[检索] 混合检索相关表 (Keyword={keyword_weight}, Embedding={embedding_weight})")
        logger.info(f"[问题] {question}")
        
        # 1. 关键词匹配分数
        keyword_scores = self._compute_keyword_scores(question)
        
        # 2. Embedding 语义分数
        question_vec = np.array(self.embeddings.embed_query(question))
        embedding_scores = {}
        for table_name, table_vec in self.table_embeddings.items():
            similarity = cosine_similarity(
                question_vec.reshape(1, -1), 
                table_vec.reshape(1, -1)
            )[0][0]
            embedding_scores[table_name] = float(similarity)
        
        # 3. 加权融合
        hybrid_scores = {}
        for table_name in self.tables.keys():
            kw_score = keyword_scores.get(table_name, 0.0)
            emb_score = embedding_scores.get(table_name, 0.0)
            hybrid_scores[table_name] = (
                keyword_weight * kw_score + embedding_weight * emb_score
            )
        
        # 4. 基于外键关系传播分数（权重 0.3）
        propagated_scores = hybrid_scores.copy()
        for fk in self.foreign_keys:
            from_table = fk['from_table']
            to_table = fk['to_table']
            if from_table in hybrid_scores:
                propagated_scores[to_table] = max(
                    propagated_scores.get(to_table, 0),
                    hybrid_scores[from_table] * 0.3
                )
            if to_table in hybrid_scores:
                propagated_scores[from_table] = max(
                    propagated_scores.get(from_table, 0),
                    hybrid_scores[to_table] * 0.3
                )
        
        # 5. 返回 top_k 表
        sorted_tables = sorted(propagated_scores.items(), key=lambda x: x[1], reverse=True)
        top_tables = [table for table, _ in sorted_tables[:top_k]]
        
        # 日志输出
        logger.info(f"[完成] 检索到 {len(top_tables)} 个相关表:")
        for table, score in sorted_tables[:top_k]:
            kw = keyword_scores.get(table, 0)
            emb = embedding_scores.get(table, 0)
            logger.info(f"   - {table}: 总分={score:.4f} (KW={kw:.4f}, Emb={emb:.4f})")
        
        return top_tables, propagated_scores
    
    def get_schema_subgraph(self, table_names: List[str]) -> str:
        """获取子图的 schema 文本表示"""
        schema_text = []
        visited_tables = set()
        
        # 添加直接相关的表
        for table_name in table_names:
            if table_name in self.tables:
                visited_tables.add(table_name)
                table_info = self.tables[table_name]
                cols = ", ".join(table_info['columns'])
                schema_text.append(f"{table_name}: {cols}")
        
        # 添加通过外键连接的邻居表
        for fk in self.foreign_keys:
            from_table = fk['from_table']
            to_table = fk['to_table']
            
            if from_table in visited_tables and to_table not in visited_tables:
                if to_table in self.tables:
                    visited_tables.add(to_table)
                    table_info = self.tables[to_table]
                    cols = ", ".join(table_info['columns'])
                    schema_text.append(f"{to_table}: {cols}")
            elif to_table in visited_tables and from_table not in visited_tables:
                if from_table in self.tables:
                    visited_tables.add(from_table)
                    table_info = self.tables[from_table]
                    cols = ", ".join(table_info['columns'])
                    schema_text.append(f"{from_table}: {cols}")
        
        logger.info(f"[子图] 包含 {len(visited_tables)} 个表: {', '.join(visited_tables)}")
        return "\n".join(schema_text)
    
    def get_full_schema(self) -> str:
        """获取完整的 schema 文本"""
        schema_text = []
        for table_name, table_info in self.tables.items():
            cols = ", ".join(table_info['columns'])
            schema_text.append(f"{table_name}: {cols}")
        return "\n".join(schema_text)


class GraphRAGRetriever:
    """基于图的检索器（延迟加载版本）"""
    
    def __init__(self, tables_json_path: str, db_filter: Optional[List[str]] = None):
        """
        初始化 GraphRAG 检索器
        
        Args:
            tables_json_path: tables.json 路径
            db_filter: 只加载指定的数据库列表（如 ['concert_singer']），None 表示加载所有
        """
        self.tables_json_path = tables_json_path
        self.db_filter = db_filter
        self.schema_graphs: Dict[str, SchemaGraph] = {}
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-large",
            base_url=os.getenv("base_url"),
            openai_api_key=os.getenv("api_key")
        )
        self._load_schemas()
    
    def _load_schemas(self):
        """从 tables.json 加载指定数据库的 schema 图"""
        logger.info(f"[加载] 从 {self.tables_json_path} 加载 Schema...")
        
        with open(self.tables_json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        for entry in data:
            db_id = entry['db_id']
            
            if self.db_filter and db_id not in self.db_filter:
                continue
            
            logger.info(f"[加载] 正在加载数据库: {db_id}")
            self.schema_graphs[db_id] = SchemaGraph(db_id, entry, self.embeddings)
        
        logger.info(f"[完成] 加载完成: {len(self.schema_graphs)} 个数据库")
    
    def retrieve_relevant_schema(self, db_id: str, question: str, 
                                 use_full_schema: bool = False,
                                 top_k: int = 5,
                                 keyword_weight: float = 0.4,
                                 embedding_weight: float = 0.6) -> Tuple[str, Dict]:
        """
        基于用户问题检索相关的 schema 信息
        
        Args:
            db_id: 数据库 ID
            question: 用户问题
            use_full_schema: 如果为 True，返回完整 schema
            top_k: 检索前 K 个相关表
            keyword_weight: 关键词权重
            embedding_weight: Embedding 权重
        
        Returns:
            (schema 文本, 检索元数据)
        """
        if db_id not in self.schema_graphs:
            logger.warning(f"[警告] 未找到数据库 {db_id}")
            return "", {"error": "database not found"}
        
        graph = self.schema_graphs[db_id]
        
        if use_full_schema:
            logger.info(f"[完整] 使用完整 Schema (数据库: {db_id})")
            return graph.get_full_schema(), {"mode": "full_schema"}
        
        # 使用混合检索
        relevant_tables, scores = graph.get_relevant_tables_hybrid(
            question, 
            top_k=top_k,
            keyword_weight=keyword_weight,
            embedding_weight=embedding_weight
        )
        
        if not relevant_tables:
            logger.warning(f"[警告] 未检索到相关表，回退到完整 Schema")
            return graph.get_full_schema(), {
                "mode": "fallback_full_schema",
                "reason": "no relevant tables found"
            }
        
        # 返回子图 schema
        schema_text = graph.get_schema_subgraph(relevant_tables)
        
        metadata = {
            "mode": "hybrid_retrieval",
            "relevant_tables": relevant_tables,
            "scores": {table: scores[table] for table in relevant_tables},
            "total_tables": len(graph.tables),
            "retrieved_tables": len(relevant_tables),
            "weights": {
                "keyword": keyword_weight,
                "embedding": embedding_weight
            }
        }
        
        return schema_text, metadata
    
    def get_foreign_key_hints(self, db_id: str) -> str:
        """获取外键关系提示"""
        if db_id not in self.schema_graphs:
            return ""
        
        graph = self.schema_graphs[db_id]
        hints = []
        
        for fk in graph.foreign_keys:
            hint = (f"{fk['from_table']}.{fk['from_column']} -> "
                   f"{fk['to_table']}.{fk['to_column']}")
            hints.append(hint)
        
        if hints:
            return "Foreign key relationships:\n" + "\n".join(hints)
        return ""