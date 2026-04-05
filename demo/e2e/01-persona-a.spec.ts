import { test } from "@playwright/test";
import { Recorder, BASE_URL, API_BASE, issueGuestToken, injectAuth } from "./lib/helpers";

test("페르소나 A — 여성 20대 · 여름쿨소프트 · 소개팅 룩", async ({ page, request }) => {
  test.setTimeout(180_000);
  const rec = new Recorder("A", "페르소나 A (여성 20대·여름쿨소프트·데이트)");

  page.on("console", (msg) => {
    if (msg.type() === "error") console.log(`  [browser:err] ${msg.text()}`);
  });

  // 게스트 JWT 발급
  const guest = await issueGuestToken(request);
  console.log(`  [demo] guest user_id=${guest.user_id}`);

  // 1. 로그인
  await page.goto(`${BASE_URL}/login`, { waitUntil: "networkidle" });
  await injectAuth(page, guest.user_id, guest.access_token);
  await page.reload({ waitUntil: "networkidle" });
  await rec.shoot(page, "login", "① 로그인 화면", "카카오/구글 OAuth + 게스트 진입. 데모는 JWT 주입으로 우회.");

  // 2~7. 온보딩 5스텝
  await page.getByText("게스트로 둘러보기").click();
  await page.waitForURL(/\/onboarding\/step1/);
  await rec.shoot(page, "onb1", "② Step1 성별/연령", "여성·20대 선택");
  await page.getByRole("button", { name: "여성 선택" }).click();
  await page.getByRole("button", { name: /20대 선택/ }).click();
  await page.waitForURL(/\/step2/);
  await page.getByText("여름쿨", { exact: true }).click();
  await page.waitForTimeout(400);
  await rec.shoot(page, "onb2_tone", "③ Step2 톤 확장", "여름쿨 → 소프트/라이트/뮤트 확장");
  await page.getByRole("button", { name: /소프트/ }).first().click();
  await page.getByRole("button", { name: /다음 단계로/ }).click();
  await page.waitForURL(/\/step3/);
  await page.getByText("데이트", { exact: true }).click();
  await page.getByRole("button", { name: /다음 단계로/ }).click();
  await page.waitForURL(/\/step4/);
  await page.getByRole("button", { name: /5~15만/ }).first().click();
  await page.getByRole("button", { name: /추천 코디 보러가기/ }).click();
  await page.waitForURL(/\/step5/);
  await page.getByRole("button", { name: /취향 분석 건너뛰기/ }).click();
  await page.waitForURL(/\/feed/, { timeout: 15_000 });
  await page.waitForTimeout(1500);

  // 온보딩 후 user_id 재발급
  const newUid = await page.evaluate(() => localStorage.getItem("colorfit_user_id"));
  if (newUid && newUid !== guest.user_id) {
    const refreshed = await issueGuestToken(request, newUid);
    await page.evaluate((t) => localStorage.setItem("colorfit_token", t), refreshed.access_token);
  }
  const userId = newUid!;

  await rec.shoot(page, "feed", "④ 피드 진입", "여름쿨소프트 + 데이트 맞춤 피드 (5022 outfits)");

  // 스와이프 싫어요
  const firstCard = page.locator("article[role='link']").first();
  const box = await firstCard.boundingBox();
  if (box) {
    await page.mouse.move(box.x + box.width - 30, box.y + box.height / 2);
    await page.mouse.down();
    await page.mouse.move(box.x - 100, box.y + box.height / 2, { steps: 10 });
    await page.mouse.up();
    await page.waitForTimeout(800);
    await rec.shoot(page, "dislike_swipe", "⑤ 스와이프 싫어요", "좌스와이프로 관심없음 처리 → 피드에서 제거");
  }

  // 하트 저장
  const heart = page.locator('button[aria-label="저장"]').first();
  await heart.scrollIntoViewIfNeeded();
  await heart.evaluate((el: HTMLElement) => el.click());
  await page.waitForTimeout(800);
  await rec.shoot(page, "save_heart", "⑥ 하트 저장", "reactions 테이블 기록 (onConflict 지원)");

  // 코디 상세
  const card = page.locator("article[role='link']").first();
  const savedOutfitId = await card.evaluate((el) => {
    const next = el.nextElementSibling as HTMLElement | null;
    return el.getAttribute("data-outfit-id") || next?.getAttribute("data-outfit-id") || "";
  });
  await card.click();
  await page.waitForURL(/\/outfit\//, { timeout: 10_000 });
  await page.waitForTimeout(1500);
  await rec.shoot(page, "detail", "⑦ 코디 상세 & 5축 스코어", "PCF·OF·CH·PE·SF 레이더 + 추천 이유");

  await page.mouse.wheel(0, 400);
  await page.waitForTimeout(400);
  await rec.shoot(page, "detail_items", "⑧ 아이템 리스트", "상품별 외부 링크 (무신사/29cm)");

  // 착장샷 (Gemini)
  const tryOnBtn = page.getByRole("button", { name: /착장으로 보기/ });
  if (await tryOnBtn.count()) {
    await tryOnBtn.click();
    await rec.shoot(page, "tryon_loading", "⑨ 착장샷 생성 중", "Gemini 2.5 Flash Image로 AI 합성 (10~30초)");
    // wait for image
    await page.waitForSelector("img[alt*='착장'], img[src^='data:image']", { timeout: 60_000 }).catch(() => {});
    await page.waitForTimeout(2000);
    await rec.shoot(page, "tryon_result", "⑩ 착장샷 결과", "Gemini nano-banana 생성 이미지");
    // close modal: 오버레이 JS click (Framer Motion 애니메이션 중에도 작동)
    await page.evaluate(() => {
      const overlay = document.querySelector("div.fixed.inset-0.bg-black\\/40") as HTMLElement | null;
      overlay?.click();
    });
    await page.waitForTimeout(1200);
    // 모달이 사라질 때까지 대기
    await page.locator('div[role="dialog"][aria-label="AI 착장 미리보기"]').waitFor({ state: "detached", timeout: 5000 }).catch(() => {});
  }

  // A vs B 비교
  const compareBtn = page.getByRole("button", { name: /A vs B 비교/ });
  if (await compareBtn.count()) {
    await compareBtn.click();
    await page.waitForTimeout(1200);
    await rec.shoot(page, "compare_picker", "⑪ 비교 대상 선택", "저장한 코디 중 1개 선택 → A vs B");
    // pick first available
    const candidate = page.locator("button").filter({ hasText: /₩/ }).first();
    if (await candidate.count()) {
      await candidate.click();
      await page.waitForURL(/\/compare/, { timeout: 10_000 });
      await page.waitForTimeout(1500);
      await rec.shoot(page, "compare_view", "⑫ A vs B 결과", "두 코디 스코어 5축 직접 비교");
      await page.goBack();
      await page.waitForTimeout(800);
    } else {
      await page.keyboard.press("Escape").catch(() => {});
    }
  }

  // 저장 목록
  await page.goto(`${BASE_URL}/saved`, { waitUntil: "networkidle" });
  await page.waitForTimeout(1000);
  await rec.shoot(page, "saved_list", "⑬ 저장 목록", "정렬(최근/점수/가격) + Top Pick + A vs B 진입점");

  // 프로필
  await page.goto(`${BASE_URL}/profile`, { waitUntil: "networkidle" });
  await page.waitForTimeout(800);
  await rec.shoot(page, "profile", "⑭ 프로필", "톤 정보 · 설정 · 로그아웃");

  rec.save();
});
