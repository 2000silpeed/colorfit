"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence, useReducedMotion } from "framer-motion";
import { deleteUser, fetchToneDetail, type ToneDetailResponse } from "@/lib/api";

function clearColorfitStorage(): void {
  for (let i = localStorage.length - 1; i >= 0; i--) {
    const key = localStorage.key(i);
    if (key && key.startsWith("colorfit_")) {
      localStorage.removeItem(key);
    }
  }
}

/* ── 톤별 그라데이션 매핑 ── */
const TONE_GRADIENTS: Record<string, string> = {
  spring_warm_light: "linear-gradient(135deg, #FADADD 0%, #FFE4C4 50%, #FFFACD 100%)",
  spring_warm_bright: "linear-gradient(135deg, #FF7F50 0%, #FFD700 50%, #FFA07A 100%)",
  spring_warm_vivid: "linear-gradient(135deg, #FF6347 0%, #FF8C00 50%, #FFD700 100%)",
  summer_cool_light: "linear-gradient(135deg, #E6E6FA 0%, #B0C4DE 50%, #FFB6C1 100%)",
  summer_cool_soft: "linear-gradient(135deg, #C9B1D0 0%, #B0C4DE 50%, #D4A5A5 100%)",
  summer_cool_bright: "linear-gradient(135deg, #4169E1 0%, #DA70D6 50%, #00CED1 100%)",
  summer_cool_mute: "linear-gradient(135deg, #A9A9C8 0%, #C4B7A6 50%, #B0A6C6 100%)",
  autumn_warm_deep: "linear-gradient(135deg, #8B4513 0%, #800020 50%, #556B2F 100%)",
  autumn_warm_mute: "linear-gradient(135deg, #C4A882 0%, #BDB76B 50%, #BC8F8F 100%)",
  autumn_warm_strong: "linear-gradient(135deg, #CC5500 0%, #B8860B 50%, #8B4513 100%)",
  winter_cool_deep: "linear-gradient(135deg, #191970 0%, #4B0082 50%, #800020 100%)",
  winter_cool_strong: "linear-gradient(135deg, #0000CD 0%, #DC143C 50%, #008080 100%)",
  winter_cool_vivid: "linear-gradient(135deg, #FF0000 0%, #0000FF 50%, #FF00FF 100%)",
};

/* ── 스켈레톤 ── */
function ProfileSkeleton() {
  return (
    <div className="min-h-screen bg-bg-primary pb-[80px]">
      <div className="h-[180px] bg-[#E0DCD7] animate-pulse" />
      <div className="px-[20px] pt-[24px]">
        <div className="flex gap-[12px] mb-[32px]">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="w-[40px] h-[40px] rounded-full bg-[#E0DCD7] animate-pulse" />
          ))}
        </div>
        <div className="space-y-[16px]">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-[48px] rounded-[8px] bg-[#E0DCD7] animate-pulse" />
          ))}
        </div>
      </div>
    </div>
  );
}

/* ── 색상 스와치 ── */
function ColorSwatch({ hex, name }: { hex: string; name: string }) {
  return (
    <div className="flex flex-col items-center gap-[4px]">
      <div
        className="w-[40px] h-[40px] rounded-full border border-border"
        style={{ backgroundColor: hex }}
      />
      <span
        className="text-[11px] leading-[1.4] text-text-tertiary text-center"
        style={{ fontFamily: "var(--font-body)", maxWidth: "48px" }}
      >
        {name}
      </span>
    </div>
  );
}

/* ── TPO 라벨 매핑 ── */
const TPO_LABELS: Record<string, string> = {
  commute: "출근",
  date: "데이트",
  interview: "면접",
  weekend: "주말",
  campus: "캠퍼스",
  travel: "여행",
  event: "행사",
  workout: "운동",
};

