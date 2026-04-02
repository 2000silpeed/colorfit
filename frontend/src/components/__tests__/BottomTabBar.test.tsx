import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import BottomTabBar from "../BottomTabBar";

let mockPathname = "/feed";

vi.mock("next/navigation", () => ({
  usePathname: () => mockPathname,
}));

vi.mock("framer-motion", () => ({
  motion: {
    div: ({ children, ...rest }: Record<string, unknown>) => {
      const { initial, animate, transition, ...htmlProps } = rest as Record<string, unknown>;
      void initial; void animate; void transition;
      return <div {...(htmlProps as React.HTMLAttributes<HTMLDivElement>)}>{children as React.ReactNode}</div>;
    },
  },
  useReducedMotion: () => false,
}));

describe("BottomTabBar", () => {
  it("4개 탭(홈, 옷장, 저장, 마이)이 모두 렌더링된다", () => {
    render(<BottomTabBar />);
    expect(screen.getByText("홈")).toBeInTheDocument();
    expect(screen.getByText("옷장")).toBeInTheDocument();
    expect(screen.getByText("저장")).toBeInTheDocument();
    expect(screen.getByText("마이")).toBeInTheDocument();
  });

  it("활성 탭은 Marsala 컬러와 bold 스타일을 가진다", () => {
    mockPathname = "/feed";
    render(<BottomTabBar />);
    const homeLabel = screen.getByText("홈");
    expect(homeLabel).toHaveStyle({ color: "var(--color-accent)", fontWeight: 700 });
  });

  it("비활성 탭은 tertiary 컬러와 normal weight를 가진다", () => {
    mockPathname = "/feed";
    render(<BottomTabBar />);
    const savedLabel = screen.getByText("저장");
    expect(savedLabel).toHaveStyle({ color: "var(--color-text-tertiary)", fontWeight: 400 });
  });

  it("각 탭이 올바른 경로의 링크를 가진다", () => {
    render(<BottomTabBar />);
    const links = screen.getAllByRole("link");
    const hrefs = links.map((link) => link.getAttribute("href"));
    expect(hrefs).toEqual(["/feed", "/closet", "/saved", "/profile"]);
  });

  it("하위 경로에서도 해당 탭이 활성화된다", () => {
    mockPathname = "/saved/123";
    render(<BottomTabBar />);
    const savedLabel = screen.getByText("저장");
    expect(savedLabel).toHaveStyle({ color: "var(--color-accent)", fontWeight: 700 });
  });

  it("nav 역할의 요소가 렌더링된다", () => {
    render(<BottomTabBar />);
    expect(screen.getByRole("navigation")).toBeInTheDocument();
  });
});
