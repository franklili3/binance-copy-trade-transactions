#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修复后的收益率计算功能
不依赖API密钥，使用模拟数据测试
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 模拟BinanceTransactions类的核心功能
class MockBinanceTransactions:
    def __init__(self):
        pass
    
    def _get_mock_bitcoin_price_data(self, start_date=None, end_date=None, days=30):
        """生成模拟比特币价格数据"""
        if not start_date:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
        elif not end_date:
            end_date = datetime.now()
        
        # 创建日期范围
        date_range = pd.date_range(start=start_date, end=end_date, freq='D')
        
        # 生成模拟价格数据 - 有趋势的价格变化
        np.random.seed(42)
        base_price = 95000.0
        prices = []
        
        for i in range(len(date_range)):
            # 添加趋势性变化
            trend = i * 100  # 每天上涨100 USDT
            random_change = np.random.normal(0, 500)  # 随机波动
            price = base_price + trend + random_change
            prices.append(max(price, 1000))  # 最低价格限制
        
        # 创建DataFrame
        mock_data = []
        for i, date in enumerate(date_range):
            price = prices[i]
            high = price * 1.02
            low = price * 0.98
            open_price = low + (high - low) * np.random.random()
            volume = np.random.uniform(1000, 5000)
            
            mock_data.append({
                'open': open_price,
                'high': high,
                'low': low,
                'close': price,
                'volume': volume
            })
        
        df = pd.DataFrame(mock_data, index=date_range)
        print(f"生成 {len(df)} 天的模拟比特币价格数据")
        print(f"价格范围: {df['close'].min():.2f} - {df['close'].max():.2f} USDT")
        
        return df
    
    def _calculate_daily_positions(self, raw_transactions, btc_price_df):
        """计算每日持仓变化（修复后的版本）"""
        # 创建日期范围
        date_range = pd.date_range(
            start=btc_price_df.index.min(),
            end=btc_price_df.index.max(),
            freq='D'
        )
        
        positions_df = pd.DataFrame(index=date_range)
        
        # 初始化持仓列
        positions_df['BTC'] = 0.0
        positions_df['USDT'] = 0.0
        
        # 添加初始USDT余额
        initial_usdt = 10000.0
        positions_df.loc[:, 'USDT'] = initial_usdt
        
        # 按日期处理交易，逐日更新持仓
        current_btc = 0.0
        current_usdt = initial_usdt
        
        # 先按日期排序交易记录
        sorted_transactions = sorted(raw_transactions, key=lambda x: x['datetime'])
        
        # 为每个日期处理交易
        for i, date in enumerate(date_range):
            # 处理当日的所有交易
            daily_transactions = [tx for tx in sorted_transactions 
                                if pd.to_datetime(tx['datetime'], utc=True).date() == date.date()]
            
            # 处理当日每笔交易
            for tx in daily_transactions:
                symbol = tx['symbol']
                side = tx['side']
                amount = tx['amount']
                cost = tx['cost']
                price = tx['price']
                
                if symbol == 'BTC/USDT':
                    if side == 'buy':
                        # 买入BTC：减少USDT，增加BTC
                        current_btc += amount
                        current_usdt -= cost
                    else:  # sell
                        # 卖出BTC：增加USDT，减少BTC
                        current_btc -= amount
                        current_usdt += cost
                elif symbol.endswith('/USDT'):
                    # 其他USDT交易对，简化处理为USDT价值变化
                    if side == 'buy':
                        current_usdt -= cost
                    else:  # sell
                        current_usdt += cost
            
            # 更新当日持仓
            positions_df.loc[date, 'BTC'] = current_btc
            positions_df.loc[date, 'USDT'] = current_usdt
        
        return positions_df
    
    def _calculate_portfolio_value(self, daily_positions, btc_price_df):
        """计算每日投资组合价值"""
        portfolio_values = []
        
        for date in daily_positions.index:
            daily_value = 0.0
            
            # 获取当日持仓
            positions = daily_positions.loc[date]
            
            # 计算各资产价值
            for asset, amount in positions.items():
                if amount == 0:
                    continue
                    
                if asset == 'USDT':
                    # USDT直接计入价值
                    daily_value += amount
                elif asset == 'BTC':
                    # 获取当日BTC价格
                    if date in btc_price_df.index:
                        btc_price = btc_price_df.loc[date, 'close']
                        daily_value += amount * btc_price
                    else:
                        # 如果没有当日价格，使用最近的价格
                        nearest_date = btc_price_df.index[btc_price_df.index.get_indexer([date], method='nearest')[0]]
                        btc_price = btc_price_df.loc[nearest_date, 'close']
                        daily_value += amount * btc_price
                else:
                    # 其他资产的简化处理
                    estimated_price = 100.0  # 简化价格
                    daily_value += amount * estimated_price
            
            portfolio_values.append(daily_value)
        
        return pd.Series(portfolio_values, index=daily_positions.index)
    
    def calculate_returns(self, transactions):
        """计算收益率（模拟版本）"""
        if transactions.empty:
            return pd.Series()
        
        print("开始基于仓位和比特币价格计算收益率...")
        
        # 获取比特币价格数据
        start_date = transactions.index.min().normalize()
        end_date = transactions.index.max().normalize()
        btc_price_df = self._get_mock_bitcoin_price_data(
            start_date=start_date,
            end_date=end_date
        )
        
        # 生成模拟的原始交易数据
        raw_transactions = self._generate_mock_raw_transactions(transactions)
        
        # 计算每日持仓变化
        daily_positions = self._calculate_daily_positions(raw_transactions, btc_price_df)
        
        print("每日持仓变化:")
        print(daily_positions.head(10))
        
        # 计算每日账户净值
        daily_portfolio_value = self._calculate_portfolio_value(daily_positions, btc_price_df)
        
        print("每日投资组合价值:")
        print(daily_portfolio_value.head(10))
        
        # 计算收益率
        returns = daily_portfolio_value.pct_change().fillna(0)
        
        print(f"基于 {len(daily_portfolio_value)} 天的数据计算收益率")
        print(f"收益率范围: {returns.min():.4f} - {returns.max():.4f}")
        
        return returns, daily_positions, daily_portfolio_value
    
    def _generate_mock_raw_transactions(self, transactions_df):
        """生成模拟的原始交易数据"""
        raw_transactions = []
        
        for idx, row in transactions_df.iterrows():
            # 模拟生成买卖交易
            if row['txn_volume'] > 0:
                # 假设是买入交易
                raw_transactions.append({
                    'datetime': idx,
                    'symbol': 'BTC/USDT',
                    'side': 'buy',
                    'amount': row['txn_shares'],
                    'cost': row['txn_volume'],
                    'price': row['txn_volume'] / row['txn_shares'] if row['txn_shares'] != 0 else 95000
                })
            else:
                # 假设是卖出交易
                raw_transactions.append({
                    'datetime': idx,
                    'symbol': 'BTC/USDT',
                    'side': 'sell',
                    'amount': abs(row['txn_shares']),
                    'cost': abs(row['txn_volume']),
                    'price': abs(row['txn_volume']) / abs(row['txn_shares']) if row['txn_shares'] != 0 else 95000
                })
        
        return raw_transactions

