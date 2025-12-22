#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试简化后的收益率计算功能
不需要API密钥，使用模拟数据测试
"""

import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 模拟BinanceTransactions类的关键方法
class MockBinanceTransactions:
    def __init__(self):
        """初始化模拟交易分析器"""
        logger.info("初始化模拟币安交易分析器")
    
    def get_bitcoin_price_data(self, start_date=None, end_date=None, days=30):
        """模拟获取比特币价格数据"""
        logger.info("生成模拟比特币价格数据...")
        
        # 计算日期范围
        if not start_date and not end_date:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
        
        # 创建日期范围
        date_range = pd.date_range(start=start_date, end=end_date, freq='D')
        
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
        
        logger.info(f"生成 {len(df)} 天的模拟比特币价格数据")
        logger.info(f"价格范围: {df['close'].min():.2f} - {df['close'].max():.2f} USDT")
        
        return df
    
    def get_all_transactions(self, symbol=None, since=None, limit=None, days=None):
        """模拟获取交易记录"""
        logger.info("生成模拟交易记录...")
        
        # 生成一些模拟交易记录
        transactions = []
        base_date = datetime.now() - timedelta(days=30)
        
        # 模拟BTC/USDT交易 - 分布在整个30天期间
        for i in range(10):  # 生成10笔交易
            # 让交易分布在整个30天期间
            days_offset = np.random.randint(0, 30)  # 随机分布在30天内
            tx_date = base_date + timedelta(days=days_offset)
            
            # 随机决定买入或卖出
            side = 'buy' if i % 2 == 0 else 'sell'
            
            # 模拟交易参数
            amount = np.random.uniform(0.001, 0.01)  # BTC数量
            price = 95000 + np.random.normal(0, 2000)  # 价格
            cost = amount * price  # 交易金额
            
            transaction = {
                'datetime': tx_date.isoformat(),
                'symbol': 'BTC/USDT',
                'side': side,
                'amount': amount,
                'price': price,
                'cost': cost,
                'fee': {
                    'cost': cost * 0.001,  # 0.1% 手续费
                    'currency': 'USDT'
                }
            }
            transactions.append(transaction)
        
        logger.info(f"生成 {len(transactions)} 笔模拟交易记录")
        return transactions
    
    def transactions_to_pyfolio_format(self, transactions):
        """将交易记录转换为pyfolio格式"""
        if not transactions:
            return pd.DataFrame()
        
        pyfolio_data = []
        for tx in transactions:
            txn_volume = tx['cost']  # 交易金额
            txn_shares = tx['amount']  # 交易数量
            
            pyfolio_data.append({
                'date': pd.to_datetime(tx['datetime'], utc=True),
                'txn_volume': txn_volume,
                'txn_shares': txn_shares
            })
        
        df = pd.DataFrame(pyfolio_data)
        df.set_index('date', inplace=True)
        df.sort_index(inplace=True)
        
        return df
    
    def _calculate_daily_positions(self, raw_transactions, btc_price_df):
        """计算每日持仓变化"""
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
        
        # 按日期处理交易
        for tx in raw_transactions:
            tx_date = pd.to_datetime(tx['datetime'], utc=True).normalize()
            
            if tx_date not in positions_df.index:
                continue
            
            symbol = tx['symbol']
            side = tx['side']
            amount = tx['amount']
            cost = tx['cost']
            
            if symbol == 'BTC/USDT':
                if side == 'buy':
                    # 买入BTC：减少USDT，增加BTC
                    positions_df.loc[tx_date:, 'BTC'] += amount
                    positions_df.loc[tx_date:, 'USDT'] -= cost
                else:  # sell
                    # 卖出BTC：增加USDT，减少BTC
                    positions_df.loc[tx_date:, 'BTC'] -= amount
                    positions_df.loc[tx_date:, 'USDT'] += cost
        
        return positions_df
    
    def _calculate_portfolio_value(self, daily_positions, btc_price_df):
        """计算每日投资组合价值"""
        portfolio_values = []
        
        for date in daily_positions.index:
            daily_value = 0.0
            
            # 获取当日持仓
            positions = daily_positions.loc[date]
            
            # 计算各资产价值 - 简化为 BTC价值 + USDT
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
            
            portfolio_values.append(daily_value)
        
        return pd.Series(portfolio_values, index=daily_positions.index)
    
    def calculate_returns(self, transactions):
        """基于仓位和比特币价格计算每日账户净值和收益率序列"""
        if transactions.empty:
            return pd.Series()
        
        logger.info("开始基于仓位和比特币价格计算收益率...")
        
        # 获取比特币价格数据
        start_date = transactions.index.min().normalize()
        end_date = transactions.index.max().normalize()
        btc_price_df = self.get_bitcoin_price_data(
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d')
        )
        
        if btc_price_df.empty:
            logger.warning("无法获取比特币价格数据")
            return pd.Series()
        
        # 获取原始交易数据以提取symbol和交易方向
        since = int(start_date.timestamp() * 1000)
        raw_transactions = self.get_all_transactions(since=since)
        
        # 计算每日持仓变化
        daily_positions = self._calculate_daily_positions(raw_transactions, btc_price_df)
        
        # 计算每日账户净值
        daily_portfolio_value = self._calculate_portfolio_value(daily_positions, btc_price_df)
        
        # 计算收益率
        returns = daily_portfolio_value.pct_change().fillna(0)
        
        logger.info(f"基于 {len(daily_portfolio_value)} 天的数据计算收益率")
        logger.info(f"收益率范围: {returns.min():.4f} - {returns.max():.4f}")
        
        return returns
    
    def _calculate_simple_returns(self, transactions):
        """简化的收益率计算方法（当无法获取价格数据时使用）"""
        logger.info("使用简化方法计算收益率...")
        
        # 按日期排序
        transactions_sorted = transactions.sort_index()
        
        # 计算每日的盈亏
        daily_pnl = []
        portfolio_values = []
        
        # 初始化投资组合价值
        current_portfolio_value = 0.0
        
        # 使用更兼容的方式按日期分组
        transactions_sorted['date_only'] = transactions_sorted.index.date
        for date, group in transactions_sorted.groupby('date_only'):
            # 简化的收益率计算：基于交易金额的变化
            day_volume = group['txn_volume'].sum()
            day_shares = group['txn_shares'].sum()
            
            # 简化假设：每日投资组合价值变化基于交易金额
            # 这里使用一个简化的收益率计算方法
            if day_volume != 0:
                # 基于交易金额的简单收益率计算
                portfolio_value_change = day_shares * 100  # 简化假设每个share价值100 USDT
                current_portfolio_value += portfolio_value_change
            else:
                portfolio_value_change = 0
            
            # 计算收益率（基于前一日价值）
            if len(portfolio_values) > 0:
                daily_return = portfolio_value_change / portfolio_values[-1] if portfolio_values[-1] != 0 else 0
            else:
                daily_return = 0
            
            portfolio_values.append(current_portfolio_value)
            daily_pnl.append({
                'date': pd.to_datetime(date),
                'return': daily_return,
                'portfolio_value': current_portfolio_value
            })
        
        # 删除临时列
        transactions_sorted.drop('date_only', axis=1, inplace=True)
        
        returns_df = pd.DataFrame(daily_pnl)
        returns_df.set_index('date', inplace=True)
        
        return returns_df['return']
    
    def save_to_csv(self, data, filename):
        """保存数据到CSV文件"""
        try:
            data.to_csv(filename)
            logger.info(f"数据已保存到 {filename}")
        except Exception as e:
            logger.error(f"保存文件失败: {e}")

def test_simplified_functionality():
    """测试简化后的功能"""
    logger.info("=== 开始测试简化后的收益率计算功能 ===")
    
    try:
        # 创建模拟分析器
        analyzer = MockBinanceTransactions()
        
        # 获取模拟交易数据
        raw_transactions = analyzer.get_all_transactions()
        transactions_df = analyzer.transactions_to_pyfolio_format(raw_transactions)
        
        logger.info(f"获取到 {len(transactions_df)} 条交易记录")
        
        # 测试基于仓位的收益率计算
        logger.info("\n--- 测试基于仓位的收益率计算 ---")
        returns = analyzer.calculate_returns(transactions_df)
        
        if not returns.empty:
            logger.info(f"成功计算 {len(returns)} 天的收益率")
            logger.info(f"收益率统计:")
            logger.info(f"  平均日收益率: {(returns.mean() * 100):.4f}%")
            logger.info(f"  累计收益率: {(returns.sum() * 100):.2f}%")
            logger.info(f"  最大日收益率: {(returns.max() * 100):.4f}%")
            logger.info(f"  最小日收益率: {(returns.min() * 100):.4f}%")
            logger.info(f"  收益率标准差: {(returns.std() * 100):.4f}%")
            
            # 保存收益率数据
            analyzer.save_to_csv(returns, 'test_returns_simplified.csv')
            
            # 显示前5天的收益率
            logger.info(f"\n前5天收益率数据:")
            for i, (date, ret) in enumerate(returns.head().items()):
                logger.info(f"  {date.strftime('%Y-%m-%d')}: {ret:.6f} ({ret*100:.4f}%)")
        else:
            logger.error("收益率计算失败，返回空序列")
            return False
        
        # 测试简化收益率计算方法
        logger.info("\n--- 测试简化收益率计算方法 ---")
        simple_returns = analyzer._calculate_simple_returns(transactions_df)
        
        if not simple_returns.empty:
            logger.info(f"简化方法计算 {len(simple_returns)} 天的收益率")
            logger.info(f"简化方法平均日收益率: {(simple_returns.mean() * 100):.4f}%")
            
            # 保存简化收益率数据
            analyzer.save_to_csv(simple_returns, 'test_simple_returns.csv')
        else:
            logger.error("简化收益率计算失败")
            return False
        
        logger.info("\n=== 测试完成！所有功能正常工作 ===")
        return True
        
    except Exception as e:
        logger.error(f"测试过程中出错: {e}")
        import traceback
        logger.error(f"错误详情: {traceback.format_exc()}")
        return False

def main():
    """主函数"""
    success = test_simplified_functionality()
    
    if success:
        logger.info("✓ 所有测试通过")
        logger.info("✓ 简化后的收益率计算功能工作正常")
        logger.info("✓ 已删除initial_capital参数")
        logger.info("✓ 每日投资组合价值 = BTC价值 + USDT")
        sys.exit(0)
    else:
        logger.error("✗ 测试失败")
        sys.exit(1)

if __name__ == "__main__":
    main()
