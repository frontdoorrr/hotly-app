"""Instagram metadata extraction using yt-dlp."""

import yt_dlp
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

from .base import PlatformExtractor, Platform, ContentType


class InstagramExtractor(PlatformExtractor):
    """yt-dlp based Instagram metadata extraction and download."""

    def __init__(self, download_dir: str = "temp"):
        """
        Initialize Instagram extractor.

        Args:
            download_dir: Directory to store downloaded media files
        """
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)

    async def extract_metadata(self, url: str) -> Dict[str, Any]:
        """
        Extract Instagram post metadata and download media.

        Args:
            url: Instagram post URL

        Returns:
            Dictionary containing:
                - platform: 'instagram'
                - content_type: 'video|image|carousel'
                - url: Original URL
                - title: Post caption
                - description: Caption text
                - hashtags: List of hashtags
                - location: Optional location info
                - media_urls: List of downloaded file paths
                - timestamp: Post creation time

        Raises:
            ValueError: If URL is invalid or post not accessible
            Exception: If download fails
        """
        ydl_opts = {
            'format': 'best',
            'outtmpl': str(self.download_dir / '%(id)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                return self._parse_info(info, url)

        except Exception as e:
            raise ValueError(f"Failed to extract Instagram content: {e}")

    def _parse_info(self, info: Dict, original_url: str) -> Dict[str, Any]:
        """
        Parse yt-dlp extracted info.

        Args:
            info: yt-dlp info dictionary
            original_url: Original Instagram URL

        Returns:
            Standardized metadata dictionary
        """
        # Extract caption and hashtags
        caption = info.get('description', '')
        hashtags = self._extract_hashtags(caption)

        # Determine content type
        content_type = ContentType.VIDEO if info.get('ext') in ['mp4', 'mov'] else ContentType.IMAGE

        # Get downloaded file path
        downloaded_file = self.download_dir / f"{info.get('id')}.{info.get('ext')}"

        return {
            'platform': Platform.INSTAGRAM.value,
            'content_type': content_type.value,
            'url': original_url,
            'title': caption[:100] if caption else '',  # First 100 chars
            'description': caption,
            'hashtags': hashtags,
            'location': info.get('location'),
            'media_urls': [str(downloaded_file)],
            'timestamp': self._parse_timestamp(info.get('timestamp')),
            'metadata': {
                'post_id': info.get('id'),
                'uploader': info.get('uploader'),
                'like_count': info.get('like_count'),
                'comment_count': info.get('comment_count'),
                'duration': info.get('duration') if content_type == ContentType.VIDEO else None,
            }
        }

    @staticmethod
    def _extract_hashtags(text: str) -> List[str]:
        """
        Extract hashtags from caption text.

        Args:
            text: Caption text

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