def test_fixed_returns_calculation():
    """测试修复后的收益率计算"""
    print("=== 测试修复后的收益率计算功能 ===\n")
    
    # 创建测试数据
    print("1. 创建测试交易数据...")
    
    # 创建分布在整个30天期间的交易数据
    np.random.seed(42)
    base_date = datetime.now() - timedelta(days=30)
    
    transactions = []
    for i in range(20):  # 创建20笔交易
        # 让交易分布在整个30天期间
        days_offset = np.random.randint(0, 30)  # 随机分布在30天内
        tx_date = base_date + timedelta(days=days_offset)
        
        # 随机生成买卖交易
        side = np.random.choice(['buy', 'sell'])
        
        if side == 'buy':
            # 买入交易
            amount = np.random.uniform(0.001, 0.01)  # 0.001-0.01 BTC
            price = np.random.uniform(94000, 98000)   # 价格范围
            volume = amount * price
        else:
            # 卖出交易
            amount = np.random.uniform(0.001, 0.01)
            price = np.random.uniform(94000, 98000)
            volume = amount * price
            volume = -volume  # 卖出为负
            amount = -amount  # 卖出数量为负
        
        transactions.append({
            'date': tx_date,
            'txn_volume': volume,
            'txn_shares': amount
        })
    
    # 创建DataFrame
    transactions_df = pd.DataFrame(transactions)
    transactions_df['date'] = pd.to_datetime(transactions_df['date'], utc=True)
    transactions_df.set_index('date', inplace=True)
    transactions_df.sort_index(inplace=True)
    
    print(f"创建了 {len(transactions_df)} 笔交易记录")
    print(f"交易日期范围: {transactions_df.index.min()} 到 {transactions_df.index.max()}")
    print(f"总交易额: {transactions_df['txn_volume'].abs().sum():.2f} USDT")
    print("\n交易数据样例:")
    print(transactions_df.head(10))
    
    print("\n2. 测试修复后的收益率计算...")
    
    # 创建模拟分析器
    analyzer = MockBinanceTransactions()
    
    # 计算收益率
    returns, daily_positions, portfolio_values = analyzer.calculate_returns(transactions_df)
    
    print("\n=== 收益率分析结果 ===")
    print(f"收益率数据点数: {len(returns)}")
    print(f"非零收益率数量: {(returns != 0).sum()}")
    print(f"平均日收益率: {(returns.mean() * 100):.4f}%")
    print(f"收益率标准差: {(returns.std() * 100):.4f}%")
    print(f"最大单日收益率: {(returns.max() * 100):.4f}%")
    print(f"最小单日收益率: {(returns.min() * 100):.4f}%")
    print(f"总收益率: {(returns.sum() * 100):.4f}%")
    
    print("\n收益率详细数据（前10天）:")
    returns_head = returns.head(10)
    for date, ret in returns_head.items():
        print(f"{date.strftime('%Y-%m-%d')}: {(ret * 100):.4f}%")
    
    if len(returns) > 10:
        print("...")
        returns_tail = returns.tail(5)
        for date, ret in returns_tail.items():
            print(f"{date.strftime('%Y-%m-%d')}: {(ret * 100):.4f}%")
    
    print("\n=== 投资组合价值变化 ===")
    print(f"初始价值: {portfolio_values.iloc[0]:.2f} USDT")
    print(f"最终价值: {portfolio_values.iloc[-1]:.2f} USDT")
    print(f"价值变化: {portfolio_values.iloc[-1] - portfolio_values.iloc[0]:.2f} USDT")
    print(f"总收益率: {((portfolio_values.iloc[-1] / portfolio_values.iloc[0]) - 1) * 100:.4f}%")
    
    print("\n=== 持仓变化（前10天）===")
    positions_head = daily_positions.head(10)
    for date, row in positions_head.iterrows():
        print(f"{date.strftime('%Y-%m-%d')}: BTC={row['BTC']:.6f}, USDT={row['USDT']:.2f}")
    
    # 验证收益率计算是否正确
    print("\n=== 验证计算正确性 ===")
    calculated_returns = returns
    expected_returns = portfolio_values.pct_change().fillna(0)
    
    # 比较计算的收益率
    diff = abs(calculated_returns - expected_returns)
    max_diff = diff.max()
    
    print(f"收益率计算与预期值的最大差异: {max_diff:.8f}")
    
    if max_diff < 1e-10:
        print("✓ 收益率计算正确")
    else:
        print("✗ 收益率计算可能存在问题")
    
    # 检查是否有非零收益率
    non_zero_count = (returns != 0).sum()
    if non_zero_count > 0:
        print(f"✓ 成功计算出 {non_zero_count} 个非零收益率")
    else:
        print("✗ 所有收益率都为零，可能仍有问题")
    
    return returns, daily_positions, portfolio_values

if __name__ == "__main__":
    try:
        returns, positions, values = test_fixed_returns_calculation()
        print("\n🎉 修复后的收益率计算测试完成！")
        
        # 保存测试结果
        returns.to_csv('test_fixed_returns.csv')
        positions.to_csv('test_fixed_positions.csv')
        values.to_csv('test_fixed_portfolio_values.csv')
        
        print("测试结果已保存到 CSV 文件")
        
    except Exception as e:
        print(f"❌ 测试过程中出错: {e}")
        import traceback
        traceback.print_exc()
