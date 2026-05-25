---
name: etf
description: ETF份额数据分析工具 - 查询证券ETF份额变化、份额增减排行、ETF趋势等
user-invocable: true
---

# ETF份额数据分析工具

基于上海证券交易所数据的ETF份额分析工具。

## 数据更新时机

**重要**: A股清算后数据才更新，约晚上8-10点后能查到当天数据。白天查不到当天数据是正常的。

## 常用命令

### 1. 更新数据
```bash
python -m src.etf.cli fetch 5
```

### 2. 证券ETF份额变化
```bash
python -m src.etf.cli securities         # 按份额从高到低
python -m src.etf.cli securities change   # 按变化从高到低
python -m src.etf.cli securities pct      # 按增幅从高到低
```

### 3. 份额增加/增幅排行
```bash
python -m src.etf.cli top 10      # 份额增加前10
python -m src.etf.cli top_pct 10 # 份额增幅前10
```

### 4. 特定ETF查询
```bash
python -m src.etf.cli trend 510300   # 沪深300ETF
python -m src.etf.cli trend 512880   # 证券ETF
```

### 5. 检查数据完整性
```bash
python -m src.etf.cli check
```

### 6. 十大持有人数据
```bash
python -m src.etf.cli holders              # 采集所有ETF十大持有人（从新浪财经）
python -m src.etf.cli holders 512880       # 查看某ETF十大持有人
python -m src.etf.cli holders_type 保险    # 按持有人类型查询（如：保险/信托/私募）
```

### 7. 生成趋势图HTML
```bash
python scripts/etf_trend.py 512880 500
```

### 8. 生成ETF对比图
```bash
python scripts/etf_compare.py 510300 500
```

## 数据库字段说明

### etf_info - ETF基本信息

| 字段      | 类型 | 说明              |
| --------- | ---- | ----------------- |
| sec_code  | TEXT | ETF代码 (PK)      |
| sec_name  | TEXT | ETF简称           |
| full_name | TEXT | ETF全称（含公司） |
| etf_type  | TEXT | ETF类型           |

### etf_daily_share - 每日份额

| 字段      | 类型    | 说明           |
| --------- | ------- | -------------- |
| sec_code  | TEXT    | ETF代码 (PK)   |
| stat_date | TEXT    | 日期 (PK)      |
| tot_vol   | REAL    | 总份额（万份） |
| num       | INTEGER | 排名           |

### etf_top_holders - ETF十大持有人

| 字段        | 类型    | 说明               |
| ----------- | ------- | ------------------ |
| sec_code    | TEXT    | ETF代码            |
| stat_date   | TEXT    | 报告期（如2025-12-31） |
| rank        | INTEGER | 排名（1-10）      |
| holder_name | TEXT    | 持有人名称         |
| holder_share| REAL    | 持有份额（份）     |
| holder_pct  | REAL    | 占总份额比（%）    |

> 数据来源：新浪财经基金档案页，每年4-5月更新年报，8-9月更新半年报。实时性约滞后4-5个月。