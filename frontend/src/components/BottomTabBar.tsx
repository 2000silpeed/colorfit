"use client";

import { usePathname } from "next/navigation";
import Link from "next/link";
import { motion, useReducedMotion } from "framer-motion";

interface TabItem {
  label: string;
  path: string;
  icon: (active: boolean) => React.ReactNode;
}

function HomeIcon({ active }: { active: boolean }) {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke={active ? "var(--color-accent)" : "var(--color-text-tertiary)"} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M3 9.5L12 3l9 6.5V20a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V9.5z" />
      <polyline points="9 21 9 14 15 14 15 21" />
    </svg>
  );
}

function HeartIcon({ active }: { active: boolean }) {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill={active ? "var(--color-accent)" : "none"} stroke={active ? "var(--color-accent)" : "var(--color-text-tertiary)"} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78L12 21.23l8.84-8.84a5.5 5.5 0 0 0 0-7.78z" />
    </svg>
  );
}

function ClosetIcon({ active }: { active: boolean }) {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke={active ? "var(--color-accent)" : "var(--color-text-tertiary)"} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M4 6h16" />
      <path d="M6 6c0-1.1.9-2 2-2h8a2 2 0 0 1 2 2" />
      <path d="M8 6v14" />
      <path d="M16 6v14" />
      <path d="M10 10c.5 1 1.5 2 2 4" />
      <path d="M14 10c-.5 1-1.5 2-2 4" />
    </svg>
  );
}

function UserIcon({ active }: { active: boolean }) {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke={active ? "var(--color-accent)" : "var(--color-text-tertiary)"} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
      <circle cx="12" cy="7" r="4" />
    </svg>
  );
}

const tabs: TabItem[] = [
  { label: "홈", path: "/feed", icon: (a) => <HomeIcon active={a} /> },
  { label: "옷장", path: "/closet", icon: (a) => <ClosetIcon active={a} /> },
  { label: "저장", path: "/saved", icon: (a) => <HeartIcon active={a} /> },
  { label: "마이", path: "/profile", icon: (a) => <UserIcon active={a} /> },
];

export default function BottomTabBar() {
  const pathname = usePathname();
  const shouldReduceMotion = useReducedMotion();

  return (
    <nav
      className="fixed bottom-0 left-0 right-0 z-50 bg-white border-t"
      style={{
        height: "calc(60px + env(safe-area-inset-bottom, 0px))",
        paddingBottom: "env(safe-area-inset-bottom, 0px)",
        borderColor: "var(--color-border)",
      }}
    >
      <div className="flex items-center justify-around h-[60px] max-w-[430px] mx-auto">
        {tabs.map((tab) => {
          const isActive = pathname === tab.path || pathname.startsWith(tab.path + "/");

          return (
            <Link
              key={tab.path}
              href={tab.path}
              className="flex flex-col items-center justify-center gap-[2px] flex-1 h-full"
            >
              <motion.div
                key={`icon-${tab.path}-${isActive}`}
                initial={shouldReduceMotion ? false : { scale: 0.9 }}
                animate={{ scale: 1 }}
                transition={
                  shouldReduceMotion
                    ? { duration: 0 }
                    : {
                        type: "spring",
                        stiffness: 500,
                        damping: 15,
                        mass: 0.8,
                      }
                }
              >
                {tab.icon(isActive)}
              </motion.div>
              <span
                className="text-[11px] leading-[1.4]"
                style={{
                  color: isActive ? "var(--color-accent)" : "var(--color-text-tertiary)",
                  fontWeight: isActive ? 700 : 400,
                  fontFamily: "var(--font-body)",
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