export default function ProfilePage() {
  const router = useRouter();
  const shouldReduceMotion = useReducedMotion();
  const [tone, setTone] = useState<ToneDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  const handleLogout = useCallback(() => {
    clearColorfitStorage();
    router.replace("/login");
  }, [router]);

  const handleDeleteAccount = useCallback(async () => {
    if (deleting) return;
    const userId = localStorage.getItem("colorfit_user_id");
    if (!userId) {
      clearColorfitStorage();
      router.replace("/login");
      return;
    }
    setDeleting(true);
    setDeleteError(null);
    try {
      await deleteUser(userId);
      clearColorfitStorage();
      router.replace("/login");
    } catch {
      setDeleteError("계정 삭제에 실패했어요. 다시 시도해주세요.");
      setDeleting(false);
    }
  }, [deleting, router]);

  const toneId = typeof window !== "undefined"
    ? localStorage.getItem("colorfit_tone_id") ?? localStorage.getItem("colorfit_tone") ?? "summer_cool_soft"
    : "summer_cool_soft";
  const gender = typeof window !== "undefined"
    ? localStorage.getItem("colorfit_gender") ?? "female"
    : "female";
  const tpoList: string[] = (() => {
    if (typeof window === "undefined") return [];
    try {
      return JSON.parse(localStorage.getItem("colorfit_tpo_list") ?? "[]");
    } catch {
      return [];
    }
  })();
  const budgetMin = typeof window !== "undefined"
    ? Number(localStorage.getItem("colorfit_budget_min") ?? "30000")
    : 30000;
  const budgetMax = typeof window !== "undefined"
    ? Number(localStorage.getItem("colorfit_budget_max") ?? "100000")
    : 100000;

  useEffect(() => {
    fetchToneDetail(toneId)
      .then(setTone)
      .catch(() => setError("톤 정보를 불러올 수 없습니다"))
      .finally(() => setLoading(false));
  }, [toneId]);

  if (loading) return <ProfileSkeleton />;

  if (error || !tone) {
    return (
      <div className="min-h-screen bg-bg-primary flex flex-col items-center justify-center px-[20px] pb-[80px]">
        <p className="text-text-secondary text-[15px] mb-[16px]" style={{ fontFamily: "var(--font-body)" }}>
          {error ?? "톤 정보를 불러올 수 없습니다"}
        </p>
        <button
          onClick={() => window.location.reload()}
          className="px-[24px] py-[10px] rounded-full text-[14px] font-medium"
          style={{
            fontFamily: "var(--font-body)",
            backgroundColor: "var(--color-accent)",
            color: "#FFFFFF",
          }}
        >
          다시 시도
        </button>
      </div>
    );
  }

  const gradient = TONE_GRADIENTS[toneId] ?? TONE_GRADIENTS.summer_cool_soft;

  function formatBudget(min: number, max: number): string {
    const fmtMin = min >= 10000 ? `${Math.floor(min / 10000)}만` : `${min.toLocaleString("ko-KR")}`;
    const fmtMax = max >= 10000 ? `${Math.floor(max / 10000)}만` : `${max.toLocaleString("ko-KR")}`;
    return `${fmtMin}~${fmtMax}원`;
  }

  return (
    <div className="min-h-screen bg-bg-primary pb-[80px]">
      {/* 톤 카드 히어로 */}
      <motion.button
        onClick={() => router.push(`/tone/${toneId}`)}
        className="w-full text-left"
        initial={shouldReduceMotion ? false : { opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={shouldReduceMotion ? { duration: 0 } : { duration: 0.4 }}
      >
        <div
          className="relative w-full flex flex-col items-center justify-center"
          style={{
            background: gradient,
            height: "180px",
          }}
        >
          <h1
            className="text-[28px] text-white leading-[1.25]"
            style={{ fontFamily: "var(--font-display)", fontWeight: 700 }}
          >
            {tone.tone_name_ko}
          </h1>
          <p
            className="text-[13px] text-white/80 mt-[8px]"
            style={{ fontFamily: "var(--font-body)" }}
          >
            {tone.description.slice(0, 30)}...
          </p>
          <div
            className="absolute bottom-[12px] right-[16px] text-[12px] text-white/60"
            style={{ fontFamily: "var(--font-body)" }}
          >
            탭하여 상세 보기
          </div>
        </div>
      </motion.button>

      {/* 대표색 스와치 */}
      <motion.div
        className="px-[20px] pt-[24px]"
        initial={shouldReduceMotion ? false : { opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={shouldReduceMotion ? { duration: 0 } : { duration: 0.3, delay: 0.1 }}
      >
        <h2
          className="text-[16px] font-semibold text-text-primary mb-[12px]"
          style={{ fontFamily: "var(--font-body)" }}
        >
          잘 어울리는 색
        </h2>
        <div className="flex gap-[12px] overflow-x-auto pb-[4px]">
          {tone.best_colors.map((c) => (
            <ColorSwatch key={c.hex} hex={c.hex} name={c.name_ko} />
          ))}
        </div>

        <h2
          className="text-[16px] font-semibold text-text-primary mt-[24px] mb-[12px]"
          style={{ fontFamily: "var(--font-body)" }}
        >
          피해야 할 색
        </h2>
        <div className="flex gap-[12px] overflow-x-auto pb-[4px]">
          {tone.worst_colors.map((c) => (
            <div key={c.hex} className="flex flex-col items-center gap-[4px]">
              <div className="relative">
                <div
                  className="w-[40px] h-[40px] rounded-full border border-border"
                  style={{ backgroundColor: c.hex }}
                />
                <div className="absolute inset-0 flex items-center justify-center">
                  <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                    <line x1="4" y1="4" x2="16" y2="16" stroke="white" strokeWidth="2.5" strokeLinecap="round" />
                    <line x1="16" y1="4" x2="4" y2="16" stroke="white" strokeWidth="2.5" strokeLinecap="round" />
                  </svg>
                </div>
              </div>
              <span
                className="text-[11px] leading-[1.4] text-text-tertiary text-center"
                style={{ fontFamily: "var(--font-body)", maxWidth: "48px" }}
              >
                {c.name_ko}
              </span>
            </div>
          ))}
        </div>
      </motion.div>

      {/* 내 정보 */}
      <motion.div
        className="px-[20px] mt-[32px]"
        initial={shouldReduceMotion ? false : { opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={shouldReduceMotion ? { duration: 0 } : { duration: 0.3, delay: 0.2 }}
      >
        <h2
          className="text-[18px] text-text-primary mb-[16px]"
          style={{ fontFamily: "var(--font-display)", fontWeight: 700, lineHeight: 1.3 }}
        >
          내 정보
        </h2>

        <div className="space-y-[2px]">
          {/* 성별 */}
          <div
            className="flex items-center justify-between py-[14px] border-b"
            style={{ borderColor: "var(--color-border)" }}
          >
            <span className="text-[15px] text-text-primary" style={{ fontFamily: "var(--font-body)" }}>
              성별
            </span>
            <span className="text-[14px] text-text-secondary" style={{ fontFamily: "var(--font-body)" }}>
              {gender === "male" ? "남성" : "여성"}
            </span>
          </div>

          {/* TPO */}
          <div
            className="flex items-center justify-between py-[14px] border-b"
            style={{ borderColor: "var(--color-border)" }}
          >
            <span className="text-[15px] text-text-primary" style={{ fontFamily: "var(--font-body)" }}>
              선택 TPO
            </span>
            <span className="text-[14px] text-text-secondary" style={{ fontFamily: "var(--font-body)" }}>
              {tpoList.length > 0 ? tpoList.map((t) => TPO_LABELS[t] ?? t).join(", ") : "미설정"}
            </span>
          </div>

          {/* 예산 */}
          <div
            className="flex items-center justify-between py-[14px] border-b"
            style={{ borderColor: "var(--color-border)" }}
          >
            <span className="text-[15px] text-text-primary" style={{ fontFamily: "var(--font-body)" }}>
              예산 범위
            </span>
            <span className="text-[14px] text-text-secondary" style={{ fontFamily: "var(--font-body)" }}>
              {formatBudget(budgetMin, budgetMax)}
            </span>
          </div>
        </div>
      </motion.div>

      {/* 취향 관리 */}
      <motion.div
        className="px-[20px] mt-[32px]"
        initial={shouldReduceMotion ? false : { opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={shouldReduceMotion ? { duration: 0 } : { duration: 0.3, delay: 0.3 }}
      >
        <button
          onClick={() => router.push("/tryon-gallery")}
          className="flex items-center justify-between w-full py-[14px] border-b"
          style={{ borderColor: "var(--color-border)" }}
        >
          <span className="text-[15px] text-text-primary" style={{ fontFamily: "var(--font-body)" }}>
            AI 착장 갤러리
          </span>
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <path d="M6 3l5 5-5 5" stroke="var(--color-text-tertiary)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </button>
        <button
          onClick={() => router.push("/preference")}
          className="flex items-center justify-between w-full py-[14px] border-b"
          style={{ borderColor: "var(--color-border)" }}
        >
          <span className="text-[15px] text-text-primary" style={{ fontFamily: "var(--font-body)" }}>
            취향 관리
          </span>
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <path d="M6 3l5 5-5 5" stroke="var(--color-text-tertiary)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </button>
        <button
          onClick={() => router.push("/brands")}
          className="flex items-center justify-between w-full py-[14px] border-b"
          style={{ borderColor: "var(--color-border)" }}
        >
          <span className="text-[15px] text-text-primary" style={{ fontFamily: "var(--font-body)" }}>
            선호 브랜드
          </span>
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <path d="M6 3l5 5-5 5" stroke="var(--color-text-tertiary)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </button>
      </motion.div>

      {/* 설정 */}
      <motion.div
        className="px-[20px] mt-[32px]"
        initial={shouldReduceMotion ? false : { opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={shouldReduceMotion ? { duration: 0 } : { duration: 0.3, delay: 0.4 }}
      >
        <h2
          className="text-[18px] text-text-primary mb-[16px]"
          style={{ fontFamily: "var(--font-display)", fontWeight: 700, lineHeight: 1.3 }}
        >
          설정
        </h2>

        <div className="space-y-[2px]">
          <button
            type="button"
            onClick={handleLogout}
            className="flex items-center justify-between w-full py-[14px] border-b"
            style={{ borderColor: "var(--color-border)" }}
          >
            <span className="text-[15px] text-text-primary" style={{ fontFamily: "var(--font-body)" }}>
              로그아웃
            </span>
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path d="M6 3l5 5-5 5" stroke="var(--color-text-tertiary)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </button>
          <button
            type="button"
            onClick={() => setShowDeleteDialog(true)}
            className="flex items-center justify-between w-full py-[14px] border-b"
            style={{ borderColor: "var(--color-border)" }}
          >
            <span className="text-[15px]" style={{ fontFamily: "var(--font-body)", color: "var(--color-accent)" }}>
              계정 삭제
            </span>
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path d="M6 3l5 5-5 5" stroke="var(--color-text-tertiary)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </button>
        </div>
      </motion.div>

      {/* 계정 삭제 확인 다이얼로그 */}
      <AnimatePresence>
        {showDeleteDialog && (
          <>
            <motion.div
              className="fixed inset-0 bg-black/40 z-40"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => !deleting && setShowDeleteDialog(false)}
            />
            <motion.div
              role="dialog"
              aria-modal="true"
              aria-labelledby="delete-dialog-title"
              className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 z-50 w-[320px] bg-bg-primary rounded-[var(--radius-lg)] p-[20px] shadow-lg"
              initial={shouldReduceMotion ? false : { opacity: 0, scale: 0.96 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.96 }}
              transition={shouldReduceMotion ? { duration: 0 } : { duration: 0.2 }}
            >
              <h3
                id="delete-dialog-title"
                className="text-[17px] text-text-primary mb-[8px]"
                style={{ fontFamily: "var(--font-display)", fontWeight: 700 }}
              >
                계정을 삭제할까요?
              </h3>
              <p
                className="text-[13px] text-text-secondary leading-[1.5] mb-[20px]"
                style={{ fontFamily: "var(--font-body)" }}
              >
                저장한 옷장, 코디, 취향 데이터가 모두 삭제되며 복구할 수 없어요.
              </p>
              {deleteError && (
                <p
                  className="text-[13px] mb-[12px]"
                  style={{ fontFamily: "var(--font-body)", color: "var(--color-accent)" }}
                >
                  {deleteError}
                </p>
              )}
              <div className="flex gap-[8px]">
                <button
                  type="button"
                  onClick={() => setShowDeleteDialog(false)}
                  disabled={deleting}
                  className="flex-1 py-[12px] rounded-full text-[14px] font-medium border disabled:opacity-60"
                  style={{
                    fontFamily: "var(--font-body)",
                    borderColor: "var(--color-border)",
                    color: "var(--color-text-primary)",
                  }}
                >
                  취소
                </button>
                <button
                  type="button"
                  onClick={handleDeleteAccount}
                  disabled={deleting}
                  className="flex-1 py-[12px] rounded-full text-[14px] font-medium text-white disabled:opacity-60"
                  style={{
                    fontFamily: "var(--font-body)",
                    backgroundColor: "var(--color-accent)",
                  }}
                >
                  {deleting ? "삭제 중..." : "삭제"}
                </button>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  );
}
