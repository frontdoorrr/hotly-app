"""
사용자 행동 분석 및 대시보드 서비스

사용자 행동 추적, 분석, 세분화, 대시보드 시각화를 위한 종합 분석 시스템입니다.
TDD 방식으로 개발된 프로덕션 레디 사용자 분석 서비스입니다.
"""

import uuid
import time
import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from collections import defaultdict, deque
from enum import Enum
import threading
from concurrent.futures import ThreadPoolExecutor
import json

from app.services.logging_service import logging_service, LogLevel


class ActionType(str, Enum):
    """사용자 액션 타입"""
    SEARCH = "search"
    PLACE_VIEW = "place_view"
    PLACE_CLICK = "place_click"
    ADD_FAVORITE = "add_favorite"
    REMOVE_FAVORITE = "remove_favorite"
    SHARE = "share"
    APP_OPEN = "app_open"
    SESSION_START = "session_start"
    SESSION_END = "session_end"


class FunnelStage(str, Enum):
    """퍼널 단계"""
    AWARENESS = "awareness"
    INTEREST = "interest"
    CONSIDERATION = "consideration"
    CONVERSION = "conversion"


class UserSegment(str, Enum):
    """사용자 세그먼트"""
    YOUNG_POWER_USER = "young_power_user"
    ACTIVE_PROFESSIONAL = "active_professional"
    MATURE_EXPLORER = "mature_explorer"
    CASUAL_USER = "casual_user"
    GENERAL_USER = "general_user"


@dataclass
class UserAction:
    """사용자 액션 데이터"""
    user_id: str
    action_type: str
    action_data: Dict[str, Any]
    session_id: str
    timestamp: datetime
    id: int = field(default_factory=lambda: int(time.time() * 1000000))


@dataclass
class UserSession:
    """사용자 세션 데이터"""
    session_id: str
    user_id: str
    start_time: datetime
    last_activity: datetime
    device_info: Dict[str, Any]
    actions: List[Dict[str, Any]]
    is_active: bool = True
    end_time: Optional[datetime] = None
    duration_minutes: Optional[float] = None


@dataclass
class UserJourney:
    """사용자 여정 데이터"""
    user_id: str
    first_action: Dict[str, Any]
    actions: List[Dict[str, Any]]
    conversion_events: List[Dict[str, Any]]
    funnel_stage: FunnelStage
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class UserProfile:
    """사용자 프로필 데이터"""
    user_id: str
    demographics: Dict[str, Any]
    behavior_summary: Dict[str, Any]
    segment: Optional[UserSegment]
    created_at: datetime = field(default_factory=datetime.now)


