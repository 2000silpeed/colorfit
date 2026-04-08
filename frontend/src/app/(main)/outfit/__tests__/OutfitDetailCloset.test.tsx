import { render, screen, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import OutfitDetailPage from "../[id]/page";

/* ── framer-motion mock ── */

function pickHtmlProps(props: Record<string, unknown>) {
  const skip = new Set([
    "initial", "animate", "transition", "whileDrag", "drag",
    "dragConstraints", "dragElastic", "onDragEnd", "exit",
    "strokeDasharray", "strokeDashoffset", "whileHover", "whileTap",
    "variants", "layout", "layoutId",
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
    header: ({ children, ...rest }: Record<string, unknown>) => (
      <header {...pickHtmlProps(rest)}>{children as React.ReactNode}</header>
    ),
    button: ({ children, ...rest }: Record<string, unknown>) => (
      <button {...pickHtmlProps(rest)}>{children as React.ReactNode}</button>
    ),
    img: (props: Record<string, unknown>) => <img {...pickHtmlProps(props)} />,
    svg: (props: Record<string, unknown>) => <svg {...pickHtmlProps(props)} />,
    section: ({ children, ...rest }: Record<string, unknown>) => (
      <section {...pickHtmlProps(rest)}>{children as React.ReactNode}</section>
    ),
  },
  AnimatePresence: ({ children }: Record<string, unknown>) => <>{children}</>,
  useScroll: () => ({ scrollY: { get: () => 0 } }),
  useTransform: () => ({ get: () => 0 }),
  useMotionValueEvent: () => {},
  useReducedMotion: () => true,
}));

vi.mock("next/image", () => ({
  default: ({ src, alt, className }: Record<string, unknown>) => (
    <img
      src={src as string}
      alt={alt as string}
      className={className as string}
      data-testid="mock-image"
    />
  ),
}));

const mockPush = vi.fn();
const mockBack = vi.fn();
let mockParamsId = "outfit-100";
let mockSearchParams = new URLSearchParams("closet_item_id=item-abc");

vi.mock("next/navigation", () => ({
  useParams: () => ({ id: mockParamsId }),
  useRouter: () => ({
    push: mockPush,
    back: mockBack,
  }),
  useSearchParams: () => mockSearchParams,
}));

const mockFetchOutfitDetail = vi.fn();
const mockFetchSaved = vi.fn();
const mockFetchClosetOutfits = vi.fn();
const mockPostReaction = vi.fn();
const mockGenerateTryon = vi.fn();
const mockFetchTryonUsage = vi.fn();

vi.mock("@/lib/api", () => ({
  fetchOutfitDetail: (...args: unknown[]) => mockFetchOutfitDetail(...args),
  fetchSaved: (...args: unknown[]) => mockFetchSaved(...args),
  fetchClosetOutfits: (...args: unknown[]) => mockFetchClosetOutfits(...args),
  postReaction: (...args: unknown[]) => mockPostReaction(...args),
  generateTryon: (...args: unknown[]) => mockGenerateTryon(...args),
  fetchTryonUsage: (...args: unknown[]) => mockFetchTryonUsage(...args),
  TryonLimitError: class TryonLimitError extends Error {},
}));

vi.mock("@/lib/auth", () => ({
  isLoggedIn: () => true,
}));

vi.mock("@/components/PurchaseFeedbackSheet", () => ({
  default: () => null,
}));

/* ── 테스트 데이터 ── */

const MOCK_OUTFIT_DETAIL = {
  id: "outfit-100",
  image_url: "/img/outfit-hero.jpg",
  tpo: "commute",
  season: "autumn",
  total_score: 85,
  scores: { pcf: 92, of: 80, ch: 88, pe: 75, sf: 82 },
  reasons: ["가을 출근룩에 잘 어울리는 조합"],
  items: [
    {
      id: "item-owned-1",
      category: "니트",
      name: "캐시미어 니트",
      brand: "ZARA",
      image_url: "/img/knit.jpg",
      price: 59000,
      mall_url: "https://shop.example.com/knit",
    },
    {
      id: "item-owned-2",
      category: "슬랙스",
      name: "와이드 슬랙스",
      brand: "COS",
      image_url: "/img/slacks.jpg",
      price: 89000,
      mall_url: "https://shop.example.com/slacks",
    },
    {
      id: "item-catalog-1",
      category: "로퍼",
      name: "클래식 로퍼",
      brand: "ALDO",
      image_url: "/img/loafer.jpg",
      price: 129000,
      mall_url: "https://shop.example.com/loafer",
    },
  ],
  total_price: 277000,
  lowest_total_price: null,
};

