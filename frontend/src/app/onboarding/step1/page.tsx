"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";
import { motion, AnimatePresence, useReducedMotion } from "framer-motion";
import { Card } from "@/components/ui/card";
import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";

type Gender = "female" | "male";
type AgeGroup = "20s" | "30s" | "40plus";

const MotionCard = motion.create(Card);

const GENDER_CARDS: { value: Gender; label: string; image: string }[] = [
  { value: "female", label: "여성", image: "/gender-female.png?v=3" },
  { value: "male", label: "남성", image: "/gender-male.png?v=3" },
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

            <div className="flex gap-[16px] mt-[48px] w-full max-w-[500px] justify-center px-[10px]">
              {GENDER_CARDS.map((card, i) => (
                <MotionCard
                  key={card.value}
                  role="button"
                  tabIndex={0}
                  onClick={() => handleGenderSelect(card.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" || e.key === " ") {
                      e.preventDefault();
                      handleGenderSelect(card.value);
                    }
                  }}
                  initial={prefersReducedMotion ? false : { y: 30, opacity: 0 }}
                  animate={{ y: 0, opacity: 1, scale: 1 }}
                  transition={
                    prefersReducedMotion
                      ? { duration: 0 }
                      : { duration: 0.4, delay: i * 0.15, ease: "easeOut" }
                  }
                  className="relative group w-1/2 aspect-[3/4] rounded-[24px] flex flex-col items-center justify-center cursor-pointer border-2 border-white/40 bg-white/70 overflow-hidden shadow-lg ring-0 p-0"
                  aria-label={`${card.label} 선택`}
                >
                  <Image
                    src={card.image}
                    alt={card.label}
                    fill
                    className="object-cover transition-transform duration-500 group-hover:scale-105"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-black/10 to-transparent" />
                  
                  <span className="absolute bottom-[24px] font-body text-[17px] font-semibold text-white tracking-widest drop-shadow-md">
                    {card.label}
                  </span>
                </MotionCard>
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
                <MotionCard
                  key={card.value}
                  role="button"
                  tabIndex={0}
                  onClick={() => handleAgeSelect(card.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" || e.key === " ") {
                      e.preventDefault();
                      handleAgeSelect(card.value);
                    }
                  }}
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
                  className={cn(
                    "w-full rounded-[var(--radius-lg)] flex flex-row items-center justify-between px-[24px] py-[20px] cursor-pointer border-2 bg-white/70 backdrop-blur-md shadow-sm ring-0 transition-all duration-300 ease-out hover:bg-white/90",
                    selectedAge === card.value
                      ? "border-[var(--color-accent)] shadow-md"
                      : "border-white/40"
                  )}
                  aria-pressed={selectedAge === card.value}
                  aria-label={`${card.label} 선택`}
                >
                  <span className="font-body text-[17px] font-semibold text-text-primary">
                    {card.label}
                  </span>
                  <span className="font-body text-[13px] text-text-secondary">
                    {card.sub}
                  </span>
                </MotionCard>
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
        className={cn(
          buttonVariants({ variant: "link" }),
          "mt-[var(--space-2xl)] font-body text-[14px] text-text-secondary"
        )}
        aria-label="건너뛰기"
      >
        건너뛰기
      </motion.button>
    </div>
  );
}
