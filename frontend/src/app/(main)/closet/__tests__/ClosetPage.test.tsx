import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import ClosetPage from "../page";

/* ── Mocks ── */

function pickHtmlProps(props: Record<string, unknown>) {
  const skip = new Set([
    "initial", "animate", "transition", "whileDrag", "drag",
    "dragConstraints", "dragElastic", "onDragEnd", "exit",
    "strokeDasharray", "strokeDashoffset",
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
    button: ({ children, ...rest }: Record<string, unknown>) => (
      <button {...pickHtmlProps(rest)}>{children as React.ReactNode}</button>
    ),
    circle: (props: Record<string, unknown>) => (
      <circle {...pickHtmlProps(props)} />
    ),
  },
  useReducedMotion: () => false,
}));

vi.mock("next/image", () => ({
  default: ({ src, alt }: Record<string, unknown>) => (
    // eslint-disable-next-line @next/next/no-img-element
    <img src={src as string} alt={alt as string} data-testid="mock-image" />
  ),
}));

const mockPush = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: mockPush,
    back: vi.fn(),
  }),
}));

const mockFetchCloset = vi.fn();

vi.mock("@/lib/api", () => ({
  fetchCloset: (...args: unknown[]) => mockFetchCloset(...args),
}));

const MOCK_ITEMS = [
  {
    id: "item-1",
    image_url: "/img/top1.jpg",
    category: "top",
    dominant_color_hex: "#C4726F",
    matched_tone_id: "autumn_warm_deep",
    pcf_score: 88,
    overall_score: 82,
    reasons: ["가을 웜 딥 톤에 잘 어울려요"],
    created_at: "2026-03-28T10:00:00",
  },
  {
    id: "item-2",
    image_url: "/img/bottom1.jpg",
    category: "bottom",
    dominant_color_hex: "#3A3530",
    matched_tone_id: "autumn_warm_deep",
    pcf_score: 45,
    overall_score: 40,
    reasons: ["채도가 다소 낮아요"],
    created_at: "2026-03-27T10:00:00",
  },
  {
    id: "item-3",
    image_url: "/img/outer1.jpg",
    category: "outer",
    dominant_color_hex: "#5C3A2E",
    matched_tone_id: "autumn_warm_deep",
    pcf_score: 72,
    overall_score: 75,
    reasons: ["어울리는 톤이에요"],
    created_at: "2026-03-26T10:00:00",
  },
];

const MOCK_STATS = {
  total_count: 3,
  average_pcf: 68.3,
  good_count: 2,
  good_ratio: 66.7,
};

const MOCK_RESPONSE = { items: MOCK_ITEMS, stats: MOCK_STATS };

beforeEach(() => {
  vi.clearAllMocks();
});

