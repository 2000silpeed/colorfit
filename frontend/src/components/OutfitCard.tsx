"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import Image from "next/image";
import { motion, useReducedMotion } from "framer-motion";
import type { FeedItemBrief } from "@/lib/api";

interface OutfitScores {
  pcf: number;
  of: number;
}

const STYLE_TAG_LABEL: Record<string, string> = {
  formal: "Formal",
  classic: "Classic",
  smart_casual: "Smart Casual",
  casual: "Casual",
  sporty: "Sporty",
  street: "Street",
};

interface OutfitCardProps {
  id: string;
  imageUrl: string;
  items: FeedItemBrief[];
  title: string;
  totalPrice: number;
  originalPrice?: number;
  reason: string;
  scores: OutfitScores;
  itemCount: number;
  isSaved?: boolean;
  index?: number;
  onTap?: (id: string) => void;
  onSaveToggle?: (id: string) => void;
  onDislike?: (id: string) => void;
}

function formatPrice(price: number): string {
  if (price >= 10000) {
    const man = Math.floor(price / 10000);
    const remainder = price % 10000;
    if (remainder === 0) return `${man}만`;
    return `${man}만${remainder.toLocaleString("ko-KR")}`;
  }
  return `${price.toLocaleString("ko-KR")}`;
}

const GROUP_ORDER: Record<string, number> = {
  top: 0,
  onepiece: 1,
  outer: 2,
  bottom: 3,
  shoes: 4,
  bag: 5,
  acc: 6,
};

function sortItemsByGroup(items: FeedItemBrief[]): FeedItemBrief[] {
  return [...items].sort((a, b) => {
    const orderA = GROUP_ORDER[a.group ?? ""] ?? 99;
    const orderB = GROUP_ORDER[b.group ?? ""] ?? 99;
    return orderA - orderB;
  });
}

const SWIPE_THRESHOLD = 100;
const DOUBLE_TAP_DELAY = 250;

