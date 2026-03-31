"""
Task 1.17 — Gemini 나노바나나 Virtual Try-On 테스트
멀티 아이템(상의+하의) 코디 착장 이미지 생성 검증
"""
import os
import io
import time
import requests
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

API_KEY = os.getenv("GEMINI_API_KEY")
assert API_KEY, "GEMINI_API_KEY가 .env에 설정되지 않았습니다."

client = genai.Client(api_key=API_KEY)

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data" / "tryon_test"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

MODEL_IMAGE_URL = (
    "https://v3.fal.media/files/panda/"
    "jRavCEb1D4OpZBjZKxaH7_image_2024-12-08_18-37-27%20Large.jpeg"
)

TOP_IMAGE_URL = (
    "https://v3.fal.media/files/elephant/"
    "qXMQpeM6fVOlg7bZs0dEh_fashn-tshirt-2.png"
)

BOTTOM_IMAGE_URL = (
    "https://images.unsplash.com/photo-1594938298603-c8148c4dae35?w=600"
)


def download_image(url: str) -> bytes:
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return resp.content


def test_single_garment():
    """테스트 1: 단일 아이템 — 상의만 착용"""
    print("\n" + "=" * 50)
    print("테스트 1: 단일 아이템 (상의)")
    print("=" * 50)

    model_bytes = download_image(MODEL_IMAGE_URL)
    top_bytes = download_image(TOP_IMAGE_URL)

    prompt = (
        "You are a fashion virtual try-on expert. "
        "The first image is a person (model). The second image is a top garment. "
        "Generate a photorealistic image of the person wearing this top. "
        "Preserve the garment's exact color, pattern, texture, and design details. "
        "Keep the person's face, hair, pose, and background unchanged. "
        "Output only the image."
    )

    start = time.time()
    response = client.models.generate_content(
        model="gemini-2.5-flash-image",
        contents=[
            prompt,
            types.Part.from_bytes(data=model_bytes, mime_type="image/jpeg"),
            types.Part.from_bytes(data=top_bytes, mime_type="image/png"),
        ],
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE", "TEXT"],
        ),
    )
    elapsed = time.time() - start

    return save_result(response, "gemini_single_top", elapsed)


def test_multi_garment():
    """테스트 2: 멀티 아이템 — 상의 + 하의 동시 착용"""
    print("\n" + "=" * 50)
    print("테스트 2: 멀티 아이템 (상의 + 하의)")
    print("=" * 50)

    model_bytes = download_image(MODEL_IMAGE_URL)
    top_bytes = download_image(TOP_IMAGE_URL)
    bottom_bytes = download_image(BOTTOM_IMAGE_URL)

    prompt = (
        "You are a fashion virtual try-on expert. "
        "The first image is a person (model). "
        "The second image is a top garment. "
        "The third image is a bottom garment (pants). "
        "Generate a photorealistic full-body image of the person wearing BOTH "
        "the top from image 2 AND the pants from image 3 as a complete outfit. "
        "Preserve each garment's exact color, pattern, texture, and design details. "
        "Keep the person's face, hair, and background unchanged. "
        "Output only the image."
    )

    start = time.time()
    response = client.models.generate_content(
        model="gemini-2.5-flash-image",
        contents=[
            prompt,
            types.Part.from_bytes(data=model_bytes, mime_type="image/jpeg"),
            types.Part.from_bytes(data=top_bytes, mime_type="image/png"),
            types.Part.from_bytes(data=bottom_bytes, mime_type="image/jpeg"),
        ],
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE", "TEXT"],
        ),
    )
    elapsed = time.time() - start

    return save_result(response, "gemini_multi_outfit", elapsed)


def test_warm_tone_styling():
    """테스트 3: 여름 웜톤 코디 — 프롬프트로 톤 지정"""
    print("\n" + "=" * 50)
    print("테스트 3: 여름 웜톤 스타일링 (프롬프트 기반)")
    print("=" * 50)

    model_bytes = download_image(MODEL_IMAGE_URL)
    top_bytes = download_image(TOP_IMAGE_URL)

    prompt = (
        "You are a personal color styling expert specializing in Warm Spring tones. "
        "The first image is a person (model). The second image is a garment. "
        "Generate a photorealistic image of the person wearing this garment, "
        "styled in a warm spring color palette. "
        "Add warm-toned accessories (gold jewelry, warm beige bag) that complement "
        "the outfit for a Warm Spring personal color type. "
        "Keep the person's face and hair unchanged. "
        "Output only the image."
    )

    start = time.time()
    response = client.models.generate_content(
        model="gemini-2.5-flash-image",
        contents=[
            prompt,
            types.Part.from_bytes(data=model_bytes, mime_type="image/jpeg"),
            types.Part.from_bytes(data=top_bytes, mime_type="image/png"),
        ],
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE", "TEXT"],
        ),
    )
    elapsed = time.time() - start

    return save_result(response, "gemini_warm_styling", elapsed)


def save_result(response, name: str, elapsed: float) -> dict:
    saved = False
    text_response = ""

    if response.candidates:
        for part in response.candidates[0].content.parts:
            if part.inline_data and part.inline_data.mime_type.startswith("image/"):
                ext = part.inline_data.mime_type.split("/")[1]
                fname = OUTPUT_DIR / f"{name}.{ext}"
                fname.write_bytes(part.inline_data.data)
                print(f"  저장: {fname}")
                saved = True
            elif part.text:
                text_response = part.text

    if text_response:
        print(f"  AI 응답: {text_response[:200]}")

    status = "completed" if saved else "no_image"
    print(f"  상태: {status} ({elapsed:.1f}초)")

    return {"name": name, "status": status, "elapsed_sec": round(elapsed, 1)}


def main():
    print("Gemini 나노바나나 Virtual Try-On 테스트")
    print(f"모델: gemini-2.5-flash-preview-05-20")

    results = []

    results.append(test_single_garment())
    results.append(test_multi_garment())
    results.append(test_warm_tone_styling())

    print(f"\n{'=' * 50}")
    print("테스트 결과 요약")
    print(f"{'=' * 50}")
    for r in results:
        icon = "✅" if r["status"] == "completed" else "❌"
        print(f"  {icon} {r['name']}: {r['status']} ({r['elapsed_sec']}초)")


if __name__ == "__main__":
    main()
