"""Abstract interface for AI-based place classification."""

from abc import ABC, abstractmethod
from typing import Any, Dict

from app.schemas.place import PlaceCreate


class AIClassifierInterface(ABC):
    """Abstract interface for AI-based place category classification."""

    @abstractmethod
    async def classify_place(self, place_data: PlaceCreate) -> Dict[str, Any]:
        """
        Classify a place into appropriate category.

        Args:
            place_data: Place information to classify

        Returns:
            Dict containing:
            - category: Predicted category string
            - confidence: Confidence score (0.0-1.0)
            - reasoning: Explanation of classification decision
        """

    @abstractmethod
    async def classify_batch(self, places: list[PlaceCreate]) -> list[Dict[str, Any]]:
        """
        Classify multiple places efficiently.

        Args:
            places: List of places to classify

        Returns:
            List of classification results
        """

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the AI classifier is available and ready to use."""
