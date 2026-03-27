export interface TgAuthResult {
  access_token: string;
  user_id: string;
  tg_user_id: number;
}

export async function authenticateViaTelegram(apiBase: string): Promise<TgAuthResult | null> {
  const tg = (window as any).Telegram?.WebApp;
  if (!tg?.initData) return null;

  const res = await fetch(`${apiBase}/api/v1/agent/tg-auth`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ init_data: tg.initData }),
  });

  if (!res.ok) return null;
  return res.json();
}

export function expandTgWebApp() {
  const tg = (window as any).Telegram?.WebApp;
  if (tg) {
    tg.expand();
    tg.ready();
  }
}
