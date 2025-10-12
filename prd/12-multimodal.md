좋습니다! 멀티모달 콘텐츠 분석을 위한 모듈화 설계를 체계적으로 계획해보겠습니다.
🏗️ 모듈화 설계 계획
📊 현재 구조 분석
현재 흐름:
LinkAnalysis API → ContentExtractor → PlaceAnalysisService → GeminiAnalyzer
                    (mock 데이터)      (URL만 전달)        (이미지 못봄)
문제점:
ContentExtractor: Playwright 의존성, mock fallback
PlaceAnalysisService: 이미지 URL을 문자열로만 전달
GeminiAnalyzer: 실제 이미지 객체 받을 준비는 되어있음
🎯 목표: 멀티모달 분석 파이프라인
사용자 입력 (URL/파일/텍스트)
    ↓
[Content Loader] - 콘텐츠 가져오기
    ↓
[Media Processor] - 미디어 전처리
    ↓
[AI Analyzer] - Gemini 멀티모달 분석
    ↓
[Result Builder] - 결과 구조화
📦 제안하는 모듈 구조
Module 1: Content Loader
위치: app/services/content/
책임: 다양한 소스에서 원시 콘텐츠 가져오기
# content_loader.py
class ContentLoader:
    """콘텐츠 로딩을 담당하는 추상 계층"""
    
    async def load_from_url(url: str) -> RawContent
    async def load_from_file(file_path: str) -> RawContent
    async def load_from_upload(file: UploadFile) -> RawContent

# url_loader.py
class URLLoader:
    """URL에서 콘텐츠 로딩"""
    
    - HTTP 요청 (간단한 페이지)
    - Open Graph 메타데이터 추출
    - oEmbed 프로토콜 지원
    - (선택) Playwright 통합

# file_loader.py  
class FileLoader:
    """로컬 파일에서 콘텐츠 로딩"""
    
    - 이미지 파일 읽기
    - 동영상 파일 읽기
    - 텍스트 파일 읽기
출력: RawContent (URL, 파일경로, 바이너리 데이터 등)
Module 2: Media Processor
위치: app/services/media/
책임: 미디어를 AI가 이해할 수 있는 형태로 변환
# image_processor.py
class ImageProcessor:
    """이미지 처리"""
    
    async def download_image(url: str) -> PIL.Image
    async def resize_image(image: PIL.Image, max_size: tuple) -> PIL.Image
    async def extract_image_metadata(image: PIL.Image) -> ImageMetadata
    async def validate_image(image: PIL.Image) -> bool

# video_processor.py
class VideoProcessor:
    """동영상 처리"""
    
    async def extract_thumbnail(video_url: str) -> PIL.Image
    async def extract_frames(video_url: str, num_frames: int) -> List[PIL.Image]
    async def get_video_metadata(video_url: str) -> VideoMetadata
    
    # YouTube 특화
    async def get_youtube_thumbnail(video_id: str) -> PIL.Image
    async def get_youtube_transcript(video_id: str) -> str

# text_processor.py
class TextProcessor:
    """텍스트 처리"""
    
    async def extract_hashtags(text: str) -> List[str]
    async def clean_text(text: str) -> str
    async def extract_keywords(text: str) -> List[str]
출력: ProcessedMedia (PIL.Image 객체, 정제된 텍스트)
Module 3: Multimodal Analyzer
위치: app/services/ai/ (기존 확장)
책임: 여러 모달리티를 결합하여 AI 분석
# multimodal_analyzer.py
class MultimodalAnalyzer:
    """멀티모달 콘텐츠 분석 오케스트레이터"""
    
    def __init__(self):
        self.gemini = GeminiAnalyzer()
        self.image_processor = ImageProcessor()
        self.video_processor = VideoProcessor()
    
    async def analyze_content(
        self,
        text: Optional[str],
        images: Optional[List[Union[str, PIL.Image]]],
        video: Optional[str]
    ) -> AnalysisResult:
        """
        텍스트 + 이미지 + 동영상을 종합 분석
        """
        
        # 1. 미디어 전처리
        processed_images = await self._process_images(images)
        video_frames = await self._process_video(video)
        
        # 2. Gemini에 멀티모달 입력
        result = await self.gemini.analyze_multimodal(
            text=text,
            images=processed_images + video_frames
        )
        
        return result

# gemini_analyzer.py (기존 개선)
class GeminiAnalyzer:
    """Gemini API 전문 클래스"""
    
    async def analyze_multimodal(
        self,
        text: str,
        images: List[PIL.Image]
    ) -> PlaceInfo:
        """이미지를 포함한 멀티모달 분석"""
        
        # Gemini API 호출 (이미 구현됨)
        ...
Module 4: Result Builder
위치: app/services/analysis/
책임: AI 분석 결과를 비즈니스 객체로 변환
# result_builder.py
class AnalysisResultBuilder:
    """분석 결과를 구조화"""
    
    def build_place_info(
        self,
        ai_result: PlaceInfo,
        metadata: ContentMetadata,
        confidence: float
    ) -> EnrichedPlaceInfo:
        """AI 결과 + 메타데이터 결합"""
        
        return EnrichedPlaceInfo(
            name=ai_result.name,
            category=ai_result.category,
            confidence=confidence,
            source_url=metadata.url,
            analyzed_images=metadata.images,
            ...
        )
