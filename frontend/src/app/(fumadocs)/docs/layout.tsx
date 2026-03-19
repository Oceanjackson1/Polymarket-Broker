import { DocsLayout } from 'fumadocs-ui/layouts/docs';
import type { ReactNode } from 'react';
import { source } from '@/lib/source';
import Link from 'next/link';

export default function Layout({ children }: { children: ReactNode }) {
  return (
    <DocsLayout
      tree={source.pageTree}
      nav={{
        title: (
          <Link href="/" className="flex items-center gap-2">
            <span className="text-lg font-bold text-amber-400">PM</span>
            <span className="text-base font-semibold">Broker Docs</span>
          </Link>
        ),
      }}
    >
      {children}
    </DocsLayout>
  );
}
