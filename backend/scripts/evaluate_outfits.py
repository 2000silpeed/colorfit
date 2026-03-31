"""Task 1.11 — Gemini Flash 배치 코디 품질 평가.

generated_outfits.json의 각 코디를 Gemini Flash로 5점 척도 평가.
3점 미만 코디를 제거하고 llm_quality_score 필드에 점수를 저장한다.
비용 추산: ~$6 (1,900개 x ~$0.003/req)
"""

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
INPUT_PATH = DATA_DIR / "generated_outfits.json"
OUTPUT_PATH = DATA_DIR / "generated_outfits.json"

API_KEY = os.getenv("GEMINI_API_KEY")
MODEL = "gemini-2.5-flash"

EVAL_PROMPT_TEMPLATE = """패션 코디 카테고리 조합을 평가해주세요.

중요: 상품명은 무시하고 [카테고리]만 보고 평가하세요. 상품명에 다른 계절이나 이상한 단어가 있어도 무관합니다.

## 점수 기준
- 5점: 해당 TPO/계절에 완벽한 카테고리 구성
- 4점: 좋은 구성. 사소한 아쉬움 1개
- 3점: 무난함. 기본적으로 입을 수 있는 조합
- 2점: 카테고리 조합이 TPO/계절에 안 맞음
- 1점: 입을 수 없는 조합

## 코디
- {gender}, {tpo}, {season}, 무드: {moods}
{items_text}

JSON만: {{"score": <1~5>, "reason": "<한줄>"}}"""


def format_items_text(items_snapshot: list[dict]) -> str:
    lines = []
    for item in items_snapshot:
        price_str = f"{item.get('price', 0):,}원" if item.get("price") else "가격 미상"
        lines.append(
            f"  - [{item['category']}] {item['name']} ({price_str}, 포멀도 {item.get('formality', '?')})"
        )
    return "\n".join(lines)


SEASON_KR = {"spring": "봄", "summer": "여름", "fall": "가을", "winter": "겨울"}


def build_prompt(outfit: dict) -> str:
    season = outfit.get("designed_season", "")
    return EVAL_PROMPT_TEMPLATE.format(
        gender="여성" if outfit["gender"] == "female" else "남성",
        tpo=outfit["designed_tpo"],
        season=SEASON_KR.get(season, season),
        moods=", ".join(outfit.get("designed_moods", [])),
        items_text=format_items_text(outfit.get("items_snapshot", [])),
    )


