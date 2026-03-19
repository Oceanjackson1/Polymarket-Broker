import MarketsClient from "./markets-client";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000/api/v1";

async function fetchMarkets() {
  try {
    const res = await fetch(`${API_BASE}/markets?limit=30`, {
      next: { revalidate: 60 },
    });
    if (!res.ok) return [];
    const data = await res.json();
    return data.data || data || [];
  } catch {
    return [];
  }
}

export default async function MarketsPage() {
  const initialMarkets = await fetchMarkets();

  return <MarketsClient initialMarkets={initialMarkets} />;
}
