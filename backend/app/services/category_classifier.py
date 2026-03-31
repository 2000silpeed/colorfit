"""하이브리드 카테고리 분류: 키워드 매칭 + LLM 폴백.

기획서 5.4.1 구현. 키워드 매칭(~70%) → LLM 캐시(~27%) → 실시간 LLM(~3%).
분류 속성: category, silhouette, formality, tpo, gender.
"""

import json
import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
LLM_CACHE_PATH = DATA_DIR / "llm_cache.json"

# 7개 대카테고리 → 세부 카테고리 31종 × 키워드
# 우선순위가 높은 카테고리(복합 아이템)를 먼저 배치하여 오분류 방지
# 예: "셔츠 원피스" → 원피스가 먼저 매칭되도록
CATEGORY_KEYWORDS: dict[str, dict[str, list[str]]] = {
    "onepiece": {
        "원피스": ["원피스", "드레스", "점프수트", "롬퍼"],
    },
    "outer": {
        "코트": ["코트", "트렌치코트", "핸드메이드코트", "더플코트"],
        "패딩": ["패딩", "다운자켓", "다운점퍼", "패딩조끼", "경량패딩"],
        "자켓": ["자켓", "재킷", "블레이저", "수트자켓", "데님자켓", "라이더자켓", "봄버자켓"],
        "가디건": ["가디건", "카디건"],
        "점퍼": ["점퍼", "바람막이", "윈드브레이커", "아노락", "집업"],
        "조끼": ["조끼", "베스트", "질레"],
    },
    "top": {
        "니트": ["니트", "스웨터", "풀오버", "터틀넥", "목폴라", "캐시미어"],
        "셔츠": ["셔츠", "남방"],
        "블라우스": ["블라우스"],
        "티셔츠": ["티셔츠", "반팔티", "반팔", "롱슬리브"],
        "맨투맨": ["맨투맨", "스웨트셔츠", "크루넥"],
        "후드": ["후드", "후디", "후드티"],
        "크롭탑": ["크롭탑", "크롭", "브라탑", "브라렛"],
        "탱크탑": ["탱크탑", "슬리브리스", "나시"],
        "폴로": ["폴로", "카라티"],
    },
    "bottom": {
        "슬랙스": ["슬랙스", "드레스팬츠", "테일러드팬츠", "정장바지"],
        "청바지": ["청바지", "데님팬츠", "진"],
        "스커트": ["스커트", "치마", "미니스커트", "롱스커트", "플리츠스커트"],
        "와이드팬츠": ["와이드팬츠", "와이드"],
        "조거팬츠": ["조거팬츠", "조거", "트레이닝팬츠"],
        "숏팬츠": ["숏팬츠", "반바지", "숏츠", "버뮤다"],
        "레깅스": ["레깅스", "레깅스팬츠", "요가팬츠"],
        "치노": ["치노", "치노팬츠", "면바지"],
    },
    "shoes": {
        "스니커즈": ["스니커즈", "운동화", "러닝화"],
        "로퍼": ["로퍼", "페니로퍼"],
        "힐": ["힐", "하이힐", "펌프스", "뮬"],
        "부츠": ["부츠", "앵클부츠", "첼시부츠", "워커"],
        "샌들": ["샌들", "슬리퍼", "플리플랍"],
        "더비": ["더비", "옥스퍼드", "구두"],
    },
    "bag": {
        "가방": ["가방", "백팩", "토트백", "크로스백", "숄더백", "클러치", "메신저백", "에코백"],
    },
    "acc": {
        "액세서리": ["모자", "벨트", "스카프", "머플러", "장갑", "양말", "선글라스", "시계", "주얼리", "목걸이", "귀걸이", "반지", "팔찌"],
    },
}

# 네이버 raw_category3/4 → 우리 카테고리 매핑
RAW_CATEGORY_MAP: dict[str, str] = {
    "니트": "니트", "카디건": "가디건", "스웨터": "니트",
    "셔츠": "셔츠", "블라우스": "블라우스",
    "티셔츠": "티셔츠", "반팔티셔츠": "티셔츠", "긴팔티셔츠": "티셔츠",
    "맨투맨": "맨투맨", "후드티셔츠": "후드",
    "원피스": "원피스", "미니원피스": "원피스", "롱원피스": "원피스",
    "코트": "코트", "자켓": "자켓", "점퍼": "점퍼", "패딩": "패딩",
    "청바지": "청바지", "데님팬츠": "청바지",
    "슬랙스": "슬랙스", "면바지": "치노",
    "스커트": "스커트", "미니스커트": "스커트", "롱스커트": "스커트",
    "레깅스": "레깅스", "조거팬츠": "조거팬츠",
    "운동화": "스니커즈", "스니커즈": "스니커즈",
    "구두": "더비", "로퍼": "로퍼", "부츠": "부츠",
    "샌들": "샌들", "슬리퍼": "샌들",
    "힐": "힐", "펌프스": "힐",
}

