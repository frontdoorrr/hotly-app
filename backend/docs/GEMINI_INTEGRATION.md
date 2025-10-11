# Gemini AI Integration Guide

This document explains how to set up and use Google Gemini AI for place information extraction from SNS content.

## Overview

The Gemini Analyzer uses Google's Gemini 1.5 Flash model to extract structured place information from social media posts (Instagram, Naver Blog, YouTube, etc.).

## Features

- **Multimodal Analysis**: Processes both text and images
- **Structured Output**: Returns JSON formatted place information
- **Error Resilience**: Automatic retry with exponential backoff
- **Rate Limit Handling**: Graceful degradation when API limits are reached

## Setup

### 1. Get API Key

1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the generated API key

### 2. Configure Environment

Add the API key to your `.env` file:

```bash
# Google Gemini AI Configuration
GEMINI_API_KEY="your_actual_api_key_here"
```

### 3. Verify Configuration

Check if the API key is properly loaded:

```python
from app.core.config import settings

print(f"Gemini API Key configured: {bool(settings.GEMINI_API_KEY)}")
```

## Usage

### Basic Usage

```python
from app.services.ai.gemini_analyzer import GeminiAnalyzer
from app.schemas.ai import PlaceAnalysisRequest

# Initialize analyzer
analyzer = GeminiAnalyzer()

# Prepare request
request = PlaceAnalysisRequest(
    platform="instagram",
    content_text="강남 맛집 발견! 분위기 좋고 음식도 맛있어요",
    content_description="파스타가 정말 맛있었던 이탈리안 레스토랑",
    hashtags=["강남맛집", "이탈리안", "데이트코스"],
    images=[]  # Optional: PIL Image objects or URLs
)

# Analyze content
place_info = await analyzer.analyze_place_content(request)

print(f"Place: {place_info.name}")
print(f"Category: {place_info.category}")
print(f"Score: {place_info.recommendation_score}/10")
```

### Via API Endpoint

```bash
curl -X POST "http://localhost:8000/api/v1/link-analysis/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.instagram.com/p/ABC123xyz/"
  }'
```

## Response Format

The analyzer returns a `PlaceInfo` object with the following structure:

```json
{
  "name": "레스토랑 이름",
  "address": "서울시 강남구 테헤란로 123",
  "category": "restaurant",
  "keywords": ["이탈리안", "파스타", "분위기좋은", "데이트"],
  "recommendation_score": 8,
  "phone": "02-1234-5678",
  "website": "https://restaurant.com",
  "opening_hours": "매일 11:00-22:00",
  "price_range": "2-3만원"
}
```

### Category Values

- `restaurant` - 음식점
- `cafe` - 카페
- `bar` - 바/펍
- `tourist_attraction` - 관광지
- `shopping` - 쇼핑
- `accommodation` - 숙박
- `entertainment` - 엔터테인먼트
- `other` - 기타

## Error Handling

### Rate Limit Errors

When API quota is exceeded:

```python
from app.exceptions.ai import RateLimitError

try:
    result = await analyzer.analyze_place_content(request)
except RateLimitError as e:
    print(f"Rate limit exceeded: {e}")
    # Implement backoff or queue mechanism
```

### Service Unavailable

When Gemini API is down:

```python
from app.exceptions.ai import AIServiceUnavailableError

try:
    result = await analyzer.analyze_place_content(request)
except AIServiceUnavailableError as e:
    print(f"Service unavailable: {e}")
    # Use fallback or cached data
```

### Invalid Response

When API returns unexpected format:

```python
from app.exceptions.ai import InvalidResponseError

try:
    result = await analyzer.analyze_place_content(request)
except InvalidResponseError as e:
    print(f"Invalid response: {e}")
    # Log for debugging
```

## Model Configuration

### Current Model

- **Model**: `gemini-1.5-flash`
- **Strengths**: Fast, cost-effective, supports multimodal (text + images)
- **Use Case**: Real-time place extraction from SNS posts

### Alternative: High Accuracy

For higher accuracy (but slower and more expensive):

```python
# In gemini_analyzer.py __init__
self.model_name = "gemini-1.5-pro"
```

### Generation Parameters

Configured for consistent structured output:

```python
generation_config=genai.GenerationConfig(
    temperature=0.1,      # Low for consistency
    top_p=0.8,
    top_k=40,
    max_output_tokens=2048
)
```

## Performance Optimization

### Caching

Link analysis results are automatically cached:

```python
# First request: Calls Gemini API (~2-5 seconds)
result1 = await analyze_link(url="https://instagram.com/p/123")

# Subsequent requests: Returns cached result (~50ms)
result2 = await analyze_link(url="https://instagram.com/p/123")
```

### Retry Strategy

Automatic retry with exponential backoff:

- **Max Retries**: 3
- **Base Delay**: 1 second
- **Backoff**: Doubles each retry (1s → 2s → 4s)

## Monitoring

### Check API Usage

Monitor your API usage at:
- [Google Cloud Console](https://console.cloud.google.com/apis/api/generativelanguage.googleapis.com)

### Logging

All API calls are logged:

```python
import logging
logger = logging.getLogger("app.services.ai.gemini_analyzer")
logger.setLevel(logging.INFO)
```

## Best Practices

1. **Always set timeout**: Default 60 seconds is reasonable
2. **Handle rate limits**: Implement queue or backoff strategy
3. **Cache results**: Avoid redundant API calls
4. **Validate input**: Ensure content has meaningful text
5. **Monitor costs**: Track API usage and optimize prompts

## Troubleshooting

### "API key not configured"

**Solution**: Check `.env` file has `GEMINI_API_KEY` set

```bash
cat backend/.env | grep GEMINI_API_KEY
```

### "Empty response from Gemini API"

**Possible causes**:
- Content is too short or unclear
- Safety filters blocked the content
- API timeout

**Solution**: Add more context to the prompt or use fallback logic

### "Rate limit exceeded"

**Solution**: Implement request queuing:

```python
from asyncio import Semaphore

# Limit concurrent API calls
semaphore = Semaphore(5)  # Max 5 concurrent calls

async def limited_analyze(request):
    async with semaphore:
        return await analyzer.analyze_place_content(request)
```

## Cost Estimation

Gemini 1.5 Flash pricing (as of 2024):
- **Input**: $0.075 per 1M tokens
- **Output**: $0.30 per 1M tokens

Typical place extraction:
- **Input**: ~500 tokens (prompt + content)
- **Output**: ~150 tokens (JSON response)
- **Cost per request**: ~$0.00008 (less than 0.01 cents)

## References

- [Gemini API Documentation](https://ai.google.dev/docs)
- [Google AI Studio](https://makersuite.google.com)
- [Pricing](https://ai.google.dev/pricing)
