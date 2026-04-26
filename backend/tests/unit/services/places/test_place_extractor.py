"""PlaceExtractorService 키워드 검색 / place.name 정규화 단위 테스트."""

import pytest

from app.services.places.place_extractor import (
    PlaceExtractorService,
    _build_keyword_candidates,
    _choose_entity,
    _choose_place_name,
    _extract_region_token,
    _pick_best_result,
)


class TestExtractRegionToken:
    def test_named_entity_with_gu_suffix(self):
        assert _extract_region_token(["진진바리횟집", "강서구청"], []) == "강서구청"

    def test_keyword_with_compound_token(self):
        assert _extract_region_token([], ["강서구청 맛집"]) == "강서구청"

    def test_no_match_returns_none(self):
        assert _extract_region_token(["횟집", "참치"], ["가성비"]) is None

    def test_handles_none_inputs(self):
        assert _extract_region_token(None, None) is None  # type: ignore[arg-type]

    def test_dong_suffix_match(self):
        assert _extract_region_token(["성수동"], []) == "성수동"


class TestChooseEntity:
    def test_skips_generic_first_entity(self):
        assert _choose_entity(["맛집", "진진바리횟집"]) == "진진바리횟집"

    def test_returns_first_specific(self):
        assert _choose_entity(["진진바리횟집", "강서구청"]) == "진진바리횟집"

    def test_all_generic_returns_none(self):
        assert _choose_entity(["맛집", "카페", "식당"]) is None

    def test_empty_returns_none(self):
        assert _choose_entity([]) is None

    def test_blocklist_case_insensitive(self):
        assert _choose_entity(["Cafe", "스타벅스"]) == "스타벅스"


class TestBuildKeywordCandidates:
    def test_region_plus_entity_first(self):
        result = _build_keyword_candidates(
            name="강서구청 가성비 극강 진진바리횟집 후기",
            named_entities=["진진바리횟집", "강서구청"],
            keywords_main=["횟집", "강서구청 맛집"],
        )
        assert result[0] == "강서구청 진진바리횟집"
        assert "진진바리횟집" in result

    def test_dedupes_repeated_entries(self):
        result = _build_keyword_candidates(
            name="진진바리횟집",
            named_entities=["진진바리횟집"],
            keywords_main=[],
        )
        assert result.count("진진바리횟집") == 1

    def test_falls_back_to_truncated_name(self):
        long_name = "강서구청 가성비 극강 진진바리횟집 2.5 모듬회 정식 후기"
        result = _build_keyword_candidates(
            name=long_name,
            named_entities=[],
            keywords_main=[],
        )
        assert result == [long_name[:20]]

    def test_no_entity_no_region(self):
        result = _build_keyword_candidates(
            name="진진바리횟집",
            named_entities=[],
            keywords_main=[],
        )
        assert result == ["진진바리횟집"]

    def test_empty_inputs(self):
        assert _build_keyword_candidates(None, [], []) == []
        assert _build_keyword_candidates("", [], []) == []


class TestPickBestResult:
    def test_prefers_entity_match(self):
        results = [
            {"place_name": "다른 가게", "latitude": 1.0, "longitude": 2.0},
            {"place_name": "진진바리횟집", "latitude": 3.0, "longitude": 4.0},
        ]
        picked = _pick_best_result(results, "진진바리횟집")
        assert picked["latitude"] == 3.0

    def test_falls_back_to_first(self):
        results = [
            {"place_name": "전혀 다른 곳", "latitude": 1.0, "longitude": 2.0},
        ]
        picked = _pick_best_result(results, "진진바리횟집")
        assert picked["latitude"] == 1.0

    def test_empty_returns_none(self):
        assert _pick_best_result([], "진진바리횟집") is None

    def test_skips_results_without_coords(self):
        results = [
            {"place_name": "first", "latitude": None, "longitude": None},
        ]
        assert _pick_best_result(results, "first") is None

    def test_no_entity_returns_first(self):
        results = [{"place_name": "x", "latitude": 1.0, "longitude": 2.0}]
        picked = _pick_best_result(results, None)
        assert picked["latitude"] == 1.0


class TestChoosePlaceName:
    def test_prefers_specific_entity(self):
        assert (
            _choose_place_name(
                "강서구청 가성비 극강 진진바리횟집 2.5 모듬회 정식 후기",
                ["진진바리횟집", "강서구청"],
            )
            == "진진바리횟집"
        )

    def test_falls_back_to_truncated_title(self):
        long_title = "x" * 200
        result = _choose_place_name(long_title, ["맛집"])
        assert result == "x" * 80

    def test_returns_none_when_both_empty(self):
        assert _choose_place_name(None, []) is None
        assert _choose_place_name("", []) is None


class TestGetCoordinatesIntegration:
    @pytest.mark.asyncio
    async def test_keyword_fallback_uses_entity_with_region(self, monkeypatch):
        """주소 매칭 실패 시 region+entity 쿼리가 첫 번째로 시도된다."""
        from app.services.places import place_extractor as pe

        called_queries: list[str] = []

        class FakeKakao:
            def __init__(self):
                pass

            async def _address_to_coordinate_async(self, address):
                raise ValueError("address not found")

            async def _search_places_async(self, keyword, *args, **kwargs):
                called_queries.append(keyword)
                if keyword == "강서구청 진진바리횟집":
                    return [
                        {
                            "place_name": "진진바리횟집",
                            "address": "서울 강서구 ...",
                            "latitude": 37.5,
                            "longitude": 126.8,
                        }
                    ]
                return []

        monkeypatch.setattr(pe, "KakaoMapService", FakeKakao)

        svc = PlaceExtractorService()
        lat, lng = await svc._get_coordinates(
            name="강서구청 가성비 극강 진진바리횟집 2.5 모듬회 정식 후기",
            address="강서구청 뒤골목",
            named_entities=["진진바리횟집", "강서구청"],
            keywords_main=["횟집", "강서구청 맛집"],
        )

        assert (lat, lng) == (37.5, 126.8)
        assert called_queries[0] == "강서구청 진진바리횟집"

    @pytest.mark.asyncio
    async def test_returns_none_when_all_candidates_miss(self, monkeypatch):
        from app.services.places import place_extractor as pe

        class FakeKakao:
            def __init__(self):
                pass

            async def _address_to_coordinate_async(self, address):
                raise ValueError("not found")

            async def _search_places_async(self, keyword, *args, **kwargs):
                return []

        monkeypatch.setattr(pe, "KakaoMapService", FakeKakao)

        svc = PlaceExtractorService()
        lat, lng = await svc._get_coordinates(
            name="긴 제목",
            address="구어체 주소",
            named_entities=["진진바리횟집"],
            keywords_main=[],
        )
        assert (lat, lng) == (None, None)