Module 5: Analysis Pipeline
위치: app/services/analysis/
책임: 전체 파이프라인 오케스트레이션
# analysis_pipeline.py
class AnalysisPipeline:
    """전체 분석 파이프라인"""
    
    def __init__(self):
        self.content_loader = ContentLoader()
        self.media_processor = MediaProcessor()
        self.analyzer = MultimodalAnalyzer()
        self.result_builder = AnalysisResultBuilder()
    
    async def analyze_from_url(self, url: str) -> AnalysisResult:
        """URL → 분석 결과 (전체 파이프라인)"""
        
        # 1. 콘텐츠 로딩
        raw_content = await self.content_loader.load_from_url(url)
        
        # 2. 미디어 처리
        processed = await self.media_processor.process(raw_content)
        
        # 3. AI 분석
        ai_result = await self.analyzer.analyze_content(
            text=processed.text,
            images=processed.images,
            video=processed.video
        )
        
        # 4. 결과 구조화
        final_result = self.result_builder.build(ai_result, raw_content)
        
        return final_result
📂 최종 디렉토리 구조
backend/app/
├── services/
│   ├── content/              # 새로 추가
│   │   ├── __init__.py
│   │   ├── content_loader.py    # 추상 로더
│   │   ├── url_loader.py        # URL 소스
│   │   ├── file_loader.py       # 파일 소스
│   │   └── upload_loader.py     # 업로드 소스
│   │
│   ├── media/                # 새로 추가
│   │   ├── __init__.py
│   │   ├── image_processor.py   # 이미지 처리
│   │   ├── video_processor.py   # 동영상 처리
│   │   └── text_processor.py    # 텍스트 처리
│   │
│   ├── ai/                   # 기존 확장
│   │   ├── gemini_analyzer.py   # (기존) Gemini API
│   │   └── multimodal_analyzer.py  # (새) 멀티모달 오케스트레이터
│   │
│   ├── analysis/             # 새로 추가
│   │   ├── __init__.py
│   │   ├── analysis_pipeline.py # 전체 파이프라인
│   │   └── result_builder.py    # 결과 구조화
│   │
│   └── places/               # 기존 (리팩토링)
│       ├── content_extractor.py  # → url_loader로 대체 고려
│       └── place_analysis_service.py  # → pipeline 사용
│
├── schemas/
│   ├── content.py            # (기존)
│   ├── media.py              # 새로 추가
│   └── analysis.py           # 새로 추가
│
└── utils/
    └── media_helpers.py      # 미디어 유틸리티
🔄 모듈 간 데이터 흐름
# 데이터 모델 정의

# 1. Content Loader 출력
class RawContent(BaseModel):
    source_type: Literal["url", "file", "upload"]
    source: str
    text_content: Optional[str]
    image_urls: List[str]
    video_urls: List[str]
    metadata: Dict[str, Any]

# 2. Media Processor 출력
class ProcessedMedia(BaseModel):
    text: str
    images: List[PIL.Image]  # 실제 이미지 객체
    video_frames: List[PIL.Image]
    metadata: MediaMetadata

# 3. AI Analyzer 출력
class AIAnalysisResult(BaseModel):
    place_info: PlaceInfo
    confidence: float
    reasoning: Optional[str]

# 4. Result Builder 출력
class EnrichedAnalysisResult(BaseModel):
    place_info: PlaceInfo
    confidence: float
    source_metadata: ContentMetadata
    processing_stats: ProcessingStats
⚖️ 설계 원칙
1. 단일 책임 원칙 (SRP)
각 모듈은 하나의 책임만
ContentLoader: 가져오기만
MediaProcessor: 변환만
Analyzer: 분석만
2. 의존성 역전 (DIP)
# 인터페이스 정의
class IContentLoader(ABC):
    @abstractmethod
    async def load(self, source: str) -> RawContent:
        pass

# 구현체들
class URLLoader(IContentLoader): ...
class FileLoader(IContentLoader): ...
3. 확장 가능성 (OCP)
새 미디어 타입 추가 용이 (audio, PDF 등)
새 AI 모델 추가 가능 (GPT-4V, Claude 등)
새 소스 타입 추가 가능 (S3, CDN 등)
4. 테스트 용이성
# 각 모듈 독립 테스트 가능
async def test_image_processor():
    processor = ImageProcessor()
    image = await processor.download_image("https://...")
    assert image.size == (800, 600)
🎯 마이그레이션 전략
Phase 1: 기반 구축
✅ ImageProcessor 구현
✅ MultimodalAnalyzer 구현
✅ 기존 GeminiAnalyzer와 통합
Phase 2: 파이프라인 구축
✅ AnalysisPipeline 구현
✅ 기존 API 엔드포인트 연결
Phase 3: 확장
✅ VideoProcessor 추가
✅ URLLoader 리팩토링
✅ 캐싱 레이어 추가
★ Insight ───────────────────────────────────── 모듈화의 핵심 이점:
테스트 격리: 각 모듈을 독립적으로 테스트
유연한 확장: 새 미디어 타입/AI 모델 쉽게 추가
명확한 책임: 각 모듈의 역할이 명확함
재사용성: ImageProcessor는 다른 기능에서도 사용 가능
점진적 개선: Playwright 나중에 추가해도 기존 코드 영향 최소
중요한 선택:
Content는 "가져오기"만 (HTML 파싱 등 최소)
Media는 "변환"만 (AI 호출 없음)
Analyzer는 "분석"만 (미디어 다운로드 없음)
Pipeline은 "조율"만 (비즈니스 로직 최소) ─────────────────────────────────────────────────
이 설계가 목표하시는 방향과 맞나요? 특정 부분을 더 자세히 논의하거나, 바로 구현을 시작할까요?