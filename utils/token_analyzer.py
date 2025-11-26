# utils/token_analyzer.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Token 使用分析工具
"""

import json
import os
from typing import Dict, List
from collections import defaultdict

def load_token_stats(db_name: str) -> Dict:
    """加载 token 统计文件"""
    stats_file = f"test/token_stats_{db_name}.json"
    if os.path.exists(stats_file):
        with open(stats_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def print_token_summary(db_names: List[str]):
    """打印多个数据库的 token 统计摘要"""
    print("="*80)
    print("Token 使用统计汇总")
    print("="*80)
    
    all_stats = defaultdict(lambda: {
        "total_queries": 0,
        "total_prompt_tokens": 0,
        "total_completion_tokens": 0,
        "total_tokens": 0,
        "databases": []
    })
    
    # 用于计算所有数据库的总体统计
    grand_total_queries = 0
    grand_total_prompt_tokens = 0
    grand_total_completion_tokens = 0
    grand_total_tokens = 0
    
    for db_name in db_names:
        stats = load_token_stats(db_name)
        if not stats:
            print(f"\n【{db_name}】- 无统计数据")
            continue
        
        # 计算当前数据库的总体统计
        db_total_queries = 0
        db_total_prompt_tokens = 0
        db_total_completion_tokens = 0
        db_total_tokens = 0
        
        print(f"\n【{db_name}】")
        for hardness in ['easy', 'medium', 'hard', 'extra']:
            if hardness in stats:
                h_stats = stats[hardness]
                print(f"  {hardness:8s}: {h_stats['avg_tokens']:8.1f} tokens/query "
                      f"({h_stats['total_queries']} queries, {h_stats['total_tokens']:,} total)")
                
                # 累加当前数据库的统计
                db_total_queries += h_stats["total_queries"]
                db_total_prompt_tokens += h_stats.get("total_prompt_tokens", 0)
                db_total_completion_tokens += h_stats.get("total_completion_tokens", 0)
                db_total_tokens += h_stats["total_tokens"]
                
                # 累加所有数据库的统计
                all_stats[hardness]["total_queries"] += h_stats["total_queries"]
                all_stats[hardness]["total_tokens"] += h_stats["total_tokens"]
                all_stats[hardness]["total_prompt_tokens"] += h_stats.get("total_prompt_tokens", 0)
                all_stats[hardness]["total_completion_tokens"] += h_stats.get("total_completion_tokens", 0)
                all_stats[hardness]["databases"].append(db_name)
        
        # 打印当前数据库的总体统计
        if db_total_queries > 0:
            db_avg_tokens = db_total_tokens / db_total_queries
            print(f"  {'总计':8s}: {db_avg_tokens:8.1f} tokens/query "
                  f"({db_total_queries} queries, {db_total_tokens:,} total)")
            print(f"    - Prompt Tokens: {db_total_prompt_tokens:,}")
            print(f"    - Completion Tokens: {db_total_completion_tokens:,}")
            
            # 累加到总体统计
            grand_total_queries += db_total_queries
            grand_total_prompt_tokens += db_total_prompt_tokens
            grand_total_completion_tokens += db_total_completion_tokens
            grand_total_tokens += db_total_tokens
    
    print("\n" + "="*80)
    print("【所有数据库汇总 - 按难度级别】")
    print("="*80)
    for hardness in ['easy', 'medium', 'hard', 'extra']:
        if hardness in all_stats:
            stats = all_stats[hardness]
            if stats["total_queries"] > 0:
                avg = stats["total_tokens"] / stats["total_queries"]
                print(f"  {hardness:8s}: {avg:8.1f} tokens/query "
                      f"({stats['total_queries']} queries, {stats['total_tokens']:,} total)")
                if stats.get("total_prompt_tokens", 0) > 0:
                    print(f"    - Prompt Tokens: {stats['total_prompt_tokens']:,}")
                    print(f"    - Completion Tokens: {stats['total_completion_tokens']:,}")
    
    # 打印所有数据库的总体统计
    print("\n" + "="*80)
    print("【所有数据库汇总 - 总体统计】")
    print("="*80)
    if grand_total_queries > 0:
        grand_avg_tokens = grand_total_tokens / grand_total_queries
        print(f"  总查询数: {grand_total_queries}")
        print(f"  总 Token: {grand_total_tokens:,}")
        print(f"  平均 Token: {grand_avg_tokens:.1f} tokens/query")
        if grand_total_prompt_tokens > 0:
            print(f"  总 Prompt Tokens: {grand_total_prompt_tokens:,}")
            print(f"  总 Completion Tokens: {grand_total_completion_tokens:,}")
            print(f"  平均 Prompt Tokens: {grand_total_prompt_tokens / grand_total_queries:.1f}")
            print(f"  平均 Completion Tokens: {grand_total_completion_tokens / grand_total_queries:.1f}")
    else:
        print("  无统计数据")

if __name__ == "__main__":
    import sys
    db_names = sys.argv[1:] if len(sys.argv) > 1 else ["concert_singer", "flight_2", "student_transcripts_tracking"]
    print_token_summary(db_names)