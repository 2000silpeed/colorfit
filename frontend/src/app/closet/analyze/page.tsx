"use client";

import { useState, useEffect, useCallback } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import Image from "next/image";
import { motion, AnimatePresence, useReducedMotion } from "framer-motion";
import {
  addClosetItem,
  analyzeClosetItem,
  fetchClosetRecommendations,
  generateTryon,
  fetchTryonUsage,
  TryonLimitError,
  type ClosetAnalyzeResponse,
  type ClosetRecommendationResponse,
  type TpoOutfitSuggestion,
  type RecommendedProduct,
  type TryonUsageResponse,
} from "@/lib/api";

type PageState = "loading" | "success" | "error";

/* ── TPO 라벨 매핑 ── */
const TPO_EMOJI: Record<string, string> = {
  commute: "\uD83D\uDCBC",
  date: "\u2764\uFE0F",
  weekend: "\u2600\uFE0F",
  campus: "\uD83C\uDF93",
  interview: "\uD83D\uDC54",
  travel: "\u2708\uFE0F",
  event: "\uD83C\uDF89",
  workout: "\uD83C\uDFCB\uFE0F",
};

/* ── 점수 → 등급 라벨 ── */
function scoreLabel(score: number): string {
  if (score >= 85) return "\uD83D\uDC4D \uD6CC\uB96D\uD574\uC694!";
  if (score >= 70) return "\uD83D\uDE0A \uC798 \uC5B4\uC6B8\uB824\uC694";
  if (score >= 50) return "\uD83E\uDD14 \uBCF4\uD1B5\uC774\uC5D0\uC694";
  return "\uD83D\uDE45 \uC544\uC26C\uC6CC\uC694";
}

/* ── 가격 포맷 ── */
function formatPrice(price: number): string {
  if (price >= 10000) {
    const man = Math.floor(price / 10000);
    const remainder = price % 10000;
    if (remainder === 0) return `${man}\uB9CC`;
    return `${man}\uB9CC${remainder.toLocaleString("ko-KR")}`;
  }
  return price.toLocaleString("ko-KR");
}

/* ── 스코어 바 컴포넌트 ── */
function ScoreBar({
  label,
  score,
  color,
  index,
}: {
  label: string;
  score: number;
  color: string;
  index: number;
}) {
  const prefersReducedMotion = useReducedMotion();
  return (
    <div className="flex items-center gap-[12px]">
      <span className="font-body text-[13px] text-text-secondary w-[40px] shrink-0">
        {label}
      </span>
      <div
        className="flex-1 h-[6px] rounded-full bg-score-track overflow-hidden"
        role="progressbar"
        aria-valuenow={Math.round(score)}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={`${label} ${Math.round(score)}점`}
      >
        <motion.div
          className="h-full rounded-full"
          style={{ backgroundColor: color }}
          initial={prefersReducedMotion ? { width: `${score}%` } : { width: 0 }}
          animate={{ width: `${score}%` }}
          transition={
            prefersReducedMotion
              ? { duration: 0 }
              : { type: "spring", stiffness: 300, damping: 30, delay: index * 0.15 }
          }
        />
      </div>
      <span className="font-body text-[13px] text-text-primary font-medium w-[32px] text-right">
        {Math.round(score)}
      </span>
    </div>
  );
}

