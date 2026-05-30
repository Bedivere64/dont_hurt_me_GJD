# ETF Dashboard 部署文档

## 1. 项目结构

```
etf-dashboard/
├── backend/                      # Flask 后端
│   ├── app/
│   │   ├── __init__.py         # Flask 应用工厂
│   │   ├── models.py           # 数据模型
│   │   ├── routes/             # API 路由
│   │   │   ├── __init__.py
│   │   │   ├── auth.py         # 认证相关 API
│   │   │   ├── etf.py         # ETF 相关 API
│   │   │   └── health.py      # 健康检查
│   │   ├── services/           # 业务逻辑
│   │   └── utils/              # 工具函数
│   ├── migrations/             # 数据库迁移
│   ├── scripts/
│   │   ├── init_db.py         # 数据库初始化
│   │   ├── migrate_data.py     # 数据迁移脚本
│   │   └── fetch_data.sh      # 定时任务脚本
│   ├── tests/                  # 测试目录
│   ├── wsgi.py                # WSGI 入口
│   ├── run.py                 # 开发入口
│   └── requirements.txt        # Python 依赖
│
├── frontend/                    # React 前端
│   ├── src/
│   │   ├── pages/             # 页面组件
│   │   │   ├── Dashboard/     # 首页
│   │   │   ├── Ranking/       # 排行榜
│   │   │   ├── Trend/         # 趋势图
│   │   │   ├── Compare/       # 对比分析
│   │   │   └── Login/         # 登录页
│   │   ├── components/        # 公共组件
│   │   │   ├── ui/            # UI 组件
│   │   │   ├── charts/         # 图表组件
│   │   │   └── layout/        # 布局组件
│   │   ├── hooks/              # React Hooks
│   │   ├── services/           # API 调用
│   │   ├── stores/             # 状态管理
│   │   ├── App.tsx            # 应用入口
│   │   └── main.tsx           # React 入口
│   ├── public/                # 静态资源
│   ├── package.json
│   ├── vite.config.ts
│   └── tsconfig.json
│
├── docs/                       # 文档
│   └── DEPLOY.md              # 本文档
│
├── .github/
│   └── workflows/
│       └── deploy.yml          # CI/CD 部署流程
│
├── ARCHITECTURE.md             # 架构设计文档
└── README.md                   # 项目说明
```

---

## 2. 本地开发

### 2.1 环境要求

| 组件 | 版本 | 说明 |
|------|------|------|
| Node.js | ≥20.x | 前端构建 |
| Python | 3.13.x | 后端运行 |
| PostgreSQL | ≥14 | 本地数据库（可选） |

### 2.2 后端开发

```bash
# 进入后端目录
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 运行开发服务器
python run.py
```

### 2.3 前端开发

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 开发模式
npm run dev

# 构建生产版本
npm run build
```

---

## 3. CI/CD 自动化部署

### 3.1 GitHub Actions 工作流程

代码推送到 `main` 分支后自动触发部署：

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: self-hosted
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.13'
          
      - name: Install backend dependencies
        run: |
          cd backend
          python -m venv venv
          source venv/bin/activate
          pip install -r requirements.txt
          
      - name: Install frontend dependencies
        run: |
          cd frontend
          npm install
          npm run build
          
      - name: Restart backend service
        run: |
          ssh root@${{ secrets.SERVER_HOST }} "
            pkill -f gunicorn
            cd /opt/etf-dashboard/backend
            source venv/bin/activate
            nohup gunicorn -w 2 -b 127.0.0.1:8000 'wsgi:app' > /tmp/gunicorn.log 2>&1 &
          "
```

### 3.2 服务器配置 GitHub Runner

```bash
# 在服务器上安装 GitHub Runner
cd /opt
mkdir -p actions-runner && cd actions-runner
curl -o actions-runner.tar.gz -L https://github.com/actions/runner/releases/download/v2.322.0/actions-runner-linux-x64-2.322.0.tar.gz
tar xzf actions-runner.tar.gz

# 配置 Runner（需要 GitHub 仓库的 Token）
./config.sh --url https://github.com/YOUR_USERNAME/etf-dashboard --token YOUR_TOKEN

# 安装为服务
./svc.sh install
./svc.sh start
```

### 3.3 配置 GitHub Secrets

在 GitHub 仓库 Settings → Secrets 中配置：

| Secret | 说明 |
|--------|------|
| `SERVER_HOST` | 服务器 IP |
| `SERVER_SSH_KEY` | SSH 私钥（用于连接服务器） |

---

## 4. 服务器部署

### 4.1 目录结构

```
/opt/etf-dashboard/
├── backend/              # Flask 后端代码
├── frontend/             # React 前端代码
├── frontend/dist/        # 前端构建产物
└── scripts/             # 工具脚本
```

### 4.2 服务管理

```bash
# 查看后端服务状态
ps aux | grep gunicorn

# 重启后端服务
pkill -f gunicorn
cd /opt/etf-dashboard/backend
source venv/bin/activate
nohup gunicorn -w 2 -b 127.0.0.1:8000 'wsgi:app' > /tmp/gunicorn.log 2>&1 &

# 查看日志
tail -f /tmp/gunicorn.log
```

### 4.3 Nginx 配置

```bash
# Nginx 配置文件
/etc/nginx/sites-available/etf-dashboard

# 重载 Nginx
nginx -t && systemctl reload nginx
```

### 4.4 数据库

```bash
# 连接数据库
sudo -u postgres psql -d etf_db

# 常用命令
\l                          # 列出数据库
\dt                         # 列出表
SELECT COUNT(*) FROM etf_daily_share;  # 查看数据量
```

---

## 5. 定时任务

```bash
# 查看定时任务
crontab -l

# 编辑定时任务
crontab -e
```

默认配置：每天 06:00 执行数据采集

---

## 6. 维护命令

```bash
# 更新代码（手动）
cd /opt/etf-dashboard
git pull

# 重启服务
systemctl restart nginx
pkill -f gunicorn && cd /opt/etf-dashboard/backend && source venv/bin/activate && nohup gunicorn -w 2 -b 127.0.0.1:8000 'wsgi:app' > /tmp/gunicorn.log 2>&1 &

# 查看服务状态
systemctl status nginx
ps aux | grep gunicorn
curl -s https://bedivere.space/api/health
```

---

## 7. 故障排查

| 问题 | 解决方法 |
|------|----------|
| 前端 500 错误 | 检查 `/opt/etf-dashboard/frontend/dist` 是否存在 |
| API 404 | 检查 Nginx 代理配置和 Gunicorn 是否运行 |
| 数据库连接失败 | 检查 PostgreSQL 服务和密码配置 |
| SSL 证书过期 | 运行 `certbot renew` |

---

## 8. 开发规范

### 8.1 Git 工作流

```
main          # 生产代码
├── develop   # 开发分支（可选）
└── feature/* # 功能分支
```

### 8.2 提交规范

```
feat: 新功能
fix: 修复bug
docs: 文档更新
style: 代码格式
refactor: 重构
test: 测试
chore: 构建/工具
```

### 8.3 分支保护

- `main` 分支不能直接推送，需要 PR
- 至少 1 个 review 通过才能合并
- CI/CD 必须通过才能合并
