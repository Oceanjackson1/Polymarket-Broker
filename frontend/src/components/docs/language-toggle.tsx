"use client";

import { usePathname, useRouter } from "next/navigation";

export function LanguageToggle() {
  const pathname = usePathname();
  const router = useRouter();

  // Detect if current page is Chinese (.cn suffix in path)
  const isChinese = pathname.endsWith(".cn") || pathname.includes(".cn/");

  const toggle = () => {
    if (isChinese) {
      // Switch to English: remove .cn
      router.push(pathname.replace(/\.cn(\/|$)/, "$1"));
    } else {
      // Switch to Chinese: add .cn before trailing slash or at end
      // /docs/getting-started/quickstart → /docs/getting-started/quickstart.cn
      const cnPath = pathname.replace(/\/?$/, "") + ".cn";
      router.push(cnPath);
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