class UserBehaviorTracker:
    """사용자 행동 추적기"""
    
    def __init__(self):
        self.user_actions: List[UserAction] = []
        self.sessions: Dict[str, UserSession] = {}
        self.user_journeys: Dict[str, UserJourney] = {}
        self._lock = threading.Lock()
    
    def track_user_action(
        self,
        user_id: str,
        action_type: str,
        action_data: Dict[str, Any],
        session_id: str = None,
        timestamp: datetime = None
    ) -> Dict[str, Any]:
        """사용자 액션 추적"""
        with self._lock:
            action = UserAction(
                user_id=user_id,
                action_type=action_type,
                action_data=action_data,
                session_id=session_id or f"session-{uuid.uuid4().hex[:8]}",
                timestamp=timestamp or datetime.now()
            )
            
            self.user_actions.append(action)
            
            # 사용자 여정에 추가
            action_dict = asdict(action)
            # ActionType enum을 문자열로 변환
            action_dict["action_type"] = action_type
            self._track_user_journey(user_id, action_dict)
            
            logging_service.log(
                LogLevel.INFO,
                f"User action tracked: {action_type}",
                user_id=user_id,
                extra_fields={
                    "action_type": action_type,
                    "session_id": action.session_id
                }
            )
            
            # ActionType enum을 문자열로 변환하여 반환
            result = asdict(action)
            result["action_type"] = action_type
            return result
    
    def _track_user_journey(self, user_id: str, action: Dict[str, Any]):
        """사용자 여정 추적 (내부 메서드)"""
        if user_id not in self.user_journeys:
            self.user_journeys[user_id] = UserJourney(
                user_id=user_id,
                first_action=action,
                actions=[],
                conversion_events=[],
                funnel_stage=FunnelStage.AWARENESS
            )
        
        journey = self.user_journeys[user_id]
        journey.actions.append(action)
        
        # 퍼널 단계 업데이트
        action_type = action["action_type"]
        if action_type == "search":
            journey.funnel_stage = FunnelStage.INTEREST
        elif action_type == "place_view":
            journey.funnel_stage = FunnelStage.CONSIDERATION
        elif action_type in ["add_favorite", "share"]:
            journey.funnel_stage = FunnelStage.CONVERSION
            journey.conversion_events.append(action)
    
    def start_session(self, user_id: str, device_info: Dict = None) -> str:
        """세션 시작"""
        session_id = f"session-{uuid.uuid4().hex[:8]}"
        
        with self._lock:
            self.sessions[session_id] = UserSession(
                session_id=session_id,
                user_id=user_id,
                start_time=datetime.now(),
                last_activity=datetime.now(),
                device_info=device_info or {},
                actions=[]
            )
        
        return session_id
    
    def update_session_activity(self, session_id: str, action_data: Dict = None):
        """세션 활동 업데이트"""
        with self._lock:
            if session_id in self.sessions:
                session = self.sessions[session_id]
                session.last_activity = datetime.now()
                if action_data:
                    session.actions.append(action_data)
    
    def end_session(self, session_id: str):
        """세션 종료"""
        with self._lock:
            if session_id in self.sessions:
                session = self.sessions[session_id]
                session.end_time = datetime.now()
                session.is_active = False
                session.duration_minutes = (
                    session.end_time - session.start_time
                ).total_seconds() / 60
    
    def get_active_sessions(self) -> List[Dict]:
        """활성 세션 조회"""
        with self._lock:
            return [asdict(s) for s in self.sessions.values() if s.is_active]
    
    def analyze_user_journey(self, user_id: str) -> Dict[str, Any]:
        """사용자 여정 분석"""
        with self._lock:
            if user_id not in self.user_journeys:
                return {"error": "Journey not found"}
            
            journey = self.user_journeys[user_id]
            actions = journey.actions
            
            # 행동 패턴 분석
            action_types = [a["action_type"] for a in actions]
            search_count = action_types.count("search")
            view_count = action_types.count("place_view")
            favorite_count = action_types.count("add_favorite")
            
            # 시간 분석
            if len(actions) >= 2:
                first_time = actions[0]["timestamp"]
                last_time = actions[-1]["timestamp"]
                # 문자열이면 datetime으로 변환
                if isinstance(first_time, str):
                    first_time = datetime.fromisoformat(first_time.replace('Z', '+00:00'))
                if isinstance(last_time, str):
                    last_time = datetime.fromisoformat(last_time.replace('Z', '+00:00'))
                journey_duration = (last_time - first_time).total_seconds() / 60
            else:
                journey_duration = 0
            
            return {
                "user_id": user_id,
                "funnel_stage": journey.funnel_stage.value,
                "total_actions": len(actions),
                "search_count": search_count,
                "view_count": view_count,
                "favorite_count": favorite_count,
                "conversion_events": len(journey.conversion_events),
                "journey_duration_minutes": journey_duration,
                "conversion_rate": len(journey.conversion_events) / max(len(actions), 1)
            }


