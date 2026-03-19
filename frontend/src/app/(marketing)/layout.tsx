import Link from "next/link";

const navLinks = [
  { href: "/markets", label: "Markets" },
  { href: "/docs", label: "Docs" },
  { href: "/blog", label: "Blog" },
  { href: "/pricing", label: "Pricing" },
];

export default function MarketingLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <>
      {/* Navigation */}
      <header className="sticky top-0 z-50 border-b border-white/[0.06] bg-black/80 backdrop-blur-xl">
        <nav className="mx-auto flex h-14 max-w-6xl items-center justify-between px-6">
          <Link href="/" className="flex items-center gap-2.5">
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-white text-[11px] font-bold text-black">
              PM
            </div>
            <span className="text-[15px] font-semibold text-white">Broker</span>
          </Link>

          <div className="hidden items-center gap-8 md:flex">
            {navLinks.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className="text-[13px] text-white/40 transition-colors hover:text-white"
              >
                {link.label}
              </Link>
            ))}
          </div>

          <div className="flex items-center gap-3">
            <Link
              href="/login"
              className="text-[13px] text-white/40 transition-colors hover:text-white"
            >
              Sign in
            </Link>
            <Link
              href="/register"
              className="rounded-full bg-white px-5 py-2 text-[13px] font-medium text-black transition-all hover:bg-white/90"
            >
              Get started
            </Link>
          </div>
        </nav>
      </header>

      <main className="flex-1">{children}</main>

      {/* Footer */}
      <footer className="border-t border-white/[0.06] bg-black">
        <div className="mx-auto max-w-6xl px-6 py-16">
          <div className="grid grid-cols-2 gap-8 md:grid-cols-4">
            <div>
              <h3 className="mb-5 text-xs font-medium uppercase tracking-widest text-white/30">
                Product
              </h3>
              <ul className="space-y-3">
                {["Markets", "Dashboard", "Pricing"].map((t) => (
                  <li key={t}>
                    <Link href={`/${t.toLowerCase()}`} className="text-sm text-white/40 transition-colors hover:text-white">
                      {t}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <h3 className="mb-5 text-xs font-medium uppercase tracking-widest text-white/30">
                Exclusive Data
              </h3>
              <ul className="space-y-3">
                {[
                  { label: "NBA Fusion", href: "/docs/guides/nba-fusion-trading" },
                  { label: "BTC Predictions", href: "/docs/guides/btc-multiframe" },
                  { label: "Sports Orderbooks", href: "/docs/guides/sports-orderbooks" },
                ].map((item) => (
                  <li key={item.label}>
                    <Link href={item.href} className="text-sm text-white/40 transition-colors hover:text-white">
                      {item.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <h3 className="mb-5 text-xs font-medium uppercase tracking-widest text-white/30">
                Developers
              </h3>
              <ul className="space-y-3">
                {[
                  { label: "Documentation", href: "/docs" },
                  { label: "Quick Start", href: "/docs/getting-started/quickstart" },
                  { label: "Changelog", href: "/docs/changelog" },
                ].map((item) => (
                  <li key={item.label}>
                    <Link href={item.href} className="text-sm text-white/40 transition-colors hover:text-white">
                      {item.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <h3 className="mb-5 text-xs font-medium uppercase tracking-widest text-white/30">
                Resources
              </h3>
              <ul className="space-y-3">
                {[
                  { label: "Blog", href: "/blog" },
                  { label: "About", href: "/about" },
                  { label: "Glossary", href: "/glossary" },
                ].map((item) => (
                  <li key={item.label}>
                    <Link href={item.href} className="text-sm text-white/40 transition-colors hover:text-white">
                      {item.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          <div className="mt-16 flex items-center justify-between border-t border-white/[0.06] pt-8">
            <p className="text-xs text-white/20">
              &copy; {new Date().getFullYear()} Polymarket Broker
            </p>
            <div className="flex items-center gap-6">
              <Link href="/feed.xml" className="text-xs text-white/20 hover:text-white/40">RSS</Link>
              <Link href="/llms.txt" className="text-xs text-white/20 hover:text-white/40">llms.txt</Link>
            </div>
          </div>
        </div>
      </footer>
    </>
  );
}
