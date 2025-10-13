import '../models/place.dart';

/// Mock 데이터 - 개발 및 테스트용
/// dummy.json의 Kakao 즐겨찾기 데이터를 Place 모델로 변환
class MockPlaces {
  static final List<Place> savedPlaces = [
    // 서울 - 마포/상수 카페
    Place(
      id: '913503433',
      name: '장싸롱리저브',
      address: '서울 마포구 와우산로3길 31 1호 (상수동)',
      latitude: 37.54580847,
      longitude: 126.92130939,
      description: '상수동의 감성 있는 카페',
      category: '카페',
      rating: 4.5,
      reviewCount: 89,
      tags: ['상수동', '카페', '감성'],
      isSaved: true,
    ),

    // 일산 - 키딩2
    Place(
      id: '483811924',
      name: '키딩2',
      address: '경기 고양시 일산동구 대산로11번길 5-4 (정발산동)',
      latitude: 37.66912698,
      longitude: 126.77459623,
      description: '일산의 인기 디저트 카페',
      category: '카페',
      rating: 4.7,
      reviewCount: 156,
      tags: ['일산', '카페', '디저트'],
      isSaved: true,
    ),

    // 일산 - 포쉬커피
    Place(
      id: '2046492848',
      name: '포쉬커피',
      address: '경기 고양시 일산동구 일산로380번길 5-19 1층 (정발산동)',
      latitude: 37.66984988,
      longitude: 126.78146739,
      description: '정발산동의 세련된 커피 전문점',
      category: '카페',
      rating: 4.6,
      reviewCount: 234,
      tags: ['일산', '커피', '정발산'],
      isSaved: true,
    ),

    // 제주 - 제주술익는집
    Place(
      id: '1240625494',
      name: '제주술익는집',
      address: '제주특별자치도 서귀포시 표선면 중산간동로 4726 (표선면 성읍리)',
      latitude: 33.38495886,
      longitude: 126.79377368,
      description: '제주의 전통 술과 음식을 맛볼 수 있는 곳',
      category: '음식점',
      rating: 4.8,
      reviewCount: 312,
      tags: ['제주', '서귀포', '한식', '전통주'],
      isSaved: true,
    ),

    // 제주 - 아베베비킬라베이커리
    Place(
      id: '1431802252',
      name: '아베베비킬라베이커리',
      address: '제주특별자치도 제주시 구좌읍 해맞이해안로 617-4 B동 (구좌읍 행원리)',
      latitude: 33.5570829,
      longitude: 126.80965216,
      description: '제주 바다 뷰가 아름다운 베이커리',
      category: '베이커리',
      rating: 4.9,
      reviewCount: 428,
      tags: ['제주', '베이커리', '오션뷰'],
      isLiked: true,
      isSaved: true,
    ),

    // 제주 - 월정기록
    Place(
      id: '1357485911',
      name: '월정기록',
      address: '제주특별자치도 제주시 구좌읍 월정5길 47 1층 (구좌읍 월정리)',
      latitude: 33.55452743,
      longitude: 126.79475433,
      description: '월정리 해변 근처의 감성 카페',
      category: '카페',
      rating: 4.7,
      reviewCount: 367,
      tags: ['제주', '월정리', '카페', '해변'],
      isSaved: true,
    ),

    // 고양 삼송 - 탐닉바이삼송
    Place(
      id: '1393858416',
      name: '탐닉바이삼송',
      address: '경기 고양시 덕양구 신도2길 8 1층 (삼송동)',
      latitude: 37.65237896,
      longitude: 126.89517874,
      description: '삼송동의 트렌디한 브런치 카페',
      category: '카페',
      rating: 4.5,
      reviewCount: 198,
      tags: ['삼송', '브런치', '카페'],
      isSaved: true,
    ),

    // 서울 마곡 - 서울 오마카세 우미마토
    Place(
      id: '1862163744',
      name: '서울 오마카세 우미마토',
      address: '서울 강서구 공항대로 219 센테니아 1층 114호 (마곡동)',
      latitude: 37.55950803,
      longitude: 126.83226804,
      description: '프리미엄 일식 오마카세 레스토랑',
      category: '음식점',
      rating: 4.9,
      reviewCount: 445,
      tags: ['마곡', '일식', '오마카세', '고급'],
      isLiked: true,
      isSaved: true,
    ),

    // 서울 마곡 - 뱅션 원그로브점
    Place(
      id: '1994612419',
      name: '뱅션 원그로브점',
      address: '서울 강서구 공항대로 165 1층 (마곡동)',
      latitude: 37.56156867,
      longitude: 126.82669484,
      description: '마곡 원그로브의 디저트 카페',
      category: '카페',
      rating: 4.4,
      reviewCount: 276,
      tags: ['마곡', '디저트', '카페'],
      isSaved: true,
    ),

    // 제주 - 도립
    Place(
      id: '1206393936',
      name: '도립',
      address: '제주특별자치도 제주시 구좌읍 행원로5길 33 1층 (구좌읍 행원리)',
      latitude: 33.55605904,
      longitude: 126.80523929,
      description: '제주 감성의 카페 겸 갤러리',
      category: '카페',
      rating: 4.6,
      reviewCount: 189,
      tags: ['제주', '카페', '갤러리'],
      isSaved: true,
    ),

    // 일산 - 스즈메바치
    Place(
      id: '80752309',
      name: '스즈메바치',
      address: '경기 고양시 일산동구 백석로71번길 6-11 101~102호 (백석동)',
      latitude: 37.64756798,
      longitude: 126.78601987,
      description: '일본식 라멘 전문점',
      category: '음식점',
      rating: 4.7,
      reviewCount: 523,
      tags: ['일산', '라멘', '일식'],
      isSaved: true,
    ),

    // 서울 망원 - 루바토
    Place(
      id: '1725620089',
      name: '루바토',
      address: '서울 마포구 월드컵로19길 95 1층 (망원동)',
      latitude: 37.5536073,
      longitude: 126.90621782,
      description: '망원동의 감성 카페',
      category: '카페',
      rating: 4.5,
      reviewCount: 167,
      tags: ['망원동', '카페', '감성'],
      isSaved: true,
    ),

    // 고양 삼송 - 시스터후드
    Place(
      id: '383332600',
      name: '시스터후드',
      address: '경기 고양시 덕양구 삼송로 240 (삼송동)',
      latitude: 37.65318701,
      longitude: 126.90022721,
      description: '삼송동의 브런치 & 디저트 카페',
      category: '카페',
      rating: 4.6,
      reviewCount: 298,
      tags: ['삼송', '브런치', '디저트'],
      isSaved: true,
    ),

    // 서울 마곡 - 바틀리스트
    Place(
      id: '735096893',
      name: '바틀리스트',
      address: '서울 강서구 강서로 433 오드카운티2차상가 1층 116호 (마곡동)',
      latitude: 37.56439449,
      longitude: 126.8396595,
      description: '마곡의 와인 바 & 레스토랑',
      category: '음식점',
      rating: 4.8,
      reviewCount: 412,
      tags: ['마곡', '와인', '레스토랑'],
      isLiked: true,
      isSaved: true,
    ),

    // 서울 대흥동 - 스위그(Swig)
    Place(
      id: '267207347',
      name: '스위그(Swig)',
      address: '서울 마포구 백범로16안길 21 구가빌딩 1층 (대흥동)',
      latitude: 37.5464085,
      longitude: 126.94323005,
      description: '대흥동의 아늑한 커피 전문점',
      category: '카페',
      rating: 4.6,
      reviewCount: 145,
      tags: ['대흥동', '커피', '감성'],
      isSaved: true,
    ),

    // 서울 대흥동 - 파사주
    Place(
      id: '401805607',
      name: '파사주',
      address: '서울 마포구 백범로20길 24-5 상수라이크 1층 (대흥동)',
      latitude: 37.54592946,
      longitude: 126.94384147,
      description: '대흥동의 유럽풍 브런치 카페',
      category: '카페',
      rating: 4.7,
      reviewCount: 321,
      tags: ['대흥동', '브런치', '유럽풍'],
      isSaved: true,
    ),

    // 서울 합정 - 리틀케이브
    Place(
      id: '871754083',
      name: '리틀케이브',
      address: '서울 마포구 독막로4길 9 지층 지1호 (합정동)',
      latitude: 37.54771561,
      longitude: 126.91695292,
      description: '합정동 숨은 지하 카페',
      category: '카페',
      rating: 4.5,
      reviewCount: 178,
      tags: ['합정동', '카페', '힙'],
      isSaved: true,
    ),
  ];
}