# 카테고리 → 대카테고리 역매핑 (빌드 타임에 생성)
_CATEGORY_TO_GROUP: dict[str, str] = {}
for group, categories in CATEGORY_KEYWORDS.items():
    for cat in categories:
        _CATEGORY_TO_GROUP[cat] = group

# 키워드 → (카테고리, 대카테고리) 인덱스 (긴 키워드 우선 매칭)
_KEYWORD_INDEX: list[tuple[str, str, str]] = []
for group, categories in CATEGORY_KEYWORDS.items():
    for cat, keywords in categories.items():
        for kw in keywords:
            _KEYWORD_INDEX.append((kw, cat, group))
_KEYWORD_INDEX.sort(key=lambda x: len(x[0]), reverse=True)


def classify_by_keyword(
    name: str,
    raw_category3: str | None = None,
    raw_category4: str | None = None,
) -> dict[str, str | None] | None:
    """키워드 기반 1단계 분류.

    Returns:
        {"category": str, "group": str} 또는 매칭 실패 시 None.
    """
    # 1) 네이버 raw_category 힌트 먼저 시도
    for raw_cat in (raw_category4, raw_category3):
        if raw_cat and raw_cat in RAW_CATEGORY_MAP:
            cat = RAW_CATEGORY_MAP[raw_cat]
            return {"category": cat, "group": _CATEGORY_TO_GROUP[cat]}

    # 2) 상품명 키워드 매칭 (긴 키워드 우선)
    name_lower = name.lower().replace(" ", "")
    for kw, cat, group in _KEYWORD_INDEX:
        if kw in name_lower:
            return {"category": cat, "group": group}

    return None


class LlmClassificationCache:
    """LLM 분류 결과 JSON 캐시."""

    def __init__(self, cache_path: Path = LLM_CACHE_PATH) -> None:
        self.cache_path = cache_path
        self._cache: dict[str, dict] = {}
        self._load()

    def _load(self) -> None:
        if self.cache_path.exists():
            with open(self.cache_path, encoding="utf-8") as f:
                self._cache = json.load(f)
            logger.info("LLM 캐시 로드: %d건", len(self._cache))
        else:
            self._cache = {}

    def get(self, product_id: str) -> dict | None:
        return self._cache.get(product_id)

    def put(self, product_id: str, result: dict) -> None:
        self._cache[product_id] = result

    def put_batch(self, results: dict[str, dict]) -> None:
        self._cache.update(results)

    def save(self) -> None:
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.cache_path, "w", encoding="utf-8") as f:
            json.dump(self._cache, f, ensure_ascii=False, indent=2)
        logger.info("LLM 캐시 저장: %d건", len(self._cache))

    def __len__(self) -> int:
        return len(self._cache)


# Gemini 분류 프롬프트
GEMINI_CLASSIFY_PROMPT = """다음 패션 상품들을 분류해주세요. 각 상품에 대해 JSON 객체로 응답하세요.

분류 속성:
- category: {categories} 중 하나
- silhouette: oversized, slim, fitted, wide, regular 중 하나
- formality: 1~5 정수 (1=매우 캐주얼, 5=매우 포멀)
- tpo: [{tpo_list}] 중 해당하는 것 모두 (배열)
- gender: female, male, unisex 중 하나

상품 목록:
{items}

JSON 배열로만 응답하세요. 다른 텍스트 없이:
[{{"product_id": "...", "category": "...", "silhouette": "...", "formality": N, "tpo": [...], "gender": "..."}}]"""

VALID_CATEGORIES = sorted({cat for cats in CATEGORY_KEYWORDS.values() for cat in cats})
VALID_TPO = [
    "office", "interview", "commute", "date", "wedding",
    "weekend", "campus", "travel", "event", "workout", "casual",
]
VALID_SILHOUETTES = ["oversized", "slim", "fitted", "wide", "regular"]
VALID_GENDERS = ["female", "male", "unisex"]


def _build_gemini_prompt(items: list[dict]) -> str:
    item_lines = []
    for item in items:
        item_lines.append(
            f"- product_id: {item['product_id']}, "
            f"name: {item['name']}, "
            f"raw_category: {item.get('raw_category3', '')}/{item.get('raw_category4', '')}"
        )
    return GEMINI_CLASSIFY_PROMPT.format(
        categories=", ".join(VALID_CATEGORIES),
        tpo_list=", ".join(VALID_TPO),
        items="\n".join(item_lines),
    )


