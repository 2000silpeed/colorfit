import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import UploadPage from "../page";

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

const mockPush = vi.fn();
const mockBack = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: mockPush,
    back: mockBack,
  }),
}));

const mockUpload = vi.fn();

vi.mock("@/lib/api", () => ({
  uploadClosetImage: (...args: unknown[]) => mockUpload(...args),
}));

// Mock PhotoUploader to simplify page tests
let capturedOnFileReady: ((file: File, url: string) => void) | null = null;

vi.mock("@/components/PhotoUploader", () => ({
  default: ({ onFileReady, disabled }: { onFileReady: (f: File, u: string) => void; disabled?: boolean }) => {
    capturedOnFileReady = onFileReady;
    return (
      <div data-testid="photo-uploader" data-disabled={disabled}>
        <button
          type="button"
          onClick={() => {
            const mockFile = new File(["test"], "test.jpg", { type: "image/jpeg" });
            onFileReady(mockFile, "blob:preview");
          }}
        >
          Select Photo
        </button>
      </div>
    );
  },
}));

beforeEach(() => {
  vi.clearAllMocks();
  capturedOnFileReady = null;
});

describe("ClosetUploadPage", () => {
  it("renders header and PhotoUploader", () => {
    render(<UploadPage />);
    expect(screen.getByText("옷 분석하기")).toBeInTheDocument();
    expect(screen.getByTestId("photo-uploader")).toBeInTheDocument();
  });

  it("shows category pills after file selection", async () => {
    render(<UploadPage />);

    fireEvent.click(screen.getByText("Select Photo"));

    await waitFor(() => {
      expect(screen.getByText("어떤 종류의 옷인가요?")).toBeInTheDocument();
    });
    expect(screen.getByText("상의")).toBeInTheDocument();
    expect(screen.getByText("하의")).toBeInTheDocument();
    expect(screen.getByText("아우터")).toBeInTheDocument();
    expect(screen.getByText("원피스")).toBeInTheDocument();
    expect(screen.getByText("신발")).toBeInTheDocument();
    expect(screen.getByText("가방")).toBeInTheDocument();
    expect(screen.getByText("액세서리")).toBeInTheDocument();
  });

  it("shows submit button after file selection", async () => {
    render(<UploadPage />);
    fireEvent.click(screen.getByText("Select Photo"));

    await waitFor(() => {
      expect(screen.getByText("분석 시작하기")).toBeInTheDocument();
    });
  });

  it("defaults to 상의 category", async () => {
    render(<UploadPage />);
    fireEvent.click(screen.getByText("Select Photo"));

    await waitFor(() => {
      const topBtn = screen.getByText("상의");
      expect(topBtn.className).toContain("bg-accent");
    });
  });

  it("switches category on click", async () => {
    render(<UploadPage />);
    fireEvent.click(screen.getByText("Select Photo"));

    await waitFor(() => {
      expect(screen.getByText("하의")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("하의"));
    expect(screen.getByText("하의").className).toContain("bg-accent");
    expect(screen.getByText("상의").className).not.toContain("bg-accent");
  });

  it("uploads and navigates to analyze page on submit", async () => {
    mockUpload.mockResolvedValue({ image_url: "https://storage.example.com/img.jpg" });

    render(<UploadPage />);
    fireEvent.click(screen.getByText("Select Photo"));

    await waitFor(() => {
      expect(screen.getByText("분석 시작하기")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("분석 시작하기"));

    await waitFor(() => {
      expect(mockUpload).toHaveBeenCalledTimes(1);
    });

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith(
        expect.stringContaining("/closet/analyze?"),
      );
    });

    const url = mockPush.mock.calls[0][0] as string;
    expect(url).toContain("image_url=https");
    expect(url).toContain("category=top");
    expect(url).toContain("user_tone_id=autumn_warm_deep");
  });

  it("shows upload progress during upload", async () => {
    let progressCallback: ((p: number) => void) | undefined;
    mockUpload.mockImplementation((_file: File, onProgress: (p: number) => void) => {
      progressCallback = onProgress;
      return new Promise(() => {}); // never resolves
    });

    render(<UploadPage />);
    fireEvent.click(screen.getByText("Select Photo"));

    await waitFor(() => {
      expect(screen.getByText("분석 시작하기")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("분석 시작하기"));

    await waitFor(() => {
      expect(progressCallback).toBeDefined();
    });

    progressCallback!(50);

    await waitFor(() => {
      expect(screen.getByText(/업로드 중.*50%/)).toBeInTheDocument();
    });
  });

  it("shows error message on upload failure", async () => {
    mockUpload.mockRejectedValue(new Error("서버 연결 실패"));

    render(<UploadPage />);
    fireEvent.click(screen.getByText("Select Photo"));

    await waitFor(() => {
      expect(screen.getByText("분석 시작하기")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("분석 시작하기"));

    await waitFor(() => {
      expect(screen.getByText("서버 연결 실패")).toBeInTheDocument();
    });
    expect(screen.getByText("다시 시도하기")).toBeInTheDocument();
  });

  it("navigates back on back button click", () => {
    Object.defineProperty(window.history, "length", { value: 2, configurable: true });
    render(<UploadPage />);
    fireEvent.click(screen.getByLabelText("뒤로가기"));
    expect(mockBack).toHaveBeenCalled();
  });
});
