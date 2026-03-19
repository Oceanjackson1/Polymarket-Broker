import { docs } from '../../.source/server';
import { loader } from 'fumadocs-core/source';
import { i18n } from '@/lib/i18n';

export const source = loader({
  baseUrl: '/docs',
  source: docs.toFumadocsSource(),
  i18n: {
    ...i18n,
    // Put locale AFTER baseUrl: /docs/en/... instead of default /en/docs/...
    hideLocale: 'never',
  },
  url: (slugs: string[], locale?: string) =>
    `/docs/${locale ?? 'en'}${slugs.length > 0 ? '/' + slugs.join('/') : ''}`,
});
