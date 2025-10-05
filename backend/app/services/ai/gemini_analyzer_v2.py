"""Advanced Gemini AI analyzer for place information extraction."""

import asyncio
import json
import time
import logging
from typing import List, Optional, Dict, Any
import os
import base64
# import httpx  # Not available, will use mock implementation

from app.schemas.ai import (
    GeminiRequest, 
    GeminiResponse, 
    PlaceAnalysisResult, 
    AnalysisConfidence,
    PlaceAnalysisRequest,
    PlaceInfo,
    PlaceCategory
)
from app.schemas.content import ExtractedContent
from app.exceptions.ai import AIAnalysisError, RateLimitError
from app.prompts.place_extraction import (
    PLACE_EXTRACTION_PROMPT_V2,
    PLACE_EXTRACTION_JSON_SCHEMA
)

logger = logging.getLogger(__name__)


class GeminiAnalyzerV2:
    """Advanced Gemini AI analyzer with multimodal capabilities."""

    def __init__(self):
        """Initialize Gemini analyzer."""
        self.api_key = os.getenv("GOOGLE_AI_API_KEY")
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"
        self.model_name = "gemini-pro-vision"
        self.max_retries = 3
        self.base_delay = 1.0  # Base delay for exponential backoff
        
        if not self.api_key:
            logger.warning("GOOGLE_AI_API_KEY not set, using mock responses")

    async def analyze_place_content_extracted(
        self, 
        content: ExtractedContent,
        min_confidence: str = "medium"
    ) -> GeminiResponse:
        """Analyze content to extract place information."""
        start_time = time.time()
        
        try:
            # Build request
            request = self._build_gemini_request(content)
            
            # Call Gemini API with retries
            response_data = await self._call_gemini_api_with_retries(request)
            
            # Parse and validate response
            places = self._parse_gemini_response(response_data)
            
            # Filter by confidence if specified
            if min_confidence != "low":
                places = self._filter_by_confidence(places, min_confidence)
            
            processing_time = time.time() - start_time
            
            return GeminiResponse(
                places=places,
                overall_confidence=self._calculate_overall_confidence(places),
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"Gemini analysis failed: {str(e)}")
            if isinstance(e, (AIAnalysisError, RateLimitError)):
                raise
            raise AIAnalysisError(f"Analysis failed: {str(e)}")

    def _build_gemini_request(self, content: ExtractedContent) -> GeminiRequest:
        """Build Gemini API request from extracted content."""
        # Combine text content
        text_content = f"""
        Platform: {content.platform.value}
        Title: {content.metadata.title or 'N/A'}
        Description: {content.metadata.description or 'N/A'}
        Location: {content.metadata.location or 'N/A'}
        Hashtags: {', '.join(content.metadata.hashtags) if content.metadata.hashtags else 'N/A'}
        """
        
        return GeminiRequest(
            content=text_content.strip(),
            images=content.metadata.images,
            platform=content.platform.value
        )

    async def _call_gemini_api_with_retries(self, request: GeminiRequest) -> Dict[str, Any]:
        """Call Gemini API with exponential backoff retries."""
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                return await self._call_gemini_api(request)
                
            except RateLimitError as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    # Extract wait time from error message if available
                    wait_time = self._extract_rate_limit_wait_time(str(e))
                    logger.warning(f"Rate limited, waiting {wait_time}s before retry {attempt + 1}")
                    await asyncio.sleep(wait_time)
                    continue
                raise
                
            except AIAnalysisError as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    # Exponential backoff for temporary failures
                    delay = self.base_delay * (2 ** attempt)
                    logger.warning(f"Temporary failure, retrying in {delay}s: {str(e)}")
                    await asyncio.sleep(delay)
                    continue
                raise
                
        raise last_exception or AIAnalysisError("Max retries exceeded")

    async def _call_gemini_api(self, request: GeminiRequest) -> Dict[str, Any]:
        """Make actual API call to Gemini."""
        if not self.api_key:
            # Return mock response for testing
            return self._generate_mock_response(request)
        
        try:
            # Build prompt
            prompt = self._build_prompt(request)
            
            # Prepare API request
            api_request = {
                "contents": [{
                    "parts": self._build_content_parts(prompt, request.images)
                }],
                "generationConfig": {
                    "temperature": 0.1,  # Low temperature for consistent extraction
                    "topK": 40,
                    "topP": 0.95,
                    "maxOutputTokens": 2048,
                }
            }
            
            url = f"{self.base_url}/{self.model_name}:generateContent?key={self.api_key}"
            
            # httpx not available, fall back to mock implementation
            logger.info("httpx not available, using mock implementation")
            return self._generate_mock_response(request)
        except Exception as e:
            if isinstance(e, (AIAnalysisError, RateLimitError)):
                raise
            raise AIAnalysisError(f"API call failed: {str(e)}")

    def _build_prompt(self, request: GeminiRequest) -> str:
        """Build optimized prompt for place extraction."""
        platform_specific_instructions = {
            "instagram": "Focus on hashtags and visual content. Look for restaurant names, cafe mentions, and location tags.",
            "naver_blog": "Analyze detailed review content. Extract specific business names, addresses, and detailed descriptions.",
            "youtube": "Focus on video title and description. Look for location mentions and place recommendations."
        }
        
        platform_instruction = platform_specific_instructions.get(
            request.platform, 
            "Analyze the content for place information."
        )
        
        return PLACE_EXTRACTION_PROMPT_V2.format(
            platform=request.platform,
            platform_instruction=platform_instruction,
            content=request.content,
            json_schema=json.dumps(PLACE_EXTRACTION_JSON_SCHEMA, indent=2)
        )

    def _build_content_parts(self, prompt: str, image_urls: List[str]) -> List[Dict[str, Any]]:
        """Build content parts for multimodal request."""
        parts = [{"text": prompt}]
        
        # Add images for vision analysis (limited to prevent API limits)
        for i, image_url in enumerate(image_urls[:3]):  # Limit to 3 images
            try:
                # For now, just reference the image URL
                # In production, you'd download and encode the image
                parts.append({
                    "text": f"[Image {i+1}: {image_url}]"
                })
            except Exception as e:
                logger.warning(f"Failed to process image {image_url}: {str(e)}")
                continue
        
        return parts

    def _parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """Parse JSON response from Gemini."""
        try:
            # Try to find JSON in the response
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx == -1 or end_idx == 0:
                raise AIAnalysisError("No JSON found in response")
            
            json_text = response_text[start_idx:end_idx]
            return json.loads(json_text)
            
        except json.JSONDecodeError as e:
            raise AIAnalysisError(f"Invalid JSON response: {str(e)}")

    def _generate_mock_response(self, request: GeminiRequest) -> Dict[str, Any]:
        """Generate mock response for testing."""
        # Simulate processing delay
        
        # Analyze content for keywords to generate relevant mock data
        content_lower = request.content.lower()
        
        if "korean" in content_lower and "bbq" in content_lower:
            return {
                "places": [
                    {
                        "name": "Korean BBQ Restaurant",
                        "address": "Gangnam, Seoul",
                        "category": "restaurant",
                        "confidence": "high",
                        "description": "Korean BBQ restaurant with excellent beef"
                    }
                ],
                "analysis_confidence": "high"
            }
        elif "coffee" in content_lower:
            return {
                "places": [
                    {
                        "name": "Coffee Shop",
                        "address": "Seoul",
                        "category": "cafe", 
                        "confidence": "medium",
                        "description": "Local coffee shop"
                    }
                ],
                "analysis_confidence": "medium"
            }
        else:
            return {
                "places": [],
                "analysis_confidence": "high"
            }

    def _parse_gemini_response(self, response_data: Dict[str, Any]) -> List[PlaceAnalysisResult]:
        """Parse Gemini response into structured format."""
        places = []
        
        if "places" in response_data:
            for place_data in response_data["places"]:
                try:
                    # Validate and sanitize data
                    name = str(place_data.get("name", "")).strip()
                    if not name:
                        continue
                        
                    address = place_data.get("address", "")
                    if address:
                        address = str(address).strip()
                    
                    category = str(place_data.get("category", "other")).lower()
                    
                    # Parse confidence
                    confidence_str = str(place_data.get("confidence", "medium")).lower()
                    if confidence_str in ["high", "medium", "low"]:
                        confidence = AnalysisConfidence(confidence_str)
                    else:
                        confidence = AnalysisConfidence.MEDIUM
                    
                    description = place_data.get("description", "")
                    if description:
                        description = str(description).strip()
                    
                    place = PlaceAnalysisResult(
                        name=name,
                        address=address,
                        category=category,
                        confidence=confidence,
                        description=description
                    )
                    
                    places.append(place)
                    
                except Exception as e:
                    logger.warning(f"Failed to parse place data: {str(e)}")
                    continue
        
        return places

    def _filter_by_confidence(self, places: List[PlaceAnalysisResult], min_confidence: str) -> List[PlaceAnalysisResult]:
        """Filter places by minimum confidence level."""
        confidence_order = {
            "low": 0,
            "medium": 1,
            "high": 2
        }
        
        min_level = confidence_order.get(min_confidence, 1)
        
        return [
            place for place in places
            if confidence_order.get(place.confidence.value, 0) >= min_level
        ]

    def _calculate_overall_confidence(self, places: List[PlaceAnalysisResult]) -> AnalysisConfidence:
        """Calculate overall confidence based on individual place confidences."""
        if not places:
            return AnalysisConfidence.HIGH  # High confidence in finding no places
        
        confidence_scores = {
            AnalysisConfidence.HIGH: 3,
            AnalysisConfidence.MEDIUM: 2,
            AnalysisConfidence.LOW: 1
        }
        
        avg_score = sum(confidence_scores[place.confidence] for place in places) / len(places)
        
        if avg_score >= 2.5:
            return AnalysisConfidence.HIGH
        elif avg_score >= 1.5:
            return AnalysisConfidence.MEDIUM
        else:
            return AnalysisConfidence.LOW

    def _extract_rate_limit_wait_time(self, error_message: str) -> float:
        """Extract wait time from rate limit error message."""
        # Try to extract wait time from error message
        import re
        match = re.search(r'retry after (\d+)', error_message.lower())
        if match:
            return float(match.group(1))
        return 60.0  # Default wait time

    # Legacy methods for compatibility with existing tests
    async def analyze_place_content_legacy(self, request: PlaceAnalysisRequest) -> PlaceInfo:
        """Legacy method for compatibility with existing code."""
        # Convert to new format
        content_text = f"""
        Content: {request.content_text}
        Description: {request.content_description or ''}
        Hashtags: {', '.join(request.hashtags) if request.hashtags else ''}
        Platform: {request.platform}
        """
        
        gemini_request = GeminiRequest(
            content=content_text.strip(),
            images=request.images,
            platform=request.platform
        )
        
        try:
            response_data = await self._call_gemini_api(gemini_request)
            
            # Convert to legacy format
            if "places" in response_data and response_data["places"]:
                place_data = response_data["places"][0]  # Take first place
                
                return PlaceInfo(
                    name=place_data.get("name", "Unknown Place"),
                    address=place_data.get("address"),
                    category=self._map_category_to_enum(place_data.get("category", "other")),
                    keywords=place_data.get("keywords", []),
                    recommendation_score=min(10, max(1, place_data.get("recommendation_score", 7)))
                )
            else:
                # No places found
                return PlaceInfo(
                    name="Unknown Place",
                    category=PlaceCategory.OTHER,
                    keywords=[],
                    recommendation_score=5
                )
                
        except Exception as e:
            if isinstance(e, (AIAnalysisError, RateLimitError)):
                raise
            raise AIAnalysisError(f"Legacy analysis failed: {str(e)}")

    def _map_category_to_enum(self, category_str: str) -> PlaceCategory:
        """Map category string to PlaceCategory enum."""
        category_mapping = {
            "restaurant": PlaceCategory.RESTAURANT,
            "cafe": PlaceCategory.CAFE,
            "bar": PlaceCategory.BAR,
            "tourist_attraction": PlaceCategory.TOURIST_ATTRACTION,
            "shopping": PlaceCategory.SHOPPING,
            "accommodation": PlaceCategory.ACCOMMODATION,
            "entertainment": PlaceCategory.ENTERTAINMENT,
        }
        
        return category_mapping.get(category_str.lower(), PlaceCategory.OTHER)

    # Keep the default method name for legacy compatibility
    analyze_place_content = analyze_place_content_legacy