"""
CDN 연동 및 정적 리소스 캐싱 TDD 테스트

CDN 연동과 정적 리소스 캐싱 시스템을 위한 TDD 테스트를 정의합니다.
"""
import hashlib
import mimetypes
from datetime import datetime, timedelta
from typing import Any, Dict, List


class TestCDNIntegration:
    """CDN 연동 테스트"""

    def test_cdn_url_generation(self):
        """CDN URL 생성 테스트"""
        # Given: CDN 설정
        cdn_config = {
            "base_url": "https://cdn.hotly.app",
            "version": "v1",
            "cache_control": "max-age=86400",
        }

        def generate_cdn_url(resource_path: str, version: str = None) -> str:
            """CDN URL 생성"""
            version = version or cdn_config["version"]
            base_url = cdn_config["base_url"].rstrip("/")
            resource_path = resource_path.lstrip("/")

            return f"{base_url}/{version}/{resource_path}"

        # When: 다양한 리소스에 대한 CDN URL 생성
        image_url = generate_cdn_url("/images/logo.png")
        css_url = generate_cdn_url("css/styles.css", "v2")
        js_url = generate_cdn_url("/js/app.min.js")

        # Then: 올바른 CDN URL 생성
        assert image_url == "https://cdn.hotly.app/v1/images/logo.png"
        assert css_url == "https://cdn.hotly.app/v2/css/styles.css"
        assert js_url == "https://cdn.hotly.app/v1/js/app.min.js"

        print("✅ CDN URL 생성 테스트 통과")

    def test_static_resource_upload(self):
        """정적 리소스 업로드 테스트"""
        # Given: CDN 업로드 시뮬레이터
        uploaded_files = {}

        def upload_to_cdn(
            local_path: str, cdn_path: str, content_type: str = None
        ) -> Dict[str, Any]:
            """CDN에 파일 업로드 시뮬레이션"""
            # 실제 파일 존재 여부 체크 대신 시뮬레이션
            # if not os.path.exists(local_path):
            #     raise FileNotFoundError(f"Local file not found: {local_path}")

            # 파일 크기와 해시 계산 (실제로는 파일 내용 사용)
            file_size = len(local_path) * 100  # 시뮬레이션
            file_hash = hashlib.md5(local_path.encode()).hexdigest()

            if not content_type:
                content_type, _ = mimetypes.guess_type(local_path)
                content_type = content_type or "application/octet-stream"

            upload_result = {
                "local_path": local_path,
                "cdn_path": cdn_path,
                "cdn_url": f"https://cdn.hotly.app/v1/{cdn_path}",
                "content_type": content_type,
                "file_size": file_size,
                "file_hash": file_hash,
                "uploaded_at": datetime.now().isoformat(),
                "success": True,
            }

            uploaded_files[cdn_path] = upload_result
            return upload_result

        # When: 다양한 정적 리소스 업로드
        # 실제 파일 경로 대신 시뮬레이션 경로 사용
        logo_result = upload_to_cdn("/local/images/logo.png", "images/logo.png")
        css_result = upload_to_cdn("/local/css/app.css", "css/app.css")
        js_result = upload_to_cdn("/local/js/bundle.js", "js/bundle.js")

        # Then: 업로드 성공 및 메타데이터 생성
        assert logo_result["success"] is True
        assert logo_result["content_type"] == "image/png"
        assert logo_result["cdn_url"] == "https://cdn.hotly.app/v1/images/logo.png"

        assert css_result["content_type"] == "text/css"
        assert js_result["content_type"] in [
            "application/javascript",
            "text/javascript",
        ]

        assert len(uploaded_files) == 3
        assert "images/logo.png" in uploaded_files

        print("✅ 정적 리소스 업로드 테스트 통과")

    def test_cdn_cache_invalidation(self):
        """CDN 캐시 무효화 테스트"""
        # Given: CDN 캐시 무효화 시뮬레이터
        invalidation_requests = []

        def invalidate_cdn_cache(paths: List[str]) -> Dict[str, Any]:
            """CDN 캐시 무효화"""
            invalidation_id = f"INV_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            request = {
                "invalidation_id": invalidation_id,
                "paths": paths,
                "status": "in_progress",
                "created_at": datetime.now().isoformat(),
                "estimated_completion": (
                    datetime.now() + timedelta(minutes=15)
                ).isoformat(),
            }

            invalidation_requests.append(request)
            return request

        def check_invalidation_status(invalidation_id: str) -> Dict[str, Any]:
            """무효화 상태 확인"""
            request = next(
                (
                    r
                    for r in invalidation_requests
                    if r["invalidation_id"] == invalidation_id
                ),
                None,
            )

            if not request:
                return {"error": "Invalidation not found"}

            # 시뮬레이션: 5분 후 완료
            created_time = datetime.fromisoformat(request["created_at"])
            if datetime.now() - created_time > timedelta(minutes=5):
                request["status"] = "completed"
                request["completed_at"] = datetime.now().isoformat()

            return request

        # When: CDN 캐시 무효화 요청
        paths_to_invalidate = [
            "/v1/images/logo.png",
            "/v1/css/*",  # 와일드카드 패턴
            "/v1/js/app.min.js",
        ]

        invalidation = invalidate_cdn_cache(paths_to_invalidate)

        # Then: 무효화 요청 생성
        assert invalidation["status"] == "in_progress"
        assert invalidation["paths"] == paths_to_invalidate
        assert "invalidation_id" in invalidation
        assert "estimated_completion" in invalidation

        # When: 상태 확인
        status = check_invalidation_status(invalidation["invalidation_id"])
        assert status["invalidation_id"] == invalidation["invalidation_id"]

        print("✅ CDN 캐시 무효화 테스트 통과")


