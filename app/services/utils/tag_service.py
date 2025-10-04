"""Tag management service for places."""

import logging
from collections import Counter
from typing import Dict, List, Optional
from uuid import UUID

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.models.place import Place, PlaceStatus
from app.utils.tag_normalizer import TagNormalizer

logger = logging.getLogger(__name__)


class TagService:
    """Service for managing place tags and providing suggestions."""

    def __init__(self, db: Session):
        """Initialize tag service with database session."""
        self.db = db
        self.normalizer = TagNormalizer()

    def get_tag_suggestions(
        self, query: str, user_id: UUID, limit: int = 10
    ) -> List[Dict[str, any]]:
        """
        Get tag auto-completion suggestions based on query.

        Args:
            query: Partial tag input from user
            user_id: User ID for personalized suggestions
            limit: Maximum number of suggestions

        Returns:
            List of tag suggestions with usage statistics
        """
        if not query or len(query) < 2:
            return self.get_popular_tags(user_id, limit)

        normalized_query = self.normalizer.normalize_tag(query)
        if not normalized_query:
            return []

        # Get user's existing tags that match query
        user_tags = self._get_user_tags_with_stats(user_id)

        # Find matching tags
        suggestions = []
        for tag_data in user_tags:
            tag = tag_data["tag"]

            # Check if query matches tag (prefix or contains)
            if tag.startswith(normalized_query) or normalized_query in tag:
                suggestions.append(
                    {
                        "tag": tag,
                        "usage_count": tag_data["count"],
                        "match_type": (
                            "prefix" if tag.startswith(normalized_query) else "contains"
                        ),
                    }
                )

        # Get similar tags if not enough exact matches
        if len(suggestions) < limit:
            all_system_tags = self._get_all_system_tags()
            similar_tags = self.normalizer.suggest_similar_tags(
                normalized_query, all_system_tags
            )

            for similar_tag in similar_tags:
                if similar_tag not in [s["tag"] for s in suggestions]:
                    suggestions.append(
                        {"tag": similar_tag, "usage_count": 0, "match_type": "similar"}
                    )

        # Sort by usage count and match type priority
        suggestions.sort(
            key=lambda x: (
                x["match_type"] == "prefix",  # Prefix matches first
                x["usage_count"],
            ),
            reverse=True,
        )

        return suggestions[:limit]

    def get_popular_tags(self, user_id: UUID, limit: int = 10) -> List[Dict[str, any]]:
        """
        Get popular tags for the user.

        Args:
            user_id: User ID
            limit: Maximum number of tags to return

        Returns:
            List of popular tags with statistics
        """
        user_tags = self._get_user_tags_with_stats(user_id, limit)

        return [
            {
                "tag": tag_data["tag"],
                "usage_count": tag_data["count"],
                "match_type": "popular",
            }
            for tag_data in user_tags
        ]

    def add_tags_to_place(
        self, place_id: UUID, user_id: UUID, tags: List[str]
    ) -> List[str]:
        """
        Add normalized tags to a place.

        Args:
            place_id: Place ID
            user_id: User ID (for ownership verification)
            tags: List of tags to add

        Returns:
            List of successfully added normalized tags
        """
        if not tags:
            return []

        # Get place and verify ownership
        place = (
            self.db.query(Place)
            .filter(and_(Place.id == place_id, Place.user_id == user_id))
            .first()
        )

        if not place:
            raise ValueError(f"Place {place_id} not found or access denied")

        # Normalize tags
        normalized_tags = self.normalizer.normalize_tags(tags)

        # Add tags to place
        added_tags = []
        for tag in normalized_tags:
            if not place.tags or tag not in place.tags:
                place.add_tag(tag)
                added_tags.append(tag)

        # Update tag usage statistics
        self._update_tag_statistics(user_id, added_tags)

        self.db.commit()
        logger.info(f"Added {len(added_tags)} tags to place {place_id}")

        return added_tags

    def remove_tags_from_place(
        self, place_id: UUID, user_id: UUID, tags: List[str]
    ) -> List[str]:
        """
        Remove tags from a place.

        Args:
            place_id: Place ID
            user_id: User ID (for ownership verification)
            tags: List of tags to remove

        Returns:
            List of successfully removed tags
        """
        if not tags:
            return []

        # Get place and verify ownership
        place = (
            self.db.query(Place)
            .filter(and_(Place.id == place_id, Place.user_id == user_id))
            .first()
        )

        if not place:
            raise ValueError(f"Place {place_id} not found or access denied")

        # Remove tags from place
        removed_tags = []
        for tag in tags:
            normalized_tag = self.normalizer.normalize_tag(tag)
            if place.remove_tag(normalized_tag):
                removed_tags.append(normalized_tag)

        self.db.commit()
        logger.info(f"Removed {len(removed_tags)} tags from place {place_id}")

        return removed_tags

    def get_tag_statistics(self, user_id: UUID) -> Dict[str, any]:
        """
        Get comprehensive tag usage statistics for user.

        Args:
            user_id: User ID

        Returns:
            Dictionary with tag statistics
        """
        # Get all user's places with tags
        places = (
            self.db.query(Place)
            .filter(and_(Place.user_id == user_id, Place.status == PlaceStatus.ACTIVE))
            .all()
        )

        if not places:
            return {
                "total_unique_tags": 0,
                "total_tag_usage": 0,
                "most_used_tags": [],
                "tag_categories": {},
                "average_tags_per_place": 0.0,
            }

        # Collect all tags with counts
        all_tags = []
        for place in places:
            if place.tags:
                all_tags.extend(place.tags)

        tag_counts = Counter(all_tags)

        # Calculate statistics
        total_unique_tags = len(tag_counts)
        total_tag_usage = sum(tag_counts.values())
        average_tags_per_place = total_tag_usage / len(places)

        # Get most used tags
        most_used_tags = [
            {"tag": tag, "count": count} for tag, count in tag_counts.most_common(20)
        ]

        # Categorize tags
        tag_categories = self.normalizer.categorize_tags(list(tag_counts.keys()))

        return {
            "total_unique_tags": total_unique_tags,
            "total_tag_usage": total_tag_usage,
            "most_used_tags": most_used_tags,
            "tag_categories": tag_categories,
            "average_tags_per_place": round(average_tags_per_place, 2),
            "places_count": len(places),
        }

    def suggest_tags_for_place(
        self,
        place_name: str,
        place_description: Optional[str],
        user_id: UUID,
        max_suggestions: int = 5,
    ) -> List[str]:
        """
        Suggest tags for a place based on name, description, and user's tag history.

        Args:
            place_name: Name of the place
            place_description: Optional description
            user_id: User ID for personalized suggestions
            max_suggestions: Maximum number of suggestions

        Returns:
            List of suggested tags
        """
        suggestions = set()

        # Extract from place name
        name_tags = self.normalizer.extract_tags_from_text(place_name, max_tags=3)
        suggestions.update(name_tags)

        # Extract from description if provided
        if place_description:
            desc_tags = self.normalizer.extract_tags_from_text(
                place_description, max_tags=3
            )
            suggestions.update(desc_tags)

        # Add popular user tags if space available
        if len(suggestions) < max_suggestions:
            popular_tags = self.get_popular_tags(user_id, limit=10)
            for tag_data in popular_tags:
                suggestions.add(tag_data["tag"])
                if len(suggestions) >= max_suggestions:
                    break

        return list(suggestions)[:max_suggestions]

    def merge_duplicate_tags(self, user_id: UUID) -> Dict[str, any]:
        """
        Find and merge duplicate/similar tags across user's places.

        Args:
            user_id: User ID

        Returns:
            Summary of merge operations
        """
        # Get all user's tags
        user_tags = self._get_user_tags_with_stats(user_id)
        all_tags = [tag_data["tag"] for tag_data in user_tags]

        merge_operations = []
        processed_tags = set()

        for tag in all_tags:
            if tag in processed_tags:
                continue

            # Find similar tags
            similar_tags = self.normalizer.suggest_similar_tags(tag, all_tags)

            if similar_tags:
                # Choose the most used tag as canonical
                candidates = [tag] + similar_tags
                canonical_tag = max(
                    candidates,
                    key=lambda t: next(
                        (td["count"] for td in user_tags if td["tag"] == t), 0
                    ),
                )

                # Track merge operation
                if len(candidates) > 1:
                    merge_operations.append(
                        {
                            "canonical": canonical_tag,
                            "merged": [t for t in candidates if t != canonical_tag],
                        }
                    )

                    # Perform merge in database
                    self._merge_tags(user_id, canonical_tag, candidates)

                processed_tags.update(candidates)

        return {
            "merges_performed": len(merge_operations),
            "operations": merge_operations,
        }

    def _get_user_tags_with_stats(
        self, user_id: UUID, limit: Optional[int] = None
    ) -> List[Dict]:
        """Get user's tags with usage statistics."""
        # Query to get all tags used by user with counts
        query = (
            self.db.query(
                func.unnest(Place.tags).label("tag"), func.count().label("count")
            )
            .filter(and_(Place.user_id == user_id, Place.status == PlaceStatus.ACTIVE))
            .group_by("tag")
            .order_by(func.count().desc())
        )

        if limit:
            query = query.limit(limit)

        results = query.all()

        return [
            {"tag": row.tag, "count": row.count}
            for row in results
            if row.tag  # Filter out null/empty tags
        ]

    def _get_all_system_tags(self, limit: int = 1000) -> List[str]:
        """Get all tags used in the system."""
        # Get most common tags across all users
        query = (
            self.db.query(func.unnest(Place.tags).label("tag"))
            .filter(Place.status == PlaceStatus.ACTIVE)
            .group_by("tag")
            .order_by(func.count().desc())
            .limit(limit)
        )

        results = query.all()
        return [row.tag for row in results if row.tag]

    def _update_tag_statistics(self, user_id: UUID, tags: List[str]) -> None:
        """Update tag usage statistics (placeholder for future statistics table)."""
        # For now, this is handled by the place model's tags array
        # In the future, we might want a separate tag_statistics table
        logger.info(f"Updated tag statistics for user {user_id}: {tags}")

    def _merge_tags(
        self, user_id: UUID, canonical_tag: str, tags_to_merge: List[str]
    ) -> None:
        """Merge similar tags into canonical tag."""
        places = (
            self.db.query(Place)
            .filter(and_(Place.user_id == user_id, Place.status == PlaceStatus.ACTIVE))
            .all()
        )

        updated_places = 0

        for place in places:
            if not place.tags:
                continue

            updated = False
            new_tags = []

            for tag in place.tags:
                if tag in tags_to_merge and tag != canonical_tag:
                    if canonical_tag not in new_tags:
                        new_tags.append(canonical_tag)
                    updated = True
                else:
                    new_tags.append(tag)

            if updated:
                place.tags = new_tags
                updated_places += 1

        if updated_places > 0:
            self.db.commit()
            logger.info(
                f"Merged tags {tags_to_merge} → {canonical_tag} in {updated_places} places"
            )

    def get_trending_tags(self, days: int = 7, limit: int = 10) -> List[Dict[str, any]]:
        """
        Get trending tags based on recent usage.

        Args:
            days: Number of days to look back
            limit: Maximum number of trending tags

        Returns:
            List of trending tags with growth metrics
        """
        from datetime import datetime, timedelta

        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # Get tags from recent places
        recent_query = (
            self.db.query(
                func.unnest(Place.tags).label("tag"), func.count().label("recent_count")
            )
            .filter(
                and_(
                    Place.status == PlaceStatus.ACTIVE, Place.created_at >= cutoff_date
                )
            )
            .group_by("tag")
            .order_by(func.count().desc())
            .limit(limit * 2)  # Get more for comparison
        )

        recent_results = recent_query.all()

        # Get historical counts for comparison
        historical_query = (
            self.db.query(
                func.unnest(Place.tags).label("tag"), func.count().label("total_count")
            )
            .filter(Place.status == PlaceStatus.ACTIVE)
            .group_by("tag")
        )

        historical_results = {
            row.tag: row.total_count for row in historical_query.all()
        }

        # Calculate trending score
        trending_tags = []
        for row in recent_results:
            tag = row.tag
            recent_count = row.recent_count
            total_count = historical_results.get(tag, recent_count)

            # Calculate growth ratio
            if total_count > recent_count:
                growth_ratio = recent_count / (total_count - recent_count)
            else:
                growth_ratio = 1.0  # New tag

            trending_tags.append(
                {
                    "tag": tag,
                    "recent_count": recent_count,
                    "total_count": total_count,
                    "growth_ratio": round(growth_ratio, 2),
                    "trend_score": recent_count * growth_ratio,
                }
            )

        # Sort by trend score
        trending_tags.sort(key=lambda x: x["trend_score"], reverse=True)

        return trending_tags[:limit]

    def get_tag_clusters(self, user_id: UUID) -> Dict[str, List[str]]:
        """
        Group user's tags into semantic clusters.

        Args:
            user_id: User ID

        Returns:
            Dictionary with cluster names and tag lists
        """
        user_tags = self._get_user_tags_with_stats(user_id)
        tag_list = [tag_data["tag"] for tag_data in user_tags]

        return self.normalizer.categorize_tags(tag_list)

    def validate_and_normalize_tags(self, tags: List[str]) -> Dict[str, any]:
        """
        Validate and normalize a list of tags.

        Args:
            tags: Raw tag list

        Returns:
            Validation result with normalized tags and warnings
        """
        if not tags:
            return {"normalized_tags": [], "warnings": [], "rejected_tags": []}

        normalized_tags = []
        warnings = []
        rejected_tags = []

        for original_tag in tags:
            normalized = self.normalizer.normalize_tag(original_tag)

            if normalized:
                if normalized != original_tag:
                    warnings.append(f"'{original_tag}' normalized to '{normalized}'")
                normalized_tags.append(normalized)
            else:
                rejected_tags.append(original_tag)
                warnings.append(f"'{original_tag}' rejected (invalid format)")

        # Remove duplicates while preserving order
        seen = set()
        unique_normalized = []
        for tag in normalized_tags:
            if tag not in seen:
                unique_normalized.append(tag)
                seen.add(tag)
            else:
                warnings.append(f"Duplicate tag '{tag}' removed")

        return {
            "normalized_tags": unique_normalized,
            "warnings": warnings,
            "rejected_tags": rejected_tags,
        }
