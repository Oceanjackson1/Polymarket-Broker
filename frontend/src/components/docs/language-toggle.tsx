"use client";

import { usePathname, useRouter } from "next/navigation";

export function LanguageToggle() {
  const pathname = usePathname();
  const router = useRouter();

  const isChinese = pathname.endsWith(".cn");

  const toggle = () => {
    if (isChinese) {
      // /docs/api-reference/orders.cn → /docs/api-reference/orders
      // /docs/index.cn → /docs
      const enPath = pathname.replace(/\.cn$/, "");
      router.push(enPath.endsWith("/index") ? enPath.replace(/\/index$/, "") : enPath);
    } else {
      // /docs → /docs/index.cn
      // /docs/api-reference/orders → /docs/api-reference/orders.cn
      if (pathname === "/docs" || pathname === "/docs/") {
        router.push("/docs/index.cn");
      } else {
        router.push(pathname.replace(/\/$/, "") + ".cn");
      }
    }
  };

  return (
    <button
      onClick={toggle}
      className="flex items-center gap-1.5 rounded-md border border-fd-border px-2.5 py-1.5 text-xs font-medium text-fd-muted-foreground transition-colors hover:bg-fd-accent hover:text-fd-foreground"
      title={isChinese ? "Switch to English" : "切换到中文"}
    >
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="10" />
        <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
        <path d="M2 12h20" />
      </svg>
      {isChinese ? "EN" : "中文"}
    </button>
  );
}
