"use client";

import { useRef, type ReactNode } from "react";
import clsx from "clsx";

interface HoverCardProps {
  children: ReactNode;
  className?: string;
  glowColor?: string;
}

export function HoverCard({ children, className, glowColor }: HoverCardProps) {
  const ref = useRef<HTMLDivElement>(null);

  const handleMouseMove = (e: React.MouseEvent) => {
    const el = ref.current;
    if (!el) return;
    const rect = el.getBoundingClientRect();
    el.style.setProperty("--mouse-x", `${e.clientX - rect.left}px`);
    el.style.setProperty("--mouse-y", `${e.clientY - rect.top}px`);
  };

  return (
    <div
      ref={ref}
      onMouseMove={handleMouseMove}
      className={clsx("hover-glow rounded-lg border border-border-subtle bg-bg-card transition-all duration-200", className)}
      style={glowColor ? { "--glow-color": glowColor } as React.CSSProperties : undefined}
    >
      {children}
    </div>
  );
}
