"""
Course recommendation engine for optimal date course generation.

Uses algorithms for:
- Distance optimization (TSP-like approach)
- Category diversity
- Travel time estimation
"""

import logging
from dataclasses import dataclass
from typing import List, Optional, Tuple

from geopy.distance import geodesic

from app.schemas.place import PlaceCreate

logger = logging.getLogger(__name__)


@dataclass
class PlaceInCourse:
    """Place with position in course and travel information."""

    place: PlaceCreate
    position: int  # 0-indexed position in course
    category: str
    travel_distance_km: Optional[float] = None  # Distance from previous place
    travel_duration_minutes: Optional[int] = None  # Travel time from previous
    estimated_duration_minutes: int = 60  # Default stay duration


@dataclass
class CourseRecommendation:
    """Complete course recommendation result."""

    places: List[PlaceInCourse]
    total_distance_km: float
    total_duration_minutes: int  # Including travel + stay times
    optimization_score: float  # 0.0 to 1.0, higher is better


class CourseRecommender:
    """
    AI-powered course recommendation engine.

    Optimizes place ordering based on:
    1. Geographic distance (70% weight)
    2. Category diversity (30% weight)
    """

    def __init__(
        self,
        distance_weight: float = 0.7,
        diversity_weight: float = 0.3,
        avg_speed_kmh: float = 4.0,  # Walking speed
    ):
        """
        Initialize course recommender.

        Args:
            distance_weight: Weight for distance optimization (0-1)
            diversity_weight: Weight for category diversity (0-1)
            avg_speed_kmh: Average travel speed in km/h
        """
        self.distance_weight = distance_weight
        self.diversity_weight = diversity_weight
        self.avg_speed_kmh = avg_speed_kmh

    def recommend_course(
        self,
        places: List[PlaceCreate],
        start_location: Optional[Tuple[float, float]] = None,
    ) -> CourseRecommendation:
        """
        Recommend optimal course order for given places.

        Args:
            places: List of 3-6 places to visit
            start_location: Optional (lat, lng) starting point

        Returns:
            CourseRecommendation with optimized order

        Raises:
            ValueError: If place count is outside 3-6 range
        """
        # Validate input
        if len(places) < 3:
            raise ValueError("At least 3 places required for course recommendation")
        if len(places) > 6:
            raise ValueError("Maximum 6 places allowed for course recommendation")

        logger.info(f"Generating course recommendation for {len(places)} places")

        # Optimize place order
        optimized_order = self._optimize_order(places, start_location)

        # Calculate travel information
        places_in_course = self._calculate_travel_info(optimized_order)

        # Calculate totals
        total_distance = (
            sum(p.travel_distance_km for p in places_in_course if p.travel_distance_km)
            or 0.0
        )
        total_duration = sum(
            p.estimated_duration_minutes + (p.travel_duration_minutes or 0)
            for p in places_in_course
        )

        # Calculate optimization score
        optimization_score = self._calculate_optimization_score(
            places, optimized_order, total_distance
        )

        return CourseRecommendation(
            places=places_in_course,
            total_distance_km=total_distance,
            total_duration_minutes=total_duration,
            optimization_score=optimization_score,
        )

    def _optimize_order(
        self,
        places: List[PlaceCreate],
        start_location: Optional[Tuple[float, float]] = None,
    ) -> List[PlaceCreate]:
        """
        Optimize place order using distance and category diversity.

        Uses nearest-neighbor + 2-opt improvement with category diversity.

        Args:
            places: Places to order
            start_location: Optional starting point

        Returns:
            Optimized list of places
        """
        # Step 1: Get initial order with nearest neighbor
        if len(places) <= 3:
            initial_order = self._nearest_neighbor_order(places, start_location)
        else:
            initial_order = self._diversity_aware_order(places, start_location)

        # Step 2: Apply 2-opt improvement for distance optimization
        optimized_order = self._two_opt_improve(initial_order)

        return optimized_order

    def _nearest_neighbor_order(
        self,
        places: List[PlaceCreate],
        start_location: Optional[Tuple[float, float]] = None,
    ) -> List[PlaceCreate]:
        """
        Order places using nearest neighbor algorithm.

        Tries different starting points and selects the shortest route.

        Args:
            places: Places to order
            start_location: Optional starting point

        Returns:
            Ordered list of places
        """
        if start_location:
            # Use specified start location
            return self._nn_from_location(places, start_location)

        # Try starting from each place and pick the best
        best_route = None
        best_distance = float("inf")

        for start_place in places:
            route = self._nn_from_place(places, start_place)
            distance = self._calculate_route_distance(route)

            if distance < best_distance:
                best_distance = distance
                best_route = route

        return best_route

    def _nn_from_location(
        self, places: List[PlaceCreate], start_loc: Tuple[float, float]
    ) -> List[PlaceCreate]:
        """Nearest neighbor from a specific location."""
        unvisited = places.copy()
        ordered = []
        current_loc = start_loc

        while unvisited:
            nearest = min(
                unvisited,
                key=lambda p: geodesic(
                    current_loc, (p.latitude, p.longitude)
                ).kilometers,
            )
            ordered.append(nearest)
            unvisited.remove(nearest)
            current_loc = (nearest.latitude, nearest.longitude)

        return ordered

    def _nn_from_place(
        self, places: List[PlaceCreate], start_place: PlaceCreate
    ) -> List[PlaceCreate]:
        """Nearest neighbor starting from a specific place."""
        unvisited = [p for p in places if p != start_place]
        ordered = [start_place]
        current_loc = (start_place.latitude, start_place.longitude)

        while unvisited:
            nearest = min(
                unvisited,
                key=lambda p: geodesic(
                    current_loc, (p.latitude, p.longitude)
                ).kilometers,
            )
            ordered.append(nearest)
            unvisited.remove(nearest)
            current_loc = (nearest.latitude, nearest.longitude)

        return ordered

    def _diversity_aware_order(
        self,
        places: List[PlaceCreate],
        start_location: Optional[Tuple[float, float]] = None,
    ) -> List[PlaceCreate]:
        """
        Order places with category diversity consideration.

        Balances distance optimization with category variety.

        Args:
            places: Places to order
            start_location: Optional starting point

        Returns:
            Ordered list with better category distribution
        """
        unvisited = places.copy()
        ordered = []

        current_loc = start_location or (places[0].latitude, places[0].longitude)
        prev_category = None
        consecutive_count = 0

        while unvisited:
            # Calculate score for each unvisited place
            candidates = []
            for place in unvisited:
                # Distance score (closer is better)
                distance = geodesic(
                    current_loc, (place.latitude, place.longitude)
                ).kilometers
                distance_score = 1.0 / (1.0 + distance)  # Normalize

                # Diversity score (different category is better)
                if place.category == prev_category and consecutive_count >= 1:
                    # Penalize third consecutive same category
                    diversity_score = 0.3
                elif place.category == prev_category:
                    # Small penalty for second consecutive
                    diversity_score = 0.7
                else:
                    # Reward for different category
                    diversity_score = 1.0

                # Combined score
                total_score = (
                    self.distance_weight * distance_score
                    + self.diversity_weight * diversity_score
                )

                candidates.append((place, total_score, distance))

            # Select best candidate
            best_place = max(candidates, key=lambda x: x[1])[0]

            ordered.append(best_place)
            unvisited.remove(best_place)

            # Update tracking
            if best_place.category == prev_category:
                consecutive_count += 1
            else:
                consecutive_count = 0
                prev_category = best_place.category

            current_loc = (best_place.latitude, best_place.longitude)

        return ordered

    def _two_opt_improve(self, places: List[PlaceCreate]) -> List[PlaceCreate]:
        """
        Improve route using 2-opt algorithm.

        2-opt repeatedly removes two edges and reconnects them in a different way
        if it reduces total distance.

        Args:
            places: Initial order of places

        Returns:
            Improved order of places
        """
        improved = places.copy()
        improved_found = True

        # Keep improving until no more improvements found
        while improved_found:
            improved_found = False

            for i in range(1, len(improved) - 1):
                for j in range(i + 1, len(improved)):
                    # Try reversing the segment between i and j
                    new_route = (
                        improved[:i] + improved[i : j + 1][::-1] + improved[j + 1 :]
                    )

                    # Calculate distances
                    current_distance = self._calculate_route_distance(improved)
                    new_distance = self._calculate_route_distance(new_route)

                    # If improvement found, accept it
                    if new_distance < current_distance:
                        improved = new_route
                        improved_found = True
                        break

                if improved_found:
                    break

        return improved

    def _calculate_route_distance(self, places: List[PlaceCreate]) -> float:
        """
        Calculate total distance for a route.

        Args:
            places: Ordered list of places

        Returns:
            Total distance in kilometers
        """
        total = 0.0
        for i in range(len(places) - 1):
            coord1 = (places[i].latitude, places[i].longitude)
            coord2 = (places[i + 1].latitude, places[i + 1].longitude)
            total += geodesic(coord1, coord2).kilometers
        return total

    def _calculate_travel_info(self, places: List[PlaceCreate]) -> List[PlaceInCourse]:
        """
        Calculate travel distance and time between consecutive places.

        Args:
            places: Ordered list of places

        Returns:
            List of PlaceInCourse with travel information
        """
        result = []

        for i, place in enumerate(places):
            travel_distance = None
            travel_duration = None

            if i > 0:
                # Calculate distance from previous place
                prev_place = places[i - 1]
                coord1 = (prev_place.latitude, prev_place.longitude)
                coord2 = (place.latitude, place.longitude)

                travel_distance = geodesic(coord1, coord2).kilometers
                # Estimate travel time based on average speed
                travel_duration = int((travel_distance / self.avg_speed_kmh) * 60)

            result.append(
                PlaceInCourse(
                    place=place,
                    position=i,
                    category=place.category,
                    travel_distance_km=travel_distance,
                    travel_duration_minutes=travel_duration,
                    estimated_duration_minutes=60,  # Default 1 hour per place
                )
            )

        return result

    def _calculate_optimization_score(
        self,
        original_places: List[PlaceCreate],
        optimized_places: List[PlaceCreate],
        total_distance: float,
    ) -> float:
        """
        Calculate optimization quality score (0.0 to 1.0).

        Compares optimized distance against original order distance.

        Args:
            original_places: Original place order
            optimized_places: Optimized place order
            total_distance: Total distance of optimized route

        Returns:
            Score from 0.0 (no improvement) to 1.0 (perfect)
        """
        # Calculate original distance
        original_distance = 0.0
        for i in range(len(original_places) - 1):
            coord1 = (original_places[i].latitude, original_places[i].longitude)
            coord2 = (original_places[i + 1].latitude, original_places[i + 1].longitude)
            original_distance += geodesic(coord1, coord2).kilometers

        if original_distance == 0:
            return 1.0

        # Calculate improvement ratio
        improvement = (original_distance - total_distance) / original_distance

        # Convert to score (cap at 1.0)
        return min(1.0, max(0.0, improvement * 2.0))  # Scale improvement to 0-1
