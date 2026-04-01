"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence, useReducedMotion } from "framer-motion";
import OutfitCard from "@/components/OutfitCard";
import { fetchFeed, postReaction, type OutfitFeedItem } from "@/lib/api";

/* ── TPO 탭 데이터 ── */
const TPO_TABS = [
  { id: "all", label: "전체" },
  { id: "commute", label: "출근" },
  { id: "date", label: "데이트" },
  { id: "interview", label: "면접" },
  { id: "weekend", label: "주말" },
  { id: "campus", label: "캠퍼스" },
  { id: "travel", label: "여행" },
  { id: "event", label: "행사" },
  { id: "workout", label: "운동" },
];

/* ── 예산 프리셋 ── */
const BUDGET_MIN_DEFAULT = 30000;
const BUDGET_MAX_DEFAULT = 100000;
const BUDGET_STEP = 10000;
const BUDGET_ABSOLUTE_MIN = 0;
const BUDGET_ABSOLUTE_MAX = 300000;

function formatBudgetLabel(min: number, max: number): string {
  const fmtMin = min >= 10000 ? `${Math.floor(min / 10000)}만` : `${min.toLocaleString("ko-KR")}`;
  const fmtMax = max >= 10000 ? `${Math.floor(max / 10000)}만` : `${max.toLocaleString("ko-KR")}`;
  return `₩${fmtMin}~₩${fmtMax}`;
}

/* ── 스켈레톤 카드 ── */
function SkeletonCard() {
  return (
    <div className="px-[20px] mb-[20px]">
      <div
        className="w-full rounded-[var(--radius-lg)] bg-[#E0DCD7] animate-pulse"
        style={{ aspectRatio: "3/4" }}
      />
      <div className="mt-[12px] h-[16px] w-3/4 rounded bg-[#E0DCD7] animate-pulse" />
      <div className="mt-[8px] h-[14px] w-1/2 rounded bg-[#E0DCD7] animate-pulse" />
    </div>
  );
}

/* ── 오늘의 컬러핏 특별 카드 ── */
function TodayColorFitCard({ outfit }: { outfit: OutfitFeedItem }) {
  return (
    <div className="mx-[20px] mb-[24px] bg-bg-secondary rounded-[var(--radius-xl)] p-[24px]">
      <span className="font-display text-[18px] text-accent">
        오늘의 컬러핏
      </span>
      <div className="mt-[12px]" style={{ transform: "scale(1.1)", transformOrigin: "top center" }}>
        <OutfitCard
          id={outfit.id}
          imageUrl={outfit.image_url ?? "/placeholder-outfit.png"}
          title={outfit.reasons[0] ?? "오늘의 추천 코디"}
          totalPrice={outfit.total_price ?? 0}
          reason={outfit.reasons[1] ?? ""}
          scores={{ pcf: outfit.scores?.pcf ?? 0, of: outfit.scores?.of ?? 0 }}
          itemCount={outfit.tags?.length ?? 3}
          index={0}
        />
      </div>
      {outfit.reasons.length >= 2 && (
        <p className="font-body text-[13px] text-text-secondary mt-[12px] line-clamp-2">
          {outfit.reasons.slice(0, 2).join(" · ")}
        </p>
      )}
    </div>
  );
}

