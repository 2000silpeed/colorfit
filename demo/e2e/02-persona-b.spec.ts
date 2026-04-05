import { test } from "@playwright/test";
import { Recorder, BASE_URL, issueGuestToken, injectAuth } from "./lib/helpers";

test("페르소나 B — 남성 30대 · 가을웜딥 · 출근룩", async ({ page, request }) => {
  test.setTimeout(120_000);
  const rec = new Recorder("B", "페르소나 B (남성 30대·가을웜딥·출근)");

  // 게스트 JWT + 프로필 localStorage 프리셋
  const guest = await issueGuestToken(request);
  await page.goto(`${BASE_URL}/login`, { waitUntil: "networkidle" });
  await injectAuth(page, guest.user_id, guest.access_token, {
    colorfit_gender: "male",
    colorfit_tone: "autumn_warm_deep",
    colorfit_tone_id: "autumn_warm_deep",
    colorfit_age_group: "30s",
    colorfit_tpos: JSON.stringify(["commute"]),
    colorfit_budget: JSON.stringify([50000, 150000]),
  });
  await page.reload({ waitUntil: "networkidle" });

  // 1. 피드 진입 (온보딩 건너뜀 — 톤이 있어서 /feed로 바로)
  await page.goto(`${BASE_URL}/feed`, { waitUntil: "networkidle" });
  await page.waitForTimeout(1500);
  await rec.shoot(page, "feed_entry", "① 피드 진입 (게스트 + 프로필 프리셋)", "가을웜딥 + 남성 + 30대 맞춤 피드");

  // 2. 출근 TPO
  const commuteTab = page.getByRole("button", { name: "출근" }).first();
  await commuteTab.click();
  await page.waitForTimeout(1200);
  await rec.shoot(page, "tpo_commute", "② 출근 TPO 필터", "오피스 포멀 코디 우선 노출");

  // 3. 예산 슬라이더 조정
  const budgetBtn = page.locator("button").filter({ hasText: /₩\d+만~₩\d+만/ }).first();
  if (await budgetBtn.count()) {
    await budgetBtn.click();
    await page.waitForTimeout(600);
    await rec.shoot(page, "budget_open", "③ 예산 슬라이더 열기", "듀얼 레인지 슬라이더 (0~50만원, 1만 단위)");
  }

  // 4. 추천 브랜드 토글
  const brandToggle = page.getByText("추천 브랜드", { exact: false }).first();
  if (await brandToggle.count()) {
    await brandToggle.click({ force: true });
    await page.waitForTimeout(1000);
    await rec.shoot(page, "brand_filter", "④ 추천 브랜드 필터", "선호 브랜드 아이템만 노출 (프리퍼런스 기반)");
  }

  // 5. 피드 스크롤 + 코디 상세
  await page.mouse.wheel(0, 600);
  await page.waitForTimeout(500);
  const card = page.locator("article[role='link']").first();
  await card.click();
  await page.waitForURL(/\/outfit\//, { timeout: 10_000 });
  // 스켈레톤이 사라지고 실제 콘텐츠(제목 h1)가 나타날 때까지 대기
  await page.locator("h1").first().waitFor({ state: "visible", timeout: 10_000 });
  await page.waitForTimeout(500);
  await rec.shoot(page, "detail", "⑤ 코디 상세", "가을웜딥 + 출근 스코어 + 5축 레이더");

  // 6. 상세에서 스코어 확인 스크롤
  await page.mouse.wheel(0, 500);
  await page.waitForTimeout(400);
  await rec.shoot(page, "detail_score", "⑥ 5축 스코어 전체", "PCF·OF·CH·PE·SF 각 축 설명 + 툴팁");

  // 7. 돌아가서 저장 3개
  await page.goBack();
  await page.waitForTimeout(1000);
  const hearts = page.locator('button[aria-label="저장"]');
  const heartCount = Math.min(await hearts.count(), 3);
  for (let i = 0; i < heartCount; i++) {
    await hearts.nth(i).scrollIntoViewIfNeeded();
    await hearts.nth(i).evaluate((el: HTMLElement) => el.click());
    await page.waitForTimeout(400);
  }
  await rec.shoot(page, "save_multi", "⑦ 복수 저장 (3개)", "Top Pick 진입 조건 충족 (2개 이상)");

  // 8. 저장 목록 진입
  await page.goto(`${BASE_URL}/saved`, { waitUntil: "networkidle" });
  await page.waitForTimeout(1200);
  await rec.shoot(page, "saved_list", "⑧ 저장 목록", "Top Pick + A vs B 버튼 노출");

  // 9. Top Pick 모달
  const topPickBtn = page.getByRole("button", { name: /Top Pick/i }).first();
  if (await topPickBtn.count()) {
    await topPickBtn.click();
    await page.waitForTimeout(2500); // Top Pick 스코어링 대기
    await rec.shoot(page, "top_pick", "⑨ Top Pick 추천", "저장 코디 중 최고 스코어 1개 자동 선별 (5축 가중 평균)");
    await page.keyboard.press("Escape").catch(() => {});
    await page.waitForTimeout(400);
  }

  // 10. 정렬 변경 (점수순)
  const scoreSortBtn = page.getByRole("button", { name: "점수순" }).first();
  if (await scoreSortBtn.count()) {
    await scoreSortBtn.click();
    // 정렬 후 이미지가 로딩될 때까지 대기
    await page.locator("img").first().waitFor({ state: "visible", timeout: 10_000 });
    await page.waitForTimeout(800);
    await rec.shoot(page, "saved_sort_score", "⑩ 점수순 정렬", "저장 코디 스코어 기준 재정렬");
  }

  rec.save();
});