const MOCK_CLOSET_OUTFIT = {
  id: "closet-outfit-1",
  source: "db_match",
  db_outfit_id: "outfit-100",
  total_score: 85,
  scores: { pcf: 92, of: 80, ch: 88, pe: 75, sf: 82 },
  reasons: ["가을 출근룩에 잘 어울리는 조합"],
  items: [
    {
      id: "item-owned-1",
      source: "closet",
      category: "top",
      image_url: "/img/knit.jpg",
      label: "내 옷",
      name: "캐시미어 니트",
      brand: "ZARA",
      price: 59000,
      mall_url: null,
    },
    {
      id: "item-owned-2",
      source: "closet",
      category: "bottom",
      image_url: "/img/slacks.jpg",
      label: "내 옷",
      name: "와이드 슬랙스",
      brand: "COS",
      price: 89000,
      mall_url: null,
    },
    {
      id: "item-catalog-1",
      source: "catalog",
      category: "shoes",
      image_url: "/img/loafer.jpg",
      label: null,
      name: "클래식 로퍼",
      brand: "ALDO",
      price: 129000,
      mall_url: "https://shop.example.com/loafer",
    },
  ],
  purchase_summary: {
    my_items_count: 2,
    purchase_items_count: 1,
    purchase_total: 129000,
  },
};

const MOCK_CLOSET_RESPONSE = {
  outfits: [MOCK_CLOSET_OUTFIT],
  total_count: 1,
  strategy_used: "db_match",
};

beforeEach(() => {
  vi.clearAllMocks();
  mockParamsId = "outfit-100";
  mockSearchParams = new URLSearchParams("closet_item_id=item-abc");
  localStorage.setItem("colorfit_user_id", "test-user-id");
  localStorage.setItem("colorfit_saved_ids", "[]");
  localStorage.removeItem("colorfit_tryon_images");

  mockFetchOutfitDetail.mockResolvedValue(MOCK_OUTFIT_DETAIL);
  mockFetchClosetOutfits.mockResolvedValue(MOCK_CLOSET_RESPONSE);
  mockFetchSaved.mockResolvedValue([]);
  mockFetchTryonUsage.mockResolvedValue({ remaining: 3 });
  mockPostReaction.mockResolvedValue({});
});

