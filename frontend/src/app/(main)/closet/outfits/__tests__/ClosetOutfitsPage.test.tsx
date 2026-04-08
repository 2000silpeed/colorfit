import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import ClosetOutfitsPage from "../page";
import type { ClosetOutfit } from "@/lib/api";

/* ── framer-motion mock ── */

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
    article: ({ children, ...rest }: Record<string, unknown>) => (
      <article {...pickHtmlProps(rest)}>{children as React.ReactNode}</article>
    ),
    div: ({ children, ...rest }: Record<string, unknown>) => (
      <div {...pickHtmlProps(rest)}>{children as React.ReactNode}</div>
    ),
    button: ({ children, ...rest }: Record<string, unknown>) => (
      <button {...pickHtmlProps(rest)}>{children as React.ReactNode}</button>
    ),
    svg: (props: Record<string, unknown>) => (
      <svg {...pickHtmlProps(props)} />
    ),
  },
  AnimatePresence: ({ children }: Record<string, unknown>) => (
    <>{children}</>
  ),
  useReducedMotion: () => false,
}));

vi.mock("next/image", () => ({
  default: ({ src, alt }: Record<string, unknown>) => (
    <img src={src as string} alt={alt as string} data-testid="mock-image" />
  ),
}));

const mockPush = vi.fn();
const mockBack = vi.fn();
const mockReplace = vi.fn();
let mockSearchParams = new URLSearchParams("item_id=item-abc");

vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: mockPush,
    back: mockBack,
    replace: mockReplace,
  }),
  useSearchParams: () => mockSearchParams,
}));

const mockFetchClosetOutfits = vi.fn();
const mockPostReaction = vi.fn();

vi.mock("@/lib/api", () => ({
  fetchClosetOutfits: (...args: unknown[]) => mockFetchClosetOutfits(...args),
  postReaction: (...args: unknown[]) => mockPostReaction(...args),
}));

vi.mock("@/lib/auth", () => ({
  isLoggedIn: () => true,
}));

/* ── 테스트 데이터 ── */

const MOCK_OUTFIT: ClosetOutfit = {
  id: "outfit-1",
  source: "db_match",
  db_outfit_id: "db-outfit-1",
  total_score: 82.5,
  scores: { pcf: 90, of: 78, ch: 85, pe: 70, sf: 80 },
  reasons: ["가을 웜 톤에 잘 어울리는 조합이에요"],
  items: [
    {
      id: "closet-item-1",
      source: "closet",
      category: "top",
      image_url: "/img/my-top.jpg",
      label: "내 옷",
      name: "니트",
      brand: "ZARA",
      price: 39000,
      mall_url: null,
    },
    {
      id: "catalog-item-1",
      source: "catalog",
      category: "bottom",
      image_url: "/img/pants.jpg",
      label: null,
      name: "슬랙스",
      brand: "COS",
      price: 89000,
      mall_url: "https://shop.example.com/pants",
    },
    {
      id: "catalog-item-2",
      source: "catalog",
      category: "shoes",
      image_url: "/img/shoes.jpg",
      label: null,
      name: "로퍼",
      brand: "ALDO",
      price: 120000,
      mall_url: "https://shop.example.com/shoes",
    },
  ],
  purchase_summary: {
    my_items_count: 1,
    purchase_items_count: 2,
    purchase_total: 209000,
  },
};

const MOCK_OUTFIT_FREE: ClosetOutfit = {
  ...MOCK_OUTFIT,
  id: "outfit-2",
  db_outfit_id: "db-outfit-2",
  total_score: 75,
  scores: { pcf: 80, of: 70, ch: 75, pe: 90, sf: 60 },
  reasons: ["이미 가지고 있는 아이템만으로 코디 가능해요"],
  items: [
    { ...MOCK_OUTFIT.items[0], id: "closet-1", source: "closet" },
    { ...MOCK_OUTFIT.items[1], id: "closet-2", source: "closet", price: 0, mall_url: null },
  ],
  purchase_summary: {
    my_items_count: 2,
    purchase_items_count: 0,
    purchase_total: 0,
  },
};

