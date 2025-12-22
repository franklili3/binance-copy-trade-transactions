#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试收益率计算问题
"""

import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def debug_position_calculation():
    """调试持仓计算过程"""
    logger.info("=== 调试持仓计算过程 ===")
    
    # 创建测试数据
    end_date = pd.Timestamp.now().normalize()  # 使用pandas Timestamp的normalize方法
    start_date = end_date - timedelta(days=30)
    date_range = pd.date_range(start=start_date, end=end_date, freq='D')
    
    # 创建价格数据
    np.random.seed(42)
    base_price = 95000.0
    price_changes = np.random.normal(0, 0.02, len(date_range))
    prices = [base_price]
    for change in price_changes[1:]:
        new_price = prices[-1] * (1 + change)
        prices.append(max(new_price, 1000))
    
    btc_price_df = pd.DataFrame({'close': prices}, index=date_range)
    logger.info(f"价格数据范围: {btc_price_df.index.min()} 到 {btc_price_df.index.max()}")
    
    # 创建持仓DataFrame
    positions_df = pd.DataFrame(index=date_range)
    positions_df['BTC'] = 0.0
    positions_df['USDT'] = 0.0
    
    # 添加一些初始USDT余额
    initial_usdt = 10000.0
    positions_df['USDT'] = initial_usdt
    
    logger.info(f"初始持仓: BTC={positions_df.loc[positions_df.index[0], 'BTC']}, USDT={positions_df.loc[positions_df.index[0], 'USDT']}")
    
    # 模拟交易 - 确保有买卖不平衡
    transactions = [
        {
            'datetime': (start_date + timedelta(days=5)).isoformat(),
            'symbol': 'BTC/USDT',
            'side': 'buy',
            'amount': 0.1,  # 买入0.1 BTC
            'price': 95000,
            'cost': 9500  # 花费9500 USDT
        },
        {
            'datetime': (start_date + timedelta(days=15)).isoformat(),
            'symbol': 'BTC/USDT',
            'side': 'sell',
            'amount': 0.05,  # 卖出0.05 BTC
            'price': 97000,
            'cost': 4850  # 获得4850 USDT
        }
    ]
    
    logger.info(f"模拟交易: {len(transactions)} 笔")
    
    # 处理交易
    for tx in transactions:
        tx_date = pd.to_datetime(tx['datetime']).normalize()  # 移除时区信息
        logger.info(f"处理交易日期: {tx_date}")
        logger.info(f"日期范围最小值: {positions_df.index.min()}")
        logger.info(f"日期范围最大值: {positions_df.index.max()}")
        
        if tx_date not in positions_df.index:
            logger.warning(f"交易日期 {tx_date} 不在日期范围内")
            # 尝试找到最近的日期
            nearest_idx = positions_df.index.get_indexer([tx_date], method='nearest')[0]
            tx_date = positions_df.index[nearest_idx]
            logger.info(f"使用最近日期: {tx_date}")
        
        symbol = tx['symbol']
        side = tx['side']
        amount = tx['amount']
        cost = tx['cost']
        
        if symbol == 'BTC/USDT':
            if side == 'buy':
                # 买入BTC：减少USDT，增加BTC
                logger.info(f"买入 {amount} BTC，花费 {cost} USDT")
                positions_df.loc[tx_date:, 'BTC'] += amount
                positions_df.loc[tx_date:, 'USDT'] -= cost
            else:  # sell
                # 卖出BTC：增加USDT，减少BTC
                logger.info(f"卖出 {amount} BTC，获得 {cost} USDT")
                positions_df.loc[tx_date:, 'BTC'] -= amount
                positions_df.loc[tx_date:, 'USDT'] += cost
    
    # 显示持仓变化
    logger.info("\n=== 持仓变化 ===")
    key_dates = [0, 5, 6, 15, 16, -1]  # 关键日期索引
    for idx in key_dates:
        if idx < len(positions_df):
            date = positions_df.index[idx]
            btc = positions_df.iloc[idx]['BTC']
            usdt = positions_df.iloc[idx]['USDT']
            logger.info(f"{date.strftime('%Y-%m-%d')}: BTC={btc:.6f}, USDT={usdt:.2f}")
    
    # 计算投资组合价值
    logger.info("\n=== 投资组合价值计算 ===")
    portfolio_values = []
    
    for date in positions_df.index:
        btc_holding = positions_df.loc[date, 'BTC']
        usdt_holding = positions_df.loc[date, 'USDT']
        
        if date in btc_price_df.index:
            btc_price = btc_price_df.loc[date, 'close']
        else:
            nearest_date = btc_price_df.index[btc_price_df.index.get_indexer([date], method='nearest')[0]]
            btc_price = btc_price_df.loc[nearest_date, 'close']
        
        portfolio_value = (btc_holding * btc_price) + usdt_holding
        portfolio_values.append(portfolio_value)
        
        if date in [positions_df.index[0], positions_df.index[5], positions_df.index[15], positions_df.index[-1]]:
            logger.info(f"{date.strftime('%Y-%m-%d')}: BTC={btc_holding:.6f} × {btc_price:.2f} + USDT={usdt_holding:.2f} = {portfolio_value:.2f}")
    
    portfolio_series = pd.Series(portfolio_values, index=positions_df.index)
    
    # 计算收益率
    returns = portfolio_series.pct_change().fillna(0)
    
    logger.info(f"\n=== 收益率统计 ===")
    logger.info(f"投资组合价值范围: {portfolio_series.min():.2f} - {portfolio_series.max():.2f} USDT")
    logger.info(f"收益率范围: {returns.min():.6f} - {returns.max():.6f}")
    logger.info(f"非零收益率天数: {(returns != 0).sum()}")
    
    # 显示非零收益率
    non_zero_returns = returns[returns != 0]
    if not non_zero_returns.empty:
        logger.info("\n非零收益率:")
        for date, ret in non_zero_returns.head().items():
            logger.info(f"  {date.strftime('%Y-%m-%d')}: {ret:.6f} ({ret*100:.4f}%)")
    else:
        logger.warning("所有收益率都是0！")
    
    return returns

if __name__ == "__main__":
    try:
        returns = debug_position_calculation()
        
        if (returns != 0).any():
            logger.info("✓ 调试成功：发现非零收益率")
        else:
            logger.error("✗ 调试失败：所有收益率仍为0")
            
    except Exception as e:
        logger.error(f"调试过程中出错: {e}")
        import traceback
        logger.error(f"错误详情: {traceback.format_exc()}")
