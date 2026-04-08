"use client";

import { useState, useEffect, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import Image from "next/image";
import { motion, useReducedMotion } from "framer-motion";
import {
  type ItemDetail,
  type PriceEntry,
  type SimilarProduct,
  fetchItemDetail,
  fetchSimilarItems,
} from "@/lib/api";

/* ── 가격 포맷 ── */
function formatPrice(price: number): string {
  return price.toLocaleString("ko-KR");
}

/* ── 스켈레톤 ── */
function ItemSkeleton() {
  return (
    <div className="min-h-screen bg-bg-primary">
      <div className="w-full bg-[#E0DCD7] animate-pulse" style={{ aspectRatio: "1/1" }} />
      <div className="px-[20px] pt-[24px]">
        <div className="h-[14px] w-1/3 rounded bg-[#E0DCD7] animate-pulse" />
        <div className="mt-[8px] h-[22px] w-3/4 rounded bg-[#E0DCD7] animate-pulse" />
        <div className="mt-[12px] h-[28px] w-1/3 rounded bg-[#E0DCD7] animate-pulse" />
        <div className="mt-[32px] h-[16px] w-1/2 rounded bg-[#E0DCD7] animate-pulse" />
        <div className="mt-[12px] space-y-[8px]">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-[48px] rounded-[8px] bg-[#E0DCD7] animate-pulse" />
          ))}
        </div>
      </div>
    </div>
  );
}

/* ── 가격 비교 행 ── */
function PriceRow({ entry }: { entry: PriceEntry }) {
  return (
    <a
      href={entry.mall_url}
      target="_blank"
      rel="noopener noreferrer"
      className={`flex items-center justify-between px-[16px] py-[12px] rounded-[8px] transition-colors ${
        entry.is_lowest
          ? "bg-[#F0EDE8] border border-accent/20"
          : "bg-bg-secondary border border-border"
      }`}
    >
      <div className="flex items-center gap-[10px]">
        <span className="font-body text-[14px] text-text-primary font-medium">
          {entry.mall_name}
        </span>
        {entry.is_lowest && (
          <span className="bg-accent text-white text-[11px] font-body font-medium px-[8px] py-[2px] rounded-full">
            최저가
          </span>
        )}
      </div>
      <div className="flex items-center gap-[8px]">
        <span className={`font-body text-[15px] font-semibold ${
          entry.is_lowest ? "text-accent" : "text-text-primary"
        }`}>
          {"\u20A9"}{formatPrice(entry.price)}
        </span>
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--color-text-tertiary)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
          <polyline points="15 3 21 3 21 9" />
          <line x1="10" y1="14" x2="21" y2="3" />
        </svg>
      </div>
    </a>
  );
}

