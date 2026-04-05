"use client";

import { useState, useCallback, useEffect } from "react";
import { useRouter } from "next/navigation";
import { motion, useReducedMotion } from "framer-motion";
import {
  subscribe,
  fetchSubscriptionStatus,
  fetchTryonUsage,
  type SubscriptionPlan,
} from "@/lib/api";
import { isLoggedIn } from "@/lib/auth";

type PlanType = SubscriptionPlan;
type RegisterState = "idle" | "submitting" | "done";

interface BenefitItem {
  icon: string;
  title: string;
  description: string;
}

const BENEFITS: BenefitItem[] = [
  {
    icon: "M15.75 10.5l4.72-4.72a.75.75 0 011.28.53v11.38a.75.75 0 01-1.28.53l-4.72-4.72M4.5 18.75h9a2.25 2.25 0 002.25-2.25v-9a2.25 2.25 0 00-2.25-2.25h-9A2.25 2.25 0 002.25 7.5v9a2.25 2.25 0 002.25 2.25z",
    title: "AI 착장 샘플 무제한",
    description: "내 옷으로 만드는 코디 착장 이미지를 제한 없이 생성하세요.",
  },
  {
    icon: "M9.568 3H5.25A2.25 2.25 0 003 5.25v4.318c0 .597.237 1.17.659 1.591l9.581 9.581c.699.699 1.78.872 2.607.33a18.095 18.095 0 005.223-5.223c.542-.827.369-1.908-.33-2.607L11.16 3.66A2.25 2.25 0 009.568 3z M6 6h.008v.008H6V6z",
    title: "제휴 할인 쿠폰",
    description: "쇼핑몰 5~10% 전용 할인 쿠폰을 매월 받아보세요.",
  },
  {
    icon: "M14.857 17.082a23.848 23.848 0 005.454-1.31A8.967 8.967 0 0118 9.75v-.7V9A6 6 0 006 9v.75a8.967 8.967 0 01-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 01-5.714 0m5.714 0a3 3 0 11-5.714 0",
    title: "가격 하락 알림",
    description: "저장한 아이템의 가격이 떨어지면 바로 알려드려요.",
  },
  {
    icon: "M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 012.25-2.25h13.5A2.25 2.25 0 0121 7.5v11.25m-18 0A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75m-18 0v-7.5A2.25 2.25 0 015.25 9h13.5A2.25 2.25 0 0121 11.25v7.5",
    title: "시즌 신상 알림",
    description: "새 시즌 톤 맞춤 신상품을 가장 먼저 확인하세요.",
  },
];

const PLANS = {
  monthly: {
    label: "월간",
    price: "4,900",
    unit: "월",
    subtext: null,
  },
  yearly: {
    label: "연간",
    price: "39,000",
    unit: "연",
    subtext: "월 3,250원꼴",
  },
} as const;

