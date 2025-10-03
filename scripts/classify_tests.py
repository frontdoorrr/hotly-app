#!/usr/bin/env python3
"""테스트 파일 분류 스크립트."""
import os
import re
from pathlib import Path
from typing import Dict, List, Set

# 분류 기준
PATTERNS = {
    "unit": {
        "keywords": ["Mock", "AsyncMock", "patch", "from app.services", "from app.models", "from app.utils"],
        "not_keywords": ["TestClient", "client:", "FastAPI", "e2e", "integration", "workflow"],
        "files": set(),
    },
    "integration": {
        "keywords": ["TestClient", "Session", "db:", "API", "integration"],
        "not_keywords": ["e2e", "workflow", "complete flow"],
        "files": set(),
    },
    "e2e": {
        "keywords": ["e2e", "workflow", "complete flow", "end-to-end", "user journey"],
        "not_keywords": [],
        "files": set(),
    },
    "performance": {
        "keywords": ["performance", "benchmark", "load", "stress", "time.time", "statistics"],
        "not_keywords": [],
        "files": set(),
    },
}

def analyze_file(filepath: Path) -> str:
    """파일 내용을 분석하여 카테고리 반환."""
    try:
        content = filepath.read_text(encoding="utf-8")

        # E2E 먼저 체크 (가장 명확한 특징)
        if any(kw in content.lower() for kw in PATTERNS["e2e"]["keywords"]):
            return "e2e"

        # Performance 체크
        if any(kw in content for kw in PATTERNS["performance"]["keywords"]):
            if "performance" in filepath.name.lower():
                return "performance"

        # Integration vs Unit 구분
        has_testclient = "TestClient" in content or "client:" in content
        has_session = re.search(r"(Session|db:.*=.*Depends)", content) is not None
        has_api_import = "from fastapi" in content or "from app.api" in content

        if has_testclient or (has_session and has_api_import):
            return "integration"

        # Unit test 판정
        has_mock = "Mock" in content or "patch" in content
        has_service_import = "from app.services" in content or "from app.models" in content

        if has_mock or has_service_import:
            return "unit"

        return "unknown"

    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return "unknown"

def main():
    """메인 실행 함수."""
    tests_dir = Path(__file__).parent.parent / "tests"

    # 루트 레벨 테스트 파일만 찾기
    root_test_files = [
        f for f in tests_dir.glob("test_*.py")
        if f.is_file()
    ]

    print(f"Found {len(root_test_files)} test files in root level\n")

    # 분류
    categorized: Dict[str, List[Path]] = {
        "unit": [],
        "integration": [],
        "e2e": [],
        "performance": [],
        "unknown": [],
    }

    for filepath in sorted(root_test_files):
        category = analyze_file(filepath)
        categorized[category].append(filepath)

    # 결과 출력
    print("=" * 80)
    print("분류 결과")
    print("=" * 80)

    for category in ["unit", "integration", "e2e", "performance", "unknown"]:
        files = categorized[category]
        print(f"\n{category.upper()} ({len(files)}개):")
        print("-" * 80)
        for f in files:
            print(f"  - {f.name}")

    # 이동 명령어 생성
    print("\n" + "=" * 80)
    print("이동 명령어")
    print("=" * 80)

    for category in ["unit", "integration", "e2e", "performance"]:
        files = categorized[category]
        if files:
            print(f"\n# {category.upper()} ({len(files)}개)")
            for f in files:
                if category == "unit":
                    # Unit 테스트는 세부 카테고리로 분류
                    if "service" in f.name or "_service" in f.name:
                        dest = "tests/unit/services/"
                    elif "model" in f.name:
                        dest = "tests/unit/models/"
                    elif "api" in f.name and category == "unit":
                        dest = "tests/unit/api/"
                    else:
                        dest = "tests/unit/"
                elif category == "integration":
                    if "api" in f.name:
                        dest = "tests/integration/api/"
                    else:
                        dest = "tests/integration/services/"
                else:
                    dest = f"tests/{category}/"

                print(f"git mv {f} {dest}")

    # 요약
    print("\n" + "=" * 80)
    print("요약")
    print("=" * 80)
    print(f"Unit: {len(categorized['unit'])}개")
    print(f"Integration: {len(categorized['integration'])}개")
    print(f"E2E: {len(categorized['e2e'])}개")
    print(f"Performance: {len(categorized['performance'])}개")
    print(f"Unknown: {len(categorized['unknown'])}개")
    print(f"Total: {sum(len(v) for v in categorized.values())}개")

if __name__ == "__main__":
    main()
