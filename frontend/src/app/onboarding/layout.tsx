"use client";

import { usePathname, useRouter } from "next/navigation";
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
  const pathname = usePathname();
  const router = useRouter();
  const currentStep = getCurrentStep(pathname);
  const prefersReducedMotion = useReducedMotion();

  const handleBack = () => {
    if (currentStep > 0) {
      router.push(STEPS[currentStep - 1].path);
    }
  };

  return (
    <div className="min-h-dvh flex flex-col bg-bg-primary">
      <header className="sticky top-0 z-10 bg-bg-primary px-[var(--space-md)] pt-[var(--space-md)] pb-[var(--space-sm)]">
        <div className="h-10 flex items-center">
          {currentStep > 0 && (
            <button
              onClick={handleBack}
              className="flex items-center justify-center w-10 h-10 -ml-2 text-text-primary"
              aria-label="이전 단계로"
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
          )}
        </div>

        <div
          className="flex gap-[var(--space-xs)] mt-[var(--space-sm)]"
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
        </div>

        <p
          className="mt-[var(--space-xs)] font-body text-text-secondary"
          style={{ fontSize: "13px" }}
        >
          {currentStep + 1} / {STEPS.length}
        </p>
      </header>

      <main className="flex-1 flex flex-col px-[var(--space-md)]">
        {children}
      </main>
    </div>
  );
}
