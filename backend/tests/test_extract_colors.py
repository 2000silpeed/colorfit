"""extract_colors 스크립트 테스트."""

import json
from unittest.mock import patch, MagicMock

import pytest

from scripts.extract_colors import process_tone, get_available_tones
from app.services.color_matcher import TonePalette


@pytest.fixture
def mock_palette(tmp_path, monkeypatch):
    """테스트용 미니 팔레트."""
    monkeypatch.setattr(TonePalette, "EXPECTED_TONES", {"spring_warm_light"})
    tone = {
        "tone_id": "spring_warm_light",
        "colors": [
            {"hex": "#FADADD", "rgb": [250, 218, 221], "hsl": [354, 76, 92], "name_ko": "핑크"},
        ],
    }
    path = tmp_path / "spring_warm_light.json"
    with open(path, "w") as f:
        json.dump(tone, f)
    return TonePalette(palettes_dir=tmp_path)


@pytest.fixture
def normalized_file(tmp_path):
    """테스트용 normalized JSON 파일."""
    data = {
        "tone_id": "spring_warm_light",
        "item_count": 3,
        "items": [
            {
                "product_id": "1",
                "name": "핑크 블라우스",
                "color_hex": None,
                "tone_id": "spring_warm_light",
                "image_url": "https://example.com/img1.jpg",
            },
            {
                "product_id": "2",
                "name": "이미 처리된 상품",
                "color_hex": "#FF0000",
                "tone_id": "spring_warm_light",
                "image_url": "https://example.com/img2.jpg",
            },
            {
                "product_id": "3",
                "name": "이미지 없는 상품",
                "color_hex": None,
                "tone_id": "spring_warm_light",
                "image_url": "",
            },
        ],
    }
    return data


class TestProcessTone:
    @patch("scripts.extract_colors.NORMALIZED_DIR")
    @patch("scripts.extract_colors.extract_colors_from_url")
    def test_process_with_mixed_items(
        self, mock_extract, mock_dir, tmp_path, mock_palette, normalized_file
    ):
        mock_dir.__truediv__ = lambda self, name: tmp_path / name
        filepath = tmp_path / "spring_warm_light.json"
        with open(filepath, "w") as f:
            json.dump(normalized_file, f)

        mock_extract.return_value = ["#FADADD", "#FFE4C4", "#FFDAB9"]

        client = MagicMock()
        stats = process_tone("spring_warm_light", mock_palette, client, dry_run=True)

        assert stats["processed"] == 1   # product_id "1"
        assert stats["skipped"] == 1     # product_id "2" (이미 color_hex 있음)
        assert stats["failed"] == 1      # product_id "3" (image_url 없음)

    @patch("scripts.extract_colors.NORMALIZED_DIR")
    @patch("scripts.extract_colors.extract_colors_from_url")
    def test_saves_when_not_dry_run(
        self, mock_extract, mock_dir, tmp_path, mock_palette, normalized_file
    ):
        mock_dir.__truediv__ = lambda self, name: tmp_path / name
        filepath = tmp_path / "spring_warm_light.json"
        with open(filepath, "w") as f:
            json.dump(normalized_file, f)

        mock_extract.return_value = ["#FADADD"]

        client = MagicMock()
        process_tone("spring_warm_light", mock_palette, client, dry_run=False)

        with open(filepath) as f:
            saved = json.load(f)

        assert "color_extracted_at" in saved
        assert saved["color_stats"]["processed"] == 1

    @patch("scripts.extract_colors.NORMALIZED_DIR")
    @patch("scripts.extract_colors.extract_colors_from_url")
    def test_extraction_failure_counted(
        self, mock_extract, mock_dir, tmp_path, mock_palette, normalized_file
    ):
        mock_dir.__truediv__ = lambda self, name: tmp_path / name
        normalized_file["items"] = [normalized_file["items"][0]]  # URL 있는 것만
        filepath = tmp_path / "spring_warm_light.json"
        with open(filepath, "w") as f:
            json.dump(normalized_file, f)

        mock_extract.return_value = []  # 추출 실패

        client = MagicMock()
        stats = process_tone("spring_warm_light", mock_palette, client, dry_run=True)

        assert stats["failed"] == 1
        assert stats["processed"] == 0

    @patch("scripts.extract_colors.NORMALIZED_DIR")
    def test_missing_file(self, mock_dir, tmp_path, mock_palette):
        mock_dir.__truediv__ = lambda self, name: tmp_path / name
        client = MagicMock()
        stats = process_tone("nonexistent_tone", mock_palette, client)
        assert stats == {"processed": 0, "skipped": 0, "failed": 0}
