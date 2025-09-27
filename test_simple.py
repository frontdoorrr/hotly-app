"""
간단한 ML 엔진 테스트
"""
import asyncio
from app.services.ml_engine import get_ml_engine_sync

def test_ml_engine_basic():
    """ML 엔진 기본 기능 테스트"""
    # 동기식 ML 엔진 가져오기
    ml_engine = get_ml_engine_sync()
    
    # 기본 속성 확인
    assert ml_engine is not None
    assert hasattr(ml_engine, 'relevance_model')
    assert hasattr(ml_engine, 'personalization_model')
    assert ml_engine.is_trained == False  # 초기에는 훈련되지 않음
    
    print("✅ ML 엔진 기본 기능 테스트 통과")

def test_default_scores():
    """기본 점수 계산 테스트"""
    ml_engine = get_ml_engine_sync()
    
    # 테스트 특성 벡터
    feature_vectors = [
        {
            'rating': 4.5,
            'distance': 1000,
            'popularity': 80,
            'price_range': 2
        },
        {
            'rating': 3.0,
            'distance': 5000,
            'popularity': 20,
            'price_range': 4
        }
    ]
    
    # 기본 점수 계산 (모델이 훈련되지 않았을 때)
    scores = asyncio.run(ml_engine._get_default_scores(feature_vectors))
    
    assert len(scores) == 2
    assert all(0 <= score <= 1 for score in scores)
    assert scores[0] > scores[1]  # 첫 번째가 더 높은 점수여야 함
    
    print("✅ 기본 점수 계산 테스트 통과")

def test_feature_conversion():
    """특성 벡터 변환 테스트"""
    ml_engine = get_ml_engine_sync()
    
    feature_vectors = [
        {
            'rating': 4.5,
            'distance': 1000,
            'popularity': 80,
        }
    ]
    
    # 특성 배열로 변환
    features_array = ml_engine._convert_features_to_array(feature_vectors)
    
    assert features_array.shape == (1, 10)  # 1개 샘플, 10개 특성
    assert features_array[0][0] == 4.5  # rating
    assert features_array[0][1] == 1000  # distance
    
    print("✅ 특성 벡터 변환 테스트 통과")

if __name__ == "__main__":
    test_ml_engine_basic()
    test_default_scores() 
    test_feature_conversion()
    print("🎉 모든 테스트 통과!")