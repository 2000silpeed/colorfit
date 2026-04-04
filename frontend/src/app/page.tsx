"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    const token = localStorage.getItem("colorfit_token");
    const tone = localStorage.getItem("colorfit_tone");
    const userId = localStorage.getItem("colorfit_user_id");

    if (token && tone) {
      router.replace("/feed");
    } else if (userId && tone) {
      // guest with tone → feed
      router.replace("/feed");
    } else {
      router.replace("/login");
    }
  }, [router]);

  return null;
}
