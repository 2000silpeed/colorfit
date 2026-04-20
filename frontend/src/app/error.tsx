"use client";

import { useEffect } from "react";
import Link from "next/link";

interface ErrorProps {
  error: Error & { digest?: string };
  reset: () => void;
}

export default function RouteError({ error, reset }: ErrorProps) {
  useEffect(() => {
    console.error("[route-error]", error);
  }, [error]);

  return (
    <div className="flex min-h-[80vh] flex-col items-center justify-center px-6 text-center">
      <h1 className="mb-2 font-display text-[22px] font-semibold text-[var(--color-text-primary)]">
        잠시 문제가 있었어요
      </h1>
      <p className="mb-6 text-sm text-[var(--color-text-secondary)]">
        페이지를 불러오지 못했습니다. 다시 시도하거나 홈으로 돌아가 주세요.
      </p>
      <div className="flex gap-3">
        <button
          type="button"
          onClick={reset}
          className="inline-flex min-h-[44px] min-w-[112px] items-center justify-center rounded-lg bg-[#964F4C] px-5 text-sm font-semibold text-white"
        >
          다시 시도
        </button>
        <Link
          href="/"
          className="inline-flex min-h-[44px] min-w-[112px] items-center justify-center rounded-lg border border-[var(--color-border)] px-5 text-sm font-semibold text-[var(--color-text-primary)]"
        >
          홈으로
        </Link>
      </div>
    </div>
  );
}