export default function FeedPage() {
  const prefersReducedMotion = useReducedMotion();
  const router = useRouter();

  /* 사용자 프로필 (localStorage에서 로드) */
  const [toneId, setToneId] = useState<string>("");
  const [gender, setGender] = useState<string>("");

  /* 필터 상태 */
  const [activeTpo, setActiveTpo] = useState("all");
  const [budgetMin, setBudgetMin] = useState(BUDGET_MIN_DEFAULT);
  const [budgetMax, setBudgetMax] = useState(BUDGET_MAX_DEFAULT);
  const [budgetOpen, setBudgetOpen] = useState(false);

  /* 토스트 */
  const [toast, setToast] = useState<string | null>(null);
  const toastTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const showToast = useCallback((message: string) => {
    if (toastTimerRef.current) clearTimeout(toastTimerRef.current);
    setToast(message);
    toastTimerRef.current = setTimeout(() => setToast(null), 1500);
  }, []);

  /* 저장된 코디 ID Set */
  const [savedIds, setSavedIds] = useState<Set<string>>(new Set());

  /* 피드 데이터 */
  const [outfits, setOutfits] = useState<OutfitFeedItem[]>([]);
  const [page, setPage] = useState(1);
  const [hasNext, setHasNext] = useState(false);
  const [status, setStatus] = useState<"loading" | "success" | "empty" | "error">("loading");
  const [loadingMore, setLoadingMore] = useState(false);

  /* refs */
  const sentinelRef = useRef<HTMLDivElement>(null);
  const tpoScrollRef = useRef<HTMLDivElement>(null);

  /* 프로필 로드 */
  useEffect(() => {
    const storedTone = localStorage.getItem("colorfit_tone") ?? "";
    const storedGender = localStorage.getItem("colorfit_gender") ?? "";
    setToneId(storedTone);
    setGender(storedGender);
  }, []);

  /* 피드 로드 */
  const loadFeed = useCallback(
    async (pageNum: number, append: boolean) => {
      if (!toneId) {
        setStatus("empty");
        return;
      }

      if (!append) setStatus("loading");
      else setLoadingMore(true);

      try {
        const data = await fetchFeed({
          toneId,
          gender: gender || undefined,
          tpo: activeTpo === "all" ? undefined : activeTpo,
          budgetMin,
          budgetMax,
          page: pageNum,
        });

        setOutfits((prev) => {
          const newOutfits = append ? [...prev, ...data.outfits] : data.outfits;
          setStatus(newOutfits.length === 0 ? "empty" : "success");
          return newOutfits;
        });
        setHasNext(data.has_next);
        setPage(pageNum);
      } catch {
        if (!append) setStatus("error");
      } finally {
        setLoadingMore(false);
      }
    },
    [toneId, gender, activeTpo, budgetMin, budgetMax],
  );

  /* 필터 변경 시 리로드 */
  useEffect(() => {
    if (toneId) {
      loadFeed(1, false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [toneId, gender, activeTpo, budgetMin, budgetMax]);

  /* 무한 스크롤 (IntersectionObserver) */
  useEffect(() => {
    const sentinel = sentinelRef.current;
    if (!sentinel) return;

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && hasNext && !loadingMore && status === "success") {
          loadFeed(page + 1, true);
        }
      },
      { rootMargin: "200px" },
    );

    observer.observe(sentinel);
    return () => observer.disconnect();
  }, [hasNext, loadingMore, page, status, loadFeed]);

  /* toastTimer cleanup */
  useEffect(() => {
    return () => {
      if (toastTimerRef.current) clearTimeout(toastTimerRef.current);
    };
  }, []);

  /* save/dislike 핸들러 */
  const userId = typeof window !== "undefined"
    ? localStorage.getItem("colorfit_user_id") ?? ""
    : "";

  const handleSaveToggle = useCallback((id: string) => {
    const wasSaved = savedIds.has(id);
    setSavedIds((prev) => {
      const next = new Set(prev);
      if (wasSaved) next.delete(id);
      else next.add(id);
      return next;
    });
    showToast(wasSaved ? "저장 취소" : "저장했어요");
    if (userId) {
      postReaction(userId, id, "save").catch(() => {});
    }
  }, [savedIds, userId, showToast]);

  const handleDislike = useCallback(
    (id: string) => {
      setOutfits((prev) => prev.filter((o) => o.id !== id));
      showToast("관심없음");
      if (userId) {
        postReaction(userId, id, "dislike").catch(() => {});
      }
    },
    [userId, showToast],
  );

  const handleCardTap = useCallback((id: string) => {
    router.push(`/outfit/${id}`);
  }, [router]);

  /* 오늘의 컬러핏 (피드 첫 번째 아이템) */
  const todayPick = outfits[0] ?? null;
  const feedOutfits = outfits.slice(1);

  return (
    <div className="min-h-screen bg-bg-primary">
      {/* ── 헤더 (sticky) ── */}
      <header className="sticky top-0 z-30 bg-bg-primary/95 backdrop-blur-sm">
        <div className="flex items-center justify-between px-[20px] h-[52px] max-w-[768px] mx-auto">
          <span className="font-display text-[20px] text-text-primary font-bold">
            ColorFit
          </span>
          <button
            type="button"
            className="w-[32px] h-[32px] rounded-full bg-bg-secondary flex items-center justify-center"
            aria-label="프로필"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--color-text-secondary)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
              <circle cx="12" cy="7" r="4" />
            </svg>
          </button>
        </div>

        {/* ── TPO 탭 필터 ── */}
        <div
          ref={tpoScrollRef}
          className="flex gap-[8px] px-[20px] pb-[12px] overflow-x-auto scrollbar-hide max-w-[768px] mx-auto"
          style={{ scrollbarWidth: "none" }}
        >
          {TPO_TABS.map((tab) => (
            <button
              key={tab.id}
              type="button"
              onClick={() => setActiveTpo(tab.id)}
              className={`shrink-0 px-[16px] py-[8px] rounded-full text-[14px] font-body transition-colors whitespace-nowrap ${
                activeTpo === tab.id
                  ? "bg-accent text-white"
                  : "bg-bg-secondary text-text-secondary border border-border"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* ── 예산 슬라이더 ── */}
        <div className="px-[20px] pb-[12px] max-w-[768px] mx-auto">
          <button
            type="button"
            onClick={() => setBudgetOpen((prev) => !prev)}
            className="flex items-center gap-[6px] text-[13px] font-body text-text-secondary"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="4" y1="21" x2="4" y2="14" /><line x1="4" y1="10" x2="4" y2="3" />
              <line x1="12" y1="21" x2="12" y2="12" /><line x1="12" y1="8" x2="12" y2="3" />
              <line x1="20" y1="21" x2="20" y2="16" /><line x1="20" y1="12" x2="20" y2="3" />
              <line x1="1" y1="14" x2="7" y2="14" /><line x1="9" y1="8" x2="15" y2="8" />
              <line x1="17" y1="16" x2="23" y2="16" />
            </svg>
            <span>{formatBudgetLabel(budgetMin, budgetMax)}</span>
            <svg
              width="12"
              height="12"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              className={`transition-transform ${budgetOpen ? "rotate-180" : ""}`}
            >
              <polyline points="6 9 12 15 18 9" />
            </svg>
          </button>

          <AnimatePresence>
            {budgetOpen && (
              <motion.div
                initial={prefersReducedMotion ? false : { height: 0, opacity: 0 }}
                animate={{ height: "auto", opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                transition={{ duration: 0.3 }}
                className="overflow-hidden"
              >
                <div className="pt-[12px] flex flex-col gap-[8px]">
                  <label className="flex items-center justify-between text-[12px] font-body text-text-tertiary">
                    <span>최소</span>
                    <span>₩{budgetMin.toLocaleString("ko-KR")}</span>
                  </label>
                  <input
                    type="range"
                    min={BUDGET_ABSOLUTE_MIN}
                    max={budgetMax - BUDGET_STEP}
                    step={BUDGET_STEP}
                    value={budgetMin}
                    onChange={(e) => setBudgetMin(Number(e.target.value))}
                    className="w-full accent-accent"
                    aria-label="최소 예산"
                  />
                  <label className="flex items-center justify-between text-[12px] font-body text-text-tertiary">
                    <span>최대</span>
                    <span>₩{budgetMax.toLocaleString("ko-KR")}</span>
                  </label>
                  <input
                    type="range"
                    min={budgetMin + BUDGET_STEP}
                    max={BUDGET_ABSOLUTE_MAX}
                    step={BUDGET_STEP}
                    value={budgetMax}
                    onChange={(e) => setBudgetMax(Number(e.target.value))}
                    className="w-full accent-accent"
                    aria-label="최대 예산"
                  />
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </header>

      {/* ── 메인 콘텐츠 ── */}
      <main className="max-w-[768px] mx-auto">
        {/* Loading */}
        {status === "loading" && (
          <div>
            <SkeletonCard />
            <SkeletonCard />
            <SkeletonCard />
          </div>
        )}

        {/* Error */}
        {status === "error" && (
          <div className="flex flex-col items-center justify-center py-[80px] px-[20px]">
            <p className="font-body text-[16px] text-text-primary mb-[16px]">
              불러오지 못했어요
            </p>
            <button
              type="button"
              onClick={() => loadFeed(1, false)}
              className="px-[24px] py-[10px] rounded-full border border-accent text-accent text-[14px] font-body"
            >
              다시 시도
            </button>
          </div>
        )}

        {/* Empty */}
        {status === "empty" && (
          <div className="flex flex-col items-center justify-center py-[80px] px-[20px]">
            <svg width="64" height="64" viewBox="0 0 64 64" fill="none" className="mb-[16px]">
              <rect x="20" y="8" width="4" height="40" rx="2" fill="var(--color-border)" />
              <rect x="40" y="8" width="4" height="40" rx="2" fill="var(--color-border)" />
              <path d="M16 8h32" stroke="var(--color-border)" strokeWidth="4" strokeLinecap="round" />
            </svg>
            <p className="font-body text-[16px] text-text-primary mb-[4px]">
              조건에 맞는 코디가 없어요
            </p>
            <button
              type="button"
              onClick={() => {
                setActiveTpo("all");
                setBudgetMin(BUDGET_MIN_DEFAULT);
                setBudgetMax(BUDGET_MAX_DEFAULT);
              }}
              className="mt-[12px] px-[24px] py-[10px] rounded-full bg-accent text-white text-[14px] font-body"
            >
              필터를 변경해보세요
            </button>
          </div>
        )}

        {/* Success */}
        {status === "success" && (
          <>
            {/* 오늘의 컬러핏 */}
            {todayPick && <TodayColorFitCard outfit={todayPick} />}

            {/* 코디 카드 리스트 */}
            {feedOutfits.map((outfit, i) => (
              <OutfitCard
                key={outfit.id}
                id={outfit.id}
                imageUrl={outfit.image_url ?? "/placeholder-outfit.png"}
                title={outfit.reasons[0] ?? "코디 추천"}
                totalPrice={outfit.total_price ?? 0}
                reason={outfit.reasons[1] ?? ""}
                scores={{
                  pcf: outfit.scores?.pcf ?? 0,
                  of: outfit.scores?.of ?? 0,
                }}
                itemCount={outfit.tags?.length ?? 3}
                isSaved={savedIds.has(outfit.id)}
                index={i}
                onTap={handleCardTap}
                onSaveToggle={handleSaveToggle}
                onDislike={handleDislike}
              />
            ))}

            {/* 무한 스크롤 센티널 */}
            <div ref={sentinelRef} className="h-[1px]" />

            {/* 추가 로딩 */}
            {loadingMore && (
              <div className="py-[20px]">
                <SkeletonCard />
              </div>
            )}
          </>
        )}

        {/* 하단 여백 (탭바 겹침 방지) */}
        <div className="h-[80px]" />
      </main>

      {/* 토스트 */}
      <AnimatePresence>
        {toast && (
          <motion.div
            className="fixed bottom-[100px] left-1/2 -translate-x-1/2 z-50 bg-[#333] text-white text-[14px] font-body px-[20px] py-[10px] rounded-full shadow-lg"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 20 }}
            transition={{ duration: 0.2 }}
          >
            {toast}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
