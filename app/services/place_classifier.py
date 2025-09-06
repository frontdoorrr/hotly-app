"""AI-based place category classification service using scikit-learn."""

import asyncio
import os
import time
from dataclasses import dataclass
from typing import List, Optional

import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline

from app.models.place import PlaceCategory
from app.schemas.place import PlaceCreate


@dataclass
class ClassificationResult:
    """Result of place category classification."""

    predicted_category: PlaceCategory
    confidence: float
    classification_time: float
    needs_manual_review: bool = False
    feature_scores: Optional[dict] = None


class PlaceClassifier:
    """AI-based place category classifier using TF-IDF + RandomForest."""

    def __init__(self, confidence_threshold: float = 0.70) -> None:
        """Initialize place classifier."""
        self.confidence_threshold = confidence_threshold
        self.model: Optional[Pipeline] = None
        self.categories = [
            PlaceCategory.RESTAURANT,
            PlaceCategory.CAFE,
            PlaceCategory.BAR,
            PlaceCategory.TOURIST_ATTRACTION,
            PlaceCategory.SHOPPING,
            PlaceCategory.ACCOMMODATION,
            PlaceCategory.ENTERTAINMENT,
            PlaceCategory.OTHER,
        ]

    def train_model(self, training_data: List[dict]) -> bool:
        """Train the classification model with training data."""
        try:
            if not training_data:
                return False

            # Extract features and labels
            texts = []
            labels = []

            for item in training_data:
                text_features = self._extract_text_from_dict(item)
                texts.append(text_features)
                labels.append(item["category"])

            # Create ML pipeline
            self.model = Pipeline(
                [
                    (
                        "tfidf",
                        TfidfVectorizer(
                            max_features=1000,
                            ngram_range=(1, 2),
                            stop_words=None,  # Korean stop words could be added
                            lowercase=True,
                        ),
                    ),
                    (
                        "classifier",
                        RandomForestClassifier(
                            n_estimators=100,
                            random_state=42,
                            max_depth=10,
                            min_samples_split=2,
                        ),
                    ),
                ]
            )

            # Train the model
            self.model.fit(texts, labels)
            return True

        except Exception:
            return False

    def is_model_trained(self) -> bool:
        """Check if model is trained and ready."""
        return self.model is not None

    async def classify_place(self, place_data: PlaceCreate) -> ClassificationResult:
        """Classify a single place into categories."""
        start_time = time.time()

        if not self.is_model_trained():
            # Return default classification if model not trained
            return ClassificationResult(
                predicted_category=PlaceCategory.OTHER,
                confidence=0.0,
                classification_time=time.time() - start_time,
                needs_manual_review=True,
            )

        try:
            # Extract features
            features = self._extract_features(place_data)

            # Run classification in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            prediction, probabilities = await loop.run_in_executor(
                None, self._predict_with_confidence, features
            )

            classification_time = time.time() - start_time
            confidence = float(max(probabilities))

            # Determine if manual review is needed
            needs_manual_review = confidence < self.confidence_threshold

            return ClassificationResult(
                predicted_category=PlaceCategory(prediction),
                confidence=confidence,
                classification_time=classification_time,
                needs_manual_review=needs_manual_review,
            )

        except Exception:
            return ClassificationResult(
                predicted_category=PlaceCategory.OTHER,
                confidence=0.0,
                classification_time=time.time() - start_time,
                needs_manual_review=True,
            )

    def classify_batch(self, places: List[PlaceCreate]) -> List[ClassificationResult]:
        """Classify multiple places efficiently."""
        if not self.is_model_trained():
            return [
                ClassificationResult(
                    predicted_category=PlaceCategory.OTHER,
                    confidence=0.0,
                    classification_time=0.0,
                    needs_manual_review=True,
                )
                for _ in places
            ]

        results = []
        for place in places:
            start_time = time.time()
            try:
                features = self._extract_features(place)
                prediction, probabilities = self._predict_with_confidence(features)
                classification_time = time.time() - start_time
                confidence = float(max(probabilities))

                results.append(
                    ClassificationResult(
                        predicted_category=PlaceCategory(prediction),
                        confidence=confidence,
                        classification_time=classification_time,
                        needs_manual_review=confidence < self.confidence_threshold,
                    )
                )
            except Exception:
                results.append(
                    ClassificationResult(
                        predicted_category=PlaceCategory.OTHER,
                        confidence=0.0,
                        classification_time=time.time() - start_time,
                        needs_manual_review=True,
                    )
                )

        return results

    async def update_model_online(self, feedback_data: List[dict]) -> bool:
        """Update model with new feedback data (online learning simulation)."""
        try:
            if not feedback_data or not self.is_model_trained():
                return False

            # For this implementation, we retrain with additional data
            # In production, this could be replaced with incremental learning

            # Extract existing training data representation
            len(self.model.named_steps["classifier"].classes_)

            # Add new feedback data and retrain
            success = self.train_model(feedback_data)
            return success

        except Exception:
            return False

    def save_model(self, model_path: str) -> bool:
        """Save trained model to file."""
        try:
            if not self.is_model_trained():
                return False

            # Ensure directory exists
            os.makedirs(os.path.dirname(model_path), exist_ok=True)

            # Save model and metadata
            model_data = {
                "model": self.model,
                "confidence_threshold": self.confidence_threshold,
                "categories": self.categories,
            }

            joblib.dump(model_data, model_path)
            return True

        except Exception:
            return False

    def load_model(self, model_path: str) -> bool:
        """Load trained model from file."""
        try:
            if not os.path.exists(model_path):
                return False

            # Load model and metadata
            model_data = joblib.load(model_path)
            self.model = model_data["model"]
            self.confidence_threshold = model_data["confidence_threshold"]
            self.categories = model_data["categories"]

            return True

        except Exception:
            return False

    def set_confidence_threshold(self, threshold: float) -> None:
        """Set confidence threshold for classification decisions."""
        if 0.0 <= threshold <= 1.0:
            self.confidence_threshold = threshold

    def _extract_features(self, place_data: PlaceCreate) -> str:
        """Extract text features from place data for classification."""
        features_parts = []

        # Add name (most important feature)
        if place_data.name:
            features_parts.append(place_data.name)

        # Add description
        if place_data.description:
            features_parts.append(place_data.description)

        # Add keywords
        if place_data.keywords:
            features_parts.extend(place_data.keywords)

        # Add tags
        if place_data.tags:
            features_parts.extend(place_data.tags)

        return " ".join(features_parts)

    def _extract_text_from_dict(self, item: dict) -> str:
        """Extract text features from training data dictionary."""
        features_parts = []

        if item.get("name"):
            features_parts.append(item["name"])
        if item.get("description"):
            features_parts.append(item["description"])
        if item.get("keywords"):
            features_parts.extend(item["keywords"])

        return " ".join(features_parts)

    def _predict_with_confidence(self, features: str) -> tuple:
        """Make prediction and return confidence scores."""
        if not self.model:
            return PlaceCategory.OTHER, [0.0]

        # Get prediction and probabilities
        prediction = self.model.predict([features])[0]
        probabilities = self.model.predict_proba([features])[0]

        return prediction, probabilities

    def _calculate_confidence(self, features: str) -> float:
        """Calculate confidence score for given features."""
        if not self.model:
            return 0.0

        try:
            probabilities = self.model.predict_proba([features])[0]
            return float(max(probabilities))
        except Exception:
            return 0.0
