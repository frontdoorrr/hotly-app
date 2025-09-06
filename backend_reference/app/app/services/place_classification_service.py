"""Place classification business logic service."""

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import List, Optional

from app.exceptions.ai import AIAnalysisError
from app.models.place import PlaceCategory
from app.schemas.place import PlaceCreate
from app.services.ai.gemini_classifier import GeminiClassifier
from app.services.ai.interfaces.classifier_interface import AIClassifierInterface

logger = logging.getLogger(__name__)


@dataclass
class ClassificationResult:
    """Result of place category classification."""

    predicted_category: PlaceCategory
    confidence: float
    classification_time: float
    reasoning: str
    needs_manual_review: bool = False


class PlaceClassificationService:
    """Business logic service for place category classification."""

    def __init__(self, ai_classifier: Optional[AIClassifierInterface] = None):
        """Initialize classification service with AI classifier."""
        self.ai_classifier = ai_classifier or GeminiClassifier()
        self.confidence_threshold = 0.70
        self.max_classification_time = 5.0  # 5 seconds max

    async def classify_place(self, place_data: PlaceCreate) -> ClassificationResult:
        """
        Classify a place into appropriate category.

        Args:
            place_data: Place information to classify

        Returns:
            Classification result with category, confidence, and reasoning
        """
        start_time = time.time()

        try:
            # Check if AI classifier is available
            if not self.ai_classifier.is_available():
                logger.warning("AI classifier not available, using fallback")
                return self._fallback_classification(place_data, start_time)

            # Call AI classifier
            ai_result = await asyncio.wait_for(
                self.ai_classifier.classify_place(place_data),
                timeout=self.max_classification_time,
            )

            classification_time = time.time() - start_time

            # Process AI result
            predicted_category = PlaceCategory(ai_result["category"])
            confidence = float(ai_result["confidence"])
            reasoning = ai_result["reasoning"]

            # Determine if manual review is needed
            needs_manual_review = confidence < self.confidence_threshold

            result = ClassificationResult(
                predicted_category=predicted_category,
                confidence=confidence,
                classification_time=classification_time,
                reasoning=reasoning,
                needs_manual_review=needs_manual_review,
            )

            logger.info(
                f"Place classified: {place_data.name} → {predicted_category} "
                f"(confidence: {confidence:.2f}, time: {classification_time:.2f}s)"
            )

            return result

        except asyncio.TimeoutError:
            logger.error(f"Classification timeout for place: {place_data.name}")
            return self._fallback_classification(place_data, start_time)
        except AIAnalysisError as e:
            logger.error(f"AI analysis error: {e}")
            return self._fallback_classification(place_data, start_time)
        except Exception as e:
            logger.error(f"Unexpected classification error: {e}")
            return self._fallback_classification(place_data, start_time)

    async def classify_places_batch(
        self, places: List[PlaceCreate], max_concurrent: int = 3
    ) -> List[ClassificationResult]:
        """
        Classify multiple places with controlled concurrency.

        Args:
            places: List of places to classify
            max_concurrent: Maximum concurrent classifications

        Returns:
            List of classification results
        """
        if not places:
            return []

        # Use semaphore to control concurrency
        semaphore = asyncio.Semaphore(max_concurrent)

        async def classify_with_semaphore(place):
            async with semaphore:
                return await self.classify_place(place)

        # Execute classifications concurrently
        tasks = [classify_with_semaphore(place) for place in places]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results and handle exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Batch classification failed for place {i}: {result}")
                processed_results.append(
                    self._fallback_classification(places[i], time.time())
                )
            else:
                processed_results.append(result)

        return processed_results

    async def classify_and_update_place(
        self, place_data: PlaceCreate, auto_update: bool = True
    ) -> ClassificationResult:
        """
        Classify place and optionally auto-update if confident.

        Args:
            place_data: Place data to classify
            auto_update: Whether to update place category if confident

        Returns:
            Classification result with update status
        """
        # Classify the place
        result = await self.classify_place(place_data)

        # Auto-update category if confident and enabled
        if (
            auto_update
            and not result.needs_manual_review
            and result.predicted_category != PlaceCategory.OTHER
        ):
            place_data.category = result.predicted_category
            logger.info(
                f"Auto-updated place category: {place_data.name} → {result.predicted_category}"
            )

        return result

    def set_confidence_threshold(self, threshold: float) -> None:
        """Set confidence threshold for manual review decision."""
        if 0.0 <= threshold <= 1.0:
            self.confidence_threshold = threshold
            logger.info(f"Updated confidence threshold to {threshold}")

    def _fallback_classification(
        self, place_data: PlaceCreate, start_time: float
    ) -> ClassificationResult:
        """Provide fallback classification when AI is unavailable."""
        classification_time = time.time() - start_time

        # Simple heuristic-based classification as fallback
        fallback_category = self._heuristic_classification(place_data)

        return ClassificationResult(
            predicted_category=fallback_category,
            confidence=0.30,  # Low confidence for fallback
            classification_time=classification_time,
            reasoning="AI 서비스 이용 불가로 인한 기본 분류",
            needs_manual_review=True,
        )

    def _heuristic_classification(self, place_data: PlaceCreate) -> PlaceCategory:
        """Simple heuristic classification as fallback."""
        name_lower = place_data.name.lower()
        description_lower = (place_data.description or "").lower()
        keywords_str = " ".join(place_data.keywords or []).lower()

        # Combine all text for analysis
        combined_text = f"{name_lower} {description_lower} {keywords_str}"

        # Simple keyword-based heuristics
        cafe_keywords = ["카페", "커피", "스타벅스", "빽다방", "투썸", "coffee"]
        restaurant_keywords = ["음식점", "식당", "레스토랑", "치킨", "피자", "한식"]
        tourist_keywords = ["관광", "명소", "궁", "타워", "박물관", "공원"]
        shopping_keywords = ["쇼핑", "매장", "마트", "백화점", "아울렛"]

        if any(keyword in combined_text for keyword in cafe_keywords):
            return PlaceCategory.CAFE
        elif any(keyword in combined_text for keyword in restaurant_keywords):
            return PlaceCategory.RESTAURANT
        elif any(keyword in combined_text for keyword in tourist_keywords):
            return PlaceCategory.TOURIST_ATTRACTION
        elif any(keyword in combined_text for keyword in shopping_keywords):
            return PlaceCategory.SHOPPING

        return PlaceCategory.OTHER
