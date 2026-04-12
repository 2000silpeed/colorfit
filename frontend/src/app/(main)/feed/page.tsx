"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence, useReducedMotion } from "framer-motion";
import OutfitCard from "@/components/OutfitCard";
import { fetchFeed, postReaction, type OutfitFeedItem } from "@/lib/api";
import { isLoggedIn } from "@/lib/auth";
import { migrateLegacyTones } from "@/lib/toneMigration";

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

/* ── 예산 ── */
const BUDGET_MIN_DEFAULT = 30000;
const BUDGET_MAX_DEFAULT = 100000;
const BUDGET_STEP = 10000;
const BUDGET_ABSOLUTE_MIN = 0;
const BUDGET_ABSOLUTE_MAX = 500000;

function formatBudgetLabel(min: number, max: number): string {
  const fmtMin = min >= 10000 ? `${Math.floor(min / 10000)}만` : `${min.toLocaleString("ko-KR")}`;
  const fmtMax = max >= 10000 ? `${Math.floor(max / 10000)}만` : `${max.toLocaleString("ko-KR")}`;
  return `₩${fmtMin}~₩${fmtMax}`;
}

/* ── 스켈레톤 ── */
function SkeletonCard() {
  return (
    <div className="mb-[24px]">
      <div
        className="w-full bg-bg-secondary animate-pulse"
        style={{ aspectRatio: "1/1", borderRadius: "var(--radius-lg)" }}
      />
      <div className="mt-[12px] px-[2px]">
        <div className="h-[16px] w-3/4 rounded bg-bg-secondary animate-pulse" />
        <div className="mt-[8px] h-[14px] w-1/3 rounded bg-bg-secondary animate-pulse" />
        <div className="mt-[6px] h-[13px] w-2/3 rounded bg-bg-secondary animate-pulse" />
        <div className="mt-[8px] flex gap-[6px]">
          <div className="h-[22px] w-[56px] rounded-full bg-bg-secondary animate-pulse" />
          <div className="h-[22px] w-[52px] rounded-full bg-bg-secondary animate-pulse" />
        </div>
      </div>
    </div>
  );
}

/* ── 오늘의 컬러핏 ── */
interface TodayColorFitCardProps {
  outfit: OutfitFeedItem;
  isSaved: boolean;
  onTap: (id: string) => void;
  onSaveToggle: (id: string) => void;
}

function TodayColorFitCard({ outfit, isSaved, onTap, onSaveToggle }: TodayColorFitCardProps) {
  return (
    <div
      className="mb-[32px] p-[20px]"
      style={{
        backgroundColor: "var(--color-bg-secondary)",
        borderRadius: "var(--radius-xl)",
      }}
    >
      <span
        className="text-[18px] font-semibold"
        style={{ fontFamily: "var(--font-display)", color: "var(--color-accent)" }}
      >
        오늘의 컬러핏
      </span>
      <div className="mt-[12px]">
        <OutfitCard
          id={outfit.id}
          imageUrl={outfit.image_url ?? "/placeholder-outfit.png"}
          items={outfit.items ?? []}
          title={outfit.reasons[0] ?? "오늘의 추천 코디"}
          totalPrice={outfit.total_price ?? 0}
          reason={outfit.reasons[1] ?? ""}
          scores={{ pcf: outfit.scores?.pcf ?? 0, of: outfit.scores?.of ?? 0 }}
          itemCount={outfit.items?.length ?? 0}
          isSaved={isSaved}
          index={0}
          onTap={onTap}
          onSaveToggle={onSaveToggle}
        />
      </div>
    </div>
  );
}

