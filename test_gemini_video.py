#!/usr/bin/env python3
"""
Gemini 2.5 비디오 분석 기능 테스트 스크립트

YouTube URL 또는 로컬 비디오 파일을 Gemini 2.5로 분석합니다.

필수 패키지:
  pip install google-genai

사용 예시:
  python test_gemini_video.py "https://www.youtube.com/watch?v=xxx"
  python test_gemini_video.py "video.mp4"
"""

import json
import sys
import time
from pathlib import Path

# ============================================
# 🔑 API 키 설정 (여기에 입력하세요)
# ============================================
GEMINI_API_KEY = "AIzaSyBYPG6AEK7Vga4pdOQZvcrYPiIsWeiMKAI"


# ============================================
# 분석 프롬프트 설정
# ============================================
SIMPLE_PROMPT = """
해당 프로그램의 사용법을 순서대로 번호붙여 최대한 자세히 설명해주세요.
"""


def is_youtube_url(input_str: str) -> bool:
    """YouTube URL인지 확인"""
    return (
        input_str.startswith("http")
        and "youtube.com" in input_str
        or "youtu.be" in input_str
    )


def analyze_video(input_source: str, use_prompt: bool = True) -> dict:
    """
    YouTube URL 또는 로컬 비디오 파일을 Gemini 2.5로 분석

    Args:
        input_source: YouTube URL 또는 로컬 파일 경로
        use_prompt: 프롬프트 사용 여부

    Returns:
        분석 결과 딕셔너리
    """
    from google import genai
    from google.genai import types

    # API 키 검증
    if GEMINI_API_KEY == "your_gemini_api_key_here":
        raise ValueError("❌ GEMINI_API_KEY를 설정해주세요!")

    is_youtube = is_youtube_url(input_source)

    print(f"🎬 비디오 분석 시작")
    print(f"입력: {'YouTube URL' if is_youtube else '로컬 파일'} - {input_source}\n")

    try:
        # Gemini 클라이언트 초기화
        client = genai.Client(api_key=GEMINI_API_KEY)

        # 비디오 파트 생성
        if is_youtube:
            print("📺 YouTube URL로 분석 중...")
            video_part = types.Part.from_uri(
                file_uri=input_source, mime_type="video/mp4"
            )
        else:
            # 로컬 파일
            print("📖 로컬 파일 읽는 중...")
            with open(input_source, "rb") as f:
                video_bytes = f.read()

            file_size_mb = len(video_bytes) / (1024 * 1024)
            print(f"📦 파일 크기: {file_size_mb:.2f}MB")

            if file_size_mb > 20:
                return {"error": "파일 크기 제한 초과 (20MB)"}

            video_part = types.Part(
                inline_data=types.Blob(data=video_bytes, mime_type="video/mp4"),
            )

        # 프롬프트 구성
        parts = [video_part]
        if use_prompt:
            parts.append(types.Part(text=SIMPLE_PROMPT))

        # 비디오 분석
        print("🤖 Gemini 2.5로 분석 중...\n")
        start_time = time.time()

        response = client.models.generate_content(
            model="gemini-2.5-flash", contents=parts
        )

        elapsed = time.time() - start_time
        print(f"✅ 분석 완료! (소요 시간: {elapsed:.2f}초)\n")

        # 결과 추출
        result_text = response.text

        # JSON 추출 시도
        if use_prompt:
            try:
                # JSON 코드 블록 제거
                if "```json" in result_text:
                    result_text = result_text.split("```json")[1].split("```")[0]
                elif "```" in result_text:
                    result_text = result_text.split("```")[1].split("```")[0]

                result = json.loads(result_text.strip())
                result["_elapsed_time"] = f"{elapsed:.2f}s"
            except json.JSONDecodeError:
                # JSON 파싱 실패 시 텍스트 그대로 반환
                result = {
                    "raw_response": result_text,
                    "parsing_note": "JSON 형식이 아닌 응답",
                    "_elapsed_time": f"{elapsed:.2f}s",
                }
        else:
            result = {"raw_response": result_text, "_elapsed_time": f"{elapsed:.2f}s"}

        return result

    except FileNotFoundError:
        return {"error": f"파일을 찾을 수 없습니다: {input_source}"}
    except Exception as e:
        return {"error": str(e), "error_type": type(e).__name__}


def main():
    """메인 함수"""
    print("=" * 60)
    print("🎥 Gemini 2.5 비디오 분석 테스트")
    print("=" * 60)
    print()

    # 사용 방법 안내
    print("📌 사용 방법:")
    print(
        '  - YouTube URL: python test_gemini_video.py "https://www.youtube.com/watch?v=xxx"'
    )
    print('  - 로컬 파일: python test_gemini_video.py "video.mp4" (20MB 이하)')
    print()

    # 입력 받기
    if len(sys.argv) > 1:
        input_source = sys.argv[1]
    else:
        input_source = input("🎬 YouTube URL 또는 파일 경로를 입력하세요: ").strip()

    if not input_source:
        print("❌ URL 또는 파일 경로를 입력해주세요!")
        return

    # 프롬프트 사용 여부
    use_prompt = True
    if len(sys.argv) > 2 and sys.argv[2] == "--no-prompt":
        use_prompt = False
        print("⚠️  프롬프트 없이 실행합니다.\n")

    print()

    # 분석 실행
    result = analyze_video(input_source, use_prompt=use_prompt)

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
