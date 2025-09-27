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


PLACE_EXTRACTION_PROMPT_V2 = """
You are an expert at extracting place information from social media content.

**Task:** Analyze the following content and extract place information with high accuracy.

**Platform:** {platform}
**Content to analyze:**
{content}

**Platform-specific instructions:**
{platform_instruction}

**Extraction Requirements:**
1. **Place Name**: Exact business name (include brand name if applicable)
2. **Address**: Street address preferred, or at least neighborhood/district
3. **Category**: Choose from restaurant, cafe, bar, tourist_attraction, shopping, accommodation, entertainment, other
4. **Confidence**: Rate your confidence as "high", "medium", or "low"
5. **Description**: Brief description of the place based on content
6. **Keywords**: Characteristic features (max 10)

**Critical Guidelines:**
- Only extract information explicitly mentioned in the content
- If a place is unclear or ambiguous, set confidence to "low"
- Multiple places are allowed if clearly mentioned
- Never include personal information
- Focus on businesses and public places only

**Response Format:** Must follow this exact JSON schema:

```json
{{
  "places": [
    {{
      "name": "string",
      "address": "string or null",
      "category": "restaurant|cafe|bar|tourist_attraction|shopping|accommodation|entertainment|other",
      "confidence": "high|medium|low",
      "description": "string or null"
    }}
  ],
  "analysis_confidence": "high|medium|low"
}}
```

**Output only the JSON response. No additional text or explanations.**
"""


MULTIMODAL_PLACE_EXTRACTION_PROMPT = """
You are analyzing both text content and images to extract place information.

**Text Content:**
{text_content}

**Images:** {image_count} image(s) provided for visual analysis

**Instructions for Visual Analysis:**
- Look for storefront signs, business names, menu boards
- Identify restaurant/cafe/shop interiors or exteriors  
- Extract text from images (OCR) for business names
- Note visual clues about place category (food, shopping, etc.)
- Consider image context along with text description

**Confidence Scoring:**
- High: Place clearly identified in both text and images
- Medium: Place mentioned in text with supporting visual evidence
- Low: Place mentioned but unclear or conflicting information

Follow the same JSON response format as standard extraction.
"""
