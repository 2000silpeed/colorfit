import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import AnalyzePage from "../page";

/* ── Mocks ── */

function pickHtmlProps(props: Record<string, unknown>) {
  const skip = new Set([
    "initial", "animate", "transition", "whileDrag", "drag",
    "dragConstraints", "dragElastic", "onDragEnd", "fill", "exit",
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
    section: ({ children, ...rest }: Record<string, unknown>) => (
      <section {...pickHtmlProps(rest)}>{children as React.ReactNode}</section>
    ),
  },
  useReducedMotion: () => false,
}));

vi.mock("next/image", () => ({
  default: ({ src, alt, ...rest }: Record<string, unknown>) => (
    // eslint-disable-next-line @next/next/no-img-element
    <img src={src as string} alt={alt as string} data-testid="mock-image" />
  ),
}));

const mockPush = vi.fn();
const mockBack = vi.fn();
const mockSearchParams = new URLSearchParams();

vi.mock("next/navigation", () => ({
  useSearchParams: () => mockSearchParams,
  useRouter: () => ({
    push: mockPush,
    back: mockBack,
  }),
}));

const mockAnalyze = vi.fn();
const mockRecommend = vi.fn();

vi.mock("@/lib/api", () => ({
  analyzeClosetItem: (...args: unknown[]) => mockAnalyze(...args),
  fetchClosetRecommendations: (...args: unknown[]) => mockRecommend(...args),
}));

const MOCK_ANALYSIS = {
  dominant_colors: [{ hex: "#C4726F", ratio: 0.6 }],
  matched_tone_id: "autumn_warm_deep",
  matched_tone_name: "가을 웜 딥",
  pcf_score: 88,
  saturation_score: 72,
  lightness_score: 65,
  overall_score: 82,
  reasons: [
    "가을 웜 딥 톤의 핵심 컬러에 가까워요",
    "채도가 적절하게 높아 풍부한 인상을 줘요",
  ],
};

const MOCK_RECOMMENDATIONS = {
  source_color_hex: "#C4726F",
  source_category: "top",
  user_tone_id: "autumn_warm_deep",
  recommendations: [
    {
      tpo: "commute",
      tpo_label: "출근",
      items: [
        {
          id: "p1",
          name: "울 슬랙스",
          brand: "COS",
          category: "bottom",
          price: 89000,
          image_url: "/img/p1.jpg",
          mall_url: "https://example.com/p1",
          color_hex: "#3A3530",
          similarity: 0.85,
          match_reason: "톤 호환",
        },
        {
          id: "p2",
          name: "가죽 로퍼",
          brand: "ZARA",
          category: "shoes",
          price: 69000,
          image_url: "/img/p2.jpg",
          mall_url: "https://example.com/p2",
          color_hex: "#5C3A2E",
          similarity: 0.78,
          match_reason: "색상 조화",
        },
      ],
    },
    {
      tpo: "date",
      tpo_label: "데이트",
      items: [
        {
          id: "p3",
          name: "플리츠 스커트",
          brand: "MANGO",
          category: "bottom",
          price: 59000,
          image_url: "/img/p3.jpg",
          mall_url: "https://example.com/p3",
          color_hex: "#DDB67D",
          similarity: 0.82,
          match_reason: "보색 조합",
        },
      ],
    },
  ],
  total_count: 3,
};

beforeEach(() => {
  vi.clearAllMocks();
  mockSearchParams.delete("image_url");
  mockSearchParams.delete("user_tone_id");
  mockSearchParams.delete("category");
});

function setParams(imageUrl: string, toneId: string, category = "top") {
  mockSearchParams.set("image_url", imageUrl);
  mockSearchParams.set("user_tone_id", toneId);
  mockSearchParams.set("category", category);
}