class TestStaticResourceOptimization:
    """정적 리소스 최적화 테스트"""

    def test_image_optimization(self):
        """이미지 최적화 테스트"""
        # Given: 이미지 최적화 시뮬레이터
        optimized_images = {}

        def optimize_image(
            original_path: str, quality: int = 85, formats: List[str] = None
        ) -> Dict[str, Any]:
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
                    "compression_ratio": (original_size - optimized_size)
                    / original_size,
                    "quality": quality,
                }

            optimization_result = {
                "original_path": original_path,
                "original_size": original_size,
                "variants": optimized_variants,
                "total_size_saved": original_size
                - min(v["size"] for v in optimized_variants.values()),
                "optimized_at": datetime.now().isoformat(),
            }

            optimized_images[original_path] = optimization_result
            return optimization_result

        # When: 이미지 최적화 수행
        optimization = optimize_image(
            "images/hero-banner.png", quality=80, formats=["webp", "jpeg", "png"]
        )

        # Then: 최적화 결과 확인
        assert len(optimization["variants"]) == 3
        assert "webp" in optimization["variants"]
        assert "jpeg" in optimization["variants"]

        webp_variant = optimization["variants"]["webp"]
        assert webp_variant["compression_ratio"] > 0.3  # 30% 이상 압축
        assert webp_variant["size"] < optimization["original_size"]

        jpeg_variant = optimization["variants"]["jpeg"]
        assert jpeg_variant["quality"] == 80

        print("✅ 이미지 최적화 테스트 통과")

    def test_css_minification(self):
        """CSS 압축 테스트"""

        # Given: CSS 압축기
        def minify_css(css_content: str) -> Dict[str, Any]:
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
                "size_saved": original_size - minified_size,
            }

        # When: CSS 압축 수행
        original_css = """
        body {
            margin: 0;
            padding: 0;
            font-family: 'Arial', sans-serif;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
        }

        .button {
            background-color: #007bff;
            color: white;
            padding: 10px 20px;
        }
        """

        result = minify_css(original_css)

        # Then: 압축 결과 확인
        assert result["minified_size"] < result["original_size"]
        assert result["compression_ratio"] > 0  # 압축됨
        assert "\n" not in result["minified_content"]  # 줄바꿈 제거

        # 기본적인 CSS 구조는 유지
        assert (
            "body{" in result["minified_content"]
            or "body {" in result["minified_content"]
        )
        assert "#007bff" in result["minified_content"]

        print("✅ CSS 압축 테스트 통과")

    def test_javascript_bundling(self):
        """JavaScript 번들링 테스트"""
        # Given: JavaScript 번들러
        bundled_files = {}

        def bundle_javascript(
            entry_files: List[str], output_path: str, minify: bool = True
        ) -> Dict[str, Any]:
            """JavaScript 번들링"""
            # 파일 내용 시뮬레이션
            file_contents = {
                "utils.js": "function formatDate(date) { return date.toISOString(); }",
                "api.js": "const API_BASE = 'https://api.hotly.app'; function fetchData() {}",
                "app.js": "import { formatDate } from './utils.js'; import { fetchData } from './api.js';",
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
                "compression_ratio": (total_original_size - final_size)
                / total_original_size
                if minify
                else 0,
                "minified": minify,
                "created_at": datetime.now().isoformat(),
            }

            bundled_files[output_path] = bundle_result
            return bundle_result

        # When: JavaScript 번들링 수행
        entry_files = ["utils.js", "api.js", "app.js"]
        bundle_result = bundle_javascript(
            entry_files=entry_files, output_path="dist/bundle.min.js", minify=True
        )

        # Then: 번들링 결과 확인
        assert bundle_result["minified"] is True
        assert bundle_result["bundled_size"] > 0
        assert len(bundle_result["entry_files"]) == 3

        # 모든 파일 내용이 포함되었는지 확인
        content = bundle_result["bundled_content"]
        assert "formatDate" in content
        assert "fetchData" in content
        assert "API_BASE" in content

        # 압축으로 인한 크기 감소 확인 (압축된 경우)
        if bundle_result["minified"]:
            assert bundle_result["compression_ratio"] > 0

        print("✅ JavaScript 번들링 테스트 통과")


