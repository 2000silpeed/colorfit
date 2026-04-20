import Link from "next/link";

export default function NotFound() {
  return (
    <div className="flex min-h-[80vh] flex-col items-center justify-center px-6 text-center">
      <h1 className="mb-2 font-display text-[22px] font-bold text-[var(--color-text-primary)]">
        페이지를 찾을 수 없어요
      </h1>
      <p className="mb-6 text-sm text-[var(--color-text-secondary)]">
        주소가 변경되었거나 존재하지 않는 페이지입니다.
      </p>
      <Link
        href="/"
        className="inline-flex min-h-[44px] min-w-[112px] items-center justify-center rounded-lg bg-[#964F4C] px-5 text-sm font-semibold text-white"
      >
        홈으로
      </Link>
    </div>
  );
}
