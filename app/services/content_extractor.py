"""Content extraction service for SNS link analysis."""

import asyncio
import time
import re
from typing import List, Optional
from urllib.parse import urlparse

from app.exceptions.external import UnsupportedPlatformError, ContentExtractionError
from app.schemas.content import ContentMetadata, ExtractedContent, PlatformType


class ContentExtractor:
    """Extract content and metadata from SNS links."""

    def __init__(self) -> None:
        """Initialize content extractor."""
        self.timeout = 30  # 30 seconds timeout

    def _detect_platform(self, url: str) -> PlatformType:
        """Detect platform from URL."""
        parsed = urlparse(url)
        domain = parsed.netloc.lower()

        if "instagram.com" in domain:
            return PlatformType.INSTAGRAM
        elif "blog.naver.com" in domain:
            return PlatformType.NAVER_BLOG
        elif "youtube.com" in domain or "youtu.be" in domain:
            return PlatformType.YOUTUBE
        else:
            raise UnsupportedPlatformError(f"Unsupported platform: {domain}")

    async def extract_content(self, url: str) -> ExtractedContent:
        """Extract content from URL."""
        start_time = time.time()

        try:
            platform = self._detect_platform(url)
            content = await self._extract_with_playwright(url, platform)

            # Calculate extraction time
            extraction_time = time.time() - start_time
            content.extraction_time = extraction_time

            return content

        except Exception as e:
            # Re-raise known exceptions without wrapping
            if isinstance(e, (UnsupportedPlatformError, TimeoutError)):
                raise
            # Wrap other exceptions
            raise Exception(f"Content extraction failed: {str(e)}")

    async def _extract_with_playwright(
        self, url: str, platform: PlatformType
    ) -> ExtractedContent:
        """Extract content using Playwright."""
        try:
            # Import playwright here to avoid import errors if not installed
            from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
        except ImportError:
            # Fallback to mock implementation if Playwright not available
            return await self._extract_mock_content(url, platform)

        try:
            async with async_playwright() as p:
                # Launch browser with mobile user agent for better Instagram support
                browser = await p.chromium.launch(
                    headless=True,
                    args=[
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-accelerated-2d-canvas',
                        '--no-first-run',
                        '--no-zygote',
                        '--disable-gpu'
                    ]
                )
                
                context = await browser.new_context(
                    user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Mobile/15E148 Safari/604.1',
                    viewport={'width': 375, 'height': 812}
                )
                
                page = await context.new_page()
                
                # Set timeout for page operations
                page.set_default_timeout(self.timeout * 1000)  # Convert to milliseconds
                
                try:
                    # Navigate to URL
                    await page.goto(url, wait_until='networkidle', timeout=self.timeout * 1000)
                    
                    # Extract metadata based on platform
                    if platform == PlatformType.INSTAGRAM:
                        metadata = await self._extract_instagram_metadata(page)
                    elif platform == PlatformType.NAVER_BLOG:
                        metadata = await self._extract_naver_blog_metadata(page)
                    elif platform == PlatformType.YOUTUBE:
                        metadata = await self._extract_youtube_metadata(page)
                    else:
                        metadata = await self._extract_generic_metadata(page)
                        
                    return ExtractedContent(url=url, platform=platform, metadata=metadata)
                    
                finally:
                    await browser.close()
                    
        except PlaywrightTimeoutError:
            raise TimeoutError(f"Content extraction timed out for URL: {url}")
        except Exception as e:
            raise ContentExtractionError(f"Failed to extract content from {url}: {str(e)}")

    async def _extract_mock_content(self, url: str, platform: PlatformType) -> ExtractedContent:
        """Mock content extraction for testing/fallback."""
        # Simulate processing time
        await asyncio.sleep(0.1)

        # Return mock content based on platform
        if platform == PlatformType.INSTAGRAM:
            metadata = ContentMetadata(
                title="Amazing restaurant in Seoul",
                description="Great food and atmosphere!",
                images=["https://instagram.com/image1.jpg"],
                location="Seoul, South Korea",
                hashtags=["#food", "#seoul", "#restaurant"],
            )
        elif platform == PlatformType.NAVER_BLOG:
            metadata = ContentMetadata(
                title="Best places to visit in Gangnam",
                description="Food tour guide in Gangnam",
                images=["https://blog.image.jpg"],
                location="Gangnam, Seoul",
                hashtags=["#gangnam", "#food", "#travel"],
            )
        elif platform == PlatformType.YOUTUBE:
            metadata = ContentMetadata(
                title="YouTube Video Title",
                description="YouTube video description",
                images=["https://img.youtube.com/vi/ABC123/maxresdefault.jpg"],
                hashtags=["#video", "#youtube"]
            )
        else:
            metadata = ContentMetadata(
                title="Content title", 
                description="Content description"
            )

        return ExtractedContent(url=url, platform=platform, metadata=metadata)

    async def _extract_instagram_metadata(self, page) -> ContentMetadata:
        """Extract metadata from Instagram page."""
        try:
            # Wait for content to load
            await page.wait_for_selector('article', timeout=10000)
            
            # Extract title/caption
            title = None
            description = None
            try:
                # Try to get the main post text
                caption_element = await page.query_selector('article div[data-testid="post-caption"] span')
                if caption_element:
                    caption_text = await caption_element.text_content()
                    if caption_text:
                        lines = caption_text.strip().split('\n')
                        title = lines[0][:100] if lines else None  # First line as title
                        description = caption_text[:500]  # Full text as description
            except:
                pass
            
            # Extract images
            images = []
            try:
                img_elements = await page.query_selector_all('article img')
                for img in img_elements:
                    src = await img.get_attribute('src')
                    if src and 'instagram' in src:
                        images.append(src)
            except:
                pass
            
            # Extract hashtags
            hashtags = []
            if description:
                hashtags = re.findall(r'#\w+', description)
            
            # Try to extract location
            location = None
            try:
                location_element = await page.query_selector('[data-testid="location-link"]')
                if location_element:
                    location = await location_element.text_content()
            except:
                pass
            
            return ContentMetadata(
                title=title or "Instagram Post",
                description=description or "Instagram content",
                images=images,
                location=location,
                hashtags=hashtags
            )
            
        except Exception as e:
            # Return basic metadata if detailed extraction fails
            return ContentMetadata(
                title="Instagram Post",
                description="Content extraction partially failed",
                images=[],
                hashtags=[]
            )

    async def _extract_naver_blog_metadata(self, page) -> ContentMetadata:
        """Extract metadata from Naver Blog page."""
        try:
            # Wait for content to load
            await page.wait_for_selector('.se-main-container, .post-view, #postViewArea', timeout=10000)
            
            # Extract title
            title = None
            try:
                title_selectors = [
                    '.se-title-text',
                    '.post_title', 
                    '.title_area h3',
                    'h3.tit_h3'
                ]
                for selector in title_selectors:
                    title_element = await page.query_selector(selector)
                    if title_element:
                        title = await title_element.text_content()
                        break
            except:
                pass
            
            # Extract description/content
            description = None
            try:
                content_selectors = [
                    '.se-main-container',
                    '.post-view .content',
                    '#postViewArea'
                ]
                for selector in content_selectors:
                    content_element = await page.query_selector(selector)
                    if content_element:
                        content_text = await content_element.text_content()
                        if content_text:
                            description = content_text.strip()[:500]  # Limit to 500 chars
                            break
            except:
                pass
            
            # Extract images
            images = []
            try:
                img_elements = await page.query_selector_all('img')
                for img in img_elements:
                    src = await img.get_attribute('src')
                    if src and ('blogfiles.naver.net' in src or 'blog.naver.com' in src):
                        images.append(src)
            except:
                pass
            
            # Extract hashtags from content
            hashtags = []
            if description:
                hashtags = re.findall(r'#\w+', description)
            
            return ContentMetadata(
                title=title or "Naver Blog Post",
                description=description or "Blog content",
                images=images,
                hashtags=hashtags
            )
            
        except Exception as e:
            return ContentMetadata(
                title="Naver Blog Post",
                description="Content extraction partially failed",
                images=[],
                hashtags=[]
            )

    async def _extract_youtube_metadata(self, page) -> ContentMetadata:
        """Extract metadata from YouTube page."""
        try:
            # Wait for content to load
            await page.wait_for_selector('#watch7-content, ytd-watch-flexy', timeout=10000)
            
            # Extract title
            title = None
            try:
                title_selectors = [
                    'h1.title yt-formatted-string',
                    '#watch7-headline h1',
                    'h1.ytd-video-primary-info-renderer'
                ]
                for selector in title_selectors:
                    title_element = await page.query_selector(selector)
                    if title_element:
                        title = await title_element.text_content()
                        break
            except:
                pass
            
            # Extract description
            description = None
            try:
                desc_selectors = [
                    '#watch7-description-text',
                    'ytd-expandable-video-description-body-renderer',
                    '#description'
                ]
                for selector in desc_selectors:
                    desc_element = await page.query_selector(selector)
                    if desc_element:
                        desc_text = await desc_element.text_content()
                        if desc_text:
                            description = desc_text.strip()[:500]
                            break
            except:
                pass
            
            # Extract thumbnail
            images = []
            try:
                # Try to get video thumbnail
                video_id_match = re.search(r'(?:v=|/)([0-9A-Za-z_-]{11})', page.url)
                if video_id_match:
                    video_id = video_id_match.group(1)
                    images.append(f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg")
            except:
                pass
            
            return ContentMetadata(
                title=title or "YouTube Video",
                description=description or "YouTube video content",
                images=images,
                hashtags=[]
            )
            
        except Exception as e:
            return ContentMetadata(
                title="YouTube Video",
                description="Content extraction partially failed",
                images=[],
                hashtags=[]
            )

    async def _extract_generic_metadata(self, page) -> ContentMetadata:
        """Extract generic metadata using meta tags."""
        try:
            # Extract title
            title = None
            try:
                title = await page.title()
            except:
                pass
            
            # Extract meta description
            description = None
            try:
                desc_element = await page.query_selector('meta[name="description"]')
                if desc_element:
                    description = await desc_element.get_attribute('content')
            except:
                pass
            
            # Extract Open Graph images
            images = []
            try:
                og_img_elements = await page.query_selector_all('meta[property="og:image"]')
                for img in og_img_elements:
                    src = await img.get_attribute('content')
                    if src:
                        images.append(src)
            except:
                pass
            
            return ContentMetadata(
                title=title or "Web Content",
                description=description or "Generic web content",
                images=images,
                hashtags=[]
            )
            
        except Exception as e:
            return ContentMetadata(
                title="Web Content",
                description="Content extraction failed",
                images=[],
                hashtags=[]
            )
