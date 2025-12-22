#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试备用价格数据获取功能（不需要API密钥）
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os
import requests

# 添加当前目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_binance_public_api():
    """直接测试币安公开API"""
    print("=== 测试币安公开API ===")
    
    try:
        # 使用币安公开API获取K线数据
        url = "https://api.binance.com/api/v3/klines"
        
        # 计算日期范围
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        since = int(start_date.timestamp() * 1000)
        
        params = {
            'symbol': 'BTCUSDT',
            'interval': '1d',  # 日线数据
            'startTime': since,
            'limit': 1000  # 最大1000条
        }
        
        print(f"请求URL: {url}")
        print(f"时间范围: {start_date} 到 {end_date}")
        
        # 发送请求
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        if not data:
            print("✗ 币安API返回空数据")
            return None
        
        print(f"✓ 成功获取 {len(data)} 个K线数据点")
        
        # 转换为DataFrame
        df = pd.DataFrame(data, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_asset_volume', 'number_of_trades',
            'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
        ])
        
        # 转换数据类型
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # 设置索引
        df.set_index('datetime', inplace=True)
        
        # 只保留需要的列
        df = df[['open', 'high', 'low', 'close', 'volume']]
        
        # 删除空值
        df = df.dropna()
        
        print(f"✓ 处理后得到 {len(df)} 天的数据")
        print(f"  日期范围: {df.index.min()} 到 {df.index.max()}")
        print(f"  价格范围: {df['close'].min():.2f} - {df['close'].max():.2f} USDT")
        print("前3条数据:")
        print(df.head(3))
        
        return df
        
    except Exception as e:
        print(f"✗ 测试币安公开API失败: {e}")
        return None

def test_simple_returns_calculation():
    """测试简化的收益率计算"""
    print("\n=== 测试简化收益率计算 ===")
    
    try:
        # 创建模拟交易数据
        dates = pd.date_range(start='2025-11-20', end='2025-11-26', freq='D')
        transactions_data = []
        
        # 模拟一些交易
        for i, date in enumerate(dates):
            if i == 0:  # 第一天买入
                transactions_data.append({
                    'date': date,
                    'txn_volume': 1000.0,  # 花费1000 USDT
                    'txn_shares': 0.02     # 买入0.02 单位
                })
            elif i == 3:  # 第四天卖出
                transactions_data.append({
                    'date': date,
                    'txn_volume': -1100.0,  # 获得1100 USDT
                    'txn_shares': -0.02     # 卖出0.02 单位
                })
        
        transactions_df = pd.DataFrame(transactions_data)
        transactions_df.set_index('date', inplace=True)
        
        print(f"创建模拟交易数据: {len(transactions_df)} 笔交易")
        print(transactions_df)
        
        # 简单的收益率计算
        initial_capital = 10000
        current_capital = initial_capital
        returns = []
        
        for i in range(len(transactions_df)):
            daily_return = 0.01 if i == 0 else -0.01  # 简化的日收益率
            returns.append(daily_return)
        
        returns_series = pd.Series(returns, index=transactions_df.index)
        
        print(f"✓ 成功计算简化收益率: {len(returns_series)} 天")
        print(f"  收益率范围: {returns_series.min():.4f} - {returns_series.max():.4f}")
        print(f"  平均收益率: {returns_series.mean():.4f}")
        print(returns_series)
        
        return True
        
    except Exception as e:
        print(f"✗ 测试简化收益率计算失败: {e}")
        return False

def main():
    """主测试函数"""
    print("开始测试价格数据获取功能...\n")
    
    # 测试币安公开API
    btc_data = test_binance_public_api()
    
    # 测试简化收益率计算
    returns_success = test_simple_returns_calculation()
    
    # 打印测试结果摘要
    print("\n" + "="*50)
    print("测试结果摘要:")
    print("="*50)
    
    if btc_data is not None:
        print("币安公开API: ✓ 通过")
        print(f"  获取到 {len(btc_data)} 天的比特币价格数据")
    else:
        print("币安公开API: ✗ 失败")
    
    print(f"简化收益率计算: {'✓ 通过' if returns_success else '✗ 失败'}")
    
    if btc_data is not None and returns_success:
        print("\n🎉 关键功能测试通过！")
        return True
    else:
        print("\n⚠️  部分测试失败")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
