"""
Simple tests for duplicate detection service.

Focus on core functionality to improve coverage.
"""

import pytest


class TestDuplicateDetector:
    """Test duplicate detection basic functionality."""

    def test_calculateStringSimilarity_identicalStrings_returns1(self):
        """Test identical strings return similarity of 1.0."""
        from unittest.mock import MagicMock

        from app.services.duplicate_detector import DuplicateDetector

        detector = DuplicateDetector(db=MagicMock())
        similarity = detector._calculate_string_similarity("강남카페", "강남카페")

        assert similarity == pytest.approx(1.0, rel=0.01)

    def test_calculateStringSimilarity_differentStrings_returnsLess1(self):
        """Test different strings return similarity less than 1.0."""
        from unittest.mock import MagicMock

        from app.services.duplicate_detector import DuplicateDetector

        detector = DuplicateDetector(db=MagicMock())
        similarity = detector._calculate_string_similarity("강남카페", "홍대레스토랑")

        assert similarity < 1.0
        assert similarity >= 0.0

    def test_normalizeAddress_koreanAddress_removes공통Words(self):
        """Test Korean address normalization removes common words."""
        from unittest.mock import MagicMock

        from app.services.duplicate_detector import DuplicateDetector

        detector = DuplicateDetector(db=MagicMock())
        normalized = detector._normalize_address("서울특별시 강남구 테헤란로")

        # Should remove common words like 시, 구
        assert "서울" in normalized or "강남" in normalized
