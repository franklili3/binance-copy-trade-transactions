#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
比特币价格下载器
从币安API获取比特币历史价格数据并保存为CSV文件
"""

import pandas as pd
import requests
from datetime import datetime, timezone, timedelta
import logging
import argparse
import sys
import os

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BinancePriceDownloader:
    """币安价格下载器类"""
    def __init__(self):
        self.base_url = "https://api.binance.com"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'BTCPriceDownloader/1.0'
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
            
            logger.info(f"正在获取 {symbol} 的历史数据...")
            response = self.session.get(f"{self.base_url}/api/v3/klines", params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            if not data:
                logger.warning("API返回空数据")
                return pd.DataFrame()
            
            # 转换为DataFrame
            df = pd.DataFrame(data, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_asset_volume', 'number_of_trades',
                'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
            ])
            
            # 转换数据类型
            numeric_columns = ['open', 'high', 'low', 'close', 'volume', 
                             'quote_asset_volume', 'number_of_trades',
                             'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume']
            
            for col in numeric_columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # 转换时间戳
            df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)
            df['date'] = df['datetime'].dt.date
            
            # 重命名列以更清晰
            df = df.rename(columns={
                'open': 'open_price',
                'high': 'high_price', 
                'low': 'low_price',
                'close': 'close_price',
                'volume': 'volume_btc',
                'quote_asset_volume': 'volume_usdt',
                'number_of_trades': 'trade_count',
                'taker_buy_base_asset_volume': 'taker_buy_volume_btc',
                'taker_buy_quote_asset_volume': 'taker_buy_volume_usdt'
            })
            
            # 选择有用的列
            df = df[[
                'date', 'datetime', 'open_price', 'high_price', 'low_price', 'close_price',
                'volume_btc', 'volume_usdt', 'trade_count', 'taker_buy_volume_btc', 'taker_buy_volume_usdt'
            ]]
            
            logger.info(f"成功获取 {len(df)} 条{symbol}的历史价格数据")
            return df
            
        except requests.exceptions.RequestException as e:
            logger.error(f"网络请求失败: {e}")
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"处理价格数据失败: {e}")
            return pd.DataFrame()
    
    def download_price_range(self, start_date, end_date, symbol='BTCUSDT', interval='1d'):
        """下载指定日期范围内的价格数据"""
        try:
            # 转换日期为时间戳
            if isinstance(start_date, str):
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            if isinstance(end_date, str):
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            
            start_datetime = datetime.combine(start_date, datetime.min.time(), tzinfo=timezone.utc)
            end_datetime = datetime.combine(end_date, datetime.max.time(), tzinfo=timezone.utc)
            
            start_timestamp = int(start_datetime.timestamp() * 1000)
            end_timestamp = int(end_datetime.timestamp() * 1000)
            
            logger.info(f"下载 {start_date} 到 {end_date} 的 {symbol} 价格数据")
            
            # 获取数据
            df = self.get_historical_klines(
                symbol=symbol,
                interval=interval,
                start_time=start_timestamp,
                end_time=end_timestamp,
                limit=1000
            )
            
            if df.empty:
                logger.error("未能获取到价格数据")
                return None
            
            # 添加一些有用的计算列
            df['price_change'] = df['close_price'].pct_change()
            df['price_change_abs'] = df['close_price'].diff()
            df['high_low_ratio'] = df['high_price'] / df['low_price']
            df['volume_ratio'] = df['taker_buy_volume_usdt'] / df['volume_usdt']
            
            # 计算移动平均线
            df['ma_7'] = df['close_price'].rolling(window=7).mean()
            df['ma_30'] = df['close_price'].rolling(window=30).mean()
            df['ma_90'] = df['close_price'].rolling(window=90).mean()
            
            return df
            
        except Exception as e:
            logger.error(f"下载价格范围数据失败: {e}")
            return None
    
    def download_recent_days(self, days=365, symbol='BTCUSDT', interval='1d'):
        """下载最近N天的价格数据"""
        try:
            end_date = datetime.now(timezone.utc).date()
            start_date = end_date - timedelta(days=days-1)
            
            return self.download_price_range(start_date, end_date, symbol, interval)
            
        except Exception as e:
            logger.error(f"下载最近{days}天数据失败: {e}")
            return None
    
    def save_to_csv(self, df, filename):
        """保存数据到CSV文件"""
        try:
            if df.empty:
                logger.error("没有数据可保存")
                return False
            
            # 确保文件名以.csv结尾
            if not filename.endswith('.csv'):
                filename += '.csv'
            
            # 保存到CSV
            df.to_csv(filename, index=False, encoding='utf-8')
            
            logger.info(f"数据已保存到 {filename}")
            logger.info(f"保存了 {len(df)} 条记录")
            logger.info(f"数据时间范围: {df['date'].min()} 到 {df['date'].max()}")
            logger.info(f"价格范围: {df['close_price'].min():.2f} - {df['close_price'].max():.2f} USDT")
            
            return True
            
        except Exception as e:
            logger.error(f"保存CSV文件失败: {e}")
            return False

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='下载比特币历史价格数据')
    parser.add_argument('--start-date', type=str, help='开始日期 (YYYY-MM-DD)')
    parser.add_argument('--end-date', type=str, help='结束日期 (YYYY-MM-DD)')
    parser.add_argument('--days', type=int, default=365, help='下载最近N天的数据 (默认365)')
    parser.add_argument('--symbol', type=str, default='BTCUSDT', help='交易对符号 (默认BTCUSDT)')
    parser.add_argument('--interval', type=str, default='1d', help='时间间隔 (默认1d)')
    parser.add_argument('--output', type=str, default='btc_prices.csv', help='输出文件名 (默认btc_prices.csv)')
    
    args = parser.parse_args()
    
    # 创建下载器
    downloader = BinancePriceDownloader()
    
    # 下载数据
    if args.start_date and args.end_date:
        # 指定日期范围
        df = downloader.download_price_range(args.start_date, args.end_date, args.symbol, args.interval)
    else:
        # 下载最近N天
        df = downloader.download_recent_days(args.days, args.symbol, args.interval)
    
    if df is None or df.empty:
        logger.error("未能获取到价格数据")
        sys.exit(1)
    
    # 保存数据
    if downloader.save_to_csv(df, args.output):
        logger.info("下载完成！")
        
        # 显示数据摘要
        print("\n=== 数据摘要 ===")
        print(f"记录数量: {len(df)}")
        print(f"时间范围: {df['date'].min()} 到 {df['date'].max()}")
        print(f"价格范围: {df['close_price'].min():.2f} - {df['close_price'].max():.2f} USDT")
        print(f"平均价格: {df['close_price'].mean():.2f} USDT")
        print(f"最高成交量: {df['volume_usdt'].max():,.0f} USDT")
        print(f"总成交量: {df['volume_usdt'].sum():,.0f} USDT")
        
        # 显示前几行数据
        print("\n=== 前5条记录 ===")
        print(df[['date', 'open_price', 'high_price', 'low_price', 'close_price', 'volume_usdt']].head())
        
        print(f"\n完整数据已保存到: {args.output}")
    else:
        logger.error("保存失败")
        sys.exit(1)

if __name__ == "__main__":
    main()
