"use client";

import { useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { motion, useReducedMotion } from "framer-motion";
import PhotoUploader from "@/components/PhotoUploader";
import { uploadClosetImage } from "@/lib/api";

type PageState = "select" | "uploading" | "error";

const CATEGORIES = [
  { value: "top", label: "상의" },
  { value: "bottom", label: "하의" },
  { value: "outer", label: "아우터" },
  { value: "dress", label: "원피스" },
  { value: "shoes", label: "신발" },
  { value: "bag", label: "가방" },
  { value: "accessory", label: "액세서리" },
] as const;

const MOCK_USER_TONE_ID = "autumn_warm_deep";

export default function ClosetUploadPage() {
  const router = useRouter();
  const prefersReducedMotion = useReducedMotion();

  const [state, setState] = useState<PageState>("select");
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [category, setCategory] = useState("top");
  const [uploadProgress, setUploadProgress] = useState(0);
  const [errorMessage, setErrorMessage] = useState("");

  const handleFileReady = useCallback((f: File, url: string) => {
    setFile(f);
    setPreviewUrl(url);
  }, []);

  const handleSubmit = useCallback(async () => {
    if (!file) return;

    setState("uploading");
    setUploadProgress(0);
    setErrorMessage("");

    try {
      const { image_url } = await uploadClosetImage(file, setUploadProgress);

      const params = new URLSearchParams({
        image_url,
        user_tone_id: MOCK_USER_TONE_ID,
        category,
      });
      router.push(`/closet/analyze?${params.toString()}`);
    } catch (err) {
      setState("error");
      setErrorMessage(
        err instanceof Error ? err.message : "업로드 중 오류가 발생했어요.",
      );
    }
  }, [file, category, router]);

  const handleRetry = useCallback(() => {
    setState("select");
    setUploadProgress(0);
    setErrorMessage("");
  }, []);

  return (
    <div className="min-h-screen bg-bg-primary pb-[120px]">
      {/* 헤더 */}
      <div className="flex items-center px-[20px] pt-[16px] pb-[12px]">
        <button
          type="button"
          onClick={() => window.history.length > 1 ? router.back() : router.push("/closet")}
          className="w-[44px] h-[44px] rounded-full flex items-center justify-center -ml-[12px]"
          aria-label="뒤로가기"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--color-text-primary)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M15 18l-6-6 6-6" />
          </svg>
        </button>
        <h1 className="font-display text-[18px] text-text-primary ml-[4px]">
          옷 분석하기
        </h1>
      </div>

      <div className="px-[20px]">
        {/* 사진 업로드 */}
        <PhotoUploader
          onFileReady={handleFileReady}
          disabled={state === "uploading"}
        />

        {/* 카테고리 선택 */}
        {previewUrl && (
          <motion.div
            className="mt-[24px]"
            initial={prefersReducedMotion ? false : { y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={prefersReducedMotion ? { duration: 0 } : { type: "spring", stiffness: 300, damping: 30 }}
          >
            <h2 className="font-display text-[16px] text-text-primary mb-[12px]">
              어떤 종류의 옷인가요?
            </h2>
            <div className="flex flex-wrap gap-[8px]">
              {CATEGORIES.map((cat) => (
                <button
                  key={cat.value}
                  type="button"
                  onClick={() => setCategory(cat.value)}
                  disabled={state === "uploading"}
                  className={`px-[14px] py-[8px] rounded-[var(--radius-full)] font-body text-[14px] font-medium transition-colors ${
                    category === cat.value
                      ? "bg-accent text-white"
                      : "bg-bg-secondary text-text-secondary border border-border"
                  }`}
                >
                  {cat.label}
                </button>
              ))}
            </div>
          </motion.div>
        )}

        {/* 업로드 진행 상태 */}
        {state === "uploading" && (
          <motion.div
            className="mt-[32px] flex flex-col items-center"
            initial={prefersReducedMotion ? false : { opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={prefersReducedMotion ? { duration: 0 } : { duration: 0.2 }}
          >
            {/* 프로그레스 바 */}
            <div className="w-full h-[4px] rounded-full bg-bg-secondary overflow-hidden mb-[16px]">
              <motion.div
                className="h-full rounded-full bg-accent"
                initial={{ width: 0 }}
                animate={{ width: `${uploadProgress}%` }}
                transition={prefersReducedMotion ? { duration: 0 } : { duration: 0.3 }}
              />
            </div>

            {/* 분석 중 로딩 애니메이션 */}
            <div className="flex flex-col items-center gap-[12px]">
              <div className="relative w-[48px] h-[48px]">
                <motion.div
                  className="absolute inset-0 rounded-full border-3 border-accent border-t-transparent"
                  animate={{ rotate: 360 }}
                  transition={
                    prefersReducedMotion
                      ? { duration: 0 }
                      : { repeat: Infinity, duration: 1, ease: "linear" }
                  }
                />
              </div>
              <p className="font-body text-[14px] text-text-secondary">
                {uploadProgress < 100
                  ? `업로드 중... ${uploadProgress}%`
                  : "AI가 옷을 분석하고 있어요..."}
              </p>
            </div>
          </motion.div>
        )}

        {/* 에러 상태 */}
        {state === "error" && (
          <div className="mt-[24px] p-[16px] rounded-[var(--radius-lg)] bg-error-bg">
            <p className="font-body text-[14px] text-text-primary mb-[12px]">
              {errorMessage}
            </p>
            <button
              type="button"
              onClick={handleRetry}
              className="px-[16px] py-[8px] bg-accent text-white font-body text-[13px] font-medium rounded-[var(--radius-full)]"
            >
              다시 시도하기
            </button>
          </div>
        )}
      </div>

      {/* 하단 CTA */}
      {previewUrl && state === "select" && (
        <div className="fixed bottom-0 left-0 right-0 bg-bg-primary border-t border-border px-[20px] py-[12px] safe-area-bottom">
          <button
            type="button"
            onClick={handleSubmit}
            disabled={!file}
            className="w-full py-[14px] bg-accent text-white font-body text-[15px] font-medium rounded-[var(--radius-full)] disabled:opacity-50"
          >
            분석 시작하기
          </button>
        </div>
      )}
    </div>
  );
}
