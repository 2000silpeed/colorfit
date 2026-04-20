"use client";

import { Suspense, useCallback } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Image from "next/image";
import { motion, useReducedMotion } from "framer-motion";
import { sanitizeReturnUrl } from "@/lib/auth";
import { migrateLegacyTones } from "@/lib/toneMigration";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default function LoginPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-bg-primary" />}>
      <LoginContent />
    </Suspense>
  );
}

function LoginContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const prefersReducedMotion = useReducedMotion();
  const returnUrl = sanitizeReturnUrl(searchParams.get("returnUrl"));

  const handleKakaoLogin = useCallback(() => {
    const state = crypto.randomUUID();
    sessionStorage.setItem("oauth_state", state);
    if (returnUrl) sessionStorage.setItem("colorfit_return_url", returnUrl);
    window.location.href = `${API_BASE}/api/auth/kakao?state=${state}`;
  }, [returnUrl]);

  const handleGoogleLogin = useCallback(() => {
    const state = crypto.randomUUID();
    sessionStorage.setItem("oauth_state", state);
    if (returnUrl) sessionStorage.setItem("colorfit_return_url", returnUrl);
    window.location.href = `${API_BASE}/api/auth/google?state=${state}`;
  }, [returnUrl]);

  const handleGuest = useCallback(() => {
    if (typeof window !== "undefined") {
      migrateLegacyTones();
      let userId = localStorage.getItem("colorfit_user_id");
      if (!userId) {
        userId = crypto.randomUUID();
        localStorage.setItem("colorfit_user_id", userId);
      }
      sessionStorage.removeItem("colorfit_return_url");
      const tone = localStorage.getItem("colorfit_tone");
      if (tone) {
        router.push(returnUrl ?? "/feed");
      } else {
        router.push("/onboarding/step1");
      }
    }
  }, [router, returnUrl]);

  return (
    <div className="relative min-h-screen flex flex-col items-center px-[32px] pt-[12vh] pb-[6vh] overflow-hidden bg-bg-primary">
      {/* 에디토리얼 패션 배경 */}
      <Image
        src="/editorial-bg.png"
        alt="Editorial Fashion Background"
        fill
        className="object-cover object-top opacity-85 z-0"
        priority
      />
      {/* 그라데이션 ও버레이 (글라스모피즘/페이드 효과) */}
      <div className="absolute inset-0 bg-gradient-to-b from-[#F8F6F3]/30 via-[#F8F6F3]/60 to-[#F8F6F3] z-0 pointer-events-none" />

      {/* 내부 콘텐츠 (z-index) */}
      <div className="relative z-10 w-full flex-1 flex flex-col justify-between items-center max-w-[380px] mx-auto">
      {/* 로��� + 서브카피 */}
      <motion.div
        className="flex flex-col items-center w-full"
        initial={prefersReducedMotion ? false : { opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={prefersReducedMotion ? { duration: 0 } : { duration: 0.6 }}
      >
        <h1 className="font-display text-[48px] font-semibold tracking-[-0.02em] text-accent">
          ColorFit
        </h1>
        <p className="mt-[20px] font-body text-[15px] font-medium tracking-[0.02em] text-center leading-[1.6] text-text-primary/90 drop-shadow-sm">
          내 색을 아는 순간,<br />선택이 쉬워진다
        </p>
      </motion.div>

      {/* 하단 영역: 로그인 카드 + 게스트 */}
      <div className="w-full flex flex-col items-center gap-[24px]">
        <motion.div
          className="w-full"
          initial={prefersReducedMotion ? false : { opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={
          prefersReducedMotion
            ? { duration: 0 }
            : { duration: 0.6, delay: 0.15 }
        }
      >
        <Card className="border-white/50 bg-white/75 backdrop-blur-xl shadow-[0_8px_30px_rgb(0,0,0,0.06)] rounded-[16px] overflow-hidden">
          <CardContent className="flex flex-col gap-[12px] p-[20px]">
            {/* 카카오 로그인 */}
            <Button
              variant="outline"
              size="lg"
              onClick={handleKakaoLogin}
              className="relative w-full h-[48px] text-[15px] font-medium bg-[#FEE500] text-[#191919] border-[#FEE500] hover:bg-[#FEE500]/90 hover:text-[#191919]"
            >
              <svg
                className="absolute left-[16px]"
                width="20"
                height="20"
                viewBox="0 0 24 24"
                fill="#191919"
              >
                <path d="M12 3C6.477 3 2 6.463 2 10.691c0 2.72 1.804 5.108 4.516 6.445l-.946 3.527c-.082.306.254.556.52.387l4.2-2.78c.558.065 1.127.1 1.71.1 5.523 0 10-3.463 10-7.679S17.523 3 12 3z" />
              </svg>
              카카오로 시작하기
            </Button>

            {/* 구글 로그인 */}
            <Button
              variant="outline"
              size="lg"
              onClick={handleGoogleLogin}
              className="relative w-full h-[48px] text-[15px] font-medium bg-white text-text-primary border-border hover:bg-muted"
            >
              <svg
                className="absolute left-[16px]"
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
            </Button>
          </CardContent>
        </Card>
      </motion.div>

      {/* 구분선 + 게스트 */}
      <motion.div
        className="w-full flex flex-col items-center mt-[24px] gap-[16px]"
        initial={prefersReducedMotion ? false : { opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={
          prefersReducedMotion
            ? { duration: 0 }
            : { duration: 0.6, delay: 0.3 }
        }
      >
        <div className="flex items-center w-full gap-[12px]">
          <Separator className="flex-1" />
          <span className="font-body text-[12px] text-text-tertiary">또는</span>
          <Separator className="flex-1" />
        </div>
        <Button
          variant="ghost"
          onClick={handleGuest}
          className="font-body text-[14px] text-text-tertiary hover:text-text-secondary"
        >
          게스트로 둘러보기
        </Button>
      </motion.div>
      </div>
      </div>
    </div>
  );
}
