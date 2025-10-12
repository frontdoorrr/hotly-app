https://medium.com/%40david_yoo/building-a-simple-youtube-ai-video-summarizer-07d372bfcb6a


저자의 이미지
대규모 언어 모델 ( LLM )을 기능적 도구에 통합하는 방법을 보여주기 위해 , YouTube 스크립트를 스크래핑 하고 요약하는 Python 애플리케이션을 살펴보겠습니다 . 이 프로젝트는 웹 스크래핑 , OpenAI API , Streamlit을 활용하여 유용하고 효율적인 도구를 개발합니다. 긴 비디오 스크립트를 간결한 요약으로 변환함으로써, 이 애플리케이션은 사용자의 귀중한 시간을 절약하고 전체 콘텐츠를 시청하지 않고도 비디오의 주요 내용을 빠르게 파악할 수 있도록 합니다.

David Yoo 의 스토리를 이메일로 받아보세요
이 작가의 업데이트를 받아보려면 무료로 Medium에 가입하세요.

이메일을 입력하세요
구독하다
모든 관련 코드와 데이터는 이 Github 저장소 에 저장됩니다.

개요
이 신청서는 세 가지 주요 구성 요소로 나뉩니다.

scrape_youtube.py :YouTube 동영상에서 메타데이터 , 대본 , 썸네일을 추출합니다.
summarize_text.py :OpenAI API를 사용하여 추출된 대본을 요약합니다 .
app.py :모든 것을 연결하는 Streamlit 웹 인터페이스를 빌드합니다.
1단계: YouTube 데이터 추출
첫 번째 단계는 YouTube URL에서 동영상 ID , 메타데이터 (제목 및 채널 이름), 대본 , 썸네일 이미지를 추출하는 것입니다. scrape_youtube.py 의 함수를 자세히 살펴보겠습니다 .

import sys 
import re 
import requests 
from bs4 import BeautifulSoup 
from youtube_transcript_api import YouTubeTranscriptApi 

def  extract_video_id ( url ): 
    match = re.search( r"v=([a-zA-Z0-9_-]+)" , url) 
    if  match : 
        return  match .group( 1 ) 
    else : 
        raise ValueError( "Invalid YouTube URL" )
extract_video_id (url): 이 함수는 정규 표현식을 사용하여 YouTube URL에서 비디오 ID를 추출합니다. 비디오 ID는 각 YouTube 비디오를 식별하는 고유 식별자로, URL의 "v=" 뒤에 위치합니다.
def extract_metadata (url): 
    r = requests.get ( url) 
    soup = BeautifulSoup (r.text, features= "html.parser" ) 
    title = soup.find ( "title" ).text channel     = soup.find ( " link" , itemprop= "name" )[ 'content' ]     return title, channel

extract_metadata (url): 이 함수는 YouTube 페이지의 HTML 콘텐츠를 가져와 BeautifulSoup 으로 파싱하여 비디오 제목과 채널 이름을 추출합니다. 제목은 태그에서 <title>, 채널 이름은 속성을 <link>가진 태그 에 저장됩니다 itemprop="name".
def  download_thumbnail ( video_id ): 
    image_url = f"https://img.youtube.com/vi/ {video_id} /hqdefault.jpg"
     img_data = requests.get(image_url).content 
    with  open ( 'thumbnail.jpg' , 'wb' ) as handler: 
        handler.write(img_data)
download_thumbnail (video_id): 이 함수는 비디오 ID를 사용하여 비디오 썸네일 이미지의 URL을 생성합니다. 그런 다음 이미지를 다운로드하여 로컬에 ' thumbnail.jpg '라는 이름으로 저장합니다.
def get_transcript (video_id): 
    transcript_raw = YouTubeTranscriptApi.get_transcript (video_id, 언어=[ 'en' , ' es' , 'ko' ])     transcript_full = ' ' . join ([i[ 'text' ] for i in transcript_raw])     return transcript_full

get_transcript (video_id): 이 함수는 .을 사용하여 비디오의 대본을 가져옵니다 YouTubeTranscriptApi. 대본은 가능한 경우 영어, 스페인어 또는 한국어로 제공됩니다. 그런 다음 원시 대본 데이터를 처리하여 텍스트를 추출하고 단일 문자열로 결합합니다.
매개변수가 없는 함수 YouTubeTranscriptApi.get_transcript()는 기본적으로 영어로 된 대본을 검색합니다. 영어 대본이 없는 비디오를 고려하여 매개변수 목록에 스페인어 와 한국어 등 다른 언어도 추가했습니다. 자세한 내용은 설명서 를 참조하세요.YouTubeTranscriptApi

2단계: 대본 요약
대본을 준비했다면 다음 단계는 요약하는 것입니다. 이 작업은 summarize_text.py 의 OpenAI API를 사용하여 수행됩니다. 이 스크립트를 실행하기 전에 OpenAI API 키를 환경 변수 로 설정해야 합니다 .

OPENAI_API_KEY= '여기에 API 키를 입력하세요' 내보내기
요약 스크립트는 다음과 같습니다.

import os 
from openai import OpenAI 

def  summarize_text ( text, lang= 'en' ): 
    OpenAI.api_key = os.getenv( "OPENAI_API_KEY" ) 
    client = OpenAI(api_key=OpenAI.api_key) 
    
    prompt = f""" 
    다음 텍스트는 원래 언어로 되어 있습니다. 출력을 다음 언어로 제공하세요: {lang} . 
    출력 형식을 다음과 같이 지정하세요. 
    
    요약: 
    비디오의 간략한 요약 
    
    주요 내용: 
    핵심 내용을 간결하게 나열한 목록 
    
    입력 텍스트: {text}
     """
    
     response = client.chat.completions.create( 
        messages=[{ "role" : "user" , "content" : prompt}], 
        model= "gpt-3.5-turbo" , 
        #model="gpt-4-turbo", # 성능 향상, 추론 속도 저하
     ) 
    
    summary_text = response.to_dict()[ 'choices' ][ 0 ][ 'message' ][ 'content' ] 
    return summary_text
