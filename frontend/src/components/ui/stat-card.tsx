import { clsx } from "clsx";
import type { HTMLAttributes } from "react";

interface StatCardProps extends HTMLAttributes<HTMLDivElement> {
  label: string;
  value: string | number;
  /** e.g. "+2.8%" or "-1.2%". Positive values render green, negative red. */
  change?: string | null;
  /** Override the automatic profit/loss coloring on change */
  changeVariant?: "profit" | "loss" | "neutral";
}

function resolveChangeVariant(
  change: string,
  override?: StatCardProps["changeVariant"]
): "profit" | "loss" | "neutral" {
  if (override) return override;
  if (change.startsWith("+")) return "profit";
  if (change.startsWith("-")) return "loss";
  return "neutral";
}

const changeColors = {
  profit: "text-profit",
  loss: "text-loss",
  neutral: "text-text-muted",
};

export function StatCard({
  label,
  value,
  change,
  changeVariant,
  className,
  ...props
}: StatCardProps) {
  const variant =
    change != null ? resolveChangeVariant(change, changeVariant) : "neutral";

  return (
    <div
      className={clsx(
        "rounded-lg border border-border-subtle bg-bg-card p-5",
        className
      )}
      {...props}
    >
      <p className="text-xs text-text-muted">{label}</p>
      <p className="mt-1 font-mono text-2xl font-semibold text-text-primary">
        {value}
      </p>
      {change != null && (
        <p className={clsx("mt-1 font-mono text-sm", changeColors[variant])}>
          {change}
        </p>
      )}
    </div>
  );
}
