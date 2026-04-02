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
