"""
피드백 서비스 간단한 테스트
"""
import asyncio
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from datetime import datetime

from app.services.search_feedback_service import SearchFeedbackService
from app.schemas.search_ranking import FeedbackType
from app.core.cache import MemoryCacheService

async def test_feedback_collection():
    """피드백 수집 테스트"""
    # Mock dependencies with async support
    mock_db = AsyncMock()
    cache_service = MemoryCacheService()
    mock_ml_engine = AsyncMock()
    
    # 서비스 생성
    feedback_service = SearchFeedbackService(mock_db, cache_service, mock_ml_engine)
    
    # 테스트 데이터
    user_id = uuid4()
    place_id = uuid4()
    
    # 피드백 수집
    result = await feedback_service.collect_search_feedback(
        user_id=user_id,
        search_session_id="test_session",
        place_id=place_id,
        feedback_type=FeedbackType.CLICK,
        context={"category": "cafe", "distance": 500},
        metadata={"source": "search_results"}
    )
    
    assert result == True
    print("✅ 피드백 수집 테스트 통과")

async def test_feedback_to_training_data_conversion():
    """피드백을 훈련 데이터로 변환하는 테스트"""
    mock_db = AsyncMock() 
    cache_service = MemoryCacheService()
    mock_ml_engine = AsyncMock()
    
    feedback_service = SearchFeedbackService(mock_db, cache_service, mock_ml_engine)
    
    # 테스트 피드백 데이터
    feedback_data = [
        {
            'feedback_type': 'click',
            'place_id': 'place1',
            'context': {'category': 'cafe', 'distance': 500},
            'metadata': {'source': 'search'}
        },
        {
            'feedback_type': 'bookmark', 
            'place_id': 'place2',
            'context': {'category': 'restaurant', 'distance': 1000},
            'metadata': {'source': 'recommendation'}
        }
    ]
    
    # 훈련 데이터 변환
    training_data = await feedback_service._convert_feedback_to_training_data(feedback_data)
    
    assert len(training_data) == len(feedback_data)
    assert all('features' in item and 'score' in item for item in training_data)
    
    print("✅ 피드백-훈련데이터 변환 테스트 통과")

def test_feedback_distribution_analysis():
    """피드백 분포 분석 테스트"""
    mock_db = AsyncMock()
    cache_service = MemoryCacheService()
    mock_ml_engine = AsyncMock()
    
    feedback_service = SearchFeedbackService(mock_db, cache_service, mock_ml_engine)
    
    # 테스트 피드백 데이터
    feedback_data = [
        {'feedback_type': 'click'},
        {'feedback_type': 'click'},
        {'feedback_type': 'bookmark'},
        {'feedback_type': 'visit'},
        {'feedback_type': 'skip'},
    ]
    
    distribution = feedback_service._analyze_feedback_distribution(feedback_data)
    
    assert distribution['click'] == 2
    assert distribution['bookmark'] == 1
    assert distribution['visit'] == 1
    assert distribution['skip'] == 1
    
    print("✅ 피드백 분포 분석 테스트 통과")

def test_interaction_quality_calculation():
    """상호작용 품질 계산 테스트"""
    mock_db = AsyncMock()
    cache_service = MemoryCacheService()
    mock_ml_engine = AsyncMock()
    
    feedback_service = SearchFeedbackService(mock_db, cache_service, mock_ml_engine)
    
    # 고품질 피드백 데이터
    high_quality_feedback = [
        {'feedback_type': 'visit'},
        {'feedback_type': 'bookmark'},
        {'feedback_type': 'click'},
    ]
    
    # 저품질 피드백 데이터  
    low_quality_feedback = [
        {'feedback_type': 'skip'},
        {'feedback_type': 'negative'},
        {'feedback_type': 'view'},
    ]
    
    high_quality_score = feedback_service._calculate_interaction_quality(high_quality_feedback)
    low_quality_score = feedback_service._calculate_interaction_quality(low_quality_feedback)
    
    assert high_quality_score > low_quality_score
    assert 0 <= high_quality_score <= 1
    assert 0 <= low_quality_score <= 1
    
    print("✅ 상호작용 품질 계산 테스트 통과")

async def main():
    """모든 테스트 실행"""
    await test_feedback_collection()
    await test_feedback_to_training_data_conversion()
    test_feedback_distribution_analysis()
    test_interaction_quality_calculation()
    print("🎉 모든 피드백 테스트 통과!")

if __name__ == "__main__":
    asyncio.run(main())