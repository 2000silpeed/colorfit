import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import PhotoUploader from "../PhotoUploader";

/* ── Mocks ── */

vi.mock("framer-motion", () => ({
  motion: {
    div: ({ children, ...rest }: Record<string, unknown>) => {
      const skip = new Set(["initial", "animate", "transition", "whileDrag", "exit"]);
      const out: Record<string, unknown> = {};
      for (const [k, v] of Object.entries(rest)) {
        if (!skip.has(k)) out[k] = v;
      }
      return <div {...out}>{children as React.ReactNode}</div>;
    },
  },
  useReducedMotion: () => false,
}));

vi.mock("next/image", () => ({
  default: ({ src, alt }: Record<string, unknown>) => (
    // eslint-disable-next-line @next/next/no-img-element
    <img src={src as string} alt={alt as string} data-testid="preview-image" />
  ),
}));

function createMockFile(name = "test.jpg", size = 1024, type = "image/jpeg"): File {
  const buffer = new ArrayBuffer(size);
  return new File([buffer], name, { type });
}

beforeEach(() => {
  vi.clearAllMocks();
  vi.spyOn(URL, "createObjectURL").mockReturnValue("blob:mock-preview-url");
  vi.spyOn(URL, "revokeObjectURL").mockImplementation(() => {});
});

describe("PhotoUploader", () => {
  it("renders upload area with camera and gallery buttons", () => {
    const onFileReady = vi.fn();
    render(<PhotoUploader onFileReady={onFileReady} />);

    expect(screen.getByText("옷 사진을 올려주세요")).toBeInTheDocument();
    expect(screen.getByText("촬영")).toBeInTheDocument();
    expect(screen.getByText("갤러리")).toBeInTheDocument();
  });

  it("has camera input with capture attribute", () => {
    const onFileReady = vi.fn();
    render(<PhotoUploader onFileReady={onFileReady} />);

    const cameraInput = screen.getByTestId("camera-input");
    expect(cameraInput).toHaveAttribute("capture", "environment");
    expect(cameraInput).toHaveAttribute("accept", "image/*");
  });

  it("has gallery input without capture attribute", () => {
    const onFileReady = vi.fn();
    render(<PhotoUploader onFileReady={onFileReady} />);

    const galleryInput = screen.getByTestId("gallery-input");
    expect(galleryInput).not.toHaveAttribute("capture");
    expect(galleryInput).toHaveAttribute("accept", "image/*");
  });

  it("shows error for files exceeding 20MB", async () => {
    const onFileReady = vi.fn();
    render(<PhotoUploader onFileReady={onFileReady} />);

    const bigFile = createMockFile("big.jpg", 25 * 1024 * 1024);
    const galleryInput = screen.getByTestId("gallery-input");

    fireEvent.change(galleryInput, { target: { files: [bigFile] } });

    await waitFor(() => {
      expect(screen.getByText("20MB 이하 파일만 업로드할 수 있어요.")).toBeInTheDocument();
    });
    expect(onFileReady).not.toHaveBeenCalled();
  });

  it("clicking camera button triggers camera input", () => {
    const onFileReady = vi.fn();
    render(<PhotoUploader onFileReady={onFileReady} />);

    const cameraInput = screen.getByTestId("camera-input");
    const clickSpy = vi.spyOn(cameraInput, "click");

    fireEvent.click(screen.getByText("촬영"));
    expect(clickSpy).toHaveBeenCalled();
  });

  it("clicking gallery button triggers gallery input", () => {
    const onFileReady = vi.fn();
    render(<PhotoUploader onFileReady={onFileReady} />);

    const galleryInput = screen.getByTestId("gallery-input");
    const clickSpy = vi.spyOn(galleryInput, "click");

    fireEvent.click(screen.getByText("갤러리"));
    expect(clickSpy).toHaveBeenCalled();
  });
});
