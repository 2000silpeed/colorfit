"use client";

import { motion, useReducedMotion } from "framer-motion";

interface OnboardingTemplateProps {
  children: React.ReactNode;
}

export default function OnboardingTemplate({ children }: OnboardingTemplateProps) {
  const prefersReducedMotion = useReducedMotion();

  return (
    <motion.div
      initial={prefersReducedMotion ? false : { x: 60, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      transition={
        prefersReducedMotion
          ? { duration: 0 }
          : { type: "spring", stiffness: 300, damping: 30 }
      }
      className="flex-1 flex flex-col"
    >
      {children}
    </motion.div>
  );
}
