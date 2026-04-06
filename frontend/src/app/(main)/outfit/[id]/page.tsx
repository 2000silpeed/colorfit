"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import Image from "next/image";
import { motion, AnimatePresence, useScroll, useTransform, useMotionValueEvent, useReducedMotion } from "framer-motion";
import {
  fetchOutfitDetail,
  fetchSaved,
  fetchClosetOutfits,
  postReaction,
  generateTryon,
  fetchTryonUsage,
  TryonLimitError,
  type OutfitDetailResponse,
  type ScoresResponse,
  type SavedOutfit,
  type ClosetOutfit,
} from "@/lib/api";
import PurchaseFeedbackSheet from "@/components/PurchaseFeedbackSheet";
import { isLoggedIn } from "@/lib/auth";

/* ── 스코어 축 설정 ── */
const SCORE_AXES: {
  key: keyof ScoresResponse;
  label: string;
  fullLabel: string;
  color: string;
}[] = [
  { key: "pcf", label: "PCF", fullLabel: "퍼스널컬러", color: "#964F4C" },
  { key: "of", label: "OF", fullLabel: "TPO 적합", color: "#4F97A3" },
  { key: "ch", label: "CH", fullLabel: "색상 조화", color: "#DDB67D" },
  { key: "pe", label: "PE", fullLabel: "가격 효율", color: "#D1933F" },
  { key: "sf", label: "SF", fullLabel: "스타일 핏", color: "#6B5876" },
];

/* ── 가격 포맷 ── */
function formatPrice(price: number): string {
  if (price >= 10000) {
    const man = Math.floor(price / 10000);
    const remainder = price % 10000;
    if (remainder === 0) return `${man}만`;
    return `${man}만${remainder.toLocaleString("ko-KR")}`;
  }
  return price.toLocaleString("ko-KR");
}

/* ── 스코어 바 컴포넌트 ── */
function ScoreBar({
  label,
  fullLabel,
  value,
  color,
  delay,
}: {
  label: string;
  fullLabel: string;
  value: number;
  color: string;
  delay: number;
}) {
  const prefersReducedMotion = useReducedMotion();
  const percentage = Math.min(Math.max(value, 0), 100);

  return (
    <div className="flex items-center gap-[12px]">
      <div className="w-[72px] shrink-0">
        <span className="font-body text-[13px] text-text-secondary">{fullLabel}</span>
        <span className="font-body text-[10px] text-text-tertiary ml-[4px] hidden sm:inline" title={fullLabel}>
          {label}
        </span>
      </div>
      <div className="flex-1 h-[8px] bg-border rounded-full overflow-hidden">
        <motion.div
          className="h-full rounded-full"
          style={{ backgroundColor: color }}
          initial={prefersReducedMotion ? { width: `${percentage}%` } : { width: "0%" }}
          animate={{ width: `${percentage}%` }}
          transition={
            prefersReducedMotion
              ? { duration: 0 }
              : { duration: 0.8, delay, ease: "easeOut" }
          }
        />
      </div>
      <span className="w-[32px] text-right font-body text-[13px] text-text-primary font-medium">
        {Math.round(value)}
      </span>
    </div>
  );
}

/* ── 스켈레톤 ── */
function DetailSkeleton() {
  return (
    <div className="min-h-screen bg-bg-primary">
      <div className="w-full bg-[#E0DCD7] animate-pulse" style={{ aspectRatio: "3/4" }} />
      <div className="px-[20px] pt-[24px]">
        <div className="h-[24px] w-3/4 rounded bg-[#E0DCD7] animate-pulse" />
        <div className="mt-[12px] h-[16px] w-1/2 rounded bg-[#E0DCD7] animate-pulse" />
        <div className="mt-[24px] space-y-[12px]">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="h-[8px] rounded bg-[#E0DCD7] animate-pulse" />
          ))}
        </div>
      </div>
    </div>
  );
}

/* ── 비교 대상 선택 바텀시트 ── */
interface ComparePickerSheetProps {
  currentOutfitId: string;
  onSelect: (id: string) => void;
  onClose: () => void;
}