/* ── 유사 상품 카드 ── */
function SimilarCard({ product }: { product: SimilarProduct }) {
  const prefersReducedMotion = useReducedMotion();

  return (
    <motion.a
      href={product.mall_url ?? "#"}
      target={product.mall_url ? "_blank" : undefined}
      rel={product.mall_url ? "noopener noreferrer" : undefined}
      className="block group"
      initial={prefersReducedMotion ? {} : { opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <div className="relative w-full rounded-[12px] overflow-hidden bg-bg-secondary border border-border" style={{ aspectRatio: "1/1" }}>
        {product.image_url ? (
          <Image
            src={product.image_url}
            alt={product.name ?? "유사 상품"}
            fill
            sizes="(max-width: 768px) 50vw, 25vw"
            className="object-cover group-hover:scale-105 transition-transform duration-300"
            loading="lazy"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="var(--color-text-tertiary)" strokeWidth="1.5">
              <rect x="3" y="3" width="18" height="18" rx="2" />
              <circle cx="8.5" cy="8.5" r="1.5" />
              <path d="M21 15l-5-5L5 21" />
            </svg>
          </div>
        )}
        <div className="absolute top-[8px] right-[8px] bg-black/50 text-white text-[11px] font-body font-medium px-[8px] py-[3px] rounded-full backdrop-blur-sm">
          {product.similarity}%
        </div>
      </div>
      <div className="mt-[8px]">
        {product.brand && (
          <p className="font-body text-[11px] text-text-tertiary">{product.brand}</p>
        )}
        <p className="font-body text-[13px] text-text-primary line-clamp-2 leading-[1.4]">
          {product.name ?? "상품"}
        </p>
        {product.price != null && (
          <p className="font-body text-[14px] text-text-primary font-semibold mt-[4px]">
            {"\u20A9"}{formatPrice(product.price)}
          </p>
        )}
      </div>
    </motion.a>
  );
}

export default function ItemDetailPage() {
  const params = useParams();
  const router = useRouter();
  const prefersReducedMotion = useReducedMotion();
  const itemId = params.id as string;

  const [item, setItem] = useState<ItemDetail | null>(null);
  const [similar, setSimilar] = useState<SimilarProduct[]>([]);
  const [status, setStatus] = useState<"loading" | "success" | "error">("loading");

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const [detail, similarRes] = await Promise.all([
          fetchItemDetail(itemId),
          fetchSimilarItems(itemId),
        ]);
        if (!cancelled) {
          setItem(detail);
          setSimilar(similarRes.similar);
          setStatus("success");
        }
      } catch {
        if (!cancelled) setStatus("error");
      }
    }

    load();
    return () => { cancelled = true; };
  }, [itemId]);

  const handleBack = useCallback(() => {
    if (window.history.length > 1) {
      router.back();
    } else {
      router.push("/feed");
    }
  }, [router]);

  if (status === "loading") return <ItemSkeleton />;

  if (status === "error" || !item) {
    return (
      <div className="min-h-screen bg-bg-primary flex flex-col items-center justify-center px-[20px]">
        <p className="font-body text-[16px] text-text-primary mb-[16px]">
          상품을 불러오지 못했어요
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

  const lowestEntry = item.price_entries.find((e) => e.is_lowest);

  return (
    <div className="min-h-screen bg-bg-primary">
      {/* ── 헤더 ── */}
      <header className="sticky top-0 z-40 bg-bg-primary/95 backdrop-blur-sm border-b border-border">
        <div className="flex items-center justify-between px-[20px] h-[52px] max-w-[768px] mx-auto">
          <button type="button" onClick={handleBack} aria-label="뒤로가기">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="var(--color-text-primary)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="15 18 9 12 15 6" />
            </svg>
          </button>
          <span className="font-display text-[16px] text-text-primary line-clamp-1 max-w-[240px]">
            {item.name ?? "상품 상세"}
          </span>
          <div className="w-[24px]" />
        </div>
      </header>

      {/* ── 상품 이미지 (1:1) ── */}
      <div className="relative w-full bg-bg-secondary" style={{ aspectRatio: "1/1" }}>
        {item.image_url ? (
          <Image
            src={item.image_url}
            alt={item.name ?? "상품 이미지"}
            fill
            sizes="100vw"
            className="object-cover"
            priority
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--color-text-tertiary)" strokeWidth="1.5">
              <rect x="3" y="3" width="18" height="18" rx="2" />
              <circle cx="8.5" cy="8.5" r="1.5" />
              <path d="M21 15l-5-5L5 21" />
            </svg>
          </div>
        )}

      </div>

      {/* ── 메인 콘텐츠 ── */}
      <main className="max-w-[768px] mx-auto px-[20px] pt-[24px]">
        {/* 브랜드 + 상품명 + 가격 */}
        <div>
          {item.brand && (
            <p className="font-body text-[13px] text-text-secondary">{item.brand}</p>
          )}
          <h1 className="font-display text-[22px] text-text-primary leading-[1.3] mt-[4px]">
            {item.name ?? "상품"}
          </h1>
          <div className="flex items-baseline gap-[8px] mt-[12px]">
            <span className="font-body text-[24px] text-text-primary font-bold">
              {item.price != null ? `\u20A9${formatPrice(item.price)}` : "가격 미정"}
            </span>
            {lowestEntry && lowestEntry.price !== item.price && (
              <span className="font-body text-[14px] text-accent font-medium">
                최저 {"\u20A9"}{formatPrice(lowestEntry.price)}
              </span>
            )}
          </div>
        </div>

        {/* 카테고리 + 실루엣 태그 */}
        <div className="flex flex-wrap gap-[6px] mt-[16px]">
          {item.category && (
            <span className="bg-bg-secondary text-text-secondary text-[12px] font-body rounded-full px-[10px] py-[4px] border border-border">
              {item.category}
            </span>
          )}
          {item.silhouette && (
            <span className="bg-bg-secondary text-text-secondary text-[12px] font-body rounded-full px-[10px] py-[4px] border border-border">
              {item.silhouette}
            </span>
          )}
          {item.tone_id && (
            <span className="bg-accent/10 text-accent text-[12px] font-body rounded-full px-[10px] py-[4px]">
              {item.tone_id.replace(/_/g, " ")}
            </span>
          )}
        </div>

        {/* ── 가격 비교 테이블 ── */}
        {item.price_entries.length > 0 && (
          <section className="mt-[32px]">
            <h2 className="font-display text-[18px] text-text-primary mb-[12px]">
              가격 비교
            </h2>
            <div className="space-y-[8px]">
              {item.price_entries.map((entry, i) => (
                <PriceRow key={`${entry.mall_name}-${i}`} entry={entry} />
              ))}
            </div>
          </section>
        )}

        {/* ── 유사 상품 섹션 ── */}
        {similar.length > 0 && (
          <section className="mt-[32px]">
            <h2 className="font-display text-[18px] text-text-primary mb-[12px]">
              유사 상품
            </h2>
            <div className="grid grid-cols-2 gap-[12px]">
              {similar.map((product) => (
                <SimilarCard key={product.id} product={product} />
              ))}
            </div>
          </section>
        )}

        {/* 하단 여백 (CTA 겹침 방지) */}
        <div className="h-[100px]" />
      </main>

      {/* ── 하단 CTA ── */}
      {item.mall_url && (
        <div className="fixed bottom-0 left-0 right-0 z-30 bg-bg-primary/95 backdrop-blur-sm border-t border-border">
          <div className="px-[20px] py-[12px] max-w-[768px] mx-auto">
            <a
              href={item.mall_url}
              target="_blank"
              rel="noopener noreferrer"
              className="block w-full py-[14px] rounded-full bg-accent text-white text-center text-[15px] font-body font-medium"
            >
              {item.mall_name ? `${item.mall_name}에서 구매하기` : "구매하러 가기"}
            </a>
          </div>
        </div>
      )}
    </div>
  );
}
