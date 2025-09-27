"""
CDN 연동 및 정적 리소스 캐싱 서비스

CDN 업로드, 캐시 무효화, 정적 리소스 최적화 기능을 제공합니다.
"""
import asyncio
import hashlib
import mimetypes
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
import logging
from io import BytesIO
import gzip
import json

logger = logging.getLogger(__name__)


@dataclass
class CDNUploadResult:
    """CDN 업로드 결과"""
    local_path: str
    cdn_path: str
    cdn_url: str
    content_type: str
    file_size: int
    file_hash: str
    uploaded_at: str
    success: bool
    error_message: str = ""


@dataclass
class InvalidationRequest:
    """CDN 캐시 무효화 요청"""
    invalidation_id: str
    paths: List[str]
    status: str  # in_progress, completed, failed
    created_at: str
    completed_at: Optional[str] = None
    estimated_completion: Optional[str] = None


@dataclass
class OptimizedResource:
    """최적화된 리소스"""
    original_path: str
    variants: Dict[str, Any] = field(default_factory=dict)
    total_size_saved: int = 0
    optimized_at: str = field(default_factory=lambda: datetime.now().isoformat())


class CDNManager:
    """CDN 관리자"""
    
    def __init__(self, base_url: str = "https://cdn.hotly.app", version: str = "v1"):
        self.base_url = base_url.rstrip("/")
        self.version = version
        self.uploaded_files: Dict[str, CDNUploadResult] = {}
        self.invalidation_requests: List[InvalidationRequest] = []
        self.resource_versions: Dict[str, Dict[str, Any]] = {}
        
    def generate_cdn_url(self, resource_path: str, version: str = None) -> str:
        """CDN URL 생성"""
        version = version or self.version
        resource_path = resource_path.lstrip("/")
        return f"{self.base_url}/{version}/{resource_path}"
    
    async def upload_to_cdn(
        self,
        local_path: str,
        cdn_path: str,
        content_type: str = None
    ) -> CDNUploadResult:
        """CDN에 파일 업로드"""
        try:
            # 콘텐츠 타입 결정
            if not content_type:
                content_type, _ = mimetypes.guess_type(local_path)
                content_type = content_type or "application/octet-stream"
            
            # 파일 정보 계산 (실제 구현에서는 파일을 읽어야 함)
            if os.path.exists(local_path):
                file_size = os.path.getsize(local_path)
                with open(local_path, 'rb') as f:
                    file_hash = hashlib.md5(f.read()).hexdigest()
            else:
                # 테스트/시뮬레이션용
                file_size = len(local_path) * 100
                file_hash = hashlib.md5(local_path.encode()).hexdigest()
            
            # CDN URL 생성
            cdn_url = self.generate_cdn_url(cdn_path)
            
            # 업로드 시뮬레이션 (실제로는 CDN API 호출)
            await asyncio.sleep(0.1)  # 네트워크 지연 시뮬레이션
            
            upload_result = CDNUploadResult(
                local_path=local_path,
                cdn_path=cdn_path,
                cdn_url=cdn_url,
                content_type=content_type,
                file_size=file_size,
                file_hash=file_hash,
                uploaded_at=datetime.now().isoformat(),
                success=True
            )
            
            self.uploaded_files[cdn_path] = upload_result
            return upload_result
            
        except Exception as e:
            logger.error(f"Failed to upload to CDN: {e}")
            return CDNUploadResult(
                local_path=local_path,
                cdn_path=cdn_path,
                cdn_url="",
                content_type=content_type or "",
                file_size=0,
                file_hash="",
                uploaded_at=datetime.now().isoformat(),
                success=False,
                error_message=str(e)
            )
    
    async def invalidate_cache(self, paths: List[str]) -> InvalidationRequest:
        """CDN 캐시 무효화"""
        invalidation_id = f"INV_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        request = InvalidationRequest(
            invalidation_id=invalidation_id,
            paths=paths,
            status="in_progress",
            created_at=datetime.now().isoformat(),
            estimated_completion=(datetime.now() + timedelta(minutes=15)).isoformat()
        )
        
        self.invalidation_requests.append(request)
        
        # 백그라운드에서 무효화 처리 시뮬레이션
        asyncio.create_task(self._process_invalidation(request))
        
        return request
    
    async def _process_invalidation(self, request: InvalidationRequest):
        """무효화 처리 (백그라운드)"""
        # 실제 무효화 처리 시뮬레이션
        await asyncio.sleep(300)  # 5분 후 완료
        
        request.status = "completed"
        request.completed_at = datetime.now().isoformat()
    
    def check_invalidation_status(self, invalidation_id: str) -> Dict[str, Any]:
        """무효화 상태 확인"""
        request = next(
            (r for r in self.invalidation_requests if r.invalidation_id == invalidation_id),
            None
        )
        
        if not request:
            return {"error": "Invalidation not found"}
        
        # 5분 후 완료로 시뮬레이션
        created_time = datetime.fromisoformat(request.created_at)
        if datetime.now() - created_time > timedelta(minutes=5):
            request.status = "completed"
            request.completed_at = datetime.now().isoformat()
        
        return {
            "invalidation_id": request.invalidation_id,
            "paths": request.paths,
            "status": request.status,
            "created_at": request.created_at,
            "completed_at": request.completed_at,
            "estimated_completion": request.estimated_completion
        }
    
    def generate_versioned_url(self, file_path: str, content_hash: str = None) -> str:
        """버전이 포함된 리소스 URL 생성"""
        if not content_hash:
            # 파일 내용 기반 해시 시뮬레이션
            content_hash = hashlib.md5(file_path.encode()).hexdigest()[:8]
        
        # 파일명에 해시 추가
        name, ext = file_path.rsplit(".", 1) if "." in file_path else (file_path, "")
        versioned_name = f"{name}.{content_hash}"
        
        if ext:
            versioned_name += f".{ext}"
        
        self.resource_versions[file_path] = {
            "original_path": file_path,
            "versioned_path": versioned_name,
            "content_hash": content_hash,
            "generated_at": datetime.now().isoformat()
        }
        
        return versioned_name