function ComparePickerSheet({ currentOutfitId, onSelect, onClose }: ComparePickerSheetProps) {
  const prefersReducedMotion = useReducedMotion();
  const [savedOutfits, setSavedOutfits] = useState<SavedOutfit[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const userId = localStorage.getItem("colorfit_user_id") ?? "";
        if (!userId) {
          setLoading(false);
          return;
        }
        const data = await fetchSaved(userId);
        setSavedOutfits(data.outfits.filter((o) => o.id !== currentOutfitId));
      } catch {
        // ignore
      } finally {
        setLoading(false);
      }
    }
    load();
    document.body.style.overflow = "hidden";
    return () => { document.body.style.overflow = ""; };
  }, [currentOutfitId]);

  return (
    <motion.div
      className="fixed inset-0 z-[60] flex items-end justify-center"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
    >
      <div className="absolute inset-0 bg-black/40" onClick={onClose} />
      <motion.div
        className="relative w-full max-w-[430px] rounded-t-[var(--radius-xl)] px-[20px] pt-[20px]"
        style={{
          backgroundColor: "var(--color-bg-primary)",
          paddingBottom: "calc(24px + env(safe-area-inset-bottom, 0px))",
          maxHeight: "70vh",
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
        <div className="flex items-center justify-between mb-[16px]">
          <h3
            className="text-[16px] font-medium"
            style={{ fontFamily: "var(--font-display)", color: "var(--color-text-primary)" }}
          >
            비교할 코디 선택
          </h3>
          <button
            onClick={onClose}
            className="w-[44px] h-[44px] flex items-center justify-center rounded-full"
            style={{ backgroundColor: "var(--color-bg-secondary)" }}
            aria-label="닫기"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--color-text-primary)" strokeWidth="2" strokeLinecap="round">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>

        <div className="overflow-y-auto" style={{ maxHeight: "calc(70vh - 80px)" }}>
          {loading && (
            <div className="flex gap-[12px] overflow-x-auto py-[8px]">
              {[...Array(3)].map((_, i) => (
                <div key={i} className="shrink-0 w-[100px]">
                  <div className="w-[100px] h-[133px] rounded-[var(--radius-md)] bg-[#E0DCD7] animate-pulse" />
                </div>
              ))}
            </div>
          )}

          {!loading && savedOutfits.length === 0 && (
            <p
              className="text-[14px] text-center py-[32px]"
              style={{ color: "var(--color-text-secondary)", fontFamily: "var(--font-body)" }}
            >
              저장한 코디가 없어요.{"\n"}피드에서 코디를 저장해보세요.
            </p>
          )}

          {!loading && savedOutfits.length > 0 && (
            <div className="grid grid-cols-3 gap-[12px]">
              {savedOutfits.map((outfit) => (
                <button
                  key={outfit.id}
                  type="button"
                  onClick={() => onSelect(outfit.id)}
                  className="text-left"
                >
                  <div
                    className="relative w-full overflow-hidden rounded-[var(--radius-md)]"
                    style={{ aspectRatio: "1/1", backgroundColor: "var(--color-bg-secondary)" }}
                  >
                    {outfit.image_url ? (
                      <Image
                        src={outfit.image_url}
                        alt={`코디 ${outfit.id}`}
                        fill
                        sizes="33vw"
                        className="object-contain"
                        loading="lazy"
                      />
                    ) : (
                      <div className="absolute inset-0 flex items-center justify-center">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="var(--color-text-tertiary)" strokeWidth="1.5">
                          <rect x="3" y="3" width="18" height="18" rx="2" />
                        </svg>
                      </div>
                    )}
                  </div>
                  <p
                    className="mt-[4px] text-[11px] line-clamp-1"
                    style={{ color: "var(--color-text-secondary)", fontFamily: "var(--font-body)" }}
                  >
                    {outfit.reasons?.[0] ?? outfit.designed_tpo ?? "코디"}
                  </p>
                </button>
              ))}
            </div>
          )}
        </div>
      </motion.div>
    </motion.div>
  );
}

