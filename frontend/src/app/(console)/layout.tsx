"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { QueryProvider } from "@/components/providers/query-provider";

const tabs = [
  { href: "/console", label: "API Keys" },
  { href: "/console/usage", label: "Usage" },
  { href: "/console/settings", label: "Settings" },
];

export default function ConsoleLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const router = useRouter();

  function handleLogout() {
    document.cookie =
      "pm_api_key=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT";
    router.push("/login");
  }

  return (
    <div className="min-h-screen bg-black">
      <header className="sticky top-0 z-50 border-b border-white/15 bg-black/80 backdrop-blur-xl">
        <nav className="mx-auto flex h-14 max-w-5xl items-center justify-between px-6">
          <Link href="/" className="flex items-center gap-2.5">
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none" className="text-white">
              <rect x="2" y="2" width="16" height="16" rx="4" stroke="currentColor" strokeWidth="1.5" />
              <path d="M7 13V7h3.5a2.5 2.5 0 0 1 0 5H7Z" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round" />
            </svg>
            <span className="font-[family-name:var(--font-space-grotesk)] text-[20px] font-semibold tracking-tight text-white">
              Polydesk
            </span>
          </Link>

          <div className="flex items-center gap-1">
            {tabs.map((tab) => {
              const isActive =
                tab.href === "/console"
                  ? pathname === "/console"
                  : pathname.startsWith(tab.href);
              return (
                <Link
                  key={tab.href}
                  href={tab.href}
                  className={`rounded-full px-5 py-2 text-[13px] transition-colors ${
                    isActive
                      ? "bg-white/10 text-white font-medium"
                      : "text-white/40 hover:text-white hover:bg-white/[0.05]"
                  }`}
                >
                  {tab.label}
                </Link>
              );
            })}
          </div>

          <div className="flex items-center gap-5">
            <Link href="/docs" className="text-[13px] text-white/40 transition-colors hover:text-white">
              Docs
            </Link>
            <button
              onClick={handleLogout}
              className="rounded-full border border-white/20 px-4 py-1.5 text-[13px] text-white/60 transition-colors hover:border-white/40 hover:text-white"
            >
              Log out
            </button>
          </div>
        </nav>
      </header>

      <main className="mx-auto max-w-5xl px-6 py-12">
        <QueryProvider>{children}</QueryProvider>
      </main>
    </div>
  );
}
