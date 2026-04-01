"""이미지에서 dominant color를 추출한다.

PIL + scikit-learn K-means 클러스터링으로 상위 N개 색상을 반환.
"""

import io
import logging

import httpx
import numpy as np
from PIL import Image
from sklearn.cluster import MiniBatchKMeans

logger = logging.getLogger(__name__)

DEFAULT_N_COLORS = 3
RESIZE_MAX = 150
REQUEST_TIMEOUT = 10.0


def _resize_for_clustering(img: Image.Image, max_side: int = RESIZE_MAX) -> Image.Image:
    """클러스터링 속도를 위해 이미지를 축소한다."""
    img.thumbnail((max_side, max_side), Image.LANCZOS)
    return img


def _remove_background(pixels: np.ndarray) -> np.ndarray:
    """흰색/검정 배경 픽셀을 제거한다.

    완전 흰색(>250) 또는 완전 검정(<5) 픽셀은 의류 색상이 아닐 가능성이 높다.
    """
    white_mask = np.all(pixels > 250, axis=1)
    black_mask = np.all(pixels < 5, axis=1)
    mask = ~(white_mask | black_mask)
    filtered = pixels[mask]
    if len(filtered) < 50:
        return pixels
    return filtered


def extract_colors_from_image(
    img: Image.Image,
    n_colors: int = DEFAULT_N_COLORS,
) -> list[str]:
    """PIL Image에서 dominant color HEX 목록을 반환한다.

    Args:
        img: PIL Image 객체 (RGB)
        n_colors: 추출할 색상 수 (기본 3)

    Returns:
        HEX 색상 리스트 (비중 높은 순), 예: ["#B0A6C6", "#FFE4C4", "#1E1E4E"]
    """
    img = img.convert("RGB")
    img = _resize_for_clustering(img)

    pixels = np.array(img).reshape(-1, 3).astype(np.float32)
    pixels = _remove_background(pixels)

    if len(pixels) < n_colors:
        return []

    kmeans = MiniBatchKMeans(n_clusters=n_colors, n_init=1, random_state=42)
    kmeans.fit(pixels)

    labels, counts = np.unique(kmeans.labels_, return_counts=True)
    order = np.argsort(-counts)

    colors: list[str] = []
    for idx in order:
        r, g, b = kmeans.cluster_centers_[labels[idx]].astype(int)
        r, g, b = np.clip([r, g, b], 0, 255)
        colors.append(f"#{r:02X}{g:02X}{b:02X}")

    return colors


def extract_colors_from_url(
    url: str,
    n_colors: int = DEFAULT_N_COLORS,
    client: httpx.Client | None = None,
) -> list[str]:
    """이미지 URL에서 dominant color HEX 목록을 반환한다.

    Args:
        url: 이미지 URL
        n_colors: 추출할 색상 수
        client: 재사용할 httpx.Client (없으면 새로 생성)

    Returns:
        HEX 색상 리스트, 실패 시 빈 리스트
    """
    try:
        if client:
            resp = client.get(url, timeout=REQUEST_TIMEOUT)
        else:
            resp = httpx.get(url, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        img = Image.open(io.BytesIO(resp.content))
        return extract_colors_from_image(img, n_colors)
    except Exception as e:
        logger.warning("색상 추출 실패 [%s]: %s", url, e)
        return []
