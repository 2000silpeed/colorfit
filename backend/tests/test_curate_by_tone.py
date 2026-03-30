"""curate_by_tone.py 핵심 함수 테스트."""

import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from scripts.curate_by_tone import (
    NAVER_SEARCH_URL,
    TONE_IDS,
    _backoff_wait,
    build_queries,
    collect_for_query,
    save_raw_json,
    search_products,
)


class TestBuildQueries:
    def test_returns_list(self):
        queries = build_queries("spring_warm_light")
        assert isinstance(queries, list)
        assert len(queries) > 0

    def test_all_queries_are_strings(self):
        queries = build_queries("spring_warm_light")
        assert all(isinstance(q, str) for q in queries)

    def test_contains_color_and_category(self):
        queries = build_queries("spring_warm_light")
        assert any("아이보리" in q for q in queries)
        assert any("코트" in q for q in queries)

    def test_unknown_tone_returns_empty(self):
        queries = build_queries("nonexistent_tone")
        assert queries == []

    def test_query_count_matches_combinations(self):
        from scripts.curate_by_tone import CATEGORY_KEYWORDS, TONE_COLOR_KEYWORDS

        tone_id = "spring_warm_light"
        colors = TONE_COLOR_KEYWORDS[tone_id]
        total_items = sum(len(v) for v in CATEGORY_KEYWORDS.values())
        expected = len(colors) * total_items
        assert len(build_queries(tone_id)) == expected


class TestBackoffWait:
    def test_exponential(self):
        assert _backoff_wait(0) == 1
        assert _backoff_wait(1) == 2
        assert _backoff_wait(2) == 4

    def test_max_cap(self):
        assert _backoff_wait(10) == 16


class TestSearchProducts:
    @pytest.mark.asyncio
    async def test_calls_api_with_correct_params(self):
        mock_response = httpx.Response(
            200,
            json={"items": [{"title": "테스트 상품"}], "total": 1},
            request=httpx.Request("GET", NAVER_SEARCH_URL),
        )
        client = AsyncMock(spec=httpx.AsyncClient)
        client.get = AsyncMock(return_value=mock_response)

        result = await search_products(
            client,
            "코랄 블라우스",
            display=10,
            start=1,
            client_id="test_id",
            client_secret="test_secret",
        )

        client.get.assert_called_once()
        call_kwargs = client.get.call_args
        assert call_kwargs.kwargs["params"]["query"] == "코랄 블라우스"
        assert call_kwargs.kwargs["params"]["display"] == 10
        assert result["items"][0]["title"] == "테스트 상품"

    @pytest.mark.asyncio
    async def test_display_capped_at_100(self):
        mock_response = httpx.Response(
            200,
            json={"items": [], "total": 0},
            request=httpx.Request("GET", NAVER_SEARCH_URL),
        )
        client = AsyncMock(spec=httpx.AsyncClient)
        client.get = AsyncMock(return_value=mock_response)

        await search_products(
            client, "test", display=200, start=1,
            client_id="id", client_secret="secret",
        )
        assert client.get.call_args.kwargs["params"]["display"] == 100


class TestCollectForQuery:
    @pytest.mark.asyncio
    async def test_collects_across_pages(self):
        items_page1 = [{"title": f"item_{i}"} for i in range(100)]
        items_page2 = [{"title": f"item_{i}"} for i in range(100, 150)]

        responses = [
            httpx.Response(
                200,
                json={"items": items_page1, "total": 150},
                request=httpx.Request("GET", NAVER_SEARCH_URL),
            ),
            httpx.Response(
                200,
                json={"items": items_page2, "total": 150},
                request=httpx.Request("GET", NAVER_SEARCH_URL),
            ),
        ]
        client = AsyncMock(spec=httpx.AsyncClient)
        client.get = AsyncMock(side_effect=responses)

        with patch("scripts.curate_by_tone.REQUEST_INTERVAL", 0):
            result = await collect_for_query(
                client, "코랄 블라우스",
                client_id="id", client_secret="secret",
                max_pages=2,
            )

        assert len(result) == 150

    @pytest.mark.asyncio
    async def test_stops_on_empty_items(self):
        mock_response = httpx.Response(
            200,
            json={"items": [], "total": 0},
            request=httpx.Request("GET", NAVER_SEARCH_URL),
        )
        client = AsyncMock(spec=httpx.AsyncClient)
        client.get = AsyncMock(return_value=mock_response)

        with patch("scripts.curate_by_tone.REQUEST_INTERVAL", 0):
            result = await collect_for_query(
                client, "empty query",
                client_id="id", client_secret="secret",
            )

        assert len(result) == 0
        assert client.get.call_count == 1


class TestSaveRawJson:
    def test_saves_json_file(self):
        data = {
            "tone_id": "spring_warm_light",
            "item_count": 2,
            "items": [{"title": "a"}, {"title": "b"}],
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("scripts.curate_by_tone.RAW_DIR", Path(tmpdir)):
                filepath = save_raw_json("spring_warm_light", data)

            assert filepath.exists()
            with open(filepath, encoding="utf-8") as f:
                saved = json.load(f)
            assert saved["tone_id"] == "spring_warm_light"
            assert len(saved["items"]) == 2


class TestToneIds:
    def test_has_12_or_more_tones(self):
        assert len(TONE_IDS) >= 12

    def test_all_tones_have_color_keywords(self):
        from scripts.curate_by_tone import TONE_COLOR_KEYWORDS

        for tone_id in TONE_IDS:
            assert tone_id in TONE_COLOR_KEYWORDS, f"{tone_id} 색상 키워드 누락"
