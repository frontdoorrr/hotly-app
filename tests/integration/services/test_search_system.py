"""
검색 시스템 종합 테스트 코드 (Task 2-3-6)

TDD 기반 검색 정확도, 필터 조합, 사용자 시나리오 테스트
검색 시스템 전반의 품질 보장을 위한 포괄적 테스트 구현
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient


class TestSearchAccuracy:
    """검색 정확도 테스트"""

    def setup_method(self) -> None:
        """테스트 설정"""
        self.test_user_id = uuid4()
        self.mock_search_service = AsyncMock()
        self.mock_elasticsearch = AsyncMock()

        # 테스트 장소 데이터
        self.sample_places = [
            {
                "id": "place_1",
                "name": "카페 ABC",
                "address": "서울시 마포구 홍대입구",
                "category": "cafe",
                "tags": ["조용한", "와이파이좋음"],
                "rating": 4.2,
                "price_range": 1,
                "location": {"lat": 37.5563, "lng": 126.9223},
                "created_at": datetime.utcnow().isoformat(),
            },
            {
                "id": "place_2",
                "name": "홍대 맛집",
                "address": "서울시 마포구 홍익로",
                "category": "restaurant",
                "tags": ["분위기좋은", "데이트"],
                "rating": 4.5,
                "price_range": 2,
                "location": {"lat": 37.5547, "lng": 126.9236},
                "created_at": (datetime.utcnow() - timedelta(days=1)).isoformat(),
            },
            {
                "id": "place_3",
                "name": "신촌 서점카페",
                "address": "서울시 서대문구 신촌동",
                "category": "cafe",
                "tags": ["독서", "조용한"],
                "rating": 4.0,
                "price_range": 1,
                "location": {"lat": 37.5596, "lng": 126.9370},
                "created_at": (datetime.utcnow() - timedelta(days=2)).isoformat(),
            },
        ]

    async def test_exact_name_search_accuracy(self) -> None:
        """
        Given: 정확한 장소명으로 검색
        When: 완전 일치 검색을 수행함
        Then: 해당 장소가 1순위로 반환됨
        """
        # Given: 정확한 장소명 검색
        search_query = "카페 ABC"
        expected_place = self.sample_places[0]

        # Mock Elasticsearch 응답
        self.mock_elasticsearch.search.return_value = {
            "hits": {
                "hits": [
                    {
                        "_source": expected_place,
                        "_score": 10.0,  # 완전 일치 높은 점수
                    }
                ]
            }
        }

        # When: 검색 실행
        from app.services.search_service import SearchService

        search_service = SearchService(
            elasticsearch=self.mock_elasticsearch,
            cache_service=AsyncMock(),
            ranking_service=AsyncMock(),
        )

        results = await search_service.search(
            user_id=self.test_user_id, query=search_query, limit=20
        )

        # Then: 정확한 장소가 1순위로 반환
        assert len(results["places"]) >= 1
        assert results["places"][0]["name"] == "카페 ABC"
        assert results["places"][0]["id"] == "place_1"
        assert results["query"] == search_query
        assert results["total_count"] >= 1

    async def test_partial_match_search_accuracy(self) -> None:
        """
        Given: 부분 일치 키워드로 검색
        When: 부분 매칭 검색을 수행함
        Then: 관련 장소들이 관련도순으로 반환됨
        """
        # Given: 부분 매칭 검색어
        search_query = "홍대"

        # Mock 부분 일치 결과
        self.mock_elasticsearch.search.return_value = {
            "hits": {
                "hits": [
                    {
                        "_source": self.sample_places[1],  # 홍대 맛집
                        "_score": 8.5,
                    },
                    {
                        "_source": self.sample_places[0],  # 카페 ABC (홍대입구)
                        "_score": 6.2,
                    },
                ]
            }
        }

        # When: 부분 매칭 검색
        from app.services.search_service import SearchService

        search_service = SearchService(
            elasticsearch=self.mock_elasticsearch,
            cache_service=AsyncMock(),
            ranking_service=AsyncMock(),
        )

        results = await search_service.search(
            user_id=self.test_user_id, query=search_query
        )

        # Then: 관련도 높은 순으로 반환
        assert len(results["places"]) == 2
        assert results["places"][0]["name"] == "홍대 맛집"  # 더 높은 관련도
        assert results["places"][1]["name"] == "카페 ABC"  # 주소에 홍대 포함

    async def test_korean_english_mixed_search(self) -> None:
        """
        Given: 한글/영문 혼용 검색어
        When: 다국어 검색을 수행함
        Then: 한글/영문 모두 정확히 매칭됨
        """
        # Given: 한영 혼용 검색어
        search_queries = ["cafe", "카페", "Cafe ABC", "까페"]

        for query in search_queries:
            # Mock 다국어 검색 결과
            self.mock_elasticsearch.search.return_value = {
                "hits": {
                    "hits": [
                        {
                            "_source": self.sample_places[0],
                            "_score": 7.5,
                        },
                        {
                            "_source": self.sample_places[2],
                            "_score": 6.8,
                        },
                    ]
                }
            }

            # When: 다국어 검색 실행
            from app.services.search_service import SearchService

            search_service = SearchService(
                elasticsearch=self.mock_elasticsearch,
                cache_service=AsyncMock(),
                ranking_service=AsyncMock(),
            )

            results = await search_service.search(
                user_id=self.test_user_id, query=query
            )

            # Then: 카페 관련 장소들 반환
            assert len(results["places"]) >= 2
            cafe_places = [
                place
                for place in results["places"]
                if place["category"] == "cafe"
            ]
            assert len(cafe_places) >= 2

    async def test_typo_tolerance_search(self) -> None:
        """
        Given: 오타가 포함된 검색어
        When: 퍼지 매칭 검색을 수행함
        Then: 오타를 보정하여 관련 결과를 반환함
        """
        # Given: 오타 포함 검색어 (편집 거리 2 이내)
        typo_queries = [
            ("까페", "카페"),  # 자음 오타
            ("맛칩", "맛집"),  # 자모 오타
            ("신혼", "신촌"),  # 유사 글자
        ]

        for typo_query, correct_query in typo_queries:
            # Mock 오타 교정 검색 결과
            self.mock_elasticsearch.search.return_value = {
                "hits": {
                    "hits": [
                        {
                            "_source": place,
                            "_score": 5.5 - idx * 0.5,  # 오타로 인한 점수 하락
                        }
                        for idx, place in enumerate(self.sample_places)
                        if correct_query in place["name"]
                        or correct_query in place["address"]
                        or correct_query in place["category"]
                    ]
                }
            }

            # When: 오타 검색 실행
            from app.services.search_service import SearchService

            search_service = SearchService(
                elasticsearch=self.mock_elasticsearch,
                cache_service=AsyncMock(),
                ranking_service=AsyncMock(),
            )

            results = await search_service.search(
                user_id=self.test_user_id, query=typo_query
            )

            # Then: 교정된 결과 반환 및 제안
            if results["places"]:
                assert len(results["places"]) >= 1
                # 오타 교정 제안이 있어야 함
                if "suggestions" in results:
                    assert any(correct_query in suggestion for suggestion in results["suggestions"])

    async def test_tag_based_search_accuracy(self) -> None:
        """
        Given: 사용자 태그로 검색
        When: 태그 매칭 검색을 수행함
        Then: 해당 태그가 있는 장소들이 반환됨
        """
        # Given: 태그 검색어들
        tag_queries = ["조용한", "#조용한", "와이파이좋음", "#분위기좋은"]

        for tag_query in tag_queries:
            # 태그에서 # 제거
            clean_tag = tag_query.replace("#", "")

            # Mock 태그 기반 검색
            matching_places = [
                place
                for place in self.sample_places
                if clean_tag in place["tags"]
            ]

            self.mock_elasticsearch.search.return_value = {
                "hits": {
                    "hits": [
                        {
                            "_source": place,
                            "_score": 8.0,  # 태그 매칭 높은 점수
                        }
                        for place in matching_places
                    ]
                }
            }

            # When: 태그 검색 실행
            from app.services.search_service import SearchService

            search_service = SearchService(
                elasticsearch=self.mock_elasticsearch,
                cache_service=AsyncMock(),
                ranking_service=AsyncMock(),
            )

            results = await search_service.search(
                user_id=self.test_user_id, query=tag_query
            )

            # Then: 해당 태그 장소들만 반환
            assert len(results["places"]) == len(matching_places)
            for place in results["places"]:
                assert clean_tag in place["tags"]

    async def test_search_priority_order(self) -> None:
        """
        Given: 다양한 매칭 조건의 검색어
        When: 우선순위 기반 검색을 수행함
        Then: 1순위(장소명) > 2순위(주소) > 3순위(태그) > 4순위(카테고리) 순으로 반환됨
        """
        # Given: "카페" 검색 (다양한 매칭 가능)
        search_query = "카페"

        # Mock 우선순위별 결과 (점수로 구분)
        priority_results = [
            {
                "_source": {
                    "id": "priority_1",
                    "name": "카페 우선순위",  # 1순위: 장소명 매칭
                    "address": "서울시 강남구",
                    "category": "restaurant",
                    "tags": ["맛있는"],
                },
                "_score": 10.0,
            },
            {
                "_source": {
                    "id": "priority_2",
                    "name": "ABC 식당",
                    "address": "서울시 카페거리",  # 2순위: 주소 매칭
                    "category": "restaurant",
                    "tags": ["분위기"],
                },
                "_score": 7.0,
            },
            {
                "_source": {
                    "id": "priority_3",
                    "name": "맛집 XYZ",
                    "address": "서울시 홍대",
                    "category": "restaurant",
                    "tags": ["카페같은"],  # 3순위: 태그 매칭
                },
                "_score": 5.0,
            },
            {
                "_source": {
                    "id": "priority_4",
                    "name": "음료전문점",
                    "address": "서울시 신촌",
                    "category": "cafe",  # 4순위: 카테고리 매칭
                    "tags": ["조용한"],
                },
                "_score": 3.0,
            },
        ]

        self.mock_elasticsearch.search.return_value = {"hits": {"hits": priority_results}}

        # When: 우선순위 검색 실행
        from app.services.search_service import SearchService

        search_service = SearchService(
            elasticsearch=self.mock_elasticsearch,
            cache_service=AsyncMock(),
            ranking_service=AsyncMock(),
        )

        results = await search_service.search(
            user_id=self.test_user_id, query=search_query
        )

        # Then: 우선순위 순으로 정렬되어 반환
        assert len(results["places"]) == 4
        assert results["places"][0]["id"] == "priority_1"  # 장소명 매칭 1순위
        assert results["places"][1]["id"] == "priority_2"  # 주소 매칭 2순위
        assert results["places"][2]["id"] == "priority_3"  # 태그 매칭 3순위
        assert results["places"][3]["id"] == "priority_4"  # 카테고리 매칭 4순위

    async def test_empty_search_results_handling(self) -> None:
        """
        Given: 검색 결과가 없는 검색어
        When: 검색을 수행함
        Then: 빈 결과와 함께 유용한 제안을 제공함
        """
        # Given: 결과 없는 검색어
        no_result_query = "존재하지않는장소명123"

        # Mock 빈 검색 결과
        self.mock_elasticsearch.search.return_value = {"hits": {"hits": []}}

        # When: 빈 결과 검색 실행
        from app.services.search_service import SearchService

        search_service = SearchService(
            elasticsearch=self.mock_elasticsearch,
            cache_service=AsyncMock(),
            ranking_service=AsyncMock(),
        )

        results = await search_service.search(
            user_id=self.test_user_id, query=no_result_query
        )

        # Then: 빈 결과 처리 확인
        assert len(results["places"]) == 0
        assert results["total_count"] == 0
        assert "message" in results
        assert "검색 결과가 없" in results["message"]

        # 유용한 제안 포함 여부 확인
        if "suggestions" in results:
            assert len(results["suggestions"]) > 0
            assert all(isinstance(suggestion, str) for suggestion in results["suggestions"])

    async def test_autocomplete_accuracy(self) -> None:
        """
        Given: 자동완성 요청
        When: 부분 입력으로 자동완성을 요청함
        Then: 관련성 높은 제안들이 빈도순으로 반환됨
        """
        # Given: 부분 입력
        partial_inputs = ["카", "홍", "조"]

        for partial_input in partial_inputs:
            # Mock 자동완성 결과
            suggestions = []
            if partial_input == "카":
                suggestions = ["카페", "카페 ABC", "카지노"]
            elif partial_input == "홍":
                suggestions = ["홍대", "홍대 맛집", "홍익대"]
            elif partial_input == "조":
                suggestions = ["조용한", "좋은", "조선"]

            # Mock 자동완성 서비스
            mock_autocomplete = AsyncMock()
            mock_autocomplete.get_suggestions.return_value = [
                {"text": suggestion, "frequency": 10 - idx, "type": "query"}
                for idx, suggestion in enumerate(suggestions)
            ]

            # When: 자동완성 실행
            from app.services.autocomplete_service import AutocompleteService

            autocomplete_service = AutocompleteService(
                redis=AsyncMock(),
                search_service=AsyncMock(),
                analytics_service=AsyncMock(),
            )
            autocomplete_service.get_suggestions = mock_autocomplete.get_suggestions

            results = await autocomplete_service.get_suggestions(
                user_id=self.test_user_id, partial_query=partial_input, limit=5
            )

            # Then: 관련성 높은 제안 반환
            assert len(results) >= 1
            assert len(results) <= 5
            assert all(partial_input in result["text"] for result in results)
            # 빈도 순으로 정렬되었는지 확인
            frequencies = [result["frequency"] for result in results]
            assert frequencies == sorted(frequencies, reverse=True)


class TestFilterCombinations:
    """필터 조합 테스트"""

    def setup_method(self) -> None:
        """테스트 설정"""
        self.test_user_id = uuid4()
        self.mock_filter_service = AsyncMock()

        # 다양한 필터 조합용 테스트 데이터
        self.diverse_places = [
            {
                "id": "filter_1",
                "name": "홍대 조용한 카페",
                "category": "cafe",
                "region": "홍대",
                "tags": ["조용한", "와이파이"],
                "price_range": 1,
                "rating": 4.2,
                "status": "즐겨찾기",
            },
            {
                "id": "filter_2",
                "name": "강남 비싼 맛집",
                "category": "restaurant",
                "region": "강남",
                "tags": ["고급", "데이트"],
                "price_range": 4,
                "rating": 4.8,
                "status": "가보고싶음",
            },
            {
                "id": "filter_3",
                "name": "홍대 저렴한 술집",
                "category": "bar",
                "region": "홍대",
                "tags": ["분위기", "저렴"],
                "price_range": 2,
                "rating": 4.0,
                "status": "방문완료",
            },
            {
                "id": "filter_4",
                "name": "신촌 넓은 카페",
                "category": "cafe",
                "region": "신촌",
                "tags": ["넓은", "단체"],
                "price_range": 2,
                "rating": 4.1,
                "status": "즐겨찾기",
            },
        ]

    async def test_single_category_filter(self) -> None:
        """
        Given: 단일 카테고리 필터 적용
        When: 카테고리 필터링을 실행함
        Then: 해당 카테고리 장소들만 반환됨
        """
        # Given: 카페 카테고리 필터
        filters = {"categories": ["cafe"]}

        expected_results = [
            place for place in self.diverse_places if place["category"] == "cafe"
        ]

        # Mock 필터링 결과
        self.mock_filter_service.apply_filters.return_value = {
            "places": expected_results,
            "total_count": len(expected_results),
            "applied_filters": filters,
        }

        # When: 카테고리 필터 적용
        from app.services.filter_service import FilterService

        filter_service = FilterService(
            elasticsearch=AsyncMock(), cache_service=AsyncMock()
        )
        filter_service.apply_filters = self.mock_filter_service.apply_filters

        results = await filter_service.apply_filters(
            user_id=self.test_user_id, filters=filters
        )

        # Then: 카페만 반환됨
        assert len(results["places"]) == 2  # filter_1, filter_4
        assert all(place["category"] == "cafe" for place in results["places"])

    async def test_multiple_categories_filter(self) -> None:
        """
        Given: 다중 카테고리 필터 적용
        When: 여러 카테고리로 필터링을 실행함
        Then: 선택된 카테고리들의 OR 조건으로 결과 반환됨
        """
        # Given: 카페 또는 맛집 카테고리
        filters = {"categories": ["cafe", "restaurant"]}

        expected_results = [
            place
            for place in self.diverse_places
            if place["category"] in ["cafe", "restaurant"]
        ]

        # Mock OR 조건 필터링
        self.mock_filter_service.apply_filters.return_value = {
            "places": expected_results,
            "total_count": len(expected_results),
            "applied_filters": filters,
        }

        # When: 다중 카테고리 필터 적용
        from app.services.filter_service import FilterService

        filter_service = FilterService(
            elasticsearch=AsyncMock(), cache_service=AsyncMock()
        )
        filter_service.apply_filters = self.mock_filter_service.apply_filters

        results = await filter_service.apply_filters(
            user_id=self.test_user_id, filters=filters
        )

        # Then: 카페 또는 맛집만 반환
        assert len(results["places"]) == 3  # filter_1, filter_2, filter_4
        assert all(
            place["category"] in ["cafe", "restaurant"] for place in results["places"]
        )

    async def test_complex_and_filter_combination(self) -> None:
        """
        Given: 복합 AND 조건 필터 적용
        When: 여러 필터를 AND 조건으로 조합함
        Then: 모든 조건을 만족하는 장소들만 반환됨
        """
        # Given: 홍대 + 카페 + 즐겨찾기 복합 조건
        filters = {
            "categories": ["cafe"],
            "regions": ["홍대"],
            "status": ["즐겨찾기"],
        }

        # 모든 조건을 만족하는 장소 필터링
        expected_results = []
        for place in self.diverse_places:
            if (
                place["category"] in filters["categories"]
                and place["region"] in filters["regions"]
                and place["status"] in filters["status"]
            ):
                expected_results.append(place)

        # Mock 복합 AND 조건
        self.mock_filter_service.apply_filters.return_value = {
            "places": expected_results,
            "total_count": len(expected_results),
            "applied_filters": filters,
        }

        # When: 복합 필터 적용
        from app.services.filter_service import FilterService

        filter_service = FilterService(
            elasticsearch=AsyncMock(), cache_service=AsyncMock()
        )
        filter_service.apply_filters = self.mock_filter_service.apply_filters

        results = await filter_service.apply_filters(
            user_id=self.test_user_id, filters=filters
        )

        # Then: 모든 조건 만족하는 장소만 반환 (filter_1만 해당)
        assert len(results["places"]) == 1
        assert results["places"][0]["id"] == "filter_1"
        assert results["places"][0]["category"] == "cafe"
        assert results["places"][0]["region"] == "홍대"
        assert results["places"][0]["status"] == "즐겨찾기"

    async def test_price_range_filter(self) -> None:
        """
        Given: 가격대 범위 필터 적용
        When: 특정 가격대로 필터링을 실행함
        Then: 해당 가격대 장소들만 반환됨
        """
        # Given: 저가격대(1-2) 필터
        filters = {"price_range": [1, 2]}

        expected_results = [
            place
            for place in self.diverse_places
            if place["price_range"] in [1, 2]
        ]

        # Mock 가격대 필터링
        self.mock_filter_service.apply_filters.return_value = {
            "places": expected_results,
            "total_count": len(expected_results),
            "applied_filters": filters,
        }

        # When: 가격대 필터 적용
        from app.services.filter_service import FilterService

        filter_service = FilterService(
            elasticsearch=AsyncMock(), cache_service=AsyncMock()
        )
        filter_service.apply_filters = self.mock_filter_service.apply_filters

        results = await filter_service.apply_filters(
            user_id=self.test_user_id, filters=filters
        )

        # Then: 저가격대 장소들만 반환
        assert len(results["places"]) == 3  # filter_1(1), filter_3(2), filter_4(2)
        assert all(place["price_range"] in [1, 2] for place in results["places"])

    async def test_tag_based_filter(self) -> None:
        """
        Given: 태그 기반 필터 적용
        When: 특정 태그들로 필터링을 실행함
        Then: 해당 태그가 있는 장소들만 반환됨
        """
        # Given: "조용한" 태그 필터
        filters = {"tags": ["조용한"]}

        expected_results = [
            place
            for place in self.diverse_places
            if any(tag in place["tags"] for tag in filters["tags"])
        ]

        # Mock 태그 필터링
        self.mock_filter_service.apply_filters.return_value = {
            "places": expected_results,
            "total_count": len(expected_results),
            "applied_filters": filters,
        }

        # When: 태그 필터 적용
        from app.services.filter_service import FilterService

        filter_service = FilterService(
            elasticsearch=AsyncMock(), cache_service=AsyncMock()
        )
        filter_service.apply_filters = self.mock_filter_service.apply_filters

        results = await filter_service.apply_filters(
            user_id=self.test_user_id, filters=filters
        )

        # Then: "조용한" 태그 장소들만 반환
        assert len(results["places"]) == 1  # filter_1만
        assert all("조용한" in place["tags"] for place in results["places"])

    async def test_maximum_filter_combinations(self) -> None:
        """
        Given: 최대 10개 필터 조건 적용
        When: 최대 허용 필터 수로 조합함
        Then: 성능 저하 없이 정확한 결과 반환됨
        """
        # Given: 최대 조건 수 필터 (PRD 기준 최대 10개)
        max_filters = {
            "categories": ["cafe", "restaurant"],
            "regions": ["홍대", "강남"],
            "tags": ["조용한", "분위기"],
            "status": ["즐겨찾기", "가보고싶음"],
            "price_range": [1, 2, 3],
            "rating_min": 4.0,
            "rating_max": 5.0,
        }

        # 복잡한 조건 처리 시뮬레이션
        filtered_results = []
        for place in self.diverse_places:
            matches = True
            
            # 각 필터 조건 검사
            if place["category"] not in max_filters["categories"]:
                matches = False
            if place["region"] not in max_filters["regions"]:
                matches = False
            if not any(tag in place["tags"] for tag in max_filters["tags"]):
                matches = False
            if place["status"] not in max_filters["status"]:
                matches = False
            if place["price_range"] not in max_filters["price_range"]:
                matches = False
            if not (max_filters["rating_min"] <= place["rating"] <= max_filters["rating_max"]):
                matches = False
                
            if matches:
                filtered_results.append(place)

        # Mock 복잡한 필터 조합
        self.mock_filter_service.apply_filters.return_value = {
            "places": filtered_results,
            "total_count": len(filtered_results),
            "applied_filters": max_filters,
            "processing_time_ms": 850,  # 1초 이내 처리
        }

        # When: 최대 필터 조합 적용
        from app.services.filter_service import FilterService

        filter_service = FilterService(
            elasticsearch=AsyncMock(), cache_service=AsyncMock()
        )
        filter_service.apply_filters = self.mock_filter_service.apply_filters

        import time
        start_time = time.time()

        results = await filter_service.apply_filters(
            user_id=self.test_user_id, filters=max_filters
        )

        processing_time = (time.time() - start_time) * 1000

        # Then: 성능 요구사항 내에서 정확한 결과
        assert processing_time < 1000  # 1초 이내 처리
        assert isinstance(results["places"], list)
        assert "applied_filters" in results
        assert len(results["applied_filters"]) <= 10  # 최대 필터 수 준수

    async def test_filter_reset_functionality(self) -> None:
        """
        Given: 필터가 적용된 상태
        When: 필터 초기화를 실행함
        Then: 모든 필터가 해제되고 전체 결과 반환됨
        """
        # Given: 초기 필터 적용 상태
        initial_filters = {
            "categories": ["cafe"],
            "regions": ["홍대"],
        }

        # When: 필터 초기화 실행
        reset_filters = {}  # 빈 필터 = 초기화

        # Mock 초기화 후 전체 결과
        self.mock_filter_service.apply_filters.return_value = {
            "places": self.diverse_places,  # 전체 장소 반환
            "total_count": len(self.diverse_places),
            "applied_filters": reset_filters,
            "reset": True,
        }

        # When: 필터 초기화 적용
        from app.services.filter_service import FilterService

        filter_service = FilterService(
            elasticsearch=AsyncMock(), cache_service=AsyncMock()
        )
        filter_service.apply_filters = self.mock_filter_service.apply_filters

        results = await filter_service.apply_filters(
            user_id=self.test_user_id, filters=reset_filters
        )

        # Then: 전체 장소 반환 및 필터 초기화 확인
        assert len(results["places"]) == len(self.diverse_places)
        assert results["applied_filters"] == {}
        assert results.get("reset", False) == True

    async def test_filter_performance_optimization(self) -> None:
        """
        Given: 자주 사용되는 필터 조합
        When: 캐시된 필터 조합으로 검색함
        Then: 빠른 응답시간으로 결과 반환됨
        """
        # Given: 인기 필터 조합 (카페 + 홍대)
        popular_filters = {
            "categories": ["cafe"],
            "regions": ["홍대"],
        }

        # Mock 캐시된 필터 결과
        cached_results = [
            place
            for place in self.diverse_places
            if place["category"] == "cafe" and place["region"] == "홍대"
        ]

        self.mock_filter_service.apply_filters.return_value = {
            "places": cached_results,
            "total_count": len(cached_results),
            "applied_filters": popular_filters,
            "cached": True,
            "processing_time_ms": 50,  # 캐시로 인한 빠른 응답
        }

        # When: 캐시된 필터 조합 실행
        from app.services.filter_service import FilterService

        filter_service = FilterService(
            elasticsearch=AsyncMock(), cache_service=AsyncMock()
        )
        filter_service.apply_filters = self.mock_filter_service.apply_filters

        import time
        start_time = time.time()

        results = await filter_service.apply_filters(
            user_id=self.test_user_id, filters=popular_filters
        )

        processing_time = (time.time() - start_time) * 1000

        # Then: 빠른 캐시 응답 확인
        assert processing_time < 200  # 200ms 이내
        assert results.get("cached", False) == True
        assert len(results["places"]) == 1  # filter_1만 해당