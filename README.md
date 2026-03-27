# Polymarket Broker — Polydesk

全栈预测市场经纪人平台：FastAPI 后端 + Next.js 交易终端，提供实时数据采集、AI 定价偏差分析、跨平台套利策略和完整的交易功能。

> **在线体验**：[polydesk.eu.cc](https://polydesk.eu.cc) · **API 文档**：[polydesk.eu.cc/docs](https://polydesk.eu.cc/docs)

## 系统架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Next.js 交易终端 (Vercel)                           │
│  Dashboard │ Markets │ Trade │ Portfolio │ Orders │ Settings                │
│  NBA Fusion │ BTC Predictions │ Weather Fusion │ AI Analysis │ Strategies  │
├──────────────────────────────── REST + WebSocket ────────────────────────────┤
│                           FastAPI 后端 (8001)                                │
│                                                                             │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌──────────┐      │
│  │ 认证   │ │ 市场   │ │ 订单   │ │ 组合   │ │ 分析   │ │ 策略     │ 路由  │
│  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘ └──────────┘      │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌──────────┐      │
│  │ 体育   │ │ NBA    │ │ BTC    │ │ 天气   │ │ Dome   │ │ 实时OB   │ 数据  │
│  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘ └──────────┘      │
├─────────────────────────────────────────────────────────────────────────────┤
│                          数据采集管道 (Background Tasks)                      │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐ │
│  │Sports    │ │NBA       │ │BTC       │ │Weather   │ │Dome: Market/     │ │
│  │ 5min     │ │ 30s      │ │ 30s      │ │ 5min     │ │Kalshi/Wallet     │ │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────────────┘ │
├─────────────────────────────────────────────────────────────────────────────┤
│  PostgreSQL (asyncpg)  │  Redis (限流/缓存)  │  WebSocket (4 实时通道)       │
└─────────────────────────────────────────────────────────────────────────────┘
    ↕              ↕              ↕              ↕              ↕
 Polymarket     ESPN /        Open-Meteo      Dome API       腾讯云服务器
 CLOB+Gamma    CoinGecko    (Ensemble API)  (8-Key Pool)   (Binance+Poly OB)
```

## 核心功能

### Web 交易终端（Next.js）

| 页面 | 功能 |
|------|------|
| Dashboard | 总资产、盈亏、持仓概览 + AI 发现（实时 scan） |
| Markets | 100+ 市场浏览、搜索、分类筛选、分页 |
| Trade | 订单簿（WebSocket 实时）+ 下单面板（实时费率） + 最近成交 |
| Portfolio | 5 维统计（余额/可用/锁定/已实现PnL/总PnL）+ 持仓明细 |
| Orders | 订单历史、状态追踪、一键取消 |
| NBA Live | 实时比分 × Polymarket 赔率 × ESPN 统计偏差信号 |
| BTC | 4 时间框架概率预测 + 价格图表 + WebSocket 实时 |
| Weather | 日期→城市→温度区间，预报概率 vs 市场价格偏差 |
| AI Analysis | 全市场 scan + 单市场深度分析 + LLM 问答 |
| Strategies | 收敛套利机会列表（含费率净 edge）+ 一键执行 |
| Fees | 11 类别费率参数表 + 交互式费率计算器 |
| Sports | 多运动分类 + 赛事列表 + 历史订单簿 |
| Settings | 账户信息、API Key 管理（CRUD）、主题 |

**技术栈**：Next.js 16 (App Router) + Tailwind CSS 4 + React Query + Lightweight Charts + fumadocs 中英文档

### 身份认证与安全
- JWT 访问令牌 + 刷新令牌机制
- API Key 认证，支持细粒度作用域（`data:read`、`orders:write`）
- 以太坊钱包签名认证（EIP-191）
- Fernet AES-256 加密存储敏感信息
- Redis 滑动窗口限流中间件

### 市场数据
- 市场列表、搜索、详情查询
- 实时订单簿代理
- 最近交易记录、中间价计算

### 订单管理
- **托管模式**：服务端使用运营商私钥进行 EIP-712 签名下单
- **非托管模式**：客户端构建订单 → 本地签名 → 提交执行
- 订单列表、取消、批量取消
- 手续费引擎（阶梯费率）+ 风控模块（单笔限额 + 持仓上限）

### 数据采集管道

| 采集器 | 间隔 | 数据源 | 说明 |
|--------|------|--------|------|
| SportsCollector | 5min | Gamma + Dome (Kalshi) | 体育赛事市场 + 跨平台匹配 |
| NbaCollector | 30s | ESPN + Dome/Gamma | 实时比分 + 赔率 + 偏差信号 |
| BtcCollector | 30s | Dome/Binance → CoinGecko | BTC 价格 + 预测概率 |
| WeatherCollector | 5min | Polymarket Gamma + Open-Meteo Ensemble | 天气市场动态发现 + 51 成员集合概率预报 |
| DomeMarketCollector | 60s | Dome API | 增强市场快照（价格+K线+深度） |
| KalshiCollector | 120s | Dome API | Polymarket↔Kalshi 跨平台价差 |
| WalletTracker | 300s | Dome API | 聪明钱持仓 + PnL 监控 |

### AI 分析 & 策略
- **市场 Scan**：全市场扫描定价偏差机会
- **单市场分析**：深度分析指定市场的定价合理性
- **LLM 问答**：自然语言查询市场信息
- **收敛套利**：自动检测 Polymarket 价格 vs 统计/预报概率的偏差，一键执行交易

### Dome API 集成（8-Key 高并发）
- **8 个 API Key 轮转池**，每秒 600+ 请求吞吐
- 自动 429 限流检测 + 10 秒冷却跳过
- WebSocket 实时订单流（自动重连 + 订阅恢复）

### 实时订单簿（腾讯云服务器）
- **Binance BTCUSDT**：现货 + 期货深度数据，100万+ 条记录（TimescaleDB）
- **Polymarket BTC Up/Down**：5分钟窗口的订单簿快照、价格变动、成交记录
- 通过 HTTP API + SSH 代理暴露给 Broker

### WebSocket 实时通道

| 端点 | 说明 |
|------|------|
| `/ws/markets/{token_id}` | 订单簿实时推送 |
| `/ws/nba/{game_id}/live` | NBA 比分实时更新 |
| `/ws/btc/live` | BTC 预测概率实时推送 |
| `/ws/portfolio/live` | 持仓变化实时通知 |

## 技术栈

| 组件 | 技术 |
|------|------|
| **前端** | Next.js 16, React 19, Tailwind CSS 4, React Query, Lightweight Charts |
| **后端** | FastAPI 0.115, SQLAlchemy 2.0 (async), Pydantic 2.8 |
| **数据库** | PostgreSQL 16 + asyncpg |
| **缓存** | Redis 7 + hiredis |
| **认证** | JWT (python-jose) + Fernet (cryptography) + eth-account |
| **文档** | fumadocs (MDX, 中英双语) |
| **测试** | pytest + pytest-asyncio（242 个测试） |
| **部署** | Vercel (前端) + Docker Compose (后端) |

## 快速开始

### 前置条件

- Python 3.11+
- Node.js 20+
- PostgreSQL 16
- Redis 7

### 后端

```bash
git clone https://github.com/Oceanjackson1/Polymarket-Broker.git
cd Polymarket-Broker

# 虚拟环境
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 环境变量
cp .env.example .env
# 编辑 .env，填入 Polymarket 私钥和 API Key

# 启动
uvicorn api.main:app --reload --host 0.0.0.0 --port 8001
```

### 前端

```bash
cd frontend
npm install
npm run dev
# 打开 http://localhost:3000
```

前端通过 Next.js rewrite 代理 `/api/*` 到后端 `localhost:8001`。

### Docker Compose（后端 + 数据库）

```bash
cp .env.example .env
docker compose up -d
```

### 环境变量

```bash
# 数据库
DATABASE_URL=postgresql+asyncpg://broker:broker@localhost:5432/broker
REDIS_URL=redis://localhost:6379/0

# 安全（必须修改）
SECRET_KEY=your-secret-key-at-least-32-chars
FERNET_KEY=  # python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Polymarket
POLYMARKET_PRIVATE_KEY=0x...
POLYMARKET_API_KEY=
POLYMARKET_FEE_ADDRESS=0x...

# 数据管道
ESPN_API_BASE=https://site.api.espn.com
COINGECKO_API_BASE=https://api.coingecko.com
DISABLE_COLLECTORS=false
```

## 运行测试

```bash
# 后端测试（242 个）
ENV_FILE=.env.test pytest tests/ -v

# 覆盖率
ENV_FILE=.env.test pytest tests/ --cov=. --cov-report=term-missing
```

## API 端点概览（46 REST + 4 WebSocket）

### 认证 `/api/v1/auth/`

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/register` | 注册用户 |
| POST | `/login` | 登录获取 JWT |
| POST | `/refresh` | 刷新访问令牌 |
| GET | `/me` | 当前用户信息 |
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
| GET | `/{sport}/events` | 赛事列表 |
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

### 数据 — 天气 `/api/v1/data/weather/`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/dates` | 有活跃市场的日期列表 |
| GET | `/dates/{date}/cities` | 该日期所有城市概览（按 bias 排序） |
| GET | `/dates/{date}/cities/{city}/fusion` | 预报概率 vs 市场价格 × bias 分析 |
| GET | `/dates/{date}/cities/{city}/orderbook` | 温度区间订单簿 |

### 数据 — Dome 增强 `/api/v1/data/dome/`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/markets` | 最新市场快照 |
| GET | `/markets/{slug}/candlesticks` | K线历史（OHLC） |
| GET | `/arbitrage/spreads` | 跨平台价差 |
| GET | `/arbitrage/opportunities` | 高价差套利机会 |
| GET | `/wallets/{addr}/positions` | 钱包持仓历史 |
| GET | `/wallets/{addr}/pnl` | 钱包盈亏曲线 |
| GET | `/crypto/{symbol}/price` | 实时加密货币价格 |

### 分析 `/api/v1/analysis/`

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/scan` | 全市场定价偏差扫描 |
| GET | `/market/{id}` | 单市场深度分析 |
| GET | `/nba/{game_id}` | NBA 赛事 AI 分析 |
| POST | `/ask` | LLM 自然语言问答 |

### 策略 `/api/v1/strategies/`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/convergence/opportunities` | 收敛套利机会（含费率扣除后净 edge） |
| POST | `/convergence/execute` | 执行套利交易 |
| GET | `/convergence/positions` | 活跃策略持仓 |

### 费率 `/api/v1/fees/`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/schedule` | 全类别费率参数表（11 类 × feeRate/exponent/makerRebate） |
| GET | `/estimate` | 实时费率估算（类别+价格+金额 → broker+平台费用明细） |
| GET | `/market/{token_id}` | 指定市场自动检测类别 + midpoint 费率计算 |

## 项目结构

```
Polymarket-Broker/
├── api/                          # FastAPI 后端
│   ├── auth/                     # 认证（JWT、API Key、钱包）
│   ├── markets/                  # 市场查询
│   ├── orders/                   # 订单管理
│   ├── portfolio/                # 投资组合
│   ├── analysis/                 # AI 分析（含费率扣除后净 bias）
│   ├── strategies/               # 交易策略（含费率扣除后净 edge）
│   ├── fees/                     # 实时费率查询（11 类别 × 动态价格）
│   ├── data/                     # 数据端点
│   │   ├── sports/               # 体育数据
│   │   ├── nba/                  # NBA 数据
│   │   ├── btc/                  # BTC 数据
│   │   ├── weather/              # 天气数据
│   │   ├── dome/                 # Dome 增强数据
│   │   └── live_orderbook/       # 实时订单簿
│   ├── ws/                       # WebSocket 端点
│   ├── webhooks/                 # Webhook 通知
│   ├── developer/                # 开发者工具
│   └── middleware/               # 错误处理、限流
├── core/                         # 核心业务逻辑
│   ├── polymarket/               # Polymarket 客户端
│   ├── dome/                     # Dome API（8-Key Pool）
│   ├── live_orderbook/           # 远程订单簿客户端
│   ├── config.py                 # 配置管理
│   ├── fee_engine.py             # 手续费引擎
│   ├── risk_guard.py             # 风控模块
│   └── security.py               # JWT / Fernet / HMAC
├── data_pipeline/                # 后台数据采集（7 个 Collector）
├── db/                           # 数据库连接（PostgreSQL + Redis）
├── frontend/                     # Next.js 交易终端
│   ├── src/app/(dashboard)/      # 12 个交易页面
│   ├── src/app/(marketing)/      # 营销页面（首页、定价、登录）
│   ├── src/app/(fumadocs)/       # 中英文 API 文档
│   ├── src/lib/                  # API Client + Hooks + Stores
│   ├── src/components/           # UI 组件库
│   └── content/docs/             # MDX 文档内容（17 页 × 2 语言）
├── tests/                        # 242 个测试
├── docker-compose.yml
└── requirements.txt
```

## 许可证

MIT License
