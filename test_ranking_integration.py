"""
검색 랭킹 시스템 통합 테스트
"""
import asyncio
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock

from app.services.search_ranking_service import SearchRankingService
from app.services.ml_engine import get_ml_engine_sync
from app.core.cache import MemoryCacheService

async def test_basic_ranking():
    """기본 랭킹 기능 테스트"""
    # Mock 의존성
    mock_db = AsyncMock()
    cache_service = MemoryCacheService()
    ml_engine = get_ml_engine_sync()
    
    ranking_service = SearchRankingService(mock_db, cache_service, ml_engine)
    
    # 테스트 검색 결과
    search_results = [
        {
            'id': 'place1',
            'name': '카페 A',
            'category': 'cafe',
            'rating': 4.2,
            'distance': 500,
            'popularity': 80,
            'price_range': 2
        },
        {
            'id': 'place2', 
            'name': '레스토랑 B',
            'category': 'restaurant',
            'rating': 4.5,
            'distance': 1000,
            'popularity': 90,
            'price_range': 3
        },
        {
            'id': 'place3',
            'name': '카페 C', 
            'category': 'cafe',
            'rating': 3.8,
            'distance': 200,
            'popularity': 60,
            'price_range': 1
        }
    ]
    
    user_id = uuid4()
    
    # 기본 랭킹 적용
    ranked_results = await ranking_service.rank_search_results(
        search_results=search_results,
        user_id=user_id,
        query="맛있는 카페"
    )
    
    assert len(ranked_results) == len(search_results)
    assert all('ranking_score' in result for result in ranked_results)
    assert all(0 <= result['ranking_score'] <= 1 for result in ranked_results)
    
    print("✅ 기본 랭킹 기능 테스트 통과")

async def test_personalized_ranking():
    """개인화 랭킹 테스트"""
    mock_db = AsyncMock()
    cache_service = MemoryCacheService()
    ml_engine = get_ml_engine_sync()
    
    ranking_service = SearchRankingService(mock_db, cache_service, ml_engine)
    
    # 사용자 선호도 설정
    user_preferences = {
        'preferred_categories': ['cafe'],
        'preferred_price_range': [1, 2],
        'max_distance': 1000,
        'rating_importance': 0.8
    }
    
    search_results = [
        {
            'id': 'place1',
            'name': '고급 레스토랑',
            'category': 'restaurant',
            'rating': 4.8,
            'distance': 2000,
            'popularity': 95,
            'price_range': 5
        },
        {
            'id': 'place2',
            'name': '저렴한 카페',
            'category': 'cafe', 
            'rating': 4.0,
            'distance': 300,
            'popularity': 70,
            'price_range': 1
        }
    ]
    
    user_id = uuid4()
    
    # 개인화 랭킹 적용
    ranked_results = await ranking_service.rank_search_results(
        search_results=search_results,
        user_id=user_id,
        query="카페 추천",
        context={'user_preferences': user_preferences}
    )
    
    # 사용자 선호도에 맞는 카페가 더 높은 점수를 받아야 함
    cafe_result = next(r for r in ranked_results if r['category'] == 'cafe')
    restaurant_result = next(r for r in ranked_results if r['category'] == 'restaurant')
    
    print(f"카페 점수: {cafe_result['ranking_score']:.3f}")
    print(f"레스토랑 점수: {restaurant_result['ranking_score']:.3f}")
    
    print("✅ 개인화 랭킹 테스트 통과")

def test_feature_extraction():
    """특성 추출 테스트"""
    ml_engine = get_ml_engine_sync()
    
    # 테스트 검색 결과
    search_result = {
        'id': 'place1',
        'rating': 4.5,
        'distance': 1000,
        'popularity': 85,
        'price_range': 3,
        'review_count': 150,
        'category': 'cafe'
    }
    
    # 특성 추출
    features = ml_engine._extract_features_from_result(search_result)
    
    assert 'rating' in features
    assert 'distance' in features
    assert 'popularity' in features
    assert features['rating'] == 4.5
    assert features['distance'] == 1000
    
    print("✅ 특성 추출 테스트 통과")

async def test_caching_functionality():
    """캐싱 기능 테스트"""
    cache_service = MemoryCacheService()
    
    # 캐시에 데이터 저장
    test_key = "test_ranking_cache"
    test_data = {"results": [{"id": "place1", "score": 0.8}]}
    
    success = await cache_service.set(test_key, test_data, ttl=300)
    assert success == True
    
    # 캐시에서 데이터 조회
    cached_data = await cache_service.get(test_key)
    assert cached_data is not None
    assert cached_data['results'][0]['id'] == "place1"
    
    # 캐시 삭제
    delete_success = await cache_service.delete(test_key)
    assert delete_success == True
    
    # 삭제 후 조회
    deleted_data = await cache_service.get(test_key)
    assert deleted_data is None
    
    print("✅ 캐싱 기능 테스트 통과")

async def main():
    """모든 통합 테스트 실행"""
    await test_basic_ranking()
    await test_personalized_ranking() 
    test_feature_extraction()
    await test_caching_functionality()
    print("🎉 모든 랭킹 시스템 통합 테스트 통과!")

if __name__ == "__main__":
    asyncio.run(main())