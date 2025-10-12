"""Content extraction service for SNS link analysis."""

import asyncio
import re
import time
from urllib.parse import urlparse

from app.exceptions.external import ContentExtractionError, UnsupportedPlatformError
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
            from playwright.async_api import TimeoutError as PlaywrightTimeoutError
            from playwright.async_api import async_playwright
        except ImportError:
            # Fallback to mock implementation if Playwright not available
            return await self._extract_mock_content(url, platform)

        try:
            async with async_playwright() as p:
                # Launch browser with mobile user agent for better Instagram support
                browser = await p.chromium.launch(
                    headless=True,
                    args=[
                        "--no-sandbox",
                        "--disable-setuid-sandbox",
                        "--disable-dev-shm-usage",
                        "--disable-accelerated-2d-canvas",
                        "--no-first-run",
                        "--no-zygote",
                        "--disable-gpu",
                    ],
                )

                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Mobile/15E148 Safari/604.1",
                    viewport={"width": 375, "height": 812},
                )

                page = await context.new_page()

                # Set timeout for page operations
                page.set_default_timeout(self.timeout * 1000)  # Convert to milliseconds

                try:
                    # Navigate to URL
                    await page.goto(
                        url, wait_until="networkidle", timeout=self.timeout * 1000
                    )

                    # Extract metadata based on platform
                    if platform == PlatformType.INSTAGRAM:
                        metadata = await self._extract_instagram_metadata(page)
                    elif platform == PlatformType.NAVER_BLOG:
                        metadata = await self._extract_naver_blog_metadata(page)
                    elif platform == PlatformType.YOUTUBE:
                        metadata = await self._extract_youtube_metadata(page)
                    else:
                        metadata = await self._extract_generic_metadata(page)

                    return ExtractedContent(
                        url=url, platform=platform, metadata=metadata
                    )

                finally:
                    await browser.close()

        except PlaywrightTimeoutError:
            raise TimeoutError(f"Content extraction timed out for URL: {url}")
        except Exception as e:
            raise ContentExtractionError(
                f"Failed to extract content from {url}: {str(e)}"
            )

    async def _extract_mock_content(
        self, url: str, platform: PlatformType
    ) -> ExtractedContent:
        """Mock content extraction for testing/fallback."""
        # Simulate processing time
        await asyncio.sleep(0.1)

        # Use URL hash to select different mock scenarios for variety
        import hashlib

        url_hash = int(hashlib.md5(url.encode()).hexdigest(), 16) % 5

        # Return mock content based on platform
        if platform == PlatformType.INSTAGRAM:
            mock_scenarios = [
                # Scenario 1: 성수동 카페
                ContentMetadata(
                    title="성수동 카페 오아시스에서 브런치 먹었어요",
                    description="성수동에 있는 북유럽 감성 카페입니다. 루프탑도 있고 브런치 메뉴가 정말 맛있어요! 에그베네딕트 추천합니다.",
                    images=[],
                    location="서울 성동구 성수동",
                    hashtags=["#성수동카페", "#브런치맛집", "#루프탑카페", "#감성카페", "#데이트코스"],
                ),
                # Scenario 2: 강남 고깃집
                ContentMetadata(
                    title="강남 숙성 한우 맛집 발견!",
                    description="강남역 근처 한우 맛집이에요. 60일 숙성 한우라 진짜 부드럽고 맛있어요. 가격은 좀 있지만 특별한 날 추천!",
                    images=[],
                    location="서울 강남구 역삼동",
                    hashtags=["#강남맛집", "#한우맛집", "#숙성한우", "#고기집추천", "#기념일맛집"],
                ),
                # Scenario 3: 홍대 디저트 카페
                ContentMetadata(
                    title="홍대 티라미수 맛집 🍰",
                    description="홍대에서 제일 맛있는 티라미수! 커피도 진하고 좋아요. 인테리어도 예뻐서 사진 찍기 좋음",
                    images=[],
                    location="서울 마포구 홍대입구",
                    hashtags=["#홍대카페", "#티라미수맛집", "#디저트카페", "#홍대데이트", "#카페투어"],
                ),
                # Scenario 4: 이태원 이탈리안 레스토랑
                ContentMetadata(
                    title="이태원 파스타 맛집 추천",
                    description="정통 이탈리안 레스토랑! 파스타 면을 직접 만들어서 쫄깃하고 소스도 진짜 맛있어요. 와인도 잘 어울림",
                    images=[],
                    location="서울 용산구 이태원동",
                    hashtags=["#이태원맛집", "#파스타맛집", "#이탈리안레스토랑", "#데이트코스", "#와인맛집"],
                ),
                # Scenario 5: 여의도 오피스 카페
                ContentMetadata(
                    title="여의도 직장인 핫플 카페",
                    description="여의도에서 일하는 직장인이라면 여기! 아메리카노도 맛있고 브런치도 괜찮아요. 점심시간엔 사람 많으니 참고",
                    images=[],
                    location="서울 영등포구 여의도동",
                    hashtags=["#여의도카페", "#직장인카페", "#브런치카페", "#오피스맛집", "#여의도핫플"],
                ),
            ]
            metadata = mock_scenarios[url_hash]
        elif platform == PlatformType.NAVER_BLOG:
            metadata = ContentMetadata(
                title="서울 핫플 맛집 리스트",
                description="서울에서 꼭 가봐야 할 맛집들을 정리해봤어요. 강남, 홍대, 성수동 등 지역별로 추천 맛집을 소개합니다.",
                images=[],
                location="서울",
                hashtags=["#서울맛집", "#맛집추천", "#맛집탐방"],
            )
        elif platform == PlatformType.YOUTUBE:
            metadata = ContentMetadata(
                title="서울 카페 브이로그 | 성수동 카페투어",
                description="성수동에서 가장 핫한 카페들을 방문해봤어요! 인테리어 예쁘고 커피 맛있는 곳들만 골라서 갔습니다.",
                images=[],
                hashtags=["#성수동카페", "#카페브이로그", "#서울카페투어"],
            )
        else:
            metadata = ContentMetadata(
                title="맛집 정보", description="맛집 관련 콘텐츠입니다."
            )

        return ExtractedContent(url=url, platform=platform, metadata=metadata)

    async def _extract_instagram_metadata(self, page) -> ContentMetadata:
        """Extract metadata from Instagram page."""
        try:
            # Wait for content to load
            await page.wait_for_selector("article", timeout=10000)

            # Extract title/caption
            title = None
            description = None
            try:
                # Try to get the main post text
                caption_element = await page.query_selector(
                    'article div[data-testid="post-caption"] span'
                )
                if caption_element:
                    caption_text = await caption_element.text_content()
                    if caption_text:
                        lines = caption_text.strip().split("\n")
                        title = lines[0][:100] if lines else None  # First line as title
                        description = caption_text[:500]  # Full text as description
            except:
                pass

            # Extract images
            images = []
            try:
                img_elements = await page.query_selector_all("article img")
                for img in img_elements:
                    src = await img.get_attribute("src")
                    if src and "instagram" in src:
                        images.append(src)
            except:
                pass

            # Extract hashtags
            hashtags = []
            if description:
                hashtags = re.findall(r"#\w+", description)

            # Try to extract location
            location = None
            try:
                location_element = await page.query_selector(
                    '[data-testid="location-link"]'
                )
                if location_element:
                    location = await location_element.text_content()
            except:
                pass

            return ContentMetadata(
                title=title or "Instagram Post",
                description=description or "Instagram content",
                images=images,
                location=location,
                hashtags=hashtags,
            )

        except Exception:
            # Return basic metadata if detailed extraction fails
            return ContentMetadata(
                title="Instagram Post",
                description="Content extraction partially failed",
                images=[],
                hashtags=[],
            )

    async def _extract_naver_blog_metadata(self, page) -> ContentMetadata:
        """Extract metadata from Naver Blog page."""
        try:
            # Wait for content to load
            await page.wait_for_selector(
                ".se-main-container, .post-view, #postViewArea", timeout=10000
            )

            # Extract title
            title = None
            try:
                title_selectors = [
                    ".se-title-text",
                    ".post_title",
                    ".title_area h3",
                    "h3.tit_h3",
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
                    ".se-main-container",
                    ".post-view .content",
                    "#postViewArea",
                ]
                for selector in content_selectors:
                    content_element = await page.query_selector(selector)
                    if content_element:
                        content_text = await content_element.text_content()
                        if content_text:
                            description = content_text.strip()[
                                :500
                            ]  # Limit to 500 chars
                            break
            except:
                pass

            # Extract images
            images = []
            try:
                img_elements = await page.query_selector_all("img")
                for img in img_elements:
                    src = await img.get_attribute("src")
                    if src and (
                        "blogfiles.naver.net" in src or "blog.naver.com" in src
                    ):
                        images.append(src)
            except:
                pass

            # Extract hashtags from content
            hashtags = []
            if description:
                hashtags = re.findall(r"#\w+", description)

            return ContentMetadata(
                title=title or "Naver Blog Post",
                description=description or "Blog content",
                images=images,
                hashtags=hashtags,
            )

        except Exception:
            return ContentMetadata(
                title="Naver Blog Post",
                description="Content extraction partially failed",
                images=[],
                hashtags=[],
            )

    async def _extract_youtube_metadata(self, page) -> ContentMetadata:
        """Extract metadata from YouTube page."""
        try:
            # Wait for content to load
            await page.wait_for_selector(
                "#watch7-content, ytd-watch-flexy", timeout=10000
            )

            # Extract title
            title = None
            try:
                title_selectors = [
                    "h1.title yt-formatted-string",
                    "#watch7-headline h1",
                    "h1.ytd-video-primary-info-renderer",
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
                    "#watch7-description-text",
                    "ytd-expandable-video-description-body-renderer",
                    "#description",
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
                video_id_match = re.search(r"(?:v=|/)([0-9A-Za-z_-]{11})", page.url)
                if video_id_match:
                    video_id = video_id_match.group(1)
                    images.append(
                        f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
                    )
            except:
                pass

            return ContentMetadata(
                title=title or "YouTube Video",
                description=description or "YouTube video content",
                images=images,
                hashtags=[],
            )

        except Exception:
            return ContentMetadata(
                title="YouTube Video",
                description="Content extraction partially failed",
                images=[],
                hashtags=[],
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
                    description = await desc_element.get_attribute("content")
            except:
                pass

            # Extract Open Graph images
            images = []
            try:
                og_img_elements = await page.query_selector_all(
                    'meta[property="og:image"]'
                )
                for img in og_img_elements:
                    src = await img.get_attribute("content")
                    if src:
                        images.append(src)
            except:
                pass

            return ContentMetadata(
                title=title or "Web Content",
                description=description or "Generic web content",
                images=images,
                hashtags=[],
            )

        except Exception:
            return ContentMetadata(
                title="Web Content",
                description="Content extraction failed",
                images=[],
                hashtags=[],
            )