describe("ClosetAnalyzeResultPage", () => {
  it("shows error when required params are missing", () => {
    render(<AnalyzePage />);
    expect(screen.getByText("분석에 실패했어요")).toBeInTheDocument();
    expect(screen.getByText("분석에 필요한 정보가 없습니다.")).toBeInTheDocument();
  });

  it("shows loading skeleton while fetching", () => {
    setParams("https://img.example.com/my-top.jpg", "autumn_warm_deep");
    mockAnalyze.mockReturnValue(new Promise(() => {}));
    render(<AnalyzePage />);
    expect(screen.getByText("옷을 분석하고 있어요...")).toBeInTheDocument();
    const skeletons = document.querySelectorAll(".animate-pulse");
    expect(skeletons.length).toBeGreaterThanOrEqual(3);
  });

  it("renders score and reasons after successful analysis", async () => {
    setParams("https://img.example.com/my-top.jpg", "autumn_warm_deep");
    mockAnalyze.mockResolvedValue(MOCK_ANALYSIS);
    mockRecommend.mockResolvedValue(MOCK_RECOMMENDATIONS);

    render(<AnalyzePage />);

    await waitFor(() => {
      expect(screen.getByText("82")).toBeInTheDocument();
    });
    expect(screen.getByText("/ 100")).toBeInTheDocument();
    expect(screen.getByText("가을 웜 딥 기준 분석 결과")).toBeInTheDocument();
    expect(screen.getByText("가을 웜 딥 톤의 핵심 컬러에 가까워요")).toBeInTheDocument();
    expect(screen.getByText("채도가 적절하게 높아 풍부한 인상을 줘요")).toBeInTheDocument();
  });

  it("renders score bars for 3 axes (색상/채도/명도)", async () => {
    setParams("https://img.example.com/my-top.jpg", "autumn_warm_deep");
    mockAnalyze.mockResolvedValue(MOCK_ANALYSIS);
    mockRecommend.mockResolvedValue(MOCK_RECOMMENDATIONS);

    render(<AnalyzePage />);

    await waitFor(() => {
      expect(screen.getByText("색상")).toBeInTheDocument();
    });
    expect(screen.getByText("채도")).toBeInTheDocument();
    expect(screen.getByText("명도")).toBeInTheDocument();
    expect(screen.getByText("88")).toBeInTheDocument();
    expect(screen.getByText("72")).toBeInTheDocument();
    expect(screen.getByText("65")).toBeInTheDocument();
  });

  it("renders TPO recommendation cards with source image badge", async () => {
    setParams("https://img.example.com/my-top.jpg", "autumn_warm_deep");
    mockAnalyze.mockResolvedValue(MOCK_ANALYSIS);
    mockRecommend.mockResolvedValue(MOCK_RECOMMENDATIONS);

    render(<AnalyzePage />);

    await waitFor(() => {
      expect(screen.getByText("이 옷으로 완성하는 코디")).toBeInTheDocument();
    });
    expect(screen.getByText(/출근/)).toBeInTheDocument();
    expect(screen.getByText(/데이트/)).toBeInTheDocument();
    const badges = screen.getAllByText("내 옷");
    expect(badges.length).toBe(2); // 2 TPO cards
    expect(screen.getByText("울 슬랙스")).toBeInTheDocument();
    expect(screen.getByText("플리츠 스커트")).toBeInTheDocument();
  });

  it("shows CTA buttons (옷장에 추가, 다른 옷도 분석하기)", async () => {
    setParams("https://img.example.com/my-top.jpg", "autumn_warm_deep");
    mockAnalyze.mockResolvedValue(MOCK_ANALYSIS);
    mockRecommend.mockResolvedValue(MOCK_RECOMMENDATIONS);

    render(<AnalyzePage />);

    await waitFor(() => {
      expect(screen.getByText("옷장에 추가")).toBeInTheDocument();
    });
    expect(screen.getByText("다른 옷도 분석하기")).toBeInTheDocument();
  });

  it("navigates to closet on '옷장에 추가' click", async () => {
    setParams("https://img.example.com/my-top.jpg", "autumn_warm_deep");
    mockAnalyze.mockResolvedValue(MOCK_ANALYSIS);
    mockRecommend.mockResolvedValue(MOCK_RECOMMENDATIONS);

    render(<AnalyzePage />);

    await waitFor(() => {
      expect(screen.getByText("옷장에 추가")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByText("옷장에 추가"));
    expect(mockPush).toHaveBeenCalledWith("/closet");
  });

  it("navigates to upload on '다른 옷도 분석하기' click", async () => {
    setParams("https://img.example.com/my-top.jpg", "autumn_warm_deep");
    mockAnalyze.mockResolvedValue(MOCK_ANALYSIS);
    mockRecommend.mockResolvedValue(MOCK_RECOMMENDATIONS);

    render(<AnalyzePage />);

    await waitFor(() => {
      expect(screen.getByText("다른 옷도 분석하기")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByText("다른 옷도 분석하기"));
    expect(mockPush).toHaveBeenCalledWith("/closet/upload");
  });

  it("shows error state on API failure with retry button", async () => {
    setParams("https://img.example.com/my-top.jpg", "autumn_warm_deep");
    mockAnalyze.mockRejectedValue(new Error("서버 에러"));

    render(<AnalyzePage />);

    await waitFor(() => {
      expect(screen.getByText("분석에 실패했어요")).toBeInTheDocument();
    });
    expect(screen.getByText("서버 에러")).toBeInTheDocument();
    expect(screen.getByText("다시 시도하기")).toBeInTheDocument();
  });

  it("displays correct score label for high score (>= 85)", async () => {
    setParams("https://img.example.com/my-top.jpg", "autumn_warm_deep");
    mockAnalyze.mockResolvedValue({ ...MOCK_ANALYSIS, overall_score: 92 });
    mockRecommend.mockResolvedValue(MOCK_RECOMMENDATIONS);

    render(<AnalyzePage />);

    await waitFor(() => {
      expect(screen.getByText("92")).toBeInTheDocument();
    });
    expect(screen.getByText(/훌륭해요/)).toBeInTheDocument();
  });

  it("displays correct score label for low score (< 50)", async () => {
    setParams("https://img.example.com/my-top.jpg", "autumn_warm_deep");
    mockAnalyze.mockResolvedValue({ ...MOCK_ANALYSIS, overall_score: 35 });
    mockRecommend.mockResolvedValue(MOCK_RECOMMENDATIONS);

    render(<AnalyzePage />);

    await waitFor(() => {
      expect(screen.getByText("35")).toBeInTheDocument();
    });
    expect(screen.getByText(/아쉬워요/)).toBeInTheDocument();
  });

  it("displays correct score label for medium score (50-69)", async () => {
    setParams("https://img.example.com/my-top.jpg", "autumn_warm_deep");
    mockAnalyze.mockResolvedValue({ ...MOCK_ANALYSIS, overall_score: 55 });
    mockRecommend.mockResolvedValue(MOCK_RECOMMENDATIONS);

    render(<AnalyzePage />);

    await waitFor(() => {
      expect(screen.getByText("55")).toBeInTheDocument();
    });
    expect(screen.getByText(/보통이에요/)).toBeInTheDocument();
  });

  it("shows recommendation loading skeleton while analysis succeeds but recs pending", async () => {
    setParams("https://img.example.com/my-top.jpg", "autumn_warm_deep");
    mockAnalyze.mockResolvedValue(MOCK_ANALYSIS);
    mockRecommend.mockReturnValue(new Promise(() => {}));

    render(<AnalyzePage />);

    await waitFor(() => {
      expect(screen.getByText("82")).toBeInTheDocument();
    });
    expect(screen.getByText("이 옷으로 완성하는 코디")).toBeInTheDocument();
    const skeletons = document.querySelectorAll(".animate-pulse");
    expect(skeletons.length).toBeGreaterThanOrEqual(1);
  });

  it("calls analyzeClosetItem with correct params", async () => {
    setParams("https://img.example.com/my-top.jpg", "autumn_warm_deep");
    mockAnalyze.mockResolvedValue(MOCK_ANALYSIS);
    mockRecommend.mockResolvedValue(MOCK_RECOMMENDATIONS);

    render(<AnalyzePage />);

    await waitFor(() => {
      expect(mockAnalyze).toHaveBeenCalledWith(
        "https://img.example.com/my-top.jpg",
        "autumn_warm_deep",
      );
    });
  });

  it("calls fetchClosetRecommendations with dominant color from analysis", async () => {
    setParams("https://img.example.com/my-top.jpg", "autumn_warm_deep");
    mockAnalyze.mockResolvedValue(MOCK_ANALYSIS);
    mockRecommend.mockResolvedValue(MOCK_RECOMMENDATIONS);

    render(<AnalyzePage />);

    await waitFor(() => {
      expect(mockRecommend).toHaveBeenCalledWith(
        "#C4726F",
        "top",
        "autumn_warm_deep",
        undefined,
        3,
      );
    });
  });

  it("shows empty recommendation message when no recommendations", async () => {
    setParams("https://img.example.com/my-top.jpg", "autumn_warm_deep");
    mockAnalyze.mockResolvedValue(MOCK_ANALYSIS);
    mockRecommend.mockResolvedValue({
      ...MOCK_RECOMMENDATIONS,
      recommendations: [],
      total_count: 0,
    });

    render(<AnalyzePage />);

    await waitFor(() => {
      expect(screen.getByText("아직 이 옷에 어울리는 코디를 준비 중이에요")).toBeInTheDocument();
    });
  });
});
