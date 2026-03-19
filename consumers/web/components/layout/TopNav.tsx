"use client";

import Link from "next/link";
import { useState } from "react";
import dynamic from "next/dynamic";
import { useLocale, useAuthContext } from "@/lib/providers";
import { Menu, X, ChevronDown } from "lucide-react";

const ConnectButton = dynamic(
  () => import("@rainbow-me/rainbowkit").then((mod) => mod.ConnectButton),
  { ssr: false, loading: () => <div className="h-8 w-24 animate-pulse rounded-md bg-zinc-800" /> }
);

const dataLinks = [
  { href: "/data/nba", labelKey: "nav.nba" },
  { href: "/data/weather", labelKey: "nav.weather" },
  { href: "/data/btc", labelKey: "nav.btc" },
];

const navLinks = [
  { href: "/markets", labelKey: "nav.markets" },
  { href: "/portfolio", labelKey: "nav.portfolio" },
  { href: "/orders", labelKey: "nav.orders" },
  { href: "/analysis", labelKey: "nav.analysis" },
  { href: "/strategies", labelKey: "nav.strategies" },
  { href: "/settings", labelKey: "nav.settings" },
];

export default function TopNav() {
  const { t, locale, setLocale } = useLocale();
  const { user, logout } = useAuthContext();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [dataOpen, setDataOpen] = useState(false);

  return (
    <nav className="border-b border-zinc-800 bg-zinc-950 px-4 py-3">
      <div className="mx-auto flex max-w-7xl items-center justify-between">
        {/* Logo */}
        <Link href="/markets" className="text-lg font-bold text-white">
          Polymarket Broker
        </Link>

        {/* Desktop Nav */}
        <div className="hidden items-center gap-1 md:flex">
          {navLinks.slice(0, 3).map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="rounded-md px-3 py-2 text-sm text-zinc-300 hover:bg-zinc-800 hover:text-white"
            >
              {t(link.labelKey)}
            </Link>
          ))}

          {/* Data Dropdown */}
          <div className="relative">
            <button
              onClick={() => setDataOpen(!dataOpen)}
              className="flex items-center gap-1 rounded-md px-3 py-2 text-sm text-zinc-300 hover:bg-zinc-800 hover:text-white"
            >
              {t("nav.data")}
              <ChevronDown className="h-3 w-3" />
            </button>
            {dataOpen && (
              <div className="absolute left-0 top-full z-50 mt-1 w-40 rounded-md border border-zinc-700 bg-zinc-900 py-1 shadow-lg">
                {dataLinks.map((link) => (
                  <Link
                    key={link.href}
                    href={link.href}
                    className="block px-4 py-2 text-sm text-zinc-300 hover:bg-zinc-800 hover:text-white"
                    onClick={() => setDataOpen(false)}
                  >
                    {t(link.labelKey)}
                  </Link>
                ))}
              </div>
            )}
          </div>

          {navLinks.slice(3).map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="rounded-md px-3 py-2 text-sm text-zinc-300 hover:bg-zinc-800 hover:text-white"
            >
              {t(link.labelKey)}
            </Link>
          ))}
        </div>

        {/* Right side */}
        <div className="flex items-center gap-3">
          {/* Language switcher */}
          <button
            onClick={() => setLocale(locale === "en" ? "zh" : "en")}
            className="rounded-md px-2 py-1 text-xs text-zinc-400 hover:bg-zinc-800 hover:text-white"
          >
            {locale === "en" ? "中文" : "EN"}
          </button>

          {/* Wallet */}
          <ConnectButton
            accountStatus="address"
            chainStatus="icon"
            showBalance={false}
          />

          {/* User menu */}
          {user && (
            <button
              onClick={logout}
              className="rounded-md px-2 py-1 text-xs text-zinc-400 hover:bg-zinc-800 hover:text-white"
            >
              {t("auth.logout")}
            </button>
          )}

          {/* Mobile menu toggle */}
          <button
            onClick={() => setMobileOpen(!mobileOpen)}
            className="md:hidden"
          >
            {mobileOpen ? (
              <X className="h-5 w-5 text-zinc-300" />
            ) : (
              <Menu className="h-5 w-5 text-zinc-300" />
            )}
          </button>
        </div>
      </div>

      {/* Mobile Nav */}
      {mobileOpen && (
        <div className="mt-2 space-y-1 border-t border-zinc-800 pt-2 md:hidden">
          {navLinks.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="block rounded-md px-3 py-2 text-sm text-zinc-300 hover:bg-zinc-800"
              onClick={() => setMobileOpen(false)}
            >
              {t(link.labelKey)}
            </Link>
          ))}
          {dataLinks.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="block rounded-md px-3 py-2 pl-6 text-sm text-zinc-400 hover:bg-zinc-800"
              onClick={() => setMobileOpen(false)}
            >
              {t(link.labelKey)}
            </Link>
          ))}
        </div>
      )}
    </nav>
  );
}
