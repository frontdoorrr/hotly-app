"""Prompt templates for place information extraction."""

PLACE_EXTRACTION_PROMPT_V1 = """
당신은 SNS 콘텐츠에서 장소 정보를 추출하는 전문가입니다.

다음 콘텐츠를 분석하여 장소 정보를 정확하게 추출해주세요:

**콘텐츠 정보:**
- 플랫폼: {platform}
- 제목: {title}
- 설명: {description}
- 해시태그: {hashtags}

**추출 요구사항:**
1. 장소명: 정확한 상호명 (브랜드명 포함)
2. 주소: 도로명주소 우선, 지역명이라도 포함
3. 카테고리: restaurant/cafe/bar/tourist_attraction/shopping/accommodation/entertainment/other 중 선택
4. 특징 키워드: 분위기, 메뉴, 가격대, 특색 등 (최대 10개)
5. 추천도: 콘텐츠 톤과 평가를 기반으로 1-10점 점수

**중요 지침:**
- 추측하지 말고 콘텐츠에 명시된 정보만 추출
- 장소가 명확하지 않으면 confidence를 낮게 설정
- 개인정보는 절대 추출하지 않음

**응답 형식:** 반드시 아래 JSON 스키마를 정확히 따라주세요.

{json_schema}

**JSON 응답만 출력하세요. 다른 설명이나 텍스트는 포함하지 마세요.**
"""


PLACE_EXTRACTION_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "string", "description": "Place name"},
        "address": {"type": ["string", "null"], "description": "Place address"},
        "category": {
            "type": "string",
            "enum": [
                "restaurant",
                "cafe",
                "bar",
                "tourist_attraction",
                "shopping",
                "accommodation",
                "entertainment",
                "other",
            ],
        },
        "keywords": {"type": "array", "items": {"type": "string"}, "maxItems": 10},
        "recommendation_score": {"type": "integer", "minimum": 1, "maximum": 10},
        "phone": {"type": ["string", "null"]},
        "website": {"type": ["string", "null"]},
        "opening_hours": {"type": ["string", "null"]},
        "price_range": {"type": ["string", "null"]},
    },
    "required": ["name", "category", "recommendation_score", "keywords"],
    "additionalProperties": False,
}
