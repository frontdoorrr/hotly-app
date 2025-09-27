"""
CDN 및 정적 리소스 최적화 API 엔드포인트

CDN 업로드, 캐시 무효화, 리소스 최적화 기능을 제공합니다.
"""
from typing import Any, Dict, List, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Query, status
from pydantic import BaseModel, Field
import logging

from app.services.cdn_service import (
    get_cdn_manager,
    get_resource_optimizer,
    get_cache_manager
)

logger = logging.getLogger(__name__)
router = APIRouter()


class CDNUploadRequest(BaseModel):
    """CDN 업로드 요청"""
    local_path: str = Field(..., description="로컬 파일 경로")
    cdn_path: str = Field(..., description="CDN 경로")
    content_type: Optional[str] = Field(None, description="MIME 타입")


class CDNUploadResponse(BaseModel):
    """CDN 업로드 응답"""
    cdn_url: str = Field(..., description="CDN URL")
    file_hash: str = Field(..., description="파일 해시")
    file_size: int = Field(..., description="파일 크기 (bytes)")
    uploaded_at: str = Field(..., description="업로드 시간")


class CacheInvalidationRequest(BaseModel):
    """캐시 무효화 요청"""
    paths: List[str] = Field(..., description="무효화할 경로 목록")


class CacheInvalidationResponse(BaseModel):
    """캐시 무효화 응답"""
    invalidation_id: str = Field(..., description="무효화 요청 ID")
    status: str = Field(..., description="처리 상태")
    estimated_completion: str = Field(..., description="예상 완료 시간")


class ImageOptimizationRequest(BaseModel):
    """이미지 최적화 요청"""
    image_path: str = Field(..., description="이미지 파일 경로")
    quality: int = Field(85, ge=10, le=100, description="이미지 품질 (10-100)")
    formats: List[str] = Field(["webp", "jpeg"], description="생성할 포맷 목록")


class ImageOptimizationResponse(BaseModel):
    """이미지 최적화 응답"""
    original_size: int = Field(..., description="원본 파일 크기")
    variants: Dict[str, Any] = Field(..., description="최적화된 변형들")
    total_size_saved: int = Field(..., description="절약된 총 크기")


class CSSMinificationRequest(BaseModel):
    """CSS 압축 요청"""
    css_content: str = Field(..., description="CSS 내용")


class CSSMinificationResponse(BaseModel):
    """CSS 압축 응답"""
    minified_content: str = Field(..., description="압축된 CSS")
    original_size: int = Field(..., description="원본 크기")
    minified_size: int = Field(..., description="압축된 크기")
    compression_ratio: float = Field(..., description="압축률")


class JSBundlingRequest(BaseModel):
    """JavaScript 번들링 요청"""
    entry_files: List[str] = Field(..., description="진입점 파일 목록")
    output_path: str = Field(..., description="출력 경로")
    minify: bool = Field(True, description="압축 여부")


class JSBundlingResponse(BaseModel):
    """JavaScript 번들링 응답"""
    bundled_content: str = Field(..., description="번들링된 내용")
    original_size: int = Field(..., description="원본 크기")
    bundled_size: int = Field(..., description="번들링된 크기")
    compression_ratio: float = Field(..., description="압축률")


class PreloadHintsRequest(BaseModel):
    """프리로딩 힌트 요청"""
    critical_resources: List[Dict[str, str]] = Field(..., description="중요 리소스 목록")


class PreloadHintsResponse(BaseModel):
    """프리로딩 힌트 응답"""
    preload_tags: List[str] = Field(..., description="프리로딩 HTML 태그")


@router.post(
    "/upload",
    response_model=CDNUploadResponse,
    summary="CDN 파일 업로드",
    description="파일을 CDN에 업로드하고 CDN URL을 반환합니다."
)
async def upload_to_cdn(request: CDNUploadRequest):
    """
    CDN 파일 업로드
    
    로컬 파일을 CDN에 업로드하고 접근 가능한 CDN URL을 생성합니다.
    """
    try:
        cdn_manager = get_cdn_manager()
        
        upload_result = await cdn_manager.upload_to_cdn(
            local_path=request.local_path,
            cdn_path=request.cdn_path,
            content_type=request.content_type
        )
        
        if not upload_result.success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Upload failed: {upload_result.error_message}"
            )
        
        return CDNUploadResponse(
            cdn_url=upload_result.cdn_url,
            file_hash=upload_result.file_hash,
            file_size=upload_result.file_size,
            uploaded_at=upload_result.uploaded_at
        )
        
    except Exception as e:
        logger.error(f"Failed to upload to CDN: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload file to CDN"
        )


