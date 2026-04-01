"use client";

import { useState, useCallback, useMemo } from "react";
import { useRouter } from "next/navigation";
import { motion, useReducedMotion } from "framer-motion";

interface TpoOption {
  id: string;
  label: string;
  desc: string;
}

interface MoodOption {
  id: string;
  label: string;
}

const FEMALE_TPOS: TpoOption[] = [
  { id: "commute", label: "출근", desc: "오피스 데일리" },
  { id: "date", label: "데이트", desc: "로맨틱, 첫인상" },
  { id: "interview", label: "면접", desc: "포멀, 신뢰감" },
  { id: "weekend", label: "주말", desc: "편안한 외출" },
  { id: "campus", label: "캠퍼스", desc: "대학 일상" },
  { id: "travel", label: "여행", desc: "활동적, 편안" },
  { id: "event", label: "행사", desc: "하객, 격식" },
  { id: "workout", label: "운동", desc: "애슬레저" },
];

const MALE_TPOS: TpoOption[] = [
  { id: "commute", label: "출근", desc: "비즈니스 캐주얼" },
  { id: "date", label: "데이트", desc: "깔끔한 인상" },
  { id: "interview", label: "면접", desc: "포멀, 단정" },
  { id: "weekend", label: "주말", desc: "편안한 외출" },
  { id: "campus", label: "캠퍼스", desc: "대학 일상" },
  { id: "travel", label: "여행", desc: "활동적, 편안" },
  { id: "event", label: "행사", desc: "수트, 격식" },
  { id: "workout", label: "운동", desc: "애슬레저" },
];

const FEMALE_MOODS: MoodOption[] = [
  { id: "casual", label: "캐주얼" },
  { id: "minimal", label: "미니멀" },
  { id: "lovely", label: "러블리" },
  { id: "classic", label: "클래식" },
  { id: "street", label: "스트릿" },
  { id: "editorial", label: "에디토리얼" },
];

const MALE_MOODS: MoodOption[] = [
  { id: "casual", label: "캐주얼" },
  { id: "minimal", label: "미니멀" },
  { id: "dandy", label: "댄디" },
  { id: "classic", label: "클래식" },
  { id: "street", label: "스트릿" },
  { id: "americana", label: "아메카지" },
];

const TONE_COLORS: Record<string, string> = {
  spring_warm_light: "#FFCBA4",
  spring_warm_bright: "#FF6B6B",
  spring_warm_mute: "#D4A574",
  summer_cool_light: "#9FB5D4",
  summer_cool_soft: "#B0A6C6",
  summer_cool_mute: "#8B8B9E",
  autumn_warm_deep: "#8B5A2B",
  autumn_warm_mute: "#A0856C",
  autumn_warm_bright: "#D4722A",
  winter_cool_deep: "#1E1E4E",
  winter_cool_bright: "#CC0066",
  winter_cool_light: "#E0E0F0",
};

const TONE_LABELS: Record<string, string> = {
  spring_warm_light: "봄웜 라이트",
  spring_warm_bright: "봄웜 브라이트",
  spring_warm_mute: "봄웜 뮤트",
  summer_cool_light: "여름쿨 라이트",
  summer_cool_soft: "여름쿨 소프트",
  summer_cool_mute: "여름쿨 뮤트",
  autumn_warm_deep: "가을웜 딥",
  autumn_warm_mute: "가을웜 뮤트",
  autumn_warm_bright: "가을웜 브라이트",
  winter_cool_deep: "겨울쿨 딥",
  winter_cool_bright: "겨울쿨 브라이트",
  winter_cool_light: "겨울쿨 라이트",
};

const MAX_TPO = 3;
const MAX_MOOD = 5;

