import { test } from "@playwright/test";
import path from "path";
import { Recorder, BASE_URL, issueGuestToken, injectAuth } from "./lib/helpers";

test("페르소나 C — 여성 40+ · 겨울쿨딥 · 하객/이벤트룩", async ({ page, request }) => {
  test.setTimeout(180_000);
  const rec = new Recorder("C", "페르소나 C (여성 40+·겨울쿨딥·이벤트)");
  page.on("pageerror", (e) => console.log(`  [pageerror] ${e.message}`));
  page.on("console", (m) => { if (m.type() === "error") console.log(`  [console:err] ${m.text()}`); });

  // 게스트 JWT + 프리셋
  const guest = await issueGuestToken(request);
  await page.goto(`${BASE_URL}/login`, { waitUntil: "networkidle" });
  await injectAuth(page, guest.user_id, guest.access_token, {
    colorfit_gender: "female",
    colorfit_tone: "winter_cool_deep",
    colorfit_tone_id: "winter_cool_deep",
    colorfit_age_group: "40plus",
    colorfit_tpos: JSON.stringify(["event"]),
    colorfit_budget: JSON.stringify([150000, 300000]),
  });
  await page.reload({ waitUntil: "networkidle" });

  // 1. 피드 진입
  await page.goto(`${BASE_URL}/feed`, { waitUntil: "networkidle" });
  await page.waitForTimeout(1500);
  await rec.shoot(page, "feed", "① 피드 진입", "겨울쿨딥 + 40+ 여성 하객룩");

  // 2. 이벤트 TPO
  const eventTab = page.getByRole("button", { name: "행사" }).first();
  if (await eventTab.count()) {
    await eventTab.click();
    await page.waitForTimeout(1200);
    await rec.shoot(page, "tpo_event", "② 행사 TPO", "격식있는 하객룩 우선 노출");
  }

  // 3. 프로필 진입
  await page.goto(`${BASE_URL}/profile`, { waitUntil: "networkidle" });
  await page.waitForTimeout(1000);
  await rec.shoot(page, "profile", "③ 프로필", "톤 · 선호도 · 브랜드 · 로그아웃");

  // 4. 톤 상세 (프로필에서 톤 카드 클릭)
  const toneCard = page.locator("button").filter({ hasText: /겨울|winter|딥/ }).first();
  if (await toneCard.count()) {
    await toneCard.click({ force: true }).catch(() => {});
    await page.waitForTimeout(1500);
    if (page.url().includes("/tone/")) {
      await rec.shoot(page, "tone_detail", "④ 톤 상세 페이지", "겨울쿨딥 팔레트 · 추천 컬러 · 회피 컬러");

      // 톤 변경 버튼
      const changeToneBtn = page.getByRole("button", { name: /다른 톤으로 변경/ });
      if (await changeToneBtn.count()) {
        await changeToneBtn.click();
        await page.waitForURL(/step2/, { timeout: 5000 }).catch(() => {});
        await page.waitForTimeout(1000);
        await rec.shoot(page, "tone_change", "⑤ 톤 변경 모드", "온보딩 Step2 재진입 (mode=change)");
      }
    }
  }

  // 5. 프리미엄 페이지
  await page.goto(`${BASE_URL}/premium`, { waitUntil: "networkidle" });
  await page.waitForTimeout(1000);
  await rec.shoot(page, "premium", "⑥ 프리미엄 구독", "Free vs Premium 비교 · 착장샷 무제한 · 광고 제거");

  // 6. 옷장 (closet)
  await page.goto(`${BASE_URL}/closet`, { waitUntil: "networkidle" });
  await page.waitForTimeout(1000);
  await rec.shoot(page, "closet", "⑦ 옷장", "내 옷 업로드 · 분석 · 추천 엔진 통합");

  // 7. 옷장 업로드 — 실제 샘플 이미지 업로드
  await page.goto(`${BASE_URL}/closet/upload`, { waitUntil: "networkidle" });
  await page.waitForTimeout(800);
  const fixturePath = path.resolve(__dirname, "fixtures/sample_top_coral.png");
  await page.locator('input[data-testid="gallery-input"]').setInputFiles(fixturePath);
  await page.waitForTimeout(1500); // 프리뷰 렌더
  await rec.shoot(page, "closet_upload", "⑧ 옷장 업로드 (프리뷰)", "상의(top) 카테고리 · 프리뷰 + 분석 시작 버튼");

  // 분석 시작
  const analyzeBtn = page.getByRole("button", { name: /분석 시작하기/ });
  await analyzeBtn.click();
  // 업로드 + Gemini Vision 분석 대기 (최대 45초)
  await page.waitForURL(/\/closet\/analyze/, { timeout: 45_000 }).catch(() => {});
  await page.waitForTimeout(2000);
  await rec.shoot(page, "closet_analyzing", "⑨ 옷장 분석 중", "Gemini Vision 호출 — 색상/카테고리/톤 호환성 분석");

  // 분석 결과 대기
  await page.waitForSelector("text=/분석 결과|추천 코디|다시|결과/", { timeout: 60_000 }).catch(() => {});
  await page.waitForTimeout(2000);
  await rec.shoot(page, "closet_analyze", "⑩ 옷장 분석 결과", "Gemini Vision 결과 + 웜톤 적합도 + 추천 코디");

  // 8. 브랜드 설정
  await page.goto(`${BASE_URL}/brands`, { waitUntil: "networkidle" });
  await page.waitForTimeout(1000);
  await rec.shoot(page, "brands", "⑨ 브랜드 선호 설정", "추천 브랜드 선택 → 피드 필터에 반영");

  // 9. 선호도 설정
  await page.goto(`${BASE_URL}/preference`, { waitUntil: "networkidle" });
  await page.waitForTimeout(1000);
  await rec.shoot(page, "preference", "⑩ 선호도 설정", "가중치 자동 조정 (PCF·OF·CH·PE·SF) · 선호 누적 시각화");

  rec.save();
});
