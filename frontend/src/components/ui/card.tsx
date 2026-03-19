import type { HTMLAttributes } from "react";
import { clsx } from "clsx";

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  /** Elevate the card one level (bg-bg-elevated instead of bg-bg-card) */
  elevated?: boolean;
  /** Remove default padding */
  noPadding?: boolean;
}

export function Card({
  elevated = false,
  noPadding = false,
  className,
  children,
  ...props
}: CardProps) {
  return (
    <div
      className={clsx(
        "rounded-lg border border-border-subtle",
        elevated ? "bg-bg-elevated" : "bg-bg-card",
        !noPadding && "p-5",
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}

interface CardHeaderProps extends HTMLAttributes<HTMLDivElement> {}

export function CardHeader({ className, children, ...props }: CardHeaderProps) {
  return (
    <div
      className={clsx(
        "mb-4 flex items-center justify-between",
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}

interface CardTitleProps extends HTMLAttributes<HTMLHeadingElement> {}

export function CardTitle({ className, children, ...props }: CardTitleProps) {
  return (
    <h3
      className={clsx("text-sm font-semibold text-text-primary", className)}
      {...props}
    >
      {children}
    </h3>
  );
}
