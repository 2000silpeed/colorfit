"use client";

import { useState, useEffect, useCallback, useRef, startTransition } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Image from "next/image";
import { motion, AnimatePresence, useReducedMotion } from "framer-motion";
import {
  fetchClosetOutfits,
  postReaction,
  type ClosetOutfit,
  type ClosetOutfitItem,
} from "@/lib/api";
import { isLoggedIn } from "@/lib/auth";

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

const CATEGORY_LABEL: Record<string, string> = {
  top: "상의",
  bottom: "하의",
  outer: "아우터",
  onepiece: "원피스",
  shoes: "신발",
  bag: "가방",
  acc: "액세서리",
};

const SCORE_AXIS: { key: string; label: string; color: string }[] = [
  { key: "pcf", label: "컬러", color: "#964F4C" },
  { key: "of", label: "TPO", color: "#4F97A3" },
  { key: "ch", label: "조화", color: "#DDB67D" },
  { key: "pe", label: "가성비", color: "#D1933F" },
  { key: "sf", label: "스타일", color: "#6B5876" },
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

/* ── 스켈레톤 카드 ── */
function SkeletonCard() {
  return (
    <div className="bg-[var(--color-surface)] rounded-[var(--radius-lg)] p-[16px] mb-[16px]">
      <div className="flex gap-[8px] mb-[12px]">
        {[0, 1, 2].map((i) => (
          <div
            key={i}
            className="w-[80px] h-[100px] rounded-[var(--radius-md)] bg-[#E0DCD7] animate-pulse"
          />
        ))}
      </div>
      <div className="h-[14px] w-3/4 rounded bg-[#E0DCD7] animate-pulse mb-[8px]" />
      <div className="h-[12px] w-1/2 rounded bg-[#E0DCD7] animate-pulse" />
    </div>
  );
}

/* ── 아이템 썸네일 ── */
interface ItemThumbProps {
  item: ClosetOutfitItem;
}

function ItemThumb({ item }: ItemThumbProps) {
  const isMyItem = item.source === "closet";
  return (
    <div className="relative shrink-0">
      <div
        className={`relative w-[80px] h-[100px] rounded-[var(--radius-md)] overflow-hidden bg-[var(--color-surface)] ${
          isMyItem ? "ring-2 ring-[var(--color-accent)]" : ""
        }`}
      >
        {item.image_url ? (
          <Image
            src={item.image_url}
            alt={item.category ?? "아이템"}
            fill
            sizes="80px"
            className="object-cover"
            loading="lazy"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-[var(--color-text-tertiary)] text-[11px]">
            No img
          </div>
        )}
      </div>
      {isMyItem && (
        <span className="absolute -top-[6px] -right-[6px] bg-[var(--color-accent)] text-white text-[10px] font-body font-medium px-[6px] py-[2px] rounded-full z-10">
          내 옷
        </span>
      )}
      {item.category && (
        <p className="text-[11px] text-[var(--color-text-tertiary)] font-body mt-[4px] text-center truncate w-[80px]">
          {CATEGORY_LABEL[item.category] ?? item.category}
        </p>
      )}
    </div>
  );
}

/* ── 코디 카드 ── */
interface OutfitCardProps {
  outfit: ClosetOutfit;
  isSaved: boolean;
  index: number;
  onTap: (outfit: ClosetOutfit) => void;
  onSaveToggle: (id: string) => void;
}

function ClosetOutfitCard({ outfit, isSaved, index, onTap, onSaveToggle }: OutfitCardProps) {
  const prefersReducedMotion = useReducedMotion();
  const [saved, setSaved] = useState(isSaved);

  useEffect(() => {
    setSaved(isSaved);
  }, [isSaved]);

  const handleSave = useCallback(
    (e: React.MouseEvent) => {
      e.stopPropagation();
      setSaved((prev) => !prev);
      onSaveToggle(outfit.id);
    },
    [outfit.id, onSaveToggle],
  );

  const { purchase_summary: ps } = outfit;
  const totalScore = Math.round(outfit.total_score);

  return (
    <motion.article
      className="bg-[var(--color-surface)] rounded-[var(--radius-lg)] p-[16px] mb-[16px] cursor-pointer"
      initial={prefersReducedMotion ? false : { y: 20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={
        prefersReducedMotion
          ? { duration: 0 }
          : { duration: 0.35, delay: index * 0.06, ease: "easeOut" }
      }
      onClick={() => onTap(outfit)}
    >
      {/* 아이템 콜라주 */}
      <div className="flex gap-[8px] overflow-x-auto pb-[4px] scrollbar-hide" style={{ scrollbarWidth: "none" }}>
        {outfit.items.map((item) => (
          <ItemThumb key={item.id} item={item} />
        ))}
      </div>

      {/* 스코어 + 저장 버튼 */}
      <div className="flex items-center justify-between mt-[12px]">
        <div className="flex items-center gap-[8px]">
          <span className="text-[18px] font-display font-bold text-[var(--color-text-primary)]">
            {totalScore}점
          </span>
          <div className="flex gap-[4px]">
            {SCORE_AXIS.map((axis) => {
              const val = outfit.scores[axis.key];
              if (val == null) return null;
              return (
                <span
                  key={axis.key}
                  className="text-[11px] font-body px-[6px] py-[2px] rounded-full"
                  style={{ backgroundColor: `${axis.color}18`, color: axis.color }}
                >
                  {axis.label} {Math.round(val)}
                </span>
              );
            })}
          </div>
        </div>
        <button
          type="button"
          onClick={handleSave}
          className="w-[36px] h-[36px] flex items-center justify-center"
          aria-label={saved ? "저장 취소" : "저장"}
          aria-pressed={saved}
        >
          <motion.svg
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill={saved ? "var(--color-accent)" : "none"}
            stroke={saved ? "var(--color-accent)" : "var(--color-text-tertiary)"}
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            animate={saved ? { scale: [0.8, 1.2, 1.0] } : { scale: 1 }}
            transition={{ duration: 0.2 }}
          >
            <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
          </motion.svg>
        </button>
      </div>

      {/* 추천 이유 */}
      {outfit.reasons.length > 0 && (
        <p className="text-[13px] font-body text-[var(--color-text-secondary)] mt-[8px] line-clamp-2">
          {outfit.reasons[0]}
        </p>
      )}

      {/* 추가 구매 비용 */}
      <div className="flex items-center justify-between mt-[10px] pt-[10px] border-t border-[var(--color-border)]">
        <div className="flex items-center gap-[8px] text-[13px] font-body">
          <span className="text-[var(--color-text-tertiary)]">
            내 옷 {ps.my_items_count}벌
          </span>
          <span className="text-[var(--color-text-tertiary)]">·</span>
          <span className="text-[var(--color-text-secondary)]">
            추가 구매 {ps.purchase_items_count}벌
          </span>
        </div>
        <span className="text-[14px] font-body font-bold text-[var(--color-accent)]">
          {ps.purchase_total > 0
            ? `+₩${formatPrice(ps.purchase_total)}`
            : "추가 비용 없음"}
        </span>
      </div>
    </motion.article>
  );
}

/* ── 메인 페이지 ── */
export default function ClosetOutfitsPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const itemId = searchParams.get("item_id") ?? "";

  /* 상태 */
  const [activeTpo, setActiveTpo] = useState("all");
  const [outfits, setOutfits] = useState<ClosetOutfit[]>([]);
  const [status, setStatus] = useState<"loading" | "success" | "empty" | "error">("loading");
  const [savedIds, setSavedIds] = useState<Set<string>>(new Set());

  /* 토스트 */
  const [toast, setToast] = useState<string | null>(null);
  const toastTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const showToast = useCallback((message: string) => {
    if (toastTimerRef.current) clearTimeout(toastTimerRef.current);
    setToast(message);
    toastTimerRef.current = setTimeout(() => setToast(null), 1500);
  }, []);

  useEffect(() => {
    return () => {
      if (toastTimerRef.current) clearTimeout(toastTimerRef.current);
    };
  }, []);

  /* userId */
  const userId = (() => {
    if (typeof window === "undefined") return "";
    let id = localStorage.getItem("colorfit_user_id");
    if (!id) {
      id = crypto.randomUUID();
      localStorage.setItem("colorfit_user_id", id);
    }
    return id;
  })();

  /* 데이터 로드 */
  const loadOutfits = useCallback(async () => {
    if (!itemId || !userId) return;
    startTransition(() => setStatus("loading"));

    try {
      const data = await fetchClosetOutfits(
        userId,
        itemId,
        activeTpo === "all" ? undefined : activeTpo,
      );
      startTransition(() => {
        setOutfits(data.outfits);
        setStatus(data.outfits.length === 0 ? "empty" : "success");
      });
    } catch {
      startTransition(() => setStatus("error"));
    }
  }, [userId, itemId, activeTpo]);

  useEffect(() => {
    if (itemId) loadOutfits();
  }, [itemId, loadOutfits]);

  /* item_id 없으면 옷장으로 리다이렉트 */
  useEffect(() => {
    if (!itemId) {
      router.replace("/closet");
    }
  }, [itemId, router]);

  /* save/dislike */
  const handleSaveToggle = useCallback(
    (id: string) => {
      if (!isLoggedIn()) {
        showToast("로그인이 필요해요");
        router.push("/login?returnUrl=/closet/outfits");
        return;
      }
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
    },
    [savedIds, userId, showToast, router],
  );

  const handleCardTap = useCallback(
    (outfit: ClosetOutfit) => {
      const dbOutfitId = outfit.db_outfit_id ?? outfit.id;
      router.push(`/outfit/${dbOutfitId}?closet_item_id=${itemId}`);
    },
    [router, itemId],
  );

  if (!itemId) return null;

  return (
    <div className="min-h-screen bg-[var(--color-bg)]">
      {/* ── 헤더 ── */}
      <header className="sticky top-0 z-30 bg-[var(--color-bg)]/95 backdrop-blur-sm">
        <div className="flex items-center px-[20px] h-[52px] max-w-[768px] mx-auto gap-[12px]">
          <button
            type="button"
            onClick={() => router.back()}
            className="w-[44px] h-[44px] flex items-center justify-center -ml-[8px]"
            aria-label="뒤로 가기"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--color-text-primary)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="15 18 9 12 15 6" />
            </svg>
          </button>
          <span className="font-display text-[18px] text-[var(--color-text-primary)] font-bold">
            코디 완성
          </span>
        </div>

        {/* ── TPO 필터 탭 ── */}
        <div
          className="flex gap-[8px] px-[20px] pb-[12px] overflow-x-auto scrollbar-hide max-w-[768px] mx-auto"
          style={{ scrollbarWidth: "none" }}
        >
          {TPO_TABS.map((tab) => (
            <button
              key={tab.id}
              type="button"
              onClick={() => setActiveTpo(tab.id)}
              className={`shrink-0 min-h-[44px] px-[16px] py-[12px] rounded-full text-[14px] font-body transition-colors whitespace-nowrap ${
                activeTpo === tab.id
                  ? "bg-[var(--color-accent)] text-white"
                  : "bg-[var(--color-surface)] text-[var(--color-text-secondary)] border border-[var(--color-border)]"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </header>

      {/* ── 메인 콘텐츠 ── */}
      <main className="max-w-[768px] mx-auto px-[20px] pt-[8px]">
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
            <p className="font-body text-[16px] text-[var(--color-text-primary)] mb-[16px]">
              코디를 불러오지 못했어요
            </p>
            <button
              type="button"
              onClick={loadOutfits}
              className="px-[24px] py-[10px] rounded-full border border-[var(--color-accent)] text-[var(--color-accent)] text-[14px] font-body"
            >
              다시 시도
            </button>
          </div>
        )}

        {/* Empty */}
        {status === "empty" && (
          <div className="flex flex-col items-center justify-center py-[80px]">
            <svg width="64" height="64" viewBox="0 0 64 64" fill="none" className="mb-[16px]">
              <rect x="20" y="8" width="4" height="40" rx="2" fill="var(--color-border)" />
              <rect x="40" y="8" width="4" height="40" rx="2" fill="var(--color-border)" />
              <path d="M16 8h32" stroke="var(--color-border)" strokeWidth="4" strokeLinecap="round" />
            </svg>
            <p className="font-body text-[16px] text-[var(--color-text-primary)] mb-[4px]">
              매칭되는 코디가 없어요
            </p>
            <p className="font-body text-[13px] text-[var(--color-text-tertiary)] mb-[16px]">
              다른 TPO를 선택해보세요
            </p>
            {activeTpo !== "all" && (
              <button
                type="button"
                onClick={() => setActiveTpo("all")}
                className="px-[24px] py-[10px] rounded-full bg-[var(--color-accent)] text-white text-[14px] font-body"
              >
                전체 보기
              </button>
            )}
          </div>
        )}

        {/* Success */}
        {status === "success" && (
          <>
            <p className="text-[13px] font-body text-[var(--color-text-tertiary)] mb-[12px]">
              {outfits.length}개의 코디를 찾았어요
            </p>
            {outfits.map((outfit, i) => (
              <ClosetOutfitCard
                key={outfit.id}
                outfit={outfit}
                isSaved={savedIds.has(outfit.db_outfit_id ?? outfit.id)}
                index={i}
                onTap={handleCardTap}
                onSaveToggle={handleSaveToggle}
              />
            ))}
          </>
        )}

        {/* 하단 여백 (BottomTabBar 60px + safe-area + 토스트 여유) */}
        <div className="h-[120px]" />
      </main>

      {/* 토스트 */}
      <AnimatePresence>
        {toast && (
          <motion.div
            className="fixed bottom-[140px] left-1/2 -translate-x-1/2 z-50 bg-[#333] text-white text-[14px] font-body px-[20px] py-[10px] rounded-full shadow-lg"
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
