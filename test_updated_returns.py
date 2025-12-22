#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试更新后的收益率计算功能
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# 添加当前目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from binance_transactions import BinanceTransactions

def test_bitcoin_price_download():
    """测试比特币价格下载功能"""
    print("=== 测试比特币价格下载功能 ===")
    
    try:
        analyzer = BinanceTransactions()
        
        # 测试下载最近7天的比特币价格数据
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        btc_data = analyzer.get_bitcoin_price_data(
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d')
        )
        
        if not btc_data.empty:
            print(f"✓ 成功获取 {len(btc_data)} 天的比特币价格数据")
            print(f"  日期范围: {btc_data.index.min()} 到 {btc_data.index.max()}")
            print(f"  价格范围: {btc_data['close'].min():.2f} - {btc_data['close'].max():.2f} USDT")
            print(f"  数据列: {list(btc_data.columns)}")
            return True
        else:
            print("✗ 未能获取比特币价格数据")
            return False
            
    except Exception as e:
        print(f"✗ 测试比特币价格下载失败: {e}")
        return False

def test_returns_calculation():
    """测试基于仓位和价格的收益率计算"""
    print("\n=== 测试基于仓位和价格的收益率计算 ===")
    
    try:
        analyzer = BinanceTransactions()
        
        # 创建模拟交易数据
        dates = pd.date_range(start='2025-11-20', end='2025-11-26', freq='D')
        transactions_data = []
        
        # 模拟一些交易
        for i, date in enumerate(dates):
            if i == 0:  # 第一天买入BTC
                transactions_data.append({
                    'date': date,
                    'txn_volume': 1000.0,  # 花费1000 USDT买BTC
                    'txn_shares': 0.02     # 买0.02 BTC
                })
            elif i == 3:  # 第四天卖出BTC
                transactions_data.append({
                    'date': date,
                    'txn_volume': -1100.0,  # 卖出获得1100 USDT
                    'txn_shares': -0.02     # 卖出0.02 BTC
                })
        
        transactions_df = pd.DataFrame(transactions_data)
        transactions_df.set_index('date', inplace=True)
        
        print(f"创建模拟交易数据: {len(transactions_df)} 笔交易")
        print(transactions_df)
        
        # 测试收益率计算
        returns = analyzer.calculate_returns(transactions_df, initial_capital=10000)
        
        if not returns.empty:
            print(f"✓ 成功计算收益率: {len(returns)} 天")
            print(f"  收益率范围: {returns.min():.4f} - {returns.max():.4f}")
            print(f"  平均收益率: {returns.mean():.4f}")
            print(returns)
            return True
        else:
            print("✗ 未能计算收益率")
            return False
            
    except Exception as e:
        print(f"✗ 测试收益率计算失败: {e}")
        return False

def test_fallback_method():
    """测试备用方法获取价格数据"""
    print("\n=== 测试备用方法获取价格数据 ===")
    
    try:
        analyzer = BinanceTransactions()
        
        # 直接调用备用方法
        end_date = datetime.now()
        start_date = end_date - timedelta(days=5)
        
        btc_data = analyzer._get_bitcoin_price_fallback(
            start_date=start_date,
            end_date=end_date,
            days=5
        )
        
        if not btc_data.empty:
            print(f"✓ 备用方法成功获取 {len(btc_data)} 天的比特币价格数据")
            print(f"  日期范围: {btc_data.index.min()} 到 {btc_data.index.max()}")
            print(f"  价格范围: {btc_data['close'].min():.2f} - {btc_data['close'].max():.2f} USDT")
            return True
        else:
            print("✗ 备用方法未能获取比特币价格数据")
            return False
            
    except Exception as e:
        print(f"✗ 测试备用方法失败: {e}")
        return False

def main():
    """主测试函数"""
    print("开始测试更新后的收益率计算功能...\n")
    
    tests = [
        ("比特币价格下载", test_bitcoin_price_download),
        ("收益率计算", test_returns_calculation),
        ("备用方法", test_fallback_method),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ {test_name} 测试出现异常: {e}")
            results.append((test_name, False))
    
    # 打印测试结果摘要
    print("\n" + "="*50)
    print("测试结果摘要:")
    print("="*50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print("🎉 所有测试都通过了！")
        return True
    else:
        print("⚠️  有测试失败，请检查代码")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
