"use client";

import { useLocale } from "@/lib/providers";
import { AlertTriangle } from "lucide-react";

export default function StaleWarning({ stale }: { stale?: boolean }) {
  const { t } = useLocale();
  if (!stale) return null;

  return (
    <div className="flex items-center gap-2 rounded-md bg-yellow-900/30 px-3 py-2 text-xs text-yellow-400">
      <AlertTriangle className="h-3 w-3" />
      {t("data.staleWarning")}
    </div>
  );
}
