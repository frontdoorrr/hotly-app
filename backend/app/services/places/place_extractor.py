"""Place information extraction and structuring service."""

import logging
import re
import time
from difflib import SequenceMatcher
from typing import List, Optional

from app.exceptions.validation import ValidationError
from app.schemas.ai import AnalysisConfidence, GeminiResponse, PlaceAnalysisResult
from app.schemas.content import ExtractedContent
from app.schemas.place import (
    ExtractedPlace,
    ExtractionConfidence,
    PlaceExtractionResult,
    PlaceValidationError,
    StructuredAddress,
)

logger = logging.getLogger(__name__)


class PlaceExtractor:
    """Service for extracting and structuring place information."""

    def __init__(self):
        """Initialize place extractor."""
        self.valid_categories = {
            "restaurant",
            "cafe",
            "bar",
            "tourist_attraction",
            "shopping",
            "accommodation",
            "entertainment",
            "other",
        }

        # Category mapping for normalization
        self.category_mappings = {
            "korean restaurant": "restaurant",
            "korean bbq": "restaurant",
            "bbq": "restaurant",
            "italian restaurant": "restaurant",
            "chinese restaurant": "restaurant",
            "food": "restaurant",
            "dining": "restaurant",
            "coffee": "cafe",
            "coffee shop": "cafe",
            "bakery": "cafe",
            "pub": "bar",
            "club": "bar",
            "nightclub": "entertainment",
            "hotel": "accommodation",
            "motel": "accommodation",
            "guesthouse": "accommodation",
            "store": "shopping",
            "shop": "shopping",
            "mall": "shopping",
            "market": "shopping",
            "attraction": "tourist_attraction",
            "museum": "tourist_attraction",
            "park": "tourist_attraction",
            "theater": "entertainment",
            "cinema": "entertainment",
            "movie": "entertainment",
        }

    async def extract_and_structure_places(
        self, content: ExtractedContent, gemini_response: GeminiResponse
    ) -> PlaceExtractionResult:
        """Extract and structure places from Gemini response."""
        start_time = time.time()

        try:
            # Initialize result
            result = PlaceExtractionResult(
                total_places_found=len(gemini_response.places),
                extraction_metadata={
                    "source_url": content.url,
                    "platform": content.platform.value,
                    "gemini_confidence": gemini_response.overall_confidence.value,
                    "gemini_processing_time": gemini_response.processing_time,
                },
            )

            # Process each place
            valid_places = []
            for place_data in gemini_response.places:
                try:
                    extracted_place = await self._process_single_place(
                        place_data, content
                    )
                    if extracted_place:
                        valid_places.append(extracted_place)
                except PlaceValidationError as e:
                    result.validation_errors.append(str(e))
                    logger.warning(f"Place validation failed: {str(e)}")
                except Exception as e:
                    result.validation_errors.append(
                        f"Unexpected error processing place: {str(e)}"
                    )
                    logger.error(f"Unexpected error processing place: {str(e)}")

            # Remove duplicates
            deduplicated_places = self._remove_duplicates(valid_places)
            result.duplicates_removed = len(valid_places) - len(deduplicated_places)

            # Set final places
            result.places = deduplicated_places
            result.places_validated = len(deduplicated_places)

            # Calculate confidence and quality scores
            result.confidence_score = self._calculate_overall_confidence(
                deduplicated_places, gemini_response.overall_confidence
            )
            result.data_quality_score = self._calculate_data_quality_score(
                deduplicated_places
            )

            # Record processing time
            processing_time = time.time() - start_time
            result.processing_time_ms = processing_time * 1000

            logger.info(
                f"Processed {len(gemini_response.places)} places, "
                f"validated {len(deduplicated_places)}, "
                f"removed {result.duplicates_removed} duplicates in {processing_time:.3f}s"
            )

            return result

        except Exception as e:
            logger.error(f"Place extraction failed: {str(e)}")
            raise ValidationError(f"Place extraction failed: {str(e)}")

    async def _process_single_place(
        self, place_data: PlaceAnalysisResult, content: ExtractedContent
    ) -> Optional[ExtractedPlace]:
        """Process a single place from AI response."""
        try:
            # Validate required fields
            if not place_data.name or not place_data.name.strip():
                raise PlaceValidationError("Place name is required")

            # Clean and normalize data
            name = place_data.name.strip()
            category = self._normalize_category(place_data.category)
            confidence = self._convert_confidence(place_data.confidence)

            # Validate category
            if category not in self.valid_categories:
                raise PlaceValidationError(f"Invalid category: {category}")

            # Structure address
            structured_address = self._structure_address(place_data.address or "")

            # Calculate data quality score
            data_quality_score = self._calculate_place_quality_score(
                name, structured_address, place_data.description, confidence
            )

            # Create extracted place
            extracted_place = ExtractedPlace(
                name=name,
                category=category,
                confidence=confidence,
                structured_address=structured_address,
                description=place_data.description.strip()
                if place_data.description
                else None,
                keywords=self._extract_keywords_from_content(place_data, content),
                data_quality_score=data_quality_score,
                original_category=place_data.category,
                validation_warnings=[],
            )

            # Add validation warnings
            if data_quality_score < 0.5:
                extracted_place.validation_warnings.append("Low data quality score")

            if structured_address.completeness_score < 0.3:
                extracted_place.validation_warnings.append(
                    "Incomplete address information"
                )

            if confidence == ExtractionConfidence.LOW:
                extracted_place.validation_warnings.append("Low confidence extraction")

            return extracted_place

        except PlaceValidationError:
            raise
        except Exception as e:
            raise PlaceValidationError(
                f"Failed to process place '{place_data.name}': {str(e)}"
            )

    def _normalize_category(self, category: str) -> str:
        """Normalize category string."""
        if not category:
            return "other"

        category_lower = category.lower().strip()

        # Direct match
        if category_lower in self.valid_categories:
            return category_lower

        # Mapping match
        if category_lower in self.category_mappings:
            return self.category_mappings[category_lower]

        # Partial match
        for keyword, mapped_category in self.category_mappings.items():
            if keyword in category_lower:
                return mapped_category

        # Default fallback
        return "other"

    def _convert_confidence(
        self, confidence: AnalysisConfidence
    ) -> ExtractionConfidence:
        """Convert AI confidence to extraction confidence."""
        mapping = {
            AnalysisConfidence.HIGH: ExtractionConfidence.HIGH,
            AnalysisConfidence.MEDIUM: ExtractionConfidence.MEDIUM,
            AnalysisConfidence.LOW: ExtractionConfidence.LOW,
        }
        return mapping.get(confidence, ExtractionConfidence.MEDIUM)

    def _structure_address(self, address: str) -> StructuredAddress:
        """Structure and parse address information."""
        if not address:
            return StructuredAddress(full_address="", completeness_score=0.0)

        full_address = address.strip()

        # Initialize components
        street_address = None
        district = None
        city = None
        province = None
        country = None
        postal_code = None

        # Parse Korean addresses
        if "서울" in full_address or "Seoul" in full_address:
            city = "Seoul"

            # Extract district (구)
            district_match = re.search(r"([가-힣]+구)", full_address)
            if district_match:
                district = district_match.group(1)
            elif "강남" in full_address:
                district = "Gangnam"
            elif "홍대" in full_address:
                district = "Hongdae"
            elif "명동" in full_address:
                district = "Myeongdong"
            elif "이태원" in full_address:
                district = "Itaewon"

        # Extract country
        if "South Korea" in full_address or "Korea" in full_address:
            country = "South Korea"
        elif "한국" in full_address:
            country = "South Korea"

        # Extract street address (numbers and road names)
        street_match = re.search(
            r"(\d+[^,]*(?:로|길|street|st|avenue|ave))", full_address, re.IGNORECASE
        )
        if street_match:
            street_address = street_match.group(1).strip()

        # Extract postal code
        postal_match = re.search(r"\b\d{5,6}\b", full_address)
        if postal_match:
            postal_code = postal_match.group(0)

        # Calculate completeness score
        components = [street_address, district, city, country, postal_code]
        filled_components = sum(1 for comp in components if comp)
        completeness_score = filled_components / len(components)

        return StructuredAddress(
            full_address=full_address,
            street_address=street_address,
            district=district,
            city=city,
            province=province,
            country=country,
            postal_code=postal_code,
            completeness_score=completeness_score,
        )

    def _extract_keywords_from_content(
        self, place_data: PlaceAnalysisResult, content: ExtractedContent
    ) -> List[str]:
        """Extract relevant keywords from place and content data."""
        keywords = set()

        # Add category-related keywords
        category_keywords = {
            "restaurant": ["food", "dining", "meal", "cuisine"],
            "cafe": ["coffee", "drink", "beverage"],
            "bar": ["drink", "alcohol", "cocktail"],
            "shopping": ["shop", "store", "buy"],
            "accommodation": ["stay", "sleep", "room"],
            "entertainment": ["fun", "show", "performance"],
            "tourist_attraction": ["visit", "see", "attraction"],
        }

        if place_data.category in category_keywords:
            keywords.update(category_keywords[place_data.category])

        # Extract from hashtags
        if content.metadata.hashtags:
            for tag in content.metadata.hashtags:
                # Remove # and add clean keyword
                clean_tag = tag.replace("#", "").lower()
                if len(clean_tag) > 2:  # Minimum length
                    keywords.add(clean_tag)

        # Extract from description
        if place_data.description:
            # Simple keyword extraction (in production, use NLP)
            description_words = re.findall(r"\w+", place_data.description.lower())
            meaningful_words = [w for w in description_words if len(w) > 3]
            keywords.update(meaningful_words[:5])  # Limit to 5 from description

        # Limit total keywords
        return list(keywords)[:10]

    def _calculate_place_quality_score(
        self,
        name: str,
        address: StructuredAddress,
        description: Optional[str],
        confidence: ExtractionConfidence,
    ) -> float:
        """Calculate data quality score for a place."""
        score = 0.0

        # Name quality (30%)
        if name and len(name.strip()) > 2:
            name_score = min(
                1.0, len(name.strip()) / 20
            )  # Longer names generally better
            score += name_score * 0.3

        # Address quality (40%)
        score += address.completeness_score * 0.4

        # Description quality (20%)
        if description and description.strip():
            desc_score = min(1.0, len(description.strip()) / 100)
            score += desc_score * 0.2

        # Confidence quality (10%)
        confidence_scores = {
            ExtractionConfidence.HIGH: 1.0,
            ExtractionConfidence.MEDIUM: 0.7,
            ExtractionConfidence.LOW: 0.3,
        }
        score += confidence_scores.get(confidence, 0.5) * 0.1

        return min(1.0, score)

    def _remove_duplicates(self, places: List[ExtractedPlace]) -> List[ExtractedPlace]:
        """Remove duplicate places based on name and address similarity."""
        if len(places) <= 1:
            return places

        unique_places = []

        for place in places:
            is_duplicate = False

            for existing_place in unique_places:
                if self._are_places_similar(place, existing_place):
                    is_duplicate = True
                    # Keep the higher quality place
                    if place.data_quality_score > existing_place.data_quality_score:
                        # Replace existing with better quality place
                        unique_places.remove(existing_place)
                        unique_places.append(place)
                    break

            if not is_duplicate:
                unique_places.append(place)

        return unique_places

    def _are_places_similar(
        self, place1: ExtractedPlace, place2: ExtractedPlace
    ) -> bool:
        """Check if two places are similar (potential duplicates)."""
        # Name similarity
        name_similarity = SequenceMatcher(
            None, place1.name.lower(), place2.name.lower()
        ).ratio()

        # Address similarity
        addr1 = place1.structured_address.full_address.lower()
        addr2 = place2.structured_address.full_address.lower()
        address_similarity = SequenceMatcher(None, addr1, addr2).ratio()

        # Consider similar if high name similarity or both high address similarity
        if name_similarity > 0.8:  # Very similar names
            return True

        if (
            name_similarity > 0.6 and address_similarity > 0.7
        ):  # Moderately similar names + similar addresses
            return True

        return False

    def _calculate_overall_confidence(
        self, places: List[ExtractedPlace], gemini_confidence: AnalysisConfidence
    ) -> float:
        """Calculate overall confidence score."""
        if not places:
            # High confidence in finding no places if AI was confident
            return 0.9 if gemini_confidence == AnalysisConfidence.HIGH else 0.5

        # Base confidence from AI
        base_confidence = {
            AnalysisConfidence.HIGH: 0.8,
            AnalysisConfidence.MEDIUM: 0.6,
            AnalysisConfidence.LOW: 0.4,
        }.get(gemini_confidence, 0.5)

        # Adjust based on place quality
        avg_place_confidence = sum(
            1.0
            if p.confidence == ExtractionConfidence.HIGH
            else 0.7
            if p.confidence == ExtractionConfidence.MEDIUM
            else 0.4
            for p in places
        ) / len(places)

        # Weighted average
        final_confidence = (base_confidence * 0.6) + (avg_place_confidence * 0.4)

        return min(1.0, final_confidence)

    def _calculate_data_quality_score(self, places: List[ExtractedPlace]) -> float:
        """Calculate overall data quality score."""
        if not places:
            return 0.9  # High quality for empty result

        return sum(place.data_quality_score for place in places) / len(places)