class BehaviorAnalyzer:
    """행동 분석기"""
    
    def __init__(self):
        self.user_profiles: Dict[str, UserProfile] = {}
        self._lock = threading.Lock()
    
    def create_user_profile(
        self,
        user_id: str,
        demographics: Dict,
        behavior_data: List[Dict]
    ):
        """사용자 프로필 생성"""
        with self._lock:
            self.user_profiles[user_id] = UserProfile(
                user_id=user_id,
                demographics=demographics,
                behavior_summary=self._analyze_behavior(behavior_data),
                segment=None
            )
    
    def _analyze_behavior(self, behavior_data: List[Dict]) -> Dict[str, Any]:
        """행동 분석"""
        if not behavior_data:
            return {"engagement_level": "low", "activity_score": 0}
        
        search_count = sum(b.get("count", 1) for b in behavior_data if b["action"] == "search")
        view_count = sum(b.get("count", 1) for b in behavior_data if b["action"] == "view")
        favorite_count = sum(b.get("count", 1) for b in behavior_data if b["action"] == "favorite")
        
        activity_score = search_count * 1 + view_count * 2 + favorite_count * 5
        
        if activity_score >= 20:
            engagement_level = "high"
        elif activity_score >= 10:
            engagement_level = "medium"
        else:
            engagement_level = "low"
        
        return {
            "engagement_level": engagement_level,
            "activity_score": activity_score,
            "search_count": search_count,
            "view_count": view_count,
            "favorite_count": favorite_count
        }
    
    def segment_users(self):
        """사용자 세분화"""
        with self._lock:
            for user_id, profile in self.user_profiles.items():
                demographics = profile.demographics
                behavior = profile.behavior_summary
                
                # 세분화 로직
                age = demographics.get("age", 0)
                engagement = behavior["engagement_level"]
                activity_score = behavior["activity_score"]
                
                if age < 25 and engagement == "high":
                    segment = UserSegment.YOUNG_POWER_USER
                elif age >= 25 and age < 40 and engagement in ["medium", "high"]:
                    segment = UserSegment.ACTIVE_PROFESSIONAL
                elif age >= 40 and activity_score > 0:
                    segment = UserSegment.MATURE_EXPLORER
                elif engagement == "low":
                    segment = UserSegment.CASUAL_USER
                else:
                    segment = UserSegment.GENERAL_USER
                
                profile.segment = segment
    
    def get_segment_summary(self) -> Dict[str, Any]:
        """세그먼트 요약"""
        with self._lock:
            segments = {}
            for profile in self.user_profiles.values():
                segment = profile.segment.value if profile.segment else "unassigned"
                if segment not in segments:
                    segments[segment] = {"count": 0, "users": []}
                segments[segment]["count"] += 1
                segments[segment]["users"].append(profile.user_id)
            
            return segments
    
    def analyze_search_patterns(self, user_actions: List[Dict]) -> Dict[str, Any]:
        """검색 패턴 분석"""
        search_actions = [a for a in user_actions if a["action_type"] == "search"]
        
        if not search_actions:
            return {"pattern": "no_search"}
        
        # 검색 키워드 분석
        keywords = []
        categories = []
        locations = []
        
        for action in search_actions:
            data = action.get("data", {})
            if "query" in data:
                keywords.extend(data["query"].split())
            if "category" in data:
                categories.append(data["category"])
            if "location" in data:
                locations.append(data["location"])
        
        # 패턴 식별
        most_common_category = max(set(categories), key=categories.count) if categories else None
        most_common_location = max(set(locations), key=locations.count) if locations else None
        
        # 검색 빈도 분석
        if len(search_actions) >= 10:
            search_frequency = "high"
        elif len(search_actions) >= 5:
            search_frequency = "medium"
        else:
            search_frequency = "low"
        
        return {
            "pattern": "search_active",
            "search_count": len(search_actions),
            "search_frequency": search_frequency,
            "top_category": most_common_category,
            "top_location": most_common_location,
            "unique_keywords": len(set(keywords)),
            "keyword_diversity": len(set(keywords)) / max(len(keywords), 1)
        }
    
    def analyze_engagement_patterns(self, user_actions: List[Dict]) -> Dict[str, Any]:
        """참여 패턴 분석"""
        if not user_actions:
            return {"pattern": "inactive"}
        
        # 시간별 활동 분석
        action_times = []
        for action in user_actions:
            timestamp = action["timestamp"]
            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            action_times.append(timestamp.hour)
        
        peak_hour = max(set(action_times), key=action_times.count)
        
        # 연속 행동 분석
        action_sequences = []
        for i in range(len(user_actions) - 1):
            current_action = user_actions[i]["action_type"]
            next_action = user_actions[i + 1]["action_type"]
            action_sequences.append(f"{current_action}->{next_action}")
        
        most_common_sequence = max(set(action_sequences), key=action_sequences.count) if action_sequences else None
        
        # 세션 지속시간 분석
        if len(user_actions) >= 2:
            first_timestamp = user_actions[0]["timestamp"]
            last_timestamp = user_actions[-1]["timestamp"]
            
            if isinstance(first_timestamp, str):
                first_timestamp = datetime.fromisoformat(first_timestamp.replace('Z', '+00:00'))
            if isinstance(last_timestamp, str):
                last_timestamp = datetime.fromisoformat(last_timestamp.replace('Z', '+00:00'))
            
            session_duration = (last_timestamp - first_timestamp).total_seconds() / 60
        else:
            session_duration = 0
        
        # 참여 수준 결정
        if len(user_actions) >= 10 and session_duration >= 10:
            engagement_level = "high"
        elif len(user_actions) >= 5 or session_duration >= 5:
            engagement_level = "medium"
        else:
            engagement_level = "low"
        
        return {
            "pattern": "engaged",
            "engagement_level": engagement_level,
            "peak_hour": peak_hour,
            "session_duration_minutes": session_duration,
            "most_common_sequence": most_common_sequence,
            "total_actions": len(user_actions)
        }


