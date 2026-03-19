import type { Metadata } from "next";
import { Inter, JetBrains_Mono, Space_Grotesk } from "next/font/google";
import "./globals.css";
import "fumadocs-ui/style.css";
import { RootProvider } from "fumadocs-ui/provider/next";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
  display: "swap",
});

const spaceGrotesk = Space_Grotesk({
  variable: "--font-space-grotesk",
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
    default: "Polydesk — Institutional Prediction Market Terminal",
    template: "%s | Polydesk",
  },
  description:
    "机构级预测市场交易平台。提供 NBA×Polymarket 实时融合数据、145 项体育历史订单簿、BTC 多时间框架预测和 AI 定价偏差分析。",
  metadataBase: new URL(
    process.env.NEXT_PUBLIC_SITE_URL || "https://broker.polymarket.com"
  ),
  openGraph: {
    type: "website",
    locale: "en_US",
    siteName: "Polydesk",
  },
  twitter: {
    card: "summary_large_image",
  },
  robots: {
    index: true,
    follow: true,
  },
  icons: {
    icon: "/icon.svg",
    apple: "/apple-icon.svg",
  },
};

const jsonLd = {
  "@context": "https://schema.org",
  "@type": "Organization",
  name: "Polydesk",
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
      suppressHydrationWarning
      className={`${inter.variable} ${jetbrainsMono.variable} ${spaceGrotesk.variable} h-full antialiased`}
    >
      <head>
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
        />
      </head>
      <body className="min-h-full flex flex-col">
        <RootProvider theme={{ defaultTheme: 'dark' }}>{children}</RootProvider>
      </body>
    </html>
  );
}
