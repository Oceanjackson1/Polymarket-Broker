# Polymarket Broker API

基于 FastAPI 构建的 Polymarket 预测市场经纪人后端服务，提供完整的身份认证、订单管理、市场数据和实时数据采集功能。

## 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                      FastAPI 应用                        │
│                                                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────────┐  │
│  │ 认证模块  │ │ 市场模块  │ │ 订单模块  │ │ 投资组合  │  │
│  └──────────┘ └──────────┘ └──────────┘ └───────────┘  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                │
│  │体育数据API│ │ NBA数据API│ │ BTC数据API│                │
│  └──────────┘ └──────────┘ └──────────┘                │
├─────────────────────────────────────────────────────────┤
│                    数据采集管道                           │
│  ┌──────────────┐ ┌────────────┐ ┌────────────────┐    │
│  │SportsCollector│ │NbaCollector│ │ BtcCollector   │    │
│  │ (每5分钟)     │ │ (每30秒)   │ │ (每30秒)       │    │
│  └──────────────┘ └────────────┘ └────────────────┘    │
├─────────────────────────────────────────────────────────┤
│  PostgreSQL (asyncpg)  │  Redis (限流/缓存)              │
└─────────────────────────────────────────────────────────┘
         ↕                    ↕                  ↕
   Polymarket CLOB     Polymarket Gamma     ESPN / CoinGecko
```

## 核心功能

### 身份认证与安全
- JWT 访问令牌 + 刷新令牌机制
- API Key 认证，支持细粒度作用域（`data:read`、`orders:write`）
- 以太坊钱包签名认证（EIP-191）
- Fernet AES-256 加密存储敏感信息
- Redis 滑动窗口限流中间件

### 市场数据
- 市场列表、搜索、详情查询
- 实时订单簿代理
- 最近交易记录
- 中间价计算

### 订单管理
- **托管模式**：服务端使用运营商私钥进行 EIP-712 签名下单
- **非托管模式**：客户端构建订单 → 本地签名 → 提交执行
- 订单列表、取消、批量取消
- 手续费引擎（阶梯费率）
- 风控模块（单笔限额 + 持仓上限）

### 投资组合
- 持仓查询
- 余额计算（可用 / 锁定）
- 逐笔盈亏分析

### 数据采集管道
- **体育数据采集器**：每 5 分钟从 Polymarket Gamma 拉取体育赛事市场，PostgreSQL upsert
- **NBA 数据采集器**：每 30 秒融合 ESPN 实时比分 + Polymarket 赔率，计算偏差信号（bias signal）
- **BTC 数据采集器**：每 30 秒从 CoinGecko 获取价格 + Polymarket 预测市场概率，追加写入

### 数据 API（12 个端点）

| 路由 | 端点数 | 说明 |
|------|--------|------|
| `/api/v1/data/sports/` | 4 | 体育分类、赛事列表、订单簿代理、已结算查询 |
| `/api/v1/data/nba/` | 4 | 比赛列表、详情、ESPN+Polymarket 融合视图、订单簿 |
| `/api/v1/data/btc/` | 4 | 全时间框架预测、单时间框架详情、链上交易代理、历史查询 |

所有数据端点包含 **陈旧检测**（staleness envelope）：返回 `stale` 标记和 `data_updated_at` 时间戳。

## 技术栈

| 组件 | 技术 |
|------|------|
| Web 框架 | FastAPI 0.115 |
| ORM | SQLAlchemy 2.0（异步） |
| 数据库 | PostgreSQL 16 + asyncpg |
| 缓存/限流 | Redis 7 + hiredis |
| HTTP 客户端 | httpx 0.27 |
| 认证 | JWT (python-jose) + Fernet (cryptography) |
| 区块链 | eth-account（EIP-712 / EIP-191） |
| 数据验证 | Pydantic 2.8 |
| 测试 | pytest + pytest-asyncio |

## 快速开始

### 前置条件

- Python 3.11+
- PostgreSQL 16
- Redis 7
- Docker & Docker Compose（可选）

### 方式一：Docker Compose（推荐）

```bash
# 克隆项目
git clone https://github.com/Oceanjackson1/Polymarket-Broker.git
cd Polymarket-Broker

# 复制并编辑环境变量
cp .env.example .env
# 编辑 .env，填入你的 Polymarket 私钥和 API Key

# 启动所有服务
docker compose up -d

# API 运行在 http://localhost:8000
```

### 方式二：本地开发

```bash
# 克隆项目
git clone https://github.com/Oceanjackson1/Polymarket-Broker.git
cd Polymarket-Broker

# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 启动 PostgreSQL 和 Redis（使用 Docker）
docker compose up postgres redis -d

# 复制并编辑环境变量
cp .env.example .env

# 启动开发服务器
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### 环境变量

