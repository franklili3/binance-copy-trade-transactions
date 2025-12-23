#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的日期格式转换示例
专门针对returns_pyfolio.csv的日期格式
"""

import pandas as pd
from datetime import datetime
import dateutil.parser

# 方法1: 使用pandas（推荐）
def convert_with_pandas():
    """使用pandas转换日期格式"""
    print("=== 方法1: 使用pandas pd.to_datetime() ===")
    
    # 你的returns_pyfolio.csv中的日期格式
    date_string = "2025-04-04 00:00:00+00:00"
    print(f"原始字符串: {date_string}")
    
    # 转换为datetime
    dt = pd.to_datetime(date_string)
    print(f"转换后: {dt}")
    print(f"类型: {type(dt)}")
    print(f"年份: {dt.year}, 月份: {dt.month}, 日期: {dt.day}")
    print()

# 方法2: 使用dateutil（更灵活）
def convert_with_dateutil():
    """使用dateutil转换日期格式"""
    print("=== 方法2: 使用dateutil.parser.parse() ===")
    
    date_string = "2025-04-04 00:00:00+00:00"
    print(f"原始字符串: {date_string}")
    
    # 转换为datetime
    dt = dateutil.parser.parse(date_string)
    print(f"转换后: {dt}")
    print(f"类型: {type(dt)}")
    print()

# 方法3: 处理整个CSV文件
def convert_csv_dates():
    """处理CSV文件中的所有日期"""
    print("=== 方法3: 处理CSV文件中的日期 ===")
    
    try:
        # 读取CSV文件，自动解析日期
        df = pd.read_csv('returns_pyfolio.csv', index_col=0, parse_dates=True)
        print(f"成功读取CSV，形状: {df.shape}")
        print(f"索引类型: {type(df.index)}")
        print(f"前5个日期: {df.index[:5].tolist()}")
        
        # 如果需要手动转换
        if not pd.api.types.is_datetime64_any_dtype(df.index):
            print("手动转换索引为datetime...")
            df.index = pd.to_datetime(df.index)
            print(f"转换后索引类型: {type(df.index)}")
        
        print()
        
    except FileNotFoundError:
        print("returns_pyfolio.csv文件未找到")
    except Exception as e:
        print(f"读取CSV出错: {e}")

# 方法4: 批量转换日期字符串
def batch_convert():
    """批量转换多个日期字符串"""
    print("=== 方法4: 批量转换日期字符串 ===")
    
    dates = [
        "2025-04-04 00:00:00+00:00",
        "2025-04-05 00:00:00+00:00",
        "2025-04-06 00:00:00+00:00"
    ]
    
    print("原始日期:")
    for d in dates:
        print(f"  {d}")
    
    # 批量转换
    converted = pd.to_datetime(dates)
    print("\n转换后:")
    for d in converted:
        print(f"  {d} ({type(d)})")
    print()

if __name__ == "__main__":
    print("Python日期格式转换示例\n")
    print("针对你的returns_pyfolio.csv文件格式: '2025-04-04 00:00:00+00:00'\n")
    
    convert_with_pandas()
    convert_with_dateutil()
    convert_csv_dates()
    batch_convert()
    
    print("=== 推荐使用 ===")
    print("对于你的情况，最简单的方法是:")
    print("```python")
    print("import pandas as pd")
    print("")
    print("# 单个日期转换")
    print("date_str = '2025-04-04 00:00:00+00:00'")
    print("dt = pd.to_datetime(date_str)")
    print("")
    print("# 读取CSV并自动转换日期索引")
    print("df = pd.read_csv('returns_pyfolio.csv', index_col=0, parse_dates=True)")
    print("```")
