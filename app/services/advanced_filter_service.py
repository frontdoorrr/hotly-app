"""
고급 필터링 서비스 (Task 2-3-3)

다중 필터 조건을 지원하는 종합적인 검색 필터링 시스템
- Elasticsearch 기반 고성능 필터링
- 다양한 필터 조합 지원 (카테고리, 지역, 태그, 가격, 평점, 위치, 시간)
- 실시간 패싯 정보 제공
- 캐싱 및 성능 최적화
- PostgreSQL fallback 지원
"""

import hashlib
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

import redis.asyncio as redis
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.db.elasticsearch import es_manager
from app.models.place import Place, PlaceStatus

logger = logging.getLogger(__name__)


class AdvancedFilterService:
    """고급 필터링 서비스"""

    def __init__(
        self,
        db: Session,
        redis_client: Optional[redis.Redis] = None,
        es_manager_instance: Optional[Any] = None,
    ):
        self.db = db
        self.redis = redis_client
        self.es_manager = es_manager_instance or es_manager

        # 필터링 설정
        self.default_limit = 20
        self.max_limit = 100
        self.cache_ttl = 300  # 5분
        self.facet_cache_ttl = 600  # 10분

        # 성능 최적화 설정
        self.optimization_thresholds = {
            "large_result_set": 1000,
            "complex_filter_count": 5,
            "geo_search_radius": 10.0,
        }

    async def comprehensive_filter_search(
        self,
        user_id: UUID,
        filter_criteria: Dict[str, Any],
        limit: int = None,
        offset: int = 0,
        include_facets: bool = False,
    ) -> Dict[str, Any]:
        """
        종합적인 고급 필터 검색 수행

        모든 필터 조건을 AND 조합으로 적용하여
        사용자의 정확한 요구사항에 맞는 장소를 검색
        """
        start_time = datetime.utcnow()

        try:
            # 파라미터 검증 및 기본값 설정
            limit = min(limit or self.default_limit, self.max_limit)
            filter_criteria = self._validate_and_normalize_filters(filter_criteria)

            # 캐시 키 생성 및 캐시 조회
            cache_key = self._generate_filter_cache_key(
                user_id, filter_criteria, limit, offset
            )
            if self.redis:
                cached_result = await self._get_cached_result(cache_key)
                if cached_result:
                    cached_result["performance"] = self._calculate_performance_metrics(
                        start_time, cache_hit=True
                    )
                    return cached_result

            # Elasticsearch 쿼리 빌드 및 실행
            try:
                result = await self._execute_elasticsearch_search(
                    user_id, filter_criteria, limit, offset, include_facets
                )
            except Exception as e:
                logger.warning(
                    f"Elasticsearch search failed: {e}, falling back to PostgreSQL"
                )
                result = await self._fallback_postgresql_filter(
                    user_id, filter_criteria, limit, offset
                )

            # 결과 후처리
            result = await self._post_process_results(result, filter_criteria)

            # 성능 메트릭 추가
            result["performance"] = self._calculate_performance_metrics(
                start_time, cache_hit=False
            )

            # 결과 캐싱
            if self.redis:
                await self._cache_result(cache_key, result)

            return result

        except Exception as e:
            logger.error(f"Comprehensive filter search failed: {e}")
            return await self._get_fallback_result(user_id, e)

    def _validate_and_normalize_filters(
        self, filters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """필터 조건 검증 및 정규화"""
        normalized = {}

        # 기본 검색어
        if filters.get("query"):
            normalized["query"] = str(filters["query"]).strip()[:100]

        # 카테고리 필터 (OR 조건)
        if filters.get("categories"):
            categories = filters["categories"]
            if isinstance(categories, str):
                categories = [categories]
            normalized["categories"] = [
                cat.strip() for cat in categories if cat.strip()
            ]

        # 지역 필터 (OR 조건)
        if filters.get("regions"):
            regions = filters["regions"]
            if isinstance(regions, str):
                regions = [regions]
            normalized["regions"] = [
                region.strip() for region in regions if region.strip()
            ]

        # 태그 필터
        if filters.get("tags"):
            tags = filters["tags"]
            if isinstance(tags, str):
                tags = [tags]
            normalized["tags"] = [tag.strip() for tag in tags if tag.strip()]
            normalized["tag_match_mode"] = filters.get("tag_match_mode", "any")

        # 가격 필터
        if filters.get("price_ranges"):
            normalized["price_ranges"] = filters["price_ranges"]

        if filters.get("price_min") is not None:
            normalized["price_min"] = max(0, int(filters["price_min"]))

        if filters.get("price_max") is not None:
            normalized["price_max"] = max(0, int(filters["price_max"]))

        # 평점 필터
        if filters.get("rating_min") is not None:
            normalized["rating_min"] = max(0.0, min(5.0, float(filters["rating_min"])))

        if filters.get("rating_max") is not None:
            normalized["rating_max"] = max(0.0, min(5.0, float(filters["rating_max"])))

        if filters.get("review_count_min") is not None:
            normalized["review_count_min"] = max(0, int(filters["review_count_min"]))

        # 방문 상태 필터
        if filters.get("visit_status"):
            status_list = filters["visit_status"]
            if isinstance(status_list, str):
                status_list = [status_list]
            valid_statuses = ["wishlist", "favorite", "visited", "planned"]
            normalized["visit_status"] = [s for s in status_list if s in valid_statuses]

        # 위치 필터
        if filters.get("location"):
            location = filters["location"]
            if isinstance(location, dict) and "lat" in location and "lng" in location:
                normalized["location"] = {
                    "lat": float(location["lat"]),
                    "lng": float(location["lng"]),
                    "radius_km": location.get("radius_km", 5.0),
                }

        # 시간 필터
        for time_field in ["created_after", "created_before", "updated_after"]:
            if filters.get(time_field):
                try:
                    if isinstance(filters[time_field], str):
                        normalized[time_field] = datetime.fromisoformat(
                            filters[time_field]
                        )
                    else:
                        normalized[time_field] = filters[time_field]
                except (ValueError, TypeError):
                    logger.warning(
                        f"Invalid {time_field} format: {filters[time_field]}"
                    )

        # 정렬 옵션
        valid_sorts = [
            "relevance",
            "rating",
            "recent",
            "price",
            "distance",
            "name",
            "popular",
        ]
        normalized["sort_by"] = filters.get("sort_by", "relevance")
        if normalized["sort_by"] not in valid_sorts:
            normalized["sort_by"] = "relevance"

        normalized["sort_order"] = filters.get("sort_order", "desc")
        if normalized["sort_order"] not in ["asc", "desc"]:
            normalized["sort_order"] = "desc"

        # 추가 옵션
        normalized["include_facets"] = filters.get("include_facets", False)
        normalized["highlight"] = filters.get("highlight", True)
        normalized["optimization_mode"] = filters.get("optimization_mode", False)

        return normalized

    async def _execute_elasticsearch_search(
        self,
        user_id: UUID,
        filters: Dict[str, Any],
        limit: int,
        offset: int,
        include_facets: bool,
    ) -> Dict[str, Any]:
        """Elasticsearch 기반 고급 필터 검색 실행"""

        # 검색 쿼리 빌드
        query = self._build_elasticsearch_query(user_id, filters)

        # 정렬 쿼리 빌드
        sort_clauses = self._build_sort_clauses(filters)

        # 패싯 쿼리 빌드
        aggregations = {}
        if include_facets:
            aggregations = self._build_facet_aggregations(filters)

        # Elasticsearch 검색 실행
        search_body = {
            "query": query,
            "sort": sort_clauses,
            "from": offset,
            "size": limit,
            "_source": self._get_source_fields(),
        }

        if aggregations:
            search_body["aggs"] = aggregations

        if filters.get("highlight"):
            search_body["highlight"] = self._build_highlight_config(filters)

        # 검색 실행
        es_result = await self.es_manager.search(index="places", body=search_body)

        # 결과 변환
        return self._convert_elasticsearch_result(es_result, filters, include_facets)

    def _build_elasticsearch_query(
        self, user_id: UUID, filters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Elasticsearch 쿼리 빌드"""

        bool_query = {
            "bool": {
                "must": [],
                "filter": [{"term": {"user_id": str(user_id)}}],  # 사용자별 필터링
                "should": [],
            }
        }

        # 기본 검색어 쿼리
        if filters.get("query"):
            bool_query["bool"]["must"].append(
                {
                    "multi_match": {
                        "query": filters["query"],
                        "fields": [
                            "name^3",
                            "name.raw^5",
                            "description^1",
                            "address^2",
                            "tags^2",
                        ],
                        "type": "best_fields",
                        "fuzziness": "AUTO",
                    }
                }
            )

        # 카테고리 필터 (OR 조건)
        if filters.get("categories"):
            bool_query["bool"]["filter"].append(
                {"terms": {"category": filters["categories"]}}
            )

        # 지역 필터 (OR 조건)
        if filters.get("regions"):
            region_queries = []
            for region in filters["regions"]:
                region_queries.extend(
                    [
                        {"match": {"address": region}},
                        {"match": {"district": region}},
                        {"match": {"city": region}},
                    ]
                )

            if region_queries:
                bool_query["bool"]["filter"].append(
                    {"bool": {"should": region_queries}}
                )

        # 태그 필터
        if filters.get("tags"):
            if filters.get("tag_match_mode") == "all":
                # 모든 태그 포함 (AND 조건)
                for tag in filters["tags"]:
                    bool_query["bool"]["filter"].append({"term": {"tags": tag}})
            else:
                # 태그 중 하나 이상 포함 (OR 조건)
                bool_query["bool"]["filter"].append(
                    {"terms": {"tags": filters["tags"]}}
                )

        # 가격 필터
        if (
            filters.get("price_ranges")
            or filters.get("price_min")
            or filters.get("price_max")
        ):
            price_filters = []

            # 가격대 범위 필터
            if filters.get("price_ranges"):
                for price_range in filters["price_ranges"]:
                    if "-" in price_range:
                        min_price, max_price = price_range.split("-")
                        price_filters.append(
                            {
                                "range": {
                                    "price_range": {
                                        "gte": int(min_price),
                                        "lte": int(max_price),
                                    }
                                }
                            }
                        )
                    elif price_range.endswith("+"):
                        min_price = int(price_range[:-1])
                        price_filters.append(
                            {"range": {"price_range": {"gte": min_price}}}
                        )

            # 직접 가격 범위
            price_range_filter = {}
            if filters.get("price_min"):
                price_range_filter["gte"] = filters["price_min"]
            if filters.get("price_max"):
                price_range_filter["lte"] = filters["price_max"]

            if price_range_filter:
                price_filters.append({"range": {"price_range": price_range_filter}})

            if price_filters:
                bool_query["bool"]["filter"].append({"bool": {"should": price_filters}})

        # 평점 필터
        rating_range = {}
        if filters.get("rating_min"):
            rating_range["gte"] = filters["rating_min"]
        if filters.get("rating_max"):
            rating_range["lte"] = filters["rating_max"]

        if rating_range:
            bool_query["bool"]["filter"].append({"range": {"rating": rating_range}})

        # 리뷰 수 필터
        if filters.get("review_count_min"):
            bool_query["bool"]["filter"].append(
                {"range": {"review_count": {"gte": filters["review_count_min"]}}}
            )

        # 방문 상태 필터
        if filters.get("visit_status"):
            bool_query["bool"]["filter"].append(
                {"terms": {"visit_status": filters["visit_status"]}}
            )

        # 위치 필터
        if filters.get("location"):
            location = filters["location"]
            bool_query["bool"]["filter"].append(
                {
                    "geo_distance": {
                        "distance": f"{location['radius_km']}km",
                        "location": {
                            "lat": location["lat"],
                            "lon": location["lng"],
                        },
                    }
                }
            )

        # 시간 필터
        for time_field, es_field in [
            ("created_after", "created_at"),
            ("created_before", "created_at"),
            ("updated_after", "updated_at"),
        ]:
            if filters.get(time_field):
                time_range = {}
                if time_field.endswith("_after"):
                    time_range["gte"] = filters[time_field].isoformat()
                else:
                    time_range["lte"] = filters[time_field].isoformat()

                bool_query["bool"]["filter"].append({"range": {es_field: time_range}})

        return bool_query

    def _build_sort_clauses(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """정렬 조건 빌드"""
        sort_by = filters.get("sort_by", "relevance")
        sort_order = filters.get("sort_order", "desc")

        if sort_by == "distance":
            location = filters.get("location")
            if not location:
                # 위치 정보가 없으면 관련도순으로 대체
                return [{"_score": {"order": "desc"}}]

            return [
                {
                    "_geo_distance": {
                        "location": {
                            "lat": location["lat"],
                            "lon": location["lng"],
                        },
                        "order": "asc",
                        "unit": "km",
                    }
                }
            ]

        elif sort_by == "rating":
            return [
                {"rating": {"order": sort_order, "missing": "_last"}},
                {"review_count": {"order": "desc"}},
                {"_score": {"order": "desc"}},
            ]

        elif sort_by == "recent":
            return [
                {"created_at": {"order": sort_order}},
                {"_score": {"order": "desc"}},
            ]

        elif sort_by == "price":
            return [
                {"price_range": {"order": sort_order, "missing": "_last"}},
                {"rating": {"order": "desc"}},
            ]

        elif sort_by == "popular":
            return [
                {"visit_count": {"order": sort_order}},
                {"rating": {"order": "desc"}},
                {"review_count": {"order": "desc"}},
            ]

        elif sort_by == "name":
            return [{"name.raw": {"order": sort_order}}]

        else:  # relevance or default
            return [
                {"_score": {"order": "desc"}},
                {"created_at": {"order": "desc"}},
            ]

    def _build_facet_aggregations(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """패싯 집계 쿼리 빌드"""
        return {
            "categories": {"terms": {"field": "category", "size": 20}},
            "regions": {"terms": {"field": "district", "size": 30}},
            "tags": {"terms": {"field": "tags", "size": 50}},
            "price_ranges": {
                "range": {
                    "field": "price_range",
                    "ranges": [
                        {"key": "~10000", "to": 10000},
                        {"key": "10000-20000", "from": 10000, "to": 20000},
                        {"key": "20000-30000", "from": 20000, "to": 30000},
                        {"key": "30000-50000", "from": 30000, "to": 50000},
                        {"key": "50000+", "from": 50000},
                    ],
                }
            },
            "visit_status": {"terms": {"field": "visit_status", "size": 10}},
            "rating_ranges": {
                "range": {
                    "field": "rating",
                    "ranges": [
                        {"key": "4.5+", "from": 4.5},
                        {"key": "4.0-4.5", "from": 4.0, "to": 4.5},
                        {"key": "3.5-4.0", "from": 3.5, "to": 4.0},
                        {"key": "3.0-3.5", "from": 3.0, "to": 3.5},
                        {"key": "~3.0", "to": 3.0},
                    ],
                }
            },
        }

    def _build_highlight_config(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """하이라이트 설정 빌드"""
        return {
            "fields": {
                "name": {
                    "fragment_size": 100,
                    "number_of_fragments": 1,
                    "pre_tags": ["<em>"],
                    "post_tags": ["</em>"],
                },
                "description": {
                    "fragment_size": 150,
                    "number_of_fragments": 1,
                    "pre_tags": ["<em>"],
                    "post_tags": ["</em>"],
                },
                "address": {
                    "fragment_size": 100,
                    "number_of_fragments": 1,
                    "pre_tags": ["<em>"],
                    "post_tags": ["</em>"],
                },
            }
        }

    def _get_source_fields(self) -> List[str]:
        """검색 결과에 포함할 필드 목록"""
        return [
            "id",
            "name",
            "description",
            "address",
            "location",
            "category",
            "tags",
            "rating",
            "review_count",
            "price_range",
            "visit_status",
            "created_at",
            "updated_at",
            "visit_count",
        ]

    def _convert_elasticsearch_result(
        self,
        es_result: Dict[str, Any],
        filters: Dict[str, Any],
        include_facets: bool,
    ) -> Dict[str, Any]:
        """Elasticsearch 결과를 응답 형태로 변환"""
        hits = es_result.get("hits", {})
        total_hits = hits.get("total", {}).get("value", 0)

        # 장소 결과 변환
        places = []
        for hit in hits.get("hits", []):
            source = hit["_source"]
            place = {
                "id": source.get("id"),
                "name": source.get("name"),
                "description": source.get("description"),
                "address": source.get("address"),
                "location": source.get("location"),
                "category": source.get("category"),
                "tags": source.get("tags", []),
                "rating": source.get("rating"),
                "review_count": source.get("review_count"),
                "price_range": source.get("price_range"),
                "visit_status": source.get("visit_status"),
                "created_at": source.get("created_at"),
                "updated_at": source.get("updated_at"),
                "relevance_score": hit.get("_score"),
            }

            # 거리 정보 추가
            if "sort" in hit and filters.get("sort_by") == "distance":
                place["distance_km"] = round(hit["sort"][0], 2)

            # 하이라이트 정보 추가
            if "highlight" in hit:
                place["highlights"] = hit["highlight"]

            places.append(place)

        # 기본 결과 구조
        result = {
            "places": places,
            "total": total_hits,
            "query_info": {
                "took": es_result.get("took", 0),
                "total_hits": total_hits,
                "max_score": hits.get("max_score"),
                "source": "elasticsearch",
            },
            "applied_filters": filters,
        }

        # 패싯 정보 추가
        if include_facets and "aggregations" in es_result:
            result["facets"] = self._convert_facets(es_result["aggregations"], filters)

        # 빈 결과 처리
        if total_hits == 0:
            result["suggestions"] = self._generate_empty_result_suggestions(filters)

        return result

    def _convert_facets(
        self, aggregations: Dict[str, Any], applied_filters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """집계 결과를 패싯 형태로 변환"""
        facets = {}

        # 카테고리 패싯
        if "categories" in aggregations:
            facets["categories"] = [
                {
                    "name": bucket["key"],
                    "count": bucket["doc_count"],
                    "selected": bucket["key"] in applied_filters.get("categories", []),
                }
                for bucket in aggregations["categories"]["buckets"]
            ]

        # 지역 패싯
        if "regions" in aggregations:
            facets["regions"] = [
                {
                    "name": bucket["key"],
                    "count": bucket["doc_count"],
                    "selected": bucket["key"] in applied_filters.get("regions", []),
                }
                for bucket in aggregations["regions"]["buckets"]
            ]

        # 태그 패싯
        if "tags" in aggregations:
            facets["tags"] = [
                {
                    "name": bucket["key"],
                    "count": bucket["doc_count"],
                    "selected": bucket["key"] in applied_filters.get("tags", []),
                }
                for bucket in aggregations["tags"]["buckets"]
            ]

        # 가격대 패싯
        if "price_ranges" in aggregations:
            facets["price_ranges"] = [
                {
                    "name": bucket["key"],
                    "count": bucket["doc_count"],
                    "selected": bucket["key"]
                    in applied_filters.get("price_ranges", []),
                }
                for bucket in aggregations["price_ranges"]["buckets"]
                if bucket["doc_count"] > 0
            ]

        # 방문 상태 패싯
        if "visit_status" in aggregations:
            facets["visit_status"] = [
                {
                    "name": bucket["key"],
                    "count": bucket["doc_count"],
                    "selected": bucket["key"]
                    in applied_filters.get("visit_status", []),
                }
                for bucket in aggregations["visit_status"]["buckets"]
            ]

        # 평점 구간 패싯
        if "rating_ranges" in aggregations:
            facets["rating_ranges"] = [
                {
                    "name": bucket["key"],
                    "count": bucket["doc_count"],
                    "selected": False,  # TODO: 평점 필터 선택 상태 확인
                }
                for bucket in aggregations["rating_ranges"]["buckets"]
                if bucket["doc_count"] > 0
            ]

        return facets

    def _generate_empty_result_suggestions(
        self, filters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """빈 결과에 대한 제안 생성"""
        suggestions = {
            "message": "검색 조건을 완화해보세요",
            "alternative_filters": [],
            "popular_filters": [],
        }

        # 필터 완화 제안
        if filters.get("rating_min"):
            suggestions["alternative_filters"].append(
                {"remove_filter": "rating_min", "description": "평점 조건을 낮춰보세요"}
            )

        if filters.get("price_ranges"):
            suggestions["alternative_filters"].append(
                {"expand_filter": "price_ranges", "description": "가격대 범위를 넓혀보세요"}
            )

        if len(filters.get("tags", [])) > 2:
            suggestions["alternative_filters"].append(
                {"reduce_filter": "tags", "description": "태그 조건을 줄여보세요"}
            )

        if filters.get("location", {}).get("radius_km", 0) < 5:
            suggestions["alternative_filters"].append(
                {"expand_filter": "location", "description": "검색 반경을 넓혀보세요"}
            )

        return suggestions

    async def _fallback_postgresql_filter(
        self,
        user_id: UUID,
        filters: Dict[str, Any],
        limit: int,
        offset: int,
    ) -> Dict[str, Any]:
        """PostgreSQL 기반 fallback 필터링"""
        try:
            query = self.db.query(Place).filter(
                Place.user_id == user_id, Place.status == PlaceStatus.ACTIVE
            )

            # 기본 검색어 필터
            if filters.get("query"):
                search_term = f"%{filters['query']}%"
                query = query.filter(
                    or_(
                        Place.name.ilike(search_term),
                        Place.description.ilike(search_term),
                        Place.address.ilike(search_term),
                    )
                )

            # 카테고리 필터
            if filters.get("categories"):
                query = query.filter(Place.category.in_(filters["categories"]))

            # 지역 필터
            if filters.get("regions"):
                region_conditions = []
                for region in filters["regions"]:
                    region_pattern = f"%{region}%"
                    region_conditions.append(Place.address.ilike(region_pattern))
                query = query.filter(or_(*region_conditions))

            # 가격 필터
            if filters.get("price_min") or filters.get("price_max"):
                if filters.get("price_min"):
                    query = query.filter(Place.price_range >= filters["price_min"])
                if filters.get("price_max"):
                    query = query.filter(Place.price_range <= filters["price_max"])

            # 평점 필터
            if filters.get("rating_min"):
                query = query.filter(Place.rating >= filters["rating_min"])

            # 시간 필터
            if filters.get("created_after"):
                query = query.filter(Place.created_at >= filters["created_after"])

            if filters.get("created_before"):
                query = query.filter(Place.created_at <= filters["created_before"])

            # 정렬
            sort_by = filters.get("sort_by", "recent")
            if sort_by == "rating":
                query = query.order_by(Place.rating.desc().nullslast())
            elif sort_by == "recent":
                query = query.order_by(Place.created_at.desc())
            elif sort_by == "name":
                query = query.order_by(Place.name.asc())
            else:
                query = query.order_by(Place.created_at.desc())

            # 페이징
            total_count = query.count()
            places = query.offset(offset).limit(limit).all()

            # 결과 변환
            result_places = []
            for place in places:
                result_places.append(
                    {
                        "id": str(place.id),
                        "name": place.name,
                        "description": place.description,
                        "address": place.address,
                        "location": {
                            "lat": float(place.latitude) if place.latitude else None,
                            "lng": float(place.longitude) if place.longitude else None,
                        }
                        if place.latitude and place.longitude
                        else None,
                        "category": place.category,
                        "tags": place.tags or [],
                        "rating": place.rating,
                        "review_count": getattr(place, "review_count", 0),
                        "price_range": getattr(place, "price_range", None),
                        "visit_status": getattr(place, "visit_status", "wishlist"),
                        "created_at": place.created_at.isoformat()
                        if place.created_at
                        else None,
                        "updated_at": place.updated_at.isoformat()
                        if place.updated_at
                        else None,
                    }
                )

            return {
                "places": result_places,
                "total": total_count,
                "query_info": {
                    "source": "postgresql_fallback",
                    "total_hits": total_count,
                },
                "applied_filters": filters,
            }

        except Exception as e:
            logger.error(f"PostgreSQL fallback failed: {e}")
            return {
                "places": [],
                "total": 0,
                "query_info": {"source": "fallback_failed", "error": str(e)},
                "applied_filters": filters,
            }

    async def _post_process_results(
        self, result: Dict[str, Any], filters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """결과 후처리 (페이지네이션, 추가 정보 등)"""

        # 페이지네이션 정보 추가
        total = result.get("total", 0)
        limit = filters.get("limit", self.default_limit)
        offset = filters.get("offset", 0)

        result["pagination"] = {
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_next": offset + limit < total,
            "has_previous": offset > 0,
        }

        return result

    def _calculate_performance_metrics(
        self,
        start_time: datetime,
        cache_hit: bool = False,
        es_took: Optional[int] = None,
    ) -> Dict[str, Any]:
        """성능 메트릭 계산"""
        end_time = datetime.utcnow()
        total_time = (end_time - start_time).total_seconds() * 1000

        return {
            "total_time_ms": int(total_time),
            "cache_hit": cache_hit,
            "optimized": False,
            "elasticsearch_took": es_took,
        }

    def _generate_filter_cache_key(
        self,
        user_id: UUID,
        filters: Dict[str, Any],
        limit: int,
        offset: int,
    ) -> str:
        """필터 결과 캐시 키 생성"""
        cache_data = {
            "user_id": str(user_id),
            "filters": filters,
            "limit": limit,
            "offset": offset,
            "version": "v1",
        }

        cache_string = json.dumps(cache_data, sort_keys=True)
        cache_hash = hashlib.md5(
            cache_string.encode(), usedforsecurity=False
        ).hexdigest()  # nosec

        return f"filter_search:{cache_hash}"

    async def _get_cached_result(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """캐시된 결과 조회"""
        try:
            if not self.redis:
                return None

            cached_data = await self.redis.get(cache_key)
            if cached_data:
                return json.loads(cached_data)

            return None

        except Exception as e:
            logger.warning(f"Cache retrieval failed: {e}")
            return None

    async def _cache_result(self, cache_key: str, result: Dict[str, Any]) -> None:
        """결과 캐싱"""
        try:
            if not self.redis:
                return

            # 성능 정보는 캐싱에서 제외
            cache_result = {k: v for k, v in result.items() if k != "performance"}
            cache_result["cached"] = True

            await self.redis.setex(
                cache_key, self.cache_ttl, json.dumps(cache_result, default=str)
            )

        except Exception as e:
            logger.warning(f"Cache storage failed: {e}")

    async def _get_fallback_result(
        self, user_id: UUID, error: Exception
    ) -> Dict[str, Any]:
        """최종 fallback 결과"""
        return {
            "places": [],
            "total": 0,
            "pagination": {
                "total": 0,
                "limit": self.default_limit,
                "offset": 0,
                "has_next": False,
                "has_previous": False,
            },
            "query_info": {
                "source": "error_fallback",
                "error": str(error),
            },
            "suggestions": {
                "message": "서비스 일시 오류입니다. 잠시 후 다시 시도해주세요",
                "alternative_filters": [],
                "popular_filters": [],
            },
        }


# 의존성 주입용 팩토리 함수
def get_advanced_filter_service(
    db: Session, redis_client: Optional[redis.Redis] = None
) -> AdvancedFilterService:
    """고급 필터링 서비스 의존성"""
    return AdvancedFilterService(db, redis_client)
