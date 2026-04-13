const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

interface FeedParams {
  toneId: string;
  gender?: string;
  ageGroup?: string;
  tpo?: string;
  budgetMin?: number;
  budgetMax?: number;
  userId?: string;
  verifiedOnly?: boolean;
  preferredBrands?: string[];
  page?: number;
}

export interface ScoresResponse {
  pcf: number;
  of: number;
  ch: number;
  pe: number;
  sf: number;
}

export interface FeedItemBrief {
  image_url: string | null;
  category: string | null;
  group: string | null;
  brand: string | null;
  style_tag: string | null;
  is_verified_brand: boolean;
}

export interface OutfitFeedItem {
  id: string;
  gender: string | null;
  designed_tpo: string | null;
  total_price: number | null;
  tags: string[] | null;
  scores: ScoresResponse | null;
  soft_score: number;
  final_score: number;
  reasons: string[];
  image_url: string | null;
  items: FeedItemBrief[];
}

export interface FeedResponse {
  outfits: OutfitFeedItem[];
  page: number;
  page_size: number;
  total: number;
  has_next: boolean;
}

export interface ReactionResponse {
  id: number;
  user_id: string;
  outfit_id: string;
  reaction_type: string;
}

export async function postReaction(
  userId: string,
  outfitId: string,
  reactionType: "save" | "dislike",
): Promise<ReactionResponse> {
  const res = await fetch(`${API_BASE}/api/reaction`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      user_id: userId,
      outfit_id: outfitId,
      reaction_type: reactionType,
    }),
  });
  if (!res.ok) {
    throw new Error(`Reaction API error: ${res.status}`);
  }
  return res.json();
}

export interface ProductBrief {
  id: string;
  name: string | null;
  brand: string | null;
  category: string | null;
  price: number | null;
  image_url: string | null;
  mall_url: string | null;
  style_tag: string | null;
  is_verified_brand: boolean;
  color_hex: string | null;
  color_name: string | null;
  color_options: ColorOption[] | null;
}

export interface ScoreExplanations {
  pcf: string;
  of: string;
  ch: string;
  pe: string;
  sf: string;
}

export interface OutfitDetailResponse {
  id: string;
  gender: string | null;
  designed_tpo: string | null;
  designed_season: string | null;
  designed_moods: string[] | null;
  total_price: number | null;
  lowest_total_price: number | null;
  is_complete_outfit: boolean | null;
  tags: string[] | null;
  scores: ScoresResponse | null;
  reasons: string[] | null;
  score_explanations: ScoreExplanations | null;
  editor_comment: string | null;
  items: ProductBrief[];
}

export async function fetchOutfitDetail(
  outfitId: string,
  toneId?: string,
): Promise<OutfitDetailResponse> {
  const params = toneId ? `?tone_id=${encodeURIComponent(toneId)}` : "";
  const res = await fetch(`${API_BASE}/api/outfit/${outfitId}${params}`);
  if (!res.ok) {
    throw new Error(`Outfit API error: ${res.status}`);
  }
  return res.json();
}

/* ── 아이템 상세 ── */

export interface PriceEntry {
  mall_name: string;
  price: number;
  mall_url: string;
  is_lowest: boolean;
}

export interface ItemDetail {
  id: string;
  name: string | null;
  brand: string | null;
  category: string | null;
  color_hex: string | null;
  tone_id: string | null;
  price: number | null;
  mall_name: string | null;
  mall_url: string | null;
  image_url: string | null;
  gender: string | null;
  silhouette: string | null;
  formality: number | null;
  price_entries: PriceEntry[];
}

export interface SimilarProduct {
  id: string;
  name: string | null;
  brand: string | null;
  price: number | null;
  image_url: string | null;
  mall_url: string | null;
  similarity: number;
  match_type: string;
}

export interface SimilarListResponse {
  source_id: string;
  similar: SimilarProduct[];
}

export async function fetchItemDetail(itemId: string): Promise<ItemDetail> {
  const res = await fetch(`${API_BASE}/api/item/${itemId}`);
  if (!res.ok) {
    throw new Error(`Item API error: ${res.status}`);
  }
  return res.json();
}

export interface ColorOption {
  name: string;
  hex: string;
}

export interface ExtractColorsResponse {
  product_id: string;
  colors: ColorOption[];
}

export async function extractProductColors(
  productId: string,
  imageUrl: string,
): Promise<ExtractColorsResponse> {
  const res = await fetch(`${API_BASE}/api/tryon/extract-colors`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ product_id: productId, image_url: imageUrl }),
  });
  if (!res.ok) throw new Error(`Extract colors error: ${res.status}`);
  return res.json();
}

