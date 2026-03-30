"""color_extractor 서비스 테스트."""

import numpy as np
import pytest
from PIL import Image

from app.services.color_extractor import (
    extract_colors_from_image,
    _remove_background,
    _resize_for_clustering,
)


class TestResizeForClustering:
    def test_large_image_resized(self):
        img = Image.new("RGB", (1000, 800), color=(255, 0, 0))
        resized = _resize_for_clustering(img, max_side=150)
        assert max(resized.size) <= 150

    def test_small_image_unchanged(self):
        img = Image.new("RGB", (50, 50), color=(0, 255, 0))
        resized = _resize_for_clustering(img, max_side=150)
        assert resized.size == (50, 50)


class TestRemoveBackground:
    def test_white_pixels_removed(self):
        pixels = np.array([
            [255, 255, 255],  # 흰색 — 제거
            [251, 252, 253],  # 거의 흰색 — 제거
            [200, 100, 50],   # 유효
        ] * 50, dtype=np.float64)
        filtered = _remove_background(pixels)
        assert len(filtered) == 50

    def test_black_pixels_removed(self):
        pixels = np.array([
            [0, 0, 0],        # 검정 — 제거
            [3, 2, 4],        # 거의 검정 — 제거
            [100, 150, 200],  # 유효
        ] * 50, dtype=np.float64)
        filtered = _remove_background(pixels)
        assert len(filtered) == 50

    def test_few_valid_pixels_returns_all(self):
        pixels = np.array([
            [255, 255, 255],
            [0, 0, 0],
            [128, 128, 128],
        ] * 10, dtype=np.float64)
        filtered = _remove_background(pixels)
        assert len(filtered) == 30  # 유효 10개 < 50이므로 전체 반환


class TestExtractColorsFromImage:
    def test_solid_color_image(self):
        img = Image.new("RGB", (200, 200), color=(255, 100, 50))
        colors = extract_colors_from_image(img, n_colors=1)
        assert len(colors) == 1
        assert colors[0].startswith("#")
        r = int(colors[0][1:3], 16)
        assert abs(r - 255) <= 5

    def test_returns_n_colors(self):
        arr = np.zeros((200, 200, 3), dtype=np.uint8)
        arr[:100, :, :] = [255, 0, 0]    # 빨강 상단
        arr[100:, :100, :] = [0, 255, 0]  # 초록 좌하단
        arr[100:, 100:, :] = [0, 0, 255]  # 파랑 우하단
        img = Image.fromarray(arr)
        colors = extract_colors_from_image(img, n_colors=3)
        assert len(colors) == 3

    def test_hex_format(self):
        img = Image.new("RGB", (100, 100), color=(10, 20, 30))
        colors = extract_colors_from_image(img, n_colors=1)
        assert len(colors[0]) == 7
        assert colors[0][0] == "#"

    def test_too_few_pixels(self):
        img = Image.new("RGB", (1, 1), color=(100, 100, 100))
        colors = extract_colors_from_image(img, n_colors=3)
        assert colors == []

    def test_rgba_image_converted(self):
        img = Image.new("RGBA", (100, 100), color=(200, 150, 100, 128))
        colors = extract_colors_from_image(img, n_colors=1)
        assert len(colors) == 1