@router.post(
    "/invalidate",
    response_model=CacheInvalidationResponse,
    summary="CDN 캐시 무효화",
    description="지정된 경로들의 CDN 캐시를 무효화합니다."
)
async def invalidate_cdn_cache(request: CacheInvalidationRequest):
    """
    CDN 캐시 무효화
    
    지정된 경로들의 CDN 캐시를 무효화하여 새로운 콘텐츠가 
    즉시 반영되도록 합니다.
    """
    try:
        cdn_manager = get_cdn_manager()
        
        invalidation_request = await cdn_manager.invalidate_cache(request.paths)
        
        return CacheInvalidationResponse(
            invalidation_id=invalidation_request.invalidation_id,
            status=invalidation_request.status,
            estimated_completion=invalidation_request.estimated_completion or ""
        )
        
    except Exception as e:
        logger.error(f"Failed to invalidate CDN cache: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to invalidate CDN cache"
        )


@router.get(
    "/invalidation/{invalidation_id}/status",
    summary="캐시 무효화 상태 확인",
    description="캐시 무효화 요청의 현재 상태를 확인합니다."
)
async def get_invalidation_status(invalidation_id: str):
    """
    캐시 무효화 상태 확인
    
    이전에 요청한 캐시 무효화의 진행 상태를 확인합니다.
    """
    try:
        cdn_manager = get_cdn_manager()
        status_info = cdn_manager.check_invalidation_status(invalidation_id)
        
        if "error" in status_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=status_info["error"]
            )
        
        return status_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get invalidation status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve invalidation status"
        )


@router.post(
    "/optimize/image",
    response_model=ImageOptimizationResponse,
    summary="이미지 최적화",
    description="이미지를 다양한 포맷과 품질로 최적화합니다."
)
async def optimize_image(request: ImageOptimizationRequest):
    """
    이미지 최적화
    
    원본 이미지를 WebP, JPEG 등 다양한 포맷으로 최적화하여
    웹 성능을 향상시킵니다.
    """
    try:
        optimizer = get_resource_optimizer()
        
        optimization_result = optimizer.optimize_image(
            original_path=request.image_path,
            quality=request.quality,
            formats=request.formats
        )
        
        return ImageOptimizationResponse(
            original_size=50 * 1024,  # 시뮬레이션된 원본 크기
            variants=optimization_result.variants,
            total_size_saved=optimization_result.total_size_saved
        )
        
    except Exception as e:
        logger.error(f"Failed to optimize image: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to optimize image"
        )


@router.post(
    "/optimize/css",
    response_model=CSSMinificationResponse,
    summary="CSS 압축",
    description="CSS 파일을 압축하여 크기를 줄입니다."
)
async def minify_css(request: CSSMinificationRequest):
    """
    CSS 압축
    
    CSS 파일에서 불필요한 공백과 개행을 제거하여
    파일 크기를 줄입니다.
    """
    try:
        optimizer = get_resource_optimizer()
        
        minification_result = optimizer.minify_css(request.css_content)
        
        return CSSMinificationResponse(**minification_result)
        
    except Exception as e:
        logger.error(f"Failed to minify CSS: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to minify CSS"
        )


@router.post(
    "/optimize/javascript",
    response_model=JSBundlingResponse,
    summary="JavaScript 번들링",
    description="여러 JavaScript 파일을 하나로 번들링하고 압축합니다."
)
async def bundle_javascript(request: JSBundlingRequest):
    """
    JavaScript 번들링
    
    여러 JavaScript 파일을 하나로 합치고 압축하여
    HTTP 요청 수를 줄이고 성능을 향상시킵니다.
    """
    try:
        optimizer = get_resource_optimizer()
        
        bundling_result = optimizer.bundle_javascript(
            entry_files=request.entry_files,
            output_path=request.output_path,
            minify=request.minify
        )
        
        return JSBundlingResponse(
            bundled_content=bundling_result["bundled_content"],
            original_size=bundling_result["original_size"],
            bundled_size=bundling_result["bundled_size"],
            compression_ratio=bundling_result["compression_ratio"]
        )
        
    except Exception as e:
        logger.error(f"Failed to bundle JavaScript: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to bundle JavaScript"
        )


