import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import OutfitCard from "../OutfitCard";

function pickHtmlProps(props: Record<string, unknown>) {
  const skip = new Set([
    "initial", "animate", "transition", "whileDrag", "drag",
    "dragConstraints", "dragElastic", "onDragEnd", "fill",
  ]);
  const out: Record<string, unknown> = {};
  for (const [k, v] of Object.entries(props)) {
    if (!skip.has(k)) out[k] = v;
  }
  return out;
}

vi.mock("framer-motion", () => ({
  motion: {
    article: ({ children, onClick, onDoubleClick, onKeyDown, ...rest }: Record<string, unknown>) => (
      <article
        onClick={onClick as React.MouseEventHandler}
        onDoubleClick={onDoubleClick as React.MouseEventHandler}
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
  useReducedMotion: () => false,
}));

vi.mock("next/image", () => ({
  default: ({ src, alt, ...rest }: { src: string; alt: string }) => (
    // eslint-disable-next-line @next/next/no-img-element
    <img src={src} alt={alt} {...rest} />
  ),
}));

const defaultProps = {
  id: "outfit-1",
  imageUrl: "/test-image.jpg",
  title: "봄웜라이트 데이트룩 코디",
  totalPrice: 89000,
  reason: "여름쿨소프트 핵심 컬러 라벤더 블루 계열",
  scores: { pcf: 94.5, of: 87.8 },
  itemCount: 3,
  items: [
    { image_url: "/item1.jpg", category: "top", group: "상의", brand: "COS", style_tag: "minimal", is_verified_brand: true },
    { image_url: "/item2.jpg", category: "bottom", group: "하의", brand: null, style_tag: null, is_verified_brand: false },
    { image_url: "/item3.jpg", category: "shoes", group: "신발", brand: null, style_tag: null, is_verified_brand: false },
  ],
};

describe("OutfitCard", () => {
  it("renders title, price, reason", () => {
    render(<OutfitCard {...defaultProps} />);
    expect(screen.getByText("봄웜라이트 데이트룩 코디")).toBeInTheDocument();
    expect(screen.getByText(/8만9,000/)).toBeInTheDocument();
    expect(
      screen.getByText("여름쿨소프트 핵심 컬러 라벤더 블루 계열"),
    ).toBeInTheDocument();
  });

  it("renders item images from items prop", () => {
    render(<OutfitCard {...defaultProps} />);
    const images = screen.getAllByRole("img");
    expect(images.length).toBeGreaterThanOrEqual(1);
  });

  it("renders score badges with rounded values", () => {
    render(<OutfitCard {...defaultProps} />);
    expect(screen.getByText("PCF 95")).toBeInTheDocument();
    expect(screen.getByText("OF 88")).toBeInTheDocument();
  });

  it("renders main image from first item", () => {
    render(<OutfitCard {...defaultProps} />);
    const img = screen.getByAltText("top");
    expect(img).toHaveAttribute("src", "/item1.jpg");
  });

  it("toggles save on heart button click", () => {
    const onSaveToggle = vi.fn();
    render(<OutfitCard {...defaultProps} onSaveToggle={onSaveToggle} />);
    const heartBtn = screen.getByRole("button", { name: "저장" });
    fireEvent.click(heartBtn);
    expect(onSaveToggle).toHaveBeenCalledWith("outfit-1");
    expect(heartBtn).toHaveAttribute("aria-pressed", "true");
  });

  it("toggles save off when already saved", () => {
    const onSaveToggle = vi.fn();
    render(<OutfitCard {...defaultProps} isSaved={true} onSaveToggle={onSaveToggle} />);
    const heartBtn = screen.getByRole("button", { name: "저장 취소" });
    fireEvent.click(heartBtn);
    expect(onSaveToggle).toHaveBeenCalledWith("outfit-1");
    expect(heartBtn).toHaveAttribute("aria-pressed", "false");
  });

  it("calls onTap on single click after delay", () => {
    vi.useFakeTimers();
    const onTap = vi.fn();
    render(<OutfitCard {...defaultProps} onTap={onTap} />);
    fireEvent.click(screen.getByRole("link"));
    expect(onTap).not.toHaveBeenCalled();
    vi.advanceTimersByTime(300);
    expect(onTap).toHaveBeenCalledWith("outfit-1");
    vi.useRealTimers();
  });

  it("calls onSaveToggle on double click without triggering onTap", () => {
    vi.useFakeTimers();
    const onTap = vi.fn();
    const onSaveToggle = vi.fn();
    render(<OutfitCard {...defaultProps} onTap={onTap} onSaveToggle={onSaveToggle} />);
    const card = screen.getByRole("link");
    fireEvent.click(card);
    fireEvent.click(card);
    vi.advanceTimersByTime(700);
    expect(onSaveToggle).toHaveBeenCalledWith("outfit-1");
    expect(onTap).not.toHaveBeenCalled();
    vi.useRealTimers();
  });

  it("shows discount when originalPrice is provided", () => {
    render(<OutfitCard {...defaultProps} originalPrice={120000} />);
    expect(screen.getByText("12만")).toBeInTheDocument();
    expect(screen.getByText("26%")).toBeInTheDocument();
  });

  it("does not show discount when no originalPrice", () => {
    render(<OutfitCard {...defaultProps} />);
    expect(screen.queryByText("%")).not.toBeInTheDocument();
  });

  it("renders with isSaved=true", () => {
    render(<OutfitCard {...defaultProps} isSaved={true} />);
    const heartBtn = screen.getByRole("button", { name: "저장 취소" });
    expect(heartBtn).toHaveAttribute("aria-pressed", "true");
  });

  it("has tabIndex and role for keyboard access", () => {
    render(<OutfitCard {...defaultProps} />);
    const article = screen.getByRole("link");
    expect(article).toHaveAttribute("tabindex", "0");
  });

  it("triggers onTap on Enter key", () => {
    const onTap = vi.fn();
    render(<OutfitCard {...defaultProps} onTap={onTap} />);
    fireEvent.keyDown(screen.getByRole("link"), { key: "Enter" });
    expect(onTap).toHaveBeenCalledWith("outfit-1");
  });

  it("applies discount price color as accent when discounted", () => {
    render(<OutfitCard {...defaultProps} originalPrice={120000} />);
    const priceEl = screen.getByText(/₩8만9,000/);
    expect(priceEl.className).toContain("text-accent");
  });

  it("applies normal price color when not discounted", () => {
    render(<OutfitCard {...defaultProps} />);
    const priceEl = screen.getByText(/₩8만9,000/);
    expect(priceEl.className).toContain("text-text-primary");
  });
});
