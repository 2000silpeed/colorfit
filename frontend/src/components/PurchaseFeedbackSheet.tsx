"use client";

import { useState, useCallback } from "react";
import { motion, AnimatePresence, useReducedMotion } from "framer-motion";
import {
  postPurchaseFeedback,
  type PurchaseFeedbackAction,
  type PurchaseFeedbackReason,
} from "@/lib/api";

interface PurchaseFeedbackSheetProps {
  outfitId: string;
  userId: string;
  onClose: () => void;
}

const REASON_TAGS: { value: PurchaseFeedbackReason; label: string }[] = [
  { value: "price_mismatch", label: "가격이 맞지 않아요" },
  { value: "style_different", label: "스타일이 달라요" },
  { value: "sold_out", label: "품절이에요" },
  { value: "other", label: "기타" },
];

export default function PurchaseFeedbackSheet({
  outfitId,
  userId,
  onClose,
}: PurchaseFeedbackSheetProps) {
  const prefersReducedMotion = useReducedMotion();
  const [step, setStep] = useState<"main" | "reason">("main");
  const [sending, setSending] = useState(false);

  const sendFeedback = useCallback(
    async (action: PurchaseFeedbackAction, reason?: PurchaseFeedbackReason) => {
      setSending(true);
      try {
        await postPurchaseFeedback(userId, outfitId, action, reason);
      } catch {
        // 실패해도 UX 차단하지 않음
      } finally {
        setSending(false);
        onClose();
      }
    },
    [userId, outfitId, onClose],
  );

  const handleAction = useCallback(
    (action: PurchaseFeedbackAction) => {
      if (action === "not_helpful") {
        setStep("reason");
      } else {
        sendFeedback(action);
      }
    },
    [sendFeedback],
  );

  return (
    <motion.div
      className="fixed inset-0 z-[70] flex items-end justify-center"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
    >
      <div className="absolute inset-0 bg-black/40" onClick={onClose} />
      <motion.div
        className="relative w-full max-w-[430px] rounded-t-[var(--radius-xl)] px-[20px] pt-[24px]"
        style={{
          backgroundColor: "var(--color-bg-primary)",
          paddingBottom: "calc(24px + env(safe-area-inset-bottom, 0px))",
        }}
        initial={prefersReducedMotion ? false : { y: "100%" }}
        animate={{ y: 0 }}
        exit={{ y: "100%" }}
        transition={
          prefersReducedMotion
            ? { duration: 0 }
            : { type: "spring", stiffness: 300, damping: 30 }
        }
      >
        <AnimatePresence mode="wait">
          {step === "main" ? (
            <motion.div
              key="main"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.15 }}
            >
              <h3
                className="text-[18px] text-center mb-[24px]"
                style={{
                  fontFamily: "var(--font-display)",
                  color: "var(--color-text-primary)",
                }}
              >
                이 추천이 도움이 됐나요?
              </h3>

              <div className="flex justify-center gap-[16px] mb-[20px]">
                <button
                  type="button"
                  disabled={sending}
                  onClick={() => handleAction("purchase")}
                  className="flex flex-col items-center gap-[8px] px-[20px] py-[16px] rounded-[var(--radius-lg)] border transition-colors"
                  style={{
                    borderColor: "var(--color-border)",
                    backgroundColor: "var(--color-bg-secondary)",
                  }}
                >
                  <span className="text-[28px]" role="img" aria-label="구매했어요">
                    👍
                  </span>
                  <span
                    className="text-[13px]"
                    style={{
                      fontFamily: "var(--font-body)",
                      color: "var(--color-text-primary)",
                    }}
                  >
                    구매했어요
                  </span>
                </button>

                <button
                  type="button"
                  disabled={sending}
                  onClick={() => handleAction("considering")}
                  className="flex flex-col items-center gap-[8px] px-[20px] py-[16px] rounded-[var(--radius-lg)] border transition-colors"
                  style={{
                    borderColor: "var(--color-border)",
                    backgroundColor: "var(--color-bg-secondary)",
                  }}
                >
                  <span className="text-[28px]" role="img" aria-label="고민 중이에요">
                    🤔
                  </span>
                  <span
                    className="text-[13px]"
                    style={{
                      fontFamily: "var(--font-body)",
                      color: "var(--color-text-primary)",
                    }}
                  >
                    고민 중이에요
                  </span>
                </button>

                <button
                  type="button"
                  disabled={sending}
                  onClick={() => handleAction("not_helpful")}
                  className="flex flex-col items-center gap-[8px] px-[20px] py-[16px] rounded-[var(--radius-lg)] border transition-colors"
                  style={{
                    borderColor: "var(--color-border)",
                    backgroundColor: "var(--color-bg-secondary)",
                  }}
                >
                  <span className="text-[28px]" role="img" aria-label="아니에요">
                    👎
                  </span>
                  <span
                    className="text-[13px]"
                    style={{
                      fontFamily: "var(--font-body)",
                      color: "var(--color-text-primary)",
                    }}
                  >
                    아니에요
                  </span>
                </button>
              </div>

              <button
                type="button"
                onClick={onClose}
                className="block mx-auto text-[13px] py-[8px]"
                style={{
                  fontFamily: "var(--font-body)",
                  color: "var(--color-text-tertiary)",
                }}
              >
                나중에
              </button>
            </motion.div>
          ) : (
            <motion.div
              key="reason"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.15 }}
            >
              <h3
                className="text-[16px] text-center mb-[20px]"
                style={{
                  fontFamily: "var(--font-display)",
                  color: "var(--color-text-primary)",
                }}
              >
                어떤 점이 아쉬웠나요?
              </h3>

              <div className="flex flex-wrap justify-center gap-[8px] mb-[20px]">
                {REASON_TAGS.map((tag) => (
                  <button
                    key={tag.value}
                    type="button"
                    disabled={sending}
                    onClick={() => sendFeedback("not_helpful", tag.value)}
                    className="px-[16px] py-[10px] rounded-full border text-[13px] transition-colors"
                    style={{
                      fontFamily: "var(--font-body)",
                      borderColor: "var(--color-border)",
                      color: "var(--color-text-primary)",
                      backgroundColor: "var(--color-bg-secondary)",
                    }}
                  >
                    {tag.label}
                  </button>
                ))}
              </div>

              <button
                type="button"
                onClick={() => setStep("main")}
                className="block mx-auto text-[13px] py-[8px]"
                style={{
                  fontFamily: "var(--font-body)",
                  color: "var(--color-text-tertiary)",
                }}
              >
                돌아가기
              </button>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>
    </motion.div>
  );
}