describe("ClosetPage", () => {
  it("shows loading skeleton while fetching", () => {
    mockFetchCloset.mockReturnValue(new Promise(() => {}));
    render(<ClosetPage />);
    const skeletons = document.querySelectorAll(".animate-pulse");
    expect(skeletons.length).toBeGreaterThanOrEqual(6);
  });

  it("shows empty state when closet has no items", async () => {
    mockFetchCloset.mockResolvedValue({ items: [], stats: { total_count: 0, average_pcf: 0, good_count: 0, good_ratio: 0 } });
    render(<ClosetPage />);

    await waitFor(() => {
      expect(screen.getByText("아직 분석한 옷이 없어요")).toBeInTheDocument();
    });
    expect(screen.getByText("첫 번째 옷 분석하기")).toBeInTheDocument();
  });

  it("navigates to upload on empty state CTA click", async () => {
    mockFetchCloset.mockResolvedValue({ items: [], stats: { total_count: 0, average_pcf: 0, good_count: 0, good_ratio: 0 } });
    render(<ClosetPage />);

    await waitFor(() => {
      expect(screen.getByText("첫 번째 옷 분석하기")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByText("첫 번째 옷 분석하기"));
    expect(mockPush).toHaveBeenCalledWith("/closet/upload");
  });

  it("shows error state with retry button on API failure", async () => {
    mockFetchCloset.mockRejectedValue(new Error("서버 에러"));
    render(<ClosetPage />);

    await waitFor(() => {
      expect(screen.getByText("옷장을 불러올 수 없어요")).toBeInTheDocument();
    });
    expect(screen.getByText("서버 에러")).toBeInTheDocument();
    expect(screen.getByText("다시 시도하기")).toBeInTheDocument();
  });

  it("renders circular gauge with average PCF score", async () => {
    mockFetchCloset.mockResolvedValue(MOCK_RESPONSE);
    render(<ClosetPage />);

    await waitFor(() => {
      expect(screen.getByText("68")).toBeInTheDocument();
    });
    expect(screen.getByText("/ 100")).toBeInTheDocument();
  });

  it("shows stats summary text", async () => {
    mockFetchCloset.mockResolvedValue(MOCK_RESPONSE);
    render(<ClosetPage />);

    await waitFor(() => {
      expect(screen.getByText("3벌 중 2벌이 잘 어울려요")).toBeInTheDocument();
    });
  });

  it("renders category diagnosis text", async () => {
    mockFetchCloset.mockResolvedValue(MOCK_RESPONSE);
    render(<ClosetPage />);

    await waitFor(() => {
      expect(screen.getByText(/상의.*훌륭/)).toBeInTheDocument();
    });
  });

  it("renders 3-column grid with items", async () => {
    mockFetchCloset.mockResolvedValue(MOCK_RESPONSE);
    render(<ClosetPage />);

    await waitFor(() => {
      expect(screen.getByText("내 옷장")).toBeInTheDocument();
    });
    const images = screen.getAllByTestId("mock-image");
    expect(images.length).toBe(3);
  });

  it("shows score badges on item cards", async () => {
    mockFetchCloset.mockResolvedValue(MOCK_RESPONSE);
    render(<ClosetPage />);

    await waitFor(() => {
      expect(screen.getByText("82")).toBeInTheDocument();
    });
    expect(screen.getByText("40")).toBeInTheDocument();
    expect(screen.getByText("75")).toBeInTheDocument();
  });

  it("shows category labels under items", async () => {
    mockFetchCloset.mockResolvedValue(MOCK_RESPONSE);
    render(<ClosetPage />);

    await waitFor(() => {
      expect(screen.getByText("상의")).toBeInTheDocument();
    });
    expect(screen.getByText("하의")).toBeInTheDocument();
    expect(screen.getByText("아우터")).toBeInTheDocument();
  });

  it("shows free analysis remaining count", async () => {
    mockFetchCloset.mockResolvedValue(MOCK_RESPONSE);
    render(<ClosetPage />);

    await waitFor(() => {
      expect(screen.getByText("무료 분석 2회 남음")).toBeInTheDocument();
    });
  });

  it("shows premium button", async () => {
    mockFetchCloset.mockResolvedValue(MOCK_RESPONSE);
    render(<ClosetPage />);

    await waitFor(() => {
      expect(screen.getByText("프리미엄")).toBeInTheDocument();
    });
  });

  it("navigates to analyze page on item click", async () => {
    mockFetchCloset.mockResolvedValue(MOCK_RESPONSE);
    render(<ClosetPage />);

    await waitFor(() => {
      expect(screen.getByText("상의")).toBeInTheDocument();
    });

    const topButton = screen.getByText("상의").closest("button")!;
    fireEvent.click(topButton);

    expect(mockPush).toHaveBeenCalledWith(
      expect.stringContaining("/closet/analyze"),
    );
  });

  it("has add button (FAB) with correct aria-label", async () => {
    mockFetchCloset.mockResolvedValue(MOCK_RESPONSE);
    render(<ClosetPage />);

    await waitFor(() => {
      expect(screen.getByLabelText("옷 추가")).toBeInTheDocument();
    });
  });

  it("navigates to upload on FAB click", async () => {
    mockFetchCloset.mockResolvedValue(MOCK_RESPONSE);
    render(<ClosetPage />);

    await waitFor(() => {
      expect(screen.getByLabelText("옷 추가")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByLabelText("옷 추가"));
    expect(mockPush).toHaveBeenCalledWith("/closet/upload");
  });

  it("shows high score badge in Marsala color (>= 70)", async () => {
    mockFetchCloset.mockResolvedValue(MOCK_RESPONSE);
    render(<ClosetPage />);

    await waitFor(() => {
      const badge82 = screen.getByText("82");
      expect(badge82).toBeInTheDocument();
      expect(badge82.style.backgroundColor).toBe("var(--color-accent)");
    });
  });

  it("shows mid score badge in Ocean Blue color (50-69)", async () => {
    const midItem = { ...MOCK_ITEMS[1], id: "item-mid", overall_score: 60, pcf_score: 60 };
    const midResponse = {
      items: [midItem],
      stats: { total_count: 1, average_pcf: 60, good_count: 0, good_ratio: 0 },
    };
    mockFetchCloset.mockResolvedValue(midResponse);
    render(<ClosetPage />);

    await waitFor(() => {
      const allSixty = screen.getAllByText("60");
      const badge60 = allSixty.find(
        (el) => el.classList.contains("font-body"),
      )!;
      expect(badge60).toBeInTheDocument();
      expect(badge60.style.backgroundColor).toBe("var(--color-score-of)");
      expect(badge60.style.color).toBe("rgb(26, 23, 20)");
    });
  });

  it("has aria-labels on item cards with category and score", async () => {
    mockFetchCloset.mockResolvedValue(MOCK_RESPONSE);
    render(<ClosetPage />);

    await waitFor(() => {
      expect(screen.getByLabelText("상의 82점")).toBeInTheDocument();
    });
    expect(screen.getByLabelText("하의 40점")).toBeInTheDocument();
    expect(screen.getByLabelText("아우터 75점")).toBeInTheDocument();
  });

  it("shows low score badge in neutral color (< 50)", async () => {
    mockFetchCloset.mockResolvedValue(MOCK_RESPONSE);
    render(<ClosetPage />);

    await waitFor(() => {
      const badge40 = screen.getByText("40");
      expect(badge40).toBeInTheDocument();
      expect(badge40.style.backgroundColor).toBe("var(--color-bg-secondary)");
    });
  });

  it("renders '코디 완성하기' button for each item", async () => {
    mockFetchCloset.mockResolvedValue(MOCK_RESPONSE);
    render(<ClosetPage />);

    await waitFor(() => {
      const outfitButtons = screen.getAllByText("코디 완성하기");
      expect(outfitButtons.length).toBe(3);
    });
  });

  it("navigates to outfits page on '코디 완성하기' click", async () => {
    mockFetchCloset.mockResolvedValue(MOCK_RESPONSE);
    render(<ClosetPage />);

    await waitFor(() => {
      expect(screen.getAllByText("코디 완성하기").length).toBe(3);
    });

    fireEvent.click(screen.getAllByText("코디 완성하기")[0]);
    expect(mockPush).toHaveBeenCalledWith("/closet/outfits?item_id=item-1");
  });
});
