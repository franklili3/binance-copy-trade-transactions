#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复positions_pyfolio.csv文件，确保日期范围与transactions_pyfolio.csv一致
"""

import pandas as pd
import numpy as np

def fix_positions_file():
    """修复positions文件，确保包含所有交易日期"""
    
    # 读取交易数据
    try:
        transactions_df = pd.read_csv('transactions_pyfolio.csv', index_col=0, parse_dates=True)
        print(f"读取到 {len(transactions_df)} 条交易记录")
        print(f"交易日期范围: {transactions_df.index.min()} 到 {transactions_df.index.max()}")
    except Exception as e:
        print(f"读取交易文件失败: {e}")
        return
    
    # 获取所有唯一的日期（标准化到日期）
    unique_dates = transactions_df.index.normalize().unique()
    print(f"唯一日期数量: {len(unique_dates)}")
    print("唯一日期:")
    for date in sorted(unique_dates):
        print(f"  {date}")
    
    # 计算总交易额作为BTC持仓价值
    total_volume = transactions_df['txn_volume'].sum()
    print(f"总交易额: {total_volume}")
    
    # 创建positions数据
    positions_data = []
    for date in sorted(unique_dates):
        positions_data.append({
            'date': date,
            'BTC': total_volume,
            'cash': 0.0
        })
    
    # 创建DataFrame
    positions_df = pd.DataFrame(positions_data)
    positions_df.set_index('date', inplace=True)
    
    # 保存到文件
    positions_df.to_csv('positions_pyfolio.csv')
    print(f"已保存修复后的positions文件，包含 {len(positions_df)} 行数据")
    
    # 显示文件内容
    print("\n修复后的positions_pyfolio.csv内容:")
    print(positions_df.to_csv())

if __name__ == "__main__":
    fix_positions_file()
