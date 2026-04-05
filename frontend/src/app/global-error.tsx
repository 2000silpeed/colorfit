"use client";

import { useEffect } from "react";

interface GlobalErrorProps {
  error: Error & { digest?: string };
  reset: () => void;
}

export default function GlobalError({ error, reset }: GlobalErrorProps) {
  useEffect(() => {
    console.error("[global-error]", error);
  }, [error]);

  return (
    <html lang="ko">
      <body
        style={{
          margin: 0,
          minHeight: "100vh",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          background: "#F8F6F3",
          color: "#1A1714",
          fontFamily: "system-ui, sans-serif",
          padding: "24px",
        }}
      >
        <div style={{ maxWidth: 360, textAlign: "center" }}>
          <h1 style={{ fontSize: 20, fontWeight: 700, margin: "0 0 8px" }}>
            문제가 발생했어요
          </h1>
          <p style={{ fontSize: 14, color: "#6B6460", margin: "0 0 24px" }}>
            잠시 후 다시 시도해 주세요. 같은 문제가 반복되면 홈으로 돌아가 주세요.
          </p>
          <div style={{ display: "flex", gap: 12, justifyContent: "center" }}>
            <button
              type="button"
              onClick={reset}
              style={{
                minWidth: 112,
                minHeight: 44,
                padding: "0 20px",
                border: "none",
                borderRadius: 8,
                background: "#964F4C",
                color: "#FFFFFF",
                fontSize: 14,
                fontWeight: 600,
                cursor: "pointer",
              }}
            >
              다시 시도
            </button>
            <a
              href="/"
              style={{
                minWidth: 112,
                minHeight: 44,
                padding: "0 20px",
                borderRadius: 8,
                border: "1px solid #D4CCC4",
                color: "#1A1714",
                fontSize: 14,
                fontWeight: 600,
                textDecoration: "none",
                display: "inline-flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              홈으로
            </a>
          </div>
        </div>
      </body>
    </html>
  );
}
