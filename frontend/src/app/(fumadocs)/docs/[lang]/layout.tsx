import { DocsLayout } from 'fumadocs-ui/layouts/docs';
import type { ReactNode } from 'react';
import { source } from '@/lib/source';
import Link from 'next/link';
import { LanguageToggle } from '@/components/docs/language-toggle';
import '../styles.css';

export default async function Layout({
  children,
  params,
}: {
  children: ReactNode;
  params: Promise<{ lang: string }>;
}) {
  const { lang } = await params;
  const tree = source.pageTree[lang] ?? source.pageTree['en'];

  return (
    <DocsLayout
      tree={tree}
      nav={{
        title: (
          <Link href="/" className="flex items-center gap-2.5">
            <svg width="18" height="18" viewBox="0 0 20 20" fill="none" className="text-fd-foreground">
              <rect x="2" y="2" width="16" height="16" rx="4" stroke="currentColor" strokeWidth="1.5" />
              <path d="M7 13V7h3.5a2.5 2.5 0 0 1 0 5H7Z" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round" />
            </svg>
            <span className="font-[family-name:var(--font-space-grotesk)] text-[18px] font-semibold tracking-tight text-fd-foreground">
              Polydesk
            </span>
          </Link>
        ),
        children: <LanguageToggle />,
      }}
    >
      {children}
    </DocsLayout>
  );
}