```bash
# 数据库
DATABASE_URL=postgresql+asyncpg://broker:broker@localhost:5432/broker
REDIS_URL=redis://localhost:6379/0

# 安全（必须修改）
SECRET_KEY=your-secret-key-at-least-32-chars
FERNET_KEY=用 python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())" 生成

# Polymarket
POLYMARKET_PRIVATE_KEY=0x...    # 运营商私钥（用于托管模式签名）
POLYMARKET_API_KEY=             # CLOB API Key
POLYMARKET_FEE_ADDRESS=0x...    # 手续费接收地址

# 数据管道
ESPN_API_BASE=https://site.api.espn.com
COINGECKO_API_BASE=https://api.coingecko.com
DISABLE_COLLECTORS=false        # 设为 true 可禁用后台采集任务
```

## 运行测试

```bash
# 创建测试数据库
createdb broker_test

# 运行全部测试（106 个）
ENV_FILE=.env.test pytest tests/ -v

# 查看覆盖率
ENV_FILE=.env.test pytest tests/ --cov=. --cov-report=term-missing
```

## API 端点概览

### 认证 `/api/v1/auth/`

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/register` | 注册用户 |
| POST | `/login` | 登录获取 JWT |
| POST | `/refresh` | 刷新访问令牌 |
| POST | `/api-keys` | 创建 API Key |
| GET | `/api-keys` | 列出 API Key |
| DELETE | `/api-keys/{id}` | 删除 API Key |
| POST | `/wallet/challenge` | 获取钱包签名挑战 |
| POST | `/wallet/verify` | 验证钱包签名 |

### 市场 `/api/v1/markets/`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/` | 市场列表 |
| GET | `/search` | 搜索市场 |
| GET | `/{id}` | 市场详情 |
| GET | `/{id}/orderbook` | 订单簿 |
| GET | `/{id}/trades` | 交易记录 |
| GET | `/{id}/midpoint` | 中间价 |

### 订单 `/api/v1/orders/`

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/` | 托管模式下单 |
| POST | `/build` | 非托管：构建订单 |
| POST | `/submit` | 非托管：提交签名订单 |
| GET | `/` | 订单列表 |
| DELETE | `/{id}` | 取消订单 |
| DELETE | `/cancel-all` | 取消全部 |

### 投资组合 `/api/v1/portfolio/`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/positions` | 持仓列表 |
| GET | `/balance` | 账户余额 |
| GET | `/pnl` | 盈亏分析 |

### 数据 — 体育 `/api/v1/data/sports/`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/categories` | 体育分类 |
| GET | `/{sport}/events` | 赛事列表（游标分页） |
| GET | `/{sport}/events/{id}/orderbook` | 赛事订单簿 |
| GET | `/{sport}/events/{id}/realized` | 已结算赛事 |

### 数据 — NBA `/api/v1/data/nba/`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/games` | 今日比赛 |
| GET | `/games/{id}` | 比赛详情 |
| GET | `/games/{id}/fusion` | ESPN+Polymarket 融合视图 |
| GET | `/games/{id}/orderbook` | 比赛订单簿 |

### 数据 — BTC `/api/v1/data/btc/`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/predictions` | 全时间框架最新预测 |
| GET | `/predictions/{tf}` | 单时间框架历史 |
| GET | `/onchain` | 链上交易代理 |
| GET | `/history` | 历史快照查询 |

## 项目结构

```
Polymarket-Broker/
├── api/                      # API 层
│   ├── auth/                 # 认证模块（JWT、API Key、钱包）
│   ├── data/                 # 数据查询端点
│   │   ├── sports/           # 体育数据 API
│   │   ├── nba/              # NBA 数据 API
│   │   └── btc/              # BTC 数据 API
│   ├── markets/              # 市场查询端点
│   ├── orders/               # 订单管理端点
│   ├── portfolio/            # 投资组合端点
│   ├── middleware/           # 错误处理、限流中间件
│   ├── deps.py               # 公共依赖（认证、作用域校验）
│   └── main.py               # FastAPI 应用入口 + 生命周期管理
├── core/                     # 核心业务逻辑
│   ├── polymarket/           # Polymarket 客户端（CLOB + Gamma）
│   ├── config.py             # 配置管理（Pydantic Settings）
│   ├── fee_engine.py         # 手续费引擎
│   ├── risk_guard.py         # 风控模块
│   └── security.py           # JWT / Fernet / HMAC 工具
├── data_pipeline/            # 后台数据采集
│   ├── base.py               # BaseCollector 基类（轮询循环）
│   ├── sports_collector.py   # 体育市场采集器
│   ├── nba_collector.py      # NBA 比分+赔率融合采集器
│   └── btc_collector.py      # BTC 价格+预测采集器
├── db/                       # 数据库连接工厂
│   ├── postgres.py           # SQLAlchemy 异步引擎
│   └── redis_client.py       # Redis 连接池
├── tests/                    # 测试套件（106 个测试）
├── docker-compose.yml        # Docker 编排
├── Dockerfile                # 容器构建
├── requirements.txt          # Python 依赖
└── .env.example              # 环境变量模板
```

## 许可证

MIT License
