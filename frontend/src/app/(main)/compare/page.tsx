"use client";

import { Suspense, useState, useEffect, useCallback } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import Image from "next/image";
import { motion, useReducedMotion } from "framer-motion";
import {
  fetchCompare,
  type CompareResponse,
  type AxisComparison,
} from "@/lib/api";

const COLOR_A = "#964F4C"; // Marsala
const COLOR_B = "#4F97A3"; // Ocean Blue

function formatPrice(price: number): string {
  if (price >= 10000) {
    const man = Math.floor(price / 10000);
    const remainder = price % 10000;
    if (remainder === 0) return `${man}만`;
    return `${man}만${remainder.toLocaleString("ko-KR")}`;
  }
  return price.toLocaleString("ko-KR");
}

/* ── 비교 바 컴포넌트 ── */
interface CompareBarProps {
  axis: AxisComparison;
  index: number;
}

function CompareBar({ axis, index }: CompareBarProps) {
  const prefersReducedMotion = useReducedMotion();
  const pctA = Math.min(Math.max(axis.score_a, 0), 100);
  const pctB = Math.min(Math.max(axis.score_b, 0), 100);

  return (
    <div className="mb-[16px]">
      {/* 축 이름 */}
      <div className="flex items-center justify-between mb-[6px]">
        <span
          className="text-[13px] font-medium"
          style={{ color: "var(--color-text-primary)", fontFamily: "var(--font-body)" }}
        >
          {axis.axis_name}
        </span>
        {axis.winner !== "tie" && (
          <span
            className="text-[11px] px-[6px] py-[1px] rounded-full font-medium"
            style={{
              backgroundColor: axis.winner === "A" ? COLOR_A : COLOR_B,
              color: "#FFFFFF",
            }}
          >
            {axis.winner}
          </span>
        )}
      </div>

      {/* A 바 */}
      <div className="flex items-center gap-[8px] mb-[4px]">
        <span
          className="w-[16px] text-[11px] font-medium text-center"
          style={{ color: COLOR_A, fontFamily: "var(--font-body)" }}
        >
          A
        </span>
        <div
          className="flex-1 h-[6px] rounded-full overflow-hidden"
          style={{ backgroundColor: "var(--color-border, #E5E1DA)" }}
        >
          <motion.div
            className="h-full rounded-full"
            style={{ backgroundColor: COLOR_A }}
            initial={prefersReducedMotion ? { width: `${pctA}%` } : { width: 0 }}
            animate={{ width: `${pctA}%` }}
            transition={
              prefersReducedMotion
                ? { duration: 0 }
                : { duration: 0.8, delay: index * 0.15, ease: "easeOut" }
            }
          />
        </div>
        <span
          className="w-[28px] text-right text-[12px] font-medium"
          style={{ color: "var(--color-text-primary)", fontFamily: "var(--font-body)" }}
        >
          {Math.round(axis.score_a)}
        </span>
      </div>

      {/* B 바 */}
      <div className="flex items-center gap-[8px]">
        <span
          className="w-[16px] text-[11px] font-medium text-center"
          style={{ color: COLOR_B, fontFamily: "var(--font-body)" }}
        >
          B
        </span>
        <div
          className="flex-1 h-[6px] rounded-full overflow-hidden"
          style={{ backgroundColor: "var(--color-border, #E5E1DA)" }}
        >
          <motion.div
            className="h-full rounded-full"
            style={{ backgroundColor: COLOR_B }}
            initial={prefersReducedMotion ? { width: `${pctB}%` } : { width: 0 }}
            animate={{ width: `${pctB}%` }}
            transition={
              prefersReducedMotion
                ? { duration: 0 }
                : { duration: 0.8, delay: index * 0.15 + 0.05, ease: "easeOut" }
            }
          />
        </div>
        <span
          className="w-[28px] text-right text-[12px] font-medium"
          style={{ color: "var(--color-text-primary)", fontFamily: "var(--font-body)" }}
        >
          {Math.round(axis.score_b)}
        </span>
      </div>
    </div>
  );
}

