"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";

import { migrateLegacyTones } from "@/lib/toneMigration";

export default function Home() {
  const router = useRouter();
  const [showSplash, setShowSplash] = useState(true);

  useEffect(() => {
    migrateLegacyTones();
    const token = localStorage.getItem("colorfit_token");
    const tone = localStorage.getItem("colorfit_tone");
    const userId = localStorage.getItem("colorfit_user_id");

    const timer = setTimeout(() => {
      setShowSplash(false);
      if (token && tone) {
        router.replace("/feed");
      } else if (userId && tone) {
        // guest with tone → feed
        router.replace("/feed");
      } else {
        router.replace("/login");
      }
    }, 1500); // 1.5s splash

    return () => clearTimeout(timer);
  }, [router]);

  if (showSplash) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#F8F6F3]">
        <motion.h1
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.8, ease: "easeOut" }}
          className="font-display text-[48px] font-semibold tracking-[-0.02em] text-accent"
        >
          ColorFit
        </motion.h1>
      </div>
    );
  }

  return null;
}
