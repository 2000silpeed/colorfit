"use client";

import { useState, useRef, useCallback } from "react";
import Image from "next/image";
import { motion, useReducedMotion } from "framer-motion";

interface PhotoUploaderProps {
  onFileReady: (file: File, previewUrl: string) => void;
  disabled?: boolean;
}

const MAX_SIZE = 1024;
const QUALITY = 0.8;
const ACCEPTED_TYPES = ["image/jpeg", "image/png", "image/webp", "image/heic", "image/heif"];
const MAX_FILE_SIZE = 20 * 1024 * 1024; // 20MB

function resizeImage(file: File): Promise<File> {
  return new Promise((resolve, reject) => {
    const img = new window.Image();
    const url = URL.createObjectURL(file);

    img.onload = () => {
      URL.revokeObjectURL(url);

      const { width, height } = img;
      if (width <= MAX_SIZE && height <= MAX_SIZE) {
        resolve(file);
        return;
      }

      const ratio = Math.min(MAX_SIZE / width, MAX_SIZE / height);
      const newW = Math.round(width * ratio);
      const newH = Math.round(height * ratio);

      const canvas = document.createElement("canvas");
      canvas.width = newW;
      canvas.height = newH;
      const ctx = canvas.getContext("2d");
      if (!ctx) {
        reject(new Error("Canvas context를 생성할 수 없습니다."));
        return;
      }

      ctx.drawImage(img, 0, 0, newW, newH);
      canvas.toBlob(
        (blob) => {
          if (!blob) {
            reject(new Error("이미지 변환에 실패했습니다."));
            return;
          }
          const resized = new File([blob], file.name.replace(/\.\w+$/, ".jpg"), {
            type: "image/jpeg",
          });
          resolve(resized);
        },
        "image/jpeg",
        QUALITY,
      );
    };

    img.onerror = () => {
      URL.revokeObjectURL(url);
      reject(new Error("이미지를 읽을 수 없습니다."));
    };

    img.src = url;
  });
}

export default function PhotoUploader({ onFileReady, disabled }: PhotoUploaderProps) {
  const prefersReducedMotion = useReducedMotion();
  const cameraRef = useRef<HTMLInputElement>(null);
  const galleryRef = useRef<HTMLInputElement>(null);

  const [preview, setPreview] = useState<string | null>(null);
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFile = useCallback(
    async (file: File) => {
      setError(null);

      if (!ACCEPTED_TYPES.includes(file.type) && !file.type.startsWith("image/")) {
        setError("이미지 파일만 업로드할 수 있어요.");
        return;
      }
      if (file.size > MAX_FILE_SIZE) {
        setError("20MB 이하 파일만 업로드할 수 있어요.");
        return;
      }

      setProcessing(true);
      try {
        const resized = await resizeImage(file);
        const previewUrl = URL.createObjectURL(resized);
        setPreview(previewUrl);
        onFileReady(resized, previewUrl);
      } catch (err) {
        setError(err instanceof Error ? err.message : "이미지 처리 중 오류가 발생했어요.");
      } finally {
        setProcessing(false);
      }
    },
    [onFileReady],
  );

  const handleInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) handleFile(file);
      e.target.value = "";
    },
    [handleFile],
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [handleFile],
  );

  const handleReset = useCallback(() => {
    if (preview) URL.revokeObjectURL(preview);
    setPreview(null);
    setError(null);
  }, [preview]);

  /* ---- 프리뷰 상태 ---- */
  if (preview) {
    return (
      <motion.div
        className="relative w-full rounded-[var(--radius-lg)] overflow-hidden bg-bg-secondary"
        style={{ aspectRatio: "3/4", maxHeight: "420px" }}
        initial={prefersReducedMotion ? false : { scale: 0.95, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={prefersReducedMotion ? { duration: 0 } : { type: "spring", stiffness: 300, damping: 30 }}
      >
        <Image
          src={preview}
          alt="선택한 옷"
          fill
          sizes="(max-width: 768px) 100vw, 768px"
          className="object-cover"
          priority
        />
        <button
          type="button"
          onClick={handleReset}
          disabled={disabled}
          className="absolute top-[12px] right-[12px] w-[32px] h-[32px] rounded-full bg-black/40 flex items-center justify-center"
          aria-label="사진 다시 선택"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" strokeWidth="2" strokeLinecap="round">
            <path d="M18 6L6 18M6 6l12 12" />
          </svg>
        </button>
      </motion.div>
    );
  }

  /* ---- 업로드 영역 ---- */
  return (
    <div>
      <div
        className="w-full rounded-[var(--radius-lg)] border-2 border-dashed border-border bg-bg-secondary flex flex-col items-center justify-center py-[48px] px-[20px]"
        style={{ minHeight: "280px" }}
        role="region"
        aria-label="옷 사진 업로드 영역"
        onDrop={handleDrop}
        onDragOver={(e) => e.preventDefault()}
      >
        {processing ? (
          <div className="flex flex-col items-center gap-[12px]">
            <div className="w-[40px] h-[40px] border-3 border-accent border-t-transparent rounded-full animate-spin" />
            <p className="font-body text-[14px] text-text-secondary">
              이미지 처리 중...
            </p>
          </div>
        ) : (
          <>
            <div className="w-[64px] h-[64px] rounded-full bg-bg-primary flex items-center justify-center mb-[16px]">
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="var(--color-accent)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                <rect x="3" y="3" width="18" height="18" rx="2" />
                <circle cx="8.5" cy="8.5" r="1.5" />
                <path d="M21 15l-5-5L5 21" />
              </svg>
            </div>
            <p className="font-display text-[16px] text-text-primary mb-[4px]">
              옷 사진을 올려주세요
            </p>
            <p className="font-body text-[13px] text-text-tertiary mb-[20px] text-center">
              카메라로 촬영하거나 갤러리에서 선택할 수 있어요
            </p>

            <div className="flex gap-[12px]">
              {/* 카메라 */}
              <button
                type="button"
                onClick={() => cameraRef.current?.click()}
                disabled={disabled}
                className="flex items-center gap-[6px] px-[16px] py-[10px] bg-accent text-white font-body text-[14px] font-medium rounded-[var(--radius-full)]"
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M23 19a2 2 0 01-2 2H3a2 2 0 01-2-2V8a2 2 0 012-2h4l2-3h6l2 3h4a2 2 0 012 2z" />
                  <circle cx="12" cy="13" r="4" />
                </svg>
                촬영
              </button>

              {/* 갤러리 */}
              <button
                type="button"
                onClick={() => galleryRef.current?.click()}
                disabled={disabled}
                className="flex items-center gap-[6px] px-[16px] py-[10px] border border-accent text-accent font-body text-[14px] font-medium rounded-[var(--radius-full)]"
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <rect x="3" y="3" width="18" height="18" rx="2" />
                  <circle cx="8.5" cy="8.5" r="1.5" />
                  <path d="M21 15l-5-5L5 21" />
                </svg>
                갤러리
              </button>
            </div>
          </>
        )}
      </div>

      {error && (
        <p className="font-body text-[13px] mt-[8px] px-[4px]" style={{ color: "var(--color-accent)" }}>
          {error}
        </p>
      )}

      {/* Hidden inputs */}
      <input
        ref={cameraRef}
        type="file"
        accept="image/*"
        capture="environment"
        className="hidden"
        onChange={handleInputChange}
        data-testid="camera-input"
      />
      <input
        ref={galleryRef}
        type="file"
        accept="image/*"
        className="hidden"
        onChange={handleInputChange}
        data-testid="gallery-input"
      />
    </div>
  );
}
