"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence, useReducedMotion } from "framer-motion";
import {
  fetchPreferenceStatus,
  resetPreference,
  type PreferenceStatusResponse,
} from "@/lib/api";

/* ── Seed 라벨 매핑 ── */
const SEED_LABELS: Record<string, Record<string, string>> = {
  mood: {
    casual: "캐주얼",
    minimal: "미니멀",
    romantic: "로맨틱",
    street: "스트릿",
    classic: "클래식",
    lovely: "러블리",
    sporty: "스포티",
    modern: "모던",
  },
  silhouette: {
    fitted: "피티드",
    relaxed: "릴랙스드",
    oversized: "오버사이즈",
    structured: "스트럭처드",
  },
  color: {
    neutral: "뉴트럴",
    vivid: "비비드",
    pastel: "파스텔",
    dark: "다크",
    earth: "어스톤",
    monochrome: "모노크롬",
  },
  price: {
    budget: "가성비",
    mid: "중간",
    premium: "프리미엄",
    luxury: "럭셔리",
  },
};

function getSeedLabel(axis: string, value: string | null): string {
  if (!value) return "미설정";
  return SEED_LABELS[axis]?.[value] ?? value;
}

/* ── 스켈레톤 ── */
function PreferenceSkeleton() {
  return (
    <div className="min-h-screen bg-bg-primary pb-[80px]">
      <div className="px-[20px] pt-[56px]">
        <div className="h-[24px] w-1/3 rounded bg-[#E0DCD7] animate-pulse mb-[32px]" />
        <div className="grid grid-cols-2 gap-[12px] mb-[32px]">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-[88px] rounded-[12px] bg-[#E0DCD7] animate-pulse" />
          ))}
        </div>
        <div className="h-[48px] rounded-[8px] bg-[#E0DCD7] animate-pulse mb-[16px]" />
        <div className="h-[48px] rounded-[8px] bg-[#E0DCD7] animate-pulse" />
      </div>
    </div>
  );
}

/* ── Seed 축 카드 ── */
interface SeedAxisCardProps {
  label: string;
  icon: React.ReactNode;
  value: string;
}

function SeedAxisCard({ label, icon, value }: SeedAxisCardProps) {
  return (
    <div
      className="flex flex-col items-center justify-center py-[16px] px-[12px] rounded-[12px] border"
      style={{
        borderColor: "var(--color-border)",
        backgroundColor: "var(--color-surface)",
      }}
    >
      <div className="mb-[6px]">{icon}</div>
      <span
        className="text-[12px] text-text-secondary mb-[4px]"
        style={{ fontFamily: "var(--font-body)" }}
      >
        {label}
      </span>
      <span
        className="text-[14px] text-text-primary font-medium"
        style={{ fontFamily: "var(--font-body)" }}
      >
        {value}
      </span>
    </div>
  );
}

/* ── 학습 진행바 ── */
function LearningProgressBar({ count, target }: { count: number; target: number }) {
  const ratio = Math.min(count / target, 1);
  const percent = Math.round(ratio * 100);

  return (
    <div className="mt-[32px]">
      <div className="flex items-center justify-between mb-[8px]">
        <span
          className="text-[14px] text-text-primary font-medium"
          style={{ fontFamily: "var(--font-body)" }}
        >
          학습 상태
        </span>
        <span
          className="text-[13px] text-text-secondary"
          style={{ fontFamily: "var(--font-body)" }}
        >
          피드백 {count}건 / {target}건
        </span>
      </div>
      <div
        className="w-full h-[6px] rounded-full"
        style={{ backgroundColor: "var(--color-score-track)" }}
      >
        <motion.div
          className="h-full rounded-full"
          style={{ backgroundColor: "var(--color-accent)" }}
          initial={{ width: 0 }}
          animate={{ width: `${percent}%` }}
          transition={{ duration: 0.6, ease: "easeOut" }}
        />
      </div>
      <p
        className="text-[12px] text-text-tertiary mt-[6px]"
        style={{ fontFamily: "var(--font-body)" }}
      >
        {count >= target
          ? "충분한 피드백으로 개인화가 완료되었어요"
          : count > 0
            ? `${target - count}건 더 모이면 더 정확한 추천을 받을 수 있어요`
            : "코디에 반응하면 취향을 학습해요"}
      </p>
    </div>
  );
}