def parse_score(text: str) -> tuple[int | None, str]:
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`").strip()
        if text.startswith("json"):
            text = text[4:].strip()
    try:
        data = json.loads(text)
        score = int(data["score"])
        reason = data.get("reason", "")
        if 1 <= score <= 5:
            return score, reason
    except (json.JSONDecodeError, KeyError, ValueError, TypeError):
        pass

    import re
    match = re.search(r'"score"\s*:\s*(\d)', text)
    if match:
        score = int(match.group(1))
        if 1 <= score <= 5:
            return score, ""
    return None, ""


def evaluate_batch(
    client: genai.Client,
    outfits: list[dict],
    batch_size: int = 10,
    delay: float = 0.5,
) -> list[dict]:
    """코디 목록을 Gemini Flash로 평가한다."""
    total = len(outfits)
    evaluated = 0
    failed = 0

    for i, outfit in enumerate(outfits):
        if outfit.get("llm_quality_score") is not None:
            evaluated += 1
            continue

        prompt = build_prompt(outfit)

        try:
            response = client.models.generate_content(
                model=MODEL,
                contents=[prompt],
                config=types.GenerateContentConfig(
                    temperature=0.1,
                    max_output_tokens=1024,
                ),
            )
            text = response.text or ""
            score, reason = parse_score(text)

            if score is not None:
                outfit["llm_quality_score"] = score
                outfit["llm_eval_reason"] = reason
                evaluated += 1
            else:
                logger.warning("[%d/%d] %s: 파싱 실패 — %s", i + 1, total, outfit["id"], text[:100])
                failed += 1

        except Exception as e:
            logger.error("[%d/%d] %s: API 에러 — %s", i + 1, total, outfit["id"], str(e)[:100])
            failed += 1
            time.sleep(2)

        if (i + 1) % batch_size == 0:
            logger.info("[%d/%d] 진행 중 (평가 %d, 실패 %d)", i + 1, total, evaluated, failed)
            time.sleep(delay)

    return outfits


def filter_low_quality(outfits: list[dict], min_score: int = 3) -> tuple[list[dict], list[dict]]:
    """min_score 미만 코디를 분리한다."""
    passed = []
    removed = []
    for outfit in outfits:
        score = outfit.get("llm_quality_score")
        if score is not None and score < min_score:
            removed.append(outfit)
        else:
            passed.append(outfit)
    return passed, removed


def main():
    parser = argparse.ArgumentParser(description="Gemini Flash 코디 품질 평가")
    parser.add_argument("--input", type=str, default=str(INPUT_PATH))
    parser.add_argument("--output", type=str, default=str(OUTPUT_PATH))
    parser.add_argument("--min-score", type=int, default=3, help="최소 품질 점수 (기본 3)")
    parser.add_argument("--batch-size", type=int, default=10, help="배치 로그 단위")
    parser.add_argument("--delay", type=float, default=0.5, help="배치 간 딜레이(초)")
    parser.add_argument("--limit", type=int, default=0, help="평가할 코디 수 제한 (0=전체)")
    parser.add_argument("--dry-run", action="store_true", help="평가만 하고 파일 저장 안 함")
    parser.add_argument("--resume", action="store_true", help="이미 평가된 코디는 건너뛰기")
    args = parser.parse_args()

    assert API_KEY, "GEMINI_API_KEY가 .env에 설정되지 않았습니다."
    client = genai.Client(api_key=API_KEY)

    input_path = Path(args.input)
    if not input_path.exists():
        logger.error("입력 파일 없음: %s", input_path)
        logger.error("먼저 generate_outfits.py를 실행하세요.")
        sys.exit(1)

    with open(input_path, encoding="utf-8") as f:
        data = json.load(f)

    outfits = data["outfits"]
    logger.info("입력: %d개 코디", len(outfits))

    if not args.resume:
        for o in outfits:
            o["llm_quality_score"] = None
            o["llm_eval_reason"] = None

    if args.limit > 0:
        target = [o for o in outfits if o.get("llm_quality_score") is None][:args.limit]
        rest = [o for o in outfits if o not in target]
        evaluate_batch(client, target, args.batch_size, args.delay)
        outfits = target + rest
    else:
        evaluate_batch(client, outfits, args.batch_size, args.delay)

    scored = [o for o in outfits if o.get("llm_quality_score") is not None]
    unscored = [o for o in outfits if o.get("llm_quality_score") is None]

    if scored:
        scores = [o["llm_quality_score"] for o in scored]
        avg = sum(scores) / len(scores)
        dist = {s: scores.count(s) for s in range(1, 6)}
        logger.info("평가 완료: %d개, 미평가: %d개", len(scored), len(unscored))
        logger.info("평균 점수: %.2f", avg)
        logger.info("점수 분포: %s", dist)

    passed, removed = filter_low_quality(outfits, args.min_score)
    logger.info("통과: %d개, 제거: %d개 (<%d점)", len(passed), len(removed), args.min_score)

    if not args.dry_run:
        output_path = Path(args.output)
        output_data = {
            "version": data.get("version", "1.0"),
            "generated_at": data.get("generated_at"),
            "evaluated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "total_count": len(passed),
            "removed_count": len(removed),
            "outfits": passed,
        }
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        logger.info("저장: %s (%d개)", output_path, len(passed))

        if removed:
            removed_path = output_path.parent / "removed_outfits.json"
            with open(removed_path, "w", encoding="utf-8") as f:
                json.dump({"count": len(removed), "outfits": removed}, f, ensure_ascii=False, indent=2)
            logger.info("제거된 코디 저장: %s (%d개)", removed_path, len(removed))
    else:
        logger.info("[DRY-RUN] 파일 저장 건너뜀")


if __name__ == "__main__":
    main()
