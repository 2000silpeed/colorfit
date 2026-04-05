"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";
import { motion, AnimatePresence, useReducedMotion } from "framer-motion";
import { fetchSaved, postReaction, fetchTopPick, type SavedOutfit, type TopPickResponse } from "@/lib/api";

type PageState = "loading" | "empty" | "success" | "error";
type SortBy = "recent" | "score" | "price";

const FALLBACK_USER_ID = "00000000-0000-0000-0000-000000000001";

const TOP_CATEGORIES = ["티셔츠", "셔츠", "블라우스", "니트", "가디건", "맨투맨", "후드", "원피스"];

function pickHeroImage(items: { category: string | null; image_url: string | null }[], fallback: string | null): string | null {
  const topItem = items.find((it) => it.image_url && TOP_CATEGORIES.includes(it.category ?? ""));
  return topItem?.image_url ?? items.find((it) => it.image_url)?.image_url ?? fallback;
}

const SORT_OPTIONS: { value: SortBy; label: string }[] = [
  { value: "recent", label: "최근 저장" },
  { value: "score", label: "점수순" },
  { value: "price", label: "가격순" },
];

function formatPrice(price: number): string {
  if (price >= 10000) {
    const man = Math.floor(price / 10000);
    const remainder = price % 10000;
    if (remainder === 0) return `${man}만`;
    return `${man}만${remainder.toLocaleString("ko-KR")}`;
  }
  return price.toLocaleString("ko-KR");
}

/* -- 스켈레톤 카드 -- */
function SkeletonCard() {
  return (
    <div>
      <div
        className="w-full rounded-[var(--radius-lg)] bg-[#E0DCD7] animate-pulse"
        style={{ aspectRatio: "3/4" }}
      />
      <div className="mt-[8px] h-[14px] w-3/4 rounded bg-[#E0DCD7] animate-pulse" />
      <div className="mt-[4px] h-[12px] w-1/2 rounded bg-[#E0DCD7] animate-pulse" />
    </div>
  );
}

/* -- 저장 카드 -- */
interface SavedCardProps {
  outfit: SavedOutfit;
  index: number;
  onTap: (id: string) => void;
  onLongPress: (id: string) => void;
  compareMode?: boolean;
  compareSelected?: boolean;
}

