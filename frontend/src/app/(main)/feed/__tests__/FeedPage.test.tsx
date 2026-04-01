import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import FeedPage from "../page";

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
    article: ({ children, onClick, onKeyDown, ...rest }: Record<string, unknown>) => (
      <article
        onClick={onClick as React.MouseEventHandler}
        onKeyDown={onKeyDown as React.KeyboardEventHandler}
        {...pickHtmlProps(rest)}
      >
        {children as React.ReactNode}
      </article>
    ),
    div: ({ children, ...rest }: Record<string, unknown>) => (
      <div {...pickHtmlProps(rest)}>{children as React.ReactNode}</div>
    ),
    svg: ({ children, ...rest }: Record<string, unknown>) => (
      <svg {...pickHtmlProps(rest)}>{children as React.ReactNode}</svg>
    ),
  },
  AnimatePresence: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  useReducedMotion: () => false,
}));

vi.mock("next/image", () => ({
  default: ({ src, alt, fill, sizes, loading, priority, ...rest }: Record<string, unknown>) => (
    // eslint-disable-next-line @next/next/no-img-element
    <img src={src as string} alt={alt as string} {...rest} />
  ),
}));

const mockFetchFeed = vi.fn();
vi.mock("@/lib/api", () => ({
  fetchFeed: (...args: unknown[]) => mockFetchFeed(...args),
}));

const makeFeedItem = (id: string, overrides?: Record<string, unknown>) => ({
  id,
  gender: "female",
  designed_tpo: "commute",
  total_price: 89000,
  tags: ["니트", "슬랙스", "로퍼"],
  scores: { pcf: 92, of: 85, ch: 70, pe: 60, sf: 78 },
  soft_score: 80,
  final_score: 82,
  reasons: [`코디 ${id} 추천`, "봄웜 톤에 잘 어울려요"],
  image_url: `/img/${id}.jpg`,
  ...overrides,
});

/* IntersectionObserver mock */
class MockIntersectionObserver {
  callback: IntersectionObserverCallback;
  constructor(callback: IntersectionObserverCallback) {
    this.callback = callback;
  }
  observe() {}
  unobserve() {}
  disconnect() {}
}
Object.defineProperty(globalThis, "IntersectionObserver", {
  value: MockIntersectionObserver,
  writable: true,
});

const localStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: (key: string) => store[key] ?? null,
    setItem: (key: string, value: string) => { store[key] = value; },
    removeItem: (key: string) => { delete store[key]; },
    clear: () => { store = {}; },
    get length() { return Object.keys(store).length; },
    key: (i: number) => Object.keys(store)[i] ?? null,
  };
})();

beforeEach(() => {
  vi.clearAllMocks();
  Object.defineProperty(globalThis, "localStorage", { value: localStorageMock, writable: true });
  localStorageMock.clear();
  localStorageMock.setItem("colorfit_tone", "spring_warm_light");
  localStorageMock.setItem("colorfit_gender", "female");
});