def _parse_gemini_response(response_text: str) -> list[dict]:
    """Gemini 응답에서 JSON 배열을 파싱한다."""
    # ```json ... ``` 블록 추출
    match = re.search(r"\[.*\]", response_text, re.DOTALL)
    if not match:
        logger.warning("Gemini 응답에서 JSON 배열을 찾을 수 없음")
        return []

    try:
        results = json.loads(match.group())
    except json.JSONDecodeError:
        logger.warning("Gemini 응답 JSON 파싱 실패")
        return []

    validated = []
    for r in results:
        if not isinstance(r, dict) or "product_id" not in r:
            continue
        # 유효성 검증
        if r.get("category") not in VALID_CATEGORIES:
            r["category"] = None
        if r.get("silhouette") not in VALID_SILHOUETTES:
            r["silhouette"] = "regular"
        formality = r.get("formality")
        if not isinstance(formality, int) or not 1 <= formality <= 5:
            r["formality"] = 3
        if not isinstance(r.get("tpo"), list):
            r["tpo"] = ["casual"]
        else:
            r["tpo"] = [t for t in r["tpo"] if t in VALID_TPO] or ["casual"]
        if r.get("gender") not in VALID_GENDERS:
            r["gender"] = "unisex"
        validated.append(r)

    return validated


async def classify_batch_with_gemini(
    items: list[dict],
    gemini_api_key: str,
    batch_size: int = 20,
) -> dict[str, dict]:
    """Gemini Flash로 배치 분류.

    Args:
        items: [{"product_id", "name", "raw_category3", "raw_category4"}, ...]
        gemini_api_key: Gemini API 키
        batch_size: 1회 요청당 아이템 수

    Returns:
        {product_id: {"category", "silhouette", "formality", "tpo", "gender"}}
    """
    import google.generativeai as genai

    genai.configure(api_key=gemini_api_key)
    model = genai.GenerativeModel("gemini-2.0-flash")

    all_results: dict[str, dict] = {}

    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        prompt = _build_gemini_prompt(batch)

        try:
            response = await model.generate_content_async(prompt)
            parsed = _parse_gemini_response(response.text)
            for r in parsed:
                pid = r.pop("product_id")
                all_results[pid] = r
        except Exception as e:
            logger.error("Gemini 배치 분류 실패 (batch %d): %s", i // batch_size, e)

    return all_results


def classify_product(
    product: dict,
    cache: LlmClassificationCache | None = None,
) -> dict:
    """단일 상품 하이브리드 분류.

    Returns:
        {"category", "group", "silhouette", "formality", "tpo", "gender", "source"}
        source: "keyword" | "raw_category" | "llm_cache" | "unknown"
    """
    name = product.get("name", "")
    product_id = product.get("product_id", "")

    # 1단계: 키워드 매칭
    kw_result = classify_by_keyword(
        name,
        product.get("raw_category3"),
        product.get("raw_category4"),
    )
    if kw_result:
        source = "keyword"
        if product.get("raw_category3") or product.get("raw_category4"):
            for raw_cat in (product.get("raw_category4"), product.get("raw_category3")):
                if raw_cat and raw_cat in RAW_CATEGORY_MAP:
                    source = "raw_category"
                    break
        # LLM 캐시에서 메타데이터 보충 (category는 키워드 결과 유지)
        cached_meta = cache.get(product_id) if cache and product_id else None
        return {
            "category": kw_result["category"],
            "group": kw_result["group"],
            "silhouette": cached_meta.get("silhouette") if cached_meta else None,
            "formality": cached_meta.get("formality") if cached_meta else None,
            "tpo": cached_meta.get("tpo") if cached_meta else None,
            "gender": cached_meta.get("gender") if cached_meta else None,
            "source": source,
        }

    # 2단계: LLM 캐시 조회
    if cache and product_id:
        cached = cache.get(product_id)
        if cached:
            group = _CATEGORY_TO_GROUP.get(cached.get("category", ""), "")
            return {
                "category": cached.get("category"),
                "group": group,
                "silhouette": cached.get("silhouette"),
                "formality": cached.get("formality"),
                "tpo": cached.get("tpo"),
                "gender": cached.get("gender"),
                "source": "llm_cache",
            }

    # 3단계: 미분류
    return {
        "category": None,
        "group": "",
        "silhouette": None,
        "formality": None,
        "tpo": None,
        "gender": None,
        "source": "unknown",
    }