class AnalyticsDashboard:
    """분석 대시보드"""
    
    def __init__(self):
        self.dashboard_data = {
            "user_metrics": {},
            "behavior_metrics": {},
            "conversion_metrics": {},
            "real_time_data": {}
        }
        self.real_time_data = {
            "current_active_users": 0,
            "live_actions": [],
            "trending_searches": {},
            "alerts": []
        }
        self._lock = threading.Lock()
    
    def collect_user_metrics(self, user_data: List[Dict]) -> Dict[str, Any]:
        """사용자 메트릭 수집"""
        total_users = len(user_data)
        active_users = sum(1 for user in user_data if user["last_active_days"] <= 7)
        new_users = sum(1 for user in user_data if user["registration_days"] <= 7)
        
        # 연령대별 분포
        age_groups = {"18-25": 0, "26-35": 0, "36-45": 0, "46+": 0}
        for user in user_data:
            age = user.get("age", 30)
            if age <= 25:
                age_groups["18-25"] += 1
            elif age <= 35:
                age_groups["26-35"] += 1
            elif age <= 45:
                age_groups["36-45"] += 1
            else:
                age_groups["46+"] += 1
        
        metrics = {
            "total_users": total_users,
            "active_users": active_users,
            "new_users": new_users,
            "retention_rate": active_users / max(total_users, 1),
            "age_distribution": age_groups
        }
        
        with self._lock:
            self.dashboard_data["user_metrics"] = metrics
        
        return metrics
    
    def collect_behavior_metrics(self, behavior_data: List[Dict]) -> Dict[str, Any]:
        """행동 메트릭 수집"""
        if not behavior_data:
            metrics = {"avg_session_duration": 0, "avg_actions_per_session": 0}
            with self._lock:
                self.dashboard_data["behavior_metrics"] = metrics
            return metrics
        
        sessions = {}
        for action in behavior_data:
            session_id = action["session_id"]
            if session_id not in sessions:
                sessions[session_id] = {
                    "actions": [],
                    "start_time": action["timestamp"],
                    "end_time": action["timestamp"]
                }
            
            sessions[session_id]["actions"].append(action)
            sessions[session_id]["end_time"] = max(
                sessions[session_id]["end_time"],
                action["timestamp"]
            )
        
        # 세션 분석
        session_durations = []
        actions_per_session = []
        
        for session in sessions.values():
            start_time = session["start_time"]
            end_time = session["end_time"]
            
            # 문자열이면 datetime으로 변환
            if isinstance(start_time, str):
                start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            if isinstance(end_time, str):
                end_time = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            
            duration = (end_time - start_time).total_seconds() / 60
            session_durations.append(duration)
            actions_per_session.append(len(session["actions"]))
        
        avg_session_duration = sum(session_durations) / len(session_durations)
        avg_actions_per_session = sum(actions_per_session) / len(actions_per_session)
        
        # 가장 인기있는 액션
        action_types = [action["action_type"] for action in behavior_data]
        popular_actions = {}
        for action_type in set(action_types):
            popular_actions[action_type] = action_types.count(action_type)
        
        metrics = {
            "total_sessions": len(sessions),
            "avg_session_duration": avg_session_duration,
            "avg_actions_per_session": avg_actions_per_session,
            "popular_actions": popular_actions
        }
        
        with self._lock:
            self.dashboard_data["behavior_metrics"] = metrics
        
        return metrics
    
    def collect_conversion_metrics(self, conversion_data: List[Dict]) -> Dict[str, Any]:
        """전환 메트릭 수집"""
        total_sessions = len(set(event["session_id"] for event in conversion_data))
        conversions = sum(1 for event in conversion_data if event["event_type"] == "conversion")
        
        # 전환 유형별 분석
        conversion_types = {}
        for event in conversion_data:
            if event["event_type"] == "conversion":
                conv_type = event["conversion_type"]
                conversion_types[conv_type] = conversion_types.get(conv_type, 0) + 1
        
        # 퍼널 분석
        funnel_steps = ["awareness", "interest", "consideration", "conversion"]
        funnel_data = {step: 0 for step in funnel_steps}
        
        for event in conversion_data:
            # 퍼널 단계가 있는 이벤트만 처리
            if "funnel_step" in event:
                step = event["funnel_step"]
                if step in funnel_data:
                    funnel_data[step] += 1
        
        metrics = {
            "total_sessions": total_sessions,
            "total_conversions": conversions,
            "conversion_rate": conversions / max(total_sessions, 1),
            "conversion_types": conversion_types,
            "funnel_data": funnel_data
        }
        
        with self._lock:
            self.dashboard_data["conversion_metrics"] = metrics
        
        return metrics
    
    def update_active_users(self, user_count: int):
        """활성 사용자 수 업데이트"""
        with self._lock:
            self.real_time_data["current_active_users"] = user_count
    
    def add_live_action(self, action: Dict[str, Any]):
        """실시간 액션 추가"""
        with self._lock:
            action["timestamp"] = datetime.now()
            self.real_time_data["live_actions"].append(action)
            
            # 최근 100개만 유지
            if len(self.real_time_data["live_actions"]) > 100:
                self.real_time_data["live_actions"] = self.real_time_data["live_actions"][-100:]
            
            # 트렌딩 검색어 업데이트
            if action["action_type"] == "search":
                query = action.get("query", "")
                if query:
                    if query not in self.real_time_data["trending_searches"]:
                        self.real_time_data["trending_searches"][query] = 0
                    self.real_time_data["trending_searches"][query] += 1
    
    def check_alerts(self, current_metrics: Dict[str, Any]):
        """알림 체크"""
        with self._lock:
            alerts = []
            
            # 활성 사용자 수 급증 알림
            if current_metrics.get("active_users", 0) > 1000:
                alerts.append({
                    "type": "high_traffic",
                    "message": f"Active users: {current_metrics['active_users']}",
                    "severity": "info",
                    "timestamp": datetime.now()
                })
            
            # 에러율 증가 알림
            if current_metrics.get("error_rate", 0) > 0.05:
                alerts.append({
                    "type": "high_error_rate",
                    "message": f"Error rate: {current_metrics['error_rate']:.1%}",
                    "severity": "warning",
                    "timestamp": datetime.now()
                })
            
            self.real_time_data["alerts"].extend(alerts)
            
            # 최근 10개 알림만 유지
            if len(self.real_time_data["alerts"]) > 10:
                self.real_time_data["alerts"] = self.real_time_data["alerts"][-10:]
    
    def get_trending_searches(self, limit: int = 5) -> List[Dict[str, Any]]:
        """트렌딩 검색어 조회"""
        with self._lock:
            searches = self.real_time_data["trending_searches"]
            sorted_searches = sorted(searches.items(), key=lambda x: x[1], reverse=True)
            
            return [
                {"query": query, "count": count}
                for query, count in sorted_searches[:limit]
            ]
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """대시보드 데이터 조회"""
        with self._lock:
            return {
                **self.dashboard_data,
                "real_time_data": self.real_time_data.copy()
            }


