const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

interface FeedParams {
  toneId: string;
  gender?: string;
  tpo?: string;
  budgetMin?: number;
  budgetMax?: number;
  userId?: string;
  page?: number;
}

export interface ScoresResponse {
  pcf: number;
  of: number;
  ch: number;
  pe: number;
  sf: number;
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
  items: ProductBrief[];
}

export async function fetchOutfitDetail(
  outfitId: string,
): Promise<OutfitDetailResponse> {
  const res = await fetch(`${API_BASE}/api/outfit/${outfitId}`);
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
): Promise<TryonGenerateResponse> {
  const body: Record<string, string> = {
    outfit_id: outfitId,
    user_id: userId,
  };
  if (closetItemId) body.closet_item_id = closetItemId;
  if (modelImageUrl) body.model_image_url = modelImageUrl;

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

/* ── 피드 ── */

export async function fetchFeed(params: FeedParams): Promise<FeedResponse> {
  const q = new URLSearchParams();
  q.set("tone_id", params.toneId);
  if (params.gender) q.set("gender", params.gender);
  if (params.tpo) q.set("tpo", params.tpo);
  if (params.budgetMin != null) q.set("budget_min", String(params.budgetMin));
  if (params.budgetMax != null) q.set("budget_max", String(params.budgetMax));
  if (params.userId) q.set("user_id", params.userId);
  if (params.page != null) q.set("page", String(params.page));

  const res = await fetch(`${API_BASE}/api/feed?${q.toString()}`);
  if (!res.ok) {
    throw new Error(`Feed API error: ${res.status}`);
  }
  return res.json();
}
