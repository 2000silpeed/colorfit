"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import {
  fetchBrandGroups,
  fetchPreferredBrands,
  savePreferredBrands,
} from "@/lib/api";

export default function BrandsPage() {
  const router = useRouter();
  const [groups, setGroups] = useState<Record<string, string[]>>({});
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [initialSelected, setInitialSelected] = useState<Set<string>>(new Set());
  const [status, setStatus] = useState<"loading" | "ready" | "saving">("loading");
  const [toast, setToast] = useState<string | null>(null);

  const userId = typeof window !== "undefined"
    ? localStorage.getItem("colorfit_user_id") ?? ""
    : "";

  useEffect(() => {
    async function load() {
      try {
        const [brandData, prefData] = await Promise.all([
          fetchBrandGroups(),
          userId ? fetchPreferredBrands(userId) : Promise.resolve({ preferred_brands: [] }),
        ]);
        setGroups(brandData.groups);
        const savedSet = new Set(prefData.preferred_brands);
        setSelected(savedSet);
        setInitialSelected(savedSet);

        // localStorage에도 동기화
        if (prefData.preferred_brands.length > 0) {
          localStorage.setItem("colorfit_preferred_brands", JSON.stringify(prefData.preferred_brands));
        }
      } catch {
        // fallback: localStorage에서 로드
        try {
          const stored = JSON.parse(localStorage.getItem("colorfit_preferred_brands") || "[]");
          setSelected(new Set(stored));
          setInitialSelected(new Set(stored));
        } catch { /* empty */ }
      } finally {
        setStatus("ready");
      }
    }
    load();
  }, [userId]);

  const toggleBrand = useCallback((brand: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(brand)) next.delete(brand);
      else next.add(brand);
      return next;
    });
  }, []);

  const selectAllInGroup = useCallback((brands: string[]) => {
    setSelected((prev) => {
      const next = new Set(prev);
      const allSelected = brands.every((b) => next.has(b));
      if (allSelected) {
        brands.forEach((b) => next.delete(b));
      } else {
        brands.forEach((b) => next.add(b));
      }
      return next;
    });
  }, []);

  const handleSave = useCallback(async () => {
    const brandList = Array.from(selected);
    setStatus("saving");

    // localStorage 즉시 저장
    localStorage.setItem("colorfit_preferred_brands", JSON.stringify(brandList));

    // DB 저장 시도
    if (userId) {
      try {
        await savePreferredBrands(userId, brandList);
      } catch {
        // DB 실패해도 localStorage에는 저장됨
      }
    }

    setInitialSelected(new Set(selected));
    setStatus("ready");
    setToast(`${brandList.length}개 브랜드 저장 완료`);
    setTimeout(() => setToast(null), 1500);
  }, [selected, userId]);

  const hasChanges = (() => {
    if (selected.size !== initialSelected.size) return true;
    for (const b of selected) {
      if (!initialSelected.has(b)) return true;
    }
    return false;
  })();

  if (status === "loading") {
    return (
      <div className="min-h-screen bg-bg-primary px-[20px] pt-[56px]">
        <div className="h-[24px] w-1/3 rounded bg-[#E0DCD7] animate-pulse mb-[32px]" />
        {[...Array(3)].map((_, i) => (
          <div key={i} className="mb-[24px]">
            <div className="h-[16px] w-1/4 rounded bg-[#E0DCD7] animate-pulse mb-[12px]" />
            <div className="flex flex-wrap gap-[8px]">
              {[...Array(6)].map((_, j) => (
                <div key={j} className="h-[36px] w-[80px] rounded-full bg-[#E0DCD7] animate-pulse" />
              ))}
            </div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-bg-primary pb-[120px]">
      {/* 헤더 */}
      <header className="sticky top-0 z-30 bg-bg-primary/95 backdrop-blur-sm">
        <div className="flex items-center justify-between px-[20px] h-[52px] max-w-[768px] mx-auto">
          <button
            type="button"
            onClick={() => router.back()}
            className="w-[32px] h-[32px] flex items-center justify-center"
            aria-label="뒤로 가기"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--color-text-primary)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="15 18 9 12 15 6" />
            </svg>
          </button>
          <span className="font-display text-[18px] text-text-primary font-bold">
            선호 브랜드
          </span>
          <span className="text-[14px] font-body text-accent font-medium">
            {selected.size}개
          </span>
        </div>
      </header>

      {/* 설명 */}
      <div className="px-[20px] pt-[8px] pb-[20px] max-w-[768px] mx-auto">
        <p className="font-body text-[14px] text-text-secondary">
          좋아하는 브랜드를 선택하면 피드에서 우선 추천해드려요.
        </p>
      </div>

      {/* 브랜드 그룹 */}
      <main className="px-[20px] max-w-[768px] mx-auto">
        {Object.entries(groups).map(([groupName, brands]) => {
          const allSelected = brands.every((b) => selected.has(b));
          return (
            <section key={groupName} className="mb-[28px]">
              <div className="flex items-center justify-between mb-[12px]">
                <h2 className="font-display text-[15px] text-text-primary font-medium">
                  {groupName}
                </h2>
                <button
                  type="button"
                  onClick={() => selectAllInGroup(brands)}
                  className="text-[12px] font-body text-text-tertiary"
                >
                  {allSelected ? "전체 해제" : "전체 선택"}
                </button>
              </div>
              <div className="flex flex-wrap gap-[8px]">
                {brands.map((brand) => {
                  const isSelected = selected.has(brand);
                  return (
                    <button
                      key={brand}
                      type="button"
                      onClick={() => toggleBrand(brand)}
                      className={`px-[14px] py-[8px] rounded-full text-[13px] font-body transition-colors ${
                        isSelected
                          ? "bg-accent text-white"
                          : "bg-bg-secondary text-text-secondary border border-border"
                      }`}
                    >
                      {brand}
                    </button>
                  );
                })}
              </div>
            </section>
          );
        })}
      </main>

      {/* 저장 버튼 (sticky bottom) */}
      {hasChanges && (
        <motion.div
          className="fixed bottom-[80px] left-0 right-0 px-[20px] z-40"
          initial={{ y: 40, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ type: "spring", stiffness: 300, damping: 30 }}
        >
          <div className="max-w-[768px] mx-auto">
            <button
              type="button"
              onClick={handleSave}
              disabled={status === "saving"}
              className="w-full py-[14px] rounded-[12px] bg-accent text-white text-[16px] font-body font-medium shadow-lg disabled:opacity-50"
            >
              {status === "saving" ? "저장 중..." : `${selected.size}개 브랜드 저장`}
            </button>
          </div>
        </motion.div>
      )}

      {/* 토스트 */}
      {toast && (
        <motion.div
          className="fixed bottom-[140px] left-1/2 -translate-x-1/2 z-50 bg-[#333] text-white text-[14px] font-body px-[20px] py-[10px] rounded-full shadow-lg"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 20 }}
          transition={{ duration: 0.2 }}
        >
          {toast}
        </motion.div>
      )}
    </div>
  );
}
