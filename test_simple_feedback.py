"""
간단한 피드백 서비스 테스트 - 핵심 로직만
"""
import asyncio
from unittest.mock import AsyncMock
from app.services.search_feedback_service import SearchFeedbackService
from app.core.cache import MemoryCacheService

def test_feedback_weights_exist():
    """피드백 가중치 설정 확인"""
    mock_db = AsyncMock()
    cache_service = MemoryCacheService() 
    mock_ml_engine = AsyncMock()
    
    feedback_service = SearchFeedbackService(mock_db, cache_service, mock_ml_engine)
    
    # 피드백 가중치가 존재하는지 확인
    assert hasattr(feedback_service, 'feedback_weights')
    assert 'visit' in feedback_service.feedback_weights
    assert 'bookmark' in feedback_service.feedback_weights
    assert 'click' in feedback_service.feedback_weights
    
    print("✅ 피드백 가중치 설정 테스트 통과")

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

if __name__ == "__main__":
    test_feedback_weights_exist()
    test_feedback_distribution_analysis()
    test_interaction_quality_calculation()
    print("🎉 모든 간단한 피드백 테스트 통과!")