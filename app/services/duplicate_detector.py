"""Place duplicate detection service with multi-stage algorithm."""

import math
import re
import unicodedata
from dataclasses import dataclass
from typing import Dict, List, Optional

from app.schemas.place import PlaceCreate


@dataclass
class DuplicateResult:
    """Result of duplicate detection check."""

    is_duplicate: bool
    confidence: float
    match_type: str
    matched_place_index: int = -1
    similarity_scores: Optional[Dict[str, float]] = None


class DuplicateDetector:
    """Multi-stage duplicate detection algorithm."""

    def __init__(self) -> None:
        """Initialize duplicate detector."""
        self.name_similarity_threshold = 0.80
        self.address_similarity_threshold = 0.70
        self.geographical_threshold_meters = 50.0
        self.exact_match_threshold = 0.95

    async def check_duplicate(
        self, new_place: PlaceCreate, existing_places: List[PlaceCreate]
    ) -> DuplicateResult:
        """
        Check if new place is duplicate of existing places.

        Multi-stage algorithm with best match selection:
        1. Exact match (highest priority)
        2. Name similarity
        3. Address similarity
        4. Geographical proximity
        """
        if not existing_places:
            return DuplicateResult(
                is_duplicate=False, confidence=0.0, match_type="no_existing_places"
            )

        best_result = DuplicateResult(
            is_duplicate=False, confidence=0.0, match_type="no_match"
        )

        for i, existing_place in enumerate(existing_places):
            # Check all stages and get the best result
            results_for_place = []

            # Stage 1: Exact match detection
            exact_result = self._check_exact_match(new_place, existing_place)
            if exact_result.is_duplicate:
                exact_result.matched_place_index = i
                return exact_result  # Return immediately for exact matches

            # Stage 2: Name similarity detection
            name_result = self._check_name_similarity(new_place, existing_place)
            results_for_place.append((name_result, i))

            # Stage 3: Address similarity detection
            address_result = self._check_address_similarity(new_place, existing_place)
            results_for_place.append((address_result, i))

            # Stage 4: Geographical proximity detection
            geo_result = self._check_geographical_proximity(new_place, existing_place)
            results_for_place.append((geo_result, i))

            # Select best result for this existing place
            for result, place_index in results_for_place:
                if result.confidence > best_result.confidence:
                    best_result = result
                    best_result.matched_place_index = place_index

        # Determine if duplicate based on confidence threshold
        best_result.is_duplicate = best_result.confidence >= 0.65

        return best_result

    def _check_exact_match(
        self, new_place: PlaceCreate, existing_place: PlaceCreate
    ) -> DuplicateResult:
        """Check for exact match (normalized name + address)."""
        new_name = self._normalize_name(new_place.name)
        existing_name = self._normalize_name(existing_place.name)

        new_address = self._normalize_address(new_place.address or "")
        existing_address = self._normalize_address(existing_place.address or "")

        if new_name == existing_name and new_address == existing_address:
            return DuplicateResult(
                is_duplicate=True,
                confidence=1.0,
                match_type="exact",
                similarity_scores={"name": 1.0, "address": 1.0},
            )

        return DuplicateResult(
            is_duplicate=False, confidence=0.0, match_type="no_exact_match"
        )

    def _check_name_similarity(
        self, new_place: PlaceCreate, existing_place: PlaceCreate
    ) -> DuplicateResult:
        """Check name similarity using Levenshtein distance."""
        new_name = self._normalize_name(new_place.name)
        existing_name = self._normalize_name(existing_place.name)

        similarity = self._calculate_string_similarity(new_name, existing_name)

        if similarity >= self.name_similarity_threshold:
            return DuplicateResult(
                is_duplicate=True,
                confidence=similarity,
                match_type="name_similarity",
                similarity_scores={"name": similarity},
            )

        return DuplicateResult(
            is_duplicate=False,
            confidence=similarity * 0.8,  # Lower confidence for name-only
            match_type="name_similarity_low",
        )

    def _check_address_similarity(
        self, new_place: PlaceCreate, existing_place: PlaceCreate
    ) -> DuplicateResult:
        """Check address similarity."""
        if not new_place.address or not existing_place.address:
            return DuplicateResult(
                is_duplicate=False, confidence=0.0, match_type="missing_address"
            )

        new_address = self._normalize_address(new_place.address)
        existing_address = self._normalize_address(existing_place.address)

        similarity = self._calculate_string_similarity(new_address, existing_address)

        if similarity >= self.address_similarity_threshold:
            return DuplicateResult(
                is_duplicate=True,
                confidence=similarity,
                match_type="address_similarity",
                similarity_scores={"address": similarity},
            )

        return DuplicateResult(
            is_duplicate=False,
            confidence=similarity * 0.6,
            match_type="address_similarity_low",
        )

    def _check_geographical_proximity(
        self, new_place: PlaceCreate, existing_place: PlaceCreate
    ) -> DuplicateResult:
        """Check geographical proximity with name similarity."""
        if (
            not new_place.latitude
            or not new_place.longitude
            or not existing_place.latitude
            or not existing_place.longitude
        ):
            return DuplicateResult(
                is_duplicate=False, confidence=0.0, match_type="missing_coordinates"
            )

        distance = self._calculate_distance(
            new_place.latitude,
            new_place.longitude,
            existing_place.latitude,
            existing_place.longitude,
        )

        if distance <= self.geographical_threshold_meters:
            # Also check name similarity for geographical matches
            name_similarity = self._calculate_string_similarity(
                self._normalize_name(new_place.name),
                self._normalize_name(existing_place.name),
            )

            # Combined score: distance proximity + name similarity
            distance_score = max(
                0.0, 1.0 - distance / self.geographical_threshold_meters
            )
            combined_confidence = distance_score * 0.6 + name_similarity * 0.4

            if combined_confidence >= 0.75:
                return DuplicateResult(
                    is_duplicate=True,
                    confidence=combined_confidence,
                    match_type="geographical_proximity",
                    similarity_scores={
                        "distance": distance_score,
                        "name": name_similarity,
                        "distance_meters": distance,
                    },
                )

        return DuplicateResult(
            is_duplicate=False,
            confidence=0.0,
            match_type="geographical_distance_too_far",
        )

    def _normalize_name(self, name: str) -> str:
        """Normalize place name for comparison."""
        if not name:
            return ""

        # Unicode normalization
        normalized = unicodedata.normalize("NFC", name)

        # Remove whitespace
        normalized = re.sub(r"\s+", "", normalized)

        # Convert to lowercase
        normalized = normalized.lower()

        # Remove special characters but keep Korean, English, numbers
        normalized = re.sub(r"[^a-z0-9가-힣]", "", normalized)

        return normalized

    def _normalize_address(self, address: str) -> str:
        """Normalize address for comparison."""
        if not address:
            return ""

        # Unicode normalization
        normalized = unicodedata.normalize("NFC", address)

        # Remove common address prefixes/suffixes
        normalized = re.sub(r"(시|도|구|군|동|읍|면|리)$", "", normalized)
        normalized = re.sub(r"^(서울특별시|서울시|서울)", "서울", normalized)

        # Remove whitespace
        normalized = re.sub(r"\s+", "", normalized)

        # Convert to lowercase
        normalized = normalized.lower()

        return normalized

    def _calculate_string_similarity(self, str1: str, str2: str) -> float:
        """Calculate string similarity using Levenshtein distance."""
        if not str1 and not str2:
            return 1.0
        if not str1 or not str2:
            return 0.0

        # Calculate Levenshtein distance
        distance = self._levenshtein_distance(str1, str2)

        # Convert to similarity score (0.0 to 1.0)
        max_length = max(len(str1), len(str2))
        similarity = 1.0 - (distance / max_length)

        return max(0.0, similarity)

    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        """Calculate Levenshtein distance between two strings."""
        if len(s1) < len(s2):
            return self._levenshtein_distance(s2, s1)

        if len(s2) == 0:
            return len(s1)

        previous_row = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row

        return previous_row[-1]

    def _calculate_distance(
        self, lat1: float, lng1: float, lat2: float, lng2: float
    ) -> float:
        """Calculate geographical distance in meters using Haversine formula."""
        # Convert latitude and longitude from degrees to radians
        lat1, lng1, lat2, lng2 = map(math.radians, [lat1, lng1, lat2, lng2])

        # Haversine formula
        dlat = lat2 - lat1
        dlng = lng2 - lng1
        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(lat1) * math.cos(lat2) * math.sin(dlng / 2) ** 2
        )
        c = 2 * math.asin(math.sqrt(a))

        # Radius of earth in meters
        earth_radius = 6371000

        return earth_radius * c
