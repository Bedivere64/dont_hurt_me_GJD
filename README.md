# ETF份额数据分析工具

上海证券交易所ETF份额历史数据采集与分析工具。

## 功能特性

- 自动采集ETF每日份额数据（支持全量837+只ETF）
- SQLite本地数据库存储
- 智能分页处理
- 节假日自动跳过
- 并发加速采集
- 份额趋势HTML可视化

## 项目结构

```
etf-project/
├── etf_db.py          # 数据库管理 + 查询分析
├── etf_trend.py       # 趋势图生成
├── etf_data.db        # SQLite数据库（自动创建）
├── requirements.txt   # 依赖
└── README.md
```

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

### 1. 采集数据

```bash
# 采集近半年数据（约126个交易日）
python etf_db.py fetch

# 采集指定天数
python etf_db.py fetch 252
```

### 2. 查询分析

```bash
# 查询份额上升的ETF
python etf_db.py query

# 查询近一年
python etf_db.py query 252
```

### 3. 生成趋势图

```bash
# 生成某ETF趋势图
python etf_trend.py 512070 500
```

### 4. 数据完整性检查

```bash
python etf_db.py check
```

## 数据库表结构

### etf_info - ETF基本信息
| 字段 | 类型 | 说明 |
|------|------|------|
| sec_code | TEXT | ETF代码 (PK) |
| sec_name | TEXT | ETF简称 |
| etf_type | TEXT | ETF类型 |

### etf_daily_share - 每日份额
| 字段 | 类型 | 说明 |
|------|------|------|
| sec_code | TEXT | ETF代码 (PK) |
| stat_date | TEXT | 日期 (PK) |
| tot_vol | REAL | 总份额 |
| num | INTEGER | 排名 |

## 数据来源

上海证券交易所 (SSE) 官方接口
- 接口: `commonQuery.do?sqlId=COMMON_SSE_ZQPZ_ETFZL_XXPL_ETFGM_SEARCH_L`
- 每日更新频率: 收盘后