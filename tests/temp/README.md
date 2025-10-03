# Temporary Test Scripts

이 디렉토리는 **개발 중 빠른 검증을 위한 임시 테스트 스크립트**를 보관합니다.

## ⚠️ 주의사항

- 이 스크립트들은 **정식 테스트 스위트에 포함되지 않습니다**
- CI/CD 파이프라인에서 실행되지 않습니다
- 수동 실행용 스크립트입니다 (`python test_xxx.py`)
- 언제든지 삭제될 수 있습니다

## 📋 파일 목록

| 파일 | 목적 | 날짜 |
|------|------|------|
| `test_enhanced_cache.py` | 향상된 캐시 기능 검증 | Sep 27 |
| `test_link_analysis_integration.py` | 링크 분석 통합 테스트 | Sep 27 |
| `test_link_analysis_direct.py` | 링크 분석 직접 호출 테스트 | Sep 29 |
| `test_link_analysis_simple.py` | 링크 분석 간단 테스트 | Sep 29 |
| `test_simple_cache.py` | 캐시 간단 테스트 | Sep 27 |
| `test_simple_extractor.py` | 컨텐츠 추출기 간단 테스트 | Sep 27 |
| `test_simple_gemini.py` | Gemini AI 간단 테스트 | Sep 27 |
| `test_simple_place_extractor.py` | 장소 추출기 간단 테스트 | Sep 27 |
| `test_url_normalization.py` | URL 정규화 테스트 | Sep 27 |

## 🔄 정식 테스트로 전환

임시 스크립트가 안정화되면 정식 테스트로 전환하세요:

### 1. Pytest 형식으로 변환
```python
# Before (임시 스크립트)
if __name__ == "__main__":
    test_something()

# After (정식 테스트)
def test_something():
    # Given-When-Then 구조
    pass
```

### 2. 적절한 위치로 이동
- Unit test → `tests/unit/`
- Integration test → `tests/integration/`
- E2E test → `tests/e2e/`

### 3. 테스트 가이드라인 준수
- `tests/README.md` 참조
- 테스트 네이밍 컨벤션 적용
- Mock 및 Fixture 활용

## 🗑️ 정리 기준

다음 조건에 해당하면 삭제를 고려하세요:

- [ ] 3개월 이상 사용하지 않음
- [ ] 관련 기능이 이미 정식 테스트로 전환됨
- [ ] 더 이상 필요하지 않은 실험적 기능

---

**참고**: 정식 테스트는 `tests/unit/`, `tests/integration/`, `tests/e2e/`에 있습니다.
