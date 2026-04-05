import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: ".",
  testMatch: ["*.spec.ts", "**/*.spec.ts"],
  testIgnore: ["**/node_modules/**", "**/_*.bak"],
  timeout: 120_000,
  reporter: [["list"]],
  outputDir: "output/artifacts",
  use: {
    baseURL: "http://localhost:3000",
    video: {
      mode: "on",
      size: { width: 390, height: 844 },
    },
    viewport: { width: 390, height: 844 },
    deviceScaleFactor: 2,
    isMobile: true,
    hasTouch: true,
    userAgent:
      "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
  },
  projects: [
    {
      name: "iphone",
      use: { ...devices["Pixel 7"] },
    },
  ],
});
