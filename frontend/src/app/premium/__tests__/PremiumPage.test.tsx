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
const mockPush = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: mockPush,
    back: mockBack,
  }),
}));

const mockSubscribe = vi.fn();
const mockFetchSubscriptionStatus = vi.fn();
const mockFetchTryonUsage = vi.fn();

vi.mock("@/lib/api", () => ({
  subscribe: (...args: unknown[]) => mockSubscribe(...args),
  fetchSubscriptionStatus: (...args: unknown[]) => mockFetchSubscriptionStatus(...args),
  fetchTryonUsage: (...args: unknown[]) => mockFetchTryonUsage(...args),
}));

vi.mock("@/lib/auth", () => ({
  isLoggedIn: () => true,
}));

beforeEach(() => {
  vi.clearAllMocks();
  localStorage.setItem("colorfit_user_id", "test-user");
  mockFetchSubscriptionStatus.mockResolvedValue({ is_premium: false });
  mockFetchTryonUsage.mockResolvedValue({ remaining: 3 });
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

  it("shows CTA button for premium subscription", () => {
    render(<PremiumPage />);
    expect(screen.getByRole("button", { name: "프리미엄 시작하기" })).toBeInTheDocument();
    expect(screen.getByText(/MVP 기간 중 결제는 발생하지 않습니다/)).toBeInTheDocument();
  });

  it("completes subscription flow with coupon code", async () => {
    mockSubscribe.mockResolvedValue({ ok: true });
    render(<PremiumPage />);
    const input = screen.getByPlaceholderText("COLORFIT-BETA") as HTMLInputElement;
    fireEvent.change(input, { target: { value: "COLORFIT-BETA" } });

    const ctaButton = screen.getByRole("button", { name: "프리미엄 시작하기" });
    fireEvent.click(ctaButton);

    await waitFor(() => {
      expect(mockSubscribe).toHaveBeenCalledWith("test-user", "yearly", "COLORFIT-BETA");
    });
    await waitFor(() => {
      expect(screen.getByText("프리미엄 활성화됨")).toBeInTheDocument();
    });
  });

  it("back button navigates back", () => {
    Object.defineProperty(window.history, "length", { value: 2, configurable: true });
    render(<PremiumPage />);
    const backButton = screen.getByLabelText("뒤로 가기");
    fireEvent.click(backButton);
    expect(mockBack).toHaveBeenCalledTimes(1);
  });

  it("shows return button after subscription and navigates back", async () => {
    Object.defineProperty(window.history, "length", { value: 2, configurable: true });
    mockSubscribe.mockResolvedValue({ ok: true });
    render(<PremiumPage />);
    const input = screen.getByPlaceholderText("COLORFIT-BETA") as HTMLInputElement;
    fireEvent.change(input, { target: { value: "COLORFIT-BETA" } });
    fireEvent.click(screen.getByRole("button", { name: "프리미엄 시작하기" }));

    await waitFor(() => {
      expect(screen.getByText("프리미엄 활성화됨")).toBeInTheDocument();
    });
    const returnButton = screen.getByRole("button", { name: "돌아가기" });
    fireEvent.click(returnButton);
    expect(mockBack).toHaveBeenCalledTimes(1);
  });
});
