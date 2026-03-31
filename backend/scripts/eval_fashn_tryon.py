"""
Task 1.17 — Fashn.ai Virtual Try-On API 테스트
여름 웜톤 옷 3종(상의/하의/원피스)으로 "내 옷 정체성 유지" 품질 검증
"""
import os
import time
import requests
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

API_KEY = os.getenv("FASHN_API_KEY")
assert API_KEY, "FASHN_API_KEY가 .env에 설정되지 않았습니다."

BASE_URL = "https://api.fashn.ai/v1"
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}",
}

MODEL_IMAGE = (
    "https://v3.fal.media/files/panda/"
    "jRavCEb1D4OpZBjZKxaH7_image_2024-12-08_18-37-27%20Large.jpeg"
)

TEST_GARMENTS = [
    {
        "name": "tops_sample_tshirt",
        "category": "tops",
        "image": "https://v3.fal.media/files/elephant/qXMQpeM6fVOlg7bZs0dEh_fashn-tshirt-2.png",
        "description": "Fashn 샘플 티셔츠 (API 동작 확인용)",
    },
    {
        "name": "tops_warm_coral",
        "category": "tops",
        "image": "https://images.unsplash.com/photo-1562157873-818bc0726f68?w=600",
        "description": "행거 위 티셔츠 (상의 테스트)",
    },
    {
        "name": "bottoms_warm_khaki",
        "category": "bottoms",
        "image": "https://images.unsplash.com/photo-1594938298603-c8148c4dae35?w=600",
        "description": "팬츠 (하의 테스트)",
    },
]

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data" / "tryon_test"


def run_tryon(garment: dict) -> dict:
    print(f"\n{'='*50}")
    print(f"테스트: {garment['name']} — {garment['description']}")
    print(f"카테고리: {garment['category']}")
    print(f"{'='*50}")

    payload = {
        "model_name": "tryon-v1.6",
        "inputs": {
            "model_image": MODEL_IMAGE,
            "garment_image": garment["image"],
            "category": garment["category"],
            "mode": "balanced",
            "garment_photo_type": "flat-lay",
        },
    }

    resp = requests.post(f"{BASE_URL}/run", json=payload, headers=HEADERS)
    if resp.status_code != 200:
        print(f"  ERROR: {resp.status_code} — {resp.text}")
        return {"name": garment["name"], "status": "error", "error": resp.text}

    prediction_id = resp.json().get("id")
    print(f"  Prediction ID: {prediction_id}")

    start = time.time()
    while True:
        status_resp = requests.get(
            f"{BASE_URL}/status/{prediction_id}", headers=HEADERS
        )
        status_data = status_resp.json()
        status = status_data.get("status", "unknown")

        if status == "completed":
            elapsed = time.time() - start
            output_urls = status_data.get("output", [])
            print(f"  완료! ({elapsed:.1f}초)")
            print(f"  결과: {output_urls}")

            OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
            for i, url in enumerate(output_urls):
                img_resp = requests.get(url)
                if img_resp.status_code == 200:
                    fname = OUTPUT_DIR / f"{garment['name']}_{i}.png"
                    fname.write_bytes(img_resp.content)
                    print(f"  저장: {fname}")

            return {
                "name": garment["name"],
                "status": "completed",
                "elapsed_sec": round(elapsed, 1),
                "output_urls": output_urls,
            }

        elif status in ("starting", "in_queue", "processing"):
            elapsed = time.time() - start
            print(f"  상태: {status} ({elapsed:.0f}초 경과)")
            time.sleep(3)

        else:
            elapsed = time.time() - start
            error = status_data.get("error", "unknown")
            print(f"  실패: {status} — {error} ({elapsed:.1f}초)")
            return {
                "name": garment["name"],
                "status": status,
                "error": error,
                "elapsed_sec": round(elapsed, 1),
            }


def main():
    print("Fashn.ai Virtual Try-On API 테스트")
    print(f"모델 이미지: {MODEL_IMAGE}")
    print(f"테스트 의류: {len(TEST_GARMENTS)}종")

    results = []
    for garment in TEST_GARMENTS:
        result = run_tryon(garment)
        results.append(result)

    print(f"\n{'='*50}")
    print("테스트 결과 요약")
    print(f"{'='*50}")
    for r in results:
        status_icon = "✅" if r["status"] == "completed" else "❌"
        elapsed = r.get("elapsed_sec", "N/A")
        print(f"  {status_icon} {r['name']}: {r['status']} ({elapsed}초)")

    report_path = OUTPUT_DIR / "test_report.json"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(results, indent=2, ensure_ascii=False))
    print(f"\n리포트 저장: {report_path}")


if __name__ == "__main__":
    main()
