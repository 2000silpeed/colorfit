"use client";

import { useState, useEffect, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import { motion, useReducedMotion } from "framer-motion";
import { fetchToneDetail, type ToneDetailResponse } from "@/lib/api";

/* ── 톤별 그라데이션 ── */
const TONE_GRADIENTS: Record<string, string> = {
  spring_warm_light: "linear-gradient(135deg, #FADADD 0%, #FFE4C4 50%, #FFFACD 100%)",
  spring_warm_bright: "linear-gradient(135deg, #FF7F50 0%, #FFD700 50%, #FFA07A 100%)",
  spring_warm_vivid: "linear-gradient(135deg, #FF6347 0%, #FF8C00 50%, #FFD700 100%)",
  summer_cool_light: "linear-gradient(135deg, #E6E6FA 0%, #B0C4DE 50%, #FFB6C1 100%)",
  summer_cool_soft: "linear-gradient(135deg, #C9B1D0 0%, #B0C4DE 50%, #D4A5A5 100%)",
  summer_cool_bright: "linear-gradient(135deg, #4169E1 0%, #DA70D6 50%, #00CED1 100%)",
  summer_cool_mute: "linear-gradient(135deg, #A9A9C8 0%, #C4B7A6 50%, #B0A6C6 100%)",
  autumn_warm_deep: "linear-gradient(135deg, #8B4513 0%, #800020 50%, #556B2F 100%)",
  autumn_warm_mute: "linear-gradient(135deg, #C4A882 0%, #BDB76B 50%, #BC8F8F 100%)",
  autumn_warm_strong: "linear-gradient(135deg, #CC5500 0%, #B8860B 50%, #8B4513 100%)",
  winter_cool_deep: "linear-gradient(135deg, #191970 0%, #4B0082 50%, #800020 100%)",
  winter_cool_strong: "linear-gradient(135deg, #0000CD 0%, #DC143C 50%, #008080 100%)",
  winter_cool_vivid: "linear-gradient(135deg, #FF0000 0%, #0000FF 50%, #FF00FF 100%)",
};

/* ── 스켈레톤 ── */
function ToneSkeleton() {
  return (
    <div className="min-h-screen bg-bg-primary">
      <div className="h-[200px] bg-[#E0DCD7] animate-pulse" />
      <div className="px-[20px] pt-[24px]">
        <div className="h-[16px] w-3/4 rounded bg-[#E0DCD7] animate-pulse mb-[24px]" />
        <div className="flex gap-[12px] mb-[32px]">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="w-[48px] h-[48px] rounded-full bg-[#E0DCD7] animate-pulse" />
          ))}
        </div>
        <div className="h-[16px] w-1/2 rounded bg-[#E0DCD7] animate-pulse mb-[12px]" />
        <div className="flex gap-[12px]">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="w-[48px] h-[48px] rounded-full bg-[#E0DCD7] animate-pulse" />
          ))}
        </div>
      </div>
    </div>
  );
}