class TestStaticResourceCaching:
    """정적 리소스 캐싱 테스트"""

    def test_browser_caching_headers(self):
        """브라우저 캐싱 헤더 테스트"""

        # Given: 정적 리소스 서빙 시뮬레이터
        def generate_cache_headers(
            file_path: str, cache_duration: int = None
        ) -> Dict[str, str]:
            """캐시 헤더 생성"""
            file_ext = file_path.split(".")[-1].lower()

            # 파일 타입별 기본 캐시 설정
            cache_settings = {
                "css": 86400 * 30,  # 30일
                "js": 86400 * 30,  # 30일
                "png": 86400 * 365,  # 1년
                "jpg": 86400 * 365,  # 1년
                "jpeg": 86400 * 365,  # 1년
                "webp": 86400 * 365,  # 1년
                "svg": 86400 * 30,  # 30일
                "ico": 86400 * 365,  # 1년
                "woff": 86400 * 365,  # 1년
                "woff2": 86400 * 365,  # 1년
                "html": 300,  # 5분
                "json": 3600,  # 1시간
            }

            max_age = cache_duration or cache_settings.get(file_ext, 3600)

            headers = {
                "Cache-Control": f"public, max-age={max_age}",
                "Expires": (datetime.now() + timedelta(seconds=max_age)).strftime(
                    "%a, %d %b %Y %H:%M:%S GMT"
                ),
            }

            # 이미지는 immutable 추가
            if file_ext in ["png", "jpg", "jpeg", "webp", "svg", "ico"]:
                headers["Cache-Control"] += ", immutable"

            # ETag 생성
            etag = hashlib.md5(file_path.encode()).hexdigest()[:16]
            headers["ETag"] = f'"{etag}"'

            return headers

        # When: 다양한 파일에 대한 캐시 헤더 생성
        css_headers = generate_cache_headers("css/app.css")
        image_headers = generate_cache_headers("images/logo.png")
        html_headers = generate_cache_headers("index.html")

        # Then: 적절한 캐시 헤더 생성
        # CSS 파일
        assert "max-age=2592000" in css_headers["Cache-Control"]  # 30일
        assert "public" in css_headers["Cache-Control"]
        assert "ETag" in css_headers

        # 이미지 파일
        assert "max-age=31536000" in image_headers["Cache-Control"]  # 1년
        assert "immutable" in image_headers["Cache-Control"]

        # HTML 파일
        assert "max-age=300" in html_headers["Cache-Control"]  # 5분

        print("✅ 브라우저 캐싱 헤더 테스트 통과")

    def test_versioned_static_resources(self):
        """버전 관리된 정적 리소스 테스트"""
        # Given: 리소스 버전 관리 시스템
        resource_versions = {}

        def generate_versioned_url(file_path: str, content_hash: str = None) -> str:
            """버전이 포함된 리소스 URL 생성"""
            if not content_hash:
                # 파일 내용 기반 해시 시뮬레이션
                content_hash = hashlib.md5(file_path.encode()).hexdigest()[:8]

            # 파일명에 해시 추가
            name, ext = (
                file_path.rsplit(".", 1) if "." in file_path else (file_path, "")
            )
            versioned_name = f"{name}.{content_hash}"

            if ext:
                versioned_name += f".{ext}"

            resource_versions[file_path] = {
                "original_path": file_path,
                "versioned_path": versioned_name,
                "content_hash": content_hash,
                "generated_at": datetime.now().isoformat(),
            }

            return versioned_name

        def invalidate_old_versions(file_path: str, keep_latest: int = 3):
            """이전 버전 정리"""
            # 실제로는 CDN이나 스토리지에서 파일 삭제
            # 여기서는 시뮬레이션
            return f"Cleaned up old versions of {file_path}, kept latest {keep_latest}"

        # When: 버전 관리된 URL 생성
        css_versioned = generate_versioned_url("css/app.css")
        js_versioned = generate_versioned_url("js/bundle.js")
        image_versioned = generate_versioned_url("images/hero.png")

        # Then: 버전 정보가 포함된 URL 생성
        assert "css/app." in css_versioned
        assert css_versioned.endswith(".css")
        assert len(css_versioned.split(".")[-2]) == 8  # 8자리 해시

        assert "js/bundle." in js_versioned
        assert js_versioned.endswith(".js")

        assert "images/hero." in image_versioned
        assert image_versioned.endswith(".png")

        # 리소스 버전 정보 저장 확인
        assert len(resource_versions) == 3
        assert resource_versions["css/app.css"]["versioned_path"] == css_versioned

        print("✅ 버전 관리된 정적 리소스 테스트 통과")

    def test_resource_preloading(self):
        """리소스 프리로딩 테스트"""
        # Given: 리소스 프리로딩 관리자
        preload_resources = {}

        def generate_preload_hints(
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
                    "image": "image",
                }

                as_attr = as_mapping.get(resource_type, resource_type)

                preload_tag = f'<link rel="preload" href="{path}" as="{as_attr}"'

                # 폰트는 crossorigin 추가
                if resource_type == "font":
                    preload_tag += " crossorigin"

                # 이미지는 fetchpriority 추가
                if resource_type == "image" and resource.get("priority") == "high":
                    preload_tag += ' fetchpriority="high"'

                preload_tag += ">"
                preload_tags.append(preload_tag)

                # 프리로딩 리소스 기록
                preload_resources[path] = {
                    "type": resource_type,
                    "as": as_attr,
                    "priority": resource.get("priority", "normal"),
                    "added_at": datetime.now().isoformat(),
                }

            return preload_tags

        # When: 크리티컬 리소스 프리로딩
        critical_resources = [
            {"path": "/css/critical.css", "type": "css"},
            {"path": "/js/app.bundle.js", "type": "js"},
            {"path": "/fonts/inter.woff2", "type": "font"},
            {"path": "/images/hero-bg.webp", "type": "image", "priority": "high"},
        ]

        preload_tags = generate_preload_hints(critical_resources)

        # Then: 프리로딩 태그 생성 확인
        assert len(preload_tags) == 4

        # CSS 프리로딩 태그
        css_tag = next(tag for tag in preload_tags if "critical.css" in tag)
        assert 'as="style"' in css_tag
        assert 'rel="preload"' in css_tag

        # 폰트 프리로딩 태그
        font_tag = next(tag for tag in preload_tags if "inter.woff2" in tag)
        assert 'as="font"' in font_tag
        assert "crossorigin" in font_tag

        # 이미지 프리로딩 태그
        image_tag = next(tag for tag in preload_tags if "hero-bg.webp" in tag)
        assert 'as="image"' in image_tag
        assert 'fetchpriority="high"' in image_tag

        # 프리로딩 리소스 기록 확인
        assert len(preload_resources) == 4
        assert preload_resources["/fonts/inter.woff2"]["type"] == "font"

        print("✅ 리소스 프리로딩 테스트 통과")


