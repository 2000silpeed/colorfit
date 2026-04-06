"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";
import { motion, AnimatePresence, useReducedMotion } from "framer-motion";

interface TryonImage {
  outfitId: string;
  imageUrl: string;
  createdAt: string;
}

export default function TryonGalleryPage() {
  const router = useRouter();
  const prefersReducedMotion = useReducedMotion();
  const [images, setImages] = useState<TryonImage[]>([]);
  const [selectedImage, setSelectedImage] = useState<TryonImage | null>(null);

  useEffect(() => {
    const raw = localStorage.getItem("colorfit_tryon_images");
    if (raw) {
      try {
        setImages(JSON.parse(raw));
      } catch { /* ignore */ }
    }
  }, []);

  const handleDelete = useCallback((imageUrl: string) => {
    setImages((prev) => {
      const next = prev.filter((img) => img.imageUrl !== imageUrl);
      localStorage.setItem("colorfit_tryon_images", JSON.stringify(next));
      return next;
    });
    setSelectedImage(null);
  }, []);

  return (
    <div
      className="min-h-screen"
      style={{
        backgroundColor: "var(--color-bg-primary)",
        paddingBottom: "calc(80px + env(safe-area-inset-bottom, 0px))",
      }}
    >
      {/* Header */}
      <header className="sticky top-0 z-10 bg-[var(--color-bg-primary)]">
        <div className="flex items-center px-[20px] h-[52px] gap-[12px]">
          <button
            type="button"
            onClick={() => router.back()}
            className="w-[44px] h-[44px] flex items-center justify-center -ml-[8px]"
            aria-label="뒤로 가기"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--color-text-primary)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="15 18 9 12 15 6" />
            </svg>
          </button>
          <h1 className="font-display text-[18px] text-[var(--color-text-primary)] font-bold">
            AI 착장 갤러리
          </h1>
        </div>
      </header>

      {/* Empty */}
      {images.length === 0 && (
        <div className="flex flex-col items-center justify-center px-[20px] pt-[120px]">
          <div
            className="w-[80px] h-[80px] rounded-full flex items-center justify-center mb-[16px]"
            style={{ backgroundColor: "var(--color-bg-secondary)" }}
          >
            <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="var(--color-text-tertiary)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
              <rect x="3" y="3" width="18" height="18" rx="2" />
              <circle cx="8.5" cy="8.5" r="1.5" />
              <path d="m21 15-5-5L5 21" />
            </svg>
          </div>
          <p className="font-display text-[18px] text-[var(--color-text-primary)] mb-[8px]">
            저장된 착장이 없어요
          </p>
          <p className="font-body text-[14px] text-[var(--color-text-secondary)] text-center mb-[24px]">
            코디 상세에서 "착장으로 보기"를 사용하면{"\n"}생성된 이미지를 여기서 볼 수 있어요
          </p>
          <button
            type="button"
            onClick={() => router.push("/feed")}
            className="px-[24px] py-[14px] rounded-[var(--radius-full)] text-[15px] font-body font-medium"
            style={{ backgroundColor: "var(--color-accent)", color: "#FFFFFF" }}
          >
            코디 피드 둘러보기
          </button>
        </div>
      )}

      {/* Grid */}
      {images.length > 0 && (
        <div className="grid grid-cols-2 gap-[12px] px-[20px] pt-[8px]">
          {images.map((img, i) => (
            <motion.button
              key={img.imageUrl}
              type="button"
              onClick={() => setSelectedImage(img)}
              className="w-full text-left"
              initial={prefersReducedMotion ? false : { opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={
                prefersReducedMotion
                  ? { duration: 0 }
                  : { delay: i * 0.05, duration: 0.3 }
              }
            >
              <div
                className="relative w-full rounded-[var(--radius-lg)] overflow-hidden bg-[var(--color-bg-secondary)]"
                style={{ aspectRatio: "3/4" }}
              >
                <Image
                  src={img.imageUrl}
                  alt="AI 착장"
                  fill
                  sizes="(max-width: 430px) 50vw, 200px"
                  className="object-cover"
                  loading="lazy"
                  unoptimized
                />
              </div>
              <p className="font-body text-[12px] text-[var(--color-text-tertiary)] mt-[4px]">
                {new Date(img.createdAt).toLocaleDateString("ko-KR")}
              </p>
            </motion.button>
          ))}
        </div>
      )}

      {/* Lightbox */}
      <AnimatePresence>
        {selectedImage && (
          <>
            <motion.div
              className="fixed inset-0 bg-black/60 z-40"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setSelectedImage(null)}
            />
            <motion.div
              className="fixed inset-0 z-50 flex flex-col items-center justify-center px-[20px]"
              initial={prefersReducedMotion ? false : { opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              transition={prefersReducedMotion ? { duration: 0 } : { duration: 0.2 }}
            >
              <div
                className="relative w-full max-w-[360px] rounded-[var(--radius-lg)] overflow-hidden"
                style={{ aspectRatio: "3/4" }}
              >
                <Image
                  src={selectedImage.imageUrl}
                  alt="AI 착장"
                  fill
                  sizes="360px"
                  className="object-cover"
                  unoptimized
                />
              </div>
              <div className="flex gap-[12px] mt-[16px] w-full max-w-[360px]">
                <button
                  type="button"
                  onClick={() => router.push(`/outfit/${selectedImage.outfitId}`)}
                  className="flex-1 py-[14px] bg-[var(--color-accent)] text-white font-body text-[15px] font-medium rounded-[var(--radius-full)]"
                >
                  코디 보기
                </button>
                <button
                  type="button"
                  onClick={() => handleDelete(selectedImage.imageUrl)}
                  className="flex-1 py-[14px] border border-[var(--color-border)] text-[var(--color-text-primary)] font-body text-[15px] font-medium rounded-[var(--radius-full)]"
                >
                  삭제
                </button>
              </div>
              <button
                type="button"
                onClick={() => setSelectedImage(null)}
                className="mt-[12px] font-body text-[14px] text-white/80"
              >
                닫기
              </button>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  );
}
