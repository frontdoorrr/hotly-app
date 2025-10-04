"""Advanced search service with Korean text analysis and Elasticsearch support."""

import logging
import re
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.elasticsearch import es_manager
from app.models.place import Place, PlaceStatus
from app.services.search.search_schemas import SearchIndexSchemas
from app.utils.korean_analyzer import KoreanAnalyzer

logger = logging.getLogger(__name__)


class SearchService:
    """Advanced search service with Korean support, fuzzy matching, and Elasticsearch."""

    def __init__(self, db: Session):
        self.db = db
        self.korean_analyzer = KoreanAnalyzer()
        self.schemas = SearchIndexSchemas()

    async def initialize_elasticsearch_indices(self) -> None:
        """Initialize Elasticsearch indices for enhanced search."""
        try:
            # Ensure Elasticsearch connection is established
            if not es_manager.client:
                await es_manager.connect()

            # Get all schemas
            all_schemas = self.schemas.get_all_schemas()

            # Create indices
            for index_name, schema_config in all_schemas.items():
                await es_manager.create_index(
                    index_name=index_name,
                    mapping=schema_config["mapping"],
                    settings_dict=schema_config["settings"],
                )

            logger.info("Successfully initialized all search indices")

        except Exception as e:
            logger.error(f"Failed to initialize search indices: {e}")
            raise

    async def index_place_to_elasticsearch(self, place: Place) -> bool:
        """Index a place to Elasticsearch for enhanced search."""
        try:
            # Prepare document for indexing
            doc = self._prepare_place_document(place)

            # Index document
            doc_id = await es_manager.index_document(
                index_name="places", document=doc, doc_id=str(place.id)
            )

            logger.info(f"Indexed place to Elasticsearch: {doc_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to index place to Elasticsearch: {e}")
            return False

    def _prepare_place_document(self, place: Place) -> Dict[str, any]:
        """Prepare place data for Elasticsearch indexing."""
        # Extract location coordinates
        location = None
        if place.latitude and place.longitude:
            location = {"lat": float(place.latitude), "lon": float(place.longitude)}

        # Prepare search keywords by combining various fields
        search_keywords = []
        for field in [place.name, place.description, place.address, place.category]:
            if field:
                search_keywords.append(str(field))

        # Add tags
        if place.tags:
            search_keywords.extend(place.tags)

        return {
            "id": str(place.id),
            "user_id": str(place.user_id),
            "name": place.name or "",
            "description": place.description or "",
            "address": place.address or "",
            "location": location,
            "district": getattr(place, "district", None),
            "city": getattr(place, "city", None),
            "category": place.category,
            "tags": place.tags or [],
            "auto_category": getattr(place, "auto_category", None),
            "status": place.status.value if place.status else "active",
            "rating": getattr(place, "rating", None),
            "visit_count": getattr(place, "visit_count", 0),
            "last_visited_at": place.last_visited_at.isoformat()
            if place.last_visited_at
            else None,
            "created_at": place.created_at.isoformat() if place.created_at else None,
            "updated_at": place.updated_at.isoformat() if place.updated_at else None,
            "popularity_score": getattr(place, "popularity_score", 0.0),
            "relevance_score": 1.0,
            "search_keywords": " ".join(search_keywords),
        }

    async def elasticsearch_search_places(
        self,
        user_id: UUID,
        query: str = "",
        location: Optional[Dict[str, float]] = None,
        radius_km: Optional[float] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        sort_by: str = "relevance",
        limit: int = 20,
        offset: int = 0,
    ) -> Dict[str, any]:
        """
        Advanced search using Elasticsearch with Korean language support.
        """
        try:
            # Build search query
            search_query = self._build_elasticsearch_query(
                user_id=user_id,
                query=query,
                location=location,
                radius_km=radius_km,
                category=category,
                tags=tags,
            )

            # Build sort configuration
            sort_config = self._build_sort_config(sort_by, location)

            # Execute search
            result = await es_manager.search(
                index_name="places",
                query=search_query,
                size=limit,
                from_=offset,
                sort=sort_config,
            )

            # Process results
            return self._process_elasticsearch_results(result, query)

        except Exception as e:
            logger.error(f"Elasticsearch search failed: {e}")
            # Fall back to PostgreSQL search
            postgres_results = self.full_text_search(user_id, query, category, limit)
            return {
                "places": [
                    {"place": place, "score": score}
                    for place, score in postgres_results
                ],
                "total": len(postgres_results),
                "query": query,
                "source": "postgresql_fallback",
            }

    def _build_elasticsearch_query(
        self,
        user_id: UUID,
        query: str = "",
        location: Optional[Dict[str, float]] = None,
        radius_km: Optional[float] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> Dict[str, any]:
        """Build Elasticsearch query for place search."""

        must_clauses = []
        filter_clauses = []

        # User filter
        filter_clauses.append({"term": {"user_id": str(user_id)}})

        # Text search query with Korean support
        if query:
            must_clauses.append(
                {
                    "multi_match": {
                        "query": query,
                        "fields": [
                            "name^3",
                            "name.ngram^2",
                            "description^1.5",
                            "address^2",
                            "search_keywords^1.2",
                            "tags.text^1.5",
                        ],
                        "type": "best_fields",
                        "fuzziness": "AUTO",
                        "minimum_should_match": "75%",
                    }
                }
            )

        # Geographic search
        if location and radius_km:
            filter_clauses.append(
                {"geo_distance": {"distance": f"{radius_km}km", "location": location}}
            )

        # Category filter
        if category:
            filter_clauses.append({"term": {"category": category}})

        # Tags filter
        if tags:
            filter_clauses.append({"terms": {"tags": tags}})

        # Status filter (only active places)
        filter_clauses.append({"term": {"status": "active"}})

        # Build final query
        if must_clauses or filter_clauses:
            search_query = {"bool": {"must": must_clauses, "filter": filter_clauses}}
        else:
            search_query = {"match_all": {}}

        # Add function score for relevance boosting
        return {
            "function_score": {
                "query": search_query,
                "functions": [
                    {
                        "field_value_factor": {
                            "field": "popularity_score",
                            "factor": 1.5,
                            "modifier": "log1p",
                            "missing": 0,
                        }
                    },
                    {
                        "field_value_factor": {
                            "field": "visit_count",
                            "factor": 0.01,
                            "modifier": "log1p",
                            "missing": 0,
                        }
                    },
                ],
                "score_mode": "multiply",
                "boost_mode": "multiply",
            }
        }

    def _build_sort_config(
        self, sort_by: str, location: Optional[Dict[str, float]] = None
    ) -> List[Dict[str, any]]:
        """Build sort configuration for search results."""
        sort_configs = {
            "relevance": [{"_score": {"order": "desc"}}],
            "recent": [
                {"created_at": {"order": "desc"}},
                {"_score": {"order": "desc"}},
            ],
            "distance": [],
            "name": [{"name.keyword": {"order": "asc"}}, {"_score": {"order": "desc"}}],
        }

        # Add distance sort if location provided
        if sort_by == "distance" and location:
            sort_configs["distance"] = [
                {"_geo_distance": {"location": location, "order": "asc", "unit": "km"}},
                {"_score": {"order": "desc"}},
            ]

        return sort_configs.get(sort_by, sort_configs["relevance"])

    def _process_elasticsearch_results(
        self, result: Dict[str, any], query: str = ""
    ) -> Dict[str, any]:
        """Process Elasticsearch results into application format."""
        hits = result.get("hits", {})
        total_hits = hits.get("total", {}).get("value", 0)

        places = []
        for hit in hits.get("hits", []):
            source = hit["_source"]
            place_data = {
                "id": source.get("id"),
                "name": source.get("name"),
                "description": source.get("description"),
                "address": source.get("address"),
                "location": source.get("location"),
                "category": source.get("category"),
                "tags": source.get("tags", []),
                "score": hit.get("_score"),
            }

            # Add distance if geo sort was used
            if hit.get("sort") and len(hit["sort"]) > 0:
                try:
                    distance = float(hit["sort"][0])
                    if distance < 999999:  # Valid distance value
                        place_data["distance_km"] = round(distance, 2)
                except (ValueError, IndexError):
                    pass

            places.append(place_data)

        return {
            "places": places,
            "total": total_hits,
            "query": query,
            "took": result.get("took"),
            "timed_out": result.get("timed_out", False),
            "source": "elasticsearch",
        }

    async def get_elasticsearch_suggestions(
        self,
        user_id: UUID,
        query: str,
        categories: Optional[List[str]] = None,
        limit: int = 10,
    ) -> List[Dict[str, any]]:
        """Get search suggestions using Elasticsearch."""
        try:
            search_query = {
                "multi_match": {
                    "query": query,
                    "fields": ["name.suggest", "address.suggest"],
                    "type": "bool_prefix",
                }
            }

            filter_clauses = [
                {"term": {"user_id": str(user_id)}},
                {"term": {"status": "active"}},
            ]

            if categories:
                filter_clauses.append({"terms": {"category": categories}})

            final_query = {"bool": {"must": [search_query], "filter": filter_clauses}}

            result = await es_manager.search(
                index_name="places",
                query=final_query,
                size=limit,
                from_=0,
            )

            suggestions = []
            for hit in result.get("hits", {}).get("hits", []):
                source = hit["_source"]
                suggestions.append(
                    {
                        "text": source.get("name"),
                        "type": "place",
                        "category": source.get("category"),
                        "address": source.get("address"),
                        "score": hit.get("_score"),
                    }
                )

            return suggestions

        except Exception as e:
            logger.error(f"Failed to get Elasticsearch suggestions: {e}")
            # Fall back to PostgreSQL autocomplete
            return [
                {"text": suggestion, "type": "place", "score": 1.0}
                for suggestion in self.autocomplete_suggestions(user_id, query, limit)
            ]

    def full_text_search(
        self,
        user_id: UUID,
        query: str,
        category: Optional[str] = None,
        limit: int = 20,
        enable_fuzzy: bool = True,
    ) -> List[Tuple[Place, float]]:
        """
        Perform full-text search with Korean analysis and ranking.

        Args:
            user_id: User identifier
            query: Search query
            category: Optional category filter
            limit: Maximum results
            enable_fuzzy: Enable fuzzy matching for typos

        Returns:
            List of (Place, relevance_score) tuples
        """
        try:
            # Analyze Korean query
            analyzed_query = self.korean_analyzer.analyze_text(query)
            search_terms = analyzed_query.get("keywords", [query])

            # Build base query
            base_query = self.db.query(Place).filter(
                Place.user_id == user_id, Place.status == PlaceStatus.ACTIVE
            )

            if category:
                base_query = base_query.filter(Place.category == category)

            # PostgreSQL full-text search with Korean configuration
            search_vector = func.to_tsvector(
                "korean",
                func.coalesce(Place.name, "")
                + " "
                + func.coalesce(Place.description, "")
                + " "
                + func.coalesce(Place.address, ""),
            )

            # Create search query for multiple terms
            ts_queries = []
            for term in search_terms:
                ts_queries.append(func.plainto_tsquery("korean", term))

            # Combine queries with OR
            combined_query = ts_queries[0]
            for ts_query in ts_queries[1:]:
                combined_query = combined_query.op("||")(ts_query)

            # Execute search with ranking
            results = (
                base_query.filter(search_vector.op("@@")(combined_query))
                .add_columns(func.ts_rank(search_vector, combined_query).label("rank"))
                .order_by(func.ts_rank(search_vector, combined_query).desc())
                .limit(limit)
                .all()
            )

            places_with_scores = [(place, float(rank)) for place, rank in results]

            # Apply fuzzy matching if no results and enabled
            if not places_with_scores and enable_fuzzy:
                places_with_scores = self._fuzzy_search_fallback(
                    user_id, query, category, limit
                )

            logger.info(
                f"Full-text search for '{query}': {len(places_with_scores)} results"
            )
            return places_with_scores

        except Exception as e:
            logger.error(f"Error in full-text search: {e}")
            raise

    def autocomplete_suggestions(
        self, user_id: UUID, partial_query: str, limit: int = 10
    ) -> List[str]:
        """
        Generate autocomplete suggestions for partial queries.

        Args:
            user_id: User identifier
            partial_query: Partial search query
            limit: Maximum suggestions

        Returns:
            List of autocomplete suggestions
        """
        try:
            # Get places for text extraction
            places = (
                self.db.query(Place)
                .filter(Place.user_id == user_id, Place.status == PlaceStatus.ACTIVE)
                .all()
            )

            suggestions = set()

            # Extract suggestions from place names and descriptions
            for place in places:
                # Name suggestions
                if place.name and partial_query.lower() in place.name.lower():
                    suggestions.add(place.name)

                # Description word suggestions
                if place.description:
                    words = self.korean_analyzer.extract_keywords(place.description)
                    for word in words:
                        if partial_query.lower() in word.lower():
                            suggestions.add(word)

            # Sort by relevance (length and frequency)
            sorted_suggestions = sorted(
                list(suggestions),
                key=lambda x: (
                    len(x),
                    (
                        x.lower().index(partial_query.lower())
                        if partial_query.lower() in x.lower()
                        else 999
                    ),
                ),
            )

            logger.info(
                f"Autocomplete for '{partial_query}': {len(sorted_suggestions)} suggestions"
            )
            return sorted_suggestions[:limit]

        except Exception as e:
            logger.error(f"Error in autocomplete: {e}")
            return []

    def highlight_search_terms(
        self, text: str, query: str, highlight_tag: str = "mark"
    ) -> str:
        """
        Highlight search terms in text.

        Args:
            text: Text to highlight
            query: Search query
            highlight_tag: HTML tag for highlighting

        Returns:
            Text with highlighted search terms
        """
        try:
            if not text or not query:
                return text

            # Analyze query terms
            analyzed_query = self.korean_analyzer.analyze_text(query)
            terms = analyzed_query.get("keywords", [query])

            highlighted_text = text

            # Highlight each term
            for term in terms:
                if len(term) >= 2:  # Only highlight terms with 2+ characters
                    pattern = re.compile(re.escape(term), re.IGNORECASE)
                    highlighted_text = pattern.sub(
                        f"<{highlight_tag}>\\g<0></{highlight_tag}>", highlighted_text
                    )

            return highlighted_text

        except Exception as e:
            logger.error(f"Error in search highlighting: {e}")
            return text

    def _fuzzy_search_fallback(
        self, user_id: UUID, query: str, category: Optional[str] = None, limit: int = 20
    ) -> List[Tuple[Place, float]]:
        """
        Fallback fuzzy search when exact search returns no results.

        Uses similarity matching for handling typos and variations.
        """
        try:
            # Use PostgreSQL similarity functions
            base_query = self.db.query(Place).filter(
                Place.user_id == user_id, Place.status == PlaceStatus.ACTIVE
            )

            if category:
                base_query = base_query.filter(Place.category == category)

            # Calculate similarity scores for fuzzy matching
            similarity_expr = func.greatest(
                func.similarity(Place.name, query),
                func.similarity(func.coalesce(Place.description, ""), query),
                func.similarity(func.coalesce(Place.address, ""), query),
            )

            # Filter by minimum similarity threshold (0.3)
            results = (
                base_query.filter(similarity_expr > 0.3)
                .add_columns(similarity_expr.label("similarity"))
                .order_by(similarity_expr.desc())
                .limit(limit)
                .all()
            )

            places_with_scores = [
                (place, float(similarity)) for place, similarity in results
            ]

            logger.info(
                f"Fuzzy search for '{query}': {len(places_with_scores)} results"
            )
            return places_with_scores

        except Exception as e:
            logger.error(f"Error in fuzzy search: {e}")
            return []

    def search_with_boost(
        self,
        user_id: UUID,
        query: str,
        boost_factors: Optional[Dict[str, float]] = None,
        limit: int = 20,
    ) -> List[Tuple[Place, float]]:
        """
        Search with customizable boost factors for different fields.

        Args:
            user_id: User identifier
            query: Search query
            boost_factors: Field boost weights (name, description, tags, etc.)
            limit: Maximum results

        Returns:
            List of (Place, boosted_score) tuples
        """
        try:
            if boost_factors is None:
                boost_factors = {
                    "name": 3.0,  # Name matches are most important
                    "tags": 2.0,  # Tag matches are important
                    "description": 1.0,  # Description matches baseline
                    "address": 0.5,  # Address matches least important
                }

            # Build weighted search expression
            ts_query = func.plainto_tsquery("korean", query)

            # Separate tsvectors for different fields with weights
            name_vector = func.setweight(
                func.to_tsvector("korean", func.coalesce(Place.name, "")), "A"
            )
            tag_vector = func.setweight(
                func.to_tsvector("korean", func.array_to_string(Place.tags, " ")), "B"
            )
            desc_vector = func.setweight(
                func.to_tsvector("korean", func.coalesce(Place.description, "")), "C"
            )
            addr_vector = func.setweight(
                func.to_tsvector("korean", func.coalesce(Place.address, "")), "D"
            )

            # Combine all vectors
            combined_vector = (
                name_vector.op("||")(tag_vector)
                .op("||")(desc_vector)
                .op("||")(addr_vector)
            )

            # Execute search with custom ranking
            results = (
                self.db.query(Place)
                .filter(
                    Place.user_id == user_id,
                    Place.status == PlaceStatus.ACTIVE,
                    combined_vector.op("@@")(ts_query),
                )
                .add_columns(func.ts_rank_cd(combined_vector, ts_query).label("score"))
                .order_by(func.ts_rank_cd(combined_vector, ts_query).desc())
                .limit(limit)
                .all()
            )

            places_with_scores = [(place, float(score)) for place, score in results]

            logger.info(
                f"Boosted search for '{query}': {len(places_with_scores)} results"
            )
            return places_with_scores

        except Exception as e:
            logger.error(f"Error in boosted search: {e}")
            raise