function SavedCard({ outfit, index, onTap, onLongPress, compareMode, compareSelected }: SavedCardProps) {
  const prefersReducedMotion = useReducedMotion();
  const longPressTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const isLongPress = useRef(false);

  const handleTouchStart = useCallback(() => {
    isLongPress.current = false;
    longPressTimer.current = setTimeout(() => {
      isLongPress.current = true;
      onLongPress(outfit.id);
    }, 500);
  }, [outfit.id, onLongPress]);

  const handleTouchEnd = useCallback(() => {
    if (longPressTimer.current) {
      clearTimeout(longPressTimer.current);
    }
    if (!isLongPress.current) {
      onTap(outfit.id);
    }
  }, [outfit.id, onTap]);

  const handleTouchMove = useCallback(() => {
    if (longPressTimer.current) {
      clearTimeout(longPressTimer.current);
    }
  }, []);

  const reason = outfit.reasons?.[0] ?? "";
  const tpoLabel = outfit.designed_tpo ?? "";

  return (
    <motion.div
      initial={prefersReducedMotion ? false : { opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.95 }}
      transition={
        prefersReducedMotion
          ? { duration: 0 }
          : { delay: index * 0.05, duration: 0.3 }
      }
      className="cursor-pointer select-none"
      onTouchStart={handleTouchStart}
      onTouchEnd={handleTouchEnd}
      onTouchMove={handleTouchMove}
      onMouseDown={handleTouchStart}
      onMouseUp={handleTouchEnd}
    >
      <div
        className="relative w-full overflow-hidden rounded-[var(--radius-lg)] bg-[var(--color-bg-secondary)]"
        style={{ aspectRatio: "1/1" }}
      >
        {outfit.image_url ? (
          <Image
            src={outfit.image_url}
            alt={`코디 ${outfit.id}`}
            fill
            sizes="(max-width: 430px) 50vw, 200px"
            className="object-contain"
            loading="lazy"
          />
        ) : (
          <div className="absolute inset-0 flex items-center justify-center">
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="var(--color-text-tertiary)" strokeWidth="1.5">
              <rect x="3" y="3" width="18" height="18" rx="2" />
              <circle cx="8.5" cy="8.5" r="1.5" />
              <path d="m21 15-5-5L5 21" />
            </svg>
          </div>
        )}

        {/* 점수 뱃지 */}
        {outfit.scores && (
          <div
            className="absolute top-[8px] right-[8px] px-[6px] py-[2px] rounded-full text-[11px] font-medium"
            style={{
              backgroundColor: outfit.scores.pcf >= 70
                ? "var(--color-accent)"
                : "var(--color-bg-secondary)",
              color: outfit.scores.pcf >= 70 ? "#FFFFFF" : "var(--color-text-secondary)",
            }}
          >
            {Math.round(outfit.scores.pcf)}
          </div>
        )}

        {/* TPO 뱃지 */}
        {tpoLabel && (
          <div
            className="absolute bottom-[8px] left-[8px] px-[6px] py-[2px] rounded-full text-[10px]"
            style={{
              backgroundColor: "rgba(0,0,0,0.5)",
              color: "#FFFFFF",
            }}
          >
            {tpoLabel}
          </div>
        )}

        {/* 비교 모드 선택 표시 */}
        {compareMode && (
          <div
            className="absolute top-[8px] left-[8px] w-[24px] h-[24px] rounded-full flex items-center justify-center text-[12px] font-bold"
            style={{
              backgroundColor: compareSelected ? "var(--color-accent)" : "rgba(255,255,255,0.8)",
              color: compareSelected ? "#FFFFFF" : "var(--color-text-tertiary)",
              border: compareSelected ? "none" : "2px solid var(--color-border)",
            }}
          >
            {compareSelected ? "✓" : ""}
          </div>
        )}
      </div>

      {/* 제목 (1줄 추천 이유) */}
      <p
        className="mt-[8px] text-[13px] leading-[1.4] line-clamp-1"
        style={{ color: "var(--color-text-primary)", fontFamily: "var(--font-body)" }}
      >
        {reason || "저장한 코디"}
      </p>

      {/* 가격 */}
      {outfit.total_price != null && (
        <p
          className="mt-[2px] text-[12px]"
          style={{ color: "var(--color-text-secondary)", fontFamily: "var(--font-body)" }}
        >
          ₩{formatPrice(outfit.total_price)}
        </p>
      )}
    </motion.div>
  );
}

/* -- 삭제 확인 바텀시트 -- */
interface DeleteSheetProps {
  outfitId: string;
  onConfirm: () => void;
  onCancel: () => void;
}

function DeleteBottomSheet({ outfitId, onConfirm, onCancel }: DeleteSheetProps) {
  const prefersReducedMotion = useReducedMotion();

  return (
    <motion.div
      className="fixed inset-0 z-[60] flex items-end justify-center"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
    >
      {/* 백드롭 */}
      <div
        className="absolute inset-0 bg-black/40"
        onClick={onCancel}
      />

      {/* 시트 */}
      <motion.div
        className="relative w-full max-w-[430px] rounded-t-[var(--radius-xl)] px-[20px] pt-[24px] pb-[32px]"
        style={{
          backgroundColor: "var(--color-bg-primary)",
          paddingBottom: "calc(32px + env(safe-area-inset-bottom, 0px))",
        }}
        initial={prefersReducedMotion ? false : { y: "100%" }}
        animate={{ y: 0 }}
        exit={{ y: "100%" }}
        transition={
          prefersReducedMotion
            ? { duration: 0 }
            : { type: "spring", stiffness: 300, damping: 30 }
        }
      >
        <p
          className="text-[16px] font-medium text-center mb-[20px]"
          style={{ color: "var(--color-text-primary)", fontFamily: "var(--font-body)" }}
        >
          이 코디를 저장 목록에서 삭제할까요?
        </p>

        <div className="flex gap-[12px]">
          <button
            onClick={onCancel}
            className="flex-1 py-[14px] rounded-[var(--radius-md)] text-[15px] font-medium"
            style={{
              backgroundColor: "var(--color-bg-secondary)",
              color: "var(--color-text-primary)",
              fontFamily: "var(--font-body)",
            }}
          >
            취소
          </button>
          <button
            onClick={onConfirm}
            className="flex-1 py-[14px] rounded-[var(--radius-md)] text-[15px] font-medium"
            style={{
              backgroundColor: "var(--color-accent)",
              color: "#FFFFFF",
              fontFamily: "var(--font-body)",
            }}
          >
            삭제
          </button>
        </div>
      </motion.div>
    </motion.div>
  );
}

