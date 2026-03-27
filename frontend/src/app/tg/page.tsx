"use client";

import { useEffect, useState } from "react";
import { authenticateViaTelegram, expandTgWebApp } from "@/lib/tg-auth";

export default function TgEntryPage() {
  const [status, setStatus] = useState<"loading" | "authenticated" | "error">("loading");
  const [error, setError] = useState("");

  useEffect(() => {
    expandTgWebApp();

    authenticateViaTelegram(process.env.NEXT_PUBLIC_API_URL || "")
      .then((result) => {
        if (result) {
          sessionStorage.setItem("access_token", result.access_token);
          setStatus("authenticated");
        } else {
          setError("Please use /bind in the bot to link your account first.");
          setStatus("error");
        }
      })
      .catch(() => {
        setError("Authentication failed.");
        setStatus("error");
      });
  }, []);

  if (status === "loading") {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p>Connecting...</p>
      </div>
    );
  }

  if (status === "error") {
    return (
      <div className="flex items-center justify-center min-h-screen p-4">
        <p className="text-red-500">{error}</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="p-4">
        <h1 className="text-xl font-bold mb-4">Polymarket Broker</h1>
        <nav className="grid grid-cols-2 gap-2">
          <a href="/tg/markets" className="p-4 rounded-lg bg-card border text-center">
            Markets
          </a>
          <a href="/tg/portfolio" className="p-4 rounded-lg bg-card border text-center">
            Portfolio
          </a>
        </nav>
      </div>
    </div>
  );
}
