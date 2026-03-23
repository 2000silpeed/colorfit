export interface UserProfile {
  id: string;
  toneId: string;
  tpoList: string[];
  styleMoods: string[];
  budgetMin: number;
  budgetMax: number;
}

export interface OutfitCard {
  id: string;
  imageUrl: string;
  summary: string;
  totalPrice: number;
  lowestTotalPrice: number;
  scores: {
    personalColorFit: number;
    occasionFit: number;
    total: number;
  };
  reasons: string[];
  isCompleteOutfit: boolean;
  itemCount: number;
  isSaved: boolean;
}

export interface ProductDetail {
  id: string;
  name: string;
  brand: string;
  category: string;
  colorHex: string;
  toneId: string;
  price: number;
  mallName: string;
  mallUrl: string;
  imageUrl: string;
}

export interface PriceEntry {
  mallName: string;
  price: number;
  url: string;
  matchType: 'exact' | 'similar';
  similarity?: number;
}

export interface CompareResult {
  comparison: Record<string, { A: number; B: number }>;
  winner: 'A' | 'B';
  reason: string;
}
