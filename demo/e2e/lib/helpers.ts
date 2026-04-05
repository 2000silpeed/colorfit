import { Page, APIRequestContext } from "@playwright/test";
import fs from "fs";
import path from "path";

export const BASE_URL = "http://localhost:3000";
export const API_BASE = "http://localhost:8000";
export const OUT_DIR = path.resolve(__dirname, "../output");
export const SHOTS_DIR = path.join(OUT_DIR, "screenshots");

fs.mkdirSync(SHOTS_DIR, { recursive: true });

export interface Step {
  persona: string;
  id: string;
  title: string;
  desc: string;
  url: string;
  screenshot: string;
  timestamp: string;
}

export class Recorder {
  private steps: Step[] = [];
  private counter = 0;

  constructor(public personaId: string, public personaName: string) {}

  async shoot(page: Page, id: string, title: string, desc: string) {
    await page.waitForTimeout(500);
    this.counter++;
    const filename = `${this.personaId}_${String(this.counter).padStart(2, "0")}_${id}.png`;
    const fullpath = path.join(SHOTS_DIR, filename);
    await page.screenshot({ path: fullpath, fullPage: false });
    const step: Step = {
      persona: this.personaName,
      id,
      title,
      desc,
      url: page.url().replace(BASE_URL, ""),
      screenshot: `screenshots/${filename}`,
      timestamp: new Date().toISOString(),
    };
    this.steps.push(step);
    console.log(`  ✓ [${this.personaId}:${this.counter}] ${title} → ${filename}`);
  }

  save() {
    const out = path.join(OUT_DIR, `steps_${this.personaId}.json`);
    fs.writeFileSync(out, JSON.stringify(this.steps, null, 2));
    return this.steps;
  }
}

export async function issueGuestToken(
  request: APIRequestContext,
  existingUserId?: string,
): Promise<{ user_id: string; access_token: string }> {
  const url = new URL(`${API_BASE}/api/auth/guest`);
  if (existingUserId) url.searchParams.set("guest_user_id", existingUserId);
  const res = await request.post(url.toString());
  return res.json();
}

export async function injectAuth(
  page: Page,
  userId: string,
  token: string,
  extras?: Record<string, string>,
) {
  await page.evaluate(
    ({ userId, token, extras }) => {
      localStorage.setItem("colorfit_user_id", userId);
      localStorage.setItem("colorfit_token", token);
      if (extras) for (const [k, v] of Object.entries(extras)) localStorage.setItem(k, v);
    },
    { userId, token, extras },
  );
}