const MOCK_RESPONSE = {
  outfits: [MOCK_OUTFIT, MOCK_OUTFIT_FREE],
  total_count: 2,
  strategy_used: "db_match",
};

beforeEach(() => {
  vi.clearAllMocks();
  mockSearchParams = new URLSearchParams("item_id=item-abc");
  localStorage.setItem("colorfit_user_id", "test-user-id");
  localStorage.setItem("colorfit_saved_ids", "[]");
});

describe("ClosetOutfitsPage", () => {
  /* ── 로딩 상태 ── */
  it("shows skeleton cards while loading", () => {
    mockFetchClosetOutfits.mockReturnValue(new Promise(() => {}));
    render(<ClosetOutfitsPage />);
    const skeletons = document.querySelectorAll(".animate-pulse");
    expect(skeletons.length).toBeGreaterThanOrEqual(3);
  });

  /* ── item_id 없으면 리다이렉트 ── */
  it("redirects to /closet when item_id is missing", () => {
    mockSearchParams = new URLSearchParams("");
    mockFetchClosetOutfits.mockResolvedValue({ outfits: [], total_count: 0 });
    render(<ClosetOutfitsPage />);
    expect(mockReplace).toHaveBeenCalledWith("/closet");
  });

  /* ── 에러 상태 ── */
  it("shows error state with retry button on API failure", async () => {
    mockFetchClosetOutfits.mockRejectedValue(new Error("서버 에러"));
    render(<ClosetOutfitsPage />);

    await waitFor(() => {
      expect(screen.getByText("코디를 불러오지 못했어요")).toBeInTheDocument();
    });
    expect(screen.getByText("다시 시도")).toBeInTheDocument();
  });

  it("retries on '다시 시도' click", async () => {
    mockFetchClosetOutfits
      .mockRejectedValueOnce(new Error("fail"))
      .mockResolvedValueOnce(MOCK_RESPONSE);
    render(<ClosetOutfitsPage />);

    await waitFor(() => {
      expect(screen.getByText("다시 시도")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByText("다시 시도"));

    await waitFor(() => {
      expect(screen.getByText(/코디를 찾았어요/)).toBeInTheDocument();
    });
    expect(mockFetchClosetOutfits).toHaveBeenCalledTimes(2);
  });

  /* ── 빈 상태 ── */
  it("shows empty state when no outfits match", async () => {
    mockFetchClosetOutfits.mockResolvedValue({ outfits: [], total_count: 0 });
    render(<ClosetOutfitsPage />);

    await waitFor(() => {
      expect(screen.getByText("매칭되는 코디가 없어요")).toBeInTheDocument();
    });
    expect(screen.getByText("다른 TPO를 선택해보세요")).toBeInTheDocument();
  });

  it("shows '전체 보기' button in empty state when TPO filter active", async () => {
    mockFetchClosetOutfits
      .mockResolvedValueOnce(MOCK_RESPONSE) // initial load (all)
      .mockResolvedValueOnce({ outfits: [], total_count: 0 }); // commute → empty
    render(<ClosetOutfitsPage />);

    await waitFor(() => {
      expect(screen.getByText(/코디를 찾았어요/)).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("출근"));

    await waitFor(() => {
      expect(screen.getByText("전체 보기")).toBeInTheDocument();
    });
  });

  /* ── 카드 렌더링 ── */
  it("renders outfit cards with count message", async () => {
    mockFetchClosetOutfits.mockResolvedValue(MOCK_RESPONSE);
    render(<ClosetOutfitsPage />);

    await waitFor(() => {
      expect(screen.getByText("2개의 코디를 찾았어요")).toBeInTheDocument();
    });
  });

  it("renders total score on each card", async () => {
    mockFetchClosetOutfits.mockResolvedValue(MOCK_RESPONSE);
    render(<ClosetOutfitsPage />);

    await waitFor(() => {
      expect(screen.getByText("83점")).toBeInTheDocument(); // Math.round(82.5)
    });
    expect(screen.getByText("75점")).toBeInTheDocument();
  });

  it("renders score axis badges (컬러, TPO, 조화, 가성비, 스타일)", async () => {
    mockFetchClosetOutfits.mockResolvedValue({
      outfits: [MOCK_OUTFIT],
      total_count: 1,
    });
    render(<ClosetOutfitsPage />);

    await waitFor(() => {
      expect(screen.getByText("컬러 90")).toBeInTheDocument();
    });
    expect(screen.getByText("TPO 78")).toBeInTheDocument();
    expect(screen.getByText("조화 85")).toBeInTheDocument();
    expect(screen.getByText("가성비 70")).toBeInTheDocument();
    expect(screen.getByText("스타일 80")).toBeInTheDocument();
  });

  it("renders recommendation reason text", async () => {
    mockFetchClosetOutfits.mockResolvedValue({
      outfits: [MOCK_OUTFIT],
      total_count: 1,
    });
    render(<ClosetOutfitsPage />);

    await waitFor(() => {
      expect(screen.getByText("가을 웜 톤에 잘 어울리는 조합이에요")).toBeInTheDocument();
    });
  });

  it("renders item thumbnails for each outfit card", async () => {
    mockFetchClosetOutfits.mockResolvedValue({
      outfits: [MOCK_OUTFIT],
      total_count: 1,
    });
    render(<ClosetOutfitsPage />);

    await waitFor(() => {
      const images = screen.getAllByTestId("mock-image");
      expect(images.length).toBe(3);
    });
  });

  /* ── 내 옷 뱃지 ── */
  it("shows '내 옷' badge on closet-sourced items", async () => {
    mockFetchClosetOutfits.mockResolvedValue({
      outfits: [MOCK_OUTFIT],
      total_count: 1,
    });
    render(<ClosetOutfitsPage />);

    await waitFor(() => {
      const badges = screen.getAllByText("내 옷");
      expect(badges.length).toBe(1); // only the closet-source item
    });
  });

  it("does not show '내 옷' badge on catalog items", async () => {
    const catalogOnly: ClosetOutfit = {
      ...MOCK_OUTFIT,
      items: MOCK_OUTFIT.items.filter((i) => i.source === "catalog"),
    };
    mockFetchClosetOutfits.mockResolvedValue({
      outfits: [catalogOnly],
      total_count: 1,
    });
    render(<ClosetOutfitsPage />);

    await waitFor(() => {
      expect(screen.getByText(/코디를 찾았어요/)).toBeInTheDocument();
    });
    expect(screen.queryByText("내 옷")).not.toBeInTheDocument();
  });

  /* ── 추가 구매 비용 ── */
  it("displays purchase summary (내 옷 count, 추가 구매 count, total)", async () => {
    mockFetchClosetOutfits.mockResolvedValue({
      outfits: [MOCK_OUTFIT],
      total_count: 1,
    });
    render(<ClosetOutfitsPage />);

    await waitFor(() => {
      expect(screen.getByText("내 옷 1벌")).toBeInTheDocument();
    });
    expect(screen.getByText("추가 구매 2벌")).toBeInTheDocument();
    expect(screen.getByText("+₩20만9,000")).toBeInTheDocument();
  });

  it("shows '추가 비용 없음' when purchase_total is 0", async () => {
    mockFetchClosetOutfits.mockResolvedValue({
      outfits: [MOCK_OUTFIT_FREE],
      total_count: 1,
    });
    render(<ClosetOutfitsPage />);

    await waitFor(() => {
      expect(screen.getByText("추가 비용 없음")).toBeInTheDocument();
    });
  });

  /* ── TPO 필터 ── */
  it("renders all 9 TPO filter tabs", async () => {
    mockFetchClosetOutfits.mockResolvedValue(MOCK_RESPONSE);
    render(<ClosetOutfitsPage />);

    const tpoLabels = ["전체", "출근", "데이트", "면접", "주말", "캠퍼스", "여행", "행사", "운동"];
    for (const label of tpoLabels) {
      expect(screen.getByText(label)).toBeInTheDocument();
    }
  });

  it("calls API with tpo parameter when non-all tab clicked", async () => {
    mockFetchClosetOutfits.mockResolvedValue(MOCK_RESPONSE);
    render(<ClosetOutfitsPage />);

    await waitFor(() => {
      expect(screen.getByText(/코디를 찾았어요/)).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("데이트"));

    await waitFor(() => {
      expect(mockFetchClosetOutfits).toHaveBeenCalledWith(
        "test-user-id",
        "item-abc",
        "date",
      );
    });
  });

  it("calls API without tpo when '전체' tab clicked after other filter", async () => {
    mockFetchClosetOutfits.mockResolvedValue(MOCK_RESPONSE);
    render(<ClosetOutfitsPage />);

    await waitFor(() => {
      expect(screen.getByText(/코디를 찾았어요/)).toBeInTheDocument();
    });

    // 다른 TPO 선택 후 전체로 복귀
    fireEvent.click(screen.getByText("데이트"));
    await waitFor(() => {
      expect(mockFetchClosetOutfits).toHaveBeenCalledWith(
        "test-user-id",
        "item-abc",
        "date",
      );
    });

    mockFetchClosetOutfits.mockClear();
    fireEvent.click(screen.getByText("전체"));

    await waitFor(() => {
      expect(mockFetchClosetOutfits).toHaveBeenCalledWith(
        "test-user-id",
        "item-abc",
        undefined,
      );
    });
  });

  /* ── 카드 탭 → 상세 네비게이션 ── */
  it("navigates to outfit detail with closet_item_id on card tap", async () => {
    mockFetchClosetOutfits.mockResolvedValue({
      outfits: [MOCK_OUTFIT],
      total_count: 1,
    });
    render(<ClosetOutfitsPage />);

    await waitFor(() => {
      expect(screen.getByText("83점")).toBeInTheDocument();
    });

    // article 클릭 (카드 전체)
    const card = screen.getByText("83점").closest("article")!;
    fireEvent.click(card);

    expect(mockPush).toHaveBeenCalledWith(
      "/outfit/db-outfit-1?closet_item_id=item-abc",
    );
  });

  /* ── 저장 토글 ── */
  it("toggles save and shows toast", async () => {
    mockPostReaction.mockResolvedValue({});
    mockFetchClosetOutfits.mockResolvedValue({
      outfits: [MOCK_OUTFIT],
      total_count: 1,
    });
    render(<ClosetOutfitsPage />);

    await waitFor(() => {
      expect(screen.getByLabelText("저장")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByLabelText("저장"));

    await waitFor(() => {
      expect(screen.getByText("저장했어요")).toBeInTheDocument();
    });
  });

  /* ── 뒤로 가기 ── */
  it("navigates back on back button click", async () => {
    mockFetchClosetOutfits.mockResolvedValue(MOCK_RESPONSE);
    render(<ClosetOutfitsPage />);

    fireEvent.click(screen.getByLabelText("뒤로 가기"));
    expect(mockBack).toHaveBeenCalled();
  });

  /* ── 헤더 ── */
  it("shows '코디 완성' header title", async () => {
    mockFetchClosetOutfits.mockResolvedValue(MOCK_RESPONSE);
    render(<ClosetOutfitsPage />);

    expect(screen.getByText("코디 완성")).toBeInTheDocument();
  });

  /* ── 카테고리 라벨 ── */
  it("shows category labels under item thumbnails", async () => {
    mockFetchClosetOutfits.mockResolvedValue({
      outfits: [MOCK_OUTFIT],
      total_count: 1,
    });
    render(<ClosetOutfitsPage />);

    await waitFor(() => {
      expect(screen.getByText("상의")).toBeInTheDocument();
    });
    expect(screen.getByText("하의")).toBeInTheDocument();
    expect(screen.getByText("신발")).toBeInTheDocument();
  });
});
