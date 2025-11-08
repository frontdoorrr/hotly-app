"""TikTok metadata extraction using yt-dlp."""

import yt_dlp
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

from .base import PlatformExtractor, Platform, ContentType


class TikTokExtractor(PlatformExtractor):
    """yt-dlp based TikTok metadata extraction and download."""

    def __init__(self, download_dir: str = "temp"):
        """
        Initialize TikTok extractor.

        Args:
            download_dir: Directory to store downloaded media files
        """
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)

    async def extract_metadata(self, url: str) -> Dict[str, Any]:
        """
        Extract TikTok video metadata and download.

        Args:
            url: TikTok video URL

        Returns:
            Dictionary containing:
                - platform: 'tiktok'
                - content_type: 'video'
                - url: Original URL
                - title: Video description
                - description: Full description text
                - hashtags: List of hashtags
                - media_urls: List of downloaded file paths
                - timestamp: Video creation time

        Raises:
            ValueError: If URL is invalid or video not accessible
            Exception: If download fails
        """
        ydl_opts = {
            'format': 'best',
            'outtmpl': str(self.download_dir / '%(id)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                return self._parse_info(info, url)

        except Exception as e:
            raise ValueError(f"Failed to extract TikTok content: {e}")

    def _parse_info(self, info: Dict, original_url: str) -> Dict[str, Any]:
        """
        Parse yt-dlp extracted info.

        Args:
            info: yt-dlp info dictionary
            original_url: Original TikTok URL

        Returns:
            Standardized metadata dictionary
        """
        # Extract description and hashtags
        description = info.get('description', '')
        hashtags = self._extract_hashtags(description)

        # Get downloaded file path
        downloaded_file = self.download_dir / f"{info.get('id')}.{info.get('ext', 'mp4')}"

        return {
            'platform': Platform.TIKTOK.value,
            'content_type': ContentType.VIDEO.value,
            'url': original_url,
            'title': description[:100] if description else '',  # First 100 chars
            'description': description,
            'hashtags': hashtags,
            'media_urls': [str(downloaded_file)],
            'timestamp': self._parse_timestamp(info.get('timestamp')),
            'metadata': {
                'video_id': info.get('id'),
                'uploader': info.get('uploader') or info.get('creator'),
                'uploader_id': info.get('uploader_id'),
                'view_count': info.get('view_count'),
                'like_count': info.get('like_count'),
                'comment_count': info.get('comment_count'),
                'duration': info.get('duration'),
                'music': {
                    'title': info.get('track'),
                    'author': info.get('artist'),
                }
            }
        }

    @staticmethod
    def _extract_hashtags(text: str) -> List[str]:
        """
        Extract hashtags from description text.

        Args:
            text: Description text

        Returns:
            List of hashtags (without # symbol)
        """
        import re
        return re.findall(r'#(\w+)', text)

    @staticmethod
    def _parse_timestamp(timestamp: Optional[int]) -> Optional[str]:
        """
        Parse Unix timestamp to ISO format.

        Args:
            timestamp: Unix timestamp

        Returns:
            ISO format datetime string or None
        """
        if timestamp:
            return datetime.fromtimestamp(timestamp).isoformat()
        return None
