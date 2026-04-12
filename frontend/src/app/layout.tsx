import type { Metadata } from "next";
import { Lora, Noto_Serif_KR, Geist } from "next/font/google";
import localFont from "next/font/local";
import "./globals.css";
import { cn } from "@/lib/utils";

const geist = Geist({subsets:['latin'],variable:'--font-sans'});

const lora = Lora({
  weight: ["400", "500", "600", "700"],
  subsets: ["latin"],
  variable: "--font-lora",
  display: "swap",
});

const notoSerifKr = Noto_Serif_KR({
  weight: ["400", "500", "600", "700"],
  subsets: ["latin"],
  variable: "--font-noto-serif-kr",
  display: "swap",
});

const pretendard = localFont({
  src: "../../public/fonts/PretendardVariable.woff2",
  weight: "100 900",
  variable: "--font-pretendard",
  display: "swap",
});

export const metadata: Metadata = {
  title: "ColorFit",
  description: "AI 퍼스널컬러 기반 패션 의사결정 엔진",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="ko"
      className={cn("h-full", "antialiased", lora.variable, notoSerifKr.variable, pretendard.variable, "font-sans", geist.variable)}
      suppressHydrationWarning
    >
      <body className="min-h-full flex flex-col items-center bg-[#E8E4DF]">
        <div className="w-full max-w-[430px] min-h-full bg-[var(--color-bg)] shadow-[0_0_40px_rgba(0,0,0,0.08)]">
          {children}
        </div>
      </body>
    </html>
  );
}
