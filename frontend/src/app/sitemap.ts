import type { MetadataRoute } from "next";

const baseUrl =
  process.env.NEXT_PUBLIC_SITE_URL || "https://broker.polymarket.com";

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  // Static marketing & content pages
  const staticPages: MetadataRoute.Sitemap = [
    { url: baseUrl, lastModified: new Date(), changeFrequency: "daily", priority: 1.0 },
    { url: `${baseUrl}/markets`, lastModified: new Date(), changeFrequency: "hourly", priority: 0.9 },
    { url: `${baseUrl}/pricing`, lastModified: new Date(), changeFrequency: "monthly", priority: 0.7 },
    { url: `${baseUrl}/about`, lastModified: new Date(), changeFrequency: "monthly", priority: 0.5 },
    { url: `${baseUrl}/blog`, lastModified: new Date(), changeFrequency: "daily", priority: 0.8 },
    { url: `${baseUrl}/docs`, lastModified: new Date(), changeFrequency: "weekly", priority: 0.8 },
  ];

  // TODO: Dynamic market pages from API
  // const markets = await fetch(`${apiUrl}/api/v1/markets?limit=1000`).then(r => r.json());
  // const marketPages = markets.data.map(m => ({
  //   url: `${baseUrl}/markets/${m.slug}`,
  //   lastModified: new Date(m.data_updated_at),
  //   changeFrequency: 'hourly' as const,
  //   priority: 0.8,
  // }));

  // TODO: Dynamic blog posts from MDX content
  // TODO: Dynamic odds pages
  // TODO: Dynamic glossary pages

  return [...staticPages];
}
