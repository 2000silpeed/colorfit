"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence, useReducedMotion } from "framer-motion";

type Gender = "female" | "male";
type AgeGroup = "20s" | "30s" | "40plus";

const GENDER_CARDS: { value: Gender; label: string; initial: string }[] = [
  { value: "female", label: "여성", initial: "W" },
  { value: "male", label: "남성", initial: "M" },
];

const AGE_CARDS: { value: AgeGroup; label: string; sub: string }[] = [
  { value: "20s", label: "10~20대", sub: "트렌디 / 캐주얼" },
  { value: "30s", label: "30대", sub: "모던 / 세미포멀" },
  { value: "40plus", label: "40대+", sub: "클래식 / 편안한" },
];

export default function Step1Page() {
  const router = useRouter();
  const prefersReducedMotion = useReducedMotion();
  const [selectedGender, setSelectedGender] = useState<Gender | null>(null);
  const [selectedAge, setSelectedAge] = useState<AgeGroup | null>(null);

  const handleGenderSelect = (gender: Gender) => {
    if (selectedGender) return;
    setSelectedGender(gender);
    localStorage.setItem("colorfit_gender", gender);
  };

  const handleAgeSelect = (age: AgeGroup) => {
    if (selectedAge) return;
    setSelectedAge(age);
    localStorage.setItem("colorfit_age_group", age);
    setTimeout(() => {
      router.push("/onboarding/step2");
    }, 300);
  };

  const handleSkip = () => {
    if (!selectedGender) {
      setSelectedGender("female");
      localStorage.setItem("colorfit_gender", "female");
    }
    localStorage.setItem("colorfit_age_group", "30s");
    router.push("/onboarding/step2");
  };

  return (
    <div className="flex-1 flex flex-col items-center justify-center px-[20px]">
      <AnimatePresence mode="wait">
        {!selectedGender ? (
          <motion.div
            key="gender"
            initial={false}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.3 }}
            className="flex flex-col items-center"
          >
            <h1 className="font-display text-[28px] font-bold text-text-primary text-center leading-[1.15]">
              나에 대해 알려주세요
            </h1>
            <p className="mt-[var(--space-sm)] font-body text-[15px] text-text-secondary text-center">
              맞춤 코디를 위해 필요해요
            </p>

            <div className="flex gap-[var(--space-md)] mt-[var(--space-2xl)] w-full max-w-[400px] justify-center">
              {GENDER_CARDS.map((card, i) => (
                <motion.button
                  key={card.value}
                  type="button"
                  onClick={() => handleGenderSelect(card.value)}
                  initial={prefersReducedMotion ? false : { y: 30, opacity: 0 }}
                  animate={{ y: 0, opacity: 1, scale: 1 }}
                  transition={
                    prefersReducedMotion
                      ? { duration: 0 }
                      : { duration: 0.4, delay: i * 0.15, ease: "easeOut" }
                  }
                  className="w-[45%] rounded-[var(--radius-xl)] flex flex-col items-center justify-center cursor-pointer border-2 border-transparent"
                  style={{
                    aspectRatio: "3 / 4",
                    backgroundColor: "#FFFFFF",
                  }}
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
          </motion.div>
        ) : (
          <motion.div
            key="age"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
            className="flex flex-col items-center w-full"
          >
            <h1 className="font-display text-[28px] font-bold text-text-primary text-center leading-[1.15]">
              연령대를 선택해주세요
            </h1>
            <p className="mt-[var(--space-sm)] font-body text-[15px] text-text-secondary text-center">
              나이에 맞는 스타일을 추천해드려요
            </p>

            <div className="flex flex-col gap-[var(--space-sm)] mt-[var(--space-2xl)] w-full max-w-[340px]">
              {AGE_CARDS.map((card, i) => (
                <motion.button
                  key={card.value}
                  type="button"
                  onClick={() => handleAgeSelect(card.value)}
                  initial={prefersReducedMotion ? false : { x: 30, opacity: 0 }}
                  animate={
                    selectedAge === card.value
                      ? { x: 0, opacity: 1, scale: 1.02 }
                      : { x: 0, opacity: 1, scale: 1 }
                  }
                  transition={
                    prefersReducedMotion
                      ? { duration: 0 }
                      : { duration: 0.3, delay: i * 0.1, ease: "easeOut" }
                  }
                  className="w-full rounded-[var(--radius-lg)] flex items-center justify-between px-[24px] py-[20px] cursor-pointer border-2"
                  style={{
                    backgroundColor: "#FFFFFF",
                    borderColor:
                      selectedAge === card.value
                        ? "var(--color-accent)"
                        : "transparent",
                    transition: "border-color 0.3s ease-out",
                  }}
                  aria-pressed={selectedAge === card.value}
                  aria-label={`${card.label} 선택`}
                >
                  <span className="font-body text-[17px] font-semibold text-text-primary">
                    {card.label}
                  </span>
                  <span className="font-body text-[13px] text-text-secondary">
                    {card.sub}
                  </span>
                </motion.button>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

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
        aria-label="건너뛰기"
      >
        건너뛰기
      </motion.button>
    </div>
  );
}