export default function Step3Page() {
  const router = useRouter();
  const prefersReducedMotion = useReducedMotion();

  const [gender, setGender] = useState<string>(() => {
    if (typeof window === "undefined") return "female";
    try {
      return localStorage.getItem("colorfit_gender") || "female";
    } catch {}
    return "female";
  });
  const [tone, setTone] = useState<string | null>(() => {
    if (typeof window === "undefined") return null;
    try {
      return localStorage.getItem("colorfit_tone");
    } catch {}
    return null;
  });
  const [selectedTpos, setSelectedTpos] = useState<string[]>([]);
  const [selectedMoods, setSelectedMoods] = useState<string[]>([]);

  const tpoOptions = useMemo(
    () => (gender === "male" ? MALE_TPOS : FEMALE_TPOS),
    [gender],
  );
  const moodOptions = useMemo(
    () => (gender === "male" ? MALE_MOODS : FEMALE_MOODS),
    [gender],
  );

  const handleTpoToggle = useCallback((id: string) => {
    setSelectedTpos((prev) => {
      if (prev.includes(id)) return prev.filter((t) => t !== id);
      if (prev.length >= MAX_TPO) return prev;
      return [...prev, id];
    });
  }, []);

  const handleMoodToggle = useCallback((id: string) => {
    setSelectedMoods((prev) => {
      if (prev.includes(id)) return prev.filter((m) => m !== id);
      if (prev.length >= MAX_MOOD) return prev;
      return [...prev, id];
    });
  }, []);

  const canProceed = selectedTpos.length >= 1;

  const handleNext = useCallback(() => {
    if (!canProceed) return;
    try {
      localStorage.setItem("colorfit_tpos", JSON.stringify(selectedTpos));
      localStorage.setItem("colorfit_moods", JSON.stringify(selectedMoods));
    } catch {}
    router.push("/onboarding/step4");
  }, [canProceed, selectedTpos, selectedMoods, router]);

  const toneColor = tone ? TONE_COLORS[tone] : undefined;
  const toneLabel = tone ? TONE_LABELS[tone] : undefined;

  return (
    <div className="flex-1 flex flex-col pb-[var(--space-lg)]">
      {/* 퍼스널컬러 칩 미리보기 */}
      {tone && toneColor && (
        <motion.div
          initial={prefersReducedMotion ? false : { opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={prefersReducedMotion ? { duration: 0 } : { duration: 0.3 }}
          className="mt-[var(--space-md)] flex items-center justify-center gap-[var(--space-xs)]"
        >
          <div
            className="rounded-full"
            style={{
              width: 24,
              height: 24,
              backgroundColor: toneColor,
              boxShadow: "0 0 0 1px var(--color-border)",
            }}
          />
          <span className="font-body text-[13px] text-text-secondary">
            {toneLabel}
          </span>
        </motion.div>
      )}

      {/* 헤드라인 */}
      <div className="mt-[var(--space-xl)]">
        <h1 className="font-display text-[24px] font-bold text-text-primary text-center leading-[1.25]">
          어떤 상황의 코디를 찾으세요?
        </h1>
      </div>

      {/* TPO 선택 */}
      <div className="mt-[var(--space-2xl)]">
        <div className="flex items-center justify-between mb-[var(--space-sm)]">
          <span className="font-body text-[13px] text-text-secondary">
            TPO 선택
          </span>
          <span className="font-body text-[12px] text-text-tertiary">
            {selectedTpos.length} / {MAX_TPO}
          </span>
        </div>
        <div
          className="flex gap-[var(--space-sm)] overflow-x-auto pb-[var(--space-xs)] [&::-webkit-scrollbar]:hidden"
          style={{ scrollbarWidth: "none" }}
        >
          {tpoOptions.map((tpo, i) => {
            const isSelected = selectedTpos.includes(tpo.id);
            return (
              <motion.button
                key={tpo.id}
                type="button"
                onClick={() => handleTpoToggle(tpo.id)}
                initial={prefersReducedMotion ? false : { y: 20, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={
                  prefersReducedMotion
                    ? { duration: 0 }
                    : { duration: 0.3, delay: i * 0.04, ease: "easeOut" }
                }
                className="flex-shrink-0 px-[var(--space-md)] py-[var(--space-sm)] rounded-full font-body text-[14px] font-medium cursor-pointer border-2"
                style={{
                  backgroundColor: isSelected
                    ? "var(--color-accent)"
                    : "#FFFFFF",
                  borderColor: isSelected
                    ? "var(--color-accent)"
                    : "#E0DCD7",
                  color: isSelected ? "#FFFFFF" : "var(--color-text-primary)",
                  transition:
                    "background-color 0.2s ease-out, border-color 0.2s ease-out, color 0.2s ease-out",
                }}
                aria-pressed={isSelected}
                aria-label={`${tpo.label} — ${tpo.desc}`}
              >
                {tpo.label}
              </motion.button>
            );
          })}
        </div>
      </div>

      {/* 무드 선택 */}
      <div className="mt-[var(--space-2xl)]">
        <div className="flex items-center justify-between mb-[var(--space-md)]">
          <h2 className="font-display text-[18px] font-bold text-text-primary leading-[1.3]">
            분위기도 골라보세요
          </h2>
          <span className="font-body text-[12px] text-text-tertiary">
            {selectedMoods.length} / {MAX_MOOD}
          </span>
        </div>
        <div className="flex flex-wrap gap-x-[var(--space-lg)] gap-y-[var(--space-md)]">
          {moodOptions.map((mood, i) => {
            const isSelected = selectedMoods.includes(mood.id);
            return (
              <motion.button
                key={mood.id}
                type="button"
                onClick={() => handleMoodToggle(mood.id)}
                initial={prefersReducedMotion ? false : { y: 15, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={
                  prefersReducedMotion
                    ? { duration: 0 }
                    : { duration: 0.3, delay: 0.2 + i * 0.05, ease: "easeOut" }
                }
                className="bg-transparent border-none cursor-pointer p-0 pb-[2px] font-body text-[16px]"
                style={{
                  fontWeight: isSelected ? 700 : 400,
                  color: "#222222",
                  borderBottom: isSelected
                    ? "2px solid var(--color-accent)"
                    : "2px solid transparent",
                  transition:
                    "font-weight 0.2s ease-out, border-color 0.2s ease-out",
                }}
                aria-pressed={isSelected}
                aria-label={`${mood.label} 무드 선택`}
              >
                {mood.label}
              </motion.button>
            );
          })}
        </div>
      </div>

      {/* CTA */}
      <div className="mt-auto pt-[var(--space-2xl)]">
        <motion.button
          type="button"
          onClick={handleNext}
          disabled={!canProceed}
          className="w-full font-body text-[16px] font-semibold rounded-[var(--radius-xl)] border-none cursor-pointer disabled:cursor-not-allowed"
          style={{
            height: 56,
            backgroundColor: canProceed
              ? "var(--color-accent)"
              : "#E0DCD7",
            color: canProceed ? "#FFFFFF" : "var(--color-text-tertiary)",
            transition: "background-color 0.3s ease-out, color 0.3s ease-out",
          }}
          aria-label="다음 단계로"
        >
          다음
        </motion.button>
      </div>
    </div>
  );
}
