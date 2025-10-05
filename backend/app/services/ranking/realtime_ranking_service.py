"""
실시간 랭킹 업데이트 서비스 (Task 2-3-4)

실시간으로 사용자 행동과 컨텍스트 변화를 감지하여 검색 랭킹을 동적으로 업데이트
- 실시간 사용자 행동 추적
- 컨텍스트 변화 감지 (위치, 시간, 날씨 등)
- 인기도 실시간 업데이트
- 랭킹 무효화 및 재계산 트리거
- WebSocket을 통한 실시간 알림
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import UUID

from fastapi import WebSocket

from app.core.cache import CacheService
from app.services.ml.ml_engine import MLEngine
from app.services.search.search_ranking_service import SearchRankingService

logger = logging.getLogger(__name__)


class RealtimeRankingService:
    """실시간 랭킹 업데이트 서비스"""

    def __init__(
        self,
        cache_service: CacheService,
        ml_engine: MLEngine,
        ranking_service: SearchRankingService,
    ):
        """서비스 초기화"""
        self.cache = cache_service
        self.ml_engine = ml_engine
        self.ranking_service = ranking_service

        # 활성 WebSocket 연결 관리
        self.active_connections: Dict[str, WebSocket] = {}

        # 실시간 업데이트 설정
        self.update_intervals = {
            "popularity": 60,  # 인기도 업데이트 (1분)
            "trends": 300,  # 트렌드 업데이트 (5분)
            "context": 30,  # 컨텍스트 업데이트 (30초)
            "user_activity": 10,  # 사용자 활동 업데이트 (10초)
        }

        # 업데이트 임계값
        self.update_thresholds = {
            "location_change_km": 1.0,  # 위치 변화 임계값 (1km)
            "time_change_hours": 1.0,  # 시간 변화 임계값 (1시간)
            "popularity_change_percent": 0.1,  # 인기도 변화 임계값 (10%)
            "trend_score_change": 0.15,  # 트렌드 점수 변화 임계값
        }

        # 배경 작업 상태
        self._background_tasks: Set[asyncio.Task] = set()
        self._is_running = False

    async def start_realtime_updates(self):
        """실시간 업데이트 시작"""
        if self._is_running:
            logger.warning("Realtime updates already running")
            return

        self._is_running = True

        # 배경 작업들 시작
        tasks = [
            self._popularity_updater(),
            self._trend_updater(),
            self._context_monitor(),
            self._user_activity_monitor(),
        ]

        for task_coro in tasks:
            task = asyncio.create_task(task_coro)
            self._background_tasks.add(task)
            task.add_done_callback(self._background_tasks.discard)

        logger.info("Realtime ranking updates started")

    async def stop_realtime_updates(self):
        """실시간 업데이트 중지"""
        self._is_running = False

        # 배경 작업들 취소
        for task in self._background_tasks:
            task.cancel()

        if self._background_tasks:
            await asyncio.gather(*self._background_tasks, return_exceptions=True)

        self._background_tasks.clear()

        logger.info("Realtime ranking updates stopped")

    async def register_websocket(self, websocket: WebSocket, user_id: str):
        """WebSocket 연결 등록"""
        await websocket.accept()
        self.active_connections[user_id] = websocket

        logger.info(f"WebSocket connection registered for user {user_id}")

        try:
            # 초기 상태 전송
            await self._send_initial_state(websocket, user_id)

            # 연결 유지 및 메시지 처리
            while True:
                try:
                    data = await websocket.receive_text()
                    await self._handle_websocket_message(user_id, json.loads(data))
                except Exception as e:
                    logger.error(
                        f"WebSocket message handling error for user {user_id}: {e}"
                    )
                    break

        except Exception as e:
            logger.error(f"WebSocket error for user {user_id}: {e}")
        finally:
            if user_id in self.active_connections:
                del self.active_connections[user_id]
            logger.info(f"WebSocket connection closed for user {user_id}")

    async def trigger_ranking_update(
        self,
        user_id: UUID,
        trigger_type: str,
        context: Optional[Dict[str, Any]] = None,
        force: bool = False,
    ) -> bool:
        """
        랭킹 업데이트 트리거

        Args:
            user_id: 사용자 ID
            trigger_type: 트리거 타입 (location, time, activity, etc.)
            context: 컨텍스트 정보
            force: 강제 업데이트 여부

        Returns:
            업데이트 수행 여부
        """
        try:
            # 업데이트 필요 여부 확인
            if not force and not await self._should_update_ranking(
                user_id, trigger_type, context
            ):
                return False

            # 사용자의 현재 검색 세션 확인
            active_searches = await self._get_active_searches(user_id)

            if not active_searches:
                return False

            # 각 활성 검색에 대해 랭킹 업데이트
            updated_count = 0
            for search_session in active_searches:
                updated = await self._update_search_ranking(
                    user_id, search_session, trigger_type, context
                )
                if updated:
                    updated_count += 1

            # WebSocket으로 업데이트 알림
            if updated_count > 0:
                await self._notify_ranking_update(user_id, trigger_type, updated_count)

            logger.info(
                f"Triggered ranking update for user {user_id}: "
                f"type={trigger_type}, updated={updated_count}"
            )

            return updated_count > 0

        except Exception as e:
            logger.error(f"Failed to trigger ranking update: {e}")
            return False

    async def update_popularity_scores(self, place_ids: List[UUID]) -> bool:
        """장소 인기도 점수 실시간 업데이트"""
        try:
            popularity_updates = {}

            for place_id in place_ids:
                # 최근 활동 데이터 수집
                recent_activity = await self._collect_recent_activity(place_id)

                # 인기도 점수 계산
                new_popularity = self._calculate_popularity_score(recent_activity)

                # 기존 점수와 비교
                current_popularity = await self._get_current_popularity(place_id)

                if self._should_update_popularity(current_popularity, new_popularity):
                    popularity_updates[str(place_id)] = new_popularity

            if popularity_updates:
                # 캐시 업데이트
                await self._update_popularity_cache(popularity_updates)

                # 영향받는 사용자들에게 알림
                await self._notify_popularity_changes(popularity_updates)

                logger.info(
                    f"Updated popularity scores for {len(popularity_updates)} places"
                )

            return len(popularity_updates) > 0

        except Exception as e:
            logger.error(f"Failed to update popularity scores: {e}")
            return False

    async def detect_trending_places(self) -> List[Dict[str, Any]]:
        """트렌딩 장소 감지"""
        try:
            # 최근 활동 데이터 분석
            recent_window = datetime.utcnow() - timedelta(hours=6)
            trend_data = await self._analyze_trending_activity(recent_window)

            # 트렌드 점수 계산
            trending_places = []
            for place_data in trend_data:
                trend_score = self._calculate_trend_score(place_data)

                if trend_score > 0.7:  # 트렌드 임계값
                    trending_places.append(
                        {
                            "place_id": place_data["place_id"],
                            "trend_score": trend_score,
                            "activity_increase": place_data["activity_increase"],
                            "detected_at": datetime.utcnow().isoformat(),
                        }
                    )

            # 트렌드 정보 캐시 업데이트
            if trending_places:
                await self.cache.set(
                    "trending_places",
                    trending_places,
                    ttl=self.update_intervals["trends"],
                )

                # 사용자들에게 트렌드 알림
                await self._notify_trending_places(trending_places)

            logger.info(f"Detected {len(trending_places)} trending places")

            return trending_places

        except Exception as e:
            logger.error(f"Failed to detect trending places: {e}")
            return []

    async def _popularity_updater(self):
        """인기도 업데이트 배경 작업"""
        while self._is_running:
            try:
                # 최근 활발한 장소들 식별
                active_places = await self._get_recently_active_places()

                if active_places:
                    await self.update_popularity_scores(active_places)

                await asyncio.sleep(self.update_intervals["popularity"])

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Popularity updater error: {e}")
                await asyncio.sleep(30)  # 에러 시 짧은 대기

    async def _trend_updater(self):
        """트렌드 업데이트 배경 작업"""
        while self._is_running:
            try:
                await self.detect_trending_places()
                await asyncio.sleep(self.update_intervals["trends"])

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Trend updater error: {e}")
                await asyncio.sleep(60)

    async def _context_monitor(self):
        """컨텍스트 변화 모니터링 배경 작업"""
        while self._is_running:
            try:
                # 활성 사용자들의 컨텍스트 변화 감지
                active_users = list(self.active_connections.keys())

                for user_id in active_users:
                    await self._monitor_user_context(UUID(user_id))

                await asyncio.sleep(self.update_intervals["context"])

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Context monitor error: {e}")
                await asyncio.sleep(30)

    async def _user_activity_monitor(self):
        """사용자 활동 모니터링 배경 작업"""
        while self._is_running:
            try:
                # 사용자 활동 패턴 분석 및 업데이트 트리거
                activity_changes = await self._detect_activity_changes()

                for user_id, change_type in activity_changes:
                    await self.trigger_ranking_update(
                        user_id, "activity_change", {"change_type": change_type}
                    )

                await asyncio.sleep(self.update_intervals["user_activity"])

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"User activity monitor error: {e}")
                await asyncio.sleep(15)

    async def _should_update_ranking(
        self, user_id: UUID, trigger_type: str, context: Optional[Dict[str, Any]]
    ) -> bool:
        """랭킹 업데이트 필요 여부 확인"""
        try:
            # 마지막 업데이트 시간 확인
            last_update_key = f"last_ranking_update:{user_id}"
            last_update = await self.cache.get(last_update_key)

            if last_update:
                last_update_time = datetime.fromisoformat(last_update)
                time_since_update = datetime.utcnow() - last_update_time

                # 최소 업데이트 간격 확인 (너무 빈번한 업데이트 방지)
                if time_since_update.total_seconds() < 30:  # 30초 최소 간격
                    return False

            # 트리거 타입별 조건 확인
            if trigger_type == "location":
                return await self._check_location_change_threshold(user_id, context)
            elif trigger_type == "time":
                return await self._check_time_change_threshold(user_id, context)
            elif trigger_type == "popularity":
                return await self._check_popularity_change_threshold(context)
            elif trigger_type == "activity_change":
                return True  # 활동 변화는 항상 업데이트

            return True

        except Exception as e:
            logger.error(f"Failed to check update necessity: {e}")
            return False

    async def _get_active_searches(self, user_id: UUID) -> List[Dict[str, Any]]:
        """사용자의 활성 검색 세션 조회"""
        try:
            cache_key = f"active_searches:{user_id}"
            active_searches = await self.cache.get(cache_key) or []

            # 만료된 검색 세션 제거
            current_time = datetime.utcnow()
            valid_searches = []

            for search in active_searches:
                try:
                    created_at = datetime.fromisoformat(search["created_at"])
                    if (current_time - created_at).total_seconds() < 3600:  # 1시간 유효
                        valid_searches.append(search)
                except Exception:
                    continue

            # 유효한 검색만 캐시에 다시 저장
            if len(valid_searches) != len(active_searches):
                await self.cache.set(cache_key, valid_searches, ttl=3600)

            return valid_searches

        except Exception as e:
            logger.error(f"Failed to get active searches: {e}")
            return []

    async def _update_search_ranking(
        self,
        user_id: UUID,
        search_session: Dict[str, Any],
        trigger_type: str,
        context: Optional[Dict[str, Any]],
    ) -> bool:
        """특정 검색 세션의 랭킹 업데이트"""
        try:
            # 검색 결과 재랭킹
            search_results = search_session.get("results", [])
            if not search_results:
                return False

            # 새로운 컨텍스트로 랭킹 재계산
            updated_context = search_session.get("context", {})
            if context:
                updated_context.update(context)

            # 랭킹 서비스를 통해 재계산
            new_ranking = await self.ranking_service.rank_search_results(
                user_id=user_id,
                search_results=search_results,
                query=search_session.get("query"),
                context=updated_context,
                personalization_strength=0.7,
            )

            # 랭킹이 실제로 변경되었는지 확인
            if self._has_ranking_changed(search_results, new_ranking):
                # 새 랭킹 저장
                search_session["results"] = new_ranking
                search_session["last_updated"] = datetime.utcnow().isoformat()
                search_session["update_trigger"] = trigger_type

                # 캐시 업데이트
                cache_key = f"active_searches:{user_id}"
                active_searches = await self.cache.get(cache_key) or []

                for i, search in enumerate(active_searches):
                    if search.get("session_id") == search_session.get("session_id"):
                        active_searches[i] = search_session
                        break

                await self.cache.set(cache_key, active_searches, ttl=3600)

                return True

            return False

        except Exception as e:
            logger.error(f"Failed to update search ranking: {e}")
            return False

    async def _notify_ranking_update(
        self, user_id: UUID, trigger_type: str, updated_count: int
    ):
        """랭킹 업데이트 알림"""
        user_id_str = str(user_id)

        if user_id_str in self.active_connections:
            try:
                websocket = self.active_connections[user_id_str]

                message = {
                    "type": "ranking_update",
                    "trigger_type": trigger_type,
                    "updated_searches": updated_count,
                    "timestamp": datetime.utcnow().isoformat(),
                }

                await websocket.send_text(json.dumps(message))

            except Exception as e:
                logger.error(f"Failed to send ranking update notification: {e}")

    async def _send_initial_state(self, websocket: WebSocket, user_id: str):
        """초기 상태 전송"""
        try:
            initial_state = {
                "type": "initial_state",
                "user_id": user_id,
                "connected_at": datetime.utcnow().isoformat(),
                "realtime_updates_enabled": True,
            }

            await websocket.send_text(json.dumps(initial_state))

        except Exception as e:
            logger.error(f"Failed to send initial state: {e}")

    async def _handle_websocket_message(self, user_id: str, message: Dict[str, Any]):
        """WebSocket 메시지 처리"""
        try:
            message_type = message.get("type")

            if message_type == "ping":
                # 연결 유지 응답
                await self.active_connections[user_id].send_text(
                    json.dumps({"type": "pong"})
                )

            elif message_type == "register_search":
                # 새 검색 세션 등록
                await self._register_search_session(UUID(user_id), message.get("data"))

            elif message_type == "update_context":
                # 컨텍스트 업데이트
                await self.trigger_ranking_update(
                    UUID(user_id), "context_update", message.get("data")
                )

        except Exception as e:
            logger.error(f"Failed to handle WebSocket message: {e}")

    async def _register_search_session(
        self, user_id: UUID, search_data: Dict[str, Any]
    ):
        """검색 세션 등록"""
        try:
            cache_key = f"active_searches:{user_id}"
            active_searches = await self.cache.get(cache_key) or []

            # 새 검색 세션 추가
            search_session = {
                "session_id": search_data.get("session_id"),
                "query": search_data.get("query"),
                "results": search_data.get("results", []),
                "context": search_data.get("context", {}),
                "created_at": datetime.utcnow().isoformat(),
                "last_updated": datetime.utcnow().isoformat(),
            }

            active_searches.append(search_session)

            # 최대 5개 검색 세션만 유지
            if len(active_searches) > 5:
                active_searches = active_searches[-5:]

            await self.cache.set(cache_key, active_searches, ttl=3600)

        except Exception as e:
            logger.error(f"Failed to register search session: {e}")

    async def _collect_recent_activity(self, place_id: UUID) -> Dict[str, Any]:
        """최근 장소 활동 데이터 수집"""
        try:
            # 캐시에서 최근 활동 데이터 조회
            activity_key = f"place_activity:{place_id}"
            recent_activity = await self.cache.get(activity_key) or {
                "views": 0,
                "clicks": 0,
                "bookmarks": 0,
                "visits": 0,
                "shares": 0,
                "last_updated": datetime.utcnow().isoformat(),
            }

            return recent_activity

        except Exception as e:
            logger.error(f"Failed to collect recent activity: {e}")
            return {}

    def _calculate_popularity_score(self, activity_data: Dict[str, Any]) -> float:
        """활동 데이터를 기반으로 인기도 점수 계산"""
        if not activity_data:
            return 0.0

        # 활동별 가중치
        weights = {
            "views": 1.0,
            "clicks": 2.0,
            "bookmarks": 4.0,
            "visits": 5.0,
            "shares": 3.0,
        }

        total_score = 0.0
        total_activities = 0

        for activity_type, weight in weights.items():
            count = activity_data.get(activity_type, 0)
            total_score += count * weight
            total_activities += count

        if total_activities == 0:
            return 0.0

        # 정규화된 점수 (0-1 범위)
        normalized_score = min(1.0, total_score / (total_activities * 10))

        return normalized_score

    async def _get_current_popularity(self, place_id: UUID) -> float:
        """현재 인기도 점수 조회"""
        try:
            cache_key = f"popularity_score:{place_id}"
            return await self.cache.get(cache_key) or 0.0
        except Exception:
            return 0.0

    def _should_update_popularity(self, current: float, new: float) -> bool:
        """인기도 업데이트 필요 여부 확인"""
        if current == 0.0:
            return new > 0.0

        change_percent = abs(new - current) / current
        return change_percent >= self.update_thresholds["popularity_change_percent"]

    async def _update_popularity_cache(self, popularity_updates: Dict[str, float]):
        """인기도 캐시 업데이트"""
        try:
            for place_id, popularity in popularity_updates.items():
                cache_key = f"popularity_score:{place_id}"
                await self.cache.set(cache_key, popularity, ttl=3600)
        except Exception as e:
            logger.error(f"Failed to update popularity cache: {e}")

    def _calculate_trend_score(self, place_data: Dict[str, Any]) -> float:
        """트렌드 점수 계산"""
        activity_increase = place_data.get("activity_increase", 0.0)
        time_factor = place_data.get("time_factor", 1.0)
        uniqueness = place_data.get("uniqueness", 0.5)

        # 트렌드 점수 = 활동 증가율 × 시간 팩터 × 독특성
        trend_score = activity_increase * time_factor * uniqueness

        return min(1.0, max(0.0, trend_score))

    def _has_ranking_changed(
        self, old_results: List[Dict[str, Any]], new_results: List[Dict[str, Any]]
    ) -> bool:
        """랭킹 변경 여부 확인"""
        if len(old_results) != len(new_results):
            return True

        # 상위 5개 결과의 순서 변경 확인
        top_count = min(5, len(old_results))

        for i in range(top_count):
            old_id = old_results[i].get("id")
            new_id = new_results[i].get("id")

            if old_id != new_id:
                return True

        return False

    # 추가 도우미 메서드들 (간단한 구현)
    async def _get_recently_active_places(self) -> List[UUID]:
        """최근 활발한 장소 목록 조회"""
        # 실제 구현에서는 DB에서 최근 활동이 있는 장소들을 조회
        return []

    async def _analyze_trending_activity(self, since: datetime) -> List[Dict[str, Any]]:
        """트렌딩 활동 분석"""
        # 실제 구현에서는 시계열 데이터 분석
        return []

    async def _monitor_user_context(self, user_id: UUID):
        """사용자 컨텍스트 모니터링"""
        # 위치, 시간, 날씨 등의 변화 감지

    async def _detect_activity_changes(self) -> List[Tuple[UUID, str]]:
        """사용자 활동 변화 감지"""
        return []

    async def _check_location_change_threshold(
        self, user_id: UUID, context: Optional[Dict[str, Any]]
    ) -> bool:
        """위치 변화 임계값 확인"""
        return True

    async def _check_time_change_threshold(
        self, user_id: UUID, context: Optional[Dict[str, Any]]
    ) -> bool:
        """시간 변화 임계값 확인"""
        return True

    async def _check_popularity_change_threshold(
        self, context: Optional[Dict[str, Any]]
    ) -> bool:
        """인기도 변화 임계값 확인"""
        return True

    async def _notify_popularity_changes(self, updates: Dict[str, float]):
        """인기도 변화 알림"""

    async def _notify_trending_places(self, trending: List[Dict[str, Any]]):
        """트렌딩 장소 알림"""
