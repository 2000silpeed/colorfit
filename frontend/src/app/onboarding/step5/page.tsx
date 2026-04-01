"use client";

import { useState, useCallback, useRef } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence, useReducedMotion } from "framer-motion";

interface RoundOption {
  id: string;
  label: string;
  color: string;
}

interface Round {
  title: string;
  seedKey: string;
  options: RoundOption[];
}

const ROUNDS: Round[] = [
  {
    title: "무드",
    seedKey: "mood_seed",
    options: [
      { id: "casual", label: "캐주얼", color: "#D4A574" },
      { id: "minimal", label: "미니멀", color: "#B0ACA6" },
      { id: "classic", label: "클래식", color: "#8B7355" },
      { id: "street", label: "스트릿", color: "#4A4A4A" },
    ],
  },
  {
    title: "실루엣",
    seedKey: "silhouette_seed",
    options: [
      { id: "slim", label: "슬림", color: "#A0856C" },
      { id: "oversized", label: "오버사이즈", color: "#C4B8A8" },
      { id: "wide", label: "와이드", color: "#8B8178" },
      { id: "fitted", label: "피티드", color: "#6B5B4E" },
    ],
  },
  {
    title: "컬러",
    seedKey: "color_seed",
    options: [
      { id: "monotone", label: "모노톤", color: "#3A3A3A" },
      { id: "pastel", label: "파스텔", color: "#E8C8B8" },
      { id: "neutral", label: "뉴트럴", color: "#C8B9A8" },
      { id: "contrast", label: "콘트라스트", color: "#964F4C" },
    ],
  },
  {
    title: "가격대",
    seedKey: "price_seed",
    options: [
      { id: "low", label: "SPA", color: "#B8C4A8" },
      { id: "mid", label: "유니섹스", color: "#A8B4C4" },
      { id: "mid_high", label: "디자이너", color: "#C4A8B8" },
      { id: "high", label: "부티크", color: "#8B6B7B" },
    ],
  },
];

const TOTAL_ROUNDS = ROUNDS.length;

