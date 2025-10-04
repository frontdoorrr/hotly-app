"""
점진적 로딩 서비스 (Task 2-3-5)

검색 결과의 점진적 로딩 및 성능 최적화 시스템
- 배치 기반 점진적 로딩
- 적응형 배치 크기 조정
- 예측 기반 미리 로딩
- 무한 스크롤 및 페이지네이션 지원
- 성능 최적화 및 메모리 효율성
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

import redis.asyncio as redis
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class ProgressiveLoadingService:
    """점진적 로딩 서비스"""

    def __init__(
        self,
        redis_client: redis.Redis,
        db_session: Session,
        initial_batch_size: int = 15,
        batch_size: int = 10,
        max_batch_size: int = 50,
        adaptive_batch_sizing: bool = True,
        enable_preloading: bool = True,
        compression_enabled: bool = True,
        parallel_loading: bool = False,
        caching_enabled: bool = True,
        pagination_enabled: bool = True,
        infinite_scroll: bool = True,
        scroll_threshold: float = 0.8,
        retry_enabled: bool = True,
        max_retries: int = 3,
        analytics_enabled: bool = True,
        concurrent_limit: int = 10,
        memory_efficient: bool = True,
        max_memory_mb: int = 200,
        personalization_enabled: bool = True,
        batch_ttl_seconds: int = 300,
    ):
        self.redis = redis_client
        self.db = db_session
        self.initial_batch_size = initial_batch_size
        self.batch_size = batch_size
        self.max_batch_size = max_batch_size
        self.adaptive_sizing = adaptive_batch_sizing
        self.preloading_enabled = enable_preloading
        self.compression = compression_enabled
        self.parallel_loading = parallel_loading
        self.caching_enabled = caching_enabled
        self.pagination_enabled = pagination_enabled
        self.infinite_scroll = infinite_scroll
        self.scroll_threshold = scroll_threshold
        self.retry_enabled = retry_enabled
        self.max_retries = max_retries
        self.analytics_enabled = analytics_enabled
        self.concurrent_limit = concurrent_limit
        self.memory_efficient = memory_efficient
        self.max_memory_mb = max_memory_mb
        self.personalization_enabled = personalization_enabled
        self.batch_ttl = batch_ttl_seconds

        # Redis 키 패턴
        self.batch_key_pattern = "progressive_loading:batch:{user_id}:{token}"
        self.session_key_pattern = "progressive_loading:session:{user_id}:{session_id}"
        self.analytics_key_pattern = "progressive_loading:analytics:{user_id}:{date}"

        # 동시성 제어
        self.active_loads = {}
        self.load_semaphore = asyncio.Semaphore(concurrent_limit)

    async def load_initial_results(
        self,
        user_id: UUID,
        search_params: Dict[str, Any],
        total_results: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """초기 검색 결과 로드"""
        try:
            start_time = time.time()

            # 적응형 초기 배치 크기 계산
            if self.adaptive_sizing:
                initial_size = await self.calculate_optimal_batch_size(
                    user_id, search_params.get("network_info", {}), "initial"
                )
            else:
                initial_size = self.initial_batch_size

            # 초기 배치 추출
            initial_batch = total_results[:initial_size]
            remaining_results = total_results[initial_size:]

            # 배치 토큰 생성
            batch_token = str(uuid4())

            # 나머지 결과 저장 (배치별로 분할)
            if remaining_results:
                await self._store_remaining_results(
                    user_id, batch_token, remaining_results, search_params
                )

            # 응답 구성
            response = {
                "results": initial_batch,
                "loading_metadata": {
                    "total_count": len(total_results),
                    "loaded_count": len(initial_batch),
                    "has_more": len(remaining_results) > 0,
                    "next_batch_token": batch_token if remaining_results else None,
                    "batch_size": initial_size,
                    "estimated_total_batches": self._calculate_total_batches(
                        len(total_results), initial_size
                    ),
                    "loading_strategy": "progressive",
                },
                "performance_metrics": {
                    "initial_load_time_ms": int((time.time() - start_time) * 1000),
                    "compression_applied": self.compression,
                    "cache_utilized": self.caching_enabled,
                },
            }

            # 분석 데이터 기록
            if self.analytics_enabled:
                await self._record_loading_analytics(
                    user_id, "initial_load", response["performance_metrics"]
                )

            # 미리 로딩 시작 (비동기)
            if self.preloading_enabled and remaining_results:
                asyncio.create_task(
                    self._start_preloading(user_id, batch_token, search_params)
                )

            return response

        except Exception as e:
            logger.error(f"Initial results loading failed: {str(e)}")
            return {
                "results": total_results[: self.initial_batch_size],
                "error": {"type": "loading_error", "message": str(e)},
            }

    async def load_next_batch(
        self,
        user_id: UUID,
        batch_token: str,
        batch_size: Optional[int] = None,
    ) -> Dict[str, Any]:
        """다음 배치 로드"""
        try:
            async with self.load_semaphore:  # 동시성 제어
                start_time = time.time()

                # 배치 크기 결정
                effective_batch_size = batch_size or self.batch_size

                if self.adaptive_sizing:
                    effective_batch_size = await self.calculate_optimal_batch_size(
                        user_id, {}, "batch"
                    )

                # 저장된 결과 조회
                batch_data = await self._get_stored_batch_data(user_id, batch_token)

                if not batch_data:
                    return {
                        "error": {
                            "type": "batch_not_found",
                            "message": "배치 데이터를 찾을 수 없습니다",
                            "retry_possible": False,
                        }
                    }

                # 다음 배치 추출
                remaining_results = batch_data["results"]
                current_batch = remaining_results[:effective_batch_size]
                updated_remaining = remaining_results[effective_batch_size:]

                # 진행 상황 계산
                total_count = batch_data["total_count"]
                loaded_count = batch_data.get("loaded_count", 0) + len(current_batch)

                # 업데이트된 데이터 저장
                if updated_remaining:
                    await self._update_stored_batch_data(
                        user_id, batch_token, updated_remaining, loaded_count
                    )
                else:
                    await self._cleanup_batch_data(user_id, batch_token)

                # 응답 구성
                response = {
                    "results": current_batch,
                    "loading_metadata": {
                        "total_count": total_count,
                        "loaded_count": loaded_count,
                        "has_more": len(updated_remaining) > 0,
                        "next_batch_token": batch_token if updated_remaining else None,
                        "batch_number": self._calculate_batch_number(
                            loaded_count, effective_batch_size
                        ),
                        "batch_size": effective_batch_size,
                        "progress_percentage": (loaded_count / total_count) * 100,
                    },
                    "performance_metrics": {
                        "batch_load_time_ms": int((time.time() - start_time) * 1000),
                        "cache_hit": batch_data.get("cached", False),
                    },
                }

                # 분석 데이터 기록
                if self.analytics_enabled:
                    await self._record_loading_analytics(
                        user_id, "batch_load", response["performance_metrics"]
                    )

                return response

        except Exception as e:
            logger.error(f"Next batch loading failed: {str(e)}")

            # 재시도 로직
            if self.retry_enabled:
                return await self._handle_loading_retry(
                    user_id, batch_token, batch_size, str(e)
                )

            return {
                "error": {
                    "type": "loading_error",
                    "message": str(e),
                    "retry_possible": self.retry_enabled,
                }
            }

    async def calculate_optimal_batch_size(
        self,
        user_id: UUID,
        network_info: Dict[str, Any],
        device_type: str = "unknown",
    ) -> int:
        """최적 배치 크기 계산"""
        try:
            base_size = self.batch_size
            multiplier = self._calculate_network_multiplier(network_info)
            multiplier *= self._calculate_device_multiplier(device_type)

            if self.personalization_enabled:
                multiplier = await self._apply_user_preferences(
                    user_id, base_size, multiplier
                )

            optimal_size = int(base_size * multiplier)
            return max(5, min(optimal_size, self.max_batch_size))

        except Exception as e:
            logger.warning(f"Batch size calculation failed: {str(e)}")
            return self.batch_size

    def _calculate_network_multiplier(self, network_info: Dict[str, Any]) -> float:
        """네트워크 기반 배치 크기 승수 계산"""
        connection_type = network_info.get("connection", "unknown")
        speed = network_info.get("speed", "medium")

        if connection_type == "wifi" and speed == "fast":
            return 2.0
        elif connection_type == "4g" and speed == "fast":
            return 1.5
        elif connection_type == "3g" or speed == "slow":
            return 0.5
        else:
            return 1.0

    def _calculate_device_multiplier(self, device_type: str) -> float:
        """디바이스 타입 기반 배치 크기 승수 계산"""
        device_multipliers = {"mobile": 0.8, "tablet": 1.2, "desktop": 1.5}
        return device_multipliers.get(device_type, 1.0)

    async def _apply_user_preferences(
        self, user_id: UUID, base_size: int, current_multiplier: float
    ) -> float:
        """사용자 선호도 기반 승수 조정"""
        user_preferences = await self._get_user_preferences(user_id)
        preferred_size = user_preferences.get("preferred_batch_size")

        if preferred_size:
            return preferred_size / base_size
        return current_multiplier

    async def preload_results(
        self,
        user_id: UUID,
        search_session_id: str,
        current_position: int,
    ) -> Dict[str, Any]:
        """예측 기반 미리 로딩"""
        try:
            if not self.preloading_enabled:
                return {"preloaded": False, "reason": "preloading_disabled"}

            # 사용자 패턴 분석
            user_patterns = await self._analyze_user_patterns(user_id)

            # 미리 로딩할 양 계산
            typical_view_count = user_patterns.get("typical_view_count", 20)
            current_position + self.batch_size

            if current_position >= typical_view_count * 0.7:  # 70% 지점
                preload_count = min(
                    self.batch_size * 2, typical_view_count - current_position
                )

                if preload_count > 0:
                    # 백그라운드에서 미리 로딩 수행
                    asyncio.create_task(
                        self._perform_background_preload(
                            user_id, search_session_id, preload_count
                        )
                    )

                    return {
                        "preloaded": True,
                        "preloaded_count": preload_count,
                        "strategy": "predictive",
                    }

            return {"preloaded": False, "reason": "not_needed"}

        except Exception as e:
            logger.error(f"Preloading failed: {str(e)}")
            return {"preloaded": False, "error": str(e)}

    async def load_optimized_batch(
        self,
        user_id: UUID,
        results: List[Dict[str, Any]],
        optimization_params: Dict[str, Any],
    ) -> Dict[str, Any]:
        """성능 최적화된 배치 로드"""
        try:
            start_time = time.time()

            # 압축 적용
            if self.compression:
                results = await self._apply_compression(results, optimization_params)

            # 병렬 처리 (필요시)
            if self.parallel_loading:
                results = await self._parallel_process_batch(
                    results, optimization_params
                )

            # 캐시 활용
            if self.caching_enabled:
                await self._cache_optimized_batch(user_id, results, optimization_params)

            loading_time_ms = int((time.time() - start_time) * 1000)

            return {
                "results": results,
                "performance_metrics": {
                    "loading_time_ms": loading_time_ms,
                    "compression_ratio": optimization_params.get(
                        "compression_ratio", 0
                    ),
                    "cache_utilization": optimization_params.get(
                        "cache_utilization", 0
                    ),
                    "parallel_workers": optimization_params.get("parallel_workers", 1),
                },
            }

        except Exception as e:
            logger.error(f"Optimized batch loading failed: {str(e)}")
            return {"results": results, "error": str(e)}

    async def load_page(
        self,
        user_id: UUID,
        search_session_id: str,
        page_number: int,
        page_size: int,
    ) -> Dict[str, Any]:
        """페이지네이션 기반 로드"""
        try:
            if not self.pagination_enabled:
                return {"error": "pagination_disabled"}

            # 세션 데이터 조회
            session_data = await self._get_session_data(user_id, search_session_id)

            if not session_data:
                return {"error": "session_not_found"}

            total_results = session_data["total_results"]
            total_count = len(total_results)

            # 페이지 계산
            start_index = (page_number - 1) * page_size
            end_index = start_index + page_size

            page_results = total_results[start_index:end_index]

            return {
                "results": page_results,
                "pagination_info": {
                    "current_page": page_number,
                    "page_size": page_size,
                    "total_results": total_count,
                    "total_pages": (total_count + page_size - 1) // page_size,
                    "has_next": end_index < total_count,
                    "has_previous": page_number > 1,
                },
            }

        except Exception as e:
            logger.error(f"Page loading failed: {str(e)}")
            return {"error": str(e)}

    async def handle_scroll_loading(
        self,
        user_id: UUID,
        search_session_id: str,
        current_position: int,
        scroll_direction: str,
        viewport_size: int,
    ) -> Dict[str, Any]:
        """스크롤 기반 로딩"""
        try:
            if not self.infinite_scroll:
                return {
                    "loading_triggered": False,
                    "reason": "infinite_scroll_disabled",
                }

            # 로딩 트리거 조건 확인
            trigger_position = current_position + viewport_size * self.scroll_threshold

            session_data = await self._get_session_data(user_id, search_session_id)
            if not session_data:
                return {"error": "session_not_found"}

            loaded_count = session_data.get("loaded_count", 0)

            if trigger_position >= loaded_count and scroll_direction == "down":
                # 추가 결과 로드
                additional_results = await self._load_additional_scroll_results(
                    user_id, search_session_id, self.batch_size
                )

                return {
                    "loading_triggered": True,
                    "new_results": additional_results,
                    "scroll_metadata": {
                        "next_position": loaded_count + len(additional_results),
                        "loading_direction": scroll_direction,
                        "viewport_optimized": True,
                    },
                }

            return {"loading_triggered": False, "reason": "threshold_not_reached"}

        except Exception as e:
            logger.error(f"Scroll loading failed: {str(e)}")
            return {"error": str(e)}

    async def load_with_analytics(
        self,
        user_id: UUID,
        search_params: Dict[str, Any],
        tracking_params: Dict[str, Any],
    ) -> Dict[str, Any]:
        """분석 데이터와 함께 로딩"""
        try:
            start_time = time.time()

            # 기본 로딩 수행
            results = await self._perform_tracked_loading(user_id, search_params)

            loading_time_ms = int((time.time() - start_time) * 1000)

            # 분석 데이터 구성
            analytics_data = {
                "loading_time_ms": loading_time_ms,
                "batch_performance": {
                    "avg_item_load_time": loading_time_ms / len(results)
                    if results
                    else 0,
                    "loading_efficiency_score": self._calculate_efficiency_score(
                        len(results), loading_time_ms
                    ),
                },
                "user_engagement_score": await self._calculate_engagement_score(
                    user_id, tracking_params
                ),
                "session_metadata": tracking_params,
            }

            # 분석 데이터 저장
            if self.analytics_enabled:
                await self._store_analytics_data(user_id, analytics_data)

            return {
                "results": results,
                "analytics": analytics_data,
            }

        except Exception as e:
            logger.error(f"Analytics loading failed: {str(e)}")
            return {"results": [], "error": str(e)}

    async def load_memory_optimized(
        self,
        user_id: UUID,
        large_dataset_size: int,
        memory_constraints: Dict[str, Any],
    ) -> Dict[str, Any]:
        """메모리 효율적 로딩"""
        try:
            if not self.memory_efficient:
                return {"error": "memory_optimization_disabled"}

            max_batch_memory = memory_constraints.get("max_batch_memory_mb", 10)
            streaming_enabled = memory_constraints.get("streaming_enabled", True)

            # 메모리 기반 배치 크기 계산
            memory_based_batch_size = self._calculate_memory_batch_size(
                max_batch_memory, large_dataset_size
            )

            # 스트리밍 방식으로 결과 로드
            if streaming_enabled:
                results = await self._stream_large_dataset(
                    user_id, large_dataset_size, memory_based_batch_size
                )
            else:
                results = await self._chunk_large_dataset(
                    user_id, large_dataset_size, memory_based_batch_size
                )

            # 메모리 사용량 모니터링
            memory_usage = await self._monitor_memory_usage()

            return {
                "results": results,
                "memory_usage": {
                    "peak_memory_mb": memory_usage["peak_mb"],
                    "current_memory_mb": memory_usage["current_mb"],
                    "streaming_active": streaming_enabled,
                    "batch_size_optimized": memory_based_batch_size,
                },
            }

        except Exception as e:
            logger.error(f"Memory optimized loading failed: {str(e)}")
            return {"error": str(e)}

    async def load_personalized_batch(
        self,
        user_id: UUID,
        search_session_id: str,
    ) -> Dict[str, Any]:
        """개인화된 로딩 전략"""
        try:
            if not self.personalization_enabled:
                return {"error": "personalization_disabled"}

            # 사용자 선호도 조회
            user_preferences = await self._get_user_preferences(user_id)

            # 개인화된 배치 크기
            personalized_batch_size = user_preferences.get(
                "preferred_batch_size", self.batch_size
            )

            # 로딩 전략 결정
            loading_patience = user_preferences.get("loading_patience", "medium")
            strategy = self._determine_loading_strategy(loading_patience)

            # 개인화된 결과 로드
            results = await self._load_with_strategy(
                user_id, search_session_id, personalized_batch_size, strategy
            )

            return {
                "results": results,
                "personalization_applied": {
                    "batch_size": personalized_batch_size,
                    "strategy": strategy,
                    "user_patience_level": loading_patience,
                },
            }

        except Exception as e:
            logger.error(f"Personalized loading failed: {str(e)}")
            return {"error": str(e)}

    # Private helper methods

    async def _store_remaining_results(
        self,
        user_id: UUID,
        batch_token: str,
        remaining_results: List[Dict[str, Any]],
        search_params: Dict[str, Any],
    ) -> None:
        """나머지 결과 저장"""
        try:
            batch_key = self.batch_key_pattern.format(
                user_id=user_id, token=batch_token
            )

            batch_data = {
                "results": remaining_results,
                "search_params": search_params,
                "total_count": len(remaining_results),
                "loaded_count": 0,
                "created_at": datetime.utcnow().isoformat(),
            }

            # 압축 적용 (대용량 데이터)
            if self.compression and len(remaining_results) > 100:
                batch_data = await self._compress_batch_data(batch_data)

            await self.redis.setex(
                batch_key, self.batch_ttl, json.dumps(batch_data, default=str)
            )

        except Exception as e:
            logger.error(f"Storing remaining results failed: {str(e)}")

    async def _get_stored_batch_data(
        self, user_id: UUID, batch_token: str
    ) -> Optional[Dict[str, Any]]:
        """저장된 배치 데이터 조회"""
        try:
            batch_key = self.batch_key_pattern.format(
                user_id=user_id, token=batch_token
            )
            batch_data = await self.redis.get(batch_key)

            if batch_data:
                data = json.loads(batch_data)

                # 압축 해제 (필요시)
                if data.get("compressed"):
                    data = await self._decompress_batch_data(data)

                return data

            return None

        except Exception as e:
            logger.error(f"Getting stored batch data failed: {str(e)}")
            return None

    async def _update_stored_batch_data(
        self,
        user_id: UUID,
        batch_token: str,
        updated_results: List[Dict[str, Any]],
        loaded_count: int,
    ) -> None:
        """저장된 배치 데이터 업데이트"""
        try:
            batch_key = self.batch_key_pattern.format(
                user_id=user_id, token=batch_token
            )

            updated_data = {
                "results": updated_results,
                "loaded_count": loaded_count,
                "updated_at": datetime.utcnow().isoformat(),
            }

            await self.redis.setex(
                batch_key, self.batch_ttl, json.dumps(updated_data, default=str)
            )

        except Exception as e:
            logger.error(f"Updating stored batch data failed: {str(e)}")

    async def _cleanup_batch_data(self, user_id: UUID, batch_token: str) -> None:
        """배치 데이터 정리"""
        try:
            batch_key = self.batch_key_pattern.format(
                user_id=user_id, token=batch_token
            )
            await self.redis.delete(batch_key)
        except Exception as e:
            logger.error(f"Batch data cleanup failed: {str(e)}")

    def _calculate_total_batches(self, total_count: int, batch_size: int) -> int:
        """전체 배치 수 계산"""
        return (total_count + batch_size - 1) // batch_size

    def _calculate_batch_number(self, loaded_count: int, batch_size: int) -> int:
        """현재 배치 번호 계산"""
        return (loaded_count + batch_size - 1) // batch_size

    async def _record_loading_analytics(
        self, user_id: UUID, event_type: str, metrics: Dict[str, Any]
    ) -> None:
        """로딩 분석 데이터 기록"""
        try:
            if not self.analytics_enabled:
                return

            analytics_key = self.analytics_key_pattern.format(
                user_id=user_id, date=datetime.utcnow().strftime("%Y-%m-%d")
            )

            analytics_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "event_type": event_type,
                "metrics": metrics,
            }

            await self.redis.lpush(analytics_key, json.dumps(analytics_entry))
            await self.redis.expire(analytics_key, 86400 * 7)  # 7일 보관

        except Exception as e:
            logger.error(f"Recording analytics failed: {str(e)}")

    async def _start_preloading(
        self, user_id: UUID, batch_token: str, search_params: Dict[str, Any]
    ) -> None:
        """미리 로딩 시작"""
        try:
            # 백그라운드에서 다음 1-2 배치를 미리 준비
            await asyncio.sleep(0.5)  # 초기 로딩 후 잠시 대기

            # 실제로는 사용자 패턴을 분석하여 필요한만큼 미리 로딩
            logger.debug(f"Started preloading for user {user_id}, token {batch_token}")

        except Exception as e:
            logger.error(f"Preloading start failed: {str(e)}")

    async def _handle_loading_retry(
        self, user_id: UUID, batch_token: str, batch_size: Optional[int], error: str
    ) -> Dict[str, Any]:
        """로딩 재시도 처리"""
        try:
            # 재시도 로직 구현
            for attempt in range(self.max_retries):
                try:
                    await asyncio.sleep(0.5 * (attempt + 1))  # 점진적 백오프
                    return await self.load_next_batch(user_id, batch_token, batch_size)
                except Exception as retry_error:
                    logger.debug(f"Retry {attempt + 1} failed: {str(retry_error)}")
                    continue

            # 모든 재시도 실패
            return {
                "error": {
                    "type": "retry_exhausted",
                    "message": f"재시도 {self.max_retries}회 실패: {error}",
                    "retry_possible": False,
                },
                "fallback_results": [],
            }

        except Exception as e:
            logger.error(f"Retry handling failed: {str(e)}")
            return {"error": {"type": "retry_handler_error", "message": str(e)}}

    # Mock implementation methods (실제 구현에서는 구체적인 로직 적용)

    async def _analyze_user_patterns(self, user_id: UUID) -> Dict[str, Any]:
        """사용자 패턴 분석 (Mock)"""
        return {
            "typical_view_count": 25,
            "scroll_speed": "medium",
            "preferred_categories": ["restaurant", "cafe"],
        }

    async def _get_user_preferences(self, user_id: UUID) -> Dict[str, Any]:
        """사용자 선호도 조회 (Mock)"""
        return {
            "preferred_batch_size": 12,
            "loading_patience": "high",
            "data_usage_concern": "low",
            "device_performance": "high",
        }

    async def _apply_compression(
        self, results: List[Dict[str, Any]], params: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """데이터 압축 적용 (Mock)"""
        # 실제로는 gzip 등을 사용하여 압축
        params["compression_ratio"] = 0.3
        return results

    async def _parallel_process_batch(
        self, results: List[Dict[str, Any]], params: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """병렬 처리 (Mock)"""
        # 실제로는 여러 워커로 배치 처리
        return results

    async def _cache_optimized_batch(
        self, user_id: UUID, results: List[Dict[str, Any]], params: Dict[str, Any]
    ) -> None:
        """최적화된 배치 캐싱 (Mock)"""
        params["cache_utilization"] = 0.8

    def _calculate_efficiency_score(
        self, result_count: int, loading_time_ms: int
    ) -> float:
        """효율성 점수 계산 (Mock)"""
        if loading_time_ms == 0:
            return 1.0
        return min(result_count / (loading_time_ms / 1000), 1.0)

    async def _calculate_engagement_score(
        self, user_id: UUID, tracking_params: Dict[str, Any]
    ) -> float:
        """사용자 참여도 점수 계산 (Mock)"""
        return 0.75

    async def _store_analytics_data(
        self, user_id: UUID, analytics_data: Dict[str, Any]
    ) -> None:
        """분석 데이터 저장 (Mock)"""

    def _calculate_memory_batch_size(
        self, max_memory_mb: int, dataset_size: int
    ) -> int:
        """메모리 기반 배치 크기 계산 (Mock)"""
        return min(max_memory_mb * 10, self.batch_size)

    async def _stream_large_dataset(
        self, user_id: UUID, dataset_size: int, batch_size: int
    ) -> List[Dict[str, Any]]:
        """대용량 데이터 스트리밍 (Mock)"""
        return [
            {"id": f"item_{i}", "data": f"stream_data_{i}"} for i in range(batch_size)
        ]

    async def _monitor_memory_usage(self) -> Dict[str, Any]:
        """메모리 사용량 모니터링 (Mock)"""
        return {"peak_mb": 50, "current_mb": 30}

    def _determine_loading_strategy(self, patience_level: str) -> str:
        """로딩 전략 결정 (Mock)"""
        strategy_map = {
            "low": "fast_small_batches",
            "medium": "balanced",
            "high": "high_patience",
        }
        return strategy_map.get(patience_level, "balanced")

    async def _load_with_strategy(
        self, user_id: UUID, session_id: str, batch_size: int, strategy: str
    ) -> List[Dict[str, Any]]:
        """전략 기반 로딩 (Mock)"""
        return [{"id": f"result_{i}", "strategy": strategy} for i in range(batch_size)]


# 의존성 주입용 팩토리 함수
def get_progressive_loading_service(
    redis_client: redis.Redis, db_session: Session
) -> ProgressiveLoadingService:
    """점진적 로딩 서비스 의존성"""
    return ProgressiveLoadingService(redis_client, db_session)
