#!/usr/bin/env python3
"""
Performance Tests for Place Schema Optimization

Tests database performance for geographical and text search operations
to ensure schema optimization meets performance targets:
- Geographical searches: < 50ms
- Text searches: < 100ms
- Complex queries: < 200ms

Follows TDD approach for Task 1-2-1: PostgreSQL 장소 스키마 및 인덱스 최적화
"""

import time

import pytest
from geoalchemy2 import func
from sqlalchemy import and_, text

from app.models.place import Place, PlaceCategory, PlaceStatus

# TODO(human): Implement performance test data generator
# Create test data generator that creates realistic place data for performance testing
# Consider: geographical distribution, text variety, realistic tags/categories


class TestPlaceSchemaPerformance:
    """
    Performance tests for Place model schema optimization.

    Validates that current database schema and indexes meet
    the performance targets defined in Task 1-2-1.
    """

    @pytest.fixture(autouse=True)
    async def setup_performance_data(self, db_session):
        """Setup test data for performance testing."""
        self.session = db_session

        # Create sample places for performance testing with user's input
        self.test_places = ["홍대입구역"]

        # Generate additional test places if needed
        await self._create_test_places()

        # Seoul coordinates for testing
        self.seoul_lat = 37.5665
        self.seoul_lng = 126.9780

        # Performance thresholds (in seconds)
        self.geo_search_threshold = 0.05  # 50ms
        self.text_search_threshold = 0.10  # 100ms
        self.complex_query_threshold = 0.20  # 200ms

    async def _create_test_places(self):
        """Create minimal test places for performance testing."""
        import uuid
        from datetime import datetime

        # Create a few test places around Seoul for performance testing
        test_places_data = [
            {
                "name": "홍대입구역 카페",
                "address": "서울특별시 마포구 홍익로",
                "category": PlaceCategory.CAFE,
                "lat": 37.5572,
                "lng": 126.9238,
            },
            {
                "name": "강남역 맛집",
                "address": "서울특별시 강남구 강남대로",
                "category": PlaceCategory.RESTAURANT,
                "lat": 37.4979,
                "lng": 127.0276,
            },
            {
                "name": "명동 쇼핑센터",
                "address": "서울특별시 중구 명동길",
                "category": PlaceCategory.SHOPPING,
                "lat": 37.5636,
                "lng": 126.9834,
            },
        ]

        for place_data in test_places_data:
            place = Place(
                id=uuid.uuid4(),
                user_id=uuid.uuid4(),
                name=place_data["name"],
                address=place_data["address"],
                category=place_data["category"],
                tags=["테스트", "성능"],
                status=PlaceStatus.ACTIVE,
                recommendation_score=85,
                ai_confidence=0.9,
                created_at=datetime.utcnow(),
            )
            place.set_coordinates(place_data["lat"], place_data["lng"])
            self.session.add(place)

        self.session.commit()

    async def measure_query_time(self, query_func) -> tuple:
        """Measure execution time of a database query."""
        start_time = time.perf_counter()
        result = await query_func()
        end_time = time.perf_counter()

        execution_time = end_time - start_time
        return execution_time, result

    @pytest.mark.asyncio
    async def test_geographical_search_performance_withinRadius_under50ms(self):
        """
        Test: Geographical search within radius completes under 50ms

        RED: This test should initially fail until schema is optimized
        """
        # Given: Search parameters for geographical query
        center_lat = self.seoul_lat
        center_lng = self.seoul_lng
        radius_km = 5.0

        async def geo_query():
            return (
                self.session.query(Place)
                .filter(
                    func.ST_DWithin(
                        Place.coordinates,
                        func.ST_GeogFromText(f"POINT({center_lng} {center_lat})"),
                        radius_km * 1000,  # Convert km to meters
                    )
                )
                .limit(100)
                .all()
            )

        # When: Execute geographical search
        execution_time, results = await self.measure_query_time(geo_query)

        # Then: Query should complete under 50ms
        assert (
            execution_time < self.geo_search_threshold
        ), f"Geographical search took {execution_time:.3f}s, expected < {self.geo_search_threshold}s"

        # Verify functional correctness
        assert isinstance(results, list)
        print(f"✅ Geographical search: {execution_time:.3f}s ({len(results)} results)")

    @pytest.mark.asyncio
    async def test_text_search_performance_koreanFullText_under100ms(self):
        """
        Test: Korean full-text search completes under 100ms

        RED: This test should initially fail until text search is optimized
        """
        # Given: Korean search terms
        search_terms = ["카페", "맛집", "서울역"]

        for search_term in search_terms:

            async def text_query():
                return (
                    self.session.query(Place)
                    .filter(
                        func.to_tsvector(
                            "korean", Place.name + " " + Place.address
                        ).match(func.plainto_tsquery("korean", search_term))
                    )
                    .limit(50)
                    .all()
                )

            # When: Execute text search
            execution_time, results = await self.measure_query_time(text_query)

            # Then: Query should complete under 100ms
            assert (
                execution_time < self.text_search_threshold
            ), f"Text search for '{search_term}' took {execution_time:.3f}s, expected < {self.text_search_threshold}s"

            print(
                f"✅ Text search '{search_term}': {execution_time:.3f}s ({len(results)} results)"
            )

    @pytest.mark.asyncio
    async def test_tag_search_performance_ginIndex_under50ms(self):
        """
        Test: Tag-based search using GIN index completes under 50ms

        RED: This test should initially fail until GIN indexes are optimized
        """
        # Given: Tag search parameters
        search_tags = ["카페", "디저트", "데이트"]

        for tag in search_tags:

            async def tag_query():
                return (
                    self.session.query(Place)
                    .filter(Place.tags.contains([tag]))
                    .limit(50)
                    .all()
                )

            # When: Execute tag search
            execution_time, results = await self.measure_query_time(tag_query)

            # Then: Query should complete under 50ms
            assert (
                execution_time < self.geo_search_threshold
            ), f"Tag search for '{tag}' took {execution_time:.3f}s, expected < {self.geo_search_threshold}s"

            print(
                f"✅ Tag search '{tag}': {execution_time:.3f}s ({len(results)} results)"
            )

    @pytest.mark.asyncio
    async def test_complex_query_performance_multipleFilters_under200ms(self):
        """
        Test: Complex query with multiple filters completes under 200ms

        RED: This test should initially fail until composite indexes are optimized
        """
        # Given: Complex query parameters
        user_id = "test-user-uuid"
        category = PlaceCategory.RESTAURANT

        async def complex_query():
            return (
                self.session.query(Place)
                .filter(
                    and_(
                        Place.user_id == user_id,
                        Place.category == category,
                        Place.status == PlaceStatus.ACTIVE,
                        Place.recommendation_score > 70,
                        func.ST_DWithin(
                            Place.coordinates,
                            func.ST_GeogFromText(
                                f"POINT({self.seoul_lng} {self.seoul_lat})"
                            ),
                            10000,  # 10km radius
                        ),
                    )
                )
                .order_by(Place.recommendation_score.desc())
                .limit(20)
                .all()
            )

        # When: Execute complex query
        execution_time, results = await self.measure_query_time(complex_query)

        # Then: Query should complete under 200ms
        assert (
            execution_time < self.complex_query_threshold
        ), f"Complex query took {execution_time:.3f}s, expected < {self.complex_query_threshold}s"

        print(f"✅ Complex query: {execution_time:.3f}s ({len(results)} results)")

    @pytest.mark.asyncio
    async def test_index_usage_analysis_allQueries_useIndexes(self):
        """
        Test: Verify that all queries use appropriate indexes

        Analyzes query execution plans to ensure indexes are being used
        """
        # Given: Sample queries to analyze
        queries_to_analyze = [
            # Geographical query
            f"""
            EXPLAIN (ANALYZE, BUFFERS)
            SELECT * FROM places
            WHERE ST_DWithin(coordinates, ST_GeogFromText('POINT({self.seoul_lng} {self.seoul_lat})'), 5000)
            LIMIT 10;
            """,
            # Text search query
            """
            EXPLAIN (ANALYZE, BUFFERS)
            SELECT * FROM places
            WHERE to_tsvector('korean', name || ' ' || COALESCE(address, '')) @@ plainto_tsquery('korean', '카페')
            LIMIT 10;
            """,
            # Tag search query
            """
            EXPLAIN (ANALYZE, BUFFERS)
            SELECT * FROM places
            WHERE tags @> ARRAY['카페']
            LIMIT 10;
            """,
        ]

        for query in queries_to_analyze:
            # When: Execute query plan analysis
            result = self.session.execute(text(query))
            plan = result.fetchall()

            # Then: Verify index usage in execution plan
            plan_text = "\n".join([str(row[0]) for row in plan])

            # Should use indexes, not sequential scans for large tables
            assert (
                "Index Scan" in plan_text or "Bitmap Index Scan" in plan_text
            ), f"Query should use index scan, but plan shows: {plan_text}"

            print(f"✅ Query uses indexes: {plan_text.split('->')[0].strip()}")