export default function OutfitCard({
  id,
  imageUrl,
  items,
  title,
  totalPrice,
  originalPrice,
  reason,
  scores,
  itemCount,
  isSaved = false,
  index = 0,
  onTap,
  onSaveToggle,
  onDislike,
}: OutfitCardProps) {
  const prefersReducedMotion = useReducedMotion();
  const [saved, setSaved] = useState(isSaved);
  const [showHeartPop, setShowHeartPop] = useState(false);
  const [dismissed, setDismissed] = useState(false);

  const tapTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const heartPopTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    setSaved(isSaved);
  }, [isSaved]);

  useEffect(() => {
    return () => {
      if (tapTimerRef.current) clearTimeout(tapTimerRef.current);
      if (heartPopTimerRef.current) clearTimeout(heartPopTimerRef.current);
    };
  }, []);

  const handleSaveToggle = useCallback(
    (e: React.MouseEvent) => {
      e.stopPropagation();
      setSaved((prev) => !prev);
      onSaveToggle?.(id);
    },
    [id, onSaveToggle],
  );

  const handleDoubleTap = useCallback(() => {
    if (saved) return;
    setSaved(true);
    setShowHeartPop(true);
    onSaveToggle?.(id);
    heartPopTimerRef.current = setTimeout(() => setShowHeartPop(false), 600);
  }, [id, saved, onSaveToggle]);

  const handleCardClick = useCallback(() => {
    if (tapTimerRef.current) {
      clearTimeout(tapTimerRef.current);
      tapTimerRef.current = null;
      handleDoubleTap();
    } else {
      tapTimerRef.current = setTimeout(() => {
        tapTimerRef.current = null;
        onTap?.(id);
      }, DOUBLE_TAP_DELAY);
    }
  }, [id, onTap, handleDoubleTap]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        onTap?.(id);
      }
    },
    [id, onTap],
  );

  const handleDragEnd = useCallback(
    (_: unknown, info: { offset: { x: number } }) => {
      if (info.offset.x < -SWIPE_THRESHOLD) {
        setDismissed(true);
        onDislike?.(id);
      }
    },
    [id, onDislike],
  );

  if (dismissed) return null;

  const hasDiscount = originalPrice && originalPrice > totalPrice;
  const discountRate = hasDiscount
    ? Math.round((1 - totalPrice / originalPrice) * 100)
    : 0;

  const sortedItems = sortItemsByGroup(items).filter((it) => it.image_url);
  const displayItems = sortedItems.slice(0, 3);
  const useGrid = displayItems.length >= 2;

  return (
    <motion.article
      className="px-[20px] mb-[20px] cursor-pointer"
      tabIndex={0}
      role="link"
      initial={prefersReducedMotion ? false : { y: 30, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={
        prefersReducedMotion
          ? { duration: 0 }
          : { duration: 0.4, delay: index * 0.1, ease: "easeOut" }
      }
      onClick={handleCardClick}
      onKeyDown={handleKeyDown}
      drag="x"
      dragConstraints={{ left: 0, right: 0 }}
      dragElastic={0.3}
      onDragEnd={handleDragEnd}
      whileDrag={{ cursor: "grabbing" }}
    >
      {/* Image Container */}
      <div className="relative w-full rounded-[var(--radius-lg)] overflow-hidden bg-[#F0EDE8]"
        style={{ aspectRatio: "1/1" }}
      >
        {/* 메인 이미지 (항상 전체 배경) */}
        <Image
          src={displayItems[0]?.image_url ?? imageUrl}
          alt={displayItems[0]?.category ?? title}
          fill
          sizes="(max-width: 768px) 100vw, 430px"
          className="object-contain"
          {...(index === 0
            ? { priority: true, fetchPriority: "high" as const }
            : { loading: "lazy" as const })}
        />

        {/* 하단 그라데이션 */}
        {useGrid && (
          <div className="absolute bottom-0 left-0 right-0 h-[80px] bg-gradient-to-t from-black/30 to-transparent" />
        )}

        {/* 서브 아이템 썸네일 - 하단 우측 */}
        {useGrid && (
          <div className="absolute bottom-[10px] right-[10px] flex gap-[8px] z-10">
            {displayItems.slice(1, 3).map((item, i) => (
              <div
                key={i}
                className="relative w-[76px] h-[76px] rounded-[12px] overflow-hidden bg-white/90 shadow-[0_2px_8px_rgba(0,0,0,0.15)] ring-1 ring-white/50"
              >
                <Image
                  src={item.image_url!}
                  alt={item.category ?? "서브 아이템"}
                  fill
                  sizes="76px"
                  className="object-cover"
                  loading="lazy"
                />
              </div>
            ))}
          </div>
        )}

        {/* 추천 브랜드 뱃지 - 이미지 좌상단 */}
        {(() => {
          const verifiedBrands = items
            .filter((it) => it.is_verified_brand && it.brand)
            .filter((it, i, arr) => arr.findIndex((a) => a.brand === it.brand) === i)
            .slice(0, 2);
          return verifiedBrands.length > 0 ? (
            <div className="absolute top-[10px] left-[10px] flex flex-col gap-[4px] z-10">
              {verifiedBrands.map((it) => (
                <span
                  key={it.brand}
                  className="inline-flex items-center gap-[4px] text-[12px] font-body font-medium rounded-[8px] px-[10px] py-[5px] backdrop-blur-md shadow-sm"
                  style={{ backgroundColor: "rgba(150, 79, 76, 0.85)", color: "#FFFFFF" }}
                >
                  <svg width="12" height="12" viewBox="0 0 16 16" fill="currentColor">
                    <path d="M8 0a8 8 0 1 1 0 16A8 8 0 0 1 8 0zm3.41 5.09L7.2 9.3 5.3 7.4a.75.75 0 0 0-1.1 1.02l.08.08 2.5 2.5a.75.75 0 0 0 1.02.08l.08-.08 4.8-4.8a.75.75 0 0 0-1.1-1.02l-.07.01z" />
                  </svg>
                  {it.brand}
                </span>
              ))}
            </div>
          ) : null;
        })()}

        {/* 메인 카테고리 라벨 */}
        {useGrid && displayItems[0]?.category && (
          <span className="absolute bottom-[12px] left-[12px] bg-white/80 text-text-primary text-[11px] font-body rounded-full px-[8px] py-[3px] z-10 backdrop-blur-sm">
            {displayItems[0].category} +{displayItems.length - 1}
          </span>
        )}

        {/* Save Heart - top right */}
        <button
          type="button"
          onClick={handleSaveToggle}
          className="absolute top-[4px] right-[4px] w-[44px] h-[44px] flex items-center justify-center z-10"
          aria-label={saved ? "저장 취소" : "저장"}
          aria-pressed={saved}
        >
          <motion.svg
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill={saved ? "var(--color-accent)" : "none"}
            stroke={saved ? "var(--color-accent)" : "#FFFFFF"}
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            style={{ filter: saved ? "none" : "drop-shadow(0 1px 3px rgba(0,0,0,0.4))" }}
            animate={
              saved
                ? { scale: [0.8, 1.2, 1.0] }
                : { scale: 1 }
            }
            transition={{ duration: 0.2 }}
          >
            <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
          </motion.svg>
        </button>

        {/* Double-tap heart pop animation */}
        {showHeartPop && (
          <motion.div
            className="absolute inset-0 flex items-center justify-center pointer-events-none z-10"
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: [0.8, 1.4, 1.0], opacity: [0, 1, 0] }}
            transition={{ duration: 0.6 }}
          >
            <svg
              width="64"
              height="64"
              viewBox="0 0 24 24"
              fill="var(--color-accent)"
              stroke="none"
            >
              <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
            </svg>
          </motion.div>
        )}
      </div>

      {/* Title */}
      <h3 className="font-display text-[16px] text-text-primary mt-[12px] line-clamp-1" title={title}>
        {title}
      </h3>

      {/* Price */}
      <div className="flex items-center gap-[6px] mt-[4px]">
        {hasDiscount && (
          <>
            <span className="font-body text-[15px] text-text-secondary line-through">
              {formatPrice(originalPrice)}
            </span>
            <span className="font-body text-[15px] text-accent font-bold">
              {discountRate}%
            </span>
          </>
        )}
        <span className={`font-body text-[15px] font-bold ${hasDiscount ? "text-accent" : "text-text-primary"}`}>
          {"\u20A9"}{formatPrice(totalPrice)}
        </span>
      </div>

      {/* Reason */}
      <p className="font-body text-[13px] text-text-secondary mt-[4px] line-clamp-1" title={reason}>
        {reason}
      </p>

      {/* Badges */}
      <div className="flex flex-wrap gap-[6px] mt-[8px]">
        {items[0]?.style_tag && (
          <span className="bg-bg-secondary text-text-secondary text-[11px] font-body rounded-full px-[8px] py-[3px]">
            {STYLE_TAG_LABEL[items[0].style_tag] ?? items[0].style_tag}
          </span>
        )}
        <span
          className="bg-bg-secondary text-text-primary text-[11px] font-body rounded-full px-[8px] py-[3px]"
          title="퍼스널컬러 적합도"
        >
          컬러 {Math.round(scores.pcf)}
        </span>
        <span
          className="bg-bg-secondary text-text-primary text-[11px] font-body rounded-full px-[8px] py-[3px]"
          title="TPO 적합도"
        >
          TPO {Math.round(scores.of)}
        </span>
      </div>
    </motion.article>
  );
}