/* ── 스켈레톤 ── */
function CompareSkeleton() {
  return (
    <div className="min-h-screen" style={{ backgroundColor: "var(--color-bg-primary)" }}>
      <div className="px-[20px] pt-[16px]">
        <div className="h-[24px] w-[120px] rounded bg-[#E0DCD7] animate-pulse" />
      </div>
      <div className="flex gap-[12px] px-[20px] mt-[24px]">
        <div className="flex-1">
          <div className="w-full rounded-[var(--radius-lg)] bg-[#E0DCD7] animate-pulse" style={{ aspectRatio: "1/1" }} />
          <div className="mt-[8px] h-[14px] w-2/3 rounded bg-[#E0DCD7] animate-pulse" />
        </div>
        <div className="flex-1">
          <div className="w-full rounded-[var(--radius-lg)] bg-[#E0DCD7] animate-pulse" style={{ aspectRatio: "1/1" }} />
          <div className="mt-[8px] h-[14px] w-2/3 rounded bg-[#E0DCD7] animate-pulse" />
        </div>
      </div>
      <div className="px-[20px] mt-[28px] space-y-[16px]">
        {[...Array(5)].map((_, i) => (
          <div key={i} className="h-[32px] rounded bg-[#E0DCD7] animate-pulse" />
        ))}
      </div>
    </div>
  );
}

/* ── 메인 ── */
export default function ComparePage() {
  return (
    <Suspense fallback={<CompareSkeleton />}>
      <CompareContent />
    </Suspense>
  );
}

function CompareContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const prefersReducedMotion = useReducedMotion();

  const idA = searchParams.get("a") ?? "";
  const idB = searchParams.get("b") ?? "";

  const hasIds = !!(idA && idB);
  const [data, setData] = useState<CompareResponse | null>(null);
  const [status, setStatus] = useState<"loading" | "success" | "error">(
    hasIds ? "loading" : "error",
  );

  useEffect(() => {
    if (!idA || !idB) return;
    let cancelled = false;
    async function load() {
      try {
        const toneId = typeof window !== "undefined"
          ? localStorage.getItem("colorfit_tone") ?? undefined
          : undefined;
        const result = await fetchCompare(idA, idB, toneId);
        if (!cancelled) {
          setData(result);
          setStatus("success");
        }
      } catch {
        if (!cancelled) setStatus("error");
      }
    }
    load();
    return () => { cancelled = true; };
  }, [idA, idB]);

  const handleBack = useCallback(() => {
    if (window.history.length > 1) {
      router.back();
    } else {
      router.push("/feed");
    }
  }, [router]);

  const handleViewOutfit = useCallback((id: string) => {
    router.push(`/outfit/${id}`);
  }, [router]);

  if (status === "loading") return <CompareSkeleton />;

  if (status === "error" || !data) {
    return (
      <div
        className="min-h-screen flex flex-col items-center justify-center px-[20px]"
        style={{ backgroundColor: "var(--color-bg-primary)" }}
      >
        <p
          className="text-[16px] mb-[16px]"
          style={{ color: "var(--color-text-primary)", fontFamily: "var(--font-body)" }}
        >
          비교 결과를 불러오지 못했어요
        </p>
        <button
          type="button"
          onClick={handleBack}
          className="px-[24px] py-[10px] rounded-full text-[14px]"
          style={{
            border: "1px solid var(--color-accent)",
            color: "var(--color-accent)",
            fontFamily: "var(--font-body)",
          }}
        >
          돌아가기
        </button>
      </div>
    );
  }

  const { outfit_a, outfit_b, axis_comparison, total_a, total_b, winner, decisive_factor } = data;

  const winnerLabel =
    winner === "A" ? "A가" :
    winner === "B" ? "B가" : "두 코디가";
  const conclusionText = decisive_factor.explanation
    || (winner === "tie"
      ? "두 코디 모두 잘 어울려요"
      : `${winnerLabel} 더 잘 어울려요`);

  return (
    <div
      className="min-h-screen"
      style={{
        backgroundColor: "var(--color-bg-primary)",
        paddingBottom: "calc(160px + env(safe-area-inset-bottom, 0px))",
      }}
    >
      {/* ── 헤더 ── */}
      <header className="flex items-center justify-between px-[20px] pt-[16px] pb-[8px]">
        <button
          type="button"
          onClick={handleBack}
          className="w-[44px] h-[44px] flex items-center justify-center rounded-full"
          style={{ backgroundColor: "var(--color-bg-secondary)" }}
          aria-label="뒤로가기"
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--color-text-primary)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="15 18 9 12 15 6" />
          </svg>
        </button>
        <span
          className="text-[16px] font-medium"
          style={{ fontFamily: "var(--font-display)", color: "var(--color-text-primary)" }}
        >
          A vs B 비교
        </span>
        <div className="w-[36px]" />
      </header>

      {/* ── 좌우 분할: 코디 이미지 + 정보 ── */}
      <div className="flex gap-[12px] px-[20px] mt-[8px]">
        {/* A */}
        <motion.div
          className="flex-1"
          initial={prefersReducedMotion ? false : { opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={prefersReducedMotion ? { duration: 0 } : { duration: 0.4 }}
        >
          <div
            className="relative w-full overflow-hidden rounded-[var(--radius-lg)]"
            style={{
              aspectRatio: "1/1",
              backgroundColor: "var(--color-bg-secondary)",
              border: winner === "A" ? `2px solid ${COLOR_A}` : "1px solid var(--color-border)",
            }}
          >
            {outfit_a.image_url ? (
              <Image
                src={outfit_a.image_url}
                alt="코디 A"
                fill
                sizes="50vw"
                className="object-cover"
              />
            ) : (
              <div className="absolute inset-0 flex items-center justify-center">
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="var(--color-text-tertiary)" strokeWidth="1.5">
                  <rect x="3" y="3" width="18" height="18" rx="2" />
                  <circle cx="8.5" cy="8.5" r="1.5" />
                  <path d="m21 15-5-5L5 21" />
                </svg>
              </div>
            )}
            {/* A 뱃지 */}
            <div
              className="absolute top-[8px] left-[8px] w-[24px] h-[24px] rounded-full flex items-center justify-center text-[12px] font-bold"
              style={{ backgroundColor: COLOR_A, color: "#FFFFFF" }}
            >
              A
            </div>
            {winner === "A" && (
              <div
                className="absolute top-[8px] right-[8px] px-[8px] py-[2px] rounded-full text-[10px] font-medium"
                style={{ backgroundColor: COLOR_A, color: "#FFFFFF" }}
              >
                WINNER
              </div>
            )}
          </div>
          <div className="mt-[8px]">
            {outfit_a.designed_tpo && (
              <span
                className="text-[11px]"
                style={{ color: "var(--color-text-secondary)", fontFamily: "var(--font-body)" }}
              >
                {outfit_a.designed_tpo}
              </span>
            )}
            {outfit_a.total_price != null && (
              <p
                className="text-[14px] font-medium mt-[2px]"
                style={{ color: "var(--color-text-primary)", fontFamily: "var(--font-body)" }}
              >
                ₩{formatPrice(outfit_a.total_price)}
              </p>
            )}
            <p
              className="text-[13px] font-bold mt-[2px]"
              style={{ color: COLOR_A, fontFamily: "var(--font-body)" }}
            >
              {Math.round(total_a)}점
            </p>
          </div>
        </motion.div>

        {/* VS 구분선 */}
        <div className="flex items-start pt-[60px]">
          <span
            className="text-[12px] font-bold"
            style={{ color: "var(--color-text-tertiary)", fontFamily: "var(--font-body)" }}
          >
            VS
          </span>
        </div>

        {/* B */}
        <motion.div
          className="flex-1"
          initial={prefersReducedMotion ? false : { opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={prefersReducedMotion ? { duration: 0 } : { duration: 0.4 }}
        >
          <div
            className="relative w-full overflow-hidden rounded-[var(--radius-lg)]"
            style={{
              aspectRatio: "1/1",
              backgroundColor: "var(--color-bg-secondary)",
              border: winner === "B" ? `2px solid ${COLOR_B}` : "1px solid var(--color-border)",
            }}
          >
            {outfit_b.image_url ? (
              <Image
                src={outfit_b.image_url}
                alt="코디 B"
                fill
                sizes="50vw"
                className="object-cover"
              />
            ) : (
              <div className="absolute inset-0 flex items-center justify-center">
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="var(--color-text-tertiary)" strokeWidth="1.5">
                  <rect x="3" y="3" width="18" height="18" rx="2" />
                  <circle cx="8.5" cy="8.5" r="1.5" />
                  <path d="m21 15-5-5L5 21" />
                </svg>
              </div>
            )}
            {/* B 뱃지 */}
            <div
              className="absolute top-[8px] left-[8px] w-[24px] h-[24px] rounded-full flex items-center justify-center text-[12px] font-bold"
              style={{ backgroundColor: COLOR_B, color: "#FFFFFF" }}
            >
              B
            </div>
            {winner === "B" && (
              <div
                className="absolute top-[8px] right-[8px] px-[8px] py-[2px] rounded-full text-[10px] font-medium"
                style={{ backgroundColor: COLOR_B, color: "#FFFFFF" }}
              >
                WINNER
              </div>
            )}
          </div>
          <div className="mt-[8px]">
            {outfit_b.designed_tpo && (
              <span
                className="text-[11px]"
                style={{ color: "var(--color-text-secondary)", fontFamily: "var(--font-body)" }}
              >
                {outfit_b.designed_tpo}
              </span>
            )}
            {outfit_b.total_price != null && (
              <p
                className="text-[14px] font-medium mt-[2px]"
                style={{ color: "var(--color-text-primary)", fontFamily: "var(--font-body)" }}
              >
                ₩{formatPrice(outfit_b.total_price)}
              </p>
            )}
            <p
              className="text-[13px] font-bold mt-[2px]"
              style={{ color: COLOR_B, fontFamily: "var(--font-body)" }}
            >
              {Math.round(total_b)}점
            </p>
          </div>
        </motion.div>
      </div>

      {/* ── 5축 비교 차트 ── */}
      <section className="px-[20px] mt-[28px]">
        <h2
          className="text-[16px] font-medium mb-[16px]"
          style={{ fontFamily: "var(--font-display)", color: "var(--color-text-primary)" }}
        >
          스코어 비교
        </h2>
        {axis_comparison.map((axis, i) => (
          <CompareBar key={axis.axis} axis={axis} index={i} />
        ))}
      </section>

      {/* ── 결론 ── */}
      <section className="px-[20px] mt-[8px]">
        <div
          className="rounded-[var(--radius-lg)] p-[20px]"
          style={{ backgroundColor: "var(--color-bg-secondary)" }}
        >
          {decisive_factor.axis_name && (
            <span
              className="text-[12px] mb-[4px] block"
              style={{ color: "var(--color-text-secondary)", fontFamily: "var(--font-body)" }}
            >
              결정적 차이: {decisive_factor.axis_name}
            </span>
          )}
          <p
            className="text-[15px] leading-[1.5] font-medium"
            style={{ color: "var(--color-text-primary)", fontFamily: "var(--font-body)" }}
          >
            {conclusionText}
          </p>
        </div>
      </section>

      {/* ── 하단 CTA (BottomTabBar 위에 고정) ── */}
      <div
        className="fixed left-0 right-0 z-40 border-t"
        style={{
          backgroundColor: "var(--color-bg-primary)",
          borderColor: "var(--color-border)",
          bottom: "calc(56px + env(safe-area-inset-bottom, 0px))",
          paddingBottom: "12px",
          paddingTop: "12px",
        }}
      >
        <div className="flex gap-[12px] px-[20px] py-[12px] max-w-[430px] mx-auto">
          <button
            type="button"
            onClick={() => handleViewOutfit(outfit_a.id)}
            className="flex-1 py-[14px] rounded-[var(--radius-md)] text-[14px] font-medium"
            style={{
              backgroundColor: winner === "A" ? COLOR_A : "var(--color-bg-secondary)",
              color: winner === "A" ? "#FFFFFF" : "var(--color-text-primary)",
              fontFamily: "var(--font-body)",
            }}
          >
            A 코디 보기
          </button>
          <button
            type="button"
            onClick={() => handleViewOutfit(outfit_b.id)}
            className="flex-1 py-[14px] rounded-[var(--radius-md)] text-[14px] font-medium"
            style={{
              backgroundColor: winner === "B" ? COLOR_B : "var(--color-bg-secondary)",
              color: winner === "B" ? "#FFFFFF" : "var(--color-text-primary)",
              fontFamily: "var(--font-body)",
            }}
          >
            B 코디 보기
          </button>
        </div>
      </div>
    </div>
  );
}
