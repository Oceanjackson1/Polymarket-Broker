import Link from "next/link";

const navLinks = [
  { href: "/markets", label: "Markets" },
  { href: "/docs", label: "API Docs" },
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
      {/* Public Navigation — SEO-friendly, server-rendered */}
      <header className="sticky top-0 z-50 border-b border-border-subtle bg-bg-base/95 backdrop-blur">
        <nav className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6">
          <Link href="/" className="flex items-center gap-2">
            <span className="text-xl font-bold text-accent-gold">PM</span>
            <span className="text-lg font-semibold text-text-primary">
              Broker
            </span>
          </Link>

          <div className="hidden items-center gap-8 md:flex">
            {navLinks.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className="text-sm text-text-secondary transition-colors hover:text-text-primary"
              >
                {link.label}
              </Link>
            ))}
          </div>

          <div className="flex items-center gap-4">
            <Link
              href="/dashboard"
              className="text-sm text-text-secondary transition-colors hover:text-text-primary"
            >
              Login
            </Link>
            <Link
              href="/dashboard"
              className="rounded-lg bg-accent-gold px-4 py-2 text-sm font-medium text-bg-base transition-colors hover:bg-accent-gold-hover"
            >
              Get Started
            </Link>
          </div>
        </nav>
      </header>

      {/* Page Content */}
      <main className="flex-1">{children}</main>

      {/* Footer — SEO link matrix */}
      <footer className="border-t border-border-subtle bg-bg-card">
        <div className="mx-auto max-w-7xl px-6 py-16">
          <div className="grid grid-cols-2 gap-8 md:grid-cols-4">
            <div>
              <h3 className="mb-4 text-sm font-semibold text-text-primary">
                Product
              </h3>
              <ul className="space-y-3">
                <li>
                  <Link href="/markets" className="text-sm text-text-secondary hover:text-text-primary">
                    Markets
                  </Link>
                </li>
                <li>
                  <Link href="/pricing" className="text-sm text-text-secondary hover:text-text-primary">
                    Pricing
                  </Link>
                </li>
                <li>
                  <Link href="/dashboard" className="text-sm text-text-secondary hover:text-text-primary">
                    Dashboard
                  </Link>
                </li>
              </ul>
            </div>

            <div>
              <h3 className="mb-4 text-sm font-semibold text-text-primary">
                Exclusive Data
              </h3>
              <ul className="space-y-3">
                <li>
                  <Link href="/docs/guides/nba-fusion-trading" className="text-sm text-text-secondary hover:text-text-primary">
                    NBA Fusion Data
                  </Link>
                </li>
                <li>
                  <Link href="/docs/guides/btc-multiframe" className="text-sm text-text-secondary hover:text-text-primary">
                    BTC Predictions
                  </Link>
                </li>
                <li>
                  <Link href="/docs/guides/sports-orderbooks" className="text-sm text-text-secondary hover:text-text-primary">
                    Sports Orderbooks
                  </Link>
                </li>
              </ul>
            </div>

            <div>
              <h3 className="mb-4 text-sm font-semibold text-text-primary">
                Developers
              </h3>
              <ul className="space-y-3">
                <li>
                  <Link href="/docs" className="text-sm text-text-secondary hover:text-text-primary">
                    API Documentation
                  </Link>
                </li>
                <li>
                  <Link href="/docs/getting-started/quickstart" className="text-sm text-text-secondary hover:text-text-primary">
                    Quick Start
                  </Link>
                </li>
                <li>
                  <Link href="/docs/changelog" className="text-sm text-text-secondary hover:text-text-primary">
                    Changelog
                  </Link>
                </li>
              </ul>
            </div>

            <div>
              <h3 className="mb-4 text-sm font-semibold text-text-primary">
                Resources
              </h3>
              <ul className="space-y-3">
                <li>
                  <Link href="/blog" className="text-sm text-text-secondary hover:text-text-primary">
                    Blog
                  </Link>
                </li>
                <li>
                  <Link href="/about" className="text-sm text-text-secondary hover:text-text-primary">
                    About
                  </Link>
                </li>
                <li>
                  <Link href="/glossary" className="text-sm text-text-secondary hover:text-text-primary">
                    Glossary
                  </Link>
                </li>
              </ul>
            </div>
          </div>

          <div className="mt-12 flex items-center justify-between border-t border-border-subtle pt-8">
            <p className="text-sm text-text-muted">
              &copy; {new Date().getFullYear()} Polymarket Broker. All rights reserved.
            </p>
            <div className="flex items-center gap-6">
              <Link href="/feed.xml" className="text-sm text-text-muted hover:text-text-secondary">
                RSS
              </Link>
              <Link href="/llms.txt" className="text-sm text-text-muted hover:text-text-secondary">
                llms.txt
              </Link>
            </div>
          </div>
        </div>
      </footer>
    </>
  );
}
