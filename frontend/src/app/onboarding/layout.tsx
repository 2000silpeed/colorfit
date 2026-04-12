"use client";

import { Suspense } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import Image from "next/image";
import { motion, useReducedMotion } from "framer-motion";

const STEPS = [
  { path: "/onboarding/step1", label: "성별" },
  { path: "/onboarding/step2", label: "퍼스널컬러" },
  { path: "/onboarding/step3", label: "TPO·무드" },
  { path: "/onboarding/step4", label: "예산" },
  { path: "/onboarding/step5", label: "취향" },
];

function getCurrentStep(pathname: string): number {
  const idx = STEPS.findIndex((s) => pathname.startsWith(s.path));
  return idx === -1 ? 0 : idx;
}

interface OnboardingLayoutProps {
  children: React.ReactNode;
}

export default function OnboardingLayout({ children }: OnboardingLayoutProps) {
  return (
    <Suspense fallback={<div className="min-h-dvh bg-bg-primary" />}>
      <OnboardingLayoutContent>{children}</OnboardingLayoutContent>
    </Suspense>
  );
}

function OnboardingLayoutContent({ children }: OnboardingLayoutProps) {
  const pathname = usePathname();
  const router = useRouter();
  const searchParams = useSearchParams();
  const isChangeMode = searchParams.get("mode") === "change";
  const currentStep = getCurrentStep(pathname);
  const prefersReducedMotion = useReducedMotion();

  const handleBack = () => {
    if (isChangeMode) {
      router.push("/profile");
      return;
    }
    if (currentStep === 0) {
      router.push("/login");
    } else {
      router.push(STEPS[currentStep - 1].path);
    }
  };

  return (
    <div className="relative min-h-dvh flex flex-col max-w-[430px] mx-auto overflow-hidden bg-bg-primary">
      {/* 온보딩 전용 화보 배경 이미지 */}
      <Image
        src="/onboarding-photo-bg.png"
        alt="Onboarding Background"
        fill
        className="object-cover opacity-80 z-0 pointer-events-none object-top"
        priority
      />
      {/* 바닥으로 갈수록 희미해지는 그라데이션 오버레이 */}
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-[#F8F6F3]/60 to-[#F8F6F3] z-0 pointer-events-none" />

      {/* 헤더 */}
      <header className="relative z-10 sticky top-0 px-[20px] pt-[16px] pb-[8px] border-b border-white/20 bg-white/30 backdrop-blur-md">
        <div className="h-[44px] flex items-center">
          <button
            onClick={handleBack}
            className="flex items-center justify-center w-[44px] h-[44px] -ml-[8px] text-text-primary active:scale-[0.95] active:opacity-70 transition-transform duration-100"
            aria-label={isChangeMode ? "프로필로 돌아가기" : currentStep === 0 ? "로그인으로 돌아가기" : "이전 단계로"}
          >
            <svg
              width="24"
              height="24"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M15 18l-6-6 6-6" />
            </svg>
          </button>
        </div>

        {!isChangeMode && <div
          className="flex gap-[4px] mt-[8px]"
          role="progressbar"
          aria-valuenow={currentStep + 1}
          aria-valuemin={1}
          aria-valuemax={STEPS.length}
          aria-label={`온보딩 진행: ${currentStep + 1}단계 / ${STEPS.length}단계`}
        >
          {STEPS.map((step, i) => (
            <div
              key={step.path}
              className="flex-1 h-1 rounded-full overflow-hidden"
              style={{ backgroundColor: "var(--color-border)" }}
            >
              <motion.div
                className="h-full rounded-full"
                initial={false}
                animate={{ scaleX: i <= currentStep ? 1 : 0 }}
                transition={
                  prefersReducedMotion
                    ? { duration: 0 }
                    : { duration: 0.3, ease: "easeInOut" }
                }
                style={{
                  backgroundColor: "var(--color-accent)",
                  transformOrigin: "left",
                }}
              />
            </div>
          ))}
        </div>}

        {!isChangeMode && <p
          className="mt-[4px] text-[12px] text-text-secondary"
          style={{ fontFamily: "var(--font-body)", fontVariantNumeric: "tabular-nums" }}
        >
          {currentStep + 1} / {STEPS.length}
        </p>}
      </header>

      <main className="relative z-10 flex-1 flex flex-col px-[20px]">
        {children}
      </main>
    </div>
  );
}