export interface AvailabilityCheck {
  available: boolean;
  mall_url: string | null;
  reason: string | null;
}

export async function checkItemAvailability(itemId: string): Promise<AvailabilityCheck> {
  const res = await fetch(`${API_BASE}/api/item/${itemId}/check-availability`);
  if (!res.ok) throw new Error(`Availability check error: ${res.status}`);
  return res.json();
}

export async function fetchSimilarItems(
  itemId: string,
  limit: number = 6,
): Promise<SimilarListResponse> {
  const res = await fetch(`${API_BASE}/api/item/${itemId}/similar?limit=${limit}`);
  if (!res.ok) {
    throw new Error(`Similar API error: ${res.status}`);
  }
  return res.json();
}

/* ── 구매 후 피드백 ── */

export type PurchaseFeedbackAction = "purchase" | "considering" | "not_helpful";
export type PurchaseFeedbackReason = "price_mismatch" | "style_different" | "sold_out" | "other";

export interface PurchaseFeedbackResponse {
  status: string;
  feedback_count: number;
  learning_phase: string;
}

export async function postPurchaseFeedback(
  userId: string,
  outfitId: string,
  action: PurchaseFeedbackAction,
  reason?: PurchaseFeedbackReason,
): Promise<PurchaseFeedbackResponse> {
  const body: Record<string, string> = {
    user_id: userId,
    outfit_id: outfitId,
    action,
  };
  if (reason) body.reason = reason;

  const res = await fetch(`${API_BASE}/api/feedback`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    throw new Error(`Feedback API error: ${res.status}`);
  }
  return res.json();
}

/* ── 톤 상세 ── */

export interface ToneColor {
  hex: string;
  name_ko: string;
}

export interface ToneDetailResponse {
  tone_id: string;
  tone_name_ko: string;
  season: string;
  temperature: string;
  depth: string;
  description: string;
  best_colors: ToneColor[];
  worst_colors: ToneColor[];
  all_colors: ToneColor[];
}

export async function fetchToneDetail(toneId: string): Promise<ToneDetailResponse> {
  const res = await fetch(`${API_BASE}/api/tone/${toneId}`);
  if (!res.ok) {
    throw new Error(`Tone API error: ${res.status}`);
  }
  return res.json();
}

/* ── 옷장 ── */

export interface ClosetItemData {
  id: string;
  image_url: string;
  category: string | null;
  dominant_color_hex: string | null;
  matched_tone_id: string | null;
  pcf_score: number | null;
  overall_score: number | null;
  reasons: string[] | null;
  created_at: string | null;
}

export interface ClosetStats {
  total_count: number;
  average_pcf: number;
  good_count: number;
  good_ratio: number;
}

export interface ClosetListResponse {
  items: ClosetItemData[];
  stats: ClosetStats;
}

export async function fetchCloset(userId: string): Promise<ClosetListResponse> {
  const res = await fetch(`${API_BASE}/api/closet?user_id=${userId}`);
  if (!res.ok) {
    throw new Error(`Closet API error: ${res.status}`);
  }
  return res.json();
}

/* ── 취향 관리 ── */

export interface StyleSeedData {
  mood_seed: string | null;
  silhouette_seed: string | null;
  color_seed: string | null;
  price_seed: string | null;
  seed_confidence: number | null;
}

export interface PreferenceStatusResponse {
  style_seed: StyleSeedData | null;
  feedback_count: number;
  learning_target: number;
  learning_phase: "seed" | "hybrid" | "learned";
  has_seed: boolean;
}

export interface PreferenceResetResponse {
  reset_mode: string;
  message: string;
}

export async function fetchPreferenceStatus(userId: string): Promise<PreferenceStatusResponse> {
  const res = await fetch(`${API_BASE}/api/preference/${userId}`);
  if (!res.ok) {
    throw new Error(`Preference API error: ${res.status}`);
  }
  return res.json();
}

export async function resetPreference(
  userId: string,
  mode: "all" | "feedback_only",
): Promise<PreferenceResetResponse> {
  const res = await fetch(`${API_BASE}/api/preference/${userId}/reset?mode=${mode}`, {
    method: "DELETE",
  });
  if (!res.ok) {
    throw new Error(`Preference reset error: ${res.status}`);
  }
  return res.json();
}

/* ── 옷 분석 ── */

export interface ColorDetail {
  hex: string;
  ratio: number;
}

