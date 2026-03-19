import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
  display: "swap",
});

const jetbrainsMono = JetBrains_Mono({
  variable: "--font-jetbrains-mono",
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  title: {
    default: "Polymarket Broker — Institutional Prediction Market Terminal",
    template: "%s | Polymarket Broker",
  },
  description:
    "机构级预测市场交易平台。提供 NBA×Polymarket 实时融合数据、145 项体育历史订单簿、BTC 多时间框架预测和 AI 定价偏差分析。",
  metadataBase: new URL(
    process.env.NEXT_PUBLIC_SITE_URL || "https://broker.polymarket.com"
  ),
  openGraph: {
    type: "website",
    locale: "en_US",
    siteName: "Polymarket Broker",
  },
  twitter: {
    card: "summary_large_image",
  },
  robots: {
    index: true,
    follow: true,
  },
};

const jsonLd = {
  "@context": "https://schema.org",
  "@type": "Organization",
  name: "Polymarket Broker",
  description:
    "Institutional-grade prediction market trading platform with real-time NBA fusion data, 145-sport historical orderbooks, BTC multi-timeframe predictions, and AI pricing-bias analysis.",
  url: process.env.NEXT_PUBLIC_SITE_URL || "https://broker.polymarket.com",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${inter.variable} ${jetbrainsMono.variable} h-full antialiased`}
    >
      <head>
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
        />
      </head>
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
