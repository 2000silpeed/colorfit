"use client";

import { usePathname } from "next/navigation";
import Link from "next/link";
import { motion, useReducedMotion } from "framer-motion";

interface TabItem {
  label: string;
  path: string;
  icon: (active: boolean) => React.ReactNode;
}

function FeedIcon({ active }: { active: boolean }) {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke={active ? "var(--color-accent)" : "var(--color-text-tertiary)"} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M3 9.5L12 3l9 6.5V20a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V9.5z" />
      <polyline points="9 21 9 14 15 14 15 21" />
    </svg>
  );
}

function CompareIcon({ active }: { active: boolean }) {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke={active ? "var(--color-accent)" : "var(--color-text-tertiary)"} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="3" width="7" height="18" rx="1" />
      <rect x="14" y="3" width="7" height="18" rx="1" />
    </svg>
  );
}

function SavedIcon({ active }: { active: boolean }) {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill={active ? "var(--color-accent)" : "none"} stroke={active ? "var(--color-accent)" : "var(--color-text-tertiary)"} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78L12 21.23l8.84-8.84a5.5 5.5 0 0 0 0-7.78z" />
    </svg>
  );
}

function ClosetIcon({ active }: { active: boolean }) {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke={active ? "var(--color-accent)" : "var(--color-text-tertiary)"} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <rect x="4" y="4" width="16" height="16" rx="2" />
      <line x1="12" y1="4" x2="12" y2="20" />
      <path d="M9 10h.01" />
      <path d="M15 10h.01" />
    </svg>
  );
}

function ProfileIcon({ active }: { active: boolean }) {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke={active ? "var(--color-accent)" : "var(--color-text-tertiary)"} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
      <circle cx="12" cy="7" r="4" />
    </svg>
  );
}

const tabs: TabItem[] = [
  { label: "피드", path: "/feed", icon: (a) => <FeedIcon active={a} /> },
  { label: "비교", path: "/compare", icon: (a) => <CompareIcon active={a} /> },
  { label: "저장", path: "/saved", icon: (a) => <SavedIcon active={a} /> },
  { label: "옷장", path: "/closet", icon: (a) => <ClosetIcon active={a} /> },
  { label: "마이", path: "/profile", icon: (a) => <ProfileIcon active={a} /> },
];

export default function BottomTabBar() {
  const pathname = usePathname();
  const shouldReduceMotion = useReducedMotion();

  return (
    <nav
      className="fixed bottom-0 left-0 right-0 z-50"
      style={{
        height: "calc(56px + env(safe-area-inset-bottom, 0px))",
        paddingBottom: "env(safe-area-inset-bottom, 0px)",
        backgroundColor: "var(--color-bg-primary)",
        borderTop: "1px solid var(--color-border)",
      }}
      role="tablist"
      aria-label="메인 네비게이션"
    >
      <div className="flex items-center justify-around h-[56px] max-w-[430px] mx-auto">
        {tabs.map((tab) => {
          const isActive = pathname === tab.path || pathname.startsWith(tab.path + "/");

          return (
            <Link
              key={tab.path}
              href={tab.path}
              role="tab"
              aria-selected={isActive}
              aria-label={tab.label}
              className="flex flex-col items-center justify-center flex-1 h-full min-w-[44px] min-h-[44px] active:scale-[0.95] active:opacity-70 transition-transform duration-100"
            >
              <motion.div
                key={`icon-${tab.path}-${isActive}`}
                initial={shouldReduceMotion ? false : { scale: 0.92 }}
                animate={{ scale: 1 }}
                transition={
                  shouldReduceMotion
                    ? { duration: 0 }
                    : { type: "spring", stiffness: 400, damping: 20 }
                }
              >
                {tab.icon(isActive)}
              </motion.div>
              <span
                className="text-[10px] leading-[1.4] mt-[2px]"
                style={{
                  color: isActive ? "var(--color-accent)" : "var(--color-text-tertiary)",
                  fontWeight: isActive ? 600 : 400,
                  fontFamily: "var(--font-body)",
                  letterSpacing: "0.01em",
                }}
              >
                {tab.label}
              </span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
