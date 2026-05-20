# ETF份额数据分析工具

上海证券交易所ETF份额历史数据采集与分析工具。

## 功能特性

- 自动采集ETF每日份额数据（支持全量800+只ETF）
- SQLite本地数据库存储
- 智能分页处理
- 节假日自动跳过
- 并发加速采集
- 份额趋势HTML可视化
- 支持简称/全称切换展示

## 项目结构

```
etf-project/
├── src/etf/              # 核心包
│   ├── __init__.py
│   ├── database.py       # 数据库操作
│   ├── fetcher.py        # 数据拉取
│   ├── queries.py        # 数据查询
│   └── cli.py            # 命令行入口
├── scripts/              # 独立脚本
│   ├── etf_trend.py      # 趋势图生成
│   └── etf_compare.py    # ETF对比工具
├── data/                 # 数据目录
│   └── etf_data.db       # SQLite数据库
├── tests/                # 测试目录
├── docs/                 # 文档目录
├── .claude/skills/etf/   # Claude Code技能
├── README.md
├── requirements.txt
└── pyproject.toml
```

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

### 命令行工具（推荐）

```bash
# 采集数据
python -m src.etf.cli fetch 5

# 查询份额上升的ETF
python -m src.etf.cli query 126

# 查看证券ETF份额变化
python -m src.etf.cli securities

# 份额增加前10名
python -m src.etf.cli top 10

# 份额增幅前10名
python -m src.etf.cli top_pct 10

# 查看某ETF趋势
python -m src.etf.cli trend 512880

# 检查数据完整性
python -m src.etf.cli check

# 更新ETF完整名称
python -m src.etf.cli update_names
```

### 独立脚本

```bash
# 生成ETF趋势HTML图
python scripts/etf_trend.py 512880 500

# 对比两只ETF
python scripts/etf_compare.py 512880 512070
```

## 数据库表结构

### etf_info - ETF基本信息
| 字段 | 类型 | 说明 |
|------|------|------|
| sec_code | TEXT | ETF代码 (PK) |
| sec_name | TEXT | ETF简称 |
| full_name | TEXT | ETF全称（含公司） |
| etf_type | TEXT | ETF类型 |

### etf_daily_share - 每日份额
| 字段 | 类型 | 说明 |
|------|------|------|
| sec_code | TEXT | ETF代码 (PK) |
| stat_date | TEXT | 日期 (PK) |
| tot_vol | REAL | 总份额（万份） |
| num | INTEGER | 排名 |

## 数据来源

上海证券交易所 (SSE) 官方接口
- 份额接口: `commonQuery.do?sqlId=COMMON_SSE_ZQPZ_ETFZL_XXPL_ETFGM_SEARCH_L`
- 全称接口: `security/stock/queryExpandName.do`
- 每日更新频率: 收盘后清算完成后（约20:00-22:00）