/* ── 확인 다이얼로그 ── */
interface ConfirmDialogProps {
  open: boolean;
  title: string;
  description: string;
  confirmLabel: string;
  onConfirm: () => void;
  onCancel: () => void;
}

function ConfirmDialog({ open, title, description, confirmLabel, onConfirm, onCancel }: ConfirmDialogProps) {
  const shouldReduceMotion = useReducedMotion();

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          className="fixed inset-0 z-[100] flex items-center justify-center px-[24px]"
          initial={shouldReduceMotion ? false : { opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.15 }}
        >
          <div className="absolute inset-0 bg-black/40" onClick={onCancel} />
          <motion.div
            className="relative w-full max-w-[320px] rounded-[16px] p-[24px]"
            style={{ backgroundColor: "var(--color-bg-primary)" }}
            initial={shouldReduceMotion ? false : { scale: 0.95, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.95, opacity: 0 }}
            transition={shouldReduceMotion ? { duration: 0 } : { type: "spring", stiffness: 400, damping: 25 }}
          >
            <h3
              className="text-[18px] text-text-primary mb-[8px]"
              style={{ fontFamily: "var(--font-display)", fontWeight: 700, lineHeight: 1.3 }}
            >
              {title}
            </h3>
            <p
              className="text-[14px] text-text-secondary leading-[1.5] mb-[24px]"
              style={{ fontFamily: "var(--font-body)" }}
            >
              {description}
            </p>
            <div className="flex gap-[12px]">
              <button
                onClick={onCancel}
                className="flex-1 py-[12px] rounded-[8px] text-[14px] font-medium border"
                style={{
                  fontFamily: "var(--font-body)",
                  borderColor: "var(--color-border)",
                  color: "var(--color-text-primary)",
                }}
              >
                취소
              </button>
              <button
                onClick={onConfirm}
                className="flex-1 py-[12px] rounded-[8px] text-[14px] font-medium"
                style={{
                  fontFamily: "var(--font-body)",
                  backgroundColor: "var(--color-error-text)",
                  color: "#FFFFFF",
                }}
              >
                {confirmLabel}
              </button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

/* ── 아이콘 ── */
function MoodIcon() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="var(--color-accent)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10" />
      <path d="M8 14s1.5 2 4 2 4-2 4-2" />
      <line x1="9" y1="9" x2="9.01" y2="9" strokeWidth="2" />
      <line x1="15" y1="9" x2="15.01" y2="9" strokeWidth="2" />
    </svg>
  );
}

function SilhouetteIcon() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="var(--color-score-of)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 2L8 7v4l-4 3v6h16v-6l-4-3V7l-4-5z" />
    </svg>
  );
}

function ColorIcon() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="var(--color-score-ch)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10" />
      <circle cx="12" cy="12" r="4" />
      <line x1="12" y1="2" x2="12" y2="6" />
      <line x1="12" y1="18" x2="12" y2="22" />
      <line x1="2" y1="12" x2="6" y2="12" />
      <line x1="18" y1="12" x2="22" y2="12" />
    </svg>
  );
}

function PriceIcon() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="var(--color-score-pe)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <line x1="12" y1="1" x2="12" y2="23" />
      <path d="M17 5H9.5a3.5 3.5 0 000 7h5a3.5 3.5 0 010 7H6" />
    </svg>
  );
}

