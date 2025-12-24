#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
币安交易记录分析器（增强版）
用于分析币安交易记录CSV文件并计算收益率
新增功能：从币安API获取比特币实时价格数据
"""

import pandas as pd
import numpy as np
import requests
from datetime import datetime, timezone, timedelta
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Tuple
import logging
import time

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BinancePriceAPI:
    """币安价格API类"""
    def __init__(self):
        self.base_url = "https://api.binance.com"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'BinanceTransactionAnalyzer/1.0'
        })
    
    def get_historical_klines(self, symbol='BTCUSDT', interval='1d', start_time=None, end_time=None, limit=1000):
        """获取历史K线数据"""
        try:
            params = {
                'symbol': symbol,
                'interval': interval,
                'limit': limit
            }
            
            if start_time:
                params['startTime'] = start_time
            if end_time:
                params['endTime'] = end_time
            
            response = self.session.get(f"{self.base_url}/api/v3/klines", params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            if not data:
                return pd.DataFrame()
            
            # 转换为DataFrame
            df = pd.DataFrame(data, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_asset_volume', 'number_of_trades',
                'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
            ])
            
            # 转换数据类型
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)
            df.set_index('datetime', inplace=True)
            
            # 只保留需要的列
            df = df[['open', 'high', 'low', 'close', 'volume']]
            
            logger.info(f"成功获取 {len(df)} 条{symbol}的历史价格数据")
            return df
            
        except requests.exceptions.RequestException as e:
            logger.error(f"获取价格数据失败: {e}")
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"处理价格数据失败: {e}")
            return pd.DataFrame()
    
    def get_price_for_date(self, date, symbol='BTCUSDT'):
        """获取指定日期的价格数据"""
        try:
            # 转换日期为时间戳
            start_of_day = datetime(date.year, date.month, date.day, 0, 0, 0, tzinfo=timezone.utc)
            end_of_day = start_of_day + timedelta(days=1)
            
            start_timestamp = int(start_of_day.timestamp() * 1000)
            end_timestamp = int(end_of_day.timestamp() * 1000)
            
            # 获取K线数据
            df = self.get_historical_klines(
                symbol=symbol,
                interval='1d',
                start_time=start_timestamp,
                end_time=end_timestamp,
                limit=1
            )
            
            if not df.empty:
                return df.iloc[0]['close']
            else:
                logger.warning(f"无法获取{date}的价格数据")
                return None
                
        except Exception as e:
            logger.error(f"获取{date}价格失败: {e}")
            return None
    
    def get_price_range(self, start_date, end_date, symbol='BTCUSDT'):
        """获取日期范围内的价格数据"""
        try:
            start_timestamp = int(start_date.timestamp() * 1000)
            end_timestamp = int(end_date.timestamp() * 1000)
            
            df = self.get_historical_klines(
                symbol=symbol,
                interval='1d',
                start_time=start_timestamp,
                end_time=end_timestamp,
                limit=1000
            )
            
            return df
            
        except Exception as e:
            logger.error(f"获取价格范围数据失败: {e}")
            return pd.DataFrame()

class BinanceTransactionAnalyzer:
    def __init__(self, csv_file_path: str):
        """初始化分析器"""
        self.csv_file = csv_file_path
        self.raw_data = None
        self.processed_data = None
        self.asset_balances = {}
        self.daily_portfolio_value = None
        self.price_api = BinancePriceAPI()
        self.btc_price_data = None
        
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
    
    def fetch_btc_price_data(self):
        """从币安API获取比特币价格数据"""
        try:
            logger.info("从币安API获取比特币价格数据...")
            
            # 获取交易记录的日期范围
            if self.raw_data is None:
                logger.error("请先加载交易数据")
                return False
            
            start_date = self.raw_data['UTC_Time'].min().date()
            end_date = self.raw_data['UTC_Time'].max().date()
            
            # 扩展日期范围，确保覆盖所有交易日
            start_date = start_date - timedelta(days=7)
            end_date = end_date + timedelta(days=1)
            
            logger.info(f"获取 {start_date} 到 {end_date} 的BTC价格数据")
            
            # 获取历史价格数据
            self.btc_price_data = self.price_api.get_price_range(start_date, end_date, 'BTCUSDT')
            
            if self.btc_price_data.empty:
                logger.warning("无法从API获取BTC价格数据，将使用备用方法")
                self.btc_price_data = self._get_backup_btc_prices(start_date, end_date)
            else:
                logger.info(f"成功获取 {len(self.btc_price_data)} 条BTC价格记录")
                logger.info(f"BTC价格范围: {self.btc_price_data['close'].min():.2f} - {self.btc_price_data['close'].max():.2f} USDT")
            
            return True
            
        except Exception as e:
            logger.error(f"获取BTC价格数据失败: {e}")
            return False
    
    def _get_backup_btc_prices(self, start_date, end_date):
        """备用方法：生成模拟BTC价格数据"""
        logger.warning("使用备用方法生成模拟BTC价格数据")
        
        try:
            date_range = pd.date_range(start=start_date, end=end_date, freq='D')
            
            # 生成模拟价格数据
            np.random.seed(42)
            base_price = 95000.0
            prices = []
            
            for i, date in enumerate(date_range):
                # 使用实际的价格波动模式
                if i == 0:
                    price = base_price
                else:
                    change = np.random.normal(0, 0.02)  # 2%的日波动
                    price = max(prices[-1] * (1 + change), 1000)  # 最低价格限制
                
                prices.append(price)
            
            df = pd.DataFrame({
                'close': prices,
                'volume': np.random.uniform(1000, 5000, len(date_range))
            }, index=date_range)
            
            logger.info(f"生成了 {len(df)} 天的模拟BTC价格数据")
            return df
            
        except Exception as e:
            logger.error(f"生成备用价格数据失败: {e}")
            return pd.DataFrame()
    
    def analyze_transactions(self):
        """分析交易数据"""
        if self.raw_data is None:
            logger.error("请先加载数据")
            return False
        
        logger.info("开始分析交易数据...")
        
        # 获取BTC价格数据
        if not self.fetch_btc_price_data():
            logger.warning("无法获取BTC价格数据，将使用固定价格估算")
        
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
    
    def _get_btc_price_for_date(self, date):
        """获取指定日期的BTC价格"""
        if self.btc_price_data is None or self.btc_price_data.empty:
            return 95000.0  # 默认价格
        
        # 尝试获取精确日期的价格
        date_obj = pd.Timestamp(date).date()
        if date_obj in self.btc_price_data.index:
            return self.btc_price_data.loc[date_obj, 'close']
        
        # 如果没有精确日期，使用最近的价格
        nearest_date = self.btc_price_data.index[
            self.btc_price_data.index.get_indexer([date_obj], method='nearest')[0]
        ]
        return self.btc_price_data.loc[nearest_date, 'close']
    
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
                        # 使用从API获取的BTC价格
                        btc_price = self._get_btc_price_for_date(date)
                        portfolio_value += balance * btc_price
                    else:
                        # 其他资产使用估算价格
                        price = self._get_price_estimate(asset, date)
                        portfolio_value += balance * price
                
                daily_values.append({
                    'date': date,
                    'portfolio_value': portfolio_value,
                    'USDT_balance': self.asset_balances['USDT'],
                    'BTC_balance': self.asset_balances['BTC'],
                    'BTC_price': self._get_btc_price_for_date(date)
                })
            else:
                daily_values.append({
                    'date': date,
                    'portfolio_value': 0.0,
                    'USDT_balance': 0.0,
                    'BTC_balance': 0.0,
                    'BTC_price': self._get_btc_price_for_date(date)
                })
        
        self.daily_portfolio_value = pd.DataFrame(daily_values)
        logger.info(f"计算了 {len(self.daily_portfolio_value)} 天的投资组合价值")
        
        # 打印价格信息
        if not self.daily_portfolio_value.empty:
            btc_prices = self.daily_portfolio_value['BTC_price']
            logger.info(f"BTC价格范围: {btc_prices.min():.2f} - {btc_prices.max():.2f} USDT")
            logger.info(f"投资组合价值范围: {self.daily_portfolio_value['portfolio_value'].min():.2f} - {self.daily_portfolio_value['portfolio_value'].max():.2f} USDT")
    
    def _get_price_estimate(self, coin: str, date) -> float:
        """获取资产价格估算（用于非BTC资产）"""
        # 简化的价格估算表
        price_estimates = {
            'USDT': 1.0,
            'BUSD': 1.0,
            'USD': 1.0,
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
        
        # 价格数据信息
        if self.btc_price_data is not None and not self.btc_price_data.empty:
            logger.info(f"BTC价格数据: {len(self.btc_price_data)} 条记录")
            logger.info(f"BTC价格范围: {self.btc_price_data['close'].min():.2f} - {self.btc_price_data['close'].max():.2f} USDT")
        
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
                    # 使用当前BTC价格计算价值
                    current_btc_price = self._get_btc_price_for_date(datetime.now())
                    value_usdt = balance * current_btc_price
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
        
        # 带单收益分析
        copy_trade_data = self.raw_data[self.raw_data['Operation'].str.contains('Copy Portfolio', na=False)]
        if not copy_trade_data.empty:
            copy_profit = copy_trade_data[copy_trade_data['Operation'].str.contains('Profit Sharing', na=False)]
            if not copy_profit.empty:
                total_copy_profit = copy_profit['Change'].sum()
                logger.info(f"\n=== 带单收益 ===")
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
            # 保存投资组合价值数据（包含BTC价格）
            self.daily_portfolio_value.to_csv('portfolio_value_with_prices.csv', index=False)
            logger.info("投资组合价值数据已保存到 portfolio_value_with_prices.csv")
        
        # 保存资产余额
        balance_df = pd.DataFrame(list(self.asset_balances.items()), columns=['Asset', 'Balance'])
        balance_df.to_csv('final_balances.csv', index=False)
        logger.info("最终资产余额已保存到 final_balances.csv")
        
        # 保存BTC价格数据
        if self.btc_price_data is not None and not self.btc_price_data.empty:
            self.btc_price_data.to_csv('btc_price_data.csv')
            logger.info("BTC价格数据已保存到 btc_price_data.csv")
    
    def plot_results(self):
        """生成可视化图表"""
        try:
            plt.style.use('seaborn-v0_8')
            fig, axes = plt.subplots(3, 2, figsize=(18, 15))
            
            # 投资组合价值变化
            ax1 = axes[0, 0]
            ax1.plot(self.daily_portfolio_value['date'], self.daily_portfolio_value['portfolio_value'], 
                    label='Portfolio Value', color='blue')
            ax1.set_title('投资组合价值变化')
            ax1.set_xlabel('日期')
            ax1.set_ylabel('价值 (USDT)')
            ax1.grid(True)
            ax1.legend()
            
            # BTC价格变化
            ax2 = axes[0, 1]
            ax2.plot(self.daily_portfolio_value['date'], self.daily_portfolio_value['BTC_price'], 
                    label='BTC Price', color='orange')
            ax2.set_title('BTC价格变化')
            ax2.set_xlabel('日期')
            ax2.set_ylabel('价格 (USDT)')
            ax2.grid(True)
            ax2.legend()
            
            # 日收益率分布
            ax3 = axes[1, 0]
            self.daily_portfolio_value['daily_return'].hist(bins=50, ax=ax3, color='green', alpha=0.7)
            ax3.set_title('日收益率分布')
            ax3.set_xlabel('收益率')
            ax3.set_ylabel('频次')
            ax3.grid(True)
            
            # 累计收益率
            ax4 = axes[1, 1]
            ax4.plot(self.daily_portfolio_value['date'], self.daily_portfolio_value['cumulative_return'] * 100, 
                    label='Cumulative Return', color='red')
            ax4.set_title('累计收益率')
            ax4.set_xlabel('日期')
            ax4.set_ylabel('收益率 (%)')
            ax4.grid(True)
            ax4.legend()
            
            # 投资组合价值 vs BTC价格
            ax5 = axes[2, 0]
            ax5_twin = ax5.twinx()
            line1 = ax5.plot(self.daily_portfolio_value['date'], self.daily_portfolio_value['portfolio_value'], 
                           'b-', label='Portfolio Value', color='blue')
            line2 = ax5_twin.plot(self.daily_portfolio_value['date'], 
                               self.daily_portfolio_value['portfolio_value'] / self.daily_portfolio_value['BTC_price'], 
                               'r--', label='Portfolio/BTC Ratio', color='purple')
            ax5.set_title('投资组合价值 vs BTC价格')
            ax5.set_xlabel('日期')
            ax5.set_ylabel('Portfolio Value (USDT)', color='blue')
            ax5_twin.set_ylabel('Portfolio/BTC Ratio', color='purple')
            ax5.grid(True)
            
            # 添加图例
            lines = line1 + line2
            labels = [l.get_label() for l in lines]
            ax5.legend(lines, labels, loc='upper left')
            
            # 资产配置（饼图）
            ax6 = axes[2, 1]
            asset_values = []
            asset_names = []
            
            # 计算各资产的当前价值
            current_date = self.daily_portfolio_value['date'].iloc[-1]
            for asset, balance in self.asset_balances.items():
                if abs(balance) > 1e-8:
                    if asset == 'USDT':
                        value = balance
                    elif asset == 'BTC':
                        btc_price = self._get_btc_price_for_date(current_date)
                        value = balance * btc_price
                    else:
                        value = balance * self._get_price_estimate(asset, current_date)
                    
                    if value > 0:
                        asset_values.append(value)
                        asset_names.append(f"{asset}\n({value:.0f} USDT)")
            
            if asset_values:
                ax6.pie(asset_values, labels=asset_names, autopct='%1.1f%%')
                ax6.set_title('资产配置')
            
            plt.tight_layout()
            plt.savefig('portfolio_analysis_enhanced.png', dpi=300, bbox_inches='tight')
            plt.show()
            logger.info("图表已保存到 portfolio_analysis_enhanced.png")
            
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
