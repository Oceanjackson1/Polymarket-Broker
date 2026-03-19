"use client";

import type { ButtonHTMLAttributes } from "react";
import { clsx } from "clsx";

type ButtonVariant = "primary" | "secondary" | "danger" | "ghost";
type ButtonSize = "sm" | "md" | "lg";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  /** Show a loading spinner and disable interactions */
  loading?: boolean;
  /** Stretch to fill the parent container */
  fullWidth?: boolean;
}

const variantClasses: Record<ButtonVariant, string> = {
  primary:
    "bg-accent-gold text-bg-base font-semibold hover:bg-accent-gold-hover active:scale-[0.98]",
  secondary:
    "border border-border-default bg-transparent text-text-primary hover:bg-bg-elevated active:scale-[0.98]",
  danger:
    "bg-loss-bg text-loss border border-loss/30 hover:bg-loss hover:text-bg-base active:scale-[0.98]",
  ghost:
    "bg-transparent text-text-secondary hover:text-text-primary hover:bg-bg-elevated active:scale-[0.98]",
};

const sizeClasses: Record<ButtonSize, string> = {
  sm: "h-7 px-3 text-xs",
  md: "h-9 px-4 text-sm",
  lg: "h-11 px-6 text-base",
};

export function Button({
  variant = "primary",
  size = "md",
  loading = false,
  fullWidth = false,
  disabled,
  className,
  children,
  ...props
}: ButtonProps) {
  const isDisabled = disabled || loading;

  return (
    <button
      disabled={isDisabled}
      className={clsx(
        "inline-flex items-center justify-center gap-2 rounded-md font-medium transition-all duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-gold focus-visible:ring-offset-2 focus-visible:ring-offset-bg-base",
        variantClasses[variant],
        sizeClasses[size],
        fullWidth && "w-full",
        isDisabled && "cursor-not-allowed opacity-50",
        className
      )}
      {...props}
    >
      {loading && (
        <span
          className="inline-block h-3.5 w-3.5 animate-spin rounded-full border-2 border-current border-t-transparent"
          aria-hidden="true"
        />
      )}
      {children}
    </button>
  );
}