export interface ClosetAnalyzeResponse {
  dominant_colors: ColorDetail[];
  matched_tone_id: string;
  matched_tone_name: string;
  pcf_score: number;
  saturation_score: number;
  lightness_score: number;
  overall_score: number;
  reasons: string[];
}

export async function analyzeClosetItem(
  imageUrl: string,
  userToneId: string,
): Promise<ClosetAnalyzeResponse> {
  const res = await fetch(`${API_BASE}/api/closet/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ image_url: imageUrl, user_tone_id: userToneId }),
  });
  if (!res.ok) {
    throw new Error(`Closet analyze error: ${res.status}`);
  }
  return res.json();
}

export interface AddClosetItemRequest {
  user_id: string;
  image_url: string;
  category?: string | null;
  dominant_color_hex?: string | null;
  matched_tone_id?: string | null;
  pcf_score?: number | null;
  overall_score?: number | null;
  reasons?: string[] | null;
}

export interface AddClosetItemResponse {
  id: string;
  message: string;
}

export async function addClosetItem(
  payload: AddClosetItemRequest,
): Promise<AddClosetItemResponse> {
  const res = await fetch(`${API_BASE}/api/closet`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    throw new Error(`Add closet item error: ${res.status}`);
  }
  return res.json();
}

export async function deleteUser(userId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/api/user/${userId}`, {
    method: "DELETE",
  });
  if (!res.ok) {
    throw new Error(`Delete user error: ${res.status}`);
  }
}

/* ── 역방향 추천 ── */

export interface RecommendedProduct {
  id: string;
  name: string | null;
  brand: string | null;
  category: string | null;
  price: number | null;
  image_url: string | null;
  mall_url: string | null;
  color_hex: string | null;
  similarity: number;
  match_reason: string;
}

export interface TpoOutfitSuggestion {
  tpo: string;
  tpo_label: string;
  items: RecommendedProduct[];
}

export interface ClosetRecommendationResponse {
  source_color_hex: string;
  source_category: string;
  user_tone_id: string;
  recommendations: TpoOutfitSuggestion[];
  total_count: number;
}

export async function fetchClosetRecommendations(
  colorHex: string,
  category: string,
  userToneId: string,
  tpo?: string,
  limit: number = 3,
): Promise<ClosetRecommendationResponse> {
  const q = new URLSearchParams({
    color_hex: colorHex,
    category,
    user_tone_id: userToneId,
    limit: String(limit),
  });
  if (tpo) q.set("tpo", tpo);
  const res = await fetch(`${API_BASE}/api/closet/recommendations?${q.toString()}`);
  if (!res.ok) {
    throw new Error(`Closet recommendations error: ${res.status}`);
  }
  return res.json();
}

/* ── 이미지 업로드 ── */

export interface UploadImageResponse {
  image_url: string;
}

export async function uploadClosetImage(
  file: File,
  onProgress?: (percent: number) => void,
): Promise<UploadImageResponse> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", `${API_BASE}/api/closet/upload`);

    xhr.upload.addEventListener("progress", (e) => {
      if (e.lengthComputable && onProgress) {
        onProgress(Math.round((e.loaded / e.total) * 100));
      }
    });

    xhr.addEventListener("load", () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        resolve(JSON.parse(xhr.responseText));
      } else {
        reject(new Error(`Upload error: ${xhr.status}`));
      }
    });

    xhr.addEventListener("error", () => reject(new Error("업로드 중 네트워크 오류가 발생했습니다.")));

    const formData = new FormData();
    formData.append("file", file);
    xhr.send(formData);
  });
}

/* ── Virtual Try-On ── */

export interface TryonGenerateResponse {
  image_url: string;
  outfit_id: string;
  cached: boolean;
  remaining: number | null;
}

export interface TryonUsageResponse {
  is_premium: boolean;
  usage_count: number;
  remaining: number | null;
}

