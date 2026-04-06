from __future__ import annotations

from pydantic import BaseModel, HttpUrl, field_validator, model_validator


class ClosetAnalyzeRequest(BaseModel):
    image_url: HttpUrl
    user_tone_id: str

    @field_validator("image_url")
    @classmethod
    def must_be_https_or_local(cls, v: HttpUrl) -> HttpUrl:
        url = str(v)
        if url.startswith("http://") and "localhost" not in url and "127.0.0.1" not in url:
            raise ValueError("https URL만 허용됩니다 (localhost 예외)")
        return v


class ColorDetail(BaseModel):
    hex: str
    ratio: float


class ClosetAnalyzeResponse(BaseModel):
    dominant_colors: list[ColorDetail]
    matched_tone_id: str
    matched_tone_name: str
    pcf_score: float
    saturation_score: float
    lightness_score: float
    overall_score: float
    reasons: list[str]


class ClosetItemAddRequest(BaseModel):
    user_id: str
    image_url: HttpUrl
    category: str | None = None
    dominant_color_hex: str | None = None
    matched_tone_id: str | None = None
    pcf_score: float | None = None
    overall_score: float | None = None
    reasons: list[str] | None = None

    @field_validator("image_url")
    @classmethod
    def must_be_https_or_local(cls, v: HttpUrl) -> HttpUrl:
        url = str(v)
        if url.startswith("http://") and "localhost" not in url and "127.0.0.1" not in url:
            raise ValueError("https URL만 허용됩니다 (localhost 예외)")
        return v


class ClosetItemAddResponse(BaseModel):
    id: str
    message: str


class ClosetItemResponse(BaseModel):
    id: str
    image_url: str
    category: str | None = None
    dominant_color_hex: str | None = None
    matched_tone_id: str | None = None
    pcf_score: float | None = None
    overall_score: float | None = None
    reasons: list[str] | None = None
    created_at: str | None = None


class ClosetStats(BaseModel):
    total_count: int
    average_pcf: float
    good_count: int
    good_ratio: float


class ClosetListResponse(BaseModel):
    items: list[ClosetItemResponse]
    stats: ClosetStats


# --- Task 6.3: 코디 매칭 API 스키마 ---


class ClosetOutfitRequest(BaseModel):
    user_id: str
    closet_item_id: str | None = None
    closet_item_ids: list[str] | None = None
    tpo: str | None = None
    budget_max: int | None = None
    limit: int = 10

    @model_validator(mode="after")
    def check_item_id_exclusive(self) -> ClosetOutfitRequest:
        if self.closet_item_id and self.closet_item_ids:
            raise ValueError("closet_item_id와 closet_item_ids를 동시에 지정할 수 없습니다")
        if not self.closet_item_id and not self.closet_item_ids:
            raise ValueError("closet_item_id 또는 closet_item_ids 중 하나는 필수입니다")
        return self

    @field_validator("limit")
    @classmethod
    def limit_range(cls, v: int) -> int:
        if v < 1 or v > 20:
            raise ValueError("limit은 1~20 범위여야 합니다")
        return v


class ClosetOutfitItem(BaseModel):
    id: str
    source: str  # "closet" | "catalog"
    category: str | None = None
    image_url: str | None = None
    label: str | None = None  # "내 옷" (closet only)
    name: str | None = None
    brand: str | None = None
    price: int | None = None
    mall_url: str | None = None


class PurchaseSummary(BaseModel):
    my_items_count: int
    purchase_items_count: int
    purchase_total: int


class ClosetOutfit(BaseModel):
    id: str
    source: str  # "db_match" | "dynamic_combo"
    db_outfit_id: str | None = None
    total_score: float
    scores: dict[str, float]
    reasons: list[str]
    items: list[ClosetOutfitItem]
    purchase_summary: PurchaseSummary


class ClosetOutfitResponse(BaseModel):
    outfits: list[ClosetOutfit]
    total_count: int
    strategy_used: str