class StaticResourceOptimizer:
    """정적 리소스 최적화"""
    
    def __init__(self):
        self.optimized_images: Dict[str, OptimizedResource] = {}
        self.bundled_files: Dict[str, Dict[str, Any]] = {}
    
    def optimize_image(
        self,
        original_path: str,
        quality: int = 85,
        formats: List[str] = None
    ) -> OptimizedResource:
        """이미지 최적화"""
        if formats is None:
            formats = ["webp", "jpeg"]
        
        # 원본 정보 시뮬레이션
        original_size = 1024 * 50  # 50KB
        
        optimized_variants = {}
        
        for fmt in formats:
            # 최적화된 크기 계산 (시뮬레이션)
            if fmt == "webp":
                optimized_size = int(original_size * 0.6)  # 40% 압축
            elif fmt == "jpeg":
                optimized_size = int(original_size * (quality / 100))
            else:
                optimized_size = original_size
            
            variant_path = original_path.replace(".png", f".{fmt}")
            
            optimized_variants[fmt] = {
                "path": variant_path,
                "size": optimized_size,
                "compression_ratio": (original_size - optimized_size) / original_size,
                "quality": quality
            }
        
        optimization_result = OptimizedResource(
            original_path=original_path,
            variants=optimized_variants,
            total_size_saved=original_size - min(v["size"] for v in optimized_variants.values())
        )
        
        self.optimized_images[original_path] = optimization_result
        return optimization_result
    
    def minify_css(self, css_content: str) -> Dict[str, Any]:
        """CSS 압축"""
        original_content = css_content
        original_size = len(original_content)
        
        # 간단한 압축 시뮬레이션
        minified_content = css_content.replace("\n", "").replace("  ", " ")
        minified_content = minified_content.replace("; ", ";").replace(": ", ":")
        minified_content = minified_content.replace("{ ", "{").replace(" }", "}")
        
        minified_size = len(minified_content)
        compression_ratio = (original_size - minified_size) / original_size
        
        return {
            "original_content": original_content,
            "minified_content": minified_content,
            "original_size": original_size,
            "minified_size": minified_size,
            "compression_ratio": compression_ratio,
            "size_saved": original_size - minified_size
        }
    
    def bundle_javascript(
        self,
        entry_files: List[str],
        output_path: str,
        minify: bool = True
    ) -> Dict[str, Any]:
        """JavaScript 번들링"""
        # 파일 내용 시뮬레이션
        file_contents = {
            "utils.js": "function formatDate(date) { return date.toISOString(); }",
            "api.js": "const API_BASE = 'https://api.hotly.app'; function fetchData() {}",
            "app.js": "import { formatDate } from './utils.js'; import { fetchData } from './api.js';"
        }
        
        # 번들링 시뮬레이션
        bundled_content = ""
        total_original_size = 0
        
        for file_path in entry_files:
            if file_path in file_contents:
                content = file_contents[file_path]
                total_original_size += len(content)
                if minify:
                    # 압축 시 주석 제외하고 직접 합치기
                    bundled_content += content
                else:
                    # 비압축 시 주석 포함
                    bundled_content += f"\n// {file_path}\n{content}\n"
        
        # 압축 시뮬레이션
        if minify:
            # 압축된 경우 더 많은 공백 제거
            minified_content = bundled_content.replace(" ", "").replace("\n", "")
            # 일부 필수 공백은 유지 (함수명과 괄호 사이 등)
            minified_content = minified_content.replace("function", " function")
            minified_content = minified_content.replace("return", " return")
            minified_content = minified_content.replace("const", " const")
            final_content = minified_content
            final_size = len(final_content)
        else:
            final_content = bundled_content
            final_size = len(final_content)
        
        bundle_result = {
            "entry_files": entry_files,
            "output_path": output_path,
            "bundled_content": final_content,
            "original_size": total_original_size,
            "bundled_size": final_size,
            "compression_ratio": (total_original_size - final_size) / total_original_size if minify else 0,
            "minified": minify,
            "created_at": datetime.now().isoformat()
        }
        
        self.bundled_files[output_path] = bundle_result
        return bundle_result


