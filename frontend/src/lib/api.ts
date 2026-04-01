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
