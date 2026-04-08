"use client";

import { useState, useCallback, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { motion, AnimatePresence, useReducedMotion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

type SeasonId = "spring_warm" | "summer_cool" | "autumn_warm" | "winter_cool";

interface ToneChip {
  id: string;
  label: string;
  color: string;
}

interface Season {
  id: SeasonId;
  label: string;
  gradient: string;
  tones: ToneChip[];
}

const SEASONS: Season[] = [
  {
    id: "spring_warm",
    label: "봄웜",
    gradient: "linear-gradient(90deg, #FF7F7F, #FFAA8A, #FFF5E1)",
    tones: [
      { id: "spring_warm_light", label: "라이트", color: "#FFCBA4" },
      { id: "spring_warm_bright", label: "브라이트", color: "#FF6B6B" },
      { id: "spring_warm_vivid", label: "비비드", color: "#FF7043" },
    ],
  },
  {
    id: "summer_cool",
    label: "여름쿨",
    gradient: "linear-gradient(90deg, #B8A9D4, #87CEEB, #98D4BB)",
    tones: [
      { id: "summer_cool_light", label: "라이트", color: "#9FB5D4" },
      { id: "summer_cool_soft", label: "소프트", color: "#B0A6C6" },
      { id: "summer_cool_mute", label: "뮤트", color: "#8B8B9E" },
    ],
  },
  {
    id: "autumn_warm",
    label: "가을웜",
    gradient: "linear-gradient(90deg, #800020, #CC5533, #C4A265)",
    tones: [
      { id: "autumn_warm_deep", label: "딥", color: "#8B5A2B" },
      { id: "autumn_warm_mute", label: "뮤트", color: "#A0856C" },
      { id: "autumn_warm_strong", label: "스트롱", color: "#D4722A" },
    ],
  },
  {
    id: "winter_cool",
    label: "겨울쿨",
    gradient: "linear-gradient(90deg, #1A1A2E, #2E4A8E, #F0C0D0)",
    tones: [
      { id: "winter_cool_deep", label: "딥", color: "#1E1E4E" },
      { id: "winter_cool_strong", label: "스트롱", color: "#6B2E8E" },
      { id: "winter_cool_vivid", label: "비비드", color: "#CC0066" },
    ],
  },
];

interface DiagnosisOption {
  id: string;
  label: string;
  color: string;
}

const Q1_OPTIONS: DiagnosisOption[] = [
  { id: "spring_warm", label: "봄웜", color: "#FFCBA4" },
  { id: "summer_cool", label: "여름쿨", color: "#9FB5D4" },
  { id: "autumn_warm", label: "가을웜", color: "#8B5A2B" },
  { id: "winter_cool", label: "겨울쿨", color: "#1E1E4E" },
];

type Q2Choice = "basic" | "earth" | "pastel" | "vivid";

const Q2_TONE_MAP: Record<string, Record<Q2Choice, string>> = {
  spring_warm: {
    basic: "spring_warm_light",
    earth: "spring_warm_light",
    pastel: "spring_warm_light",
    vivid: "spring_warm_vivid",
  },
  summer_cool: {
    basic: "summer_cool_mute",
    earth: "summer_cool_mute",
    pastel: "summer_cool_light",
    vivid: "summer_cool_soft",
  },
  autumn_warm: {
    basic: "autumn_warm_mute",
    earth: "autumn_warm_deep",
    pastel: "autumn_warm_mute",
    vivid: "autumn_warm_strong",
  },
  winter_cool: {
    basic: "winter_cool_deep",
    earth: "winter_cool_deep",
    pastel: "winter_cool_strong",
    vivid: "winter_cool_vivid",
  },
};

function needsLightText(color: string): boolean {
  const hex = color.replace("#", "");
  const r = parseInt(hex.substring(0, 2), 16);
  const g = parseInt(hex.substring(2, 4), 16);
  const b = parseInt(hex.substring(4, 6), 16);
  const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
  return luminance < 0.5;
}

export default function Step2Page() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const isChangeMode = searchParams.get("mode") === "change";
  const prefersReducedMotion = useReducedMotion();

  const [selectedSeason, setSelectedSeason] = useState<SeasonId | null>(null);
  const [selectedTone, setSelectedTone] = useState<string | null>(null);

  /* 톤 변경 모드: 현재 톤 미리 선택 */
  useEffect(() => {
    if (!isChangeMode) return;
    const currentTone = localStorage.getItem("colorfit_tone_id") ?? localStorage.getItem("colorfit_tone");
    if (!currentTone) return;
    // 정확한 tone 매칭 우선
    const exact = SEASONS.find((s) => s.tones.some((t) => t.id === currentTone));
    if (exact) {
      setSelectedSeason(exact.id);
      setSelectedTone(currentTone);
      return;
    }
    // season prefix로 fallback (e.g. spring_warm_vivid → spring_warm)
    const seasonId = SEASONS.find((s) => currentTone.startsWith(s.id))?.id;
    if (seasonId) setSelectedSeason(seasonId as SeasonId);
  }, [isChangeMode]);
  const [showBottomSheet, setShowBottomSheet] = useState(false);
  const [diagnosisStep, setDiagnosisStep] = useState(0);
  const [diagnosisAnswer, setDiagnosisAnswer] = useState<string | null>(null);

  const handleSeasonSelect = useCallback((seasonId: SeasonId) => {
    setSelectedSeason(seasonId);
    setSelectedTone(null);
  }, []);

  const handleToneSelect = useCallback((toneId: string) => {
    setSelectedTone(toneId);
  }, []);

  const handleNext = useCallback(() => {
    if (!selectedTone) return;
    localStorage.setItem("colorfit_tone", selectedTone);
    localStorage.setItem("colorfit_tone_id", selectedTone);
    if (isChangeMode) {
      router.replace("/profile");
      return;
    }
    router.push("/onboarding/step3");
  }, [selectedTone, isChangeMode, router]);

  const handleDiagnosisQ1 = useCallback((seasonId: string) => {
    setDiagnosisAnswer(seasonId);
    setDiagnosisStep(1);
  }, []);

  const handleDiagnosisQ2 = useCallback((choice: Q2Choice) => {
    if (!diagnosisAnswer) return;
    const seasonTones = Q2_TONE_MAP[diagnosisAnswer];
    const toneId = seasonTones?.[choice];
    const season = SEASONS.find((s) => s.id === diagnosisAnswer);
    if (season && toneId) {
      setSelectedSeason(season.id);
      setSelectedTone(toneId);
    }
    setShowBottomSheet(false);
    setDiagnosisStep(0);
    setDiagnosisAnswer(null);
  }, [diagnosisAnswer]);

  const motionProps = prefersReducedMotion ? { duration: 0 } : undefined;

  useEffect(() => {
    if (!showBottomSheet) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") setShowBottomSheet(false);
    };
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [showBottomSheet]);

  return (
    <div className="flex-1 flex flex-col pb-[var(--space-lg)]">
      <div className="mt-[var(--space-xl)]">
        <h1 className="font-display text-[24px] font-bold text-text-primary text-center leading-[1.25]">
          어떤 컬러가 잘 어울리세요?
        </h1>
      </div>

      <div className="mt-[var(--space-2xl)] flex flex-col gap-[var(--space-lg)]">
        {SEASONS.map((season, i) => {
          const isSelected = selectedSeason === season.id;
          const isDimmed = selectedSeason !== null && !isSelected;

          return (
            <motion.div
              key={season.id}
              initial={prefersReducedMotion ? false : { y: 30, opacity: 0 }}
              animate={{
                y: 0,
                opacity: isDimmed ? 0.4 : 1,
              }}
              transition={
                motionProps ?? {
                  y: { duration: 0.4, delay: i * 0.1, ease: "easeOut" },
                  opacity: { duration: 0.3 },
                }
              }
            >
              <button
                type="button"
                onClick={() => handleSeasonSelect(season.id)}
                className="w-full text-left cursor-pointer bg-transparent border-none p-0"
                aria-pressed={isSelected}
                aria-label={`${season.label} 시즌 선택`}
              >
                <div className="flex items-center gap-[var(--space-sm)] mb-[var(--space-xs)]">
                  <span className="font-body text-[13px] font-medium text-text-secondary">
                    {season.label}
                  </span>
                </div>
                <motion.div
                  animate={{ height: isSelected ? 64 : 48 }}
                  transition={
                    motionProps ?? { duration: 0.3, ease: "easeOut" }
                  }
                  className="w-full rounded-full"
                  style={{ background: season.gradient }}
                />
              </button>

              <AnimatePresence>
                {isSelected && (
                  <motion.div
                    initial={prefersReducedMotion ? false : { height: 0, opacity: 0 }}
                    animate={{ height: "auto", opacity: 1 }}
                    exit={prefersReducedMotion ? undefined : { height: 0, opacity: 0 }}
                    transition={
                      motionProps ?? { duration: 0.3, ease: "easeOut" }
                    }
                    className="overflow-hidden"
                  >
                    <div className="flex gap-[var(--space-lg)] justify-center mt-[var(--space-md)]">
                      {season.tones.map((tone) => {
                        const isToneSelected = selectedTone === tone.id;
                        return (
                          <button
                            key={tone.id}
                            type="button"
                            onClick={() => handleToneSelect(tone.id)}
                            className="flex flex-col items-center gap-[var(--space-xs)] cursor-pointer bg-transparent border-none p-0"
                            aria-pressed={isToneSelected}
                            aria-label={`${season.label} ${tone.label} 톤 선택`}
                          >
                            <div
                              className="size-8 rounded-full transition-shadow duration-200 ease-out"
                              style={{
                                backgroundColor: tone.color,
                                boxShadow: isToneSelected
                                  ? "0 0 0 3px var(--color-accent)"
                                  : "0 0 0 1px var(--color-border)",
                              }}
                            />
                            <span
                              className={`font-body text-[11px] ${
                                isToneSelected
                                  ? "font-semibold text-[var(--color-accent)]"
                                  : "font-normal text-text-secondary"
                              }`}
                            >
                              {tone.label}
                            </span>
                          </button>
                        );
                      })}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          );
        })}
      </div>

      <div className="mt-auto pt-[var(--space-2xl)] flex flex-col items-center gap-[var(--space-md)]">
        <Button
          variant="link"
          onClick={() => {
            setShowBottomSheet(true);
            setDiagnosisStep(0);
            setDiagnosisAnswer(null);
          }}
          className="font-body text-[14px] text-text-secondary"
        >
          잘 모르겠어요
        </Button>

        <Button
          onClick={handleNext}
          disabled={!selectedTone}
          className="w-full h-14 font-body text-[16px] font-semibold rounded-[var(--radius-xl)] transition-[background-color,color] duration-300 ease-out"
          style={{
            backgroundColor: selectedTone
              ? "var(--color-accent)"
              : "#E0DCD7",
            color: selectedTone ? "#FFFFFF" : "var(--color-text-tertiary)",
          }}
          aria-label={isChangeMode ? "톤 변경 저장" : "다음 단계로"}
        >
          {isChangeMode ? "변경하기" : "다음"}
        </Button>
      </div>

      {/* 바텀시트 — 간이 진단 */}
      <AnimatePresence>
        {showBottomSheet && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={motionProps ?? { duration: 0.2 }}
              className="fixed inset-0 z-40 bg-black/40"
              onClick={() => setShowBottomSheet(false)}
            />
            <motion.div
              initial={prefersReducedMotion ? false : { y: "100%" }}
              animate={{ y: 0 }}
              exit={prefersReducedMotion ? undefined : { y: "100%" }}
              transition={
                motionProps ?? {
                  type: "spring",
                  stiffness: 300,
                  damping: 30,
                }
              }
              role="dialog"
              aria-modal="true"
              aria-label="퍼스널컬러 간이 진단"
              className="fixed bottom-0 left-0 right-0 z-50 rounded-t-[var(--radius-lg)] bg-[var(--color-bg-primary)] px-[var(--space-lg)] pt-[var(--space-lg)] pb-[var(--space-2xl)]"
            >
              <div className="w-10 h-1 rounded-full bg-[var(--color-border)] mx-auto mb-[var(--space-lg)]" />

              {diagnosisStep === 0 ? (
                <div>
                  <h2 className="font-display text-[20px] font-bold text-text-primary text-center leading-[1.3]">
                    피부톤에 가장 가까운 이미지를 골라주세요
                  </h2>
                  <p className="mt-[var(--space-sm)] font-body text-[13px] text-text-secondary text-center">
                    1 / 2
                  </p>
                  <div className="grid grid-cols-2 gap-[var(--space-md)] mt-[var(--space-lg)]">
                    {Q1_OPTIONS.map((opt) => (
                      <Card
                        key={opt.id}
                        className="cursor-pointer border-2 border-transparent bg-[var(--color-surface)] ring-0 transition-[border-color] duration-200 ease-out hover:border-[var(--color-accent)] p-0"
                        onClick={() => handleDiagnosisQ1(opt.id)}
                        role="button"
                        aria-label={`${opt.label} 선택`}
                      >
                        <CardContent className="flex flex-col items-center gap-[var(--space-sm)] p-[var(--space-md)]">
                          <div
                            className="size-12 rounded-full shadow-[0_0_0_1px_var(--color-border)]"
                            style={{ backgroundColor: opt.color }}
                          />
                          <span className="font-body text-[14px] font-medium text-text-primary">
                            {opt.label}
                          </span>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                </div>
              ) : (
                <div>
                  <h2 className="font-display text-[20px] font-bold text-text-primary text-center leading-[1.3]">
                    평소 자주 입는 상의 색 계열은?
                  </h2>
                  <p className="mt-[var(--space-sm)] font-body text-[13px] text-text-secondary text-center">
                    2 / 2
                  </p>
                  <div className="grid grid-cols-2 gap-[var(--space-md)] mt-[var(--space-lg)]">
                    {([
                      { label: "베이직", choice: "basic" as Q2Choice, colors: ["#222222", "#FFFFFF", "#808080"] },
                      { label: "어스톤", choice: "earth" as Q2Choice, colors: ["#8B5A2B", "#A0856C", "#C4A265"] },
                      { label: "파스텔", choice: "pastel" as Q2Choice, colors: ["#FFB6C1", "#B0C4DE", "#98FB98"] },
                      { label: "비비드", choice: "vivid" as Q2Choice, colors: ["#FF0000", "#0000FF", "#FFD700"] },
                    ]).map((opt) => (
                      <Card
                        key={opt.label}
                        className="cursor-pointer border-2 border-transparent bg-[var(--color-surface)] ring-0 transition-[border-color] duration-200 ease-out hover:border-[var(--color-accent)] p-0"
                        onClick={() => handleDiagnosisQ2(opt.choice)}
                        role="button"
                        aria-label={`${opt.label} 선택`}
                      >
                        <CardContent className="flex flex-col items-center gap-[var(--space-sm)] p-[var(--space-md)]">
                          <div className="flex gap-[var(--space-xs)]">
                            {opt.colors.map((c) => (
                              <div
                                key={c}
                                className="size-6 rounded-full"
                                style={{
                                  backgroundColor: c,
                                  boxShadow: needsLightText(c) ? "none" : "inset 0 0 0 1px var(--color-border)",
                                }}
                              />
                            ))}
                          </div>
                          <span className="font-body text-[14px] font-medium text-text-primary">
                            {opt.label}
                          </span>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                </div>
              )}
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  );
}
