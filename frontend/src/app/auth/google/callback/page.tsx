"use client";

import { useEffect, useRef } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { postOAuthCallback } from "@/lib/api";

export default function GoogleCallbackPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const processed = useRef(false);

  useEffect(() => {
    if (processed.current) return;
    processed.current = true;

    const code = searchParams.get("code");
    const state = searchParams.get("state");
    const savedState = sessionStorage.getItem("oauth_state");
    sessionStorage.removeItem("oauth_state");

    if (!code || !state || state !== savedState) {
      router.replace("/login");
      return;
    }

    const guestUserId = localStorage.getItem("colorfit_user_id");

    postOAuthCallback("google", code, guestUserId)
      .then((data) => {
        localStorage.setItem("colorfit_token", data.access_token);
        localStorage.setItem("colorfit_user_id", data.user_id);

        const tone = localStorage.getItem("colorfit_tone");
        if (data.is_new_user || !tone) {
          router.replace("/onboarding/step1");
        } else {
          router.replace("/feed");
        }
      })
      .catch(() => {
        router.replace("/login");
      });
  }, [router, searchParams]);

  return (
    <div
      className="min-h-screen flex items-center justify-center"
      style={{ backgroundColor: "var(--color-bg-primary)" }}
    >
      <p
        className="text-[15px]"
        style={{
          fontFamily: "var(--font-body)",
          color: "var(--color-text-secondary)",
        }}
      >
        로그인 중...
      </p>
    </div>
  );
}
