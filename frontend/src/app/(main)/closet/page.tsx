"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";
import { motion, useReducedMotion } from "framer-motion";
import { fetchCloset, type ClosetItemData, type ClosetStats } from "@/lib/api";

type PageState = "loading" | "empty" | "success" | "error";

const MOCK_USER_ID = "00000000-0000-0000-0000-000000000001";
const FREE_ANALYSIS_LIMIT = 5;

/* -- Score badge color -- */
function scoreBadgeStyle(score: number | null): { bg: string; text: string } {
  if (score == null) return { bg: "var(--color-bg-secondary)", text: "var(--color-text-tertiary)" };
  if (score >= 70) return { bg: "var(--color-accent)", text: "#FFFFFF" };
  if (score >= 50) return { bg: "var(--color-score-of)", text: "#1A1714" };
  return { bg: "var(--color-bg-secondary)", text: "var(--color-text-secondary)" };
}

/* -- Category label -- */
const CATEGORY_LABEL: Record<string, string> = {
  top: "\uC0C1\uC758",
  bottom: "\uD558\uC758",
  outer: "\uC544\uC6B0\uD130",
  dress: "\uC6D0\uD53C\uC2A4",
  shoes: "\uC2E0\uBC1C",
  bag: "\uAC00\uBC29",
  accessory: "\uC561\uC138\uC11C\uB9AC",
};

/* -- Category stats -- */
function buildCategoryDiagnosis(items: ClosetItemData[]): string {
  const catMap: Record<string, { good: number; total: number }> = {};
  for (const item of items) {
    const cat = item.category ?? "etc";
    if (!catMap[cat]) catMap[cat] = { good: 0, total: 0 };
    catMap[cat].total += 1;
    if (item.pcf_score != null && item.pcf_score >= 70) catMap[cat].good += 1;
  }

  const entries = Object.entries(catMap).sort((a, b) => b[1].total - a[1].total);
  const parts: string[] = [];

  for (const [cat, { good, total }] of entries.slice(0, 2)) {
    const label = CATEGORY_LABEL[cat] ?? cat;
    const ratio = total > 0 ? good / total : 0;
    if (ratio >= 0.7) {
      parts.push(`${label} ${total}\uBC8C\uC740 \uD6CC\uB96D\uD558\uACE0`);
    } else if (ratio >= 0.4) {
      parts.push(`${label} ${total}\uBC8C\uC740 \uAD1C\uCC2E\uACE0`);
    } else {
      parts.push(`${label} ${total}\uBC8C\uC740 \uD1A4\uC774 \uB9DE\uC9C0 \uC54A\uC544\uC694`);
    }
  }

  if (parts.length === 0) return "";
  if (parts.length === 1) return parts[0];
  const last = parts.pop()!;
  return `${parts.join(", ")} ${last}`;
}

/* -- Circular progress gauge -- */
function CircularGauge({ percentage }: { percentage: number }) {
  const prefersReducedMotion = useReducedMotion();
  const radius = 54;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (percentage / 100) * circumference;

  return (
    <div className="relative w-[140px] h-[140px] flex items-center justify-center">
      <svg width="140" height="140" viewBox="0 0 140 140">
        <circle
          cx="70"
          cy="70"
          r={radius}
          fill="none"
          stroke="var(--color-border)"
          strokeWidth="8"
        />
        <motion.circle
          cx="70"
          cy="70"
          r={radius}
          fill="none"
          stroke="var(--color-accent)"
          strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={circumference}
          initial={prefersReducedMotion ? { strokeDashoffset: offset } : { strokeDashoffset: circumference }}
          animate={{ strokeDashoffset: offset }}
          transition={
            prefersReducedMotion
              ? { duration: 0 }
              : { type: "spring", stiffness: 60, damping: 20, delay: 0.2 }
          }
          transform="rotate(-90 70 70)"
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span
          className="font-display text-[36px] leading-[1.15] font-bold"
          style={{ color: "var(--color-accent)" }}
        >
          {Math.round(percentage)}
        </span>
        <span className="font-body text-[11px] text-text-tertiary">
          / 100
        </span>
      </div>
    </div>
  );
}

