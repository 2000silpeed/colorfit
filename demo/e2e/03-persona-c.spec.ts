import { test, expect } from "@playwright/test";
import path from "path";
import { Recorder, BASE_URL, issueGuestToken, injectAuth } from "./lib/helpers";


test("페르소나 C — 여성 40+ · 겨울쿨딥 · 옷장 → 코디 완성 풀플로우", async ({ page, request }) => {
  test.setTimeout(180_000);
  const rec = new Recorder("C", "페르소나 C (여성 40+·겨울쿨딥·코디완성)");
  page.on("pageerror", (e) => console.log(`  [pageerror] ${e.message}`));
  page.on("console", (m) => { if (m.type() === "error") console.log(`  [console:err] ${m.text()}`); });

  // ── 온보딩 API로 유저 생성 (백엔드에 프로필 등록) ──
  const onboardRes = await request.post(`${BASE_URL.replace("3000", "8000")}/api/onboarding`, {
    data: {
      gender: "female",
      age_group: "40plus",
      tone_id: "winter_cool_deep",
      tpo_list: ["event"],
      style_moods: [],
      budget_min: 150000,
      budget_max: 300000,
    },
  });
  const onboardData = await onboardRes.json() as { user_id: string };
  const userId = onboardData.user_id;
  console.log(`  [demo] onboarded user_id: ${userId}`);

  // 게스트 JWT 발급 (해당 user_id로)
  const guest = await issueGuestToken(request, userId);
  await page.goto(`${BASE_URL}/login`, { waitUntil: "networkidle" });
  await injectAuth(page, userId, guest.access_token, {
    colorfit_gender: "female",
    colorfit_tone: "winter_cool_deep",
    colorfit_tone_id: "winter_cool_deep",
    colorfit_age_group: "40plus",
    colorfit_tpos: JSON.stringify(["event"]),
    colorfit_budget: JSON.stringify([150000, 300000]),
  });
  await page.reload({ waitUntil: "networkidle" });

  // ① 옷장 진입 (빈 상태)
  await page.goto(`${BASE_URL}/closet`, { waitUntil: "networkidle" });
  await page.waitForTimeout(1500);
  await rec.shoot(page, "closet_empty", "① 옷장 (빈 상태)", "아직 분석한 옷이 없어요 → 첫 번째 옷 분석하기 CTA");

  // ② 옷장 업로드 — 샘플 이미지 업로드
  await page.goto(`${BASE_URL}/closet/upload`, { waitUntil: "networkidle" });
  await page.waitForTimeout(800);
  const fixturePath = path.resolve(__dirname, "fixtures/sample_top_coral.png");
  await page.locator('input[data-testid="gallery-input"]').setInputFiles(fixturePath);
  await page.waitForTimeout(1500);
  await rec.shoot(page, "closet_upload", "② 옷장 업로드 (프리뷰)", "코랄 톤 상의 이미지 + 분석 시작 버튼");

  // ③ 분석 시작 → 분석 중
  const analyzeBtn = page.getByRole("button", { name: /분석 시작하기/ });
  await analyzeBtn.click();
  await page.waitForURL(/\/closet\/analyze/, { timeout: 45_000 }).catch(() => {});
  await page.waitForTimeout(2000);
  await rec.shoot(page, "closet_analyzing", "③ 옷장 분석 중", "Gemini Vision — 색상/카테고리/톤 호환성 분석");

  // ④ 분석 결과 대기
  await page.waitForSelector("text=/분석 결과|추천 코디|다시|결과|훌륭|좋아요|아쉬워요/", { timeout: 60_000 }).catch(() => {});
  await page.waitForTimeout(2000);
  await rec.shoot(page, "closet_analyze_result", "④ 옷장 분석 결과", "PCF 스코어 + 톤 매칭 + 카테고리 분류");

  // ④-1 "옷장에 추가" 버튼 클릭 → 자동 리다이렉트 대기
  const addToClosetBtn = page.locator("button").filter({ hasText: "옷장에 추가" });
  if (await addToClosetBtn.count()) {
    await addToClosetBtn.click();
    await page.waitForSelector("text=옷장에 추가되었어요", { timeout: 10_000 }).catch(() => {});
    await page.waitForURL(/closet(?:\?|$)/, { timeout: 10_000 }).catch(() => {});
    await page.waitForTimeout(1500);
  }

  // ⑤ 옷장 목록 (분석된 아이템 확인)
  if (!page.url().match(/\/closet(\?|$)/)) {
    await page.goto(`${BASE_URL}/closet`, { waitUntil: "networkidle" });
  }
  // 아이템 로드 대기
  await page.waitForSelector("text=/내 옷장|코디 완성하기/", { timeout: 10_000 }).catch(() => {});
  const hasItems = await page.locator("text=코디 완성하기").count();
  if (hasItems === 0) {
    await page.reload({ waitUntil: "networkidle" });
    await page.waitForSelector("text=/내 옷장|코디 완성하기/", { timeout: 10_000 }).catch(() => {});
  }
  await page.waitForTimeout(1000);
  await rec.shoot(page, "closet_with_item", "⑤ 옷장 (아이템 보유)", "분석 완료된 아이템 + 점수 뱃지");

  // ⑥ '코디 완성하기' 클릭 → 코디 완성 피드
  const outfitBtn = page.getByRole("button", { name: /코디 완성하기/ }).first();
  if (await outfitBtn.count()) {
    await outfitBtn.click();
    await page.waitForURL(/\/closet\/outfits/, { timeout: 10_000 }).catch(() => {});
  } else {
    // 직접 URL로 진입 (아이템 ID 필요)
    const itemId = await page.evaluate(() => {
      const btn = document.querySelector("button[aria-label*='코디 완성하기']");
      return btn?.closest("[data-item-id]")?.getAttribute("data-item-id") ?? "";
    });
    if (itemId) {
      await page.goto(`${BASE_URL}/closet/outfits?item_id=${itemId}`, { waitUntil: "networkidle" });
    }
  }
  // 코디 카드 실제 렌더링 대기 (스켈레톤 → 카드 or 빈 상태 or 에러)
  await page.waitForSelector("text=/코디를 찾았어요|매칭되는 코디가 없어요|불러오지 못했어요/", { timeout: 15_000 }).catch(() => {});
  await page.waitForTimeout(1000);
  await rec.shoot(page, "closet_outfits_feed", "⑥ 코디 완성 피드", "내 옷 기반 매칭 코디 + TPO 필터 + 내 옷 뱃지 + 추가 구매 비용");

  // ⑦ TPO 필터 — 행사 탭
  const eventTab = page.getByRole("button", { name: "행사" }).first();
  if (await eventTab.count()) {
    await eventTab.click();
    await page.waitForSelector("text=/코디를 찾았어요|매칭되는 코디가 없어요|불러오지 못했어요/", { timeout: 10_000 }).catch(() => {});
    await page.waitForTimeout(1000);
    await rec.shoot(page, "closet_outfits_tpo", "⑦ TPO 필터 (행사)", "행사 TPO로 필터링된 코디");

    // 행사 결과 없으면 전체로 복귀
    const hasEvent = await page.locator("article").count();
    if (hasEvent === 0) {
      const allTab = page.getByRole("button", { name: "전체" }).first();
      if (await allTab.count()) {
        await allTab.click();
        await page.waitForSelector("text=/코디를 찾았어요/", { timeout: 10_000 }).catch(() => {});
        await page.waitForTimeout(1000);
      }
    }
  }

  // ⑧ 코디 카드 탭 → 코디 상세 (closet 모드)
  const outfitCard = page.locator("article").first();
  if (await outfitCard.count()) {
    await outfitCard.click();
    await page.waitForURL(/\/outfit\/.*closet_item_id/, { timeout: 10_000 }).catch(() => {});
    // 스켈레톤 → 실제 콘텐츠 로드 대기
    await page.locator("h1").first().waitFor({ state: "visible", timeout: 15_000 }).catch(() => {});
    await page.waitForTimeout(1000);
    await rec.shoot(page, "outfit_detail_closet", "⑧ 코디 상세 (옷장 모드)", "5축 스코어 + 추천 이유");

    // ⑨ 아이템 구성 — 보유 중 뱃지 + 구매 링크 확인
    await page.mouse.wheel(0, 600);
    await page.waitForTimeout(1000);
    await rec.shoot(page, "outfit_items_closet", "⑨ 아이템 구성 (보유 중/구매)", "보유 중 뱃지 + 카탈로그 아이템 외부 링크 + 추가 구매 합계");

    // 보유 중 뱃지 존재 확인
    const ownedBadges = page.locator("text=보유 중");
    const badgeCount = await ownedBadges.count();
    console.log(`  [demo] 보유 중 뱃지: ${badgeCount}개`);

    // 구매 합계 섹션 확인
    const purchaseSummary = page.locator("text=추가 구매 합계");
    if (await purchaseSummary.count()) {
      await page.mouse.wheel(0, 300);
      await page.waitForTimeout(500);
      await rec.shoot(page, "purchase_summary", "⑩ 추가 구매 합계", "보유 N개 · 구매 필요 N개 · 합계 금액");
    }

    // 카탈로그 아이템 외부 링크 확인
    const externalLinks = page.locator('a[target="_blank"][href*="http"]');
    const linkCount = await externalLinks.count();
    console.log(`  [demo] 외부 구매 링크: ${linkCount}개`);
    if (linkCount > 0) {
      const href = await externalLinks.first().getAttribute("href");
      console.log(`  [demo] 첫 번째 구매 링크: ${href}`);
    }
  }

  // ⑬ 피드로 이동 — 행사 TPO
  await page.goto(`${BASE_URL}/feed`, { waitUntil: "networkidle" });
  await page.waitForTimeout(1500);
  await rec.shoot(page, "feed", "⑪ 피드 진입", "겨울쿨딥 + 40+ 여성 하객룩 피드");

  const feedEventTab = page.getByRole("button", { name: "행사" }).first();
  if (await feedEventTab.count()) {
    await feedEventTab.click();
    await page.waitForTimeout(1200);
    await rec.shoot(page, "feed_tpo_event", "⑫ 행사 TPO 피드", "격식있는 하객룩 우선 노출");
  }

  // ⑭ 프로필
  await page.goto(`${BASE_URL}/profile`, { waitUntil: "networkidle" });
  await page.waitForTimeout(1000);
  await rec.shoot(page, "profile", "⑬ 프로필", "겨울쿨딥 톤 · 선호도 · 브랜드 · 로그아웃");

  rec.save();
});
