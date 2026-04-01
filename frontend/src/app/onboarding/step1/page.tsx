"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { motion, useReducedMotion } from "framer-motion";

type Gender = "female" | "male";

const CARDS: { value: Gender; label: string; initial: string }[] = [
  { value: "female", label: "여성", initial: "W" },
  { value: "male", label: "남성", initial: "M" },
];

export default function Step1Page() {
  const router = useRouter();
  const prefersReducedMotion = useReducedMotion();
  const [selected, setSelected] = useState<Gender | null>(null);

  const handleSelect = (gender: Gender) => {
    if (selected) return;
    setSelected(gender);
    localStorage.setItem("colorfit_gender", gender);
    setTimeout(() => {
      router.push("/onboarding/step2");
    }, 300);
  };

  const handleSkip = () => {
    if (selected) return;
    handleSelect("female");
  };

  return (
    <div className="flex-1 flex flex-col items-center justify-center">
      <h1 className="font-display text-[28px] font-bold text-text-primary text-center leading-[1.15]">
        나에 대해 알려주세요
      </h1>
      <p className="mt-[var(--space-sm)] font-body text-[15px] text-text-secondary text-center">
        맞춤 코디를 위해 필요해요
      </p>

      <div className="flex gap-[var(--space-md)] mt-[var(--space-2xl)] w-full max-w-[400px] justify-center">
        {CARDS.map((card, i) => (
          <motion.button
            key={card.value}
            type="button"
            onClick={() => handleSelect(card.value)}
            initial={prefersReducedMotion ? false : { y: 30, opacity: 0 }}
            animate={
              selected === card.value
                ? { y: 0, opacity: 1, scale: 1.05 }
                : { y: 0, opacity: 1, scale: 1 }
            }
            transition={
              prefersReducedMotion
                ? { duration: 0 }
                : selected === card.value
                  ? { scale: { duration: 0.3, ease: "easeOut" } }
                  : { duration: 0.4, delay: i * 0.15, ease: "easeOut" }
            }
            className="w-[45%] rounded-[var(--radius-xl)] flex flex-col items-center justify-center cursor-pointer border-2 border-transparent"
            style={{
              aspectRatio: "3 / 4",
              backgroundColor: "#FFFFFF",
              borderColor:
                selected === card.value
                  ? "var(--color-accent)"
                  : "transparent",
              transition: "border-color 0.3s ease-out",
            }}
            aria-pressed={selected === card.value}
            aria-label={`${card.label} 선택`}
          >
            <span
              className="text-text-primary leading-none"
              style={{
                fontFamily: "'Noto Serif', 'Nanum Myeongjo', serif",
                fontSize: "48px",
                fontWeight: 400,
              }}
            >
              {card.initial}
            </span>
            <span className="mt-[var(--space-sm)] font-body text-[15px] text-text-secondary">
              {card.label}
            </span>
          </motion.button>
        ))}
      </div>

      <motion.button
        type="button"
        onClick={handleSkip}
        initial={prefersReducedMotion ? false : { opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={
          prefersReducedMotion
            ? { duration: 0 }
            : { duration: 0.4, delay: 0.5 }
        }
        className="mt-[var(--space-2xl)] font-body text-[14px] text-text-secondary underline cursor-pointer bg-transparent border-none"
        aria-label="건너뛰기 — 기본값(여성)으로 진행"
      >
        건너뛰기
      </motion.button>
    </div>
  );
}
