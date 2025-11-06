#!/usr/bin/env python3
"""
Gemini 2.5 비디오 분석 기능 테스트 스크립트

로컬 비디오 파일을 Gemini 2.5로 분석합니다.

필수 패키지:
  pip install google-genai

제약사항:
  - 비디오 파일 크기: 20MB 이하
"""

import json
import sys
from pathlib import Path

# ============================================
# 🔑 API 키 설정 (여기에 입력하세요)
# ============================================
GEMINI_API_KEY = "--"


# ============================================
# 분석 프롬프트 설정
# ============================================
ANALYSIS_PROMPT = """
이 Instagram 비디오를 분석하여 다음 정보를 JSON 형식으로 추출해주세요:

{
  "category": "음식점/카페/여행지/제품/건강/생활 중 하나",
  "sub_categories": ["세부 카테고리 리스트"],
  "place_info": {
    "name": "장소명 (있다면)",
    "location": "위치 정보",
    "features": ["특징 리스트"]
  },
  "menu_items": [
    {
      "name": "메뉴/제품명",
      "price": "가격 (있다면)",
      "description": "설명"
    }
  ],
  "extracted_text": ["비디오에서 보이는 모든 텍스트"],
  "audio_transcript": "음성으로 말하는 내용 전사",
  "sentiment": "positive/negative/neutral",
  "summary": "2-3문장으로 핵심 요약",
  "keywords": ["주요 키워드 리스트"],
  "recommended_for": ["추천 대상/상황"],
  "confidence": 0.0-1.0
}

비디오의 시각적 요소(텍스트, 간판, 메뉴판)와 음성 정보를 모두 활용하여 정확하게 분석해주세요.
"""


def check_file_size(video_path: str, max_size_mb: int = 20) -> bool:
    """
    비디오 파일 크기 확인 (20MB 제한)

    Args:
        video_path: 비디오 파일 경로
        max_size_mb: 최대 파일 크기 (MB)

    Returns:
        True if 크기 OK, False otherwise
    """
    file_size = Path(video_path).stat().st_size
    file_size_mb = file_size / (1024 * 1024)

    print(f"📦 파일 크기: {file_size_mb:.2f}MB")

    if file_size_mb > max_size_mb:
        print(f"❌ 파일이 너무 큽니다! (제한: {max_size_mb}MB)")
        return False

    return True


def analyze_video_from_file(video_path: str) -> dict:
    """
    로컬 비디오 파일을 Gemini 2.5로 분석

    Args:
        video_path: 비디오 파일 경로

    Returns:
        분석 결과 딕셔너리
    """
    from google import genai
    from google.genai import types

    # API 키 검증
    if GEMINI_API_KEY == "your_gemini_api_key_here":
        raise ValueError("❌ GEMINI_API_KEY를 설정해주세요!")

    print(f"🎬 비디오 분석 시작: {video_path}\n")

    # 파일 크기 확인
    if not check_file_size(video_path):
        return {"error": "파일 크기 제한 초과 (20MB)"}

    try:
        # 비디오 파일 읽기
        print("📖 비디오 파일 읽는 중...")
        with open(video_path, 'rb') as f:
            video_bytes = f.read()
        print(f"✅ 파일 로드 완료\n")

        # Gemini 클라이언트 초기화
        client = genai.Client(api_key=GEMINI_API_KEY)

        # 비디오 분석
        print("🤖 Gemini 2.5로 분석 중...")
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=types.Content(
                parts=[
                    types.Part(
                        inline_data=types.Blob(
                            data=video_bytes,
                            mime_type='video/mp4'
                        )
                    ),
                    # types.Part(text=ANALYSIS_PROMPT)
                ]
            )
        )

        print("✅ 분석 완료!\n")

        # 결과 추출
        result_text = response.text

        # JSON 추출 시도
        try:
            # JSON 코드 블록 제거
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0]
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0]

            result = json.loads(result_text.strip())
        except json.JSONDecodeError:
            # JSON 파싱 실패 시 텍스트 그대로 반환
            result = {
                "raw_response": result_text,
                "parsing_note": "JSON 형식이 아닌 응답"
            }

        return result

    except FileNotFoundError:
        return {"error": f"파일을 찾을 수 없습니다: {video_path}"}
    except Exception as e:
        return {
            "error": str(e),
            "error_type": type(e).__name__
        }


def main():
    """메인 함수"""
    print("=" * 60)
    print("🎥 Gemini 2.5 비디오 분석 테스트")
    print("=" * 60)
    print()

    # 사용 방법 안내
    print("📌 사용 방법:")
    print("로컬 비디오 파일 경로를 입력하세요 (20MB 이하)")
    print()

    # 입력 받기
    if len(sys.argv) > 1:
        video_path = sys.argv[1]
    else:
        video_path = input("🎬 비디오 파일 경로를 입력하세요: ").strip()

    if not video_path:
        print("❌ 파일 경로를 입력해주세요!")
        return

    print()

    # 분석 실행
    result = analyze_video_from_file(video_path)

    # 결과 출력
    print("\n" + "=" * 60)
    print("📊 분석 결과")
    print("=" * 60)
    print()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print()

    # 결과 저장
    output_file = Path("gemini_analysis_result.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"✅ 결과가 {output_file}에 저장되었습니다.")


if __name__ == "__main__":
    main()