class UserBehaviorAnalyticsService:
    """사용자 행동 분석 통합 서비스"""
    
    def __init__(self):
        self.behavior_tracker = UserBehaviorTracker()
        self.behavior_analyzer = BehaviorAnalyzer()
        self.analytics_dashboard = AnalyticsDashboard()
        self.executor = ThreadPoolExecutor(max_workers=4)
    
    # 행동 추적 메서드들
    def track_action(
        self,
        user_id: str,
        action_type: str,
        action_data: Dict[str, Any],
        session_id: str = None
    ) -> Dict[str, Any]:
        """사용자 액션 추적"""
        action = self.behavior_tracker.track_user_action(
            user_id=user_id,
            action_type=action_type,
            action_data=action_data,
            session_id=session_id
        )
        
        # 실시간 대시보드에 추가
        self.analytics_dashboard.add_live_action({
            "action_type": action_type,
            "user_id": user_id,
            **action_data
        })
        
        return action
    
    def start_user_session(self, user_id: str, device_info: Dict = None) -> str:
        """사용자 세션 시작"""
        return self.behavior_tracker.start_session(user_id, device_info)
    
    def end_user_session(self, session_id: str):
        """사용자 세션 종료"""
        self.behavior_tracker.end_session(session_id)
    
    def get_user_journey(self, user_id: str) -> Dict[str, Any]:
        """사용자 여정 분석"""
        return self.behavior_tracker.analyze_user_journey(user_id)
    
    # 행동 분석 메서드들
    def create_user_profile(
        self,
        user_id: str,
        demographics: Dict,
        behavior_data: List[Dict]
    ):
        """사용자 프로필 생성"""
        self.behavior_analyzer.create_user_profile(user_id, demographics, behavior_data)
    
    def segment_all_users(self):
        """모든 사용자 세분화"""
        self.behavior_analyzer.segment_users()
    
    def get_user_segments(self) -> Dict[str, Any]:
        """사용자 세그먼트 요약"""
        return self.behavior_analyzer.get_segment_summary()
    
    def analyze_search_patterns(self, user_actions: List[Dict]) -> Dict[str, Any]:
        """검색 패턴 분석"""
        return self.behavior_analyzer.analyze_search_patterns(user_actions)
    
    def analyze_engagement_patterns(self, user_actions: List[Dict]) -> Dict[str, Any]:
        """참여 패턴 분석"""
        return self.behavior_analyzer.analyze_engagement_patterns(user_actions)
    
    # 대시보드 메서드들
    def update_dashboard_metrics(
        self,
        user_data: List[Dict] = None,
        behavior_data: List[Dict] = None,
        conversion_data: List[Dict] = None
    ) -> Dict[str, Any]:
        """대시보드 메트릭 업데이트"""
        dashboard_data = {}
        
        if user_data:
            dashboard_data["user_metrics"] = self.analytics_dashboard.collect_user_metrics(user_data)
        
        if behavior_data:
            dashboard_data["behavior_metrics"] = self.analytics_dashboard.collect_behavior_metrics(behavior_data)
        
        if conversion_data:
            dashboard_data["conversion_metrics"] = self.analytics_dashboard.collect_conversion_metrics(conversion_data)
        
        return dashboard_data
    
    def update_active_users(self, count: int):
        """활성 사용자 수 업데이트"""
        self.analytics_dashboard.update_active_users(count)
    
    def get_trending_searches(self, limit: int = 5) -> List[Dict[str, Any]]:
        """트렌딩 검색어 조회"""
        return self.analytics_dashboard.get_trending_searches(limit)
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """종합 대시보드 데이터 조회"""
        return self.analytics_dashboard.get_dashboard_data()
    
    def check_system_alerts(self, metrics: Dict[str, Any]):
        """시스템 알림 체크"""
        self.analytics_dashboard.check_alerts(metrics)