export default function OutfitDetailPage() {
  const params = useParams();
  const router = useRouter();
  const searchParams = useSearchParams();
  const prefersReducedMotion = useReducedMotion();
  const outfitId = params.id as string;
  const closetItemId = searchParams.get("closet_item_id");

  const [outfit, setOutfit] = useState<OutfitDetailResponse | null>(null);
  const [status, setStatus] = useState<"loading" | "success" | "error">("loading");
  const [loginToast, setLoginToast] = useState(false);
  const [saved, setSaved] = useState(() => {
    if (typeof window === "undefined") return false;
    const savedIds = JSON.parse(localStorage.getItem("colorfit_saved_ids") ?? "[]");
    return (savedIds as string[]).includes(outfitId);
  });

  /* parallax scroll */
  const heroRef = useRef<HTMLDivElement>(null);
  const { scrollY } = useScroll();
  const heroY = useTransform(scrollY, [0, 400], [0, 120]);
  const heroScale = useTransform(scrollY, [0, 400], [1, 1.1]);
  const headerOpacity = useTransform(scrollY, [200, 350], [0, 1]);
  const [headerVisible, setHeaderVisible] = useState(false);
  useMotionValueEvent(headerOpacity, "change", (v) => setHeaderVisible(v > 0.1));

  /* 옷장 매칭 데이터 (closet_item_id 쿼리파라미터 있을 때) */
  const [closetOutfit, setClosetOutfit] = useState<ClosetOutfit | null>(null);

  /* 데이터 로드 */
  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const data = await fetchOutfitDetail(outfitId);
        if (!cancelled) {
          setOutfit(data);
          setStatus("success");
        }
      } catch {
        if (!cancelled) setStatus("error");
      }
    }
    load();
    return () => { cancelled = true; };
  }, [outfitId]);

  /* 옷장 코디 매칭 로드 */
  useEffect(() => {
    if (!closetItemId) return;
    const uid = localStorage.getItem("colorfit_user_id") ?? "";
    if (!uid) return;
    let cancelled = false;
    async function loadClosetOutfit() {
      try {
        const res = await fetchClosetOutfits(uid, closetItemId!);
        if (cancelled) return;
        const match = res.outfits.find(
          (o) => o.db_outfit_id === outfitId || o.id === outfitId,
        );
        if (match) setClosetOutfit(match);
      } catch {
        // 실패 시 일반 모드로 표시
      }
    }
    loadClosetOutfit();
    return () => { cancelled = true; };
  }, [closetItemId, outfitId]);

  /* 카탈로그(구매 필요) 아이템 ID Set */
  const catalogItemIds = closetOutfit
    ? new Set(
        closetOutfit.items
          .filter((i) => i.source === "catalog")
          .map((i) => i.id),
      )
    : null;

  const isClosetMode = closetItemId != null && closetOutfit != null;

  const userId =
    typeof window !== "undefined"
      ? localStorage.getItem("colorfit_user_id") ?? ""
      : "";

  const handleSave = useCallback(() => {
    if (!isLoggedIn()) {
      setLoginToast(true);
      setTimeout(() => {
        sessionStorage.setItem("colorfit_return_url", `/outfit/${outfitId}`);
        router.push(`/login?returnUrl=${encodeURIComponent(`/outfit/${outfitId}`)}`);
      }, 1200);
      return;
    }
    setSaved((prev) => {
      const next = !prev;
      const savedIds: string[] = JSON.parse(
        localStorage.getItem("colorfit_saved_ids") ?? "[]",
      );
      if (next) {
        if (!savedIds.includes(outfitId)) savedIds.push(outfitId);
      } else {
        const idx = savedIds.indexOf(outfitId);
        if (idx !== -1) savedIds.splice(idx, 1);
      }
      localStorage.setItem("colorfit_saved_ids", JSON.stringify(savedIds));
      return next;
    });
    if (userId) {
      postReaction(userId, outfitId, "save").catch(() => {});
    }
  }, [outfitId, userId, router]);

  /* ── 구매 후 피드백 바텀시트 ── */
  const [showPurchaseFeedback, setShowPurchaseFeedback] = useState(false);
  const mallClickedRef = useRef(false);

  const handleMallClick = useCallback(() => {
    mallClickedRef.current = true;
  }, []);

  useEffect(() => {
    function onVisibilityChange() {
      if (document.visibilityState === "visible" && mallClickedRef.current) {
        mallClickedRef.current = false;
        const dismissed = sessionStorage.getItem(`colorfit_fb_dismissed_${outfitId}`);
        if (!dismissed) {
          setShowPurchaseFeedback(true);
        }
      }
    }
    document.addEventListener("visibilitychange", onVisibilityChange);
    return () => document.removeEventListener("visibilitychange", onVisibilityChange);
  }, [outfitId]);

  const handleFeedbackClose = useCallback(() => {
    setShowPurchaseFeedback(false);
    sessionStorage.setItem(`colorfit_fb_dismissed_${outfitId}`, "1");
  }, [outfitId]);

  const [showComparePicker, setShowComparePicker] = useState(false);

  /* Try-On 상태 */
  type TryOnState = "idle" | "loading" | "success" | "error" | "limit";
  const [tryonOpen, setTryonOpen] = useState(false);
  const [tryonState, setTryonState] = useState<TryOnState>("idle");
  const [tryonImageUrl, setTryonImageUrl] = useState("");
  const [tryonRemaining, setTryonRemaining] = useState<number | null>(null);
  const tryonCancelRef = useRef(false);

  useEffect(() => {
    if (!userId) return;
    fetchTryonUsage(userId)
      .then((usage) => setTryonRemaining(usage.remaining))
      .catch(() => {});
  }, [userId]);

  const handleTryOn = useCallback(async () => {
    if (tryonState === "loading") return;
    if (!isLoggedIn()) {
      setLoginToast(true);
      setTimeout(() => {
        sessionStorage.setItem("colorfit_return_url", `/outfit/${outfitId}`);
        router.push(`/login?returnUrl=${encodeURIComponent(`/outfit/${outfitId}`)}`);
      }, 1200);
      return;
    }
    if (!userId) return;
    tryonCancelRef.current = false;
    setTryonOpen(true);
    setTryonState("loading");
    setTryonImageUrl("");
    try {
      const result = await generateTryon(outfitId, userId);
      if (tryonCancelRef.current) return;
      setTryonImageUrl(result.image_url);
      setTryonState("success");
      setTryonRemaining(result.remaining);
    } catch (err) {
      if (tryonCancelRef.current) return;
      if (err instanceof TryonLimitError) {
        setTryonState("limit");
      } else {
        setTryonState("error");
      }
    }
  }, [outfitId, userId, router, tryonState]);

  const handleTryOnClose = useCallback(() => {
    tryonCancelRef.current = true;
    setTryonOpen(false);
    setTryonState("idle");
  }, []);

  const handleTryOnUpgrade = useCallback(() => {
    setTryonOpen(false);
    router.push("/premium");
  }, [router]);

  const handleCompareSelect = useCallback((targetId: string) => {
    setShowComparePicker(false);
    router.push(`/compare?a=${outfitId}&b=${targetId}`);
  }, [outfitId, router]);

  const handleBack = useCallback(() => {
    if (window.history.length > 1) {
      router.back();
    } else {
      router.push("/feed");
    }
  }, [router]);

  if (status === "loading") return <DetailSkeleton />;

  if (status === "error" || !outfit) {
    return (
      <div className="min-h-screen bg-bg-primary flex flex-col items-center justify-center px-[20px]">
        <p className="font-body text-[16px] text-text-primary mb-[16px]">
          코디를 불러오지 못했어요
        </p>
        <button
          type="button"
          onClick={handleBack}
          className="px-[24px] py-[10px] rounded-full border border-accent text-accent text-[14px] font-body"
        >
          돌아가기
        </button>
      </div>
    );
  }

  const GROUP_ORDER: Record<string, number> = {
    top: 0, onepiece: 1, outer: 2, bottom: 3, shoes: 4, bag: 5, acc: 6,
  };
  const CATEGORY_GROUP: Record<string, string> = {
    "티셔츠": "top", "셔츠": "top", "블라우스": "top", "니트": "top",
    "맨투맨": "top", "후드": "top", "탱크탑": "top", "크롭탑": "top", "폴로": "top",
    "원피스": "onepiece", "점프수트": "onepiece",
    "자켓": "outer", "코트": "outer", "패딩": "outer", "가디건": "outer",
    "점퍼": "outer", "조끼": "outer",
    "슬랙스": "bottom", "청바지": "bottom", "스커트": "bottom", "와이드팬츠": "bottom",
    "조거팬츠": "bottom", "숏팬츠": "bottom", "레깅스": "bottom", "치노": "bottom",
    "스니커즈": "shoes", "로퍼": "shoes", "힐": "shoes", "부츠": "shoes",
    "샌들": "shoes", "더비": "shoes",
    "가방": "bag", "액세서리": "acc",
  };
  const sortedItems = [...outfit.items].sort((a, b) => {
    const ga = GROUP_ORDER[CATEGORY_GROUP[a.category ?? ""] ?? ""] ?? 99;
    const gb = GROUP_ORDER[CATEGORY_GROUP[b.category ?? ""] ?? ""] ?? 99;
    return ga - gb;
  });
  const heroImage = sortedItems[0]?.image_url ?? "/placeholder-outfit.png";
  const hasSavings =
    outfit.lowest_total_price != null &&
    outfit.total_price != null &&
    outfit.lowest_total_price < outfit.total_price;

  return (
    <div className="min-h-screen bg-bg-primary">
      {/* ── Sticky 헤더 (스크롤 시 노출) ── */}
      <motion.header
        className="fixed top-0 left-0 right-0 z-40 bg-bg-primary/95 backdrop-blur-sm border-b border-border"
        style={{
          opacity: prefersReducedMotion ? 1 : headerOpacity,
          pointerEvents: headerVisible ? "auto" : "none",
        }}
      >
        <div className="flex items-center justify-between px-[20px] h-[52px] max-w-[768px] mx-auto">
          <button type="button" onClick={handleBack} aria-label="뒤로가기">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="var(--color-text-primary)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="15 18 9 12 15 6" />
            </svg>
          </button>
          <span className="font-display text-[16px] text-text-primary line-clamp-1 max-w-[200px]">
            {outfit.reasons?.[0] ?? "코디 상세"}
          </span>
          <button type="button" onClick={handleSave} aria-label={saved ? "저장 취소" : "저장"}>
            <svg width="24" height="24" viewBox="0 0 24 24" fill={saved ? "var(--color-accent)" : "none"} stroke={saved ? "var(--color-accent)" : "var(--color-text-primary)"} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
            </svg>
          </button>
        </div>
      </motion.header>

      {/* ── 히어로 이미지 (풀블리드 + Parallax) ── */}
      <div ref={heroRef} className="relative w-full overflow-hidden bg-[#F0EDE8]" style={{ aspectRatio: "1/1" }}>
        {/* 뒤로가기 버튼 (히어로 위) */}
        <button
          type="button"
          onClick={handleBack}
          className="absolute top-[8px] left-[8px] z-20 w-[44px] h-[44px] rounded-full bg-black/30 flex items-center justify-center backdrop-blur-sm"
          aria-label="뒤로가기"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="15 18 9 12 15 6" />
          </svg>
        </button>

        {/* 저장 버튼 (히어로 위) */}
        <button
          type="button"
          onClick={handleSave}
          className="absolute top-[8px] right-[8px] z-20 w-[44px] h-[44px] rounded-full bg-black/30 flex items-center justify-center backdrop-blur-sm"
          aria-label={saved ? "저장 취소" : "저장"}
        >
          <motion.svg
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill={saved ? "var(--color-accent)" : "none"}
            stroke={saved ? "var(--color-accent)" : "#FFFFFF"}
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            animate={saved ? { scale: [0.8, 1.2, 1.0] } : { scale: 1 }}
            transition={{ duration: 0.3 }}
          >
            <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
          </motion.svg>
        </button>

        <motion.div
          className="w-full h-full"
          style={
            prefersReducedMotion
              ? {}
              : { y: heroY, scale: heroScale }
          }
        >
          <Image
            src={heroImage}
            alt={outfit.reasons?.[0] ?? "코디 이미지"}
            fill
            sizes="100vw"
            className="object-contain"
            priority
          />
        </motion.div>

        {/* 하단 그라디언트 */}
        <div className="absolute bottom-0 left-0 right-0 h-[80px] bg-gradient-to-t from-bg-primary to-transparent" />
      </div>

      {/* ── 메인 콘텐츠 ── */}
      <main className="max-w-[768px] mx-auto px-[20px] -mt-[16px] relative z-10">
        {/* 태그 */}
        {outfit.tags && outfit.tags.length > 0 && (
          <div className="flex flex-wrap gap-[6px] mb-[12px]">
            {outfit.tags.map((tag) => (
              <span
                key={tag}
                className="bg-bg-secondary text-text-secondary text-[11px] font-body rounded-full px-[10px] py-[4px] border border-border"
              >
                {tag}
              </span>
            ))}
          </div>
        )}

        {/* 제목 + TPO */}
        <h1 className="font-display text-[24px] text-text-primary leading-[1.25]">
          {outfit.reasons?.[0] ?? "코디 추천"}
        </h1>
        {outfit.designed_tpo && (
          <span className="inline-block mt-[8px] font-body text-[13px] text-accent">
            {outfit.designed_tpo}
            {outfit.designed_season && ` / ${outfit.designed_season}`}
          </span>
        )}

        {/* ── 가격 섹션 ── */}
        <div className="mt-[20px] flex items-baseline gap-[8px]">
          <span className="font-body text-[22px] text-text-primary font-bold">
            {"\u20A9"}{formatPrice(outfit.total_price ?? 0)}
          </span>
          {hasSavings && (
            <span className="font-body text-[14px] text-accent">
              최저가 {"\u20A9"}{formatPrice(outfit.lowest_total_price!)}
            </span>
          )}
        </div>

        {/* ── 5축 스코어 바 차트 ── */}
        <section className="mt-[28px]">
          <h2 className="font-display text-[18px] text-text-primary mb-[16px]">
            스코어
          </h2>
          <div className="space-y-[12px]">
            {SCORE_AXES.map((axis, i) => (
              <ScoreBar
                key={axis.key}
                label={axis.label}
                fullLabel={axis.fullLabel}
                value={outfit.scores?.[axis.key] ?? 0}
                color={axis.color}
                delay={i * 0.15}
              />
            ))}
          </div>
        </section>

        {/* ── 추천 이유 카드 ── */}
        {outfit.reasons && outfit.reasons.length > 1 && (
          <section className="mt-[28px]">
            <h2 className="font-display text-[18px] text-text-primary mb-[12px]">
              추천 이유
            </h2>
            <div className="bg-bg-secondary rounded-[var(--radius-lg)] p-[20px] space-y-[12px]">
              {outfit.reasons.slice(1).map((reason, i) => (
                <div key={i} className="flex gap-[10px]">
                  <span className="shrink-0 w-[20px] h-[20px] rounded-full bg-accent/10 text-accent text-[11px] font-body flex items-center justify-center font-medium">
                    {i + 1}
                  </span>
                  <p className="font-body text-[14px] text-text-primary leading-[1.6]">
                    {reason}
                  </p>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* ── 아이템 캐러셀 ── */}
        {outfit.items.length > 0 && (
          <section className="mt-[28px]">
            <h2 className="font-display text-[18px] text-text-primary mb-[12px]">
              아이템 구성
            </h2>
            <div
              className="flex gap-[12px] overflow-x-auto pb-[8px]"
              style={{ scrollbarWidth: "none" }}
            >
              {sortedItems.map((item) => {
                const isOwned = isClosetMode && catalogItemIds != null && !catalogItemIds.has(item.id);
                const linkEnabled = !isOwned && !!item.mall_url;

                return (
                  <a
                    key={item.id}
                    href={linkEnabled ? item.mall_url! : undefined}
                    target={linkEnabled ? "_blank" : undefined}
                    rel={linkEnabled ? "noopener noreferrer" : undefined}
                    onClick={linkEnabled ? handleMallClick : (e) => e.preventDefault()}
                    className={`shrink-0 w-[80px] group ${isOwned ? "cursor-default" : ""}`}
                  >
                    <div className="relative">
                      <div
                        className={`w-[80px] h-[80px] rounded-[var(--radius-md)] overflow-hidden border border-border ${
                          isOwned ? "bg-[#E8E5E0]" : "bg-bg-secondary"
                        }`}
                      >
                        {item.image_url ? (
                          <Image
                            src={item.image_url}
                            alt={item.name ?? "아이템"}
                            width={80}
                            height={80}
                            className={`object-cover w-full h-full ${isOwned ? "opacity-80" : ""}`}
                            loading="lazy"
                          />
                        ) : (
                          <div className="w-full h-full flex items-center justify-center">
                            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="var(--color-text-tertiary)" strokeWidth="1.5">
                              <rect x="3" y="3" width="18" height="18" rx="2" />
                              <circle cx="8.5" cy="8.5" r="1.5" />
                              <path d="M21 15l-5-5L5 21" />
                            </svg>
                          </div>
                        )}
                      </div>
                      {isOwned && (
                        <span className="absolute top-[4px] left-[4px] bg-[#6B5876]/90 text-white text-[9px] font-body font-medium px-[6px] py-[2px] rounded-full">
                          보유 중
                        </span>
                      )}
                    </div>
                    <p className={`font-body text-[11px] mt-[6px] line-clamp-2 ${
                      isOwned
                        ? "text-text-tertiary"
                        : "text-text-secondary group-hover:text-accent transition-colors"
                    }`}>
                      {item.brand && (
                        <span className="text-text-tertiary">{item.brand} </span>
                      )}
                      {item.name ?? item.category ?? "아이템"}
                    </p>
                    {item.price != null && (
                      <p className={`font-body text-[11px] font-medium ${
                        isOwned
                          ? "text-text-tertiary line-through"
                          : isClosetMode
                            ? "text-accent"
                            : "text-text-primary"
                      }`}>
                        {isOwned ? "보유" : `₩${formatPrice(item.price)}`}
                      </p>
                    )}
                  </a>
                );
              })}
            </div>
          </section>
        )}

        {/* ── 추가 구매 합계 (옷장 모드) ── */}
        {isClosetMode && closetOutfit.purchase_summary && (
          <section className="mt-[24px] bg-bg-secondary rounded-[var(--radius-lg)] p-[16px]">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-body text-[13px] text-text-secondary">
                  보유 {closetOutfit.purchase_summary.my_items_count}개 · 구매 필요 {closetOutfit.purchase_summary.purchase_items_count}개
                </p>
                <p className="font-body text-[11px] text-text-tertiary mt-[2px]">
                  이미 가지고 있는 아이템 비용은 제외
                </p>
              </div>
              <div className="text-right">
                <p className="font-body text-[11px] text-text-tertiary">추가 구매 합계</p>
                <p className="font-display text-[20px] text-accent font-bold">
                  ₩{formatPrice(closetOutfit.purchase_summary.purchase_total)}
                </p>
              </div>
            </div>
          </section>
        )}

        {/* 하단 여백 (CTA + BottomTabBar 겹침 방지) */}
        <div className="h-[220px]" />
      </main>

      {/* ── 하단 CTA (BottomTabBar 위에 고정) ── */}
      <div
        className="fixed left-0 right-0 z-40 bg-bg-primary/95 backdrop-blur-sm border-t border-border"
        style={{ bottom: "calc(60px + env(safe-area-inset-bottom, 0px))" }}
      >
        <div className="flex flex-col gap-[8px] px-[20px] py-[12px] max-w-[768px] mx-auto">
          <button
            type="button"
            onClick={handleTryOn}
            disabled={tryonState === "loading"}
            className="w-full py-[12px] rounded-full border border-accent text-accent text-[14px] font-body font-medium flex items-center justify-center gap-[6px] disabled:opacity-60"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M20.38 3.46L16 2a4 4 0 0 1-8 0L3.62 3.46a2 2 0 0 0-1.34 2.23l.58 3.47a1 1 0 0 0 .99.84H6v10c0 1.1.9 2 2 2h8a2 2 0 0 0 2-2V10h2.15a1 1 0 0 0 .99-.84l.58-3.47a2 2 0 0 0-1.34-2.23z" />
            </svg>
            착장으로 보기
            {tryonRemaining !== null && (
              <span className="text-[12px] text-text-tertiary ml-[4px]">
                (무료 {tryonRemaining}회 남음)
              </span>
            )}
          </button>
          <div className="flex gap-[12px]">
            <button
              type="button"
              onClick={handleSave}
              className={`flex-1 py-[14px] rounded-full text-[15px] font-body font-medium transition-colors ${
                saved
                  ? "bg-accent text-white"
                  : "bg-bg-secondary text-text-primary border border-border"
              }`}
            >
              {saved ? "저장됨" : "저장"}
            </button>
            <button
              type="button"
              onClick={() => setShowComparePicker(true)}
              className="flex-1 py-[14px] rounded-full bg-accent text-white text-[15px] font-body font-medium"
            >
              A vs B 비교
            </button>
          </div>
        </div>
      </div>

      {/* ── Try-On 바텀시트 ── */}
      <AnimatePresence>
        {tryonOpen && (
          <>
            <motion.div
              className="fixed inset-0 bg-black/40 z-40"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={handleTryOnClose}
            />
            <motion.div
              role="dialog"
              aria-modal="true"
              aria-label="AI 착장 미리보기"
              className="fixed bottom-0 left-0 right-0 z-50 bg-bg-primary rounded-t-[var(--radius-xl)] px-[20px] pt-[16px] pb-[32px]"
              initial={prefersReducedMotion ? false : { y: "100%" }}
              animate={{ y: 0 }}
              exit={{ y: "100%" }}
              transition={
                prefersReducedMotion
                  ? { duration: 0 }
                  : { type: "spring", stiffness: 300, damping: 30 }
              }
            >
              <div className="flex justify-center mb-[16px]">
                <div className="w-[36px] h-[4px] rounded-full bg-border" />
              </div>

              {tryonState === "loading" && (
                <div className="flex flex-col items-center py-[32px]">
                  <div className="w-[48px] h-[48px] rounded-full border-2 border-accent border-t-transparent animate-spin mb-[16px]" />
                  <p className="font-body text-[15px] text-text-primary">
                    AI 착장 이미지 생성 중...
                  </p>
                  <p className="font-body text-[13px] text-text-secondary mt-[4px]">
                    보통 10~20초 정도 걸려요
                  </p>
                </div>
              )}

              {tryonState === "success" && tryonImageUrl && (
                <motion.div
                  className="flex flex-col items-center"
                  initial={prefersReducedMotion ? false : { y: 20, opacity: 0 }}
                  animate={{ y: 0, opacity: 1 }}
                  transition={{ duration: 0.4, ease: "easeOut" }}
                >
                  <div
                    className="w-full max-w-[320px] rounded-[var(--radius-lg)] overflow-hidden"
                    style={{ aspectRatio: "3/4" }}
                  >
                    <Image
                      src={tryonImageUrl}
                      alt="AI 착장 이미지"
                      width={320}
                      height={427}
                      className="w-full h-full object-cover"
                      unoptimized
                    />
                  </div>
                  {tryonRemaining !== null && (
                    <p className="font-body text-[12px] text-text-tertiary mt-[12px]">
                      무료 {tryonRemaining}회 남음
                    </p>
                  )}
                  <div className="flex gap-[12px] mt-[16px] w-full max-w-[320px]">
                    <button
                      type="button"
                      onClick={() => {
                        const saved: { outfitId: string; imageUrl: string; createdAt: string }[] =
                          JSON.parse(localStorage.getItem("colorfit_tryon_images") ?? "[]");
                        if (!saved.some((s) => s.imageUrl === tryonImageUrl)) {
                          saved.unshift({ outfitId, imageUrl: tryonImageUrl, createdAt: new Date().toISOString() });
                          localStorage.setItem("colorfit_tryon_images", JSON.stringify(saved.slice(0, 50)));
                        }
                        handleTryOnClose();
                      }}
                      className="flex-1 py-[14px] bg-accent text-white font-body text-[15px] font-medium rounded-[var(--radius-full)]"
                    >
                      이미지 저장
                    </button>
                    <button
                      type="button"
                      onClick={handleTryOnClose}
                      className="flex-1 py-[14px] border border-border text-text-primary font-body text-[15px] font-medium rounded-[var(--radius-full)]"
                    >
                      닫기
                    </button>
                  </div>
                </motion.div>
              )}

              {tryonState === "error" && (
                <div className="flex flex-col items-center py-[24px]">
                  <p className="font-body text-[15px] text-text-primary mb-[4px]">
                    이미지를 생성하지 못했어요
                  </p>
                  <p className="font-body text-[13px] text-text-secondary mb-[20px]">
                    네트워크를 확인하고 다시 시도해주세요
                  </p>
                  <button
                    type="button"
                    onClick={handleTryOn}
                    className="px-[24px] py-[12px] bg-accent text-white font-body text-[15px] font-medium rounded-[var(--radius-full)]"
                  >
                    다시 시도
                  </button>
                </div>
              )}

              {tryonState === "limit" && (
                <div className="flex flex-col items-center py-[24px]">
                  <p className="font-display text-[18px] text-text-primary mb-[4px]">
                    무료 착장 생성 완료
                  </p>
                  <p className="font-body text-[14px] text-text-secondary text-center mb-[20px]">
                    무료 착장 3회를 모두 사용했어요.
                    <br />
                    프리미엄으로 업그레이드하면 무제한 이용 가능해요.
                  </p>
                  <button
                    type="button"
                    onClick={handleTryOnUpgrade}
                    className="w-full max-w-[280px] py-[14px] bg-accent text-white font-body text-[15px] font-medium rounded-[var(--radius-full)]"
                  >
                    프리미엄으로 업그레이드
                  </button>
                  <button
                    type="button"
                    onClick={handleTryOnClose}
                    className="mt-[12px] font-body text-[14px] text-text-tertiary"
                  >
                    나중에 할게요
                  </button>
                </div>
              )}
            </motion.div>
          </>
        )}
      </AnimatePresence>

      {/* ── 비교 대상 선택 바텀시트 ── */}
      <AnimatePresence>
        {showComparePicker && (
          <ComparePickerSheet
            currentOutfitId={outfitId}
            onSelect={handleCompareSelect}
            onClose={() => setShowComparePicker(false)}
          />
        )}
      </AnimatePresence>

      {/* ── 구매 후 피드백 바텀시트 ── */}
      <AnimatePresence>
        {showPurchaseFeedback && userId && (
          <PurchaseFeedbackSheet
            outfitId={outfitId}
            userId={userId}
            onClose={handleFeedbackClose}
          />
        )}
      </AnimatePresence>

      {/* 로그인 필요 토스트 */}
      <AnimatePresence>
        {loginToast && (
          <motion.div
            className="fixed bottom-[100px] left-1/2 -translate-x-1/2 z-50 px-[20px] py-[12px] rounded-full text-[14px] font-body"
            style={{ backgroundColor: "rgba(0,0,0,0.8)", color: "#FFFFFF" }}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 20 }}
          >
            로그인이 필요해요
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