class TestPlaceSchemaIndexOptimization:
    """
    Tests for specific index optimization scenarios.

    Validates that database indexes are properly configured
    for common query patterns.
    """

    def test_index_definitions_allRequired_exist(self, db_session):
        """
        Test: All required indexes exist in database schema

        GREEN: Verify that required indexes are created by migration
        """
        # Given: List of required indexes
        required_indexes = [
            "idx_places_user_id",
            "idx_places_coordinates_gist",
            "idx_places_tags_gin",
            "idx_places_search_gin",
            "idx_places_user_category_created",
            "idx_places_recommendation",
            "idx_places_duplicate",
        ]

        # When: Query database for existing indexes
        for index_name in required_indexes:
            result = db_session.execute(
                text(
                    f"""
                SELECT indexname FROM pg_indexes
                WHERE indexname = '{index_name}' AND tablename = 'places'
            """
                )
            )

            # Then: Index should exist
            indexes = result.fetchall()
            assert len(indexes) > 0, f"Required index '{index_name}' not found"

        print(f"✅ All {len(required_indexes)} required indexes exist")

    def test_postgis_extension_enabled_geographicalQueries_supported(self, db_session):
        """
        Test: PostGIS extension is enabled for geographical operations

        GREEN: Verify PostGIS functions are available
        """
        # When: Test PostGIS function availability
        result = db_session.execute(text("SELECT ST_Point(126.9780, 37.5665)"))
        point = result.fetchone()

        # Then: PostGIS function should work
        assert point is not None
        print("✅ PostGIS extension is properly enabled")

    def test_korean_text_search_configuration_koreanDictionary_available(
        self, db_session
    ):
        """
        Test: Korean text search configuration is available

        GREEN: Verify Korean dictionary support
        """
        # When: Test Korean text search configuration
        result = db_session.execute(
            text(
                """
            SELECT to_tsvector('korean', '한국어 카페 맛집 테스트')
        """
            )
        )
        vector = result.fetchone()

        # Then: Korean tokenization should work
        assert vector is not None
        assert "카페" in str(vector[0]) or "맛집" in str(vector[0])
        print("✅ Korean text search configuration is working")


# Performance test fixtures and utilities
@pytest.fixture
async def performance_test_data():
    """Generate test data for performance testing."""
    # This would create a substantial dataset for realistic performance testing
    # Implementation will be provided by human


@pytest.mark.performance
class TestPlaceSchemaScalability:
    """
    Scalability tests for Place schema with large datasets.

    Tests performance degradation with increasing data volumes.
    """

    @pytest.mark.slow
    async def test_scalability_largeDataset_maintainPerformance(self):
        """
        Test: Performance is maintained with large datasets

        This test will validate that schema performs well with
        realistic data volumes (10k+ places)
        """
        # This test will be implemented after basic performance tests pass
        pytest.skip("Scalability test - implement after basic performance optimization")

    @pytest.mark.slow
    async def test_concurrent_access_multipleUsers_noPerformanceDegradation(self):
        """
        Test: Concurrent access doesn't degrade performance

        Simulates multiple users accessing place data simultaneously
        """
        # This test will be implemented for concurrent load testing
        pytest.skip("Concurrent access test - implement after basic optimization")
