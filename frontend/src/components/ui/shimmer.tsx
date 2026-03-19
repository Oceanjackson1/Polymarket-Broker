import clsx from "clsx";

interface ShimmerProps {
  className?: string;
}

export function Shimmer({ className }: ShimmerProps) {
  return <div className={clsx("skeleton-shimmer", className)} />;
}