/* ── 추천 아이템 카드 ── */
function RecommendedItemCard({ item }: { item: RecommendedProduct }) {
  return (
    <a
      href={item.mall_url ?? "#"}
      target="_blank"
      rel="noopener noreferrer"
      className="block shrink-0 w-[120px]"
    >
      <div
        className="relative w-[120px] rounded-[var(--radius-md)] overflow-hidden bg-bg-secondary"
        style={{ aspectRatio: "3/4" }}
      >
        {item.image_url ? (
          <Image
            src={item.image_url}
            alt={item.name ?? "\uCD94\uCC9C \uC544\uC774\uD15C"}
            fill
            sizes="120px"
            className="object-cover"
            loading="lazy"
          />
        ) : (
          <div className="absolute inset-0 flex items-center justify-center text-text-tertiary text-[11px] font-body">
            No Image
          </div>
        )}
      </div>
      <p className="font-body text-[11px] text-text-secondary mt-[4px] line-clamp-1">
        {item.brand}
      </p>
      <p className="font-body text-[13px] text-text-primary line-clamp-1">
        {item.name ?? "\uC0C1\uD488\uBA85 \uC5C6\uC74C"}
      </p>
      {item.price != null && (
        <p className="font-body text-[13px] text-text-primary font-medium">
          {"\u20A9"}{formatPrice(item.price)}
        </p>
      )}
    </a>
  );
}

/* ── Try-On 로딩 애니메이션 (아이템 이미지 회전) ── */
function TryOnLoadingSpinner({ itemUrls }: { itemUrls: string[] }) {
  const count = Math.min(itemUrls.length, 4);
  return (
    <div className="flex flex-col items-center gap-[16px] py-[32px]">
      <div className="relative w-[80px] h-[80px]">
        {itemUrls.slice(0, count).map((url, i) => (
          <motion.div
            key={i}
            className="absolute w-[36px] h-[36px] rounded-full overflow-hidden border-2 border-bg-primary"
            style={{
              top: "50%",
              left: "50%",
              marginTop: "-18px",
              marginLeft: "-18px",
            }}
            animate={{
              rotate: 360,
              x: Math.cos((i / count) * Math.PI * 2) * 24,
              y: Math.sin((i / count) * Math.PI * 2) * 24,
            }}
            transition={{
              rotate: { repeat: Infinity, duration: 2, ease: "linear" },
              x: { repeat: Infinity, duration: 2, ease: "linear" },
              y: { repeat: Infinity, duration: 2, ease: "linear" },
            }}
          >
            <Image src={url} alt="" width={36} height={36} className="object-cover w-full h-full" />
          </motion.div>
        ))}
      </div>
      <p className="font-body text-[14px] text-text-secondary">
        착장 이미지를 생성하고 있어요...
      </p>
    </div>
  );
}

/* ── Try-On 바텀시트 ── */
type TryOnState = "idle" | "loading" | "success" | "error" | "limit";