def main():
    """CDN 및 정적 리소스 캐싱 테스트 실행"""
    print("🌐 CDN 연동 및 정적 리소스 캐싱 TDD 테스트 시작")
    print("=" * 70)

    test_classes = [
        TestCDNIntegration(),
        TestStaticResourceOptimization(),
        TestStaticResourceCaching(),
    ]

    total_passed = 0
    total_failed = 0

    for test_instance in test_classes:
        class_name = test_instance.__class__.__name__
        print(f"\n📦 {class_name} 테스트 실행")
        print("-" * 45)

        test_methods = [
            method for method in dir(test_instance) if method.startswith("test_")
        ]

        for method_name in test_methods:
            try:
                if hasattr(test_instance, "setup_method"):
                    test_instance.setup_method()

                test_method = getattr(test_instance, method_name)
                test_method()
                total_passed += 1
            except Exception as e:
                print(f"❌ {method_name} 실패: {e}")
                total_failed += 1

    print(f"\n📊 CDN 및 정적 리소스 캐싱 테스트 결과:")
    print(f"   ✅ 통과: {total_passed}")
    print(f"   ❌ 실패: {total_failed}")
    print(f"   📈 전체: {total_passed + total_failed}")

    if total_failed == 0:
        print("🏆 모든 CDN 연동 테스트 통과!")
        return True
    else:
        print(f"⚠️ {total_failed}개 테스트 실패")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