/* -- Closet item card -- */
function ClosetItemCard({
  item,
  index,
  onClick,
  onOutfit,
}: {
  item: ClosetItemData;
  index: number;
  onClick: () => void;
  onOutfit: () => void;
}) {
  const prefersReducedMotion = useReducedMotion();
  const badge = scoreBadgeStyle(item.overall_score);

  return (
    <motion.div
      className="w-full"
      initial={prefersReducedMotion ? false : { y: 30, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={
        prefersReducedMotion
          ? { duration: 0 }
          : { type: "spring", stiffness: 300, damping: 30, delay: index * 0.05 }
      }
    >
      <button
        type="button"
        onClick={onClick}
        className="w-full text-left"
        aria-label={`${CATEGORY_LABEL[item.category ?? ""] ?? "\uB0B4 \uC637"} ${item.overall_score != null ? `${Math.round(item.overall_score)}\uC810` : ""}`}
      >
        <div
          className="relative w-full rounded-[var(--radius-md)] overflow-hidden bg-bg-secondary"
          style={{ aspectRatio: "3/4" }}
        >
          {item.image_url ? (
            <Image
              src={item.image_url}
              alt={CATEGORY_LABEL[item.category ?? ""] ?? "\uB0B4 \uC637"}
              fill
              sizes="(max-width: 768px) 33vw, 200px"
              className="object-cover"
              loading="lazy"
            />
          ) : (
            <div className="absolute inset-0 flex items-center justify-center text-text-tertiary text-[11px] font-body">
              No Image
            </div>
          )}
          {item.overall_score != null && (
            <span
              className="absolute top-[6px] right-[6px] text-[11px] font-body font-medium rounded-full px-[8px] py-[2px]"
              style={{ backgroundColor: badge.bg, color: badge.text }}
            >
              {Math.round(item.overall_score)}
            </span>
          )}
        </div>
        {item.category && (
          <p className="font-body text-[11px] text-text-secondary mt-[4px]">
            {CATEGORY_LABEL[item.category] ?? item.category}
          </p>
        )}
      </button>
      <button
        type="button"
        onClick={onOutfit}
        aria-label={`${CATEGORY_LABEL[item.category ?? ""] ?? "\uB0B4 \uC637"} 코디 완성하기`}
        className="w-full mt-[8px] min-h-[44px] py-[8px] text-[12px] font-body font-medium text-accent border border-accent rounded-[var(--radius-full)] hover:bg-accent/5 transition-colors"
      >
        코디 완성하기
      </button>
    </motion.div>
  );
}

/* -- Main Page -- */
export default function ClosetPage() {
  const router = useRouter();
  const prefersReducedMotion = useReducedMotion();

  const [state, setState] = useState<PageState>("loading");
  const [items, setItems] = useState<ClosetItemData[]>([]);
  const [stats, setStats] = useState<ClosetStats | null>(null);
  const [errorMessage, setErrorMessage] = useState("");

  const freeRemaining = Math.max(0, FREE_ANALYSIS_LIMIT - (items.length));

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const data = await fetchCloset(MOCK_USER_ID);
        if (cancelled) return;
        setItems(data.items);
        setStats(data.stats);
        setState(data.items.length === 0 ? "empty" : "success");
      } catch (err) {
        if (!cancelled) {
          setState("error");
          setErrorMessage(
            err instanceof Error ? err.message : "\uC637\uC7A5\uC744 \uBD88\uB7EC\uC624\uB294 \uC911 \uC624\uB958\uAC00 \uBC1C\uC0DD\uD588\uC2B5\uB2C8\uB2E4.",
          );
        }
      }
    }

    load();
    return () => { cancelled = true; };
  }, []);

  const handleAdd = useCallback(() => {
    router.push("/closet/upload");
  }, [router]);

  const handleItemClick = useCallback(
    (item: ClosetItemData) => {
      const params = new URLSearchParams({
        image_url: item.image_url,
        user_tone_id: item.matched_tone_id ?? "",
        category: item.category ?? "top",
      });
      router.push(`/closet/analyze?${params.toString()}`);
    },
    [router],
  );

  const handleOutfitClick = useCallback(
    (item: ClosetItemData) => {
      router.push(`/closet/outfits?item_id=${item.id}`);
    },
    [router],
  );

  const handleRetry = useCallback(() => {
    setState("loading");
    setErrorMessage("");
    window.location.reload();
  }, []);

  /* -- Loading -- */
  if (state === "loading") {
    return (
      <div className="min-h-screen bg-bg-primary px-[20px] pt-[60px] pb-[100px]">
        <div className="flex justify-center mb-[24px]">
          <div className="w-[140px] h-[140px] rounded-full bg-bg-secondary animate-pulse" />
        </div>
        <div className="h-[16px] w-3/4 mx-auto rounded bg-bg-secondary animate-pulse mb-[32px]" />
        <div className="grid grid-cols-3 gap-[10px]">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div
              key={i}
              className="rounded-[var(--radius-md)] bg-bg-secondary animate-pulse"
              style={{ aspectRatio: "3/4" }}
            />
          ))}
        </div>
      </div>
    );
  }

  /* -- Error -- */
  if (state === "error") {
    return (
      <div className="min-h-screen bg-bg-primary flex flex-col items-center justify-center px-[20px]">
        <div className="w-[64px] h-[64px] rounded-full bg-error-bg flex items-center justify-center mb-[16px]">
          <span className="text-[28px]">{"\uD83D\uDE1E"}</span>
        </div>
        <p className="font-display text-[18px] text-text-primary mb-[8px]">
          옷장을 불러올 수 없어요
        </p>
        <p className="font-body text-[14px] text-text-secondary text-center mb-[24px]">
          {errorMessage}
        </p>
        <button
          type="button"
          onClick={handleRetry}
          className="px-[24px] py-[12px] bg-accent text-white font-body text-[15px] font-medium rounded-[var(--radius-full)]"
        >
          다시 시도하기
        </button>
      </div>
    );
  }

  /* -- Empty -- */
  if (state === "empty") {
    return (
      <div className="min-h-screen bg-bg-primary flex flex-col items-center justify-center px-[20px] pb-[80px]">
        <div className="w-[80px] h-[80px] rounded-full bg-bg-secondary flex items-center justify-center mb-[16px]">
          <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="var(--color-text-tertiary)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
            <path d="M9.5 2H14.5L17 7H7L9.5 2Z" />
            <path d="M3 7H21V20C21 20.5523 20.5523 21 20 21H4C3.44772 21 3 20.5523 3 20V7Z" />
            <path d="M8 11V13" />
            <path d="M16 11V13" />
          </svg>
        </div>
        <p className="font-display text-[18px] text-text-primary mb-[8px]">
          아직 분석한 옷이 없어요
        </p>
        <p className="font-body text-[14px] text-text-secondary text-center mb-[24px]">
          옷 사진을 찍으면 퍼스널컬러에{"\n"}얼마나 어울리는지 알려드려요
        </p>
        <button
          type="button"
          onClick={handleAdd}
          className="px-[24px] py-[14px] bg-accent text-white font-body text-[15px] font-medium rounded-[var(--radius-full)]"
        >
          첫 번째 옷 분석하기
        </button>
      </div>
    );
  }

  /* -- Success -- */
  const diagnosis = buildCategoryDiagnosis(items);

  return (
    <div className="min-h-screen bg-bg-primary pb-[100px]">
      {/* Header */}
      <div className="px-[20px] pt-[56px]">
        <h1 className="font-display text-[24px] text-text-primary leading-[1.25]">
          내 옷장
        </h1>
      </div>

      {/* Gauge + Diagnosis */}
      {stats && (
        <motion.div
          className="flex flex-col items-center mt-[24px] px-[20px]"
          initial={prefersReducedMotion ? false : { y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={prefersReducedMotion ? { duration: 0 } : { type: "spring", stiffness: 300, damping: 30 }}
        >
          <CircularGauge percentage={stats.average_pcf} />

          <p className="font-body text-[14px] text-text-secondary text-center mt-[16px] leading-[1.6]">
            {stats.total_count}벌 중 {stats.good_count}벌이 잘 어울려요
          </p>

          {diagnosis && (
            <p className="font-body text-[13px] text-text-tertiary text-center mt-[4px] leading-[1.5]">
              {diagnosis}
            </p>
          )}
        </motion.div>
      )}

      {/* Free analysis remaining + Premium */}
      <div className="flex items-center justify-between px-[20px] mt-[24px]">
        <span className="font-body text-[13px] text-text-secondary">
          무료 분석 {freeRemaining}회 남음
        </span>
        <button
          type="button"
          className="font-body text-[13px] font-medium px-[12px] py-[6px] rounded-[var(--radius-full)] border border-accent text-accent"
        >
          프리미엄
        </button>
      </div>

      {/* Grid */}
      <div className="px-[20px] mt-[20px]">
        <div className="grid grid-cols-3 gap-[10px]">
          {items.map((item, idx) => (
            <ClosetItemCard
              key={item.id}
              item={item}
              index={idx}
              onClick={() => handleItemClick(item)}
              onOutfit={() => handleOutfitClick(item)}
            />
          ))}
        </div>
      </div>

      {/* FAB: Add button */}
      <button
        type="button"
        onClick={handleAdd}
        className="fixed bottom-[80px] right-[20px] w-[56px] h-[56px] rounded-full bg-accent text-white flex items-center justify-center shadow-lg z-40"
        aria-label="옷 추가"
        style={{ boxShadow: "0 4px 12px rgba(150, 79, 76, 0.3)" }}
      >
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
          <path d="M12 5v14M5 12h14" />
        </svg>
      </button>
    </div>
  );
}
