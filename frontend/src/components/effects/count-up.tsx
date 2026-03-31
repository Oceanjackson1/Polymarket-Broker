"use client";

import { useEffect, useRef, useState } from "react";
import { useInView } from "motion/react";

interface CountUpProps {
  target: number;
  suffix?: string;
  prefix?: string;
  duration?: number;
  className?: string;
}

export function CountUp({
  target,
  suffix = "",
  prefix = "",
  duration = 1.5,
  className = "",
}: CountUpProps) {
  const ref = useRef<HTMLSpanElement>(null);
  const isInView = useInView(ref, { once: true });
  const [count, setCount] = useState(0);

  useEffect(() => {
    if (!isInView) return;

    const start = 0;
    const end = target;
    const totalFrames = Math.round(duration * 60);
    let frame = 0;

    const counter = setInterval(() => {
      frame++;
      const progress = frame / totalFrames;
      // Ease out cubic
      const eased = 1 - Math.pow(1 - progress, 3);
      setCount(Math.round(start + (end - start) * eased));

      if (frame >= totalFrames) {
        setCount(end);
        clearInterval(counter);
      }
    }, 1000 / 60);

    return () => clearInterval(counter);
  }, [isInView, target, duration]);

  return (
    <span ref={ref} className={className}>
      {prefix}{count}{suffix}
    </span>
  );
}