function TryOnBottomSheet({
  isOpen,
  onClose,
  tryonState,
  tryonImageUrl,
  itemUrls,
  onRetry,
  onUpgrade,
}: {
  isOpen: boolean;
  onClose: () => void;
  tryonState: TryOnState;
  tryonImageUrl: string;
  itemUrls: string[];
  onRetry: () => void;
  onUpgrade: () => void;
}) {
  const prefersReducedMotion = useReducedMotion();

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* 오버레이 */}
          <motion.div
            className="fixed inset-0 bg-black/40 z-40"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
          />
          {/* 시트 */}
          <motion.div
            role="dialog"
            aria-modal="true"
            aria-label="AI 착장 미리보기"
            className="fixed bottom-0 left-0 right-0 z-50 bg-bg-primary rounded-t-[var(--radius-xl)] px-[20px] pt-[16px] pb-[32px] safe-area-bottom"
            initial={prefersReducedMotion ? false : { y: "100%" }}
            animate={{ y: 0 }}
            exit={{ y: "100%" }}
            transition={
              prefersReducedMotion
                ? { duration: 0 }
                : { type: "spring", stiffness: 300, damping: 30 }
            }
          >
            {/* 핸들 */}
            <div className="flex justify-center mb-[16px]">
              <div className="w-[36px] h-[4px] rounded-full bg-border" />
            </div>

            {tryonState === "loading" && (
              <TryOnLoadingSpinner itemUrls={itemUrls} />
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
                  />
                </div>
                <div className="flex gap-[12px] mt-[20px] w-full max-w-[320px]">
                  <button
                    type="button"
                    onClick={onClose}
                    className="flex-1 py-[14px] border border-accent text-accent font-body text-[15px] font-medium rounded-[var(--radius-full)]"
                  >
                    저장
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      if (navigator.share) {
                        navigator.share({ title: "ColorFit 착장", url: tryonImageUrl });
                      }
                    }}
                    className="flex-1 py-[14px] bg-accent text-white font-body text-[15px] font-medium rounded-[var(--radius-full)]"
                  >
                    공유
                  </button>
                </div>
              </motion.div>
            )}

            {tryonState === "error" && (
              <div className="flex flex-col items-center py-[24px]">
                <div className="w-[48px] h-[48px] rounded-full bg-error-bg flex items-center justify-center mb-[12px]">
                  <span className="text-[24px]">{"\uD83D\uDE1E"}</span>
                </div>
                <p className="font-body text-[15px] text-text-primary mb-[4px]">
                  이미지를 생성하지 못했어요
                </p>
                <p className="font-body text-[13px] text-text-secondary mb-[20px]">
                  네트워크를 확인하고 다시 시도해주세요
                </p>
                <button
                  type="button"
                  onClick={onRetry}
                  className="px-[24px] py-[12px] bg-accent text-white font-body text-[15px] font-medium rounded-[var(--radius-full)]"
                >
                  다시 시도
                </button>
              </div>
            )}

            {tryonState === "limit" && (
              <div className="flex flex-col items-center py-[24px]">
                <div className="w-[48px] h-[48px] rounded-full bg-warning-bg flex items-center justify-center mb-[12px]">
                  <span className="text-[24px]">{"\uD83D\uDD12"}</span>
                </div>
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
                  onClick={onUpgrade}
                  className="w-full max-w-[280px] py-[14px] bg-accent text-white font-body text-[15px] font-medium rounded-[var(--radius-full)]"
                >
                  프리미엄으로 업그레이드
                </button>
                <button
                  type="button"
                  onClick={onClose}
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
  );
}

