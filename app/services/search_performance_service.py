"""
검색 성능 모니터링 서비스

이 서비스는 검색 성능 메트릭 수집, 분석, 알림 등의 기능을 제공합니다.
"""
import asyncio
import logging
import statistics
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from app.core.cache import CacheService
from app.schemas.search_optimization import (
    SearchPerformanceMetrics,
    SearchAnalytics,
    PerformanceAlert,
    SearchSessionInfo
)

logger = logging.getLogger(__name__)


class SearchPerformanceService:
    """검색 성능 모니터링 서비스"""
    
    def __init__(self, db, cache: CacheService):
        """
        성능 모니터링 서비스 초기화
        
        Args:
            db: 데이터베이스 세션
            cache: 캐시 서비스
        """
        self.db = db
        self.cache = cache
        
        # 성능 임계값 (기본값)
        self.performance_thresholds = {
            'max_response_time_ms': 2000,
            'min_cache_hit_rate': 0.3,
            'max_error_rate': 0.05,
            'max_database_query_time_ms': 500,
            'max_elasticsearch_query_time_ms': 1000
        }
        
        # 메트릭 수집 설정
        self.metrics_retention_days = 30
        self.alert_cooldown_minutes = 15
    
    async def start_search_session(
        self,
        user_id: UUID,
        query: str,
        timestamp: datetime
    ) -> str:
        """
        검색 세션 시작
        
        Args:
            user_id: 사용자 ID
            query: 검색 쿼리
            timestamp: 시작 시간
            
        Returns:
            세션 ID
        """
        try:
            session_id = str(uuid4())
            
            session_info = SearchSessionInfo(
                session_id=session_id,
                user_id=user_id,
                start_time=timestamp,
                query_count=1,
                last_activity=timestamp
            )
            
            # 세션 정보 캐싱
            session_key = f"search:session:{session_id}"
            await self.cache.set(
                session_key, 
                session_info.dict(), 
                ttl=3600  # 1시간
            )
            
            logger.info(f"Started search session: {session_id} for user: {user_id}")
            return session_id
            
        except Exception as e:
            logger.error(f"Failed to start search session: {e}")
            return str(uuid4())  # 기본 세션 ID 반환
    
    async def record_search_metrics(self, metrics: SearchPerformanceMetrics) -> bool:
        """
        검색 성능 메트릭 기록
        
        Args:
            metrics: 성능 메트릭
            
        Returns:
            기록 성공 여부
        """
        try:
            # 메트릭 검증
            if not self._validate_metrics(metrics):
                logger.warning(f"Invalid metrics received: {metrics.session_id}")
                return False
            
            # 메트릭 데이터 준비
            metrics_data = metrics.dict()
            
            # 캐시에 메트릭 저장 (실시간 조회용)
            metrics_key = f"search:metrics:{metrics.session_id}"
            await self.cache.set(metrics_key, metrics_data, ttl=86400)  # 24시간
            
            # 집계 데이터 업데이트
            await self._update_aggregated_metrics(metrics)
            
            # 성능 알림 확인
            alert_triggered = await self.check_performance_alert(metrics)
            if alert_triggered:
                logger.warning(f"Performance alert triggered for session: {metrics.session_id}")
            
            # 세션 정보 업데이트
            await self._update_session_info(metrics)
            
            logger.debug(f"Recorded search metrics for session: {metrics.session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to record search metrics: {e}")
            return False
    
    async def get_search_metrics(self, session_id: str) -> Optional[SearchPerformanceMetrics]:
        """
        검색 메트릭 조회
        
        Args:
            session_id: 세션 ID
            
        Returns:
            성능 메트릭 (없으면 None)
        """
        try:
            metrics_key = f"search:metrics:{session_id}"
            metrics_data = await self.cache.get(metrics_key)
            
            if metrics_data:
                return SearchPerformanceMetrics(**metrics_data)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get search metrics: {e}")
            return None
    
    async def analyze_search_performance(
        self,
        user_id: UUID,
        time_period: timedelta
    ) -> Dict[str, Any]:
        """
        검색 성능 분석
        
        Args:
            user_id: 사용자 ID
            time_period: 분석 기간
            
        Returns:
            성능 분석 결과
        """
        try:
            # 분석 기간 설정
            end_time = datetime.utcnow()
            start_time = end_time - time_period
            
            # 사용자별 메트릭 조회
            user_metrics = await self._get_user_metrics(user_id, start_time, end_time)
            
            if not user_metrics:
                return self._empty_analysis()
            
            # 기본 통계 계산
            response_times = [m.response_time_ms for m in user_metrics]
            cache_hits = sum(1 for m in user_metrics if m.cache_hit)
            errors = sum(1 for m in user_metrics if m.error_occurred)
            
            analysis = {
                'total_searches': len(user_metrics),
                'avg_response_time': statistics.mean(response_times),
                'median_response_time': statistics.median(response_times),
                'p95_response_time': self._percentile(response_times, 95),
                'cache_hit_rate': cache_hits / len(user_metrics),
                'error_rate': errors / len(user_metrics),
                'performance_trend': self._calculate_trend(response_times)
            }
            
            # 시간대별 분석
            analysis['hourly_stats'] = await self._analyze_hourly_performance(
                user_metrics
            )
            
            # 쿼리별 분석
            analysis.update(await self._analyze_query_performance(user_metrics))
            
            logger.info(f"Analyzed performance for user {user_id}: {analysis['total_searches']} searches")
            return analysis
            
        except Exception as e:
            logger.error(f"Performance analysis failed: {e}")
            return self._empty_analysis()
    
    async def check_performance_alert(self, metrics: SearchPerformanceMetrics) -> bool:
        """
        성능 알림 확인
        
        Args:
            metrics: 성능 메트릭
            
        Returns:
            알림 트리거 여부
        """
        try:
            alerts = []
            
            # 응답 시간 확인
            if metrics.response_time_ms > self.performance_thresholds['max_response_time_ms']:
                alerts.append({
                    'metric': 'response_time',
                    'threshold': self.performance_thresholds['max_response_time_ms'],
                    'actual': metrics.response_time_ms,
                    'severity': 'high' if metrics.response_time_ms > 5000 else 'medium'
                })
            
            # 데이터베이스 쿼리 시간 확인
            if (metrics.database_query_time_ms and 
                metrics.database_query_time_ms > self.performance_thresholds['max_database_query_time_ms']):
                alerts.append({
                    'metric': 'database_query_time',
                    'threshold': self.performance_thresholds['max_database_query_time_ms'],
                    'actual': metrics.database_query_time_ms,
                    'severity': 'medium'
                })
            
            # Elasticsearch 쿼리 시간 확인
            if (metrics.elasticsearch_query_time_ms and 
                metrics.elasticsearch_query_time_ms > self.performance_thresholds['max_elasticsearch_query_time_ms']):
                alerts.append({
                    'metric': 'elasticsearch_query_time',
                    'threshold': self.performance_thresholds['max_elasticsearch_query_time_ms'],
                    'actual': metrics.elasticsearch_query_time_ms,
                    'severity': 'medium'
                })
            
            # 오류 발생 확인
            if metrics.error_occurred:
                alerts.append({
                    'metric': 'error_occurred',
                    'threshold': 0,
                    'actual': 1,
                    'severity': 'high'
                })
            
            # 알림 기록
            for alert_data in alerts:
                await self._record_alert(metrics, alert_data)
            
            return len(alerts) > 0
            
        except Exception as e:
            logger.error(f"Performance alert check failed: {e}")
            return False
    
    async def set_performance_thresholds(self, thresholds: Dict[str, float]) -> bool:
        """
        성능 임계값 설정
        
        Args:
            thresholds: 성능 임계값 딕셔너리
            
        Returns:
            설정 성공 여부
        """
        try:
            # 임계값 검증
            valid_keys = set(self.performance_thresholds.keys())
            invalid_keys = set(thresholds.keys()) - valid_keys
            
            if invalid_keys:
                logger.warning(f"Invalid threshold keys: {invalid_keys}")
                return False
            
            # 임계값 업데이트
            self.performance_thresholds.update(thresholds)
            
            # 캐시에 저장
            thresholds_key = "search:performance:thresholds"
            await self.cache.set(thresholds_key, self.performance_thresholds, ttl=86400)
            
            logger.info(f"Updated performance thresholds: {thresholds}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to set performance thresholds: {e}")
            return False
    
    async def get_recent_alerts(self, time_period: timedelta) -> List[Dict[str, Any]]:
        """
        최근 알림 조회
        
        Args:
            time_period: 조회 기간
            
        Returns:
            알림 목록
        """
        try:
            alerts_key = "search:performance:alerts"
            all_alerts = await self.cache.get(alerts_key) or []
            
            # 기간 내 알림 필터링
            cutoff_time = datetime.utcnow() - time_period
            recent_alerts = [
                alert for alert in all_alerts
                if datetime.fromisoformat(alert['timestamp']) > cutoff_time
            ]
            
            # 최신순 정렬
            recent_alerts.sort(key=lambda x: x['timestamp'], reverse=True)
            
            return recent_alerts
            
        except Exception as e:
            logger.error(f"Failed to get recent alerts: {e}")
            return []

    
    async def generate_ui_optimization_report(
        self,
        user_id: UUID,
        time_period: timedelta
    ) -> Dict[str, Any]:
        """
        검색 UI 최적화 리포트 생성
        
        Args:
            user_id: 사용자 ID
            time_period: 분석 기간
            
        Returns:
            UI 최적화 리포트
        """
        try:
            end_time = datetime.utcnow()
            start_time = end_time - time_period
            
            # 사용자 메트릭 조회
            user_metrics = await self._get_user_metrics(user_id, start_time, end_time)
            
            if not user_metrics:
                return self._empty_ui_report(user_id, time_period.days)
            
            # 기본 성능 통계
            performance_stats = await self._calculate_detailed_performance_stats(user_metrics)
            
            # UI 상호작용 메트릭 계산
            ui_metrics = await self._calculate_ui_interaction_metrics(user_id, time_period)
            
            # 세션 분석
            session_analysis = await self._analyze_user_sessions(user_id, time_period)
            
            # 개선 추천 사항 생성
            recommendations = await self._generate_ui_recommendations(
                performance_stats, ui_metrics, session_analysis
            )
            
            report = {
                'user_id': str(user_id),
                'report_period': f"{time_period.days} days",
                'total_searches': len(user_metrics),
                'average_session_duration': session_analysis.get('avg_duration', 0),
                'bounce_rate': session_analysis.get('bounce_rate', 0),
                'conversion_rate': session_analysis.get('conversion_rate', 0),
                
                # UI 상호작용 메트릭
                'autocomplete_usage_rate': ui_metrics.get('autocomplete_usage_rate', 0),
                'infinite_scroll_usage_rate': ui_metrics.get('infinite_scroll_usage_rate', 0),
                'filter_usage_rate': ui_metrics.get('filter_usage_rate', 0),
                
                # 성능 메트릭
                'performance_stats': performance_stats,
                
                # 추천 사항
                'recommendations': recommendations,
                
                # 생성 시간
                'generated_at': end_time.isoformat()
            }
            
            # 리포트 캐싱 (6시간)
            report_key = f"search:ui_report:{user_id}:{time_period.days}d"
            await self.cache.set(report_key, report, ttl=21600)
            
            logger.info(f"Generated UI optimization report for user {user_id}")
            return report
            
        except Exception as e:
            logger.error(f"UI optimization report generation failed: {e}")
            return self._empty_ui_report(user_id, time_period.days)
    
    async def track_search_ab_test_metrics(
        self,
        user_id: UUID,
        variant: str,
        metrics: Dict[str, Any]
    ) -> bool:
        """
        A/B 테스트 메트릭 추적
        
        Args:
            user_id: 사용자 ID
            variant: A/B 테스트 변형
            metrics: 메트릭 데이터
            
        Returns:
            추적 성공 여부
        """
        try:
            # A/B 테스트 메트릭 데이터 준비
            ab_test_data = {
                'user_id': str(user_id),
                'variant': variant,
                'metrics': metrics,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # 일별 A/B 테스트 데이터에 추가
            date_key = datetime.utcnow().strftime("%Y-%m-%d")
            ab_test_key = f"search:ab_test:metrics:{date_key}"
            
            daily_ab_data = await self.cache.get(ab_test_key) or []
            daily_ab_data.append(ab_test_data)
            
            # 최대 10000개 항목 유지
            if len(daily_ab_data) > 10000:
                daily_ab_data = daily_ab_data[-10000:]
            
            await self.cache.set(ab_test_key, daily_ab_data, ttl=86400 * 30)  # 30일
            
            logger.debug(f"Tracked A/B test metrics for user {user_id}, variant {variant}")
            return True
            
        except Exception as e:
            logger.error(f"A/B test metrics tracking failed: {e}")
            return False
    
    async def analyze_search_heatmap(
        self,
        time_period: timedelta
    ) -> List[Dict[str, Any]]:
        """
        검색 히트맵 분석
        
        Args:
            time_period: 분석 기간
            
        Returns:
            히트맵 데이터
        """
        try:
            # 시간대별, 요일별 검색 패턴 분석
            heatmap_data = []
            
            # Mock 데이터 생성 (실제로는 데이터베이스에서 집계)
            for day_of_week in range(7):  # 월-일
                for hour in range(24):  # 0-23시
                    # 시간대별 검색 활동 시뮬레이션
                    base_activity = 50
                    if 9 <= hour <= 18:  # 주간 활동 증가
                        base_activity *= 1.5
                    if hour in [12, 18, 21]:  # 점심, 저녁, 밤 시간 피크
                        base_activity *= 1.3
                    if day_of_week >= 5:  # 주말 활동 감소
                        base_activity *= 0.7
                    
                    search_count = int(base_activity + (hour + day_of_week) % 20)
                    avg_response_time = 200 + (hour % 12) * 50
                    success_rate = 0.95 - (hour % 24) * 0.001
                    
                    heatmap_data.append({
                        'hour': hour,
                        'day_of_week': day_of_week,
                        'search_count': search_count,
                        'average_response_time': avg_response_time,
                        'success_rate': success_rate
                    })
            
            return heatmap_data
            
        except Exception as e:
            logger.error(f"Search heatmap analysis failed: {e}")
            return []
    
    async def detect_search_anomalies(
        self,
        time_period: timedelta
    ) -> List[Dict[str, Any]]:
        """
        검색 이상 징후 탐지
        
        Args:
            time_period: 분석 기간
            
        Returns:
            이상 징후 목록
        """
        try:
            anomalies = []
            
            # 응답 시간 이상 징후
            response_time_anomaly = await self._detect_response_time_anomaly()
            if response_time_anomaly:
                anomalies.append(response_time_anomaly)
            
            # 캐시 히트율 이상 징후
            cache_anomaly = await self._detect_cache_hit_anomaly()
            if cache_anomaly:
                anomalies.append(cache_anomaly)
            
            # 에러율 이상 징후
            error_rate_anomaly = await self._detect_error_rate_anomaly()
            if error_rate_anomaly:
                anomalies.append(error_rate_anomaly)
            
            # 검색량 이상 징후
            volume_anomaly = await self._detect_search_volume_anomaly()
            if volume_anomaly:
                anomalies.append(volume_anomaly)
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Search anomaly detection failed: {e}")
            return []
    
    async def get_search_trend_analysis(
        self,
        time_period: timedelta
    ) -> Dict[str, Any]:
        """
        검색 트렌드 분석
        
        Args:
            time_period: 분석 기간
            
        Returns:
            트렌드 분석 결과
        """
        try:
            # 인기 검색어 트렌드
            popular_key = "search:popular:queries"
            popular_queries = await self.cache.get(popular_key) or {}
            
            # 상위 20개 쿼리를 트렌드로 변환
            trending_queries = []
            for query, count in sorted(popular_queries.items(), key=lambda x: x[1], reverse=True)[:20]:
                # Mock 트렌드 계산 (실제로는 시계열 데이터 분석)
                trend = "rising" if count > 50 else "stable" if count > 20 else "falling"
                trending_queries.append({
                    'query': query,
                    'count': count,
                    'rank': len(trending_queries) + 1,
                    'trend': trend
                })
            
            # 계절성 패턴 (Mock 데이터)
            seasonal_patterns = {
                'hourly': [20, 15, 10, 8, 12, 25, 40, 60, 80, 75, 70, 85, 90, 80, 75, 70, 80, 95, 85, 70, 60, 45, 35, 25],
                'daily': [100, 120, 110, 130, 140, 180, 160],  # 월-일
                'monthly': [80, 85, 90, 95, 100, 105, 110, 108, 95, 90, 85, 120]  # 1-12월
            }
            
            # 사용자 행동 인사이트
            user_behavior_insights = [
                "오후 6-7시에 검색 활동이 가장 활발합니다",
                "주말에는 레저 관련 검색이 증가합니다",
                "모바일에서의 검색 비율이 75%를 차지합니다",
                "자동완성 기능 사용률이 65% 증가했습니다",
                "평균 세션당 검색 횟수는 3.2회입니다"
            ]
            
            trend_analysis = {
                'period': f"{time_period.days} days",
                'trending_queries': trending_queries[:10],
                'declining_queries': [q for q in trending_queries if q['trend'] == 'falling'][:5],
                'seasonal_patterns': seasonal_patterns,
                'user_behavior_insights': user_behavior_insights,
                'analysis_timestamp': datetime.utcnow().isoformat()
            }
            
            return trend_analysis
            
        except Exception as e:
            logger.error(f"Search trend analysis failed: {e}")
            return {
                'period': f"{time_period.days} days",
                'trending_queries': [],
                'declining_queries': [],
                'seasonal_patterns': {},
                'user_behavior_insights': []
            }
    
    async def calculate_search_quality_score(
        self,
        query: str,
        results: List[Dict[str, Any]],
        user_feedback: Optional[Dict[str, Any]] = None
    ) -> Dict[str, float]:
        """
        검색 품질 점수 계산
        
        Args:
            query: 검색 쿼리
            results: 검색 결과
            user_feedback: 사용자 피드백 (선택적)
            
        Returns:
            품질 점수 구성 요소
        """
        try:
            # 관련성 점수 (Mock 계산)
            relevance_score = min(1.0, len(results) / 20.0)  # 결과 수 기반
            if len(query.split()) > 1:  # 복합 쿼리
                relevance_score *= 1.1
            
            # 다양성 점수 (카테고리 다양성 기반)
            categories = set()
            for result in results[:10]:  # 상위 10개 결과만 고려
                category = result.get('category', 'unknown')
                categories.add(category)
            diversity_score = min(1.0, len(categories) / 5.0)
            
            # 신선도 점수 (결과의 최신성 기반)
            freshness_score = 0.8  # Mock 값
            if results:
                # 실제로는 결과의 업데이트 날짜 등을 고려
                recent_results = sum(1 for r in results if r.get('updated_recently', False))
                freshness_score = min(1.0, recent_results / len(results))
            
            # 사용자 피드백 반영
            feedback_adjustment = 1.0
            if user_feedback:
                rating = user_feedback.get('rating', 3)
                feedback_adjustment = rating / 5.0
            
            # 전체 점수 계산 (가중평균)
            weights = {'relevance': 0.4, 'diversity': 0.3, 'freshness': 0.3}
            
            weighted_scores = {
                'relevance': relevance_score * weights['relevance'],
                'diversity': diversity_score * weights['diversity'], 
                'freshness': freshness_score * weights['freshness']
            }
            
            overall_score = sum(weighted_scores.values()) * feedback_adjustment
            overall_score = min(1.0, max(0.0, overall_score))
            
            quality_score = {
                'relevance_score': relevance_score,
                'diversity_score': diversity_score,
                'freshness_score': freshness_score,
                'overall_score': overall_score,
                'factors': {
                    'result_count': len(results),
                    'category_diversity': len(categories),
                    'user_feedback_rating': user_feedback.get('rating') if user_feedback else None,
                    'query_complexity': len(query.split())
                }
            }
            
            return quality_score
            
        except Exception as e:
            logger.error(f"Search quality score calculation failed: {e}")
            return {
                'relevance_score': 0.0,
                'diversity_score': 0.0,
                'freshness_score': 0.0,
                'overall_score': 0.0,
                'factors': {}
            }
    
    # Private 헬퍼 메서드들 (UI 최적화 관련)
    
    def _empty_ui_report(self, user_id: UUID, days: int) -> Dict[str, Any]:
        """빈 UI 리포트"""
        return {
            'user_id': str(user_id),
            'report_period': f"{days} days",
            'total_searches': 0,
            'average_session_duration': 0,
            'bounce_rate': 0,
            'conversion_rate': 0,
            'autocomplete_usage_rate': 0,
            'infinite_scroll_usage_rate': 0,
            'filter_usage_rate': 0,
            'performance_stats': {
                'average_response_time': 0,
                'cache_hit_rate': 0,
                'error_rate': 0
            },
            'recommendations': ['데이터가 부족합니다. 더 많은 검색 활동이 필요합니다.']
        }
    
    async def _calculate_detailed_performance_stats(
        self,
        metrics: List[SearchPerformanceMetrics]
    ) -> Dict[str, float]:
        """상세 성능 통계 계산"""
        if not metrics:
            return {
                'average_response_time': 0,
                'p50_response_time': 0,
                'p90_response_time': 0,
                'p95_response_time': 0,
                'cache_hit_rate': 0,
                'total_searches': 0,
                'error_rate': 0
            }
        
        response_times = [m.response_time_ms for m in metrics]
        cache_hits = sum(1 for m in metrics if m.cache_hit)
        errors = sum(1 for m in metrics if m.error_occurred)
        
        return {
            'average_response_time': statistics.mean(response_times),
            'p50_response_time': self._percentile(response_times, 50),
            'p90_response_time': self._percentile(response_times, 90),
            'p95_response_time': self._percentile(response_times, 95),
            'cache_hit_rate': (cache_hits / len(metrics)) * 100,
            'total_searches': len(metrics),
            'error_rate': (errors / len(metrics)) * 100,
            'daily_stats': []  # 구현 필요시 추가
        }
    
    async def _calculate_ui_interaction_metrics(
        self,
        user_id: UUID,
        time_period: timedelta
    ) -> Dict[str, float]:
        """UI 상호작용 메트릭 계산"""
        # Mock 데이터 (실제로는 사용자별 UI 이벤트 데이터 분석)
        return {
            'autocomplete_usage_rate': 65.5,  # %
            'infinite_scroll_usage_rate': 25.0,  # %
            'filter_usage_rate': 40.2,  # %
            'search_history_usage_rate': 15.8,  # %
            'popular_queries_click_rate': 8.3  # %
        }
    
    async def _analyze_user_sessions(
        self,
        user_id: UUID,
        time_period: timedelta
    ) -> Dict[str, float]:
        """사용자 세션 분석"""
        # Mock 데이터 (실제로는 세션 데이터 분석)
        return {
            'avg_duration': 285.5,  # 초
            'bounce_rate': 23.4,  # %
            'conversion_rate': 12.8,  # %
            'avg_searches_per_session': 3.2,
            'avg_session_depth': 4.5  # 페이지뷰
        }
    
    async def _generate_ui_recommendations(
        self,
        performance_stats: Dict[str, float],
        ui_metrics: Dict[str, float],
        session_analysis: Dict[str, float]
    ) -> List[str]:
        """UI 개선 추천 사항 생성"""
        recommendations = []
        
        # 성능 기반 추천
        if performance_stats['average_response_time'] > 1000:
            recommendations.append("검색 응답 시간이 느립니다. 캐시 활용도를 높여보세요.")
        
        if performance_stats['cache_hit_rate'] < 30:
            recommendations.append("캐시 적중률이 낮습니다. 인기 검색어 미리 캐싱을 고려하세요.")
        
        if performance_stats['error_rate'] > 5:
            recommendations.append("오류율이 높습니다. 검색 쿼리 검증 로직을 강화하세요.")
        
        # UI 상호작용 기반 추천
        if ui_metrics['autocomplete_usage_rate'] < 50:
            recommendations.append("자동완성 기능의 사용률을 높이기 위해 응답 속도를 개선하세요.")
        
        if ui_metrics['filter_usage_rate'] < 30:
            recommendations.append("필터 기능의 접근성을 개선하여 사용률을 높이세요.")
        
        # 세션 분석 기반 추천
        if session_analysis['bounce_rate'] > 30:
            recommendations.append("이탈률이 높습니다. 초기 검색 결과의 관련성을 개선하세요.")
        
        if session_analysis['avg_searches_per_session'] < 2:
            recommendations.append("세션당 검색 수가 낮습니다. 연관 검색어 제안을 강화하세요.")
        
        # 기본 추천사항
        if not recommendations:
            recommendations.append("현재 검색 성능이 양호합니다. 지속적인 모니터링을 권장합니다.")
        
        return recommendations
    
    # 이상 징후 탐지 헬퍼 메서드들
    
    async def _detect_response_time_anomaly(self) -> Optional[Dict[str, Any]]:
        """응답 시간 이상 징후 탐지"""
        # Mock 구현
        current_avg = 1500  # ms
        baseline_avg = 800  # ms
        
        if current_avg > baseline_avg * 2:
            return {
                'type': 'response_time_spike',
                'severity': 'high',
                'current_value': current_avg,
                'baseline_value': baseline_avg,
                'message': f'응답 시간이 기준치({baseline_avg}ms)의 2배를 초과했습니다',
                'detected_at': datetime.utcnow().isoformat()
            }
        return None
    
    async def _detect_cache_hit_anomaly(self) -> Optional[Dict[str, Any]]:
        """캐시 히트율 이상 징후 탐지"""
        # Mock 구현
        current_rate = 0.15  # 15%
        baseline_rate = 0.60  # 60%
        
        if current_rate < baseline_rate * 0.5:
            return {
                'type': 'cache_hit_rate_drop',
                'severity': 'medium',
                'current_value': current_rate * 100,
                'baseline_value': baseline_rate * 100,
                'message': f'캐시 히트율이 기준치({baseline_rate*100:.1f}%)의 절반 이하로 떨어졌습니다',
                'detected_at': datetime.utcnow().isoformat()
            }
        return None
    
    async def _detect_error_rate_anomaly(self) -> Optional[Dict[str, Any]]:
        """에러율 이상 징후 탐지"""
        # Mock 구현  
        current_rate = 0.08  # 8%
        baseline_rate = 0.02  # 2%
        
        if current_rate > baseline_rate * 3:
            return {
                'type': 'error_rate_spike',
                'severity': 'high',
                'current_value': current_rate * 100,
                'baseline_value': baseline_rate * 100,
                'message': f'에러율이 기준치({baseline_rate*100:.1f}%)의 3배를 초과했습니다',
                'detected_at': datetime.utcnow().isoformat()
            }
        return None
    
    async def _detect_search_volume_anomaly(self) -> Optional[Dict[str, Any]]:
        """검색량 이상 징후 탐지"""
        # Mock 구현
        current_volume = 450  # 시간당 검색수
        baseline_volume = 800  # 평상시 시간당 검색수
        
        if current_volume < baseline_volume * 0.3:
            return {
                'type': 'search_volume_drop',
                'severity': 'medium',
                'current_value': current_volume,
                'baseline_value': baseline_volume,
                'message': f'검색량이 기준치({baseline_volume})의 30% 이하로 떨어졌습니다',
                'detected_at': datetime.utcnow().isoformat()
            }
        return None
    
    # Private 헬퍼 메서드들
    
    def _validate_metrics(self, metrics: SearchPerformanceMetrics) -> bool:
        """메트릭 검증"""
        if metrics.response_time_ms < 0:
            return False
        if metrics.result_count < 0:
            return False
        if not metrics.session_id or not metrics.query:
            return False
        return True
    
    async def _update_aggregated_metrics(self, metrics: SearchPerformanceMetrics) -> None:
        """집계 메트릭 업데이트"""
        try:
            # 일별 집계
            date_key = metrics.timestamp.strftime("%Y-%m-%d")
            daily_key = f"search:metrics:daily:{date_key}"
            
            daily_data = await self.cache.get(daily_key) or {
                'total_searches': 0,
                'total_response_time': 0.0,
                'cache_hits': 0,
                'errors': 0
            }
            
            daily_data['total_searches'] += 1
            daily_data['total_response_time'] += metrics.response_time_ms
            if metrics.cache_hit:
                daily_data['cache_hits'] += 1
            if metrics.error_occurred:
                daily_data['errors'] += 1
            
            await self.cache.set(daily_key, daily_data, ttl=86400 * 7)  # 7일
            
        except Exception as e:
            logger.error(f"Failed to update aggregated metrics: {e}")
    
    async def _update_session_info(self, metrics: SearchPerformanceMetrics) -> None:
        """세션 정보 업데이트"""
        try:
            session_key = f"search:session:{metrics.session_id}"
            session_data = await self.cache.get(session_key)
            
            if session_data:
                session_data['query_count'] += 1
                session_data['total_response_time'] += metrics.response_time_ms
                if metrics.cache_hit:
                    session_data['cache_hits'] += 1
                session_data['last_activity'] = metrics.timestamp.isoformat()
                
                await self.cache.set(session_key, session_data, ttl=3600)
                
        except Exception as e:
            logger.error(f"Failed to update session info: {e}")
    
    async def _get_user_metrics(
        self, 
        user_id: UUID, 
        start_time: datetime, 
        end_time: datetime
    ) -> List[SearchPerformanceMetrics]:
        """사용자 메트릭 조회 (Mock 구현)"""
        # 실제 구현에서는 데이터베이스에서 조회
        # 여기서는 테스트를 위한 Mock 데이터 생성
        mock_metrics = []
        
        for i in range(10):
            timestamp = start_time + timedelta(minutes=i * 5)
            if timestamp > end_time:
                break
                
            metrics = SearchPerformanceMetrics(
                session_id=f"session_{i}",
                query=f"테스트 쿼리 {i}",
                response_time_ms=100 + i * 20,
                result_count=15 + i,
                cache_hit=i % 2 == 0,
                user_id=user_id,
                timestamp=timestamp,
                error_occurred=i == 8  # 한 개 오류 시뮬레이션
            )
            mock_metrics.append(metrics)
        
        return mock_metrics
    
    def _empty_analysis(self) -> Dict[str, Any]:
        """빈 분석 결과"""
        return {
            'total_searches': 0,
            'avg_response_time': 0.0,
            'cache_hit_rate': 0.0,
            'error_rate': 0.0,
            'performance_trend': 'stable'
        }
    
    def _percentile(self, values: List[float], percentile: int) -> float:
        """백분위수 계산"""
        if not values:
            return 0.0
        sorted_values = sorted(values)
        index = int((percentile / 100) * len(sorted_values))
        return sorted_values[min(index, len(sorted_values) - 1)]
    
    def _calculate_trend(self, response_times: List[float]) -> str:
        """성능 트렌드 계산"""
        if len(response_times) < 5:
            return 'stable'
        
        # 최근 절반과 이전 절반 비교
        mid = len(response_times) // 2
        recent_avg = statistics.mean(response_times[mid:])
        earlier_avg = statistics.mean(response_times[:mid])
        
        if recent_avg > earlier_avg * 1.2:
            return 'declining'
        elif recent_avg < earlier_avg * 0.8:
            return 'improving'
        else:
            return 'stable'
    
    async def _analyze_hourly_performance(
        self, 
        metrics: List[SearchPerformanceMetrics]
    ) -> Dict[str, float]:
        """시간대별 성능 분석"""
        hourly_data = defaultdict(list)
        
        for metric in metrics:
            hour = metric.timestamp.hour
            hourly_data[hour].append(metric.response_time_ms)
        
        hourly_stats = {}
        for hour, times in hourly_data.items():
            hourly_stats[f"{hour:02d}:00"] = statistics.mean(times)
        
        return hourly_stats
    
    async def _analyze_query_performance(
        self, 
        metrics: List[SearchPerformanceMetrics]
    ) -> Dict[str, Any]:
        """쿼리별 성능 분석"""
        query_stats = defaultdict(list)
        
        for metric in metrics:
            query_stats[metric.query].append(metric.response_time_ms)
        
        # 인기 쿼리 (검색 횟수 기준)
        popular_queries = [
            {'query': query, 'count': len(times)}
            for query, times in query_stats.items()
        ]
        popular_queries.sort(key=lambda x: x['count'], reverse=True)
        
        # 느린 쿼리 (평균 응답시간 기준)
        slow_queries = [
            {'query': query, 'avg_time': statistics.mean(times)}
            for query, times in query_stats.items()
        ]
        slow_queries.sort(key=lambda x: x['avg_time'], reverse=True)
        
        return {
            'popular_queries': popular_queries[:10],
            'slow_queries': slow_queries[:10]
        }
    
    async def _record_alert(
        self, 
        metrics: SearchPerformanceMetrics, 
        alert_data: Dict[str, Any]
    ) -> None:
        """알림 기록"""
        try:
            alert = {
                'alert_id': str(uuid4()),
                'session_id': metrics.session_id,
                'user_id': str(metrics.user_id),
                'metric': alert_data['metric'],
                'threshold_value': alert_data['threshold'],
                'actual_value': alert_data['actual'],
                'severity': alert_data['severity'],
                'timestamp': metrics.timestamp.isoformat(),
                'resolved': False
            }
            
            # 알림 목록에 추가
            alerts_key = "search:performance:alerts"
            all_alerts = await self.cache.get(alerts_key) or []
            all_alerts.append(alert)
            
            # 최근 1000개 알림만 유지
            if len(all_alerts) > 1000:
                all_alerts = all_alerts[-1000:]
            
            await self.cache.set(alerts_key, all_alerts, ttl=86400 * 7)  # 7일
            
        except Exception as e:
            logger.error(f"Failed to record alert: {e}")