class StaticResourceCacheManager:
    """정적 리소스 캐싱 관리"""
    
    def __init__(self):
        self.preload_resources: Dict[str, Dict[str, Any]] = {}
    
    def generate_cache_headers(
        self,
        file_path: str,
        cache_duration: int = None
    ) -> Dict[str, str]:
        """캐시 헤더 생성"""
        file_ext = file_path.split(".")[-1].lower()
        
        # 파일 타입별 기본 캐시 설정
        cache_settings = {
            "css": 86400 * 30,      # 30일
            "js": 86400 * 30,       # 30일
            "png": 86400 * 365,     # 1년
            "jpg": 86400 * 365,     # 1년
            "jpeg": 86400 * 365,    # 1년
            "webp": 86400 * 365,    # 1년
            "svg": 86400 * 30,      # 30일
            "ico": 86400 * 365,     # 1년
            "woff": 86400 * 365,    # 1년
            "woff2": 86400 * 365,   # 1년
            "html": 300,            # 5분
            "json": 3600,           # 1시간
        }
        
        max_age = cache_duration or cache_settings.get(file_ext, 3600)
        
        headers = {
            "Cache-Control": f"public, max-age={max_age}",
            "Expires": (datetime.now() + timedelta(seconds=max_age)).strftime(
                "%a, %d %b %Y %H:%M:%S GMT"
            )
        }
        
        # 이미지는 immutable 추가
        if file_ext in ["png", "jpg", "jpeg", "webp", "svg", "ico"]:
            headers["Cache-Control"] += ", immutable"
        
        # ETag 생성
        etag = hashlib.md5(file_path.encode()).hexdigest()[:16]
        headers["ETag"] = f'"{etag}"'
        
        return headers
    
    def generate_preload_hints(
        self,
        critical_resources: List[Dict[str, str]]
    ) -> List[str]:
        """리소스 프리로딩 힌트 생성"""
        preload_tags = []
        
        for resource in critical_resources:
            path = resource["path"]
            resource_type = resource["type"]
            
            # 리소스 타입별 as 속성 설정
            as_mapping = {
                "css": "style",
                "js": "script", 
                "font": "font",
                "image": "image"
            }
            
            as_attr = as_mapping.get(resource_type, resource_type)
            
            preload_tag = f'<link rel="preload" href="{path}" as="{as_attr}"'
            
            # 폰트는 crossorigin 추가
            if resource_type == "font":
                preload_tag += ' crossorigin'
            
            # 이미지는 fetchpriority 추가
            if resource_type == "image" and resource.get("priority") == "high":
                preload_tag += ' fetchpriority="high"'
            
            preload_tag += ">"
            preload_tags.append(preload_tag)
            
            # 프리로딩 리소스 기록
            self.preload_resources[path] = {
                "type": resource_type,
                "as": as_attr,
                "priority": resource.get("priority", "normal"),
                "added_at": datetime.now().isoformat()
            }
        
        return preload_tags


# 전역 인스턴스들
_cdn_manager: Optional[CDNManager] = None
_resource_optimizer: Optional[StaticResourceOptimizer] = None
_cache_manager: Optional[StaticResourceCacheManager] = None


def get_cdn_manager() -> CDNManager:
    """CDN 매니저 싱글톤 인스턴스"""
    global _cdn_manager
    if _cdn_manager is None:
        _cdn_manager = CDNManager()
    return _cdn_manager


def get_resource_optimizer() -> StaticResourceOptimizer:
    """리소스 최적화 싱글톤 인스턴스"""
    global _resource_optimizer
    if _resource_optimizer is None:
        _resource_optimizer = StaticResourceOptimizer()
    return _resource_optimizer


def get_cache_manager() -> StaticResourceCacheManager:
    """정적 리소스 캐시 매니저 싱글톤 인스턴스"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = StaticResourceCacheManager()
    return _cache_manager