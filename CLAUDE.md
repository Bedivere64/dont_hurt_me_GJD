# ETF份额数据分析工具

上海证券交易所ETF份额历史数据采集与分析工具。

## 项目结构

```
etf-project/
├── src/etf/              # 核心包
│   ├── __init__.py
│   ├── database.py       # 数据库操作
│   ├── fetcher.py        # 数据拉取
│   ├── queries.py         # 数据查询
│   └── cli.py            # CLI入口
├── scripts/              # 独立工具
│   ├── etf_trend.py      # 趋势图生成
│   └── etf_compare.py    # ETF对比
├── data/                 # 数据目录
│   └── etf_data.db       # SQLite数据库
├── skills/               # Claude Code技能
│   └── etf/
└── tests/                # 测试目录
```

## 常用命令

```bash
# 采集数据
python -m src.etf.cli fetch 5

# 查看证券ETF份额变化
python -m src.etf.cli securities

# 份额增加前10
python -m src.etf.cli top 10

# 份额增幅前10
python -m src.etf.cli top_pct 10

# 查看某ETF趋势
python -m src.etf.cli trend 512880

# 检查数据完整性
python -m src.etf.cli check

# 生成趋势图HTML
python scripts/etf_trend.py 512880 500

# 生成对比图
python scripts/etf_compare.py 510300 500
```

## 数据更新时机

**重要**: A股清算后数据才更新，约晚上8-10点后能查到当天数据。

## 数据库字段

- `sec_name` - ETF简称（如"证券ETF"）
- `full_name` - ETF全称（含公司，如"证券ETF国泰"）
- `tot_vol` - 总份额（单位：万份）
