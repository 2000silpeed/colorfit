"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import Image from "next/image";
import { motion, useScroll, useTransform, useReducedMotion } from "framer-motion";
import {
  fetchOutfitDetail,
  postReaction,
  type OutfitDetailResponse,
  type ScoresResponse,
} from "@/lib/api";

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
      <div className="w-[56px] shrink-0">
        <span className="font-body text-[13px] text-text-secondary">{label}</span>
        <span className="font-body text-[11px] text-text-tertiary ml-[4px] hidden sm:inline">
          {fullLabel}
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

export default function OutfitDetailPage() {
  const params = useParams();
  const router = useRouter();
  const prefersReducedMotion = useReducedMotion();
  const outfitId = params.id as string;

  const [outfit, setOutfit] = useState<OutfitDetailResponse | null>(null);
  const [status, setStatus] = useState<"loading" | "success" | "error">("loading");
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


  const userId =
    typeof window !== "undefined"
      ? localStorage.getItem("colorfit_user_id") ?? ""
      : "";

  const handleSave = useCallback(() => {
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
  }, [outfitId, userId]);

  const handleBack = useCallback(() => {
    router.back();
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
        style={{ opacity: prefersReducedMotion ? 1 : headerOpacity }}
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
      <div ref={heroRef} className="relative w-full overflow-hidden" style={{ aspectRatio: "3/4" }}>
        {/* 뒤로가기 버튼 (히어로 위) */}
        <button
          type="button"
          onClick={handleBack}
          className="absolute top-[12px] left-[12px] z-20 w-[36px] h-[36px] rounded-full bg-black/30 flex items-center justify-center backdrop-blur-sm"
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
          className="absolute top-[12px] right-[12px] z-20 w-[36px] h-[36px] rounded-full bg-black/30 flex items-center justify-center backdrop-blur-sm"
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
            className="object-cover"
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
              {sortedItems.map((item) => (
                <a
                  key={item.id}
                  href={item.mall_url ?? "#"}
                  target={item.mall_url ? "_blank" : undefined}
                  rel={item.mall_url ? "noopener noreferrer" : undefined}
                  className="shrink-0 w-[80px] group"
                >
                  <div className="w-[80px] h-[80px] rounded-[var(--radius-md)] overflow-hidden bg-bg-secondary border border-border">
                    {item.image_url ? (
                      <Image
                        src={item.image_url}
                        alt={item.name ?? "아이템"}
                        width={80}
                        height={80}
                        className="object-cover w-full h-full"
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
                  <p className="font-body text-[11px] text-text-secondary mt-[6px] line-clamp-2 group-hover:text-accent transition-colors">
                    {item.brand && (
                      <span className="text-text-tertiary">{item.brand} </span>
                    )}
                    {item.name ?? item.category ?? "아이템"}
                  </p>
                  {item.price != null && (
                    <p className="font-body text-[11px] text-text-primary font-medium">
                      {"\u20A9"}{formatPrice(item.price)}
                    </p>
                  )}
                </a>
              ))}
            </div>
          </section>
        )}

        {/* 하단 여백 (CTA 겹침 방지) */}
        <div className="h-[100px]" />
      </main>

      {/* ── 하단 CTA ── */}
      <div className="fixed bottom-0 left-0 right-0 z-30 bg-bg-primary/95 backdrop-blur-sm border-t border-border">
        <div className="flex gap-[12px] px-[20px] py-[12px] max-w-[768px] mx-auto">
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
            className="flex-1 py-[14px] rounded-full bg-accent text-white text-[15px] font-body font-medium opacity-40 cursor-not-allowed"
            disabled
            title="준비 중"
          >
            A vs B 비교
          </button>
        </div>
      </div>
    </div>
  );
}