export async function generateTryon(
  outfitId: string,
  userId: string,
  closetItemId?: string,
  modelImageUrl?: string,
  colorOverrides?: Record<string, string>,
): Promise<TryonGenerateResponse> {
  const body: Record<string, unknown> = {
    outfit_id: outfitId,
    user_id: userId,
  };
  if (closetItemId) body.closet_item_id = closetItemId;
  if (modelImageUrl) body.model_image_url = modelImageUrl;
  if (colorOverrides && Object.keys(colorOverrides).length > 0) {
    body.color_overrides = colorOverrides;
  }

  const res = await fetch(`${API_BASE}/api/tryon/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (res.status === 403) {
    const data = await res.json();
    throw new TryonLimitError(data.detail);
  }
  if (!res.ok) {
    throw new Error(`Try-On API error: ${res.status}`);
  }
  return res.json();
}

export class TryonLimitError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "TryonLimitError";
  }
}

export async function fetchTryonUsage(userId: string): Promise<TryonUsageResponse> {
  const res = await fetch(`${API_BASE}/api/tryon/usage?user_id=${userId}`);
  if (!res.ok) {
    throw new Error(`Try-On usage API error: ${res.status}`);
  }
  return res.json();
}

/* ── Subscription ── */

export type SubscriptionPlan = "monthly" | "yearly";

export interface SubscribeResponse {
  subscription_id: string;
  plan: string;
  status: string;
  price_krw: number;
  expires_at: string | null;
}

export interface SubscriptionStatusResponse {
  is_premium: boolean;
  plan: string | null;
  status: string | null;
  expires_at: string | null;
}

export async function subscribe(
  userId: string,
  plan: SubscriptionPlan,
  couponCode: string,
): Promise<SubscribeResponse> {
  const res = await fetch(`${API_BASE}/api/subscribe`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id: userId, plan, coupon_code: couponCode }),
  });
  if (!res.ok) {
    let detail = "구독 처리 중 오류가 발생했어요.";
    try {
      const data = await res.json();
      if (typeof data?.detail === "string") detail = data.detail;
    } catch {
      // ignore JSON parse error
    }
    throw new Error(detail);
  }
  return res.json();
}

export async function fetchSubscriptionStatus(
  userId: string,
): Promise<SubscriptionStatusResponse> {
  const res = await fetch(
    `${API_BASE}/api/subscription/status?user_id=${userId}`,
  );
  if (!res.ok) {
    throw new Error(`Subscription status API error: ${res.status}`);
  }
  return res.json();
}

/* ── 저장 목록 ── */

export interface SavedOutfit {
  id: string;
  gender: string | null;
  designed_tpo: string | null;
  total_price: number | null;
  tags: string[] | null;
  scores: ScoresResponse | null;
  soft_score: number;
  reasons: string[];
  image_url: string | null;
}

export interface SavedListResponse {
  outfits: SavedOutfit[];
  total: number;
}

export async function fetchSaved(
  userId: string,
  sortBy: "recent" | "score" | "price" = "recent",
): Promise<SavedListResponse> {
  const q = new URLSearchParams({ user_id: userId, sort_by: sortBy });
  const res = await fetch(`${API_BASE}/api/saved?${q.toString()}`);
  if (!res.ok) {
    throw new Error(`Saved API error: ${res.status}`);
  }
  return res.json();
}

/* ── Top Pick ── */

export interface TopPickResponse {
  id: string;
  gender: string | null;
  designed_tpo: string | null;
  total_price: number | null;
  tags: string[] | null;
  scores: ScoresResponse | null;
  soft_score: number;
  final_score: number;
  reasons: string[];
  highlight_reason: string;
  source: string;
  image_url: string | null;
  items: ProductBrief[];
}

export async function fetchTopPick(
  toneId: string,
  opts?: {
    gender?: string;
    tpo?: string;
    budgetMin?: number;
    budgetMax?: number;
    userId?: string;
  },
): Promise<TopPickResponse> {
  const q = new URLSearchParams({ tone_id: toneId });
  if (opts?.gender) q.set("gender", opts.gender);
  if (opts?.tpo) q.set("tpo", opts.tpo);
  if (opts?.budgetMin != null) q.set("budget_min", String(opts.budgetMin));
  if (opts?.budgetMax != null) q.set("budget_max", String(opts.budgetMax));
  if (opts?.userId) q.set("user_id", opts.userId);
  const res = await fetch(`${API_BASE}/api/top-pick?${q.toString()}`);
  if (!res.ok) {
    throw new Error(`Top Pick API error: ${res.status}`);
  }
  return res.json();
}

/* ── A vs B 비교 ── */

export interface OutfitBrief {
  id: string;
  gender: string | null;
  designed_tpo: string | null;
  total_price: number | null;
  scores: ScoresResponse | null;
  image_url: string | null;
}

export interface AxisComparison {
  axis: string;
  axis_name: string;
  score_a: number;
  score_b: number;
  diff: number;
  winner: string;
}

export interface DecisiveFactor {
  axis: string | null;
  axis_name: string | null;
  diff: number;
  winner: string | null;
  explanation: string;
}

export interface CompareResponse {
  outfit_a: OutfitBrief;
  outfit_b: OutfitBrief;
  axis_comparison: AxisComparison[];
  total_a: number;
  total_b: number;
  winner: string;
  decisive_factor: DecisiveFactor;
}

export async function fetchCompare(
  idA: string,
  idB: string,
  toneId?: string,
): Promise<CompareResponse> {
  const q = new URLSearchParams({ ids: `${idA},${idB}` });
  if (toneId) q.set("tone_id", toneId);
  const res = await fetch(`${API_BASE}/api/compare?${q.toString()}`);
  if (!res.ok) {
    throw new Error(`Compare API error: ${res.status}`);
  }
  return res.json();
}

/* ── 피드 ── */

export async function fetchFeed(params: FeedParams): Promise<FeedResponse> {
  const q = new URLSearchParams();
  q.set("tone_id", params.toneId);
  if (params.gender) q.set("gender", params.gender);
  if (params.ageGroup) q.set("age_group", params.ageGroup);
  if (params.tpo) q.set("tpo", params.tpo);
  if (params.budgetMin != null) q.set("budget_min", String(params.budgetMin));
  if (params.budgetMax != null) q.set("budget_max", String(params.budgetMax));
  if (params.userId) q.set("user_id", params.userId);
  if (params.verifiedOnly) q.set("verified_only", "true");
  if (params.preferredBrands?.length) q.set("preferred_brands", params.preferredBrands.join(","));
  if (params.page != null) q.set("page", String(params.page));

  const res = await fetch(`${API_BASE}/api/feed?${q.toString()}`);
  if (!res.ok) {
    throw new Error(`Feed API error: ${res.status}`);
  }
  return res.json();
}

/* ── 브랜드 ── */

export interface BrandGroupsResponse {
  groups: Record<string, string[]>;
}

export async function fetchBrandGroups(): Promise<BrandGroupsResponse> {
  const res = await fetch(`${API_BASE}/api/brands`);
  if (!res.ok) throw new Error(`Brands API error: ${res.status}`);
  return res.json();
}

export async function fetchPreferredBrands(userId: string): Promise<{ preferred_brands: string[] }> {
  const res = await fetch(`${API_BASE}/api/preference/${userId}/brands`);
  if (!res.ok) throw new Error(`Preferred brands API error: ${res.status}`);
  return res.json();
}

export async function savePreferredBrands(userId: string, brands: string[]): Promise<void> {
  const res = await fetch(`${API_BASE}/api/preference/${userId}/brands`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ brands }),
  });
  if (!res.ok) throw new Error(`Save brands API error: ${res.status}`);
}

export async function deleteClosetItem(userId: string, itemId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/api/closet/${itemId}?user_id=${userId}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error(`Delete closet item error: ${res.status}`);
}

/* ── 코디 완성 (옷장 매칭) ── */

export interface ClosetOutfitItem {
  id: string;
  source: string; // "closet" | "catalog"
  category: string | null;
  image_url: string | null;
  label: string | null; // "내 옷"
  name: string | null;
  brand: string | null;
  price: number | null;
  mall_url: string | null;
}

export interface PurchaseSummary {
  my_items_count: number;
  purchase_items_count: number;
  purchase_total: number;
}

export interface ClosetOutfit {
  id: string;
  source: string; // "db_match" | "dynamic_combo"
  db_outfit_id: string | null;
  total_score: number;
  scores: Record<string, number>;
  reasons: string[];
  items: ClosetOutfitItem[];
  purchase_summary: PurchaseSummary;
}

export interface ClosetOutfitResponse {
  outfits: ClosetOutfit[];
  total_count: number;
  strategy_used: string;
}

export async function fetchClosetOutfits(
  userId: string,
  closetItemId: string,
  tpo?: string,
  budgetMax?: number,
  limit: number = 10,
): Promise<ClosetOutfitResponse> {
  const body: Record<string, unknown> = {
    user_id: userId,
    closet_item_id: closetItemId,
    limit,
  };
  if (tpo) body.tpo = tpo;
  if (budgetMax != null) body.budget_max = budgetMax;

  const res = await fetch(`${API_BASE}/api/closet/outfits`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    throw new Error(`Closet outfits API error: ${res.status}`);
  }
  return res.json();
}

/* ── OAuth ── */

export interface AuthTokenResponse {
  access_token: string;
  token_type: string;
  user_id: string;
  is_new_user: boolean;
}

export async function postOAuthCallback(
  provider: "kakao" | "google",
  code: string,
  guestUserId?: string | null,
): Promise<AuthTokenResponse> {
  const body: Record<string, string> = { code };
  if (guestUserId) body.guest_user_id = guestUserId;

  const res = await fetch(`${API_BASE}/api/auth/${provider}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    throw new Error(`OAuth callback error: ${res.status}`);
  }
  return res.json();
}
