# ETF 份额数据分析平台 - 架构设计文档

## 1. 项目概述

### 1.1 项目背景
上海证券交易所 ETF 份额历史数据采集与分析工具，提供数据可视化展示和对比分析功能。

### 1.2 项目地址
- 域名: bedivere.space
- 服务器: 45.145.228.58

### 1.3 数据规模
| 指标 | 数值 |
|------|------|
| 总记录数 | 332,184 条 |
| 日增量 | ~300-500 条 |
| 数据大小 | 40MB |

---

## 2. 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                        用户浏览器                            │
│                     https://bedivere.space                  │
└────────────────────────────┬────────────────────────────────┘
                             │ HTTPS (Let's Encrypt)
                             ↓
┌─────────────────────────────────────────────────────────────┐
│                         Nginx                               │
│                    (443 / 80 → 443)                        │
│  ┌─────────────────┐    ┌────────────────────────────────┐ │
│  │  静态资源服务    │    │     Flask API 反向代理          │ │
│  │  /              │    │     /api/*                      │ │
│  └─────────────────┘    └────────────────────────────────┘ │
└────────────────────────────┬────────────────────────────────┘
                             │
              ┌───────────────┴───────────────┐
              ↓                               ↓
┌─────────────────────────┐     ┌─────────────────────────────┐
│      React 前端          │     │       Flask API            │
│   (端口: 3000)           │     │   (Gunicorn 端口: 8000)     │
│   npm run dev/build     │     └─────────────┬───────────────┘
└─────────────────────────┘                   │
                                              ↓
                              ┌─────────────────────────────┐
                              │       PostgreSQL            │
                              │       (端口: 5432)           │
                              └─────────────────────────────┘
```

---

## 3. 技术选型

| 组件 | 技术选型 | 版本 | 说明 |
|------|----------|------|------|
| 前端框架 | React + Vite | latest | 快速构建，热更新 |
| UI 组件库 | shadcn/ui | latest | 苹果风格，定制性强 |
| 后端框架 | Flask | 3.x | 你熟悉 |
| ORM | SQLAlchemy + Flask-SQLAlchemy | latest |  |
| 数据库 | PostgreSQL | 16 | 稳定，JSON支持好 |
| WSGI 服务器 | Gunicorn | latest | 生产级 |
| Web 服务器 | Nginx | apt | 反向代理 + 静态资源 |
| HTTPS | Let's Encrypt (certbot) | | 免费自动续期 |
| 数据采集 | 现有脚本 | - | 复用现有 etf_data.db 的采集逻辑 |

---

## 4. 功能模块划分

### 4.1 前端模块

```
frontend/
├── src/
│   ├── pages/
│   │   ├── Dashboard/           # 首页/仪表盘
│   │   ├── ETFRanking/         # ETF 份额排行榜
│   │   ├── ETFTrend/           # 单只 ETF 趋势图
│   │   ├── ETFCompare/         # ETF 对比分析
│   │   └── Search/             # 搜索页面
│   │
│   ├── components/
│   │   ├── ui/                 # shadcn/ui 基础组件
│   │   ├── charts/             # 图表组件 (ECharts)
│   │   ├── tables/             # 表格组件
│   │   └── layout/             # 布局组件 (Header, Sidebar)
│   │
│   ├── hooks/                  # React Hooks
│   ├── services/               # API 调用层
│   ├── stores/                 # 状态管理
│   └── lib/                    # 工具函数
```

#### 页面功能说明

| 页面 | 路由 | 功能描述 |
|------|------|----------|
| 首页仪表盘 | `/` | 展示市场概览、热门 ETF、涨跌幅排行 |
| 份额排行榜 | `/ranking` | 按份额/增幅排名，支持筛选和搜索 |
| ETF 趋势 | `/trend/:code` | 单只 ETF 份额历史走势图 |
| ETF 对比 | `/compare` | 多只 ETF 份额/走势对比 |
| 搜索 | `/search` | 搜索 ETF 名称/代码 |

### 4.2 后端模块

```
backend/
├── app/
│   ├── __init__.py            # Flask 应用工厂
│   ├── config.py              # 配置文件
│   ├── models.py              # 数据模型
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── etf.py             # ETF 相关 API
│   │   └── health.py          # 健康检查
│   ├── services/
│   │   ├── __init__.py
│   │   └── etf_service.py     # ETF 业务逻辑
│   └── utils/
│       ├── __init__.py
│       └── date_utils.py       # 日期工具
│
├── migrations/                # 数据库迁移 (Alembic)
├── scripts/
│   └── fetch_data.py          # 数据采集脚本
│
├── requirements.txt
└── run.py                    # 应用入口
```

#### API 设计

| 方法 | 路由 | 描述 | 响应 |
|------|------|------|------|
| GET | `/api/health` | 健康检查 | `{status: "ok"}` |
| GET | `/api/etf/list` | ETF 列表 | 分页数据 |
| GET | `/api/etf/:code` | 单只 ETF 详情 | ETF 基本信息 |
| GET | `/api/etf/:code/trend` | 份额趋势 | 时间序列数据 |
| GET | `/api/etf/:code/shares` | 份额数据 | 日度份额数据 |
| GET | `/api/etf/ranking` | 排行榜 | 排名列表 |
| GET | `/api/etf/compare` | 对比数据 | 多只 ETF 数据 |
| POST | `/api/etf/fetch` | 触发数据采集 | 采集结果 |

---

## 5. 数据库设计

### 5.1 PostgreSQL 表结构

```sql
-- ETF 基本信息表
CREATE TABLE etf_info (
    sec_code VARCHAR(20) PRIMARY KEY,  -- 证券代码，如 '512880'
    sec_name VARCHAR(100),            -- ETF 简称，如 '证券ETF'
    full_name VARCHAR(200),            -- ETF 全称，如 '证券ETF国泰'
    list_date DATE,                    -- 上市日期
    fund_manager VARCHAR(100),         -- 基金管理人
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ETF 日度份额数据表
CREATE TABLE etf_daily_share (
    id SERIAL PRIMARY KEY,
    sec_code VARCHAR(20) NOT NULL,      -- 证券代码
    stat_date DATE NOT NULL,           -- 统计日期
    tot_vol REAL,                      -- 总份额（万份）
    num INTEGER,                        -- 持有人数
    close_price REAL,                  -- 收盘价
    market VARCHAR(10) DEFAULT 'SH',   -- 市场 (SH/SZ)
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(sec_code, stat_date)
);

-- 索引
CREATE INDEX idx_etf_daily_share_sec_code ON etf_daily_share(sec_code);
CREATE INDEX idx_etf_daily_share_stat_date ON etf_daily_share(stat_date);
CREATE INDEX idx_etf_daily_share_tot_vol ON etf_daily_share(tot_vol DESC);

-- ETF 持有人信息表
CREATE TABLE etf_top_holders (
    id SERIAL PRIMARY KEY,
    sec_code VARCHAR(20) NOT NULL,
    holder_name VARCHAR(200),
    hold_volume REAL,
    hold_ratio REAL,
    stat_date DATE,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 5.2 数据迁移

现有 SQLite 数据迁移到 PostgreSQL：
- 使用 Python 脚本批量导入
- 迁移过程中保持服务可用（双写或停机迁移）

---

## 6. 部署方案

### 6.1 服务器环境

| 项目 | 配置 |
|------|------|
| 系统 | Ubuntu Linux 5.15.0 |
| 内存 | 7.8GB |
| 磁盘 | 88GB |
| 用户 | root（后期创建 deploy 用户） |

### 6.2 部署步骤

```bash
# 1. 系统更新
apt update && apt upgrade -y

# 2. 安装基础软件
apt install -y python3.13 python3.13-venv nginx postgresql certbot python3-certbot-nginx

# 3. 创建项目用户
useradd -m -s /bin/bash deploy
mkdir -p /opt/etf-dashboard
chown deploy:deploy /opt/etf-dashboard

# 4. 数据库初始化
sudo -u postgres psql
CREATE DATABASE etf_db;
CREATE USER etf_user WITH PASSWORD 'etf_password';
GRANT ALL PRIVILEGES ON DATABASE etf_db TO etf_user;

# 5. 部署后端
sudo -u deploy bash -c "cd /opt/etf-dashboard && python3.13 -m venv venv"
# ... 后续步骤见部署文档
```

### 6.3 Nginx 配置

```nginx
server {
    listen 80;
    server_name bedivere.space;

    location / {
        root /opt/etf-dashboard/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## 7. 苹果风格设计指南

### 7.1 配色方案

| 用途 | 色值 |
|------|------|
| 主色 | `#007AFF` (iOS Blue) |
| 背景 | `#F5F5F7` (Light Gray) |
| 卡片背景 | `#FFFFFF` |
| 文字主色 | `#1D1D1F` |
| 文字副色 | `#86868B` |
| 成功 | `#34C759` |
| 警告 | `#FF9500` |
| 危险 | `#FF3B30` |

### 7.2 设计特点

- 大量留白，圆角卡片 (`border-radius: 12px`)
- 轻微阴影：`box-shadow: 0 2px 10px rgba(0,0,0,0.1)`
- 渐变背景可选：顶部 `#F5F5F7` 到底部 `#FFFFFF`
- 简洁的图标，使用 Lucide Icons
- 动效轻柔：过渡 0.2s ease

---

## 8. 待确认事项

- [ ] 域名 DNS 是否已解析到 45.145.228.58
- [ ] 是否需要用户登录认证功能
- [ ] 数据更新频率（实时/每日）
- [ ] 是否需要导出功能（Excel/CSV）

---

## 9. 开发计划

### Phase 1: 基础架构
- [ ] 服务器环境初始化
- [ ] PostgreSQL 安装配置
- [ ] Nginx 安装配置
- [ ] SSL 证书申请

### Phase 2: 后端开发
- [ ] Flask 项目结构搭建
- [ ] 数据库模型创建
- [ ] 数据迁移（SQLite → PostgreSQL）
- [ ] API 接口开发
- [ ] 数据采集脚本适配

### Phase 3: 前端开发
- [ ] React + Vite 项目初始化
- [ ] shadcn/ui 配置
- [ ] 页面组件开发
- [ ] API 联调

### Phase 4: 部署上线
- [ ] 前端构建部署
- [ ] 后端 systemd 服务配置
- [ ] HTTPS 配置
- [ ] 域名解析确认

---

## 10. 文档目录

```
docs/
├── ARCHITECTURE.md        # 本文档
├── DEPLOY.md              # 部署详细文档
├── API.md                 # API 接口文档
├── DATASHEET.md           # 数据字典
└── TODO.md                # 开发任务清单
```
