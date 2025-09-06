"""Tag normalization utilities for consistent tag management."""

import re
from collections import Counter
from typing import List


class TagNormalizer:
    """Utility class for tag normalization and management."""

    # Common tag synonyms for normalization
    SYNONYM_GROUPS = {
        "커피": ["cafe", "카페", "커피샵", "coffee", "까페"],
        "음식": ["음식점", "식당", "레스토랑", "restaurant", "food"],
        "술": ["술집", "바", "bar", "pub", "호프"],
        "쇼핑": ["shopping", "상점", "매장", "shop", "store"],
        "관광": ["관광지", "명소", "tourist", "attraction", "여행"],
        "숙박": ["호텔", "펜션", "게스트하우스", "accommodation", "hotel"],
        "오락": ["놀이", "엔터테인먼트", "entertainment", "게임", "노래방"],
        "힐링": ["휴식", "쉼", "rest", "relax", "치유"],
        "데이트": ["연인", "커플", "couple", "로맨틱", "romantic"],
        "가족": ["family", "아이", "children", "키즈", "kids"],
        "친구": ["friends", "모임", "gathering", "단체"],
        "혼자": ["혼밥", "혼술", "solo", "alone", "개인"],
        "실내": ["indoor", "건물", "실내공간"],
        "야외": ["outdoor", "밖", "외부", "테라스"],
        "조용": ["quiet", "평화", "peaceful", "차분"],
        "활기": ["시끌", "활발", "energetic", "lively"],
        "저렴": ["싸다", "cheap", "affordable", "가성비"],
        "고급": ["비싸다", "expensive", "luxury", "premium"],
        "맛집": ["delicious", "tasty", "맛있다", "famous"],
        "신상": ["new", "새로운", "최신", "오픈"],
    }

    # Stopwords to filter out
    STOPWORDS = {
        "이",
        "가",
        "을",
        "를",
        "의",
        "에",
        "와",
        "과",
        "도",
        "로",
        "으로",
        "은",
        "는",
        "한",
        "하는",
        "되는",
        "있는",
        "없는",
        "좋은",
        "나쁜",
        "the",
        "a",
        "an",
        "and",
        "or",
        "but",
        "in",
        "on",
        "at",
        "to",
        "for",
        "of",
        "with",
        "by",
        "very",
        "so",
        "too",
        "more",
        "most",
        "good",
        "bad",
    }

    @classmethod
    def normalize_tag(cls, tag: str) -> str:
        """
        Normalize a single tag.

        Args:
            tag: Raw tag string

        Returns:
            Normalized tag string
        """
        if not tag or not tag.strip():
            return ""

        # Basic cleanup
        normalized = tag.strip().lower()

        # Remove special characters except Korean, English, numbers
        normalized = re.sub(r"[^\w가-힣]", "", normalized)

        # Remove stopwords
        if normalized in cls.STOPWORDS:
            return ""

        # Apply synonym normalization
        for canonical, synonyms in cls.SYNONYM_GROUPS.items():
            if normalized in synonyms:
                return canonical

        # Length validation (2-20 characters)
        if len(normalized) < 2 or len(normalized) > 20:
            return ""

        return normalized

    @classmethod
    def normalize_tags(cls, tags: List[str]) -> List[str]:
        """
        Normalize a list of tags and remove duplicates.

        Args:
            tags: List of raw tag strings

        Returns:
            List of normalized, unique tags
        """
        if not tags:
            return []

        normalized_tags = []
        seen_tags = set()

        for tag in tags:
            normalized = cls.normalize_tag(tag)
            if normalized and normalized not in seen_tags:
                normalized_tags.append(normalized)
                seen_tags.add(normalized)

        return normalized_tags

    @classmethod
    def extract_tags_from_text(cls, text: str, max_tags: int = 10) -> List[str]:
        """
        Extract potential tags from text content.

        Args:
            text: Text content to extract tags from
            max_tags: Maximum number of tags to extract

        Returns:
            List of extracted tags
        """
        if not text:
            return []

        # Split text into words
        words = re.findall(r"[\w가-힣]+", text.lower())

        # Filter and normalize words
        candidates = []
        for word in words:
            if len(word) >= 2 and word not in cls.STOPWORDS:
                normalized = cls.normalize_tag(word)
                if normalized:
                    candidates.append(normalized)

        # Count frequency and return top candidates
        word_counts = Counter(candidates)
        return [word for word, count in word_counts.most_common(max_tags)]

    @classmethod
    def suggest_similar_tags(cls, tag: str, existing_tags: List[str]) -> List[str]:
        """
        Suggest similar existing tags based on edit distance.

        Args:
            tag: Input tag to find similar matches for
            existing_tags: List of existing tags in the system

        Returns:
            List of similar tags sorted by similarity
        """
        if not tag or not existing_tags:
            return []

        normalized_input = cls.normalize_tag(tag)
        if not normalized_input:
            return []

        suggestions = []

        for existing_tag in existing_tags:
            # Skip exact matches
            if existing_tag == normalized_input:
                continue

            # Calculate similarity score (simple edit distance approximation)
            similarity = cls._calculate_similarity(normalized_input, existing_tag)

            if similarity > 0.6:  # 60% similarity threshold
                suggestions.append((existing_tag, similarity))

        # Sort by similarity and return top 5
        suggestions.sort(key=lambda x: x[1], reverse=True)
        return [tag for tag, score in suggestions[:5]]

    @classmethod
    def _calculate_similarity(cls, tag1: str, tag2: str) -> float:
        """
        Calculate similarity between two tags using simple metrics.

        Args:
            tag1: First tag
            tag2: Second tag

        Returns:
            Similarity score between 0.0 and 1.0
        """
        if not tag1 or not tag2:
            return 0.0

        # Check if one is substring of another
        if tag1 in tag2 or tag2 in tag1:
            return 0.8

        # Check common characters ratio
        set1 = set(tag1)
        set2 = set(tag2)

        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))

        if union == 0:
            return 0.0

        return intersection / union

    @classmethod
    def categorize_tags(cls, tags: List[str]) -> dict:
        """
        Categorize tags into semantic groups.

        Args:
            tags: List of tags to categorize

        Returns:
            Dictionary with category as key and list of tags as value
        """
        categories = {"장소타입": [], "분위기": [], "대상": [], "가격": [], "특징": [], "기타": []}

        # Category mapping based on synonym groups
        category_mapping = {
            "커피": "장소타입",
            "음식": "장소타입",
            "술": "장소타입",
            "쇼핑": "장소타입",
            "관광": "장소타입",
            "숙박": "장소타입",
            "오락": "장소타입",
            "조용": "분위기",
            "활기": "분위기",
            "힐링": "분위기",
            "데이트": "대상",
            "가족": "대상",
            "친구": "대상",
            "혼자": "대상",
            "저렴": "가격",
            "고급": "가격",
            "실내": "특징",
            "야외": "특징",
            "맛집": "특징",
            "신상": "특징",
        }

        for tag in tags:
            category = "기타"  # Default category

            # Find category for tag
            for canonical, cat in category_mapping.items():
                if tag == canonical or tag in cls.SYNONYM_GROUPS.get(canonical, []):
                    category = cat
                    break

            categories[category].append(tag)

        # Remove empty categories
        return {k: v for k, v in categories.items() if v}