@router.get(
    "/cache-headers",
    summary="캐시 헤더 생성",
    description="파일 타입에 맞는 적절한 캐시 헤더를 생성합니다."
)
async def generate_cache_headers(
    file_path: str = Query(..., description="파일 경로"),
    cache_duration: Optional[int] = Query(None, description="캐시 지속 시간 (초)")
):
    """
    캐시 헤더 생성
    
    파일 타입에 따라 적절한 캐시 정책을 가진 
    HTTP 헤더를 생성합니다.
    """
    try:
        cache_manager = get_cache_manager()
        
        headers = cache_manager.generate_cache_headers(
            file_path=file_path,
            cache_duration=cache_duration
        )
        
        return {"headers": headers}
        
    except Exception as e:
        logger.error(f"Failed to generate cache headers: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate cache headers"
        )


@router.post(
    "/preload-hints",
    response_model=PreloadHintsResponse,
    summary="리소스 프리로딩 힌트 생성",
    description="중요한 리소스들에 대한 프리로딩 HTML 태그를 생성합니다."
)
async def generate_preload_hints(request: PreloadHintsRequest):
    """
    리소스 프리로딩 힌트 생성
    
    중요한 CSS, JavaScript, 폰트, 이미지 등에 대한
    preload 태그를 생성하여 페이지 로딩 성능을 향상시킵니다.
    """
    try:
        cache_manager = get_cache_manager()
        
        preload_tags = cache_manager.generate_preload_hints(
            request.critical_resources
        )
        
        return PreloadHintsResponse(preload_tags=preload_tags)
        
    except Exception as e:
        logger.error(f"Failed to generate preload hints: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate preload hints"
        )


@router.get(
    "/versioned-url",
    summary="버전 관리된 리소스 URL 생성",
    description="파일 내용 해시를 포함한 캐시 무효화 안전한 URL을 생성합니다."
)
async def generate_versioned_url(
    file_path: str = Query(..., description="파일 경로"),
    content_hash: Optional[str] = Query(None, description="콘텐츠 해시")
):
    """
    버전 관리된 리소스 URL 생성
    
    파일 내용 기반 해시를 포함한 URL을 생성하여
    파일 변경 시 자동으로 캐시가 무효화되도록 합니다.
    """
    try:
        cdn_manager = get_cdn_manager()
        
        versioned_url = cdn_manager.generate_versioned_url(
            file_path=file_path,
            content_hash=content_hash
        )
        
        return {
            "versioned_url": versioned_url,
            "original_path": file_path,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to generate versioned URL: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate versioned URL"
        )


@router.get(
    "/health",
    summary="CDN 서비스 상태",
    description="CDN 및 리소스 최적화 서비스의 상태를 확인합니다."
)
async def get_cdn_health():
    """
    CDN 서비스 상태 확인
    
    CDN 매니저와 리소스 최적화 서비스의 
    작동 상태를 확인합니다.
    """
    try:
        cdn_manager = get_cdn_manager()
        optimizer = get_resource_optimizer()
        cache_manager = get_cache_manager()
        
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "cdn_manager": {
                "uploaded_files_count": len(cdn_manager.uploaded_files),
                "invalidation_requests_count": len(cdn_manager.invalidation_requests),
                "resource_versions_count": len(cdn_manager.resource_versions)
            },
            "resource_optimizer": {
                "optimized_images_count": len(optimizer.optimized_images),
                "bundled_files_count": len(optimizer.bundled_files)
            },
            "cache_manager": {
                "preload_resources_count": len(cache_manager.preload_resources)
            }
        }
        
        return health_status
        
    except Exception as e:
        logger.error(f"Failed to get CDN health: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check CDN service health"
        )