summarize_text (text, lang='en'): 이 함수는 제공된 텍스트를 요약해 달라는 요청을 OpenAI API 에 보냅니다. API 키는 보안을 위해 환경 변수 에서 가져옵니다 . 프롬프트는 지정된 언어로 요약과 주요 내용을 요청하도록 설계되었습니다. 그런 다음 API의 응답을 파싱하여 요약 텍스트를 추출합니다.
데모 목적으로 최신 모델을 사용할 것입니다 gpt-3.5-turbo. 최신 모델은 gpt-4-turbo추론 시간이 느리지만 성능은 더 높습니다.

3단계: 웹 인터페이스 구축
마지막으로, app.py 파일 에서 Streamlit을 사용하여 웹 인터페이스를 생성합니다 . Streamlit은 데이터 과학 및 머신 러닝 프로젝트를 위한 웹 애플리케이션 제작 과정을 간소화하는 Python 라이브러리입니다. 이 파일은 다른 두 스크립트의 기능을 결합하여 사용자 친화적인 인터페이스를 제공합니다.

import streamlit as st 
from scrape_youtube import extract_video_id, get_transcript, extract_metadata, download_thumbnail 
from summarize_text import summarize_text 
import os 

def  main (): 
    title_text = "YouTube AI 비디오 요약기"
     image_url = "https://i.pinimg.com/originals/3a/36/20/3a36206f35352b4230d5fc9f17fcea92.png"
     html_code = f""" 
    <div style="display: flex; align-items: center; margin-bottom: 30px;"> 
        <img src=" {image_url} " alt="작은 이미지" style="width: 50px; height: 50px; margin-right: 15px;"> 
        <h3 style="font-size: 45px;"> {title_text} </h3> 
    </div> 
    """
     st.markdown(html_code, unsafe_allow_html= True ) 
    
    # URL에서 썸네일을 가져오는 함수 
    def  get_thumbnail_from_url ( url ): 
        video_id = extract_video_id(url) 
        download_thumbnail(video_id) 
    
    # URL에서 대본을 가져오는 함수 
    def  get_transcript_from_url ( url ): 
        video_id = extract_video_id(url) 
        transcript = get_transcript(video_id) 
        return transcript 

    # 텍스트를 요약하는 함수 
    def  summarize_transcript ( transcript, lang ): 
        summary = summarize_text(transcript, lang=lang) 
        return summary 

    st.subheader( "YouTube URL 입력:" ) 
    st.write( "YouTube 링크를 붙여넣어 콘텐츠를 요약합니다(대본이 있어야 함)" ) 
    url = st.text_input( "URL" ) 
    language = st.radio( "출력할 언어를 선택하세요:" , ( '영어' , '스페인어' , '한국어' )) 
    if st.button( "요약" ): 
        if url: 
            title, channel = extract_metadata(url) 
            st.subheader( "제목:" ) 
            st.write(제목) 
            st.subheader( "채널:" ) 
            st.write(채널) 
            
            get_thumbnail_from_url(url) 
            st.image(os.path.join(os.getcwd(), "thumbnail.jpg" ), caption= '축소판 그림', use_column_width= True ) 
            
            transcript = get_transcript_from_url(url) 
            summary = summarize_transcript(transcript, language) 
            st.subheader( "동영상 요약:" ) 
            st.write(summary) 
        else : 
            st.warning( "YouTube URL을 입력하세요." ) 
if __name__ == "__main__" : 
    main()
main (): 이 함수는 Streamlit 웹 인터페이스를 설정합니다. HTML과 CSS를 사용하여 사용자 지정 제목 과 이미지를 표시합니다. 또한 YouTube URL 입력 필드 , 언어 선택 라디오 버튼 , 요약 프로세스를 트리거하는 버튼을 제공합니다 .
get_thumbnail_from_url (url): URL에서 비디오 ID를 추출하고 썸네일 이미지를 다운로드합니다.
get_transcript_from_url (url): URL에서 비디오 ID를 추출하고 대본을 검색합니다.
summarize_transcript (transcript, lang): summarize_text지정된 언어로 대본을 요약하는 함수를 호출합니다.
모두 하나로 모으기
비디오 ID 및 메타데이터 추출 : 사용자가 YouTube URL을 입력하면 앱은 .을 사용하여 비디오 ID를 추출하고 제목과 채널 이름을 검색합니다 extract_metadata(url).
썸네일 다운로드 : 앱은 비디오의 썸네일을 다운로드하여 표시합니다 get_thumbnail_from_url(url).
대본 가져오기 및 요약 : 대본은 를 사용하여 가져 get_transcript_from_url(url)오고 를 사용하여 요약합니다 summarize_transcript(transcript, language). 요약은 선택한 언어로 표시됩니다.
아래는 이 애플리케이션이 작동하는 방식을 보여주는 비디오 데모입니다.


결론
이 YouTube AI 비디오 요약기는 대규모 언어 모델 ( LLM )을 실제 애플리케이션에 간편하게 통합하는 방법을 보여줍니다 . 웹 스크래핑 , OpenAI API , Streamlit을 결합하여 콘텐츠 소비 효율성을 향상시키는 애플리케이션을 만들었습니다. OpenAI API 키를 환경 변수 로 설정하면 API에 안전하고 쉽게 액세스할 수 있습니다. 코드를 확인 하고 직접 사용해 보세요!

https://github.com/DavidYoo912/youtube_summarizer