export default function PremiumPage() {
  const router = useRouter();
  const prefersReducedMotion = useReducedMotion();

  const [selectedPlan, setSelectedPlan] = useState<PlanType>("yearly");
  const [registerState, setRegisterState] = useState<RegisterState>("idle");
  const [couponCode, setCouponCode] = useState("");
  const [errorMessage, setErrorMessage] = useState("");
  const [isPremium, setIsPremium] = useState(false);
  const [tryonRemaining, setTryonRemaining] = useState<number | null>(null);

  useEffect(() => {
    const userId = localStorage.getItem("colorfit_user_id");
    if (!userId) return;
    fetchSubscriptionStatus(userId)
      .then((status) => setIsPremium(status.is_premium))
      .catch(() => {});
    fetchTryonUsage(userId)
      .then((usage) => setTryonRemaining(usage.remaining))
      .catch(() => {});
  }, []);

  const handleBack = useCallback(() => {
    if (window.history.length > 1) {
      router.back();
    } else {
      router.push("/feed");
    }
  }, [router]);

  const handleRegister = useCallback(async () => {
    if (registerState !== "idle") return;

    if (!isLoggedIn()) {
      sessionStorage.setItem("colorfit_return_url", "/premium");
      router.push("/login?returnUrl=/premium");
      return;
    }

    const userId = localStorage.getItem("colorfit_user_id");
    if (!userId) {
      setErrorMessage("로그인 정보를 찾지 못했어요. 다시 로그인해주세요.");
      return;
    }

    const code = couponCode.trim();
    if (!code) {
      setErrorMessage("쿠폰 코드를 입력해주세요.");
      return;
    }

    setErrorMessage("");
    setRegisterState("submitting");
    try {
      await subscribe(userId, selectedPlan, code);
      setIsPremium(true);
      setRegisterState("done");
      try {
        const usage = await fetchTryonUsage(userId);
        setTryonRemaining(usage.remaining);
      } catch {
        // ignore
      }
    } catch (err) {
      setRegisterState("idle");
      setErrorMessage(
        err instanceof Error ? err.message : "구독 처리 중 오류가 발생했어요.",
      );
    }
  }, [registerState, couponCode, selectedPlan, router]);

  const fadeUp = prefersReducedMotion
    ? {}
    : { initial: { y: 30, opacity: 0 }, animate: { y: 0, opacity: 1 } };

  const springTransition = prefersReducedMotion
    ? { duration: 0 }
    : { type: "spring" as const, stiffness: 300, damping: 30 };

  return (
    <div className="min-h-screen bg-bg-primary pb-[48px]">
      {/* Header */}
      <div className="sticky top-0 z-30 bg-bg-primary/80 backdrop-blur-sm">
        <div className="flex items-center px-[20px] h-[56px]">
          <button
            type="button"
            onClick={handleBack}
            className="w-[44px] h-[44px] flex items-center justify-center -ml-[10px]"
            aria-label="뒤로 가기"
          >
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="var(--color-text-primary)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M15 19l-7-7 7-7" />
            </svg>
          </button>
        </div>
      </div>

      {/* Hero */}
      <motion.div
        className="px-[20px] mt-[8px]"
        {...fadeUp}
        transition={{ ...springTransition, delay: 0 }}
      >
        <h1 className="font-display text-[36px] text-text-primary leading-[1.15]">
          ColorFit
          <br />
          Premium
        </h1>
        <p className="font-body text-[16px] text-text-secondary mt-[12px] leading-[1.6]">
          내 옷장의 가능성을 무제한으로 탐색하세요.
        </p>
      </motion.div>

      {/* Benefits */}
      <div className="px-[20px] mt-[40px]">
        {BENEFITS.map((benefit, idx) => (
          <motion.div
            key={benefit.title}
            className="flex gap-[16px] mb-[28px]"
            {...fadeUp}
            transition={{ ...springTransition, delay: prefersReducedMotion ? 0 : 0.1 * (idx + 1) }}
          >
            <div
              className="w-[48px] h-[48px] rounded-[var(--radius-lg)] flex items-center justify-center flex-shrink-0"
              style={{ backgroundColor: "var(--color-bg-secondary)" }}
            >
              <svg
                width="24"
                height="24"
                viewBox="0 0 24 24"
                fill="none"
                stroke="var(--color-accent)"
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d={benefit.icon} />
              </svg>
            </div>
            <div className="flex-1 min-w-0">
              <p className="font-body text-[16px] text-text-primary font-medium leading-[1.4]">
                {benefit.title}
              </p>
              <p className="font-body text-[14px] text-text-secondary mt-[4px] leading-[1.5]">
                {benefit.description}
              </p>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Comparison Table */}
      <motion.div
        className="mx-[20px] mt-[12px] rounded-[var(--radius-lg)] overflow-hidden border"
        style={{ borderColor: "var(--color-border)" }}
        {...fadeUp}
        transition={{ ...springTransition, delay: prefersReducedMotion ? 0 : 0.5 }}
      >
        <table className="w-full font-body text-[14px]" aria-label="무료 vs 프리미엄 기능 비교">
          <thead>
            <tr style={{ backgroundColor: "var(--color-bg-secondary)" }}>
              <th className="text-left py-[12px] px-[16px] text-text-secondary font-medium">
                기능
              </th>
              <th className="text-center py-[12px] px-[16px] text-text-secondary font-medium w-[72px]">
                무료
              </th>
              <th
                className="text-center py-[12px] px-[16px] font-medium w-[72px]"
                style={{ color: "var(--color-accent)" }}
              >
                Premium
              </th>
            </tr>
          </thead>
          <tbody>
            {[
              { feature: "옷 분석 + 이유", free: "무제한", premium: "무제한" },
              { feature: "아이템 추천", free: "무제한", premium: "무제한" },
              { feature: "AI 착장 샘플", free: "3회", premium: "무제한", highlight: true },
              { feature: "할인 쿠폰", free: "\u2014", premium: "5~10%" },
              { feature: "가격 하락 알림", free: "\u2014", premium: "O" },
              { feature: "시즌 신상 알림", free: "\u2014", premium: "O" },
            ].map((row) => (
              <tr
                key={row.feature}
                className="border-t"
                style={{ borderColor: "var(--color-border)" }}
              >
                <td className="py-[12px] px-[16px] text-text-primary">
                  {row.feature}
                </td>
                <td className="text-center py-[12px] px-[16px] text-text-tertiary">
                  {row.free}
                </td>
                <td
                  className="text-center py-[12px] px-[16px] font-medium"
                  style={{
                    color: row.highlight
                      ? "var(--color-accent)"
                      : "var(--color-text-primary)",
                  }}
                >
                  {row.premium}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </motion.div>

      {/* Plan Selector */}
      <motion.div
        className="px-[20px] mt-[40px]"
        {...fadeUp}
        transition={{ ...springTransition, delay: prefersReducedMotion ? 0 : 0.6 }}
      >
        <div className="flex gap-[12px]">
          {(["yearly", "monthly"] as PlanType[]).map((plan) => {
            const info = PLANS[plan];
            const isSelected = selectedPlan === plan;

            return (
              <button
                key={plan}
                type="button"
                onClick={() => setSelectedPlan(plan)}
                className="flex-1 py-[20px] px-[16px] rounded-[var(--radius-lg)] border-2 text-left transition-colors"
                style={{
                  borderColor: isSelected
                    ? "var(--color-accent)"
                    : "var(--color-border)",
                  backgroundColor: isSelected
                    ? "var(--color-error-bg)"
                    : "var(--color-bg-primary)",
                }}
                aria-pressed={isSelected}
              >
                <span className="font-body text-[13px] text-text-secondary block">
                  {info.label}
                </span>
                <span
                  className="font-display text-[24px] leading-[1.25] block mt-[4px]"
                  style={{
                    color: isSelected
                      ? "var(--color-accent)"
                      : "var(--color-text-primary)",
                  }}
                >
                  {info.price}
                  <span className="font-body text-[14px] text-text-secondary">
                    원/{info.unit}
                  </span>
                </span>
                {info.subtext && (
                  <span
                    className="font-body text-[12px] block mt-[4px]"
                    style={{ color: "var(--color-accent)" }}
                  >
                    {info.subtext}
                  </span>
                )}
                {plan === "yearly" && (
                  <span
                    className="inline-block mt-[8px] font-body text-[11px] font-medium px-[8px] py-[2px] rounded-[var(--radius-full)]"
                    style={{
                      backgroundColor: "var(--color-accent)",
                      color: "#FFFFFF",
                    }}
                  >
                    33% 할인
                  </span>
                )}
              </button>
            );
          })}
        </div>
      </motion.div>

      {/* CTA */}
      <motion.div
        className="px-[20px] mt-[32px]"
        {...fadeUp}
        transition={{ ...springTransition, delay: prefersReducedMotion ? 0 : 0.7 }}
      >
        {isPremium || registerState === "done" ? (
          <div className="text-center py-[16px]">
            <div className="w-[48px] h-[48px] rounded-full mx-auto mb-[12px] flex items-center justify-center" style={{ backgroundColor: "var(--color-success-bg)" }}>
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="var(--color-success-text)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <p className="font-display text-[18px] text-text-primary">
              프리미엄 활성화됨
            </p>
            <p className="font-body text-[14px] text-text-secondary mt-[4px]">
              AI 착장 샘플을 무제한으로 이용하세요.
            </p>
            {tryonRemaining === null && (
              <p className="font-body text-[12px] text-text-tertiary mt-[8px]">
                착장 생성 무제한
              </p>
            )}
            <button
              type="button"
              onClick={handleBack}
              className="mt-[20px] font-body text-[15px] font-medium px-[24px] py-[12px] rounded-[var(--radius-full)] border"
              style={{ borderColor: "var(--color-accent)", color: "var(--color-accent)" }}
            >
              돌아가기
            </button>
          </div>
        ) : (
          <>
            <label className="block mb-[12px]">
              <span className="font-body text-[13px] text-text-secondary block mb-[6px]">
                쿠폰 코드
              </span>
              <input
                type="text"
                value={couponCode}
                onChange={(e) => {
                  setCouponCode(e.target.value);
                  if (errorMessage) setErrorMessage("");
                }}
                placeholder="COLORFIT-BETA"
                className="w-full px-[16px] py-[14px] rounded-[var(--radius-md)] border font-body text-[15px] text-text-primary bg-bg-primary focus:outline-none focus:border-accent"
                style={{ borderColor: "var(--color-border)" }}
                autoCapitalize="characters"
                autoCorrect="off"
                spellCheck={false}
              />
            </label>
            {errorMessage && (
              <p className="font-body text-[13px] text-error-text mb-[12px]" style={{ color: "var(--color-error-text)" }}>
                {errorMessage}
              </p>
            )}
            <button
              type="button"
              onClick={handleRegister}
              disabled={registerState === "submitting"}
              className="w-full py-[16px] font-body text-[16px] font-medium text-white rounded-[var(--radius-full)] disabled:opacity-60"
              style={{ backgroundColor: "var(--color-accent)" }}
            >
              {registerState === "submitting" ? "등록 중..." : "프리미엄 시작하기"}
            </button>
            <p className="font-body text-[12px] text-text-tertiary text-center mt-[12px]">
              MVP 기간 중 결제는 발생하지 않습니다.
              <br />
              테스트 쿠폰으로 프리미엄을 체험해보세요.
            </p>
          </>
        )}
      </motion.div>
    </div>
  );
}
