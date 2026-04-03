"""StyleFilter: 규칙 기반 사전 필터 (Hard Filter H8).

기획서 섹션 6.6 구현.
키워드 → LLM 캐시 → 기본값 3단계로 카테고리를 감지하고,
3축 가중합(카테고리 궁합 50% + 실루엣 밸런스 25% + 포멀도 일관성 25%)이
55점 미만이면 코디를 탈락시킨다.
"""

from __future__ import annotations

from app.services.category_classifier import (
    LlmClassificationCache,
    RAW_CATEGORY_MAP,
    classify_by_keyword,
    _CATEGORY_TO_GROUP,
)
from app.services.scoring import calculate_sf

STYLE_FILTER_THRESHOLD = 55.0

_llm_cache: LlmClassificationCache | None = None


def _get_llm_cache() -> LlmClassificationCache:
    global _llm_cache
    if _llm_cache is None:
        _llm_cache = LlmClassificationCache()
    return _llm_cache


def detect_category(
    title: str,
    category3: str | None = None,
    category4: str | None = None,
    product_id: str | None = None,
    cache: LlmClassificationCache | None = None,
) -> dict:
    """상품의 카테고리를 3단계 폴백으로 감지한다.

    1단계: 키워드 매칭 (~70%) — < 1ms
    2단계: LLM 분류 캐시 조회 (~27%) — < 1ms
    3단계: 미분류 폴백 — 기본값 적용

    Args:
        title: 상품명
        category3: 네이버 raw_category3
        category4: 네이버 raw_category4
        product_id: LLM 캐시 조회용 상품 ID
        cache: LLM 캐시 인스턴스 (None이면 글로벌 캐시 사용)

    Returns:
        {"category": str|None, "group": str, "silhouette": str|None,
         "formality": int|None, "source": str}
    """
    # 1단계: 키워드 매칭
    kw_result = classify_by_keyword(title, category3, category4)
    if kw_result:
        source = "keyword"
        if category3 or category4:
            for raw_cat in (category4, category3):
                if raw_cat and raw_cat in RAW_CATEGORY_MAP:
                    source = "raw_category"
                    break

        llm = cache or _get_llm_cache()
        cached_meta = llm.get(product_id) if product_id else None
        return {
            "category": kw_result["category"],
            "group": kw_result["group"],
            "silhouette": cached_meta.get("silhouette") if cached_meta else None,
            "formality": cached_meta.get("formality") if cached_meta else None,
            "source": source,
        }

    # 2단계: LLM 캐시 조회
    if product_id:
        llm = cache or _get_llm_cache()
        cached = llm.get(product_id)
        if cached and cached.get("category"):
            group = _CATEGORY_TO_GROUP.get(cached["category"], "")
            return {
                "category": cached["category"],
                "group": group,
                "silhouette": cached.get("silhouette"),
                "formality": cached.get("formality"),
                "source": "llm_cache",
            }

    # 3단계: 미분류 폴백
    return {
        "category": None,
        "group": "",
        "silhouette": None,
        "formality": None,
        "source": "unknown",
    }


def filter_outfit(items: list[dict]) -> tuple[bool, float]:
    """코디의 StyleFilter 점수를 계산하고 통과 여부를 판정한다.

    scoring.py의 calculate_sf를 호출하여 3축 가중합을 계산하고,
    55점 미만이면 탈락 (Hard Filter H8).

    Args:
        items: 코디 아이템 리스트. 각 아이템은 최소한 다음 필드를 가져야 한다:
            - category: str (세부 카테고리, e.g. "블라우스")
            - silhouette: str | None (e.g. "fitted", "oversized")
            - group: str | None (대카테고리, e.g. "top", "bottom")

    Returns:
        (passed: bool, score: float) — 통과 여부와 점수
    """
    if not items:
        return False, 0.0

    categories = [item["category"] for item in items if item.get("category")]
    if not categories:
        return True, STYLE_FILTER_THRESHOLD

    # 상의/하의 실루엣 추출
    top_silhouette = None
    bottom_silhouette = None
    for item in items:
        group = item.get("group", "")
        sil = item.get("silhouette")
        if not sil:
            continue
        if group in ("top", "outer") and top_silhouette is None:
            top_silhouette = sil
        elif group in ("bottom",) and bottom_silhouette is None:
            bottom_silhouette = sil

    score = calculate_sf(categories, top_silhouette, bottom_silhouette)
    return score >= STYLE_FILTER_THRESHOLD, score