describe("FeedPage", () => {
  it("renders header with logo and profile icon", async () => {
    mockFetchFeed.mockResolvedValue({
      outfits: [makeFeedItem("o1"), makeFeedItem("o2")],
      page: 1, page_size: 20, total: 2, has_next: false,
    });
    render(<FeedPage />);
    expect(screen.getByText("ColorFit")).toBeInTheDocument();
    expect(screen.getByLabelText("프로필")).toBeInTheDocument();
  });

  it("renders TPO filter tabs", async () => {
    mockFetchFeed.mockResolvedValue({
      outfits: [makeFeedItem("o1")],
      page: 1, page_size: 20, total: 1, has_next: false,
    });
    render(<FeedPage />);
    expect(screen.getByText("전체")).toBeInTheDocument();
    expect(screen.getByText("출근")).toBeInTheDocument();
    expect(screen.getByText("데이트")).toBeInTheDocument();
  });

  it("shows skeleton cards while loading", () => {
    mockFetchFeed.mockReturnValue(new Promise(() => {})); // never resolves
    render(<FeedPage />);
    const skeletons = document.querySelectorAll(".animate-pulse");
    expect(skeletons.length).toBeGreaterThanOrEqual(3);
  });

  it("shows outfits after successful load", async () => {
    mockFetchFeed.mockResolvedValue({
      outfits: [makeFeedItem("o1"), makeFeedItem("o2"), makeFeedItem("o3")],
      page: 1, page_size: 20, total: 3, has_next: false,
    });
    render(<FeedPage />);
    await waitFor(() => {
      expect(screen.getByText("오늘의 컬러핏")).toBeInTheDocument();
    });
    // 첫 번째는 오늘의 컬러핏, 나머지는 일반 카드
    expect(screen.getByText("코디 o2 추천")).toBeInTheDocument();
    expect(screen.getByText("코디 o3 추천")).toBeInTheDocument();
  });

  it("shows empty state when no outfits", async () => {
    mockFetchFeed.mockResolvedValue({
      outfits: [],
      page: 1, page_size: 20, total: 0, has_next: false,
    });
    render(<FeedPage />);
    await waitFor(() => {
      expect(screen.getByText("조건에 맞는 코디가 없어요")).toBeInTheDocument();
    });
    expect(screen.getByText("필터를 변경해보세요")).toBeInTheDocument();
  });

  it("shows error state on API failure", async () => {
    mockFetchFeed.mockRejectedValue(new Error("API error"));
    render(<FeedPage />);
    await waitFor(() => {
      expect(screen.getByText("불러오지 못했어요")).toBeInTheDocument();
    });
    expect(screen.getByText("다시 시도")).toBeInTheDocument();
  });

  it("retries on error button click", async () => {
    mockFetchFeed.mockRejectedValueOnce(new Error("fail"));
    render(<FeedPage />);
    await waitFor(() => {
      expect(screen.getByText("다시 시도")).toBeInTheDocument();
    });

    mockFetchFeed.mockResolvedValue({
      outfits: [makeFeedItem("o1")],
      page: 1, page_size: 20, total: 1, has_next: false,
    });
    fireEvent.click(screen.getByText("다시 시도"));

    await waitFor(() => {
      expect(screen.getByText("오늘의 컬러핏")).toBeInTheDocument();
    });
  });

  it("switches TPO filter and reloads", async () => {
    mockFetchFeed.mockResolvedValue({
      outfits: [makeFeedItem("o1")],
      page: 1, page_size: 20, total: 1, has_next: false,
    });
    render(<FeedPage />);
    await waitFor(() => {
      expect(screen.getByText("오늘의 컬러핏")).toBeInTheDocument();
    });

    mockFetchFeed.mockClear();
    mockFetchFeed.mockResolvedValue({
      outfits: [makeFeedItem("o2", { designed_tpo: "date" })],
      page: 1, page_size: 20, total: 1, has_next: false,
    });
    fireEvent.click(screen.getByText("데이트"));

    await waitFor(() => {
      expect(mockFetchFeed).toHaveBeenCalledWith(
        expect.objectContaining({ tpo: "date" }),
      );
    });
  });

  it("toggles budget slider open/closed", async () => {
    mockFetchFeed.mockResolvedValue({
      outfits: [makeFeedItem("o1")],
      page: 1, page_size: 20, total: 1, has_next: false,
    });
    render(<FeedPage />);
    await waitFor(() => {
      expect(screen.getByText("오늘의 컬러핏")).toBeInTheDocument();
    });

    const budgetButton = screen.getByText("₩3만~₩10만");
    fireEvent.click(budgetButton);
    expect(screen.getByText("최소")).toBeInTheDocument();
    expect(screen.getByText("최대")).toBeInTheDocument();
  });

  it("calls fetchFeed with correct params including budget", async () => {
    mockFetchFeed.mockResolvedValue({
      outfits: [makeFeedItem("o1")],
      page: 1, page_size: 20, total: 1, has_next: false,
    });
    render(<FeedPage />);

    await waitFor(() => {
      expect(mockFetchFeed).toHaveBeenCalledWith(
        expect.objectContaining({
          toneId: "spring_warm_light",
          gender: "female",
          budgetMin: 30000,
          budgetMax: 100000,
        }),
      );
    });
  });

  it("passes tpo=undefined when '전체' is selected", async () => {
    mockFetchFeed.mockResolvedValue({
      outfits: [makeFeedItem("o1")],
      page: 1, page_size: 20, total: 1, has_next: false,
    });
    render(<FeedPage />);

    await waitFor(() => {
      expect(mockFetchFeed).toHaveBeenCalledWith(
        expect.objectContaining({ tpo: undefined }),
      );
    });
  });
});
