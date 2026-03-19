export default function DashboardPage() {
  return (
    <div className="p-6">
      {/* Top Stats Row */}
      <div className="mb-8 grid grid-cols-4 gap-4">
        {[
          { label: "总资产", value: "$45,230", change: null },
          { label: "今日盈亏", value: "+$1,240", change: "+2.8%" },
          { label: "活跃仓位", value: "12", change: null },
          { label: "API 调用", value: "347 / 500", change: null },
        ].map((stat) => (
          <div
            key={stat.label}
            className="rounded-lg border border-border-subtle bg-bg-card p-5"
          >
            <p className="text-xs text-text-muted">{stat.label}</p>
            <p className="mt-1 font-mono text-2xl font-semibold text-text-primary">
              {stat.value}
            </p>
            {stat.change && (
              <p className="mt-1 text-sm text-profit">{stat.change}</p>
            )}
          </div>
        ))}
      </div>

      <div className="grid grid-cols-3 gap-6">
        {/* AI Discoveries */}
        <div className="col-span-3 rounded-lg border border-accent-gold/20 bg-bg-card p-6">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="flex items-center gap-2 text-sm font-semibold text-text-primary">
              <span className="text-accent-gold">◆</span> AI 发现
              <span className="rounded bg-accent-gold-bg px-1.5 py-0.5 text-[10px] text-accent-gold">
                独家
              </span>
            </h2>
            <span className="text-xs text-text-muted">
              3 个定价偏差机会
            </span>
          </div>
          <div className="space-y-3">
            {[
              {
                market: "GSW vs LAL",
                signal: "HOME_UNDERPRICED",
                bps: "+420bps",
                type: "NBA",
              },
              {
                market: "BTC 5m prediction",
                signal: "低估",
                bps: "概率 0.61 vs 模型 0.74",
                type: "BTC",
              },
              {
                market: "UFC Fight Night",
                signal: "偏差 >500bps",
                bps: "赔率与赛前分析偏离",
                type: "Sports",
              },
            ].map((item) => (
              <div
                key={item.market}
                className="flex items-center justify-between rounded border border-border-subtle bg-bg-base p-3"
              >
                <div className="flex items-center gap-3">
                  <span className="rounded bg-bg-elevated px-2 py-0.5 font-mono text-[10px] text-text-muted">
                    {item.type}
                  </span>
                  <span className="text-sm text-text-primary">
                    {item.market}
                  </span>
                </div>
                <div className="flex items-center gap-4">
                  <span className="font-mono text-sm text-accent-gold">
                    {item.signal}
                  </span>
                  <span className="text-xs text-text-muted">{item.bps}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* NBA Live */}
        <div className="col-span-1 rounded-lg border border-border-subtle bg-bg-card p-6">
          <h2 className="mb-4 flex items-center gap-2 text-sm font-semibold text-text-primary">
            🏀 NBA 实况
            <span className="rounded bg-accent-gold-bg px-1.5 py-0.5 text-[10px] text-accent-gold">
              PRO
            </span>
          </h2>
          <div className="space-y-4">
            {[
              {
                teams: "GSW 94 - 87 LAL",
                status: "Q3 4:22",
                bias: "HOME_UNDER +420bps",
              },
              {
                teams: "BOS 102 - 98 MIA",
                status: "Q4 1:55",
                bias: "NEUTRAL",
              },
            ].map((game) => (
              <div
                key={game.teams}
                className="rounded border border-border-subtle bg-bg-base p-3"
              >
                <div className="flex items-center justify-between">
                  <span className="font-mono text-sm text-text-primary">
                    {game.teams}
                  </span>
                  <span className="text-xs text-info-cyan">{game.status}</span>
                </div>
                <p className="mt-1 text-xs text-text-muted">
                  bias: {game.bias}
                </p>
              </div>
            ))}
          </div>
        </div>

        {/* BTC Predictions */}
        <div className="col-span-1 rounded-lg border border-border-subtle bg-bg-card p-6">
          <h2 className="mb-4 flex items-center gap-2 text-sm font-semibold text-text-primary">
            ₿ BTC 预测
            <span className="rounded bg-accent-gold-bg px-1.5 py-0.5 text-[10px] text-accent-gold">
              PRO
            </span>
          </h2>
          <p className="mb-4 font-mono text-xl text-text-primary">$68,420</p>
          <div className="space-y-2">
            {[
              { tf: "5m", prob: "0.61", dir: "▲" },
              { tf: "15m", prob: "0.48", dir: "▼" },
              { tf: "1h", prob: "0.55", dir: "▲" },
              { tf: "4h", prob: "0.62", dir: "▲" },
            ].map((row) => (
              <div
                key={row.tf}
                className="flex items-center justify-between rounded border border-border-subtle bg-bg-base p-2"
              >
                <span className="font-mono text-xs text-text-muted">
                  {row.tf}
                </span>
                <span
                  className={`font-mono text-sm ${row.dir === "▲" ? "text-profit" : "text-loss"}`}
                >
                  {row.dir} {row.prob}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Active Positions */}
        <div className="col-span-1 rounded-lg border border-border-subtle bg-bg-card p-6">
          <h2 className="mb-4 text-sm font-semibold text-text-primary">
            活跃仓位
          </h2>
          <div className="space-y-2">
            {[
              { market: "Trump 2028", pnl: "+$15", side: "BUY" },
              { market: "BTC >70k 1h", pnl: "+$12", side: "BUY" },
              { market: "GSW vs LAL", pnl: "+$2", side: "BUY" },
            ].map((pos) => (
              <div
                key={pos.market}
                className="flex items-center justify-between rounded border border-border-subtle bg-bg-base p-2"
              >
                <div className="flex items-center gap-2">
                  <span className="rounded bg-profit-bg px-1.5 py-0.5 font-mono text-[10px] text-profit">
                    {pos.side}
                  </span>
                  <span className="text-sm text-text-primary">
                    {pos.market}
                  </span>
                </div>
                <span className="font-mono text-sm text-profit">
                  {pos.pnl}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