export default function FeedPage() {
  const prefersReducedMotion = useReducedMotion();
  const router = useRouter();

  /* 프로필 */
  const [toneId, setToneId] = useState<string>("");
  const [gender, setGender] = useState<string>("");
  const [ageGroup, setAgeGroup] = useState<string>("");

  /* 필터 */
  const [activeTpo, setActiveTpo] = useState("all");
  const [budgetMin, setBudgetMin] = useState(BUDGET_MIN_DEFAULT);
  const [budgetMax, setBudgetMax] = useState(BUDGET_MAX_DEFAULT);
  const [budgetOpen, setBudgetOpen] = useState(false);
  const [verifiedOnly, setVerifiedOnly] = useState(false);
  const [preferredBrands, setPreferredBrands] = useState<string[]>([]);

  /* 토스트 */
  const [toast, setToast] = useState<string | null>(null);
  const toastTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const showToast = useCallback((message: string) => {
    if (toastTimerRef.current) clearTimeout(toastTimerRef.current);
    setToast(message);
    toastTimerRef.current = setTimeout(() => setToast(null), 1500);
  }, []);

  /* 저장 */
  const [savedIds, setSavedIds] = useState<Set<string>>(new Set());

  /* 피드 */
  const [outfits, setOutfits] = useState<OutfitFeedItem[]>([]);
  const [page, setPage] = useState(1);
  const [hasNext, setHasNext] = useState(false);
  const [status, setStatus] = useState<"loading" | "success" | "empty" | "error">("loading");
  const [loadingMore, setLoadingMore] = useState(false);

  /* 헤더 스크롤 상태 */
  const [scrolled, setScrolled] = useState(false);

  const sentinelRef = useRef<HTMLDivElement>(null);
  const tpoScrollRef = useRef<HTMLDivElement>(null);
  const tpoDragState = useRef({ isDown: false, startX: 0, scrollLeft: 0 });

  /* 스크롤 감지 */
  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 8);
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  /* 프로필 로드 */
  useEffect(() => {
    migrateLegacyTones();
    const storedTone = localStorage.getItem("colorfit_tone") ?? "";
    const storedGender = localStorage.getItem("colorfit_gender") ?? "";
    const storedAge = localStorage.getItem("colorfit_age_group") ?? "";
    setToneId(storedTone);
    setGender(storedGender);
    setAgeGroup(storedAge);
    try {
      const storedBudget = JSON.parse(localStorage.getItem("colorfit_budget") || "null");
      if (storedBudget) {
        setBudgetMin(storedBudget[0] ?? BUDGET_MIN_DEFAULT);
        setBudgetMax(storedBudget[1] ?? BUDGET_MAX_DEFAULT);
      }
    } catch { /* empty */ }
    try {
      const storedBrands = JSON.parse(localStorage.getItem("colorfit_preferred_brands") || "[]");
      if (Array.isArray(storedBrands)) setPreferredBrands(storedBrands);
    } catch { /* empty */ }
  }, []);

  /* 피드 로드 */
  const loadFeed = useCallback(
    async (pageNum: number, append: boolean) => {
      if (!toneId) {
        router.push("/onboarding/step1");
        return;
      }

      if (!append) setStatus("loading");
      else setLoadingMore(true);

      try {
        const data = await fetchFeed({
          toneId,
          gender: gender || undefined,
          ageGroup: ageGroup || undefined,
          tpo: activeTpo === "all" ? undefined : activeTpo,
          budgetMin,
          budgetMax,
          verifiedOnly: verifiedOnly || undefined,
          preferredBrands: preferredBrands.length > 0 ? preferredBrands : undefined,
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
    [toneId, gender, ageGroup, activeTpo, budgetMin, budgetMax, verifiedOnly, preferredBrands, router],
  );

  /* 필터 변경 시 리로드 */
  useEffect(() => {
    if (toneId) loadFeed(1, false);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [toneId, gender, ageGroup, activeTpo, budgetMin, budgetMax, verifiedOnly]);

  /* 무한 스크롤 */
  useEffect(() => {
    const sentinel = sentinelRef.current;
    if (!sentinel) return;
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && hasNext && !loadingMore && status === "success") {
          loadFeed(page + 1, true);
        }
      },
      { rootMargin: "300px" },
    );
    observer.observe(sentinel);
    return () => observer.disconnect();
  }, [hasNext, loadingMore, page, status, loadFeed]);

  useEffect(() => {
    return () => { if (toastTimerRef.current) clearTimeout(toastTimerRef.current); };
  }, []);

  /* 핸들러 */
  const userId = (() => {
    if (typeof window === "undefined") return "";
    let id = localStorage.getItem("colorfit_user_id");
    if (!id) {
      id = crypto.randomUUID();
      localStorage.setItem("colorfit_user_id", id);
    }
    return id;
  })();

  const handleSaveToggle = useCallback((id: string) => {
    if (!isLoggedIn()) {
      showToast("로그인이 필요해요");
      sessionStorage.setItem("colorfit_return_url", "/feed");
      router.push("/login?returnUrl=/feed");
      return;
    }
    const wasSaved = savedIds.has(id);
    setSavedIds((prev) => {
      const next = new Set(prev);
      if (wasSaved) next.delete(id); else next.add(id);
      return next;
    });
    showToast(wasSaved ? "저장 취소" : "저장했어요");
    if (userId) postReaction(userId, id, "save").catch(() => {});
  }, [savedIds, userId, showToast, router]);

  const handleDislike = useCallback((id: string) => {
    if (!isLoggedIn()) {
      showToast("로그인이 필요해요");
      sessionStorage.setItem("colorfit_return_url", "/feed");
      router.push("/login?returnUrl=/feed");
      return;
    }
    setOutfits((prev) => prev.filter((o) => o.id !== id));
    showToast("관심없음");
    if (userId) postReaction(userId, id, "dislike").catch(() => {});
  }, [userId, showToast, router]);

  const handleCardTap = useCallback((id: string) => {
    router.push(`/outfit/${id}`);
  }, [router]);

  const todayPick = outfits[0] ?? null;
  const feedOutfits = outfits.slice(1);

  return (
    <div className="min-h-screen" style={{ backgroundColor: "var(--color-bg-primary)" }}>
      {/* ── Sticky Header ── */}
      <header
        className="sticky top-0 z-30 transition-shadow duration-150"
        style={{
          backgroundColor: scrolled ? "rgba(248, 246, 243, 0.95)" : "var(--color-bg-primary)",
          backdropFilter: scrolled ? "blur(12px)" : "none",
          WebkitBackdropFilter: scrolled ? "blur(12px)" : "none",
          boxShadow: scrolled ? "0 1px 0 var(--color-border)" : "none",
        }}
      >
        {/* Logo + Profile */}
        <div className="flex items-center justify-between px-[20px] h-[48px] max-w-[430px] mx-auto">
          <span
            className="text-[20px] font-bold tracking-[-0.02em]"
            style={{ fontFamily: "var(--font-display)", color: "var(--color-text-primary)" }}
          >
            ColorFit
          </span>
          <button
            type="button"
            className="w-[36px] h-[36px] flex items-center justify-center rounded-full"
            style={{ backgroundColor: "var(--color-bg-secondary)" }}
            aria-label="프로필"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--color-text-secondary)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
              <circle cx="12" cy="7" r="4" />
            </svg>
          </button>
        </div>

        {/* TPO Filter Chips */}
        <div className="relative">
        <div
          ref={tpoScrollRef}
          className="flex gap-[6px] pl-[20px] pb-[10px] overflow-x-auto cursor-grab active:cursor-grabbing"
          style={{ scrollbarWidth: "none", WebkitOverflowScrolling: "touch" }}
          onMouseDown={(e) => {
            const el = tpoScrollRef.current;
            if (!el) return;
            tpoDragState.current = { isDown: true, startX: e.pageX - el.offsetLeft, scrollLeft: el.scrollLeft };
          }}
          onMouseLeave={() => { tpoDragState.current.isDown = false; }}
          onMouseUp={() => { tpoDragState.current.isDown = false; }}
          onMouseMove={(e) => {
            const d = tpoDragState.current;
            if (!d.isDown) return;
            e.preventDefault();
            const el = tpoScrollRef.current;
            if (!el) return;
            const x = e.pageX - el.offsetLeft;
            el.scrollLeft = d.scrollLeft - (x - d.startX);
          }}
        >
          {TPO_TABS.map((tab) => {
            const isActive = activeTpo === tab.id;
            return (
              <button
                key={tab.id}
                type="button"
                onClick={() => setActiveTpo(tab.id)}
                className="shrink-0 min-h-[34px] px-[14px] py-[6px] text-[13px] transition-colors active:scale-[0.97] active:opacity-80"
                style={{
                  fontFamily: "var(--font-body)",
                  borderRadius: "var(--radius-full)",
                  whiteSpace: "nowrap",
                  backgroundColor: isActive ? "var(--color-accent)" : "transparent",
                  color: isActive ? "#FFFFFF" : "var(--color-text-secondary)",
                  border: isActive ? "none" : "1px solid var(--color-border)",
                  fontWeight: isActive ? 600 : 400,
                }}
              >
                {tab.label}
              </button>
            );
          })}
          <div className="shrink-0 w-[20px]" aria-hidden="true" />
        </div>
        <div
          className="absolute top-0 right-0 bottom-[10px] w-[32px] pointer-events-none"
          style={{ background: "linear-gradient(to right, transparent, var(--color-bg-primary))" }}
          aria-hidden="true"
        />
        </div>

        {/* Filter bar */}
        <div className="px-[20px] pb-[8px] max-w-[430px] mx-auto flex items-center gap-[8px]">
          <button
            type="button"
            onClick={() => setBudgetOpen((prev) => !prev)}
            className="flex items-center gap-[4px] min-h-[44px] py-[8px] text-[13px]"
            style={{ fontFamily: "var(--font-body)", color: "var(--color-text-secondary)" }}
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
              width="10"
              height="10"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.5"
              className={`transition-transform duration-150 ${budgetOpen ? "rotate-180" : ""}`}
            >
              <polyline points="6 9 12 15 18 9" />
            </svg>
          </button>

          <button
            type="button"
            onClick={() => setVerifiedOnly((prev) => !prev)}
            className="shrink-0 inline-flex items-center gap-[3px] min-h-[32px] px-[10px] py-[6px] text-[12px] transition-colors active:scale-[0.97]"
            style={{
              fontFamily: "var(--font-body)",
              borderRadius: "var(--radius-full)",
              backgroundColor: verifiedOnly ? "var(--color-accent)" : "transparent",
              color: verifiedOnly ? "#FFFFFF" : "var(--color-text-secondary)",
              border: verifiedOnly ? "none" : "1px solid var(--color-border)",
              fontWeight: verifiedOnly ? 600 : 400,
            }}
          >
            <svg width="10" height="10" viewBox="0 0 16 16" fill="currentColor">
              <path d="M8 0a8 8 0 1 1 0 16A8 8 0 0 1 8 0zm3.41 5.09L7.2 9.3 5.3 7.4a.75.75 0 0 0-1.1 1.02l.08.08 2.5 2.5a.75.75 0 0 0 1.02.08l.08-.08 4.8-4.8a.75.75 0 0 0-1.1-1.02l-.07.01z" />
            </svg>
            추천 브랜드
          </button>
        </div>

        {/* Budget slider (expandable) */}
        <div className="px-[20px] max-w-[430px] mx-auto">
          <AnimatePresence>
            {budgetOpen && (
              <motion.div
                initial={prefersReducedMotion ? false : { height: 0, opacity: 0 }}
                animate={{ height: "auto", opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                transition={{ duration: 0.25 }}
                className="overflow-hidden"
              >
                <div className="pb-[12px] flex flex-col gap-[8px]">
                  <label className="flex items-center justify-between text-[12px]"
                    style={{ fontFamily: "var(--font-body)", color: "var(--color-text-tertiary)" }}
                  >
                    <span>최소</span>
                    <span style={{ fontVariantNumeric: "tabular-nums" }}>₩{budgetMin.toLocaleString("ko-KR")}</span>
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
                  <label className="flex items-center justify-between text-[12px]"
                    style={{ fontFamily: "var(--font-body)", color: "var(--color-text-tertiary)" }}
                  >
                    <span>최대</span>
                    <span style={{ fontVariantNumeric: "tabular-nums" }}>₩{budgetMax.toLocaleString("ko-KR")}</span>
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

      {/* ── Main Content ── */}
      <main className="max-w-[430px] mx-auto px-[20px] pt-[8px]">
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
          <div className="flex flex-col items-center justify-center py-[80px]">
            <p
              className="text-[16px] mb-[16px]"
              style={{ fontFamily: "var(--font-body)", color: "var(--color-text-primary)" }}
            >
              불러오지 못했어요
            </p>
            <button
              type="button"
              onClick={() => loadFeed(1, false)}
              className="px-[20px] py-[10px] text-[14px] font-medium"
              style={{
                fontFamily: "var(--font-body)",
                borderRadius: "var(--radius-full)",
                border: "1px solid var(--color-accent)",
                color: "var(--color-accent)",
                backgroundColor: "transparent",
              }}
            >
              다시 시도
            </button>
          </div>
        )}

        {/* Empty */}
        {status === "empty" && (
          <div className="flex flex-col items-center justify-center py-[80px]">
            <svg width="48" height="48" viewBox="0 0 64 64" fill="none" className="mb-[16px]">
              <rect x="20" y="8" width="4" height="40" rx="2" fill="var(--color-border)" />
              <rect x="40" y="8" width="4" height="40" rx="2" fill="var(--color-border)" />
              <path d="M16 8h32" stroke="var(--color-border)" strokeWidth="4" strokeLinecap="round" />
            </svg>
            <p
              className="text-[15px] mb-[4px]"
              style={{ fontFamily: "var(--font-body)", color: "var(--color-text-primary)" }}
            >
              조건에 맞는 코디가 없어요
            </p>
            <button
              type="button"
              onClick={() => {
                setActiveTpo("all");
                setBudgetMin(BUDGET_MIN_DEFAULT);
                setBudgetMax(BUDGET_MAX_DEFAULT);
                setVerifiedOnly(false);
                setPreferredBrands([]);
              }}
              className="mt-[12px] px-[20px] py-[10px] text-[14px] font-medium"
              style={{
                fontFamily: "var(--font-body)",
                borderRadius: "var(--radius-full)",
                backgroundColor: "var(--color-accent)",
                color: "#FFFFFF",
              }}
            >
              필터 초기화
            </button>
          </div>
        )}

        {/* Success */}
        {status === "success" && (
          <>
            {todayPick && (
              <TodayColorFitCard
                outfit={todayPick}
                isSaved={savedIds.has(todayPick.id)}
                onTap={handleCardTap}
                onSaveToggle={handleSaveToggle}
              />
            )}

            {feedOutfits.map((outfit, i) => (
              <OutfitCard
                key={outfit.id}
                id={outfit.id}
                imageUrl={outfit.image_url ?? "/placeholder-outfit.png"}
                items={outfit.items ?? []}
                title={outfit.reasons[0] ?? "코디 추천"}
                totalPrice={outfit.total_price ?? 0}
                reason={outfit.reasons[1] ?? ""}
                scores={{ pcf: outfit.scores?.pcf ?? 0, of: outfit.scores?.of ?? 0 }}
                itemCount={outfit.items?.length ?? 0}
                isSaved={savedIds.has(outfit.id)}
                index={i}
                onTap={handleCardTap}
                onSaveToggle={handleSaveToggle}
                onDislike={handleDislike}
              />
            ))}

            <div ref={sentinelRef} className="h-[1px]" />

            {loadingMore && (
              <div className="py-[16px]">
                <SkeletonCard />
              </div>
            )}
          </>
        )}

        {/* Bottom padding for tab bar */}
        <div style={{ height: "calc(72px + env(safe-area-inset-bottom, 0px))" }} />
      </main>

      {/* Toast */}
      <AnimatePresence>
        {toast && (
          <motion.div
            className="fixed z-50 left-1/2 -translate-x-1/2"
            style={{
              bottom: "calc(72px + env(safe-area-inset-bottom, 0px))",
              backgroundColor: "var(--color-text-primary)",
              color: "var(--color-bg-primary)",
              fontFamily: "var(--font-body)",
              fontSize: "13px",
              padding: "8px 16px",
              borderRadius: "var(--radius-full)",
              boxShadow: "0 4px 12px rgba(0,0,0,0.15)",
            }}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 12 }}
            transition={{ duration: 0.15 }}
          >
            {toast}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