describe("OutfitDetailPage — closet mode", () => {
  /* ── 보유 중 뱃지 ── */
  it("shows '보유 중' badge on owned items (source=closet)", async () => {
    render(<OutfitDetailPage />);

    await waitFor(() => {
      const badges = screen.getAllByText("보유 중");
      expect(badges.length).toBe(2); // item-owned-1, item-owned-2
    });
  });

  it("does not show '보유 중' badge on catalog items", async () => {
    render(<OutfitDetailPage />);

    await waitFor(() => {
      expect(screen.getByText("클래식 로퍼")).toBeInTheDocument();
    });

    // catalog 아이템(클래식 로퍼) 링크 스코프 내에 보유 중 뱃지 없음
    const loaferLink = screen.getByText("클래식 로퍼").closest("a")!;
    expect(loaferLink.querySelector(".rounded-full")).toBeFalsy();
    // 전체 보유 중 뱃지 수 = 2 (owned items만)
    const badges = screen.getAllByText("보유 중");
    expect(badges.length).toBe(2);
  });

  /* ── 보유 아이템 가격 표시 ── */
  it("shows '보유' text instead of price for owned items", async () => {
    render(<OutfitDetailPage />);

    await waitFor(() => {
      const ownedLabels = screen.getAllByText("보유");
      expect(ownedLabels.length).toBe(2);
    });
  });

  /* ── 카탈로그 아이템 가격 ── */
  it("shows price in accent color for catalog items in closet mode", async () => {
    render(<OutfitDetailPage />);

    await waitFor(() => {
      const prices = screen.getAllByText("₩12만9,000");
      expect(prices.length).toBeGreaterThanOrEqual(1);
      const itemPrice = prices.find((el) => el.classList.contains("text-accent") && el.classList.contains("text-[11px]"));
      expect(itemPrice).toBeTruthy();
    });
  });

  /* ── 외부 링크 조건부 표시 ── */
  it("catalog item has external link (href set)", async () => {
    render(<OutfitDetailPage />);

    await waitFor(() => {
      expect(screen.getByText("클래식 로퍼")).toBeInTheDocument();
    });

    const loaferLink = screen.getByText("클래식 로퍼").closest("a");
    expect(loaferLink).toHaveAttribute("href", "https://shop.example.com/loafer");
    expect(loaferLink).toHaveAttribute("target", "_blank");
  });

  it("owned items have no external link (href undefined)", async () => {
    render(<OutfitDetailPage />);

    await waitFor(() => {
      expect(screen.getByText("아이템 구성")).toBeInTheDocument();
    });

    const knitLink = screen.getByText("캐시미어 니트").closest("a");
    expect(knitLink).not.toHaveAttribute("href");
    expect(knitLink).not.toHaveAttribute("target");
  });

  it("owned items have cursor-default class", async () => {
    render(<OutfitDetailPage />);

    await waitFor(() => {
      expect(screen.getByText("아이템 구성")).toBeInTheDocument();
    });

    const knitLink = screen.getByText("캐시미어 니트").closest("a");
    expect(knitLink?.className).toContain("cursor-default");
  });

  it("owned items have reduced opacity on image", async () => {
    render(<OutfitDetailPage />);

    await waitFor(() => {
      expect(screen.getByText("아이템 구성")).toBeInTheDocument();
    });

    const images = screen.getAllByTestId("mock-image");
    // 보유 아이템 이미지는 opacity-80 클래스 포함
    const ownedImages = images.filter(
      (img) => img.className.includes("opacity-80"),
    );
    expect(ownedImages.length).toBe(2);
  });

  /* ── 구매 합계 섹션 ── */
  it("shows purchase summary section in closet mode", async () => {
    render(<OutfitDetailPage />);

    await waitFor(() => {
      expect(screen.getByText(/보유 2개 · 구매 필요 1개/)).toBeInTheDocument();
    });
    expect(screen.getByText("이미 가지고 있는 아이템 비용은 제외")).toBeInTheDocument();
    // purchase summary의 합계 금액 (아이템 가격과 동일하므로 2개)
    const prices = screen.getAllByText("₩12만9,000");
    expect(prices.length).toBe(2);
  });

  it("shows '추가 구매 합계' label", async () => {
    render(<OutfitDetailPage />);

    await waitFor(() => {
      expect(screen.getByText("추가 구매 합계")).toBeInTheDocument();
    });
  });

  /* ── closet_item_id 없으면 일반 모드 ── */
  it("does not show purchase summary without closet_item_id", async () => {
    mockSearchParams = new URLSearchParams("");
    render(<OutfitDetailPage />);

    await waitFor(() => {
      expect(screen.getByText("아이템 구성")).toBeInTheDocument();
    });

    expect(screen.queryByText("추가 구매 합계")).not.toBeInTheDocument();
    expect(screen.queryByText("보유 중")).not.toBeInTheDocument();
  });

  it("shows normal price (not strikethrough) for items in non-closet mode", async () => {
    mockSearchParams = new URLSearchParams("");
    render(<OutfitDetailPage />);

    await waitFor(() => {
      expect(screen.getByText("아이템 구성")).toBeInTheDocument();
    });

    expect(screen.queryByText("보유")).not.toBeInTheDocument();
    // 일반 모드에서는 모든 아이템의 가격이 정상 표시
    expect(screen.getByText("₩12만9,000")).toBeInTheDocument();
  });

  /* ── closetOutfit 매칭 실패 시 일반 모드로 폴백 ── */
  it("falls back to normal mode when closet outfit fetch fails", async () => {
    mockFetchClosetOutfits.mockRejectedValue(new Error("fail"));
    render(<OutfitDetailPage />);

    await waitFor(() => {
      expect(screen.getByText("아이템 구성")).toBeInTheDocument();
    });

    expect(screen.queryByText("보유 중")).not.toBeInTheDocument();
    expect(screen.queryByText("추가 구매 합계")).not.toBeInTheDocument();
  });

  it("falls back to normal mode when closet outfits have no matching ID", async () => {
    mockFetchClosetOutfits.mockResolvedValue({
      outfits: [{ ...MOCK_CLOSET_OUTFIT, id: "other-id", db_outfit_id: "other-db-id" }],
      total_count: 1,
      strategy_used: "db_match",
    });
    render(<OutfitDetailPage />);

    await waitFor(() => {
      expect(screen.getByText("아이템 구성")).toBeInTheDocument();
    });

    expect(screen.queryByText("보유 중")).not.toBeInTheDocument();
    expect(screen.queryByText("추가 구매 합계")).not.toBeInTheDocument();
  });
});
