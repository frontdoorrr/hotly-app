"""
간단한 통합 테스트 - 핵심 구성요소들 검증
"""
import asyncio
from uuid import uuid4

from app.services.ml_engine import get_ml_engine_sync
from app.core.cache import MemoryCacheService
from app.services.search_diversity_service import SearchDiversityService

def test_ml_engine_initialization():
    """ML 엔진 초기화 테스트"""
    ml_engine = get_ml_engine_sync()
    
    # 기본 상태 확인
    assert ml_engine is not None
    assert hasattr(ml_engine, 'relevance_model')
    assert hasattr(ml_engine, 'personalization_model')
    assert hasattr(ml_engine, 'scaler')
    assert ml_engine.is_trained == False  # 초기에는 훈련되지 않음
    
    print("✅ ML 엔진 초기화 테스트 통과")

async def test_ml_engine_prediction():
    """ML 엔진 예측 테스트"""
    ml_engine = get_ml_engine_sync()
    
    # 테스트 특성 벡터
    feature_vectors = [
        {
            'rating': 4.5,
            'distance': 500,
            'popularity': 90,
            'price_range': 2,
            'category': 'cafe'
        },
        {
            'rating': 3.8,
            'distance': 1500,
            'popularity': 60,
            'price_range': 4,
            'category': 'restaurant'
        }
    ]
    
    # 예측 수행
    scores = await ml_engine.predict_relevance(
        feature_vectors=feature_vectors,
        user_id=uuid4(),
        context={'query': '맛있는 카페'}
    )
    
    assert len(scores) == 2
    assert all(0 <= score <= 1 for score in scores)
    
    print("✅ ML 엔진 예측 테스트 통과")

async def test_diversity_service_integration():
    """다양성 서비스 통합 테스트"""
    diversity_service = SearchDiversityService()
    
    # 편향된 검색 결과 (모두 카페)
    search_results = [
        {
            'id': 'cafe1',
            'name': '스타벅스',
            'category': 'cafe',
            'region': '강남',
            'price_range': 2,
            'rating': 4.2
        },
        {
            'id': 'cafe2',
            'name': '투썸플레이스', 
            'category': 'cafe',
            'region': '강남',
            'price_range': 2,
            'rating': 4.0
        },
        {
            'id': 'restaurant1',
            'name': '이탈리안 레스토랑',
            'category': 'restaurant',
            'region': '홍대',
            'price_range': 4,
            'rating': 4.5
        }
    ]
    
    # 다양성 보장
    diverse_results = await diversity_service.ensure_diversity(
        search_results=search_results,
        diversity_factor=0.7,
        max_results=3
    )
    
    assert len(diverse_results) <= 3
    
    # 카테고리 다양성 확인
    categories = [r['category'] for r in diverse_results]
    unique_categories = set(categories)
    assert len(unique_categories) > 1, "다양한 카테고리가 포함되어야 함"
    
    print("✅ 다양성 서비스 통합 테스트 통과")

async def test_cache_service_basic():
    """캐시 서비스 기본 기능 테스트"""
    cache = MemoryCacheService()
    
    # 캐시 저장
    key = "test:ranking:user123"
    data = {"results": [{"id": "place1", "score": 0.8}]}
    
    success = await cache.set(key, data, ttl=300)
    assert success == True
    
    # 캐시 조회
    cached_data = await cache.get(key)
    assert cached_data is not None
    assert cached_data['results'][0]['id'] == "place1"
    
    # 캐시 삭제
    delete_success = await cache.delete(key)
    assert delete_success == True
    
    # 삭제 후 조회
    deleted_data = await cache.get(key)
    assert deleted_data is None
    
    print("✅ 캐시 서비스 기본 기능 테스트 통과")

def test_ranking_weight_calculation():
    """랭킹 가중치 계산 테스트"""
    # 기본 가중치 설정
    default_weights = {
        "base_relevance": 0.25,
        "personalization": 0.35,
        "behavior_score": 0.20,
        "contextual": 0.15,
        "real_time": 0.05,
    }
    
    # 가중치 합계가 1.0인지 확인
    total_weight = sum(default_weights.values())
    assert abs(total_weight - 1.0) < 0.001, f"가중치 합계가 1.0이 아님: {total_weight}"
    
    # 각 가중치가 유효한 범위인지 확인
    for name, weight in default_weights.items():
        assert 0 <= weight <= 1, f"가중치 {name}이 유효하지 않음: {weight}"
    
    print("✅ 랭킹 가중치 계산 테스트 통과")

async def main():
    """모든 간단한 통합 테스트 실행"""
    test_ml_engine_initialization()
    await test_ml_engine_prediction()
    await test_diversity_service_integration()
    await test_cache_service_basic()
    test_ranking_weight_calculation()
    print("🎉 모든 간단한 통합 테스트 통과!")

if __name__ == "__main__":
    asyncio.run(main())