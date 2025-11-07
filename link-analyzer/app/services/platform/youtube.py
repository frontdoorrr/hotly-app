"""YouTube metadata extraction using YouTube Data API v3."""

import re
from typing import Dict, Any, Optional
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from .base import PlatformExtractor, Platform, ContentType


class YouTubeExtractor(PlatformExtractor):
    """YouTube Data API v3 based metadata extraction."""

    def __init__(self, api_key: str):
        """
        Initialize YouTube extractor.

        Args:
            api_key: YouTube Data API v3 key
        """
        self.youtube = build('youtube', 'v3', developerKey=api_key)

    async def extract_metadata(self, url: str) -> Dict[str, Any]:
        """
        Extract YouTube video metadata.

        Args:
            url: YouTube video URL

        Returns:
            Dictionary containing:
                - platform: 'youtube'
                - content_type: 'video'
                - video_id: YouTube video ID
                - title: Video title
                - description: Video description
                - tags: List of tags
                - channel_title: Channel name
                - published_at: Publication datetime
                - duration: Video duration (ISO 8601)
                - view_count: View count
                - media_urls: None (YouTube doesn't require download)

        Raises:
            ValueError: If URL is invalid or video not found
            HttpError: If YouTube API returns an error
        """
        video_id = self._extract_video_id(url)

        try:
            response = self.youtube.videos().list(
                part='snippet,contentDetails,statistics',
                id=video_id
            ).execute()

            if not response.get('items'):
                raise ValueError(f"Video not found: {video_id}")

            return self._parse_response(response['items'][0], url)

        except HttpError as e:
            raise ValueError(f"YouTube API error: {e}")

    def _extract_video_id(self, url: str) -> str:
        """
        Extract video ID from YouTube URL.

        Supports:
            - youtube.com/watch?v=VIDEO_ID
            - youtu.be/VIDEO_ID
            - youtube.com/shorts/VIDEO_ID

        Args:
            url: YouTube URL

        Returns:
            Video ID string

        Raises:
            ValueError: If URL format is invalid
        """
        # Standard watch URL
        match = re.search(r'[?&]v=([^&]+)', url)
        if match:
            return match.group(1)

        # Short URL (youtu.be)
        match = re.search(r'youtu\.be/([^?]+)', url)
        if match:
            return match.group(1)

        # Shorts URL
        match = re.search(r'/shorts/([^?]+)', url)
        if match:
            return match.group(1)

        raise ValueError(f"Could not extract video ID from URL: {url}")

    def _parse_response(self, item: Dict[str, Any], original_url: str) -> Dict[str, Any]:
        """
        Parse YouTube API response.

        Args:
            item: YouTube API response item
            original_url: Original URL

        Returns:
            Standardized metadata dictionary
        """
        snippet = item.get('snippet', {})
        content_details = item.get('contentDetails', {})
        statistics = item.get('statistics', {})

        return {
            'platform': Platform.YOUTUBE.value,
            'content_type': ContentType.VIDEO.value,
            'url': original_url,
            'video_id': item.get('id'),
            'title': snippet.get('title', ''),
            'description': snippet.get('description', ''),
            'hashtags': snippet.get('tags', []),
            'channel_title': snippet.get('channelTitle', ''),
            'published_at': snippet.get('publishedAt'),
            'duration': content_details.get('duration'),
            'view_count': int(statistics.get('viewCount', 0)),
            'media_urls': None,  # YouTube doesn't require download
            'metadata': {
                'channel_id': snippet.get('channelId'),
                'category_id': snippet.get('categoryId'),
                'thumbnails': snippet.get('thumbnails', {}),
                'is_shorts': self.is_shorts(original_url)
            }
        }

    @staticmethod
    def is_shorts(url: str) -> bool:
        """
        Check if URL is YouTube Shorts.

        Args:
            url: YouTube URL

        Returns:
            True if Shorts, False otherwise
        """
        return "/shorts/" in url
