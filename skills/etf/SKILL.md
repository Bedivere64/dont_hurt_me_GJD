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

### 6. 生成趋势图HTML
```bash
python scripts/etf_trend.py 512880 500
```

### 7. 生成ETF对比图
```bash
python scripts/etf_compare.py 510300 500
```

## 数据库字段说明

- `sec_name` - ETF简称（如"证券ETF"）
- `full_name` - ETF全称（含公司，如"证券ETF国泰"）
- `tot_vol` - 总份额（单位：万份）
