"""Integrated link analysis service combining all components."""

import os
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from app.services.platform.base import PlatformExtractor, Platform, ContentType
from app.services.platform.youtube import YouTubeExtractor
from app.services.platform.instagram import InstagramExtractor
from app.services.platform.tiktok import TikTokExtractor
from app.services.analysis.gemini_video import GeminiVideoAnalyzer
from app.services.analysis.gemini_image import GeminiImageAnalyzer
from app.services.analysis.content_classifier import ContentClassifier
from app.schemas.analysis import AnalysisRequest, AnalysisResponse


class LinkAnalyzerService:
    """
    Integrated service for analyzing social media links.

    Pipeline:
    1. Detect platform from URL
    2. Extract metadata (title, description, etc.)
    3. Analyze content with Gemini (video/image)
    4. Classify and extract information
    5. Return structured results
    """

    def __init__(
        self,
        youtube_api_key: str,
        gemini_api_key: str,
        download_dir: str = "temp"
    ):
        """
        Initialize link analyzer service.

        Args:
            youtube_api_key: YouTube Data API v3 key
            gemini_api_key: Google Gemini API key
            download_dir: Directory for downloaded media files
        """
        # Platform extractors
        self.youtube_extractor = YouTubeExtractor(api_key=youtube_api_key)
        self.instagram_extractor = InstagramExtractor(download_dir=download_dir)
        self.tiktok_extractor = TikTokExtractor(download_dir=download_dir)

        # Gemini analyzers
        self.video_analyzer = GeminiVideoAnalyzer(api_key=gemini_api_key)
        self.image_analyzer = GeminiImageAnalyzer(api_key=gemini_api_key)
        self.classifier = ContentClassifier(api_key=gemini_api_key)

        self.download_dir = Path(download_dir)

    async def analyze(self, url: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Analyze social media link end-to-end.

        Args:
            url: Social media URL (YouTube, Instagram, TikTok)
            options: Optional analysis options

        Returns:
            Dictionary containing:
                - platform: Detected platform
                - content_type: video/image/carousel
                - metadata: Platform-specific metadata
                - video_analysis: Gemini video analysis (if applicable)
                - image_analysis: Gemini image analysis (if applicable)
                - classification: AI classification results
                - analyzed_at: Timestamp

        Raises:
            ValueError: If URL is invalid or platform not supported
        """
        if options is None:
            options = {}

        # Step 1: Detect platform
        platform = PlatformExtractor.detect_platform(url)
        if platform is None:
            raise ValueError(f"Unsupported platform or invalid URL: {url}")

        # Step 2: Extract metadata
        metadata = await self._extract_metadata(platform, url)

        # Step 3: Analyze content
        video_analysis = None
        image_analysis = None

        if metadata['content_type'] == ContentType.VIDEO:
            video_analysis = await self._analyze_video(platform, metadata, url)
        elif metadata['content_type'] == ContentType.IMAGE:
            image_analysis = await self._analyze_image(metadata)
        elif metadata['content_type'] == ContentType.CAROUSEL:
            # For carousel, analyze all media
            video_analysis = await self._analyze_video(platform, metadata, url) if metadata.get('has_video') else None
            image_analysis = await self._analyze_image(metadata) if metadata.get('has_image') else None

        # Step 4: Classify content
        classification = await self._classify_content(metadata, video_analysis, image_analysis)

        # Step 5: Build result
        result = {
            'url': url,
            'platform': platform.value,
            'content_type': metadata['content_type'] if isinstance(metadata['content_type'], str) else metadata['content_type'].value,
            'metadata': metadata,
            'video_analysis': video_analysis,
            'image_analysis': image_analysis,
            'classification': classification,
            'analyzed_at': datetime.utcnow().isoformat()
        }

        # Step 6: Cleanup temporary files
        await self._cleanup_temp_files(metadata)

        return result

    async def _extract_metadata(self, platform: Platform, url: str) -> Dict[str, Any]:
        """Extract platform-specific metadata."""
        if platform == Platform.YOUTUBE:
            return await self.youtube_extractor.extract_metadata(url)
        elif platform == Platform.INSTAGRAM:
            return await self.instagram_extractor.extract_metadata(url)
        elif platform == Platform.TIKTOK:
            return await self.tiktok_extractor.extract_metadata(url)
        else:
            raise ValueError(f"Unsupported platform: {platform}")

    async def _analyze_video(
        self,
        platform: Platform,
        metadata: Dict[str, Any],
        url: str
    ) -> Optional[Dict[str, Any]]:
        """
        Analyze video content with Gemini.

        YouTube: Use URL directly (no download)
        Instagram/TikTok: Use downloaded file
        """
        prompt = self._build_video_analysis_prompt(metadata)

        try:
            if platform == Platform.YOUTUBE:
                # YouTube: Direct URL analysis (no download)
                return await self.video_analyzer.analyze_video_url(url, prompt)
            else:
                # Instagram/TikTok: File analysis
                if 'media_urls' in metadata and metadata['media_urls']:
                    file_path = metadata['media_urls'][0]  # First video file
                    return await self.video_analyzer.analyze_video_file(file_path, prompt)
                return None
        except Exception as e:
            print(f"Video analysis failed: {e}")
            return {'error': str(e)}

    async def _analyze_image(self, metadata: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Analyze image content with Gemini."""
        prompt = self._build_image_analysis_prompt(metadata)

        try:
            if 'media_urls' in metadata and metadata['media_urls']:
                # Use first image file
                for media_path in metadata['media_urls']:
                    if media_path.endswith(('.jpg', '.jpeg', '.png', '.webp')):
                        return await self.image_analyzer.analyze_image(media_path, prompt)
            return None
        except Exception as e:
            print(f"Image analysis failed: {e}")
            return {'error': str(e)}

    async def _classify_content(
        self,
        metadata: Dict[str, Any],
        video_analysis: Optional[Dict[str, Any]],
        image_analysis: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Classify content using AI."""
        # Build content data for classification
        content_data = {
            'caption': metadata.get('title') or metadata.get('description', ''),
            'ocr_texts': [],
            'transcript': None,
            'hashtags': metadata.get('hashtags', []),
            'location': metadata.get('location')
        }

        # Extract OCR texts from video analysis
        if video_analysis and 'extracted_text' in video_analysis:
            content_data['ocr_texts'].extend(video_analysis['extracted_text'])

        # Extract transcript from video analysis
        if video_analysis and 'transcript' in video_analysis:
            content_data['transcript'] = video_analysis['transcript']

        # Extract OCR from image analysis
        if image_analysis and 'extracted_text' in image_analysis:
            content_data['ocr_texts'].append(image_analysis['extracted_text'])

        try:
            return await self.classifier.classify(content_data)
        except Exception as e:
            print(f"Classification failed: {e}")
            return {'error': str(e)}

    def _build_video_analysis_prompt(self, metadata: Dict[str, Any]) -> str:
        """Build optimized prompt for video analysis."""
        return """
        Analyze this video and extract the following information:

        1. **Transcript**: Transcribe all spoken audio
        2. **Visible Text**: Extract any text shown in the video (signs, menus, subtitles, etc.)
        3. **Visual Elements**: Describe key scenes, objects, and activities
        4. **Summary**: Brief 2-3 sentence summary

        Focus on:
        - Restaurant/cafe information (name, menu, prices)
        - Location/place information
        - Product information
        - Any Korean text visible

        Return structured information.
        """

    def _build_image_analysis_prompt(self, metadata: Dict[str, Any]) -> str:
        """Build optimized prompt for image analysis."""
        return """
        Analyze this image and extract:

        1. **Text (OCR)**: All visible text (signs, menus, prices, etc.)
        2. **Objects**: Main objects and elements in the image
        3. **Scene**: Overall scene description

        Focus on:
        - Restaurant/cafe menu boards
        - Store signs and names
        - Price information
        - Korean text

        Return structured information.
        """

    async def _cleanup_temp_files(self, metadata: Dict[str, Any]):
        """Clean up temporary downloaded files."""
        if 'media_urls' in metadata and metadata['media_urls']:
            for file_path in metadata['media_urls']:
                try:
                    path = Path(file_path)
                    if path.exists():
                        path.unlink()
                except Exception as e:
                    print(f"Failed to cleanup {file_path}: {e}")
