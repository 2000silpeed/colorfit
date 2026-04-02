import { render, screen, fireEvent, waitFor, act } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import PremiumPage from "../page";

/* ── Mocks ── */

function pickHtmlProps(props: Record<string, unknown>) {
  const skip = new Set([
    "initial", "animate", "transition", "whileDrag", "drag",
    "dragConstraints", "dragElastic", "onDragEnd", "exit",
  ]);
  const out: Record<string, unknown> = {};
  for (const [k, v] of Object.entries(props)) {
    if (!skip.has(k)) out[k] = v;
  }
  return out;
}

vi.mock("framer-motion", () => ({
  motion: {
    div: ({ children, ...rest }: Record<string, unknown>) => (
      <div {...pickHtmlProps(rest)}>{children as React.ReactNode}</div>
    ),
  },
  useReducedMotion: () => false,
}));

const mockBack = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: vi.fn(),
    back: mockBack,
  }),
}));

beforeEach(() => {
  vi.clearAllMocks();
});

describe("PremiumPage", () => {
  it("renders hero title and description", () => {
    render(<PremiumPage />);
    expect(screen.getByText("Premium")).toBeInTheDocument();
    expect(screen.getByText("내 옷장의 가능성을 무제한으로 탐색하세요.")).toBeInTheDocument();
  });

  it("renders all 4 benefit items", () => {
    render(<PremiumPage />);
    expect(screen.getByText("AI 착장 샘플 무제한")).toBeInTheDocument();
    expect(screen.getByText("제휴 할인 쿠폰")).toBeInTheDocument();
    // "가격 하락 알림" appears in benefits and comparison table
    expect(screen.getAllByText("가격 하락 알림")).toHaveLength(2);
    expect(screen.getAllByText("시즌 신상 알림")).toHaveLength(2);
  });

  it("renders comparison table with free vs premium columns", () => {
    render(<PremiumPage />);
    expect(screen.getByText("기능")).toBeInTheDocument();
    expect(screen.getByText("무료")).toBeInTheDocument();
    // AI 착장 샘플 row: free=3회, premium=무제한
    expect(screen.getByText("AI 착장 샘플")).toBeInTheDocument();
    expect(screen.getByText("3회")).toBeInTheDocument();
  });

  it("defaults to yearly plan selection", () => {
    render(<PremiumPage />);
    const yearlyButton = screen.getByRole("button", { pressed: true });
    expect(yearlyButton).toHaveTextContent("연간");
    expect(yearlyButton).toHaveTextContent("39,000");
    expect(yearlyButton).toHaveTextContent("33% 할인");
  });

  it("switches plan when monthly is clicked", () => {
    render(<PremiumPage />);
    const monthlyText = screen.getByText("월간");
    const monthlyButton = monthlyText.closest("button")!;
    fireEvent.click(monthlyButton);
    expect(monthlyButton).toHaveAttribute("aria-pressed", "true");
  });

  it("shows both plan prices", () => {
    render(<PremiumPage />);
    expect(screen.getByText("4,900")).toBeInTheDocument();
    expect(screen.getByText("39,000")).toBeInTheDocument();
    expect(screen.getByText("월 3,250원꼴")).toBeInTheDocument();
  });

  it("shows CTA button for interest registration", () => {
    render(<PremiumPage />);
    expect(screen.getByRole("button", { name: "관심 등록하기" })).toBeInTheDocument();
    expect(screen.getByText(/MVP 기간 중 결제는 발생하지 않습니다/)).toBeInTheDocument();
  });

  it("completes interest registration flow", async () => {
    vi.useFakeTimers();
    render(<PremiumPage />);
    const ctaButton = screen.getByRole("button", { name: "관심 등록하기" });
    fireEvent.click(ctaButton);

    expect(screen.getByText("등록 중...")).toBeInTheDocument();

    await act(async () => {
      vi.advanceTimersByTime(1100);
    });

    expect(screen.getByText("관심 등록 완료")).toBeInTheDocument();
    expect(screen.getByText("정식 출시 시 가장 먼저 알려드릴게요.")).toBeInTheDocument();
    vi.useRealTimers();
  });

  it("back button navigates back", () => {
    render(<PremiumPage />);
    const backButton = screen.getByLabelText("뒤로 가기");
    fireEvent.click(backButton);
    expect(mockBack).toHaveBeenCalledTimes(1);
  });

  it("shows return button after registration and navigates back", async () => {
    vi.useFakeTimers();
    render(<PremiumPage />);
    fireEvent.click(screen.getByRole("button", { name: "관심 등록하기" }));

    await act(async () => {
      vi.advanceTimersByTime(1100);
    });

    expect(screen.getByText("관심 등록 완료")).toBeInTheDocument();
    const returnButton = screen.getByRole("button", { name: "돌아가기" });
    fireEvent.click(returnButton);
    expect(mockBack).toHaveBeenCalledTimes(1);
    vi.useRealTimers();
  });
});
