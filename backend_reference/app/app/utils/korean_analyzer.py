"""Korean text analysis utilities for search optimization."""

import logging
import re
from typing import Dict, List

logger = logging.getLogger(__name__)


class KoreanAnalyzer:
    """Korean text analysis and processing utilities."""

    def __init__(self):
        # Common Korean stopwords
        self.stopwords = {
            "이",
            "가",
            "을",
            "를",
            "에",
            "에서",
            "에게",
            "으로",
            "로",
            "과",
            "와",
            "그리고",
            "하지만",
            "그런데",
            "그러나",
            "또한",
            "또",
            "매우",
            "정말",
            "아주",
            "좀",
            "좀더",
            "것",
            "거",
            "게",
            "게서",
            "께",
            "께서",
            "한테",
            "에게서",
            "로부터",
            "부터",
            "의",
            "도",
            "만",
            "까지",
            "마저",
            "조차",
            "밖에",
            "뿐",
            "이나",
            "나",
        }

        # Common place-related keywords for boosting
        self.place_keywords = {
            "카페",
            "커피",
            "음식점",
            "레스토랑",
            "식당",
            "바",
            "술집",
            "호텔",
            "모텔",
            "숙박",
            "관광지",
            "명소",
            "박물관",
            "공원",
            "쇼핑몰",
            "마트",
            "편의점",
            "병원",
            "약국",
            "은행",
            "영화관",
            "노래방",
            "pc방",
            "찜질방",
            "스파",
        }

    def analyze_text(self, text: str) -> Dict[str, any]:
        """
        Analyze Korean text and extract meaningful components.

        Args:
            text: Input text to analyze

        Returns:
            Dictionary with analysis results including keywords, entities, etc.
        """
        try:
            if not text:
                return {"keywords": [], "entities": [], "cleaned_text": ""}

            # Clean and normalize text
            cleaned_text = self._normalize_text(text)

            # Extract keywords using simple heuristics
            keywords = self._extract_keywords_heuristic(cleaned_text)

            # Identify named entities (places, brands)
            entities = self._identify_entities(cleaned_text)

            # Calculate text complexity
            complexity = self._calculate_complexity(cleaned_text)

            return {
                "keywords": keywords,
                "entities": entities,
                "cleaned_text": cleaned_text,
                "complexity": complexity,
                "word_count": len(keywords),
                "has_place_keywords": any(kw in self.place_keywords for kw in keywords),
            }

        except Exception as e:
            logger.error(f"Error analyzing text: {e}")
            return {"keywords": [text], "entities": [], "cleaned_text": text}

    def extract_keywords(self, text: str) -> List[str]:
        """
        Extract keywords from Korean text.

        Args:
            text: Input text

        Returns:
            List of extracted keywords
        """
        try:
            cleaned_text = self._normalize_text(text)
            return self._extract_keywords_heuristic(cleaned_text)
        except Exception as e:
            logger.error(f"Error extracting keywords: {e}")
            return [text] if text else []

    def calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate similarity between two Korean texts.

        Args:
            text1, text2: Texts to compare

        Returns:
            Similarity score (0.0 - 1.0)
        """
        try:
            if not text1 or not text2:
                return 0.0

            # Extract keywords from both texts
            keywords1 = set(self.extract_keywords(text1.lower()))
            keywords2 = set(self.extract_keywords(text2.lower()))

            if not keywords1 or not keywords2:
                return 0.0

            # Calculate Jaccard similarity
            intersection = len(keywords1.intersection(keywords2))
            union = len(keywords1.union(keywords2))

            jaccard_similarity = intersection / union if union > 0 else 0.0

            # Boost similarity if exact substring match exists
            if text1.lower() in text2.lower() or text2.lower() in text1.lower():
                jaccard_similarity = min(1.0, jaccard_similarity + 0.2)

            return jaccard_similarity

        except Exception as e:
            logger.error(f"Error calculating similarity: {e}")
            return 0.0

    def generate_search_variants(self, query: str) -> List[str]:
        """
        Generate search variants for typo tolerance.

        Args:
            query: Original search query

        Returns:
            List of query variants
        """
        try:
            variants = [query]

            # Common Korean typo patterns
            typo_mappings = {
                "ㅋ": "크",
                "ㅍ": "프",
                "ㅌ": "트",
                "ㅊ": "치",
                "패": "페",
                "카패": "카페",
                "레스토링": "레스토랑",
                "맛집": "맛있는집",
                "분위기좋은": "분위기 좋은",
            }

            # Apply typo corrections
            corrected_query = query
            for typo, correct in typo_mappings.items():
                if typo in corrected_query:
                    corrected_query = corrected_query.replace(typo, correct)
                    if corrected_query != query:
                        variants.append(corrected_query)

            # Add spacing variants
            if len(query) > 4 and " " not in query:
                # Try to add space in the middle
                mid_point = len(query) // 2
                spaced_variant = query[:mid_point] + " " + query[mid_point:]
                variants.append(spaced_variant)

            # Remove duplicates while preserving order
            seen = set()
            unique_variants = []
            for variant in variants:
                if variant not in seen:
                    seen.add(variant)
                    unique_variants.append(variant)

            return unique_variants[:5]  # Limit variants

        except Exception as e:
            logger.error(f"Error generating search variants: {e}")
            return [query]

    def _normalize_text(self, text: str) -> str:
        """Normalize Korean text for processing."""
        if not text:
            return ""

        # Remove extra whitespace and special characters
        normalized = re.sub(r"\s+", " ", text.strip())

        # Remove common punctuation that doesn't help search
        normalized = re.sub(r'[!@#$%^&*()_+={}\[\]|\\:";\'<>?,.`~]', " ", normalized)

        # Normalize spacing around Korean text
        normalized = re.sub(r"\s+", " ", normalized)

        return normalized.strip()

    def _extract_keywords_heuristic(self, text: str) -> List[str]:
        """Extract keywords using heuristic approaches for Korean text."""
        if not text:
            return []

        # Split by whitespace and common delimiters
        words = re.split(r"[\s,./]+", text)

        # Filter keywords
        keywords = []
        for word in words:
            word = word.strip()

            # Skip if too short, too long, or is stopword
            if len(word) < 2 or len(word) > 20 or word in self.stopwords:
                continue

            # Skip if all numbers or special characters
            if re.match(r"^[\d\W]+$", word):
                continue

            keywords.append(word)

        # Remove duplicates while preserving order
        seen = set()
        unique_keywords = []
        for keyword in keywords:
            if keyword not in seen:
                seen.add(keyword)
                unique_keywords.append(keyword)

        return unique_keywords

    def _identify_entities(self, text: str) -> List[Dict[str, str]]:
        """Identify named entities in Korean text."""
        entities = []

        # Simple pattern matching for common entities
        patterns = {
            "brand": [
                r"스타벅스",
                r"투썸플레이스",
                r"이디야",
                r"맥도날드",
                r"버거킹",
                r"롯데리아",
                r"KFC",
                r"파파존스",
                r"피자헛",
                r"도미노피자",
            ],
            "location": [
                r"강남",
                r"홍대",
                r"명동",
                r"이태원",
                r"압구정",
                r"신사",
                r"가로수길",
                r"성수",
                r"연남",
                r"서촌",
                r"북촌",
                r"인사동",
                r"종로",
                r"을지로",
            ],
        }

        for entity_type, pattern_list in patterns.items():
            for pattern in pattern_list:
                if re.search(pattern, text, re.IGNORECASE):
                    entities.append(
                        {"text": pattern, "type": entity_type, "confidence": 0.8}
                    )

        return entities

    def _calculate_complexity(self, text: str) -> float:
        """Calculate text complexity score."""
        if not text:
            return 0.0

        # Simple complexity based on length and character variety
        char_variety = len(set(text)) / len(text) if text else 0
        length_factor = min(len(text) / 50, 1.0)  # Normalize to 0-1

        return (char_variety + length_factor) / 2
