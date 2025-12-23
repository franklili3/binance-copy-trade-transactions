#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日期格式转换示例
演示如何在Python中将各种日期格式转换为datetime对象
"""

import pandas as pd
from datetime import datetime
import dateutil.parser

def convert_date_examples():
    """演示各种日期格式转换方法"""
    
    print("=== 日期格式转换示例 ===\n")
    
    # 1. 从CSV文件中读取日期（类似于returns_pyfolio.csv的格式）
    print("1. 从CSV文件读取ISO 8601格式的日期:")
    csv_date_str = "2025-04-04 00:00:00+00:00"
    print(f"原始字符串: {csv_date_str}")
    
    # 方法1: 使用pandas的to_datetime（推荐）
    dt_pandas = pd.to_datetime(csv_date_str)
    print(f"pandas转换: {dt_pandas}")
    print(f"类型: {type(dt_pandas)}")
    
    # 方法2: 使用dateutil.parser（更灵活）
    dt_dateutil = dateutil.parser.parse(csv_date_str)
    print(f"dateutil转换: {dt_dateutil}")
    print(f"类型: {type(dt_dateutil)}")
    print()
    
    # 2. 处理不同的日期格式
    print("2. 处理不同日期格式:")
    date_formats = [
        "2025-04-04",
        "2025/04/04",
        "04/04/2025",
        "2025-04-04 15:30:00",
        "Apr 4, 2025",
        "April 4, 2025 3:30 PM"
    ]
    
    for date_str in date_formats:
        print(f"\n原始字符串: {date_str}")
        
        # 使用pandas（推荐）
        try:
            dt = pd.to_datetime(date_str)
            print(f"pandas转换: {dt}")
        except Exception as e:
            print(f"pandas转换失败: {e}")
        
        # 使用dateutil（更灵活）
        try:
            dt = dateutil.parser.parse(date_str)
            print(f"dateutil转换: {dt}")
        except Exception as e:
            print(f"dateutil转换失败: {e}")
    
    print("\n" + "="*50)
    
    # 3. 从returns_pyfolio.csv读取并转换
    print("3. 从returns_pyfolio.csv文件读取并转换日期:")
    
    try:
        # 读取CSV文件
        df = pd.read_csv('returns_pyfolio.csv', index_col=0, parse_dates=True)
        print(f"成功读取CSV文件，形状: {df.shape}")
        print(f"索引类型: {type(df.index)}")
        print(f"前5个日期:")
        print(df.index[:5])
        
        # 如果索引还不是datetime类型，手动转换
        if not pd.api.types.is_datetime64_any_dtype(df.index):
            print("\n索引不是datetime类型，正在转换...")
            df.index = pd.to_datetime(df.index)
            print(f"转换后索引类型: {type(df.index)}")
        
        print(f"\n日期范围: {df.index.min()} 到 {df.index.max()}")
        
        # 访问特定日期
        specific_date = df.index[0]
        print(f"第一个日期: {specific_date}")
        print(f"年份: {specific_date.year}")
        print(f"月份: {specific_date.month}")
        print(f"日期: {specific_date.day}")
        
    except FileNotFoundError:
        print("returns_pyfolio.csv文件未找到")
    except Exception as e:
        print(f"读取CSV文件时出错: {e}")

def batch_date_conversion():
    """批量日期转换示例"""
    print("\n=== 批量日期转换示例 ===")
    
    # 模拟从CSV读取的日期字符串列表
    date_strings = [
        "2025-04-04 00:00:00+00:00",
        "2025-04-05 00:00:00+00:00", 
        "2025-04-06 00:00:00+00:00",
        "2025-04-07 00:00:00+00:00"
    ]
    
    print("原始日期字符串:")
    for ds in date_strings:
        print(f"  {ds}")
    
    # 批量转换
    print("\n转换后的datetime对象:")
    datetimes = pd.to_datetime(date_strings)
    for dt in datetimes:
        print(f"  {dt} (类型: {type(dt)})")
    
    # 转换为不同的日期格式
    print("\n转换为不同格式:")
    for dt in datetimes:
        print(f"ISO格式: {dt.isoformat()}")
        print(f"字符串格式: {dt.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"美国格式: {dt.strftime('%m/%d/%Y')}")
        print(f"欧洲格式: {dt.strftime('%d/%m/%Y')}")
        print("---")

def timezone_handling():
    """时区处理示例"""
    print("\n=== 时区处理示例 ===")
    
    # 带时区的日期
    utc_date = pd.to_datetime("2025-04-04 00:00:00+00:00")
    print(f"UTC时间: {utc_date}")
    print(f"时区: {utc_date.tz}")
    
    # 转换为不同时区
    try:
        # 转换为北京时间
        beijing_time = utc_date.tz_convert('Asia/Shanghai')
        print(f"北京时间: {beijing_time}")
        
        # 移除时区信息
        naive_date = utc_date.tz_localize(None)
        print(f"无时区日期: {naive_date}")
        
    except Exception as e:
        print(f"时区转换出错: {e}")

if __name__ == "__main__":
    convert_date_examples()
    batch_date_conversion()
    timezone_handling()
    
    print("\n=== 总结 ===")
    print("推荐方法:")
    print("1. 使用 pd.to_datetime() - 最简单，最适合pandas数据")
    print("2. 使用 dateutil.parser.parse() - 更灵活，支持更多格式")
    print("3. 对于已知格式，使用 datetime.strptime() - 最快")
    print("\n时区处理:")
    print("- 使用 tz_convert() 转换时区")
    print("- 使用 tz_localize(None) 移除时区信息")