/* ── TPO 코디 카드 ── */
function TpoCodiCard({
  suggestion,
  sourceImageUrl,
  index,
  onTryOn,
}: {
  suggestion: TpoOutfitSuggestion;
  sourceImageUrl: string;
  index: number;
  onTryOn?: (itemUrls: string[]) => void;
}) {
  const prefersReducedMotion = useReducedMotion();
  const emoji = TPO_EMOJI[suggestion.tpo] ?? "\uD83D\uDC57";
  const avgScore = suggestion.items.length > 0
    ? Math.round(suggestion.items.reduce((sum, it) => sum + it.similarity * 100, 0) / suggestion.items.length)
    : 0;

  return (
    <motion.section
      className="mb-[24px]"
      initial={prefersReducedMotion ? false : { y: 20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={
        prefersReducedMotion
          ? { duration: 0 }
          : { type: "spring", stiffness: 300, damping: 30, delay: index * 0.1 }
      }
    >
      <div className="flex items-center justify-between mb-[12px]">
        <h3 className="font-display text-[18px] text-text-primary">
          {emoji} {suggestion.tpo_label}
        </h3>
        {avgScore > 0 && (
          <span className="font-body text-[13px] text-accent font-medium">
            코디 점수 {avgScore}
          </span>
        )}
      </div>
      <div className="flex gap-[10px] overflow-x-auto pb-[8px] scrollbar-hide">
        {/* 내 옷 (뱃지) */}
        <div className="shrink-0 w-[120px]">
          <div
            className="relative w-[120px] rounded-[var(--radius-md)] overflow-hidden border-2 border-accent"
            style={{ aspectRatio: "3/4" }}
          >
            <Image
              src={sourceImageUrl}
              alt="내 옷"
              fill
              sizes="120px"
              className="object-cover"
              loading="lazy"
            />
            <span className="absolute top-[6px] left-[6px] bg-accent text-white text-[10px] font-body font-medium rounded-full px-[8px] py-[2px]">
              내 옷
            </span>
          </div>
        </div>

        {/* 추천 아이템들 */}
        {suggestion.items.map((item) => (
          <RecommendedItemCard key={item.id} item={item} />
        ))}

        {/* 아이템이 없을 때 */}
        {suggestion.items.length === 0 && (
          <div className="flex items-center justify-center w-[120px] h-[160px] rounded-[var(--radius-md)] bg-bg-secondary text-text-tertiary text-[13px] font-body">
            준비 중
          </div>
        )}
      </div>

      {/* 착장으로 보기 버튼 */}
      {suggestion.items.length > 0 && onTryOn && (
        <button
          type="button"
          onClick={() => {
            const urls = suggestion.items
              .map((item) => item.image_url)
              .filter((u): u is string => u != null);
            onTryOn(urls);
          }}
          className="mt-[8px] w-full py-[10px] border border-accent text-accent font-body text-[13px] font-medium rounded-[var(--radius-full)] hover:bg-accent/5 transition-colors"
        >
          착장으로 보기
        </button>
      )}
    </motion.section>
  );
}

/* ── 메인 페이지 ── */
export default function ClosetAnalyzeResultPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const prefersReducedMotion = useReducedMotion();

  const imageUrl = searchParams.get("image_url") ?? "";
  const userToneId = searchParams.get("user_tone_id") ?? "";
  const category = searchParams.get("category") ?? "top";

  const [state, setState] = useState<PageState>("loading");
  const [analyzeResult, setAnalyzeResult] = useState<ClosetAnalyzeResponse | null>(null);
  const [recommendations, setRecommendations] = useState<ClosetRecommendationResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState("");

  /* 옷장 추가 상태 */
  const [addingToCloset, setAddingToCloset] = useState(false);
  const [closetToast, setClosetToast] = useState<string | null>(null);

  /* Try-On 상태 */
  const [tryonOpen, setTryonOpen] = useState(false);
  const [tryonState, setTryonState] = useState<TryOnState>("idle");
  const [tryonImageUrl, setTryonImageUrl] = useState("");
  const [tryonItemUrls, setTryonItemUrls] = useState<string[]>([]);
  const [tryonRemaining, setTryonRemaining] = useState<number | null>(null);

  useEffect(() => {
    if (!imageUrl || !userToneId) {
      setState("error");
      setErrorMessage("\uBD84\uC11D\uC5D0 \uD544\uC694\uD55C \uC815\uBCF4\uAC00 \uC5C6\uC2B5\uB2C8\uB2E4.");
      return;
    }

    let cancelled = false;

    async function load() {
      try {
        const analysis = await analyzeClosetItem(imageUrl, userToneId);
        if (cancelled) return;
        setAnalyzeResult(analysis);
        setState("success");

        try {
          const colorHex = analysis.dominant_colors[0]?.hex ?? "#000000";
          const recs = await fetchClosetRecommendations(
            colorHex,
            category,
            userToneId,
            undefined,
            3,
          );
          if (!cancelled) setRecommendations(recs);
        } catch {
          // 추천 실패는 무시 — 분석 결과는 유지
        }
      } catch (err) {
        if (!cancelled) {
          setState("error");
          setErrorMessage(
            err instanceof Error ? err.message : "\uBD84\uC11D \uC911 \uC624\uB958\uAC00 \uBC1C\uC0DD\uD588\uC2B5\uB2C8\uB2E4.",
          );
        }
      }
    }

    load();
    return () => { cancelled = true; };
  }, [imageUrl, userToneId, category]);

  /* Try-On 잔여 횟수 로드 */
  useEffect(() => {
    const userId = localStorage.getItem("colorfit_user_id");
    if (!userId) return;
    fetchTryonUsage(userId)
      .then((usage) => setTryonRemaining(usage.remaining))
      .catch(() => {});
  }, []);

  /* 착장 생성 핸들러 */
  const abortRef = { current: null as AbortController | null };

  const handleTryOn = useCallback(async (itemUrls: string[]) => {
    const userId = localStorage.getItem("colorfit_user_id");
    if (!userId) return;

    if (abortRef.current) abortRef.current.abort();
    abortRef.current = new AbortController();

    setTryonItemUrls([imageUrl, ...itemUrls]);
    setTryonOpen(true);
    setTryonState("loading");
    setTryonImageUrl("");

    try {
      const firstItemId = itemUrls[0]?.split("/").pop()?.replace(/\.[^.]+$/, "") ?? "tryon";
      const result = await generateTryon(
        `closet_${firstItemId}`,
        userId,
        undefined,
        imageUrl,
      );
      if (abortRef.current?.signal.aborted) return;
      setTryonImageUrl(result.image_url);
      setTryonState("success");
      setTryonRemaining(result.remaining);
    } catch (err) {
      if (abortRef.current?.signal.aborted) return;
      if (err instanceof TryonLimitError) {
        setTryonState("limit");
      } else {
        setTryonState("error");
      }
    }
  }, [imageUrl]);

  const handleTryOnRetry = useCallback(() => {
    handleTryOn(tryonItemUrls.slice(1));
  }, [handleTryOn, tryonItemUrls]);

  const handleTryOnClose = useCallback(() => {
    if (abortRef.current) abortRef.current.abort();
    setTryonOpen(false);
    setTryonState("idle");
  }, []);

  const handleUpgrade = useCallback(() => {
    router.push("/premium");
  }, [router]);

  const handleAddToCloset = useCallback(async () => {
    if (addingToCloset) return;
    const userId = localStorage.getItem("colorfit_user_id");
    if (!userId) {
      setClosetToast("로그인이 필요해요");
      setTimeout(() => setClosetToast(null), 1800);
      return;
    }
    if (!analyzeResult) return;

    setAddingToCloset(true);
    try {
      await addClosetItem({
        user_id: userId,
        image_url: imageUrl,
        category,
        dominant_color_hex: analyzeResult.dominant_colors[0]?.hex ?? null,
        matched_tone_id: analyzeResult.matched_tone_id,
        pcf_score: analyzeResult.pcf_score,
        overall_score: analyzeResult.overall_score,
        reasons: analyzeResult.reasons,
      });
      setClosetToast("옷장에 추가되었어요");
      // 성공: 버튼 비활성 상태 유지 + 자동 이동 (중복 POST 방지)
      setTimeout(() => {
        setClosetToast(null);
        router.push("/closet");
      }, 900);
    } catch {
      setClosetToast("옷장 추가에 실패했어요");
      setTimeout(() => setClosetToast(null), 1800);
      setAddingToCloset(false);
    }
  }, [addingToCloset, analyzeResult, category, imageUrl, router]);

  const handleAnalyzeAnother = useCallback(() => {
    router.push("/closet/upload");
  }, [router]);

  const handleRetry = useCallback(() => {
    setState("loading");
    setErrorMessage("");
    window.location.reload();
  }, []);

  /* ── Loading State ── */
  if (state === "loading") {
    return (
      <div className="min-h-screen bg-bg-primary px-[20px] pt-[60px] pb-[100px]">
        {/* 이미지 스켈레톤 */}
        <div className="w-full rounded-[var(--radius-lg)] bg-bg-secondary animate-pulse"
          style={{ aspectRatio: "3/4", maxHeight: "360px" }}
        />
        {/* 점수 스켈레톤 */}
        <div className="mt-[24px] flex items-center gap-[12px]">
          <div className="w-[80px] h-[48px] rounded-[var(--radius-md)] bg-bg-secondary animate-pulse" />
          <div className="flex-1 space-y-[8px]">
            <div className="h-[12px] w-3/4 rounded bg-bg-secondary animate-pulse" />
            <div className="h-[12px] w-1/2 rounded bg-bg-secondary animate-pulse" />
          </div>
        </div>
        {/* 스코어바 스켈레톤 */}
        <div className="mt-[24px] space-y-[12px]">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-[20px] rounded bg-bg-secondary animate-pulse" />
          ))}
        </div>
        <p className="text-center text-text-secondary font-body text-[14px] mt-[32px]">
          옷을 분석하고 있어요...
        </p>
      </div>
    );
  }

  /* ── Error State ── */
  if (state === "error") {
    return (
      <div className="min-h-screen bg-bg-primary flex flex-col items-center justify-center px-[20px]">
        <div className="w-[64px] h-[64px] rounded-full bg-error-bg flex items-center justify-center mb-[16px]">
          <span className="text-[28px]">{"\uD83D\uDE1E"}</span>
        </div>
        <p className="font-display text-[18px] text-text-primary mb-[8px]">
          분석에 실패했어요
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

  if (!analyzeResult) return null;

  const { pcf_score, saturation_score, lightness_score, overall_score, reasons } = analyzeResult;

  /* ── Success State ── */
  return (
    <div className="min-h-screen bg-bg-primary pb-[120px]">
      {/* ── 헤더 영역 ── */}
      <div className="relative">
        {/* 뒤로가기 */}
        <button
          type="button"
          onClick={() => window.history.length > 1 ? router.back() : router.push("/closet")}
          className="absolute top-[12px] left-[12px] z-10 w-[44px] h-[44px] rounded-full bg-black/30 flex items-center justify-center"
          aria-label="뒤로가기"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M15 18l-6-6 6-6" />
          </svg>
        </button>

        {/* 내 옷 이미지 */}
        <div
          className="relative w-full overflow-hidden"
          style={{ aspectRatio: "3/4", maxHeight: "420px" }}
        >
          <Image
            src={imageUrl}
            alt="내 옷"
            fill
            sizes="(max-width: 768px) 100vw, 430px"
            className="object-cover"
            priority
          />
        </div>
      </div>

      {/* ── 점수 히어로 ── */}
      <div className="px-[20px] mt-[24px]">
        <motion.div
          className="flex items-start gap-[16px]"
          initial={prefersReducedMotion ? false : { y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={prefersReducedMotion ? { duration: 0 } : { type: "spring", stiffness: 300, damping: 30 }}
        >
          {/* 큰 점수 */}
          <div className="flex flex-col items-center">
            <span
              className="font-display text-[36px] leading-[1.15] font-bold"
              style={{ color: "var(--color-accent)" }}
            >
              {Math.round(overall_score)}
            </span>
            <span className="font-body text-[11px] text-text-tertiary mt-[2px]">
              / 100
            </span>
          </div>

          {/* 등급 + 톤 */}
          <div className="flex-1 pt-[4px]">
            <p className="font-display text-[18px] text-text-primary leading-[1.3]">
              {scoreLabel(overall_score)}
            </p>
            <p className="font-body text-[13px] text-text-secondary mt-[4px]">
              {analyzeResult.matched_tone_name}
              {" "}
              기준 분석 결과
            </p>
          </div>
        </motion.div>

        {/* ── 미니 스코어 3축 ── */}
        <div className="mt-[20px] space-y-[10px]">
          <ScoreBar
            label="색상"
            score={pcf_score}
            color="var(--color-score-pcf)"
            index={0}
          />
          <ScoreBar
            label="채도"
            score={saturation_score}
            color="var(--color-score-ch)"
            index={1}
          />
          <ScoreBar
            label="명도"
            score={lightness_score}
            color="var(--color-score-of)"
            index={2}
          />
        </div>

        {/* ── 상세 이유 ── */}
        <div className="mt-[24px] p-[16px] bg-bg-secondary rounded-[var(--radius-lg)]">
          <h2 className="font-display text-[16px] text-text-primary mb-[8px]">
            분석 이유
          </h2>
          <ul className="space-y-[6px]">
            {reasons.map((reason, i) => (
              <li key={i} className="font-body text-[14px] text-text-secondary leading-[1.6] flex gap-[8px]">
                <span className="text-accent shrink-0">{"\u2022"}</span>
                <span>{reason}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* ── 추천 코디 섹션 ── */}
        {recommendations && recommendations.recommendations.length > 0 && (
          <div className="mt-[32px]">
            <h2 className="font-display text-[24px] text-text-primary mb-[16px] leading-[1.25]">
              이 옷으로 완성하는 코디
            </h2>
            {/* 잔여 횟수 */}
            {tryonRemaining != null && tryonRemaining > 0 && (
              <p className="font-body text-[13px] text-text-tertiary mb-[12px]">
                무료 착장 {tryonRemaining}회 남음
              </p>
            )}
            {tryonRemaining === 0 && (
              <p className="font-body text-[13px] text-warning-text mb-[12px]">
                무료 착장 소진 — 프리미엄으로 업그레이드
              </p>
            )}

            {recommendations.recommendations.map(
              (suggestion: TpoOutfitSuggestion, idx: number) => (
                <TpoCodiCard
                  key={suggestion.tpo}
                  suggestion={suggestion}
                  sourceImageUrl={imageUrl}
                  index={idx}
                  onTryOn={handleTryOn}
                />
              ),
            )}
          </div>
        )}

        {/* ── 추천이 없을 때 ── */}
        {recommendations && recommendations.recommendations.length === 0 && (
          <div className="mt-[32px] text-center py-[32px]">
            <p className="font-body text-[14px] text-text-secondary">
              아직 이 옷에 어울리는 코디를 준비 중이에요
            </p>
          </div>
        )}

        {/* ── 추천 로딩 중 ── */}
        {!recommendations && state === "success" && (
          <div className="mt-[32px]">
            <h2 className="font-display text-[24px] text-text-primary mb-[16px] leading-[1.25]">
              이 옷으로 완성하는 코디
            </h2>
            <div className="space-y-[16px]">
              {[1, 2].map((i) => (
                <div key={i} className="h-[180px] rounded-[var(--radius-lg)] bg-bg-secondary animate-pulse" />
              ))}
            </div>
          </div>
        )}
      </div>

      {/* ── Try-On 바텀시트 ── */}
      <TryOnBottomSheet
        isOpen={tryonOpen}
        onClose={handleTryOnClose}
        tryonState={tryonState}
        tryonImageUrl={tryonImageUrl}
        itemUrls={tryonItemUrls}
        onRetry={handleTryOnRetry}
        onUpgrade={handleUpgrade}
      />

      {/* ── 하단 CTA 고정 ── */}
      <div className="fixed bottom-0 left-0 right-0 bg-bg-primary border-t border-border px-[20px] py-[12px] flex gap-[12px] safe-area-bottom">
        <button
          type="button"
          onClick={handleAnalyzeAnother}
          className="flex-1 py-[14px] border border-accent text-accent font-body text-[15px] font-medium rounded-[var(--radius-full)] hover:bg-accent/5 transition-colors"
        >
          다른 옷도 분석하기
        </button>
        <button
          type="button"
          onClick={handleAddToCloset}
          disabled={addingToCloset}
          className="flex-1 py-[14px] bg-accent text-white font-body text-[15px] font-medium rounded-[var(--radius-full)] disabled:opacity-60"
        >
          {addingToCloset ? "추가 중..." : "옷장에 추가"}
        </button>
      </div>

      {/* 토스트 */}
      <AnimatePresence>
        {closetToast && (
          <motion.div
            role="status"
            aria-live="polite"
            className="fixed bottom-[100px] left-1/2 -translate-x-1/2 z-[60] bg-[#333] text-white text-[14px] font-body px-[20px] py-[10px] rounded-full shadow-lg"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 20 }}
            transition={{ duration: 0.2 }}
          >
            {closetToast}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