export default function PreferencePage() {
  const router = useRouter();
  const shouldReduceMotion = useReducedMotion();

  const [data, setData] = useState<PreferenceStatusResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [dialogMode, setDialogMode] = useState<"all" | "feedback_only" | null>(null);
  const [resetting, setResetting] = useState(false);

  const userId = typeof window !== "undefined"
    ? localStorage.getItem("colorfit_user_id") ?? ""
    : "";

  useEffect(() => {
    if (!userId) {
      setLoading(false);
      return;
    }
    fetchPreferenceStatus(userId)
      .then(setData)
      .catch(() => setError("취향 정보를 불러올 수 없습니다"))
      .finally(() => setLoading(false));
  }, [userId]);

  async function handleReset(mode: "all" | "feedback_only") {
    if (!userId) return;
    setResetting(true);
    try {
      await resetPreference(userId, mode);
      const updated = await fetchPreferenceStatus(userId);
      setData(updated);
    } catch {
      setError("초기화 중 오류가 발생했습니다");
    } finally {
      setResetting(false);
      setDialogMode(null);
    }
  }

  if (loading) return <PreferenceSkeleton />;

  if (!userId) {
    return (
      <div className="min-h-screen bg-bg-primary flex flex-col items-center justify-center px-[20px] pb-[80px]">
        <p className="text-text-secondary text-[15px] mb-[16px]" style={{ fontFamily: "var(--font-body)" }}>
          로그인이 필요합니다
        </p>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="min-h-screen bg-bg-primary flex flex-col items-center justify-center px-[20px] pb-[80px]">
        <p className="text-text-secondary text-[15px] mb-[16px]" style={{ fontFamily: "var(--font-body)" }}>
          {error ?? "취향 정보를 불러올 수 없습니다"}
        </p>
        <button
          onClick={() => window.location.reload()}
          className="px-[24px] py-[10px] rounded-full text-[14px] font-medium"
          style={{ fontFamily: "var(--font-body)", backgroundColor: "var(--color-accent)", color: "#FFFFFF" }}
        >
          다시 시도
        </button>
      </div>
    );
  }

  const seed = data.style_seed;
  const phaseLabel = data.learning_phase === "seed"
    ? "시드 단계"
    : data.learning_phase === "hybrid"
      ? "학습 중"
      : "학습 완료";

  return (
    <div className="min-h-screen bg-bg-primary pb-[80px]">
      {/* 헤더 */}
      <div className="sticky top-0 z-10 bg-bg-primary border-b" style={{ borderColor: "var(--color-border)" }}>
        <div className="flex items-center h-[56px] px-[20px]">
          <button onClick={() => router.back()} className="mr-[12px]">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
              <path d="M15 18l-6-6 6-6" stroke="var(--color-text-primary)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </button>
          <h1
            className="text-[18px] text-text-primary"
            style={{ fontFamily: "var(--font-display)", fontWeight: 700, lineHeight: 1.3 }}
          >
            취향 관리
          </h1>
        </div>
      </div>

      {/* Style Seed 시각화 */}
      <motion.div
        className="px-[20px] pt-[24px]"
        initial={shouldReduceMotion ? false : { opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={shouldReduceMotion ? { duration: 0 } : { duration: 0.3 }}
      >
        <div className="flex items-center justify-between mb-[16px]">
          <h2
            className="text-[18px] text-text-primary"
            style={{ fontFamily: "var(--font-display)", fontWeight: 700, lineHeight: 1.3 }}
          >
            현재 취향
          </h2>
          <span
            className="text-[12px] px-[8px] py-[3px] rounded-full"
            style={{
              fontFamily: "var(--font-body)",
              backgroundColor: data.has_seed ? "var(--color-success-bg)" : "var(--color-warning-bg)",
              color: data.has_seed ? "var(--color-success-text)" : "var(--color-warning-text)",
            }}
          >
            {data.has_seed ? phaseLabel : "미분석"}
          </span>
        </div>

        {seed ? (
          <div className="grid grid-cols-2 gap-[12px]">
            <SeedAxisCard label="무드" icon={<MoodIcon />} value={getSeedLabel("mood", seed.mood_seed)} />
            <SeedAxisCard label="실루엣" icon={<SilhouetteIcon />} value={getSeedLabel("silhouette", seed.silhouette_seed)} />
            <SeedAxisCard label="색감" icon={<ColorIcon />} value={getSeedLabel("color", seed.color_seed)} />
            <SeedAxisCard label="가격" icon={<PriceIcon />} value={getSeedLabel("price", seed.price_seed)} />
          </div>
        ) : (
          <div
            className="flex flex-col items-center justify-center py-[32px] rounded-[12px] border"
            style={{ borderColor: "var(--color-border)", backgroundColor: "var(--color-surface)" }}
          >
            <p
              className="text-[14px] text-text-secondary mb-[16px]"
              style={{ fontFamily: "var(--font-body)" }}
            >
              아직 취향 분석을 하지 않았어요
            </p>
            <button
              onClick={() => router.push("/onboarding/step5")}
              className="px-[20px] py-[10px] rounded-full text-[14px] font-medium"
              style={{ fontFamily: "var(--font-body)", backgroundColor: "var(--color-accent)", color: "#FFFFFF" }}
            >
              취향 분석하기
            </button>
          </div>
        )}

        {/* 학습 진행바 */}
        <LearningProgressBar count={data.feedback_count} target={data.learning_target} />
      </motion.div>

      {/* 액션 버튼들 */}
      <motion.div
        className="px-[20px] mt-[32px]"
        initial={shouldReduceMotion ? false : { opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={shouldReduceMotion ? { duration: 0 } : { duration: 0.3, delay: 0.1 }}
      >
        <h2
          className="text-[18px] text-text-primary mb-[16px]"
          style={{ fontFamily: "var(--font-display)", fontWeight: 700, lineHeight: 1.3 }}
        >
          관리
        </h2>

        <div className="space-y-[8px]">
          {/* 재분석 */}
          <button
            onClick={() => router.push("/onboarding/step5")}
            className="flex items-center justify-between w-full py-[14px] px-[16px] rounded-[8px] border"
            style={{ borderColor: "var(--color-border)" }}
          >
            <div className="flex items-center gap-[12px]">
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="var(--color-accent)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="1 4 1 10 7 10" />
                <path d="M3.51 14.5A8 8 0 1018 10" />
              </svg>
              <span className="text-[15px] text-text-primary" style={{ fontFamily: "var(--font-body)" }}>
                취향 다시 분석하기
              </span>
            </div>
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path d="M6 3l5 5-5 5" stroke="var(--color-text-tertiary)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </button>

          {/* 피드백만 초기화 */}
          <button
            onClick={() => setDialogMode("feedback_only")}
            disabled={resetting}
            className="flex items-center justify-between w-full py-[14px] px-[16px] rounded-[8px] border"
            style={{ borderColor: "var(--color-border)" }}
          >
            <span className="text-[15px] text-text-primary" style={{ fontFamily: "var(--font-body)" }}>
              피드백만 초기화
            </span>
            <span className="text-[12px] text-text-tertiary" style={{ fontFamily: "var(--font-body)" }}>
              취향 분석은 유지
            </span>
          </button>

          {/* 전체 초기화 */}
          <button
            onClick={() => setDialogMode("all")}
            disabled={resetting}
            className="flex items-center justify-between w-full py-[14px] px-[16px] rounded-[8px] border"
            style={{ borderColor: "var(--color-error-border)" }}
          >
            <span
              className="text-[15px]"
              style={{ fontFamily: "var(--font-body)", color: "var(--color-error-text)" }}
            >
              취향 초기화
            </span>
            <span className="text-[12px] text-text-tertiary" style={{ fontFamily: "var(--font-body)" }}>
              전체 리셋
            </span>
          </button>
        </div>
      </motion.div>

      {/* 확인 다이얼로그 */}
      <ConfirmDialog
        open={dialogMode === "all"}
        title="취향 초기화"
        description="취향 분석 결과와 피드백 학습 데이터를 모두 초기화할까요? 이 작업은 되돌릴 수 없습니다."
        confirmLabel="초기화"
        onConfirm={() => handleReset("all")}
        onCancel={() => setDialogMode(null)}
      />
      <ConfirmDialog
        open={dialogMode === "feedback_only"}
        title="피드백 초기화"
        description="피드백 학습 데이터만 초기화할까요? 취향 분석 결과(Style Seed)는 유지됩니다."
        confirmLabel="초기화"
        onConfirm={() => handleReset("feedback_only")}
        onCancel={() => setDialogMode(null)}
      />
    </div>
  );
}
