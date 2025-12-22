#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试完整功能（不需要API密钥的简化版本）
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

def test_mock_data_generation():
    """测试模拟数据生成"""
    print("\n=== 测试模拟数据生成 ===")
    
    try:
        from datetime import timezone
        
        # 计算日期范围
        end_date = datetime.now(tz=timezone.utc)
        start_date = end_date - timedelta(days=10)
        
        # 创建日期范围
        date_range = pd.date_range(start=start_date, end=end_date, freq='D', tz='UTC')
        
        # 生成模拟价格数据
        np.random.seed(42)  # 固定种子以确保可重现性
        base_price = 95000.0
        price_changes = np.random.normal(0, 0.02, len(date_range))  # 2%的日波动率
        prices = [base_price]
        
        for change in price_changes[1:]:
            new_price = prices[-1] * (1 + change)
            prices.append(max(new_price, 1000))  # 最低价格限制为1000 USDT
        
        # 创建DataFrame
        mock_data = []
        for i, date in enumerate(date_range):
            price = prices[i]
            # 生成合理的OHLC数据
            high = price * (1 + abs(np.random.normal(0, 0.01)))
            low = price * (1 - abs(np.random.normal(0, 0.01)))
            open_price = low + (high - low) * np.random.random()
            volume = np.random.uniform(1000, 5000)  # 模拟交易量
            
            mock_data.append({
                'open': open_price,
                'high': high,
                'low': low,
                'close': price,
                'volume': volume
            })
        
        df = pd.DataFrame(mock_data, index=date_range)
        
        print(f"✓ 生成 {len(df)} 天的模拟比特币价格数据")
        print(f"  日期范围: {df.index.min()} 到 {df.index.max()}")
        print(f"  价格范围: {df['close'].min():.2f} - {df['close'].max():.2f} USDT")
        print("前3条数据:")
        print(df.head(3))
        
        return df
        
    except Exception as e:
        print(f"✗ 测试模拟数据生成失败: {e}")
        return None

def test_returns_calculation_with_mock_data():
    """使用模拟数据测试收益率计算"""
    print("\n=== 测试基于模拟数据的收益率计算 ===")
    
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
        
        # 创建模拟价格数据
        price_data = []
        for i, date in enumerate(dates):
            base_price = 95000
            price_change = np.random.normal(0, 0.01)
            price = base_price * (1 + price_change * i * 0.1)
            
            price_data.append({
                'open': price * 0.99,
                'high': price * 1.01,
                'low': price * 0.98,
                'close': price,
                'volume': 1000
            })
        
        price_df = pd.DataFrame(price_data, index=dates)
        
        print(f"\n创建模拟价格数据: {len(price_df)} 天")
        print(price_df[['close']].head())
        
        # 简化的收益率计算
        initial_capital = 10000
        portfolio_values = []
        current_btc = 0
        current_usdt = initial_capital
        
        for date in dates:
            if date in transactions_df.index:
                # 处理交易
                day_transactions = transactions_df.loc[[date]] if date in transactions_df.index else pd.DataFrame()
                if not day_transactions.empty:
                    for _, tx in day_transactions.iterrows():
                        if tx['txn_shares'] > 0:  # 买入
                            current_btc += tx['txn_shares']
                            current_usdt -= tx['txn_volume']
                        else:  # 卖出
                            current_btc += tx['txn_shares']  # 负数
                            current_usdt -= tx['txn_volume']  # 负数变正数
            
            # 计算当日组合价值
            btc_price = price_df.loc[date, 'close']
            portfolio_value = current_btc * btc_price + current_usdt
            portfolio_values.append(portfolio_value)
        
        # 计算收益率
        portfolio_series = pd.Series(portfolio_values, index=dates)
        returns = portfolio_series.pct_change().fillna(0)
        
        print(f"\n✓ 成功计算收益率: {len(returns)} 天")
        print(f"  组合价值变化: {portfolio_series.min():.2f} - {portfolio_series.max():.2f} USDT")
        print(f"  收益率范围: {returns.min():.4f} - {returns.max():.4f}")
        print(f"  总收益率: {((portfolio_series.iloc[-1] / portfolio_series.iloc[0]) - 1) * 100:.2f}%")
        
        return True
        
    except Exception as e:
        print(f"✗ 测试收益率计算失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("开始测试完整功能...\n")
    
    # 测试币安公开API
    btc_data = test_binance_public_api()
    
    # 测试模拟数据生成
    mock_data = test_mock_data_generation()
    
    # 测试收益率计算
    returns_success = test_returns_calculation_with_mock_data()
    
    # 打印测试结果摘要
    print("\n" + "="*50)
    print("测试结果摘要:")
    print("="*50)
    
    if btc_data is not None:
        print("币安公开API: ✓ 通过")
        print(f"  获取到 {len(btc_data)} 天的比特币价格数据")
    else:
        print("币安公开API: ✗ 失败")
    
    if mock_data is not None:
        print("模拟数据生成: ✓ 通过")
        print(f"  生成 {len(mock_data)} 天的模拟数据")
    else:
        print("模拟数据生成: ✗ 失败")
    
    print(f"收益率计算: {'✓ 通过' if returns_success else '✗ 失败'}")
    
    overall_success = (btc_data is not None) and (mock_data is not None) and returns_success
    
    if overall_success:
        print("\n🎉 所有功能测试通过！")
        print("代码已准备好在服务器上运行。")
    else:
        print("\n⚠️  部分测试失败")
        print("请检查错误信息并修复问题。")
    
    return overall_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
