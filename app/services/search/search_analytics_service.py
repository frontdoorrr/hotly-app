"""
검색 분석 서비스 (Task 2-3-5)

검색 성능 분석, 사용자 행동 분석, 대시보드 데이터 제공 시스템
- 실시간 성능 모니터링
- 검색 트렌드 분석
- 사용자 참여도 측정
- A/B 테스트 결과 분석
- 이상 탐지 및 알림
"""

import json
import logging
import statistics
from datetime import datetime, timedelta
from typing import Any, Dict, List, Tuple
from uuid import UUID, uuid4

import redis.asyncio as redis
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class SearchAnalyticsService:
    """검색 분석 서비스"""

    def __init__(
        self,
        redis_client: redis.Redis,
        db_session: Session,
        enable_trend_analysis: bool = True,
        enable_ab_testing: bool = True,
        enable_anomaly_detection: bool = True,
        real_time_enabled: bool = True,
        retention_days: int = 90,
    ):
        self.redis = redis_client
        self.db = db_session
        self.trend_analysis = enable_trend_analysis
        self.ab_testing = enable_ab_testing
        self.anomaly_detection = enable_anomaly_detection
        self.real_time = real_time_enabled
        self.retention_days = retention_days

        # Redis 키 패턴
        self.performance_key = "search_analytics:performance:{date}"
        self.trend_key = "search_analytics:trends:{period}"
        self.engagement_key = "search_analytics:engagement:{date}"
        self.real_time_key = "search_analytics:realtime"

    async def record_search_performance(
        self,
        user_id: UUID,
        query: str,
        response_time_ms: float,
        cache_hit: bool,
        error_occurred: bool,
        result_count: int,
        personalization_applied: bool = False,
    ) -> bool:
        """검색 성능 데이터 기록"""
        try:
            timestamp = datetime.utcnow()
            date_key = timestamp.strftime("%Y-%m-%d")
            hour_key = timestamp.strftime("%Y-%m-%d-%H")

            # 성능 메트릭 구성
            performance_data = {
                "timestamp": timestamp.isoformat(),
                "user_id": str(user_id),
                "query": query,
                "response_time": response_time_ms,
                "cache_hit": cache_hit,
                "error": error_occurred,
                "result_count": result_count,
                "personalization": personalization_applied,
            }

            # 일별 성능 데이터 저장
            daily_key = self.performance_key.format(date=date_key)
            await self.redis.lpush(daily_key, json.dumps(performance_data))
            await self.redis.expire(daily_key, 86400 * self.retention_days)

            # 시간별 실시간 메트릭 업데이트
            if self.real_time:
                await self._update_real_time_metrics(hour_key, performance_data)

            return True

        except Exception as e:
            logger.error(f"Failed to record search performance: {str(e)}")
            return False

    async def get_performance_metrics(
        self, time_period_hours: int = 24
    ) -> Dict[str, Any]:
        """성능 메트릭 조회 및 계산"""
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=time_period_hours)

            # 기간 내 성능 데이터 수집
            performance_data = await self._collect_performance_data(
                start_time, end_time
            )

            if not performance_data:
                return {"message": "분석할 데이터가 없습니다"}

            # 메트릭 계산
            successful_searches = [
                item for item in performance_data if not item.get("error", False)
            ]

            metrics = {
                "total_searches": len(performance_data),
                "successful_searches": len(successful_searches),
                "error_rate": (len(performance_data) - len(successful_searches))
                / len(performance_data),
                "avg_response_time": statistics.mean(
                    [item["response_time"] for item in successful_searches]
                )
                if successful_searches
                else 0,
                "median_response_time": statistics.median(
                    [item["response_time"] for item in successful_searches]
                )
                if successful_searches
                else 0,
                "p95_response_time": self._calculate_percentile(
                    [item["response_time"] for item in successful_searches], 95
                )
                if successful_searches
                else 0,
                "cache_hit_rate": sum(
                    [1 for item in performance_data if item.get("cache_hit", False)]
                )
                / len(performance_data),
                "personalization_usage": sum(
                    [
                        1
                        for item in performance_data
                        if item.get("personalization", False)
                    ]
                )
                / len(performance_data),
                "searches_per_hour": len(performance_data) / time_period_hours,
                "unique_users": len(set(item["user_id"] for item in performance_data)),
            }

            # 성능 등급 계산
            metrics["performance_grade"] = self._calculate_performance_grade(metrics)

            return metrics

        except Exception as e:
            logger.error(f"Performance metrics calculation failed: {str(e)}")
            return {"error": str(e)}

    async def analyze_search_trends(
        self, period_days: int = 7, top_queries: int = 20
    ) -> List[Dict[str, Any]]:
        """검색 트렌드 분석"""
        try:
            if not self.trend_analysis:
                return []

            # 시계열 데이터 수집
            time_series_data = await self._get_search_time_series(period_days)

            trends = []
            for query, daily_counts in time_series_data.items():
                if len(daily_counts) < 2:
                    continue

                # 트렌드 분석
                trend_direction, trend_strength = self._calculate_trend(daily_counts)

                # 최근 검색량
                recent_volume = sum(daily_counts[-3:])  # 최근 3일
                total_volume = sum(daily_counts)

                trends.append(
                    {
                        "query": query,
                        "total_searches": total_volume,
                        "recent_volume": recent_volume,
                        "trend": trend_direction,
                        "trend_strength": trend_strength,
                        "growth_rate": self._calculate_growth_rate(daily_counts),
                        "volatility": self._calculate_volatility(daily_counts),
                    }
                )

            # 검색량 기준 정렬 후 상위 N개 반환
            trends.sort(key=lambda x: x["total_searches"], reverse=True)
            return trends[:top_queries]

        except Exception as e:
            logger.error(f"Trend analysis failed: {str(e)}")
            return []

    async def analyze_user_engagement(
        self, time_period_days: int = 7
    ) -> Dict[str, Any]:
        """사용자 참여도 분석"""
        try:
            engagement_data = await self._get_user_engagement_data(time_period_days)

            if not engagement_data:
                return {"message": "참여도 데이터가 없습니다"}

            # 참여도 메트릭 계산
            total_searches = sum(user["searches"] for user in engagement_data)
            total_clicks = sum(user["clicks"] for user in engagement_data)
            total_bookmarks = sum(user["bookmarks"] for user in engagement_data)
            total_visits = sum(user["visits"] for user in engagement_data)

            metrics = {
                "total_users": len(engagement_data),
                "avg_searches_per_user": total_searches / len(engagement_data),
                "avg_click_through_rate": total_clicks / total_searches
                if total_searches > 0
                else 0,
                "avg_conversion_rate": total_visits / total_searches
                if total_searches > 0
                else 0,
                "bookmark_rate": total_bookmarks / total_searches
                if total_searches > 0
                else 0,
                "avg_session_duration": statistics.mean(
                    [user["session_duration"] for user in engagement_data]
                ),
                "user_retention_rate": await self._calculate_user_retention(
                    time_period_days
                ),
                "engagement_score": self._calculate_engagement_score(engagement_data),
            }

            # 사용자 세그먼트 분석
            metrics["user_segments"] = self._analyze_user_segments(engagement_data)

            return metrics

        except Exception as e:
            logger.error(f"User engagement analysis failed: {str(e)}")
            return {"error": str(e)}

    async def analyze_search_quality(
        self, time_period_days: int = 30
    ) -> Dict[str, Any]:
        """검색 품질 분석"""
        try:
            quality_data = await self._get_search_quality_data(time_period_days)

            if not quality_data:
                return {"message": "품질 분석 데이터가 없습니다"}

            # 품질 메트릭 계산
            total_searches = len(quality_data)
            zero_results = sum(1 for item in quality_data if item["zero_results"])

            quality_metrics = {
                "total_searches": total_searches,
                "zero_results_rate": zero_results / total_searches,
                "avg_results_count": statistics.mean(
                    [
                        item["results_count"]
                        for item in quality_data
                        if not item["zero_results"]
                    ]
                )
                if any(not item["zero_results"] for item in quality_data)
                else 0,
                "avg_relevance_score": statistics.mean(
                    [item["relevance_score"] for item in quality_data]
                ),
                "user_satisfaction_score": statistics.mean(
                    [item["user_satisfaction"] for item in quality_data]
                ),
                "click_through_rate": self._calculate_quality_ctr(quality_data),
            }

            # 개선 제안 생성
            quality_metrics[
                "improvement_suggestions"
            ] = self._generate_quality_suggestions(quality_metrics, quality_data)

            # 품질 점수 계산
            quality_metrics[
                "overall_quality_score"
            ] = self._calculate_overall_quality_score(quality_metrics)

            return quality_metrics

        except Exception as e:
            logger.error(f"Search quality analysis failed: {str(e)}")
            return {"error": str(e)}

    async def analyze_personalization_effectiveness(
        self, experiment_id: str
    ) -> Dict[str, Any]:
        """개인화 효과 분석"""
        try:
            if not self.ab_testing:
                return {"message": "A/B 테스트가 비활성화되어 있습니다"}

            # A/B 테스트 데이터 수집
            ab_data = await self._get_ab_test_data(experiment_id)

            if not ab_data:
                return {"error": "실험 데이터를 찾을 수 없습니다"}

            personalized = ab_data["personalized_group"]
            control = ab_data["control_group"]

            # 효과 분석
            effectiveness = {
                "experiment_id": experiment_id,
                "control_group_size": control["users"],
                "personalized_group_size": personalized["users"],
                "click_rate_improvement": (
                    personalized["avg_click_rate"] - control["avg_click_rate"]
                )
                / control["avg_click_rate"],
                "conversion_rate_improvement": (
                    personalized["avg_conversion_rate"] - control["avg_conversion_rate"]
                )
                / control["avg_conversion_rate"],
                "engagement_improvement": (
                    personalized["avg_session_duration"]
                    - control["avg_session_duration"]
                )
                / control["avg_session_duration"],
                "satisfaction_improvement": (
                    personalized["user_satisfaction"] - control["user_satisfaction"]
                )
                / control["user_satisfaction"],
            }

            # 통계적 유의성 검증
            effectiveness[
                "statistical_significance"
            ] = self._calculate_statistical_significance(personalized, control)

            # 비즈니스 임팩트 계산
            effectiveness["business_impact"] = self._calculate_business_impact(
                personalized, control
            )

            return effectiveness

        except Exception as e:
            logger.error(f"Personalization analysis failed: {str(e)}")
            return {"error": str(e)}

    async def detect_search_anomalies(
        self, sensitivity: float = 0.05
    ) -> List[Dict[str, Any]]:
        """검색 이상 탐지"""
        try:
            if not self.anomaly_detection:
                return []

            # 최근 24시간 패턴 분석
            hourly_counts = await self._get_hourly_search_counts()

            if len(hourly_counts) < 24:
                return []

            anomalies = []

            # 통계적 이상값 탐지
            counts = [item["count"] for item in hourly_counts[:-1]]  # 현재 시간 제외
            mean_count = statistics.mean(counts)
            std_count = statistics.stdev(counts) if len(counts) > 1 else 0

            # Z-score 기반 이상 탐지
            threshold = 2.5  # 2.5 표준편차
            current_count = hourly_counts[-1]["count"]
            z_score = (
                abs(current_count - mean_count) / std_count if std_count > 0 else 0
            )

            if z_score > threshold:
                severity = "high" if z_score > 3.0 else "medium"
                anomaly_type = (
                    "sudden_spike" if current_count > mean_count else "sudden_drop"
                )

                anomalies.append(
                    {
                        "timestamp": hourly_counts[-1]["timestamp"],
                        "type": anomaly_type,
                        "severity": severity,
                        "count": current_count,
                        "expected_range": (
                            mean_count - std_count,
                            mean_count + std_count,
                        ),
                        "z_score": z_score,
                        "description": f"검색량이 평상시 대비 {abs(current_count - mean_count):.0f}건 {'증가' if current_count > mean_count else '감소'}했습니다",
                    }
                )

            # 패턴 기반 이상 탐지
            pattern_anomalies = await self._detect_pattern_anomalies(hourly_counts)
            anomalies.extend(pattern_anomalies)

            return anomalies

        except Exception as e:
            logger.error(f"Anomaly detection failed: {str(e)}")
            return []

    async def analyze_geographic_patterns(self) -> Dict[str, Any]:
        """지리적 검색 패턴 분석"""
        try:
            geo_data = await self._get_geographic_search_data()

            if not geo_data:
                return {"message": "지리적 데이터가 없습니다"}

            # 지역별 분석
            analysis = {
                "top_regions": sorted(
                    geo_data, key=lambda x: x["searches"], reverse=True
                )[:10],
                "regional_preferences": self._analyze_regional_preferences(geo_data),
                "geographic_trends": await self._analyze_geographic_trends(geo_data),
                "regional_diversity": self._calculate_regional_diversity(geo_data),
            }

            return analysis

        except Exception as e:
            logger.error(f"Geographic analysis failed: {str(e)}")
            return {"error": str(e)}

    async def get_real_time_dashboard(self) -> Dict[str, Any]:
        """실시간 대시보드 데이터"""
        try:
            if not self.real_time:
                return {"message": "실시간 기능이 비활성화되어 있습니다"}

            # 실시간 메트릭 조회
            real_time_data = await self.redis.get(self.real_time_key)

            if real_time_data:
                current_metrics = json.loads(real_time_data)
            else:
                current_metrics = await self._calculate_current_metrics()

            dashboard = {
                "current_metrics": current_metrics,
                "recent_activity": await self._get_recent_activity(),
                "live_trends": await self._get_live_trends(),
                "system_health": await self._get_system_health(),
                "active_experiments": await self._get_active_experiments()
                if self.ab_testing
                else [],
                "alerts": await self.detect_search_anomalies()
                if self.anomaly_detection
                else [],
                "last_updated": datetime.utcnow().isoformat(),
            }

            return dashboard

        except Exception as e:
            logger.error(f"Real-time dashboard failed: {str(e)}")
            return {"error": str(e)}

    async def analyze_conversion_funnel(
        self, time_period_days: int = 30
    ) -> Dict[str, Any]:
        """전환 퍼널 분석"""
        try:
            funnel_data = await self._get_conversion_funnel_data(time_period_days)

            if not funnel_data:
                return {"message": "퍼널 데이터가 없습니다"}

            # 전환율 계산
            searches = funnel_data["searches"]
            analysis = {
                "searches": searches,
                "clicks": funnel_data["clicks"],
                "detail_views": funnel_data["detail_views"],
                "bookmarks": funnel_data["bookmarks"],
                "visits": funnel_data["visits"],
                "search_to_click_rate": funnel_data["clicks"] / searches
                if searches > 0
                else 0,
                "click_to_view_rate": funnel_data["detail_views"]
                / funnel_data["clicks"]
                if funnel_data["clicks"] > 0
                else 0,
                "view_to_bookmark_rate": funnel_data["bookmarks"]
                / funnel_data["detail_views"]
                if funnel_data["detail_views"] > 0
                else 0,
                "bookmark_to_visit_rate": funnel_data["visits"]
                / funnel_data["bookmarks"]
                if funnel_data["bookmarks"] > 0
                else 0,
                "overall_conversion_rate": funnel_data["visits"] / searches
                if searches > 0
                else 0,
            }

            # 이탈 지점 분석
            analysis["drop_off_analysis"] = self._analyze_funnel_dropoffs(analysis)

            return analysis

        except Exception as e:
            logger.error(f"Conversion funnel analysis failed: {str(e)}")
            return {"error": str(e)}

    async def generate_analytics_report(
        self,
        start_date: datetime,
        end_date: datetime,
        include_trends: bool = True,
        include_user_segments: bool = True,
        format: str = "summary",
    ) -> Dict[str, Any]:
        """종합 분석 리포트 생성"""
        try:
            period_days = (end_date - start_date).days

            report = {
                "report_metadata": {
                    "generated_at": datetime.utcnow().isoformat(),
                    "period_start": start_date.isoformat(),
                    "period_end": end_date.isoformat(),
                    "period_days": period_days,
                    "format": format,
                },
                "executive_summary": await self._generate_executive_summary(
                    start_date, end_date
                ),
                "performance_metrics": await self.get_performance_metrics(
                    period_days * 24
                ),
                "user_engagement": await self.analyze_user_engagement(period_days),
                "search_quality": await self.analyze_search_quality(period_days),
            }

            if include_trends and self.trend_analysis:
                report["trend_analysis"] = await self.analyze_search_trends(period_days)

            if include_user_segments:
                report["user_segments"] = await self._analyze_detailed_user_segments(
                    period_days
                )

            # 추천사항 생성
            report["recommendations"] = self._generate_recommendations(report)

            return report

        except Exception as e:
            logger.error(f"Analytics report generation failed: {str(e)}")
            return {"error": str(e)}

    async def analyze_ab_test(self, experiment_id: str) -> Dict[str, Any]:
        """A/B 테스트 결과 분석"""
        try:
            if not self.ab_testing:
                return {"message": "A/B 테스트가 비활성화되어 있습니다"}

            experiment_data = await self._get_experiment_data(experiment_id)

            if not experiment_data:
                return {"error": "실험 데이터를 찾을 수 없습니다"}

            variant_a = experiment_data["variant_a"]
            variant_b = experiment_data["variant_b"]

            # 전환율 계산
            conversion_rate_a = variant_a["conversions"] / variant_a["users"]
            conversion_rate_b = variant_b["conversions"] / variant_b["users"]

            results = {
                "experiment_id": experiment_id,
                "variant_a_users": variant_a["users"],
                "variant_b_users": variant_b["users"],
                "conversion_rate_a": conversion_rate_a,
                "conversion_rate_b": conversion_rate_b,
                "relative_improvement": (conversion_rate_b - conversion_rate_a)
                / conversion_rate_a,
                "statistical_significance": self._calculate_ab_significance(
                    variant_a, variant_b
                ),
                "confidence_interval": self._calculate_confidence_interval(
                    variant_a, variant_b
                ),
                "sample_size_adequate": variant_a["users"] >= 100
                and variant_b["users"] >= 100,
            }

            # 추천사항
            if results["statistical_significance"] > 0.95:
                if results["relative_improvement"] > 0.05:  # 5% 이상 개선
                    results["recommendation"] = "Variant B를 채택하여 배포하세요"
                elif results["relative_improvement"] < -0.05:
                    results["recommendation"] = "Variant A를 유지하세요"
                else:
                    results["recommendation"] = "두 변형 간 유의미한 차이가 없습니다"
            else:
                results["recommendation"] = "더 많은 데이터 수집이 필요합니다"

            return results

        except Exception as e:
            logger.error(f"A/B test analysis failed: {str(e)}")
            return {"error": str(e)}

    # Private helper methods

    async def _collect_performance_data(
        self, start_time: datetime, end_time: datetime
    ) -> List[Dict[str, Any]]:
        """기간 내 성능 데이터 수집"""
        all_data = []
        current_date = start_time.date()
        end_date = end_time.date()

        while current_date <= end_date:
            date_key = current_date.strftime("%Y-%m-%d")
            daily_key = self.performance_key.format(date=date_key)

            daily_data = await self.redis.lrange(daily_key, 0, -1)

            for item_json in daily_data:
                try:
                    item = json.loads(item_json)
                    item_time = datetime.fromisoformat(item["timestamp"])

                    if start_time <= item_time <= end_time:
                        all_data.append(item)
                except json.JSONDecodeError:
                    continue

            current_date += timedelta(days=1)

        return all_data

    async def _update_real_time_metrics(
        self, hour_key: str, performance_data: Dict[str, Any]
    ) -> None:
        """실시간 메트릭 업데이트"""
        try:
            # 현재 시간의 메트릭 업데이트
            metrics_key = f"realtime_metrics:{hour_key}"

            # 기존 메트릭 조회
            existing_metrics = await self.redis.get(metrics_key)

            if existing_metrics:
                metrics = json.loads(existing_metrics)
            else:
                metrics = {
                    "searches": 0,
                    "total_response_time": 0,
                    "cache_hits": 0,
                    "errors": 0,
                    "users": set(),
                }

            # 메트릭 업데이트
            metrics["searches"] += 1
            if not performance_data["error"]:
                metrics["total_response_time"] += performance_data["response_time"]
            if performance_data["cache_hit"]:
                metrics["cache_hits"] += 1
            if performance_data["error"]:
                metrics["errors"] += 1

            # Set을 list로 변환하여 저장 (JSON 직렬화를 위해)
            if isinstance(metrics["users"], set):
                metrics["users"] = list(metrics["users"])
            metrics["users"].append(performance_data["user_id"])
            metrics["users"] = list(set(metrics["users"]))  # 중복 제거

            await self.redis.setex(metrics_key, 3600, json.dumps(metrics, default=str))

        except Exception as e:
            logger.error(f"Real-time metrics update failed: {str(e)}")

    def _calculate_percentile(self, data: List[float], percentile: float) -> float:
        """백분위수 계산"""
        if not data:
            return 0
        sorted_data = sorted(data)
        index = (percentile / 100) * (len(sorted_data) - 1)

        if index.is_integer():
            return sorted_data[int(index)]
        else:
            lower = sorted_data[int(index)]
            upper = sorted_data[int(index) + 1]
            return lower + (upper - lower) * (index - int(index))

    def _calculate_performance_grade(self, metrics: Dict[str, Any]) -> str:
        """성능 등급 계산"""
        score = (
            self._score_response_time(metrics["avg_response_time"])
            + self._score_error_rate(metrics["error_rate"])
            + self._score_cache_hit_rate(metrics["cache_hit_rate"])
            + self._score_p95_response_time(metrics["p95_response_time"])
        )

        return self._map_score_to_grade(score)

    def _score_response_time(self, avg_response_time: float) -> int:
        """응답시간 점수 계산"""
        if avg_response_time <= 200:
            return 30
        elif avg_response_time <= 500:
            return 20
        elif avg_response_time <= 1000:
            return 10
        return 0

    def _score_error_rate(self, error_rate: float) -> int:
        """에러율 점수 계산"""
        if error_rate <= 0.01:
            return 25
        elif error_rate <= 0.05:
            return 15
        elif error_rate <= 0.1:
            return 5
        return 0

    def _score_cache_hit_rate(self, cache_hit_rate: float) -> int:
        """캐시 히트율 점수 계산"""
        if cache_hit_rate >= 0.7:
            return 25
        elif cache_hit_rate >= 0.5:
            return 15
        elif cache_hit_rate >= 0.3:
            return 5
        return 0

    def _score_p95_response_time(self, p95_response_time: float) -> int:
        """P95 응답시간 점수 계산"""
        if p95_response_time <= 500:
            return 20
        elif p95_response_time <= 1000:
            return 10
        elif p95_response_time <= 2000:
            return 5
        return 0

    def _map_score_to_grade(self, score: int) -> str:
        """점수를 등급으로 변환"""
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"

    def _calculate_trend(self, daily_counts: List[int]) -> Tuple[str, float]:
        """트렌드 방향과 강도 계산"""
        if len(daily_counts) < 2:
            return "stable", 0.0

        # 단순 선형 회귀를 통한 기울기 계산
        n = len(daily_counts)
        x_mean = (n - 1) / 2
        y_mean = sum(daily_counts) / n

        numerator = sum(
            (i - x_mean) * (count - y_mean) for i, count in enumerate(daily_counts)
        )
        denominator = sum((i - x_mean) ** 2 for i in range(n))

        if denominator == 0:
            return "stable", 0.0

        slope = numerator / denominator

        # 트렌드 방향 결정
        if slope > 1:
            direction = "increasing"
        elif slope < -1:
            direction = "decreasing"
        else:
            direction = "stable"

        # 트렌드 강도 (0-1 사이로 정규화)
        strength = (
            min(abs(slope) / max(daily_counts), 1.0) if max(daily_counts) > 0 else 0.0
        )

        return direction, strength

    def _calculate_growth_rate(self, daily_counts: List[int]) -> float:
        """성장률 계산"""
        if len(daily_counts) < 2:
            return 0.0

        first_half = sum(daily_counts[: len(daily_counts) // 2])
        second_half = sum(daily_counts[len(daily_counts) // 2 :])

        if first_half == 0:
            return 0.0

        return (second_half - first_half) / first_half

    def _calculate_volatility(self, daily_counts: List[int]) -> float:
        """변동성 계산"""
        if len(daily_counts) < 2:
            return 0.0

        mean_count = sum(daily_counts) / len(daily_counts)
        variance = sum((count - mean_count) ** 2 for count in daily_counts) / len(
            daily_counts
        )

        return (variance**0.5) / mean_count if mean_count > 0 else 0.0

    # Mock data methods (실제 구현에서는 DB 쿼리로 대체)

    async def _get_search_time_series(self, days: int) -> Dict[str, List[int]]:
        """검색 시계열 데이터 조회 (Mock)"""
        return {
            "홍대 맛집": [15, 18, 22, 25, 28, 32, 35],
            "강남 카페": [20, 19, 21, 20, 22, 21, 20],
            "이태원 바": [30, 28, 25, 22, 20, 18, 15],
        }

    async def _get_user_engagement_data(self, days: int) -> List[Dict[str, Any]]:
        """사용자 참여도 데이터 조회 (Mock)"""
        return [
            {
                "user_id": str(uuid4()),
                "searches": 5,
                "clicks": 3,
                "bookmarks": 1,
                "visits": 1,
                "session_duration": 420,
            },
            {
                "user_id": str(uuid4()),
                "searches": 8,
                "clicks": 6,
                "bookmarks": 2,
                "visits": 2,
                "session_duration": 680,
            },
        ]

    async def _get_search_quality_data(self, days: int) -> List[Dict[str, Any]]:
        """검색 품질 데이터 조회 (Mock)"""
        return [
            {
                "query": "홍대 맛집",
                "results_count": 15,
                "clicks": 8,
                "zero_results": False,
                "user_satisfaction": 4.2,
                "relevance_score": 0.85,
            },
            {
                "query": "특이한 검색어",
                "results_count": 0,
                "clicks": 0,
                "zero_results": True,
                "user_satisfaction": 1.0,
                "relevance_score": 0.0,
            },
        ]

    async def _get_ab_test_data(self, experiment_id: str) -> Dict[str, Any]:
        """A/B 테스트 데이터 조회 (Mock)"""
        return {
            "personalized_group": {
                "users": 500,
                "avg_click_rate": 0.75,
                "avg_conversion_rate": 0.42,
                "avg_session_duration": 380,
                "user_satisfaction": 4.3,
            },
            "control_group": {
                "users": 500,
                "avg_click_rate": 0.58,
                "avg_conversion_rate": 0.31,
                "avg_session_duration": 290,
                "user_satisfaction": 3.8,
            },
        }

    async def _get_hourly_search_counts(self) -> List[Dict[str, Any]]:
        """시간별 검색 횟수 조회 (Mock)"""
        base_time = datetime.utcnow() - timedelta(hours=23)
        return [
            {
                "timestamp": (base_time + timedelta(hours=i)).isoformat(),
                "count": 50 + i * 2,
            }
            for i in range(24)
        ] + [
            {"timestamp": datetime.utcnow().isoformat(), "count": 500}
        ]  # 이상값

    async def _get_geographic_search_data(self) -> List[Dict[str, Any]]:
        """지역별 검색 데이터 조회 (Mock)"""
        return [
            {"region": "강남구", "searches": 350, "popular_category": "cafe"},
            {"region": "마포구", "searches": 280, "popular_category": "restaurant"},
            {"region": "종로구", "searches": 220, "popular_category": "culture"},
        ]

    async def _get_conversion_funnel_data(self, days: int) -> Dict[str, int]:
        """전환 퍼널 데이터 조회 (Mock)"""
        return {
            "searches": 1000,
            "clicks": 680,
            "detail_views": 420,
            "bookmarks": 250,
            "visits": 120,
        }

    async def _get_experiment_data(self, experiment_id: str) -> Dict[str, Any]:
        """실험 데이터 조회 (Mock)"""
        return {
            "experiment_id": experiment_id,
            "variant_a": {
                "users": 1000,
                "conversions": 180,
                "avg_engagement": 3.2,
                "revenue": 45000,
            },
            "variant_b": {
                "users": 1000,
                "conversions": 220,
                "avg_engagement": 3.8,
                "revenue": 55000,
            },
        }

    # Additional helper methods would be implemented here...
