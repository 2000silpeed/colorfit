"use client";

import { useCallback } from "react";
import { useRouter } from "next/navigation";
import { motion, useReducedMotion } from "framer-motion";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default function LoginPage() {
  const router = useRouter();
  const prefersReducedMotion = useReducedMotion();

  const handleKakaoLogin = useCallback(() => {
    window.location.href = `${API_BASE}/api/auth/kakao`;
  }, []);

  const handleGoogleLogin = useCallback(() => {
    window.location.href = `${API_BASE}/api/auth/google`;
  }, []);

  const handleGuest = useCallback(() => {
    if (typeof window !== "undefined") {
      let userId = localStorage.getItem("colorfit_user_id");
      if (!userId) {
        userId = crypto.randomUUID();
        localStorage.setItem("colorfit_user_id", userId);
      }
      const tone = localStorage.getItem("colorfit_tone");
      if (tone) {
        router.push("/feed");
      } else {
        router.push("/onboarding/step1");
      }
    }
  }, [router]);

  return (
    <div
      className="min-h-screen flex flex-col items-center justify-center px-[32px]"
      style={{ backgroundColor: "var(--color-bg-primary)" }}
    >
      {/* 로고 + 서브카피 */}
      <motion.div
        className="flex flex-col items-center mb-[64px]"
        initial={prefersReducedMotion ? false : { opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={prefersReducedMotion ? { duration: 0 } : { duration: 0.6 }}
      >
        <h1
          className="text-[36px] leading-[1.2]"
          style={{
            fontFamily: "var(--font-display)",
            fontWeight: 800,
            color: "var(--color-accent)",
          }}
        >
          ColorFit
        </h1>
        <p
          className="mt-[12px] text-[15px] text-center leading-[1.5]"
          style={{
            fontFamily: "var(--font-body)",
            color: "var(--color-text-secondary)",
          }}
        >
          퍼스널컬러로 찾는{"\n"}나만의 코디
        </p>
      </motion.div>

      {/* 로그인 버튼 그룹 */}
      <motion.div
        className="w-full flex flex-col gap-[12px]"
        initial={prefersReducedMotion ? false : { opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={
          prefersReducedMotion
            ? { duration: 0 }
            : { duration: 0.6, delay: 0.15 }
        }
      >
        {/* 카카오 로그인 */}
        <button
          type="button"
          onClick={handleKakaoLogin}
          className="relative w-full py-[14px] rounded-[var(--radius-md)] text-[15px] font-medium"
          style={{
            backgroundColor: "#FEE500",
            color: "#191919",
            fontFamily: "var(--font-body)",
          }}
        >
          <svg
            className="absolute left-[16px] top-1/2 -translate-y-1/2"
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="#191919"
          >
            <path d="M12 3C6.477 3 2 6.463 2 10.691c0 2.72 1.804 5.108 4.516 6.445l-.946 3.527c-.082.306.254.556.52.387l4.2-2.78c.558.065 1.127.1 1.71.1 5.523 0 10-3.463 10-7.679S17.523 3 12 3z" />
          </svg>
          카카오로 시작하기
        </button>

        {/* 구글 로그인 */}
        <button
          type="button"
          onClick={handleGoogleLogin}
          className="relative w-full py-[14px] rounded-[var(--radius-md)] text-[15px] font-medium"
          style={{
            backgroundColor: "#FFFFFF",
            color: "var(--color-text-primary)",
            border: "1px solid var(--color-border)",
            fontFamily: "var(--font-body)",
          }}
        >
          <svg
            className="absolute left-[16px] top-1/2 -translate-y-1/2"
            width="20"
            height="20"
            viewBox="0 0 24 24"
          >
            <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z" fill="#4285F4" />
            <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853" />
            <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18A10.96 10.96 0 0 0 1 12c0 1.77.42 3.45 1.18 4.93l3.66-2.84z" fill="#FBBC05" />
            <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335" />
          </svg>
          Google로 시작하기
        </button>
      </motion.div>

      {/* 게스트 링크 */}
      <motion.button
        type="button"
        onClick={handleGuest}
        className="mt-[24px] text-[14px]"
        style={{
          fontFamily: "var(--font-body)",
          color: "var(--color-text-tertiary)",
          background: "none",
          border: "none",
          textDecoration: "underline",
          textUnderlineOffset: "3px",
        }}
        initial={prefersReducedMotion ? false : { opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={
          prefersReducedMotion
            ? { duration: 0 }
            : { duration: 0.6, delay: 0.3 }
        }
      >
        게스트로 둘러보기
      </motion.button>
    </div>
  );
}