export default function Step5Page() {
  const router = useRouter();
  const prefersReducedMotion = useReducedMotion();

  const [currentRound, setCurrentRound] = useState(0);
  const [selected, setSelected] = useState<string | null>(null);
  const [isTransitioning, setIsTransitioning] = useState(false);
  const seedsRef = useRef<Record<string, string>>({});

  const round = ROUNDS[currentRound];

  const advanceRound = useCallback(() => {
    const nextRound = currentRound + 1;
    if (nextRound >= TOTAL_ROUNDS) {
      try {
        localStorage.setItem(
          "colorfit_style_seeds",
          JSON.stringify(seedsRef.current),
        );
        localStorage.setItem(
          "colorfit_seed_confidence",
          String(
            Object.keys(seedsRef.current).length,
          ),
        );
      } catch {}
      router.push("/feed");
      return;
    }
    setIsTransitioning(true);
    const delay = prefersReducedMotion ? 0 : 500;
    setTimeout(() => {
      setCurrentRound(nextRound);
      setSelected(null);
      setIsTransitioning(false);
    }, delay);
  }, [currentRound, prefersReducedMotion, router]);

  const handleSelect = useCallback(
    (optionId: string) => {
      if (selected || isTransitioning) return;
      setSelected(optionId);
      seedsRef.current[round.seedKey] = optionId;
      const delay = prefersReducedMotion ? 0 : 500;
      setTimeout(() => advanceRound(), delay);
    },
    [selected, isTransitioning, round.seedKey, prefersReducedMotion, advanceRound],
  );

  const handlePass = useCallback(() => {
    if (isTransitioning) return;
    advanceRound();
  }, [isTransitioning, advanceRound]);

  const handleSkipAll = useCallback(() => {
    try {
      localStorage.setItem("colorfit_style_seeds", JSON.stringify({}));
      localStorage.setItem("colorfit_seed_confidence", "0");
    } catch {}
    router.push("/feed");
  }, [router]);

  return (
    <div className="flex-1 flex flex-col pb-[var(--space-lg)]">
      {/* 헤드라인 */}
      <div className="mt-[var(--space-xl)]">
        <h1 className="font-display text-[24px] font-bold text-text-primary text-center leading-[1.25]">
          어떤 코디가 마음에 드세요?
        </h1>
        <p className="mt-[var(--space-xs)] font-body text-[14px] text-text-secondary text-center">
          직감적으로 골라주세요
        </p>
      </div>

      {/* 2x2 이미지 그리드 */}
      <div className="mt-[var(--space-xl)] flex-1">
        <AnimatePresence mode="wait">
          <motion.div
            key={currentRound}
            initial={prefersReducedMotion ? false : { opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={prefersReducedMotion ? undefined : { opacity: 0 }}
            transition={
              prefersReducedMotion
                ? { duration: 0 }
                : { duration: 0.3, ease: "easeOut" }
            }
            className="grid grid-cols-2 gap-[var(--space-sm)]"
          >
            {round.options.map((option, i) => {
              const isSelected = selected === option.id;
              const isDimmed = selected !== null && !isSelected;

              return (
                <motion.button
                  key={option.id}
                  type="button"
                  onClick={() => handleSelect(option.id)}
                  disabled={selected !== null || isTransitioning}
                  initial={
                    prefersReducedMotion ? false : { y: 20, opacity: 0 }
                  }
                  animate={{
                    y: 0,
                    opacity: isDimmed ? 0.3 : 1,
                    scale: isSelected ? 0.95 : 1,
                  }}
                  transition={
                    prefersReducedMotion
                      ? { duration: 0 }
                      : {
                          y: { duration: 0.3, delay: i * 0.06, ease: "easeOut" },
                          opacity: { duration: 0.2 },
                          scale: { duration: 0.2 },
                        }
                  }
                  className="relative overflow-hidden rounded-[var(--radius-md)] cursor-pointer border-[3px] disabled:cursor-default"
                  style={{
                    aspectRatio: "3 / 4",
                    borderColor: isSelected
                      ? "var(--color-accent)"
                      : "transparent",
                    transition: "border-color 0.2s ease-out",
                  }}
                  aria-label={`${round.title} 선택: ${option.label}`}
                  aria-pressed={isSelected}
                >
                  {/* 플레이스홀더 이미지 영역 */}
                  <div
                    className="absolute inset-0 flex items-center justify-center"
                    style={{ backgroundColor: option.color }}
                  >
                    <span className="font-body text-[16px] font-semibold text-white drop-shadow-sm">
                      {option.label}
                    </span>
                  </div>
                </motion.button>
              );
            })}
          </motion.div>
        </AnimatePresence>
      </div>

      {/* 라운드 인디케이터 + 패스 */}
      <div className="mt-[var(--space-lg)] flex flex-col items-center gap-[var(--space-md)]">
        {/* 라운드 도트 */}
        <div className="flex items-center gap-[var(--space-sm)]">
          {ROUNDS.map((_, i) => (
            <div
              key={i}
              className="rounded-full"
              style={{
                width: 8,
                height: 8,
                backgroundColor:
                  i <= currentRound ? "var(--color-accent)" : "#E0DCD7",
                transition: "background-color 0.2s ease-out",
              }}
              aria-hidden="true"
            />
          ))}
          <span className="ml-[var(--space-xs)] font-body text-[13px] text-text-secondary">
            {currentRound + 1} / {TOTAL_ROUNDS}
          </span>
        </div>

        {/* 패스 + 건너뛰기 */}
        <div className="flex items-center gap-[var(--space-lg)]">
          <button
            type="button"
            onClick={handlePass}
            disabled={isTransitioning}
            className="font-body text-[14px] text-text-secondary bg-transparent border-none cursor-pointer disabled:cursor-default"
            aria-label="이 라운드 패스"
          >
            패스 →
          </button>
          <button
            type="button"
            onClick={handleSkipAll}
            className="font-body text-[14px] text-text-tertiary bg-transparent border-none cursor-pointer"
            aria-label="취향 분석 건너뛰기"
          >
            건너뛰기
          </button>
        </div>
      </div>
    </div>
  );
}
