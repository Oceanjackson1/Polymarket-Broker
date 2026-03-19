import type { Metadata } from "next";
import Link from "next/link";
import { QueryProvider } from "@/components/providers/query-provider";

export const metadata: Metadata = {
  robots: { index: false, follow: false },
};

const mainNav = [
  { href: "/dashboard", label: "Dashboard", icon: "◫" },
  { href: "/trade", label: "Trade", icon: "⇅" },
];

const dataNav = [
  { href: "/nba", label: "NBA Live", icon: "🏀", pro: true },
  { href: "/btc", label: "BTC", icon: "₿", pro: true },
  { href: "/sports", label: "Sports", icon: "⚡", pro: true },
  { href: "/strategies", label: "Strategies", icon: "◆", pro: true },
];

const utilNav = [
  { href: "/orders", label: "Orders", icon: "☰" },
  { href: "/settings", label: "Settings", icon: "⚙" },
];

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="terminal flex h-screen overflow-hidden">
      {/* Sidebar */}
      <aside className="flex w-56 flex-col border-r border-border-subtle bg-bg-base">
        {/* Logo */}
        <div className="flex h-14 items-center border-b border-border-subtle px-4">
          <Link href="/dashboard" className="flex items-center gap-2">
            <svg width="18" height="18" viewBox="0 0 20 20" fill="none" className="text-white">
              <rect x="2" y="2" width="16" height="16" rx="4" stroke="currentColor" strokeWidth="1.5" />
              <path d="M7 13V7h3.5a2.5 2.5 0 0 1 0 5H7Z" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round" />
            </svg>
            <span className="text-[18px] font-semibold tracking-tight text-white">Polydesk</span>
          </Link>
        </div>

        {/* Navigation */}
        <nav className="flex-1 overflow-y-auto px-2 py-4">
          {/* Main */}
          <div className="mb-6">
            <p className="mb-2 px-3 text-[10px] font-semibold uppercase tracking-wider text-text-muted">
              Terminal
            </p>
            {mainNav.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className="flex items-center gap-3 rounded-md px-3 py-2 text-sm text-text-secondary transition-colors hover:bg-bg-elevated hover:text-text-primary"
              >
                <span className="w-4 text-center text-xs">{item.icon}</span>
                {item.label}
              </Link>
            ))}
          </div>

          {/* Data — Exclusive */}
          <div className="mb-6">
            <p className="mb-2 px-3 text-[10px] font-semibold uppercase tracking-wider text-text-muted">
              Exclusive Data
            </p>
            {dataNav.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className="flex items-center gap-3 rounded-md px-3 py-2 text-sm text-text-secondary transition-colors hover:bg-bg-elevated hover:text-text-primary"
              >
                <span className="w-4 text-center text-xs">{item.icon}</span>
                {item.label}
                {item.pro && (
                  <span className="ml-auto rounded bg-accent-gold-bg px-1.5 py-0.5 text-[10px] font-medium text-accent-gold">
                    PRO
                  </span>
                )}
              </Link>
            ))}
          </div>

          {/* Utility */}
          <div>
            <p className="mb-2 px-3 text-[10px] font-semibold uppercase tracking-wider text-text-muted">
              Account
            </p>
            {utilNav.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className="flex items-center gap-3 rounded-md px-3 py-2 text-sm text-text-secondary transition-colors hover:bg-bg-elevated hover:text-text-primary"
              >
                <span className="w-4 text-center text-xs">{item.icon}</span>
                {item.label}
              </Link>
            ))}
          </div>
        </nav>

        {/* Bottom — Docs & Blog links */}
        <div className="border-t border-border-subtle p-3">
          <div className="flex gap-4">
            <Link
              href="/docs"
              className="text-xs text-text-muted transition-colors hover:text-text-secondary"
            >
              API Docs
            </Link>
            <Link
              href="/blog"
              className="text-xs text-text-muted transition-colors hover:text-text-secondary"
            >
              Blog
            </Link>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto bg-bg-base">
        <QueryProvider>{children}</QueryProvider>
      </main>
    </div>
  );
}
