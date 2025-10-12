"""Multimodal prompt templates for place extraction."""

import json

MULTIMODAL_PLACE_EXTRACTION_PROMPT = """# 🎯 장소 정보 추출 전문가 AI

당신은 SNS 콘텐츠(텍스트 + 이미지)에서 장소 정보를 정확히 추출하는 AI입니다.

## 📋 입력 정보

**플랫폼:** {platform}
**제목/캡션:** {title}
**설명:** {description}
**해시태그:** {hashtags}

{image_instruction}

## 🎯 추출 목표

다음 정보를 **JSON 형식**으로 추출하세요:

```json
{{
  "name": "장소명 (필수)",
  "address": "상세 주소 (선택)",
  "category": "카테고리 (필수)",
  "business_hours": "영업시간 (선택)",
  "phone": "전화번호 (선택)",
  "keywords": ["키워드1", "키워드2"],
  "description": "간단한 설명 (50자 이내)",
  "recommendation_score": 8
}}
```

## 📐 추출 규칙

### 1️⃣ 장소명 (name) - 필수
- **우선순위 1**: 이미지 속 간판/상호명에서 OCR로 읽은 텍스트
- **우선순위 2**: 캡션/제목에서 명확히 언급된 장소명
- **우선순위 3**: 해시태그에서 추론한 장소명
- **형식**: 정확한 공식 상호명 (예: "카페 오아시스", "명동 교자")
- **주의**: 추측이 아닌 명확한 증거가 있어야 함

### 2️⃣ 주소 (address) - 선택
- **우선순위 1**: 이미지 속 주소 텍스트 (명함, 안내판 등)
- **우선순위 2**: 캡션/설명에 명시된 주소
- **우선순위 3**: 해시태그로 추론한 지역 (예: #성수동 → "서울 성동구 성수동")
- **형식**: "시/도 구/군 동/읍/면" 형식
- **불확실하면**: null 반환 (잘못된 주소보다 나음)

### 3️⃣ 카테고리 (category) - 필수
**가능한 카테고리:**
- "cafe" (커피, 디저트 제공)
- "restaurant" (식사 제공)
- "bar" (주류 제공)
- "tourist_attraction" (명소, 랜드마크)
- "shopping" (매장, 마켓)
- "accommodation" (호텔, 숙박)
- "entertainment" (문화공간, 미술관)
- "other" (기타)

**판단 근거:**
- 이미지 속 음식/인테리어
- 메뉴판 내용
- 캡션/해시태그 (#카페, #맛집 등)

### 4️⃣ 추천 점수 (recommendation_score) - 필수
- 1~10점 사이의 정수
- 콘텐츠의 긍정성, 이미지 품질, 설명 풍부도를 종합 평가

### 5️⃣ 키워드 (keywords)
- 장소의 특징을 나타내는 단어 3-10개
- 예: ["데이트", "브런치", "루프탑", "감성", "인스타", "핫플"]

### 6️⃣ 설명 (description)
- 장소 특징 요약 (50자 이내)
- 예: "북유럽 감성의 브런치 카페, 루프탑 좌석 인기"

## 🚨 중요 원칙

1. **이미지 우선**: 이미지에서 읽은 정보가 텍스트보다 우선
2. **사실만 추출**: 추측하지 말고, 명확한 증거가 있는 것만 추출
3. **불확실하면 null**: 잘못된 정보보다 누락이 나음
4. **JSON만 반환**: 설명 없이 JSON만 출력

## 📤 출력 형식

**반드시 아래 JSON 스키마를 따르세요:**

{json_schema}

---

이제 위 정보를 바탕으로 장소 정보를 JSON으로 추출하세요.
"""


def get_multimodal_prompt(
    platform: str,
    title: str,
    description: str,
    hashtags: str,
    image_instruction: str = "",
) -> str:
    """Generate multimodal prompt."""

    # JSON schema
    json_schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "address": {"type": ["string", "null"]},
            "category": {
                "type": "string",
                "enum": [
                    "cafe",
                    "restaurant",
                    "bar",
                    "tourist_attraction",
                    "shopping",
                    "accommodation",
                    "entertainment",
                    "other",
                ],
            },
            "business_hours": {"type": ["string", "null"]},
            "phone": {"type": ["string", "null"]},
            "keywords": {"type": "array", "items": {"type": "string"}},
            "description": {"type": "string", "maxLength": 50},
            "recommendation_score": {"type": "integer", "minimum": 1, "maximum": 10},
        },
        "required": ["name", "category", "recommendation_score"],
    }

    return MULTIMODAL_PLACE_EXTRACTION_PROMPT.format(
        platform=platform,
        title=title,
        description=description,
        hashtags=hashtags,
        image_instruction=image_instruction or "",
        json_schema=json.dumps(json_schema, indent=2, ensure_ascii=False),
    )


def get_image_analysis_instruction(num_images: int) -> str:
    """Get image-specific analysis instruction."""
    if num_images == 0:
        return ""

    if num_images == 1:
        return """
## 🖼️ 이미지 분석 지침
1장의 이미지가 제공되었습니다. 다음을 중점적으로 분석하세요:
1. **간판/상호명**: 이미지 속 텍스트(간판, 메뉴판 등)를 정확히 읽어 장소명 추출
2. **인테리어/외관**: 카페/레스토랑/관광지 등 카테고리 판단
3. **음식/메뉴**: 제공하는 음식 종류로 카테고리 보강
4. **위치 단서**: 랜드마크, 주변 환경으로 위치 추정

**중요**: 이미지에서 명확히 읽을 수 있는 정보를 최우선으로 사용하세요.
"""

    return f"""
## 🖼️ 이미지 분석 지침
{num_images}장의 이미지가 제공되었습니다. 다음을 중점적으로 분석하세요:
1. **간판/상호명**: 이미지 속 텍스트(간판, 메뉴판 등)를 정확히 읽어 장소명 추출
2. **인테리어/외관**: 카페/레스토랑/관광지 등 카테고리 판단
3. **음식/메뉴**: 제공하는 음식 종류로 카테고리 보강
4. **위치 단서**: 랜드마크, 주변 환경으로 위치 추정
5. **텍스트 일치도**: 이미지 속 정보와 캡션/해시태그 교차 검증

**중요**: 여러 이미지를 비교하여 일관성 있는 정보를 추출하세요.
"""