export default function ToneDetailPage() {
  const params = useParams();
  const router = useRouter();
  const shouldReduceMotion = useReducedMotion();
  const toneId = params.id as string;

  const [tone, setTone] = useState<ToneDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetchToneDetail(toneId)
      .then(setTone)
      .catch(() => setError("톤 정보를 불러올 수 없습니다"))
      .finally(() => setLoading(false));
  }, [toneId]);

  if (loading) return <ToneSkeleton />;

  if (error || !tone) {
    return (
      <div className="min-h-screen bg-bg-primary flex flex-col items-center justify-center px-[20px]">
        <p className="text-text-secondary text-[15px] mb-[16px]" style={{ fontFamily: "var(--font-body)" }}>
          {error ?? "톤 정보를 불러올 수 없습니다"}
        </p>
        <button
          onClick={() => window.history.length > 1 ? router.back() : router.push("/feed")}
          className="px-[24px] py-[10px] rounded-full text-[14px] font-medium"
          style={{
            fontFamily: "var(--font-body)",
            backgroundColor: "var(--color-accent)",
            color: "#FFFFFF",
          }}
        >
          돌아가기
        </button>
      </div>
    );
  }

  const gradient = TONE_GRADIENTS[toneId] ?? TONE_GRADIENTS.summer_cool_soft;

  return (
    <div className="min-h-screen bg-bg-primary">
      {/* 히어로 */}
      <motion.div
        className="relative w-full flex flex-col items-center justify-center"
        style={{ background: gradient, height: "200px" }}
        initial={shouldReduceMotion ? false : { opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={shouldReduceMotion ? { duration: 0 } : { duration: 0.4 }}
      >
        {/* 뒤로가기 */}
        <button
          onClick={() => window.history.length > 1 ? router.back() : router.push("/feed")}
          className="absolute top-[12px] left-[16px] w-[36px] h-[36px] rounded-full bg-black/20 flex items-center justify-center"
        >
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
            <path d="M12.5 15L7.5 10L12.5 5" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </button>

        <h1
          className="text-[32px] text-white text-center"
          style={{ fontFamily: "var(--font-display)", fontWeight: 700, lineHeight: 1.15 }}
        >
          {tone.tone_name_ko}
        </h1>
      </motion.div>

      {/* 시즌 설명 */}
      <motion.div
        className="px-[20px] pt-[24px]"
        initial={shouldReduceMotion ? false : { opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={shouldReduceMotion ? { duration: 0 } : { duration: 0.3, delay: 0.1 }}
      >
        <p
          className="text-[15px] text-text-primary leading-[1.6]"
          style={{ fontFamily: "var(--font-body)" }}
        >
          {tone.description}
        </p>
      </motion.div>

      {/* 잘 어울리는 색 */}
      <motion.div
        className="px-[20px] mt-[32px]"
        initial={shouldReduceMotion ? false : { opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={shouldReduceMotion ? { duration: 0 } : { duration: 0.3, delay: 0.15 }}
      >
        <h2
          className="text-[18px] text-text-primary mb-[16px]"
          style={{ fontFamily: "var(--font-display)", fontWeight: 700, lineHeight: 1.3 }}
        >
          잘 어울리는 색
        </h2>
        <div
          ref={scrollRef}
          className="flex gap-[16px] overflow-x-auto pb-[8px]"
          style={{ scrollbarWidth: "none" }}
        >
          {tone.best_colors.map((c) => (
            <div key={c.hex} className="flex flex-col items-center gap-[6px] shrink-0">
              <div
                className="w-[48px] h-[48px] rounded-full border border-border"
                style={{ backgroundColor: c.hex }}
              />
              <span
                className="text-[11px] leading-[1.4] text-text-tertiary text-center"
                style={{ fontFamily: "var(--font-body)", maxWidth: "56px" }}
              >
                {c.name_ko}
              </span>
            </div>
          ))}
        </div>
      </motion.div>

      {/* 피해야 할 색 */}
      <motion.div
        className="px-[20px] mt-[32px]"
        initial={shouldReduceMotion ? false : { opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={shouldReduceMotion ? { duration: 0 } : { duration: 0.3, delay: 0.2 }}
      >
        <h2
          className="text-[18px] text-text-primary mb-[16px]"
          style={{ fontFamily: "var(--font-display)", fontWeight: 700, lineHeight: 1.3 }}
        >
          피해야 할 색
        </h2>
        <div className="flex gap-[16px] overflow-x-auto pb-[8px]" style={{ scrollbarWidth: "none" }}>
          {tone.worst_colors.map((c) => (
            <div key={c.hex} className="flex flex-col items-center gap-[6px] shrink-0">
              <div className="relative">
                <div
                  className="w-[48px] h-[48px] rounded-full border border-border"
                  style={{ backgroundColor: c.hex }}
                />
                <div className="absolute inset-0 flex items-center justify-center">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                    <line x1="5" y1="5" x2="19" y2="19" stroke="white" strokeWidth="2.5" strokeLinecap="round" />
                    <line x1="19" y1="5" x2="5" y2="19" stroke="white" strokeWidth="2.5" strokeLinecap="round" />
                  </svg>
                </div>
              </div>
              <span
                className="text-[11px] leading-[1.4] text-text-tertiary text-center"
                style={{ fontFamily: "var(--font-body)", maxWidth: "56px" }}
              >
                {c.name_ko}
              </span>
            </div>
          ))}
        </div>
      </motion.div>

      {/* 전체 팔레트 */}
      <motion.div
        className="px-[20px] mt-[32px] pb-[48px]"
        initial={shouldReduceMotion ? false : { opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={shouldReduceMotion ? { duration: 0 } : { duration: 0.3, delay: 0.25 }}
      >
        <h2
          className="text-[18px] text-text-primary mb-[16px]"
          style={{ fontFamily: "var(--font-display)", fontWeight: 700, lineHeight: 1.3 }}
        >
          전체 팔레트
        </h2>
        <div className="flex flex-wrap gap-[12px]">
          {tone.all_colors.map((c) => (
            <div key={c.hex} className="flex flex-col items-center gap-[4px]">
              <div
                className="w-[40px] h-[40px] rounded-full border border-border"
                style={{ backgroundColor: c.hex }}
              />
              <span
                className="text-[11px] leading-[1.4] text-text-tertiary text-center"
                style={{ fontFamily: "var(--font-body)", maxWidth: "48px" }}
              >
                {c.name_ko}
              </span>
            </div>
          ))}
        </div>
      </motion.div>

      {/* 톤 변경 버튼 */}
      <div className="px-[20px] pb-[32px]">
        <button
          className="w-full py-[14px] text-center text-[14px] text-accent"
          style={{ fontFamily: "var(--font-body)", fontWeight: 500 }}
        >
          다른 톤으로 변경하기
        </button>
      </div>
    </div>
  );
}
