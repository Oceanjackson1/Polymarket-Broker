"use client";

import { motion } from "motion/react";

interface AnimatedProbabilityProps {
  probability: number;
  yesLabel: string;
}

export function AnimatedProbability({ probability, yesLabel }: AnimatedProbabilityProps) {
  return (
    <div className="flex items-baseline gap-2">
      <motion.span
        className="font-mono text-4xl font-bold text-accent-gold"
        initial={{ opacity: 0, scale: 0.8 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ type: "spring", stiffness: 300, damping: 20 }}
      >
        {probability}%
      </motion.span>
      <span className="text-lg font-medium text-text-secondary">
        {yesLabel}
      </span>
    </div>
  );
}