/* -- 5축 바 차트 -- */
const SCORE_AXES: { key: keyof NonNullable<TopPickResponse["scores"]>; label: string; color: string }[] = [
  { key: "pcf", label: "퍼스널컬러", color: "var(--color-score-pcf, #964F4C)" },
  { key: "of", label: "TPO 적합", color: "var(--color-score-of, #4F97A3)" },
  { key: "ch", label: "색상 조화", color: "var(--color-score-ch, #DDB67D)" },
  { key: "pe", label: "가격 효율", color: "var(--color-score-pe, #D1933F)" },
  { key: "sf", label: "스타일 핏", color: "var(--color-score-sf, #6B5876)" },
];

/* -- Top Pick 모달 -- */
interface TopPickModalProps {
  data: TopPickResponse;
  onClose: () => void;
  onViewOutfit: (id: string) => void;
}

function TopPickModal({ data, onClose, onViewOutfit }: TopPickModalProps) {
  const prefersReducedMotion = useReducedMotion();
  const reasons = data.reasons.slice(0, 3);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", handleKeyDown);
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      document.body.style.overflow = "";
    };
  }, [onClose]);

  return (
    <motion.div
      className="fixed inset-0 z-[70] flex flex-col"
      style={{ backgroundColor: "var(--color-bg-primary)" }}
      role="dialog"
      aria-modal="true"
      aria-label="Top Pick 추천"
      initial={prefersReducedMotion ? false : { opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={prefersReducedMotion ? { duration: 0 } : { duration: 0.2 }}
    >
      {/* 상단 바 */}
      <div className="flex items-center justify-between px-[20px] pt-[16px] pb-[8px]">
        <span
          className="text-[13px]"
          style={{ color: "var(--color-text-secondary)", fontFamily: "var(--font-body)" }}
        >
          Top Pick
        </span>
        <button
          onClick={onClose}
          className="w-[44px] h-[44px] flex items-center justify-center rounded-full"
          style={{ backgroundColor: "var(--color-bg-secondary)" }}
          aria-label="닫기"
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--color-text-primary)" strokeWidth="2" strokeLinecap="round">
            <line x1="18" y1="6" x2="6" y2="18" />
            <line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        </button>
      </div>

      {/* 스크롤 영역 */}
      <div className="flex-1 overflow-y-auto px-[20px] pb-[120px]">
        {/* 헤드라인 */}
        <h2
          className="text-[24px] leading-[1.25] mt-[16px] mb-[24px]"
          style={{ fontFamily: "var(--font-display)", fontWeight: 700, color: "var(--color-text-primary)" }}
        >
          이 코디가 가장<br />잘 어울려요
        </h2>

        {/* 코디 이미지 확대 */}
        <div
          className="relative w-full overflow-hidden rounded-[var(--radius-lg)] bg-[var(--color-bg-secondary)]"
          style={{ aspectRatio: "1/1" }}
        >
          {pickHeroImage(data.items, data.image_url) ? (
            <Image
              src={pickHeroImage(data.items, data.image_url)!}
              alt="Top Pick 코디"
              fill
              sizes="(max-width: 430px) 100vw, 430px"
              className="object-contain"
              priority
            />
          ) : (
            <div className="absolute inset-0 flex items-center justify-center">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--color-text-tertiary)" strokeWidth="1.5">
                <rect x="3" y="3" width="18" height="18" rx="2" />
                <circle cx="8.5" cy="8.5" r="1.5" />
                <path d="m21 15-5-5L5 21" />
              </svg>
            </div>
          )}

          {/* TPO 뱃지 */}
          {data.designed_tpo && (
            <div
              className="absolute bottom-[12px] left-[12px] px-[10px] py-[4px] rounded-full text-[12px]"
              style={{ backgroundColor: "rgba(0,0,0,0.5)", color: "#FFFFFF", fontFamily: "var(--font-body)" }}
            >
              {data.designed_tpo}
            </div>
          )}

          {/* 가격 */}
          {data.total_price != null && (
            <div
              className="absolute bottom-[12px] right-[12px] px-[10px] py-[4px] rounded-full text-[12px] font-medium"
              style={{ backgroundColor: "rgba(0,0,0,0.5)", color: "#FFFFFF", fontFamily: "var(--font-body)" }}
            >
              ₩{formatPrice(data.total_price)}
            </div>
          )}
        </div>

        {/* 하이라이트 이유 */}
        {data.highlight_reason && (
          <p
            className="mt-[20px] text-[15px] leading-[1.6] font-medium"
            style={{ color: "var(--color-accent)", fontFamily: "var(--font-body)" }}
          >
            {data.highlight_reason}
          </p>
        )}

        {/* 추천 이유 3줄 */}
        {reasons.length > 0 && (
          <div className="mt-[12px] flex flex-col gap-[8px]">
            {reasons.map((reason, i) => (
              <div key={i} className="flex items-start gap-[8px]">
                <span
                  className="mt-[2px] w-[6px] h-[6px] rounded-full flex-shrink-0"
                  style={{ backgroundColor: "var(--color-accent)" }}
                />
                <p
                  className="text-[14px] leading-[1.5]"
                  style={{ color: "var(--color-text-primary)", fontFamily: "var(--font-body)" }}
                >
                  {reason}
                </p>
              </div>
            ))}
          </div>
        )}

        {/* 5축 바 차트 */}
        {data.scores && (
          <div className="mt-[28px]">
            <h3
              className="text-[14px] font-medium mb-[16px]"
              style={{ color: "var(--color-text-secondary)", fontFamily: "var(--font-body)" }}
            >
              스타일 분석
            </h3>
            <div className="flex flex-col gap-[12px]">
              {SCORE_AXES.map(({ key, label, color }, axisIdx) => {
                const scores = data.scores!;
                const value = scores[key] ?? 0;
                return (
                  <div key={key}>
                    <div className="flex items-center justify-between mb-[4px]">
                      <span
                        className="text-[13px]"
                        style={{ color: "var(--color-text-primary)", fontFamily: "var(--font-body)" }}
                      >
                        {label}
                      </span>
                      <span
                        className="text-[13px] font-medium"
                        style={{ color, fontFamily: "var(--font-body)" }}
                      >
                        {Math.round(value)}
                      </span>
                    </div>
                    <div
                      className="h-[6px] rounded-full overflow-hidden"
                      style={{ backgroundColor: "var(--color-border, #E5E1DA)" }}
                    >
                      <motion.div
                        className="h-full rounded-full"
                        style={{ backgroundColor: color }}
                        initial={prefersReducedMotion ? { width: `${value}%` } : { width: 0 }}
                        animate={{ width: `${value}%` }}
                        transition={
                          prefersReducedMotion
                            ? { duration: 0 }
                            : { duration: 0.8, delay: axisIdx * 0.15, ease: "easeOut" }
                        }
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>

      {/* 하단 CTA */}
      <div
        className="fixed bottom-0 left-0 right-0 px-[20px] pt-[12px]"
        style={{
          backgroundColor: "var(--color-bg-primary)",
          paddingBottom: "calc(16px + env(safe-area-inset-bottom, 0px))",
        }}
      >
        <div className="flex gap-[12px] max-w-[430px] mx-auto">
          <button
            onClick={onClose}
            className="flex-1 py-[14px] rounded-[var(--radius-md)] text-[15px] font-medium"
            style={{
              backgroundColor: "var(--color-bg-secondary)",
              color: "var(--color-text-primary)",
              fontFamily: "var(--font-body)",
            }}
          >
            닫기
          </button>
          <button
            onClick={() => onViewOutfit(data.id)}
            className="flex-1 py-[14px] rounded-[var(--radius-md)] text-[15px] font-medium"
            style={{
              backgroundColor: "var(--color-accent)",
              color: "#FFFFFF",
              fontFamily: "var(--font-body)",
            }}
          >
            코디 상세 보기
          </button>
        </div>
      </div>
    </motion.div>
  );
}

/* ── 메인 페이지 ── */
export default function SavedPage() {
  const router = useRouter();
  const prefersReducedMotion = useReducedMotion();

  const [pageState, setPageState] = useState<PageState>("loading");
  const [outfits, setOutfits] = useState<SavedOutfit[]>([]);
  const [sortBy, setSortBy] = useState<SortBy>("recent");
  const [deleteTarget, setDeleteTarget] = useState<string | null>(null);
  const [topPick, setTopPick] = useState<TopPickResponse | null>(null);
  const [showTopPick, setShowTopPick] = useState(false);
  const [topPickLoading, setTopPickLoading] = useState(false);
  const [topPickError, setTopPickError] = useState(false);
  const [compareMode, setCompareMode] = useState(false);
  const [compareSelected, setCompareSelected] = useState<string[]>([]);

  const getUserId = useCallback(() => {
    if (typeof window === "undefined") return FALLBACK_USER_ID;
    let id = localStorage.getItem("colorfit_user_id");
    if (!id) {
      id = crypto.randomUUID();
      localStorage.setItem("colorfit_user_id", id);
    }
    return id;
  }, []);

  const loadSaved = useCallback(async (sort: SortBy) => {
    try {
      setPageState("loading");
      const data = await fetchSaved(getUserId(), sort);
      setOutfits(data.outfits);
      setPageState(data.outfits.length > 0 ? "success" : "empty");
    } catch {
      setPageState("error");
    }
  }, [getUserId]);

  useEffect(() => {
    loadSaved(sortBy);
  }, [sortBy, loadSaved]);

  const handleTap = useCallback((id: string) => {
    router.push(`/outfit/${id}`);
  }, [router]);

  const handleLongPress = useCallback((id: string) => {
    setDeleteTarget(id);
  }, []);

  const handleDelete = useCallback(async () => {
    if (!deleteTarget) return;
    try {
      await postReaction(getUserId(), deleteTarget, "save"); // toggle off
      // localStorage 동기화
      try {
        const raw = localStorage.getItem("colorfit_saved_ids");
        if (raw) {
          const ids: string[] = JSON.parse(raw);
          localStorage.setItem(
            "colorfit_saved_ids",
            JSON.stringify(ids.filter((id) => id !== deleteTarget)),
          );
        }
      } catch { /* localStorage 파싱 실패 무시 */ }
      setOutfits((prev) => prev.filter((o) => o.id !== deleteTarget));
      if (outfits.length <= 1) {
        setPageState("empty");
      }
    } catch {
      // API 실패 시 무시
    }
    setDeleteTarget(null);
  }, [deleteTarget, outfits.length, getUserId]);

  const handleSortChange = useCallback((newSort: SortBy) => {
    setSortBy(newSort);
  }, []);

  const handleTopPick = useCallback(async () => {
    if (topPickLoading) return;
    setTopPickLoading(true);
    setTopPickError(false);
    try {
      const toneId = typeof window !== "undefined"
        ? localStorage.getItem("colorfit_tone") ?? "summer_cool_mute"
        : "summer_cool_mute";
      const gender = typeof window !== "undefined"
        ? localStorage.getItem("colorfit_gender") ?? undefined
        : undefined;
      const data = await fetchTopPick(toneId, {
        userId: getUserId(),
        gender,
      });
      setTopPick(data);
      setShowTopPick(true);
    } catch {
      setTopPickError(true);
    } finally {
      setTopPickLoading(false);
    }
  }, [topPickLoading, getUserId]);

  const handleToggleCompareMode = useCallback(() => {
    setCompareMode((prev) => {
      if (prev) setCompareSelected([]);
      return !prev;
    });
  }, []);

  const handleCompareToggle = useCallback((id: string) => {
    setCompareSelected((prev) => {
      if (prev.includes(id)) return prev.filter((x) => x !== id);
      if (prev.length >= 2) return prev;
      return [...prev, id];
    });
  }, []);

  const handleCompareGo = useCallback(() => {
    if (compareSelected.length === 2) {
      router.push(`/compare?a=${compareSelected[0]}&b=${compareSelected[1]}`);
    }
  }, [compareSelected, router]);

  const handleTopPickClose = useCallback(() => {
    setShowTopPick(false);
  }, []);

  const handleTopPickViewOutfit = useCallback((id: string) => {
    setShowTopPick(false);
    router.push(`/outfit/${id}`);
  }, [router]);

  return (
    <div
      className="min-h-screen"
      style={{
        backgroundColor: "var(--color-bg-primary)",
        paddingBottom: "calc(80px + env(safe-area-inset-bottom, 0px))",
      }}
    >
      {/* 헤더 */}
      <header
        className="sticky top-0 z-10 px-[20px] pt-[16px] pb-[12px]"
        style={{ backgroundColor: "var(--color-bg-primary)" }}
      >
        <h1
          className="text-[24px] leading-[1.3]"
          style={{ fontFamily: "var(--font-display)", fontWeight: 700, color: "var(--color-text-primary)" }}
        >
          저장한 코디
        </h1>

        {/* 정렬 드롭다운 */}
        {pageState === "success" && (
          <div className="flex gap-[8px] mt-[12px]">
            {SORT_OPTIONS.map((opt) => (
              <button
                key={opt.value}
                onClick={() => handleSortChange(opt.value)}
                className="px-[12px] py-[6px] rounded-full text-[13px] transition-colors"
                style={{
                  backgroundColor: sortBy === opt.value
                    ? "var(--color-accent)"
                    : "var(--color-bg-secondary)",
                  color: sortBy === opt.value
                    ? "#FFFFFF"
                    : "var(--color-text-secondary)",
                  fontFamily: "var(--font-body)",
                  fontWeight: sortBy === opt.value ? 600 : 400,
                }}
              >
                {opt.label}
              </button>
            ))}
          </div>
        )}
      </header>

      {/* Top Pick + 비교 버튼 */}
      {pageState === "success" && (
        <div className="px-[20px] pt-[8px] pb-[4px] flex gap-[8px]">
          <button
            onClick={handleTopPick}
            disabled={topPickLoading}
            className="flex-1 py-[12px] rounded-[var(--radius-md)] text-[14px] font-medium transition-opacity"
            style={{
              backgroundColor: "transparent",
              color: "var(--color-accent)",
              border: "1.5px solid var(--color-accent)",
              fontFamily: "var(--font-body)",
              opacity: topPickLoading ? 0.6 : 1,
            }}
          >
            {topPickLoading ? "분석 중..." : "Top Pick"}
          </button>
          <button
            onClick={handleToggleCompareMode}
            className="flex-1 py-[12px] rounded-[var(--radius-md)] text-[14px] font-medium"
            style={{
              backgroundColor: compareMode ? "var(--color-accent)" : "transparent",
              color: compareMode ? "#FFFFFF" : "var(--color-accent)",
              border: "1.5px solid var(--color-accent)",
              fontFamily: "var(--font-body)",
            }}
          >
            {compareMode ? "비교 취소" : "A vs B 비교"}
          </button>
          {topPickError && (
            <p
              className="mt-[8px] text-[13px] text-center col-span-2"
              style={{ color: "var(--color-accent)", fontFamily: "var(--font-body)" }}
            >
              Top Pick을 불러오지 못했어요. 다시 시도해주세요.
            </p>
          )}
        </div>
      )}

      {/* 로딩 */}
      {pageState === "loading" && (
        <div className="grid grid-cols-2 gap-[12px] px-[20px] pt-[8px]">
          {Array.from({ length: 4 }).map((_, i) => (
            <SkeletonCard key={i} />
          ))}
        </div>
      )}

      {/* 비어있음 */}
      {pageState === "empty" && (
        <div className="flex flex-col items-center justify-center px-[20px] pt-[120px]">
          <div
            className="w-[80px] h-[80px] rounded-full flex items-center justify-center mb-[16px]"
            style={{ backgroundColor: "var(--color-bg-secondary)" }}
          >
            <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="var(--color-text-tertiary)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78L12 21.23l8.84-8.84a5.5 5.5 0 0 0 0-7.78z" />
            </svg>
          </div>
          <p
            className="text-[18px] mb-[8px]"
            style={{ fontFamily: "var(--font-display)", fontWeight: 700, color: "var(--color-text-primary)" }}
          >
            아직 저장한 코디가 없어요
          </p>
          <p
            className="text-[14px] text-center mb-[24px]"
            style={{ color: "var(--color-text-secondary)", fontFamily: "var(--font-body)" }}
          >
            피드에서 마음에 드는 코디를 저장해보세요
          </p>
          <button
            onClick={() => router.push("/feed")}
            className="px-[24px] py-[14px] rounded-[var(--radius-md)] text-[15px] font-medium"
            style={{
              backgroundColor: "var(--color-accent)",
              color: "#FFFFFF",
              fontFamily: "var(--font-body)",
            }}
          >
            코디 피드 둘러보기
          </button>
        </div>
      )}

      {/* 에러 */}
      {pageState === "error" && (
        <div className="flex flex-col items-center justify-center px-[20px] pt-[120px]">
          <p
            className="text-[16px] mb-[12px]"
            style={{ color: "var(--color-text-primary)", fontFamily: "var(--font-body)" }}
          >
            저장 목록을 불러오지 못했어요
          </p>
          <button
            onClick={() => loadSaved(sortBy)}
            className="px-[24px] py-[10px] rounded-full text-[14px]"
            style={{
              backgroundColor: "var(--color-accent)",
              color: "#FFFFFF",
              fontFamily: "var(--font-body)",
            }}
          >
            다시 시도
          </button>
        </div>
      )}

      {/* 비교 모드 안내 */}
      {compareMode && (
        <div className="px-[20px] pt-[8px]">
          <p
            className="text-[13px] text-center"
            style={{ color: "var(--color-text-secondary)", fontFamily: "var(--font-body)" }}
          >
            비교할 코디 2개를 선택하세요 ({compareSelected.length}/2)
          </p>
        </div>
      )}

      {/* 성공: 2열 그리드 */}
      {pageState === "success" && (
        <div className="grid grid-cols-2 gap-[12px] px-[20px] pt-[8px]">
          <AnimatePresence mode="popLayout">
            {outfits.map((outfit, i) => (
              <SavedCard
                key={outfit.id}
                outfit={outfit}
                index={i}
                onTap={compareMode ? handleCompareToggle : handleTap}
                onLongPress={compareMode ? handleCompareToggle : handleLongPress}
                compareMode={compareMode}
                compareSelected={compareSelected.includes(outfit.id)}
              />
            ))}
          </AnimatePresence>
        </div>
      )}

      {/* 비교 모드 CTA */}
      <AnimatePresence>
        {compareMode && compareSelected.length === 2 && (
          <motion.div
            className="fixed bottom-[80px] left-0 right-0 z-20 px-[20px]"
            initial={prefersReducedMotion ? false : { y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            exit={{ y: 20, opacity: 0 }}
            transition={prefersReducedMotion ? { duration: 0 } : { duration: 0.2 }}
          >
            <button
              onClick={handleCompareGo}
              className="w-full max-w-[430px] mx-auto block py-[14px] rounded-[var(--radius-md)] text-[15px] font-medium"
              style={{
                backgroundColor: "var(--color-accent)",
                color: "#FFFFFF",
                fontFamily: "var(--font-body)",
              }}
            >
              비교하기
            </button>
          </motion.div>
        )}
      </AnimatePresence>

      {/* 삭제 확인 바텀시트 */}
      <AnimatePresence>
        {deleteTarget && (
          <DeleteBottomSheet
            outfitId={deleteTarget}
            onConfirm={handleDelete}
            onCancel={() => setDeleteTarget(null)}
          />
        )}
      </AnimatePresence>

      {/* Top Pick 모달 */}
      <AnimatePresence>
        {showTopPick && topPick && (
          <TopPickModal
            data={topPick}
            onClose={handleTopPickClose}
            onViewOutfit={handleTopPickViewOutfit}
          />
        )}
      </AnimatePresence>
    </div>
  );
}
