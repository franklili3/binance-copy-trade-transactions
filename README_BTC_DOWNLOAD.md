# 比特币价格下载器使用说明

## 概述

`download_btc_prices.py` 是一个专门用于从币安API下载比特币历史价格数据并保存为CSV文件的Python脚本。

## 功能特性

- 从币安API获取实时和历史比特币价格数据
- 支持自定义日期范围下载
- 支持多种时间间隔（1分钟、5分钟、1小时、1天等）
- 自动计算技术指标（移动平均线、价格变化等）
- 生成详细的CSV文件，包含完整的OHLCV数据
- 提供数据摘要统计

## 安装依赖

```bash
pip install pandas requests
```

## 使用方法

### 基本用法

#### 1. 下载最近365天的数据（默认）
```bash
python download_btc_prices.py
```

#### 2. 下载指定天数的数据
```bash
python download_btc_prices.py --days 30
```

#### 3. 下载指定日期范围的数据
```bash
python download_btc_prices.py --start-date 2024-01-01 --end-date 2024-12-31
```

#### 4. 自定义输出文件名
```bash
python download_btc_prices.py --output my_btc_prices.csv
```

### 高级用法

#### 1. 下载不同交易对的数据
```bash
python download_btc_prices.py --symbol ETHUSDT --days 30
```

#### 2. 使用不同的时间间隔
```bash
# 1小时K线
python download_btc_prices.py --interval 1h --days 7

# 5分钟K线
python download_btc_prices.py --interval 5m --days 1

# 1周K线
python download_btc_prices.py --interval 1w --days 52
```

#### 3. 组合参数使用
```bash
python download_btc_prices.py \
  --start-date 2024-06-01 \
  --end-date 2024-06-30 \
  --interval 4h \
  --symbol BTCUSDT \
  --output btc_june_2024_4h.csv
```

## 命令行参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--start-date` | str | 无 | 开始日期，格式：YYYY-MM-DD |
| `--end-date` | str | 无 | 结束日期，格式：YYYY-MM-DD |
| `--days` | int | 365 | 下载最近N天的数据 |
| `--symbol` | str | BTCUSDT | 交易对符号 |
| `--interval` | str | 1d | 时间间隔（1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w, 1M） |
| `--output` | str | btc_prices.csv | 输出CSV文件名 |

## 输出文件格式

生成的CSV文件包含以下列：

| 列名 | 说明 |
|------|------|
| `date` | 日期（YYYY-MM-DD） |
| `datetime` | 完整时间戳（UTC） |
| `open_price` | 开盘价（USDT） |
| `high_price` | 最高价（USDT） |
| `low_price` | 最低价（USDT） |
| `close_price` | 收盘价（USDT） |
| `volume_btc` | 成交量（BTC） |
| `volume_usdt` | 成交量（USDT） |
| `trade_count` | 交易次数 |
| `taker_buy_volume_btc` | 主动买入量（BTC） |
| `taker_buy_volume_usdt` | 主动买入量（USDT） |
| `price_change` | 价格变化百分比 |
| `price_change_abs` | 价格变化绝对值 |
| `high_low_ratio` | 最高最低价比 |
| `volume_ratio` | 主动买入量占比 |
| `ma_7` | 7日移动平均线 |
| `ma_30` | 30日移动平均线 |
| `ma_90` | 90日移动平均线 |

## 使用示例

### 示例1：下载2024年全年数据
```bash
python download_btc_prices.py --start-date 2024-01-01 --end-date 2024-12-31 --output btc_2024_yearly.csv
```

### 示例2：下载最近30天的1小时数据
```bash
python download_btc_prices.py --days 30 --interval 1h --output btc_30d_1h.csv
```

### 示例3：下载以太坊价格数据
```bash
python download_btc_prices.py --symbol ETHUSDT --days 90 --output eth_90d.csv
```

## 输出示例

运行脚本后，你会看到类似以下的输出：

```
2024-12-24 10:00:00,000 - INFO - 正在获取 BTCUSDT 的历史数据...
2024-12-24 10:00:01,000 - INFO - 成功获取 365 条BTCUSDT的历史价格数据
2024-12-24 10:00:01,000 - INFO - 数据已保存到 btc_prices.csv
2024-12-24 10:00:01,000 - INFO - 保存了 365 条记录
2024-12-24 10:00:01,000 - INFO - 数据时间范围: 2023-12-24 到 2024-12-23
2024-12-24 10:00:01,000 - INFO - 价格范围: 38,500.00 - 108,000.00 USDT
2024-12-24 10:00:01,000 - INFO - 下载完成！

=== 数据摘要 ===
记录数量: 365
时间范围: 2023-12-24 到 2024-12-23
价格范围: 38,500.00 - 108,000.00 USDT
平均价格: 67,234.56 USDT
最高成交量: 5,234,567,890 USDT
总成交量: 1,234,567,890,123 USDT

=== 前5条记录 ===
        date  open_price  high_price   low_price  close_price  volume_usdt
0  2023-12-24    42150.5     42580.3    41890.2      42345.8  1234567890
1  2023-12-25    42345.8     42890.1    42100.5      42678.9  1345678901
2  2023-12-26    42678.9     43210.5    42456.7      42987.3  1456789012
3  2023-12-27    42987.3     43567.8    42789.0      43345.6  1567890123
4  2023-12-28    43345.6     43987.2    43123.4      43789.1  1678901234

完整数据已保存到: btc_prices.csv
```

## 注意事项

1. **API限制**：币安API有请求频率限制，避免短时间内发送过多请求
2. **网络连接**：确保服务器有稳定的网络连接访问币安API
3. **时间范围**：单次请求最多获取1000条记录，如需更多数据请分批下载
4. **时区**：所有时间戳均为UTC时间
5. **数据完整性**：如果某天没有交易数据，API可能不会返回该天的记录

## 错误处理

脚本包含完善的错误处理机制：

- 网络连接失败时自动重试
- API返回空数据时给出明确提示
- 数据解析错误时记录详细日志
- 文件保存失败时提供错误信息

## 扩展功能

如需扩展功能，可以修改脚本中的以下部分：

1. **添加更多技术指标**：在`download_price_range`方法中添加新的计算列
2. **支持更多交易所**：修改API端点以支持其他交易所
3. **数据验证**：添加数据质量检查和清洗逻辑
4. **定时任务**：结合cron实现定时下载更新数据

## 许可证

本脚本仅供学习和研究使用，请遵守相关API使用条款。
