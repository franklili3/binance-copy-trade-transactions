#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
比特币价格下载示例脚本
演示如何使用BinancePriceDownloader类下载比特币价格数据
"""

from download_btc_prices import BinancePriceDownloader
from datetime import datetime, timedelta
import pandas as pd

def example_basic_download():
    """基本下载示例：下载最近30天的BTC价格数据"""
    print("=== 基本下载示例 ===")
    
    # 创建下载器实例
    downloader = BinancePriceDownloader()
    
    # 下载最近30天的数据
    df = downloader.download_recent_days(days=30)
    
    if df is not None and not df.empty:
        # 保存数据
        downloader.save_to_csv(df, "btc_last_30_days.csv")
        
        # 显示基本信息
        print(f"下载了 {len(df)} 条记录")
        print(f"时间范围: {df['date'].min()} 到 {df['date'].max()}")
        print(f"价格范围: {df['close_price'].min():.2f} - {df['close_price'].max():.2f} USDT")
        print()
    else:
        print("下载失败")

def example_custom_range():
    """自定义日期范围下载示例"""
    print("=== 自定义日期范围下载示例 ===")
    
    downloader = BinancePriceDownloader()
    
    # 下载2024年1月的数据
    start_date = "2024-01-01"
    end_date = "2024-01-31"
    
    df = downloader.download_price_range(start_date, end_date)
    
    if df is not None and not df.empty:
        downloader.save_to_csv(df, "btc_january_2024.csv")
        print(f"下载了2024年1月的数据：{len(df)} 条记录")
        print(f"1月平均价格: {df['close_price'].mean():.2f} USDT")
        print(f"1月最高价: {df['close_price'].max():.2f} USDT")
        print(f"1月最低价: {df['close_price'].min():.2f} USDT")
        print()
    else:
        print("下载失败")

def example_different_intervals():
    """不同时间间隔下载示例"""
    print("=== 不同时间间隔下载示例 ===")
    
    downloader = BinancePriceDownloader()
    
    # 下载最近7天的1小时数据
    df_1h = downloader.download_price_range(
        start_date=(datetime.now() - timedelta(days=7)).date(),
        end_date=datetime.now().date(),
        interval='1h'
    )
    
    if df_1h is not None and not df_1h.empty:
        downloader.save_to_csv(df_1h, "btc_last_7_days_1h.csv")
        print(f"下载了最近7天的小时数据：{len(df_1h)} 条记录")
        print()
    
    # 下载最近1天的5分钟数据
    df_5m = downloader.download_price_range(
        start_date=(datetime.now() - timedelta(days=1)).date(),
        end_date=datetime.now().date(),
        interval='5m'
    )
    
    if df_5m is not None and not df_5m.empty:
        downloader.save_to_csv(df_5m, "btc_last_1_day_5m.csv")
        print(f"下载了最近1天的5分钟数据：{len(df_5m)} 条记录")
        print()

def example_different_symbols():
    """不同交易对下载示例"""
    print("=== 不同交易对下载示例 ===")
    
    downloader = BinancePriceDownloader()
    
    # 下载以太坊数据
    eth_df = downloader.download_recent_days(days=30, symbol='ETHUSDT')
    if eth_df is not None and not eth_df.empty:
        downloader.save_to_csv(eth_df, "eth_last_30_days.csv")
        print(f"下载了ETH数据：{len(eth_df)} 条记录")
        print(f"ETH价格范围: {eth_df['close_price'].min():.2f} - {eth_df['close_price'].max():.2f} USDT")
        print()
    
    # 下载币安币数据
    bnb_df = downloader.download_recent_days(days=30, symbol='BNBUSDT')
    if bnb_df is not None and not bnb_df.empty:
        downloader.save_to_csv(bnb_df, "bnb_last_30_days.csv")
        print(f"下载了BNB数据：{len(bnb_df)} 条记录")
        print(f"BNB价格范围: {bnb_df['close_price'].min():.2f} - {bnb_df['close_price'].max():.2f} USDT")
        print()

def analyze_downloaded_data():
    """分析下载的数据示例"""
    print("=== 数据分析示例 ===")
    
    # 假设我们已经下载了数据
    try:
        df = pd.read_csv("btc_last_30_days.csv")
        
        if not df.empty:
            print("数据分析结果：")
            print(f"总交易日数: {len(df)}")
            print(f"上涨天数: {len(df[df['price_change'] > 0])}")
            print(f"下跌天数: {len(df[df['price_change'] < 0])}")
            print(f"最大单日涨幅: {df['price_change'].max():.2%}")
            print(f"最大单日跌幅: {df['price_change'].min():.2%}")
            print(f"平均日成交量: {df['volume_usdt'].mean():,.0f} USDT")
            
            # 找出最高价和最低价的日期
            max_price_date = df.loc[df['close_price'].idxmax(), 'date']
            min_price_date = df.loc[df['close_price'].idxmin(), 'date']
            print(f"最高价日期: {max_price_date} ({df['close_price'].max():.2f} USDT)")
            print(f"最低价日期: {min_price_date} ({df['close_price'].min():.2f} USDT)")
            
            print()
        else:
            print("数据文件为空")
            
    except FileNotFoundError:
        print("请先运行下载示例生成数据文件")

def main():
    """主函数：运行所有示例"""
    print("比特币价格下载器示例")
    print("=" * 50)
    
    # 运行各种下载示例
    example_basic_download()
    example_custom_range()
    example_different_intervals()
    example_different_symbols()
    analyze_downloaded_data()
    
    print("=" * 50)
    print("所有示例运行完成！")
    print("请检查生成的CSV文件：")
    print("- btc_last_30_days.csv")
    print("- btc_january_2024.csv")
    print("- btc_last_7_days_1h.csv")
    print("- btc_last_1_day_5m.csv")
    print("- eth_last_30_days.csv")
    print("- bnb_last_30_days.csv")

if __name__ == "__main__":
    main()
