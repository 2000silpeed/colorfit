"use client";

import { useState, useCallback, useRef } from "react";
import { useRouter } from "next/navigation";
import { motion, useReducedMotion } from "framer-motion";
import { Button } from "@/components/ui/button";

const BUDGET_MIN = 0;
const BUDGET_MAX = 500000;
const BUDGET_STEP = 10000;

interface Preset {
  label: string;
  min: number;
  max: number;
}

const PRESETS: Preset[] = [
  { label: "~5만", min: 0, max: 50000 },
  { label: "5~15만", min: 50000, max: 150000 },
  { label: "15~30만", min: 150000, max: 300000 },
  { label: "30만~", min: 300000, max: 500000 },
];

function formatPrice(value: number): string {
  return `₩${value.toLocaleString("ko-KR")}`;
}

function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max);
}

export default function Step4Page() {
  const router = useRouter();
  const prefersReducedMotion = useReducedMotion();
  const trackRef = useRef<HTMLDivElement>(null);
  const draggingRef = useRef<"min" | "max" | null>(null);
  const [dragging, setDragging] = useState<"min" | "max" | null>(null);

  const [rangeMin, setRangeMin] = useState(() => {
    if (typeof window === "undefined") return 30000;
    try {
      const stored = localStorage.getItem("colorfit_budget");
      if (stored) {
        const parsed = JSON.parse(stored);
        if (
          Array.isArray(parsed) &&
          parsed.length === 2 &&
          typeof parsed[0] === "number"
        )
          return parsed[0] as number;
      }
    } catch {}
    return 30000;
  });
  const [rangeMax, setRangeMax] = useState(() => {
    if (typeof window === "undefined") return 100000;
    try {
      const stored = localStorage.getItem("colorfit_budget");
      if (stored) {
        const parsed = JSON.parse(stored);
        if (
          Array.isArray(parsed) &&
          parsed.length === 2 &&
          typeof parsed[1] === "number"
        )
          return parsed[1] as number;
      }
    } catch {}
    return 100000;
  });
  const [activePreset, setActivePreset] = useState<number | null>(null);
  const [hasBudgetSet, setHasBudgetSet] = useState(false);

  const toPercent = useCallback(
    (value: number) =>
      ((value - BUDGET_MIN) / (BUDGET_MAX - BUDGET_MIN)) * 100,
    [],
  );

  const fromClientX = useCallback((clientX: number): number => {
    if (!trackRef.current) return 0;
    const rect = trackRef.current.getBoundingClientRect();
    const ratio = clamp((clientX - rect.left) / rect.width, 0, 1);
    const raw = BUDGET_MIN + ratio * (BUDGET_MAX - BUDGET_MIN);
    return Math.round(raw / BUDGET_STEP) * BUDGET_STEP;
  }, []);

  const handlePointerDown = useCallback(
    (thumb: "min" | "max") => (e: React.PointerEvent) => {
      e.preventDefault();
      draggingRef.current = thumb;
      setDragging(thumb);
      (e.target as HTMLElement).setPointerCapture(e.pointerId);
    },
    [],
  );

  const handlePointerMove = useCallback(
    (e: React.PointerEvent) => {
      if (!draggingRef.current) return;
      const value = fromClientX(e.clientX);
      if (draggingRef.current === "min") {
        setRangeMax((prevMax) => {
          setRangeMin(clamp(value, BUDGET_MIN, prevMax - BUDGET_STEP));
          return prevMax;
        });
      } else {
        setRangeMin((prevMin) => {
          setRangeMax(clamp(value, prevMin + BUDGET_STEP, BUDGET_MAX));
          return prevMin;
        });
      }
      setActivePreset(null);
      setHasBudgetSet(true);
    },
    [fromClientX],
  );

  const handlePointerUp = useCallback(() => {
    draggingRef.current = null;
    setDragging(null);
  }, []);

  const handleKeyDown = useCallback(
    (thumb: "min" | "max") => (e: React.KeyboardEvent) => {
      const delta =
        e.key === "ArrowRight" || e.key === "ArrowUp"
          ? BUDGET_STEP
          : e.key === "ArrowLeft" || e.key === "ArrowDown"
            ? -BUDGET_STEP
            : 0;
      if (delta === 0) return;
      e.preventDefault();
      if (thumb === "min") {
        setRangeMax((prevMax) => {
          setRangeMin((prev) =>
            clamp(prev + delta, BUDGET_MIN, prevMax - BUDGET_STEP),
          );
          return prevMax;
        });
      } else {
        setRangeMin((prevMin) => {
          setRangeMax((prev) =>
            clamp(prev + delta, prevMin + BUDGET_STEP, BUDGET_MAX),
          );
          return prevMin;
        });
      }
      setActivePreset(null);
      setHasBudgetSet(true);
    },
    [],
  );

  const handlePreset = useCallback((index: number, preset: Preset) => {
    setRangeMin(preset.min);
    setRangeMax(preset.max);
    setActivePreset(index);
    setHasBudgetSet(true);
  }, []);

  const handleNext = useCallback(() => {
    try {
      localStorage.setItem(
        "colorfit_budget",
        JSON.stringify([rangeMin, rangeMax]),
      );
    } catch {}
    router.push("/onboarding/step5");
  }, [rangeMin, rangeMax, router]);

  const leftPercent = toPercent(rangeMin);
  const rightPercent = toPercent(rangeMax);

  return (
    <div className="flex-1 flex flex-col pb-[var(--space-lg)]">
      {/* 헤드라인 */}
      <div className="mt-[var(--space-xl)]">
        <h1 className="font-display text-[24px] font-bold text-text-primary text-center leading-[1.25]">
          예산 범위를 알려주세요
        </h1>
      </div>

      {/* 가격 표시 */}
      <motion.div
        className="mt-[var(--space-2xl)] text-center"
        initial={prefersReducedMotion ? false : { opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={
          prefersReducedMotion
            ? { duration: 0 }
            : { duration: 0.3, ease: "easeOut" }
        }
      >
        <span className="font-body text-[18px] font-bold text-text-primary">
          {formatPrice(rangeMin)} ~ {formatPrice(rangeMax)}
        </span>
      </motion.div>

      {/* Dual Range Slider */}
      <div className="mt-[var(--space-xl)] px-[var(--space-xs)]">
        <div
          ref={trackRef}
          className="relative h-[6px] rounded-full"
          style={{ backgroundColor: "#E0DCD7" }}
          onPointerMove={handlePointerMove}
          onPointerUp={handlePointerUp}
          onPointerLeave={handlePointerUp}
        >
          {/* Active range */}
          <div
            className="absolute top-0 h-full rounded-full"
            style={{
              left: `${leftPercent}%`,
              width: `${rightPercent - leftPercent}%`,
              backgroundColor: "var(--color-accent)",
            }}
          />

          {/* Min thumb */}
          <div
            className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 w-[24px] h-[24px] rounded-full border-[3px] cursor-grab active:cursor-grabbing touch-none"
            style={{
              left: `${leftPercent}%`,
              backgroundColor: "#FFFFFF",
              borderColor: "var(--color-accent)",
              boxShadow: "0 2px 6px rgba(0,0,0,0.12)",
              zIndex: dragging === "min" ? 2 : 1,
            }}
            onPointerDown={handlePointerDown("min")}
            onKeyDown={handleKeyDown("min")}
            role="slider"
            aria-label="최소 예산"
            aria-valuemin={BUDGET_MIN}
            aria-valuemax={BUDGET_MAX}
            aria-valuenow={rangeMin}
            aria-valuetext={formatPrice(rangeMin)}
            tabIndex={0}
          />

          {/* Max thumb */}
          <div
            className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 w-[24px] h-[24px] rounded-full border-[3px] cursor-grab active:cursor-grabbing touch-none"
            style={{
              left: `${rightPercent}%`,
              backgroundColor: "#FFFFFF",
              borderColor: "var(--color-accent)",
              boxShadow: "0 2px 6px rgba(0,0,0,0.12)",
              zIndex: dragging === "max" ? 2 : 1,
            }}
            onPointerDown={handlePointerDown("max")}
            onKeyDown={handleKeyDown("max")}
            role="slider"
            aria-label="최대 예산"
            aria-valuemin={BUDGET_MIN}
            aria-valuemax={BUDGET_MAX}
            aria-valuenow={rangeMax}
            aria-valuetext={formatPrice(rangeMax)}
            tabIndex={0}
          />
        </div>

        {/* 범위 라벨 */}
        <div className="flex justify-between mt-[var(--space-sm)]">
          <span className="font-body text-[12px] text-text-tertiary">
            {formatPrice(BUDGET_MIN)}
          </span>
          <span className="font-body text-[12px] text-text-tertiary">
            {formatPrice(BUDGET_MAX)}
          </span>
        </div>
      </div>

      {/* 프리셋 버튼 */}
      <div className="mt-[var(--space-2xl)]">
        <span className="font-body text-[13px] text-text-secondary mb-[var(--space-sm)] block">
          빠른 선택
        </span>
        <div className="flex gap-[var(--space-sm)]">
          {PRESETS.map((preset, i) => {
            const isActive = activePreset === i;
            return (
              <motion.button
                key={preset.label}
                type="button"
                onClick={() => handlePreset(i, preset)}
                initial={prefersReducedMotion ? false : { y: 15, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={
                  prefersReducedMotion
                    ? { duration: 0 }
                    : { duration: 0.3, delay: i * 0.05, ease: "easeOut" }
                }
                className="flex-1 py-[var(--space-sm)] rounded-full font-body text-[14px] font-medium cursor-pointer border-2"
                style={{
                  backgroundColor: isActive
                    ? "var(--color-accent)"
                    : "#FFFFFF",
                  borderColor: isActive ? "var(--color-accent)" : "#E0DCD7",
                  color: isActive ? "#FFFFFF" : "var(--color-text-primary)",
                  transition:
                    "background-color 0.2s ease-out, border-color 0.2s ease-out, color 0.2s ease-out",
                }}
                aria-pressed={isActive}
                aria-label={`예산 프리셋 ${preset.label}`}
              >
                {preset.label}
              </motion.button>
            );
          })}
        </div>
      </div>

      {/* CTA */}
      <div className="mt-auto pt-[var(--space-2xl)]">
        <motion.div
          animate={
            hasBudgetSet && !prefersReducedMotion
              ? {
                  scale: [1, 1.03, 1],
                  transition: { duration: 0.4, ease: "easeInOut" },
                }
              : {}
          }
        >
          <Button
            variant="default"
            onClick={handleNext}
            className="w-full h-14 font-body text-base font-bold rounded-[var(--radius-xl)]"
            style={{
              backgroundColor: "var(--color-accent)",
              color: "#FFFFFF",
            }}
            aria-label="추천 코디 보러가기"
          >
            추천 코디 보러가기
          </Button>
        </motion.div>
      </div>
    </div>
  );
}
