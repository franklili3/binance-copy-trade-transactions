#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
币安交易记录分析器
用于分析币安交易记录CSV文件并计算收益率
"""

import pandas as pd
import numpy as np
from datetime import datetime, timezone
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Tuple
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BinanceTransactionAnalyzer:
    def __init__(self, csv_file_path: str):
        """初始化分析器"""
        self.csv_file = csv_file_path
        self.raw_data = None
        self.processed_data = None
        self.asset_balances = {}
        self.daily_portfolio_value = None
        
    def load_data(self):
        """加载CSV数据"""
        try:
            self.raw_data = pd.read_csv(self.csv_file)
            logger.info(f"成功加载 {len(self.raw_data)} 条交易记录")
            logger.info(f"交易记录时间范围: {self.raw_data.iloc[0]['UTC_Time']} 到 {self.raw_data.iloc[-1]['UTC_Time']}")
            
            # 转换时间戳为datetime对象
            self.raw_data['UTC_Time'] = pd.to_datetime(self.raw_data['UTC_Time'])
            
            return True
        except Exception as e:
            logger.error(f"加载数据失败: {e}")
            return False
    
    def analyze_transactions(self):
        """分析交易数据"""
        if self.raw_data is None:
            logger.error("请先加载数据")
            return False
        
        logger.info("开始分析交易数据...")
        
        # 按时间排序
        self.raw_data = self.raw_data.sort_values('UTC_Time')
        
        # 计算各资产的数量变化
        self._calculate_asset_balances()
        
        # 计算每日投资组合价值
        self._calculate_daily_portfolio_value()
        
        # 计算收益率
        self._calculate_returns()
        
        return True
    
    def _calculate_asset_balances(self):
        """计算各资产的数量变化"""
        logger.info("计算资产数量变化...")
        
        # 初始化资产余额
        self.asset_balances = {
            'USDT': 0.0,
            'BTC': 0.0,
            'BNB': 0.0,
            'ETH': 0.0,
            'SOL': 0.0,
            'BUSD': 0.0,
            'USD': 0.0
        }
        
        # 记录资产变化历史
        balance_history = []
        
        # 遍历每笔交易
        for _, row in self.raw_data.iterrows():
            account = row['Account']
            operation = row['Operation']
            coin = row['Coin']
            amount = float(row['Change'])
            remark = row['Remark']
            
            # 跳过非相关交易
            if account == 'Spot Lead':
                continue
                
            # 处理不同类型的交易
            if operation in ['Transaction Buy', 'Transaction Sold', 'Transaction Spend', 'Transaction Revenue']:
                if coin in self.asset_balances:
                    self.asset_balances[coin] += amount
            elif operation in ['Deposit', 'Withdraw', 'Send']:
                # 充值提现
                if coin in self.asset_balances:
                    self.asset_balances[coin] += amount
            elif operation in ['Copy Portfolio (Spot) - Profit Sharing with Leader']:
                # 带单收益分佣（USDT为正数）
                if coin in self.asset_balances:
                    self.asset_balances[coin] += amount
            elif operation in ['Lead Portfolio (Spot) - Create']:
                # 创建带单（USDT为负数）
                if coin in self.asset_balances:
                    self.asset_balances[coin] += amount
            
            # 记录余额变化
            balance_copy = self.asset_balances.copy()
            balance_copy['timestamp'] = row['UTC_Time']
            balance_copy['operation'] = operation
            balance_copy['coin'] = coin
            balance_copy['amount'] = amount
            balance_copy['remark'] = remark
            balance_history.append(balance_copy)
        
        self.balance_history = pd.DataFrame(balance_history)
        logger.info("资产数量变化计算完成")
        
        # 打印最终余额
        logger.info("=== 最终资产余额 ===")
        for asset, balance in self.asset_balances.items():
            if abs(balance) > 1e-8:  # 只显示非零余额
                logger.info(f"{asset}: {balance:.8f}")
    
    def _get_price_estimate(self, coin: str, date: datetime) -> float:
        """获取资产价格估算（用于非BTC/USDT资产）"""
        # 简化的价格估算表（实际应用中可以从API获取）
        price_estimates = {
            'USDT': 1.0,
            'BUSD': 1.0,
            'USD': 1.0,
            'BTC': 95000.0,  # 默认BTC价格
            'ETH': 3000.0,
            'BNB': 300.0,
            'SOL': 100.0,
            'ADA': 0.5,
            'DOT': 10.0,
            'LINK': 15.0,
            'AVAX': 30.0,
            'UNI': 6.0,
            'ATOM': 10.0
        }
        return price_estimates.get(coin, 1.0)
    
    def _calculate_daily_portfolio_value(self):
        """计算每日投资组合价值"""
        logger.info("计算每日投资组合价值...")
        
        if self.balance_history.empty:
            logger.error("没有余额历史数据")
            return
        
        # 创建日期范围
        start_date = self.balance_history['timestamp'].min().date()
        end_date = self.balance_history['timestamp'].max().date()
        
        date_range = pd.date_range(start=start_date, end=end_date, freq='D')
        
        # 初始化每日价值
        daily_values = []
        
        # 遍历每个日期
        for date in date_range:
            # 计算当日结束时的资产余额
            end_of_day = pd.Timestamp(date, tz=timezone.utc) + pd.Timedelta(hours=23, minutes=59, seconds=59)
            
            # 获取该日期最后一笔交易后的余额
            day_balances = self.balance_history[self.balance_history['timestamp'] <= end_of_day]
            
            if not day_balances.empty:
                last_balance = day_balances.iloc[-1]
                portfolio_value = 0.0
                
                # 计算总价值
                for asset, balance in self.asset_balances.items():
                    if asset == 'USDT':
                        portfolio_value += balance
                    elif asset == 'BTC':
                        portfolio_value += balance * 95000.0  # 使用固定的BTC价格
                    else:
                        price = self._get_price_estimate(asset, date)
                        portfolio_value += balance * price
                
                daily_values.append({
                    'date': date,
                    'portfolio_value': portfolio_value,
                    'USDT_balance': self.asset_balances['USDT'],
                    'BTC_balance': self.asset_balances['BTC']
                })
            else:
                daily_values.append({
                    'date': date,
                    'portfolio_value': 0.0,
                    'USDT_balance': 0.0,
                    'BTC_balance': 0.0
                })
        
        self.daily_portfolio_value = pd.DataFrame(daily_values)
        logger.info(f"计算了 {len(self.daily_portfolio_value)} 天的投资组合价值")
    
    def _calculate_returns(self):
        """计算收益率"""
        if self.daily_portfolio_value is None or self.daily_portfolio_value.empty:
            logger.error("没有投资组合价值数据")
            return
        
        logger.info("计算收益率...")
        
        # 计算日收益率
        self.daily_portfolio_value['daily_return'] = self.daily_portfolio_value['portfolio_value'].pct_change()
        
        # 计算累计收益率
        initial_value = self.daily_portfolio_value['portfolio_value'].iloc[0]
        if initial_value > 0:
            self.daily_portfolio_value['cumulative_return'] = (self.daily_portfolio_value['portfolio_value'] - initial_value) / initial_value
        
        # 计算统计指标
        self.return_stats = {
            'total_return': (self.daily_portfolio_value['portfolio_value'].iloc[-1] - initial_value) / initial_value if initial_value > 0 else 0,
            'annualized_return': None,  # 需要基于实际天数计算
            'volatility': self.daily_portfolio_value['daily_return'].std(),
            'max_drawdown': None,  # 需要计算
            'sharpe_ratio': None,  # 需要计算
            'total_days': len(self.daily_portfolio_value),
            'positive_days': len(self.daily_portfolio_value[self.daily_portfolio_value['daily_return'] > 0]),
            'negative_days': len(self.daily_portfolio_value[self.daily_portfolio_value['daily_return'] < 0])
        }
        
        # 计算年化收益率
        days = self.return_stats['total_days']
        if days > 0:
            self.return_stats['annualized_return'] = (1 + self.return_stats['total_return']) ** (365 / days) - 1
        
        # 计算最大回撤
        peak = self.daily_portfolio_value['portfolio_value'].expanding().max()
        drawdown = (self.daily_portfolio_value['portfolio_value'] - peak) / peak
        self.return_stats['max_drawdown'] = drawdown.min()
        
        # 计算夏普比率（假设无风险利率为0）
        if self.return_stats['volatility'] > 0:
            self.return_stats['sharpe_ratio'] = self.return_stats['annualized_return'] / self.return_stats['volatility'] * np.sqrt(365)
        
        logger.info("收益率计算完成")
    
    def generate_report(self):
        """生成分析报告"""
        if not hasattr(self, 'return_stats'):
            logger.error("请先运行分析")
            return
        
        logger.info("=== 币安交易记录分析报告 ===")
        
        # 基本统计
        logger.info("\n=== 基本统计 ===")
        logger.info(f"交易记录总数: {len(self.raw_data)}")
        logger.info(f"分析时间范围: {self.raw_data.iloc[0]['UTC_Time']} 到 {self.raw_data.iloc[-1]['UTC_Time']}")
        logger.info(f"分析天数: {self.return_stats['total_days']}")
        
        # 收益率统计
        logger.info("\n=== 收益率统计 ===")
        logger.info(f"总收益率: {self.return_stats['total_return']:.2%}")
        logger.info(f"年化收益率: {self.return_stats['annualized_return']:.2%}")
        logger.info(f"波动率: {self.return_stats['volatility']:.2%}")
        logger.info(f"最大回撤: {self.return_stats['max_drawdown']:.2%}")
        logger.info(f"夏普比率: {self.return_stats['sharpe_ratio']:.2f}")
        logger.info(f"盈利天数: {self.return_stats['positive_days']}")
        logger.info(f"亏损天数: {self.return_stats['negative_days']}")
        logger.info(f"胜率: {self.return_stats['positive_days']/self.return_stats['total_days']:.1%}")
        
        # 资产余额
        logger.info("\n=== 最终资产余额 ===")
        total_value_usdt = 0.0
        for asset, balance in self.asset_balances.items():
            if abs(balance) > 1e-8:
                if asset == 'USDT':
                    value_usdt = balance
                elif asset == 'BTC':
                    value_usdt = balance * 95000.0
                else:
                    value_usdt = balance * self._get_price_estimate(asset, datetime.now())
                
                logger.info(f"{asset}: {balance:.8f} (约 {value_usdt:.2f} USDT)")
                total_value_usdt += value_usdt
        
        logger.info(f"总资产价值: {total_value_usdt:.2f} USDT")
        
        # 交易类型分析
        logger.info("\n=== 交易类型分析 ===")
        operation_counts = self.raw_data['Operation'].value_counts()
        for operation, count in operation_counts.items():
            logger.info(f"{operation}: {count}")
        
        # 账带单收益分析
        copy_trade_data = self.raw_data[self.raw_data['Operation'].str.contains('Copy Portfolio', na=False)]
        if not copy_trade_data.empty:
            copy_profit = copy_trade_data[copy_trade_data['Operation'].str.contains('Profit Sharing', na=False)]
            if not copy_profit.empty:
                total_copy_profit = copy_profit['Change'].sum()
                logger.info(f"\n=== 费带单收益 ===")
                logger.info(f"总带单收益: {total_copy_profit:.2f} USDT")
                logger.info(f"带单收益笔数: {len(copy_profit)}")
        
        # 期货交易分析
        futures_data = self.raw_data[self.raw_data['Account'] == 'USD-M Futures']
        if not futures_data.empty:
            funding_fees = futures_data[futures_data['Operation'] == 'Funding Fee']
            if not funding_fees.empty:
                total_funding_fee = funding_fees['Change'].sum()
                logger.info(f"\n=== 期货交易 ===")
                logger.info(f"总资金费用: {total_funding_fee:.2f} USDT")
                logger.info(f"资金费用笔数: {len(funding_fees)}")
    
    def save_results(self):
        """保存分析结果"""
        if self.daily_portfolio_value is not None:
            self.daily_portfolio_value.to_csv('portfolio_value.csv', index=False)
            logger.info("投资组合价值数据已保存到 portfolio_value.csv")
        
        # 保存资产余额
        balance_df = pd.DataFrame(list(self.asset_balances.items()), columns=['Asset', 'Balance'])
        balance_df.to_csv('final_balances.csv', index=False)
        logger.info("最终资产余额已保存到 final_balances.csv")
    
    def plot_results(self):
        """生成可视化图表"""
        try:
            plt.style.use('seaborn-v0_8')
            fig, axes = plt.subplots(2, 2, figsize=(15, 12))
            
            # 投资组合价值变化
            ax1 = axes[0, 0]
            ax1.plot(self.daily_portfolio_value['date'], self.daily_portfolio_value['portfolio_value'])
            ax1.set_title('投资组合价值变化')
            ax1.set_xlabel('日期')
            ax1.set_ylabel('价值 (USDT)')
            ax1.grid(True)
            
            # 日收益率分布
            ax2 = axes[0, 1]
            self.daily_portfolio_value['daily_return'].hist(bins=50, ax=ax2)
            ax2.set_title('日收益率分布')
            ax2.set_xlabel('收益率')
            ax2.set_ylabel('频次')
            ax2.grid(True)
            
            # 累计收益率
            ax3 = axes[1, 0]
            ax3.plot(self.daily_portfolio_value['date'], self.daily_portfolio_value['cumulative_return'] * 100)
            ax3.set_title('累计收益率')
            ax3.set_xlabel('日期')
            ax3.set_ylabel('收益率 (%)')
            ax3.grid(True)
            
            # 资产配置（饼图）
            ax4 = axes[1, 1]
            asset_values = []
            asset_names = []
            for asset, balance in self.asset_balances.items():
                if abs(balance) > 1e-8:
                    if asset == 'USDT':
                        value = balance
                    elif asset == 'BTC':
                        value = balance * 95000.0
                    else:
                        value = balance * self._get_price_estimate(asset, datetime.now())
                    
                    if value > 0:
                        asset_values.append(value)
                        asset_names.append(f"{asset}\n({value:.0f} USDT)")
            
            if asset_values:
                ax4.pie(asset_values, labels=asset_names, autopct='%1.1f%%')
                ax4.set_title('资产配置')
            
            plt.tight_layout()
            plt.savefig('portfolio_analysis.png', dpi=300, bbox_inches='tight')
            plt.show()
            logger.info("图表已保存到 portfolio_analysis.png")
            
        except Exception as e:
            logger.error(f"生成图表失败: {e}")

def main():
    """主函数"""
    # 使用您提供的交易记录文件
    csv_file = "binance_transactions.csv"
    
    # 创建分析器
    analyzer = BinanceTransactionAnalyzer(csv_file)
    
    # 加载数据
    if analyzer.load_data():
        # 分析数据
        if analyzer.analyze_transactions():
            # 生成报告
            analyzer.generate_report()
            
            # 保存结果
            analyzer.save_results()
            
            # 生成图表
            analyzer.plot_results()
            
            logger.info("\n分析完成！")
        else:
            logger.error("数据分析失败")
    else:
        logger.error("数据加载失败")

if __name__ == "__main__":
    main()
