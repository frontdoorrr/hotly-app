"""Advanced search service with Korean text analysis."""

import logging
import re
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.place import Place, PlaceStatus
from app.utils.korean_analyzer import KoreanAnalyzer

logger = logging.getLogger(__name__)


class SearchService:
    """Advanced search service with Korean support and fuzzy matching."""

    def __init__(self, db: Session):
        self.db = db
        self.korean_analyzer = KoreanAnalyzer()

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
