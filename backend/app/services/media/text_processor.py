"""Text processing module for multimodal analysis."""

import re
from typing import List


class TextProcessor:
    """Text cleaning and extraction processor."""

    async def clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        if not text:
            return ""

        # Remove excessive whitespace
        cleaned = re.sub(r"\s+", " ", text)

        # Remove special characters (keep Korean, English, numbers, basic punctuation)
        cleaned = re.sub(r"[^\w\s가-힣a-zA-Z0-9.,!?@#-]", "", cleaned)

        # Trim
        cleaned = cleaned.strip()

        return cleaned

    async def extract_hashtags(self, text: str) -> List[str]:
        """Extract hashtags from text."""
        if not text:
            return []

        # Find all hashtags (#태그)
        hashtags = re.findall(r"#(\w+)", text)

        # Remove duplicates while preserving order
        seen = set()
        unique_hashtags = []
        for tag in hashtags:
            if tag not in seen:
                seen.add(tag)
                unique_hashtags.append(tag)

        return unique_hashtags[:50]  # Limit to 50

    async def extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text (simple approach)."""
        if not text:
            return []

        # Clean text
        cleaned = await self.clean_text(text)

        # Split by whitespace
        words = cleaned.split()

        # Filter short words (< 2 characters)
        keywords = [w for w in words if len(w) >= 2]

        # Remove duplicates
        keywords = list(dict.fromkeys(keywords))

        return keywords[:20]  # Limit to 20

    async def extract_location_hints(self, text: str) -> List[str]:
        """Extract location hints from text."""
        if not text:
            return []

        location_hints = []

        # Korean city/district patterns
        korean_locations = re.findall(
            r"(서울|부산|대구|인천|광주|대전|울산|세종|경기|강원|충북|충남|전북|전남|경북|경남|제주)",
            text,
        )
        location_hints.extend(korean_locations)

        # District patterns (동/구/시)
        districts = re.findall(r"(\w+(?:동|구|시))", text)
        location_hints.extend(districts)

        # Remove duplicates
        location_hints = list(dict.fromkeys(location_hints))

        return location_hints[:10]  # Limit to 10
