import type { HTMLAttributes } from "react";
import { clsx } from "clsx";

type BadgeVariant =
  | "pro"
  | "profit"
  | "loss"
  | "neutral"
  | "info"
  | "warning"
  | "default";

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: BadgeVariant;
}

const variantClasses: Record<BadgeVariant, string> = {
  pro: "bg-accent-gold-bg text-accent-gold",
  profit: "bg-profit-bg text-profit",
  loss: "bg-loss-bg text-loss",
  neutral: "bg-bg-elevated text-text-muted",
  info: "bg-bg-elevated text-info-cyan",
  warning: "bg-bg-elevated text-warning",
  default: "bg-bg-elevated text-text-secondary",
};

export function Badge({
  variant = "default",
  className,
  children,
  ...props
}: BadgeProps) {
  return (
    <span
      className={clsx(
        "inline-flex items-center rounded px-1.5 py-0.5 font-mono text-[10px] font-medium",
        variantClasses[variant],
        className
      )}
      {...props}
    >
      {children}
    </span>
  );
}

/** Convenience shorthand — always renders with the "pro" variant */
export function ProBadge({ className, ...props }: HTMLAttributes<HTMLSpanElement>) {
  return (
    <Badge variant="pro" className={className} {...props}>
      PRO
    </Badge>
  );
}