# 글로벌 서비스 인스턴스
user_analytics_service = UserBehaviorAnalyticsService()


def get_user_analytics_service() -> UserBehaviorAnalyticsService:
    """사용자 분석 서비스 인스턴스 조회"""
    return user_analytics_service


# 편의 함수들
def track_user_action(user_id: str, action_type: str, action_data: Dict[str, Any], session_id: str = None):
    """사용자 액션 추적 편의 함수"""
    return user_analytics_service.track_action(user_id, action_type, action_data, session_id)


def track_search(user_id: str, query: str, filters: Dict = None, results_count: int = 0, session_id: str = None):
    """검색 추적 편의 함수"""
    return track_user_action(
        user_id=user_id,
        action_type=ActionType.SEARCH.value,
        action_data={
            "query": query,
            "filters": filters or {},
            "results_count": results_count
        },
        session_id=session_id
    )


def track_place_view(user_id: str, place_id: str, place_name: str, duration: int = None, session_id: str = None):
    """장소 조회 추적 편의 함수"""
    return track_user_action(
        user_id=user_id,
        action_type=ActionType.PLACE_VIEW.value,
        action_data={
            "place_id": place_id,
            "place_name": place_name,
            "view_duration": duration
        },
        session_id=session_id
    )


def track_favorite_action(user_id: str, place_id: str, place_name: str, action: str = "add", session_id: str = None):
    """즐겨찾기 액션 추적 편의 함수"""
    action_type = ActionType.ADD_FAVORITE if action == "add" else ActionType.REMOVE_FAVORITE
    return track_user_action(
        user_id=user_id,
        action_type=action_type.value,
        action_data={
            "place_id": place_id,
            "place_name": place_name
        },
        session_id=session_id
    )