"""
사용자 행동 분석 및 대시보드 시스템 TDD 테스트

사용자 행동 추적, 분석, 대시보드 시각화를 위한 TDD 테스트를 정의합니다.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, patch, AsyncMock
import json
import time
import uuid


class TestUserBehaviorTracking:
    """사용자 행동 추적 테스트"""
    
    def test_user_action_tracking(self):
        """사용자 액션 추적 테스트"""
        # Given: 사용자 행동 추적 시스템
        user_actions = []
        
        def track_user_action(
            user_id: str,
            action_type: str,
            action_data: Dict[str, Any],
            session_id: str = None,
            timestamp: datetime = None
        ):
            """사용자 액션 추적"""
            action = {
                "user_id": user_id,
                "action_type": action_type,
                "action_data": action_data,
                "session_id": session_id or f"session-{uuid.uuid4().hex[:8]}",
                "timestamp": timestamp or datetime.now(),
                "id": len(user_actions) + 1
            }
            user_actions.append(action)
            return action
        
        # When: 다양한 사용자 액션 추적
        session_id = "session-12345"
        
        # 검색 액션
        search_action = track_user_action(
            user_id="user-123",
            action_type="search",
            action_data={
                "query": "맛집 강남",
                "filters": {"category": "restaurant", "location": "강남"},
                "results_count": 25
            },
            session_id=session_id
        )
        
        # 장소 클릭 액션
        place_click_action = track_user_action(
            user_id="user-123",
            action_type="place_click",
            action_data={
                "place_id": "place-456",
                "place_name": "강남 맛집",
                "click_position": 3,
                "search_query": "맛집 강남"
            },
            session_id=session_id
        )
        
        # 즐겨찾기 추가 액션
        favorite_action = track_user_action(
            user_id="user-123",
            action_type="add_favorite",
            action_data={
                "place_id": "place-456",
                "place_name": "강남 맛집"
            },
            session_id=session_id
        )
        
        # Then: 추적 데이터 검증
        assert len(user_actions) == 3
        
        # 검색 액션 검증
        assert search_action["action_type"] == "search"
        assert search_action["action_data"]["query"] == "맛집 강남"
        assert search_action["action_data"]["results_count"] == 25
        assert search_action["session_id"] == session_id
        
        # 장소 클릭 액션 검증
        assert place_click_action["action_type"] == "place_click"
        assert place_click_action["action_data"]["place_id"] == "place-456"
        assert place_click_action["action_data"]["click_position"] == 3
        
        # 즐겨찾기 액션 검증
        assert favorite_action["action_type"] == "add_favorite"
        assert favorite_action["action_data"]["place_id"] == "place-456"
        
        # 모든 액션이 같은 세션인지 확인
        assert all(action["session_id"] == session_id for action in user_actions)
        assert all(action["user_id"] == "user-123" for action in user_actions)
        
        print("✅ 사용자 액션 추적 테스트 통과")
        
    def test_session_management(self):
        """세션 관리 테스트"""
        # Given: 세션 관리 시스템
        sessions = {}
        
        def start_session(user_id: str, device_info: Dict = None) -> str:
            """세션 시작"""
            session_id = f"session-{uuid.uuid4().hex[:8]}"
            sessions[session_id] = {
                "user_id": user_id,
                "start_time": datetime.now(),
                "last_activity": datetime.now(),
                "device_info": device_info or {},
                "actions": [],
                "is_active": True
            }
            return session_id
        
        def update_session_activity(session_id: str, action_data: Dict = None):
            """세션 활동 업데이트"""
            if session_id in sessions:
                sessions[session_id]["last_activity"] = datetime.now()
                if action_data:
                    sessions[session_id]["actions"].append(action_data)
        
        def end_session(session_id: str):
            """세션 종료"""
            if session_id in sessions:
                session = sessions[session_id]
                session["end_time"] = datetime.now()
                session["is_active"] = False
                session["duration_minutes"] = (
                    session["end_time"] - session["start_time"]
                ).total_seconds() / 60
        
        def get_active_sessions() -> List[Dict]:
            """활성 세션 조회"""
            return [s for s in sessions.values() if s["is_active"]]
        
        # When: 세션 시나리오 테스트
        device_info = {
            "device_type": "mobile",
            "os": "iOS",
            "app_version": "1.2.0"
        }
        
        session1 = start_session("user-123", device_info)
        session2 = start_session("user-456", {"device_type": "web"})
        
        # 세션 활동 업데이트
        update_session_activity(session1, {"action": "search", "query": "맛집"})
        update_session_activity(session1, {"action": "click", "place_id": "place-1"})
        update_session_activity(session2, {"action": "browse", "category": "cafe"})
        
        # 첫 번째 세션 종료
        end_session(session1)
        
        # Then: 세션 관리 검증
        assert len(sessions) == 2
        
        # 세션 1 검증 (종료됨)
        session1_data = sessions[session1]
        assert session1_data["user_id"] == "user-123"
        assert session1_data["device_info"]["device_type"] == "mobile"
        assert not session1_data["is_active"]
        assert "end_time" in session1_data
        assert "duration_minutes" in session1_data
        assert len(session1_data["actions"]) == 2
        
        # 세션 2 검증 (활성)
        session2_data = sessions[session2]
        assert session2_data["user_id"] == "user-456"
        assert session2_data["is_active"]
        assert len(session2_data["actions"]) == 1
        
        # 활성 세션 확인
        active_sessions = get_active_sessions()
        assert len(active_sessions) == 1
        assert active_sessions[0]["user_id"] == "user-456"
        
        print("✅ 세션 관리 테스트 통과")
        
    def test_user_journey_tracking(self):
        """사용자 여정 추적 테스트"""
        # Given: 사용자 여정 추적 시스템
        user_journeys = {}
        
        def track_user_journey(user_id: str, action: Dict[str, Any]):
            """사용자 여정 추적"""
            if user_id not in user_journeys:
                user_journeys[user_id] = {
                    "user_id": user_id,
                    "first_action": action,
                    "actions": [],
                    "conversion_events": [],
                    "funnel_stage": "awareness"
                }
            
            journey = user_journeys[user_id]
            journey["actions"].append(action)
            
            # 퍼널 단계 업데이트
            action_type = action["action_type"]
            if action_type == "search":
                journey["funnel_stage"] = "interest"
            elif action_type == "place_view":
                journey["funnel_stage"] = "consideration"
            elif action_type == "add_favorite" or action_type == "share":
                journey["funnel_stage"] = "conversion"
                journey["conversion_events"].append(action)
        
        def analyze_user_journey(user_id: str) -> Dict[str, Any]:
            """사용자 여정 분석"""
            if user_id not in user_journeys:
                return {"error": "Journey not found"}
            
            journey = user_journeys[user_id]
            actions = journey["actions"]
            
            # 행동 패턴 분석
            action_types = [a["action_type"] for a in actions]
            search_count = action_types.count("search")
            view_count = action_types.count("place_view")
            favorite_count = action_types.count("add_favorite")
            
            # 시간 분석
            if len(actions) >= 2:
                first_time = actions[0]["timestamp"]
                last_time = actions[-1]["timestamp"]
                journey_duration = (last_time - first_time).total_seconds() / 60
            else:
                journey_duration = 0
            
            return {
                "user_id": user_id,
                "funnel_stage": journey["funnel_stage"],
                "total_actions": len(actions),
                "search_count": search_count,
                "view_count": view_count,
                "favorite_count": favorite_count,
                "conversion_events": len(journey["conversion_events"]),
                "journey_duration_minutes": journey_duration,
                "conversion_rate": len(journey["conversion_events"]) / max(len(actions), 1)
            }
        
        # When: 사용자 여정 시뮬레이션
        user_id = "user-789"
        
        # 여정 단계별 액션
        actions = [
            {
                "action_type": "app_open",
                "timestamp": datetime.now(),
                "data": {"source": "home_screen"}
            },
            {
                "action_type": "search",
                "timestamp": datetime.now() + timedelta(seconds=30),
                "data": {"query": "이태원 맛집", "category": "restaurant"}
            },
            {
                "action_type": "place_view",
                "timestamp": datetime.now() + timedelta(minutes=1),
                "data": {"place_id": "place-789", "view_duration": 45}
            },
            {
                "action_type": "place_view",
                "timestamp": datetime.now() + timedelta(minutes=2),
                "data": {"place_id": "place-790", "view_duration": 30}
            },
            {
                "action_type": "add_favorite",
                "timestamp": datetime.now() + timedelta(minutes=3),
                "data": {"place_id": "place-789"}
            }
        ]
        
        for action in actions:
            track_user_journey(user_id, action)
        
        analysis = analyze_user_journey(user_id)
        
        # Then: 여정 분석 검증
        assert analysis["user_id"] == user_id
        assert analysis["funnel_stage"] == "conversion"
        assert analysis["total_actions"] == 5
        assert analysis["search_count"] == 1
        assert analysis["view_count"] == 2
        assert analysis["favorite_count"] == 1
        assert analysis["conversion_events"] == 1
        assert analysis["journey_duration_minutes"] > 0
        assert analysis["conversion_rate"] == 0.2  # 1/5
        
        # 여정 데이터 구조 검증
        journey = user_journeys[user_id]
        assert journey["first_action"]["action_type"] == "app_open"
        assert len(journey["conversion_events"]) == 1
        assert journey["conversion_events"][0]["action_type"] == "add_favorite"
        
        print("✅ 사용자 여정 추적 테스트 통과")


class TestBehaviorAnalytics:
    """행동 분석 테스트"""
    
    def test_user_segmentation(self):
        """사용자 세분화 테스트"""
        # Given: 사용자 세분화 시스템
        user_profiles = {}
        
        def create_user_profile(user_id: str, demographics: Dict, behavior_data: List[Dict]):
            """사용자 프로필 생성"""
            user_profiles[user_id] = {
                "user_id": user_id,
                "demographics": demographics,
                "behavior_summary": analyze_behavior(behavior_data),
                "segment": None,
                "created_at": datetime.now()
            }
        
        def analyze_behavior(behavior_data: List[Dict]) -> Dict[str, Any]:
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
        
        def segment_users():
            """사용자 세분화"""
            for user_id, profile in user_profiles.items():
                demographics = profile["demographics"]
                behavior = profile["behavior_summary"]
                
                # 세분화 로직
                age = demographics.get("age", 0)
                engagement = behavior["engagement_level"]
                activity_score = behavior["activity_score"]
                
                if age < 25 and engagement == "high":
                    segment = "young_power_user"
                elif age >= 25 and age < 40 and engagement in ["medium", "high"]:
                    segment = "active_professional"
                elif age >= 40 and activity_score > 0:
                    segment = "mature_explorer"
                elif engagement == "low":
                    segment = "casual_user"
                else:
                    segment = "general_user"
                
                profile["segment"] = segment
        
        def get_segment_summary() -> Dict[str, Any]:
            """세그먼트 요약"""
            segments = {}
            for profile in user_profiles.values():
                segment = profile["segment"]
                if segment not in segments:
                    segments[segment] = {"count": 0, "users": []}
                segments[segment]["count"] += 1
                segments[segment]["users"].append(profile["user_id"])
            
            return segments
        
        # When: 다양한 사용자 프로필 생성
        # 젊은 파워 유저
        create_user_profile(
            "user-young-1",
            {"age": 22, "gender": "F", "location": "서울"},
            [
                {"action": "search", "count": 10},
                {"action": "view", "count": 20},
                {"action": "favorite", "count": 5}
            ] * 2  # 높은 활동량
        )
        
        # 활발한 직장인
        create_user_profile(
            "user-professional-1",
            {"age": 32, "gender": "M", "location": "경기"},
            [
                {"action": "search", "count": 5},
                {"action": "view", "count": 8},
                {"action": "favorite", "count": 2}
            ]
        )
        
        # 성숙한 탐험가
        create_user_profile(
            "user-mature-1",
            {"age": 45, "gender": "F", "location": "부산"},
            [
                {"action": "search", "count": 3},
                {"action": "view", "count": 5},
                {"action": "favorite", "count": 1}
            ]
        )
        
        # 캐주얼 사용자
        create_user_profile(
            "user-casual-1",
            {"age": 28, "gender": "M", "location": "대구"},
            [
                {"action": "search", "count": 1},
                {"action": "view", "count": 1}
            ]
        )
        
        # 세분화 실행
        segment_users()
        segment_summary = get_segment_summary()
        
        # Then: 세분화 결과 검증
        assert len(user_profiles) == 4
        
        # 개별 사용자 세그먼트 확인
        assert user_profiles["user-young-1"]["segment"] == "young_power_user"
        assert user_profiles["user-professional-1"]["segment"] == "active_professional"
        assert user_profiles["user-mature-1"]["segment"] == "mature_explorer"
        assert user_profiles["user-casual-1"]["segment"] == "casual_user"
        
        # 세그먼트 요약 확인
        assert "young_power_user" in segment_summary
        assert segment_summary["young_power_user"]["count"] == 1
        assert "active_professional" in segment_summary
        assert "mature_explorer" in segment_summary
        assert "casual_user" in segment_summary
        
        # 행동 분석 검증
        young_user = user_profiles["user-young-1"]
        assert young_user["behavior_summary"]["engagement_level"] == "high"
        assert young_user["behavior_summary"]["activity_score"] > 20
        
        print("✅ 사용자 세분화 테스트 통과")
        
    def test_behavior_pattern_analysis(self):
        """행동 패턴 분석 테스트"""
        # Given: 행동 패턴 분석 시스템
        behavior_patterns = []
        
        def analyze_search_patterns(user_actions: List[Dict]) -> Dict[str, Any]:
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
        
        def analyze_engagement_patterns(user_actions: List[Dict]) -> Dict[str, Any]:
            """참여 패턴 분석"""
            if not user_actions:
                return {"pattern": "inactive"}
            
            # 시간별 활동 분석
            action_times = [a["timestamp"].hour for a in user_actions]
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
                session_duration = (user_actions[-1]["timestamp"] - user_actions[0]["timestamp"]).total_seconds() / 60
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
        
        # When: 사용자 행동 데이터로 패턴 분석
        user_actions = [
            {
                "action_type": "search",
                "timestamp": datetime(2024, 1, 15, 12, 0),
                "data": {"query": "강남 맛집", "category": "restaurant", "location": "강남"}
            },
            {
                "action_type": "place_view",
                "timestamp": datetime(2024, 1, 15, 12, 5),
                "data": {"place_id": "place-1", "duration": 30}
            },
            {
                "action_type": "search",
                "timestamp": datetime(2024, 1, 15, 12, 10),
                "data": {"query": "강남 카페", "category": "cafe", "location": "강남"}
            },
            {
                "action_type": "place_view",
                "timestamp": datetime(2024, 1, 15, 12, 15),
                "data": {"place_id": "place-2", "duration": 45}
            },
            {
                "action_type": "add_favorite",
                "timestamp": datetime(2024, 1, 15, 12, 20),
                "data": {"place_id": "place-2"}
            },
            {
                "action_type": "search",
                "timestamp": datetime(2024, 1, 15, 12, 25),
                "data": {"query": "강남 술집", "category": "bar", "location": "강남"}
            }
        ]
        
        search_patterns = analyze_search_patterns(user_actions)
        engagement_patterns = analyze_engagement_patterns(user_actions)
        
        # Then: 패턴 분석 결과 검증
        
        # 검색 패턴 검증
        assert search_patterns["pattern"] == "search_active"
        assert search_patterns["search_count"] == 3
        assert search_patterns["search_frequency"] == "low"  # 3 < 5
        assert search_patterns["top_location"] == "강남"
        assert search_patterns["unique_keywords"] > 0
        
        # 참여 패턴 검증
        assert engagement_patterns["pattern"] == "engaged"
        assert engagement_patterns["peak_hour"] == 12
        assert engagement_patterns["session_duration_minutes"] == 25.0
        assert engagement_patterns["total_actions"] == 6
        assert engagement_patterns["engagement_level"] == "medium"  # 6 actions, 25 minutes
        
        # 행동 시퀀스 확인
        assert engagement_patterns["most_common_sequence"] is not None
        
        print("✅ 행동 패턴 분석 테스트 통과")


class TestDashboardSystem:
    """대시보드 시스템 테스트"""
    
    def test_analytics_dashboard_data(self):
        """분석 대시보드 데이터 테스트"""
        # Given: 대시보드 데이터 수집 시스템
        dashboard_data = {
            "user_metrics": {},
            "behavior_metrics": {},
            "conversion_metrics": {},
            "real_time_data": {}
        }
        
        def collect_user_metrics(user_data: List[Dict]) -> Dict[str, Any]:
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
            
            return {
                "total_users": total_users,
                "active_users": active_users,
                "new_users": new_users,
                "retention_rate": active_users / max(total_users, 1),
                "age_distribution": age_groups
            }
        
        def collect_behavior_metrics(behavior_data: List[Dict]) -> Dict[str, Any]:
            """행동 메트릭 수집"""
            if not behavior_data:
                return {"avg_session_duration": 0, "avg_actions_per_session": 0}
            
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
                duration = (session["end_time"] - session["start_time"]).total_seconds() / 60
                session_durations.append(duration)
                actions_per_session.append(len(session["actions"]))
            
            avg_session_duration = sum(session_durations) / len(session_durations)
            avg_actions_per_session = sum(actions_per_session) / len(actions_per_session)
            
            # 가장 인기있는 액션
            action_types = [action["action_type"] for action in behavior_data]
            popular_actions = {}
            for action_type in set(action_types):
                popular_actions[action_type] = action_types.count(action_type)
            
            return {
                "total_sessions": len(sessions),
                "avg_session_duration": avg_session_duration,
                "avg_actions_per_session": avg_actions_per_session,
                "popular_actions": popular_actions
            }
        
        def collect_conversion_metrics(conversion_data: List[Dict]) -> Dict[str, Any]:
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
            
            return {
                "total_sessions": total_sessions,
                "total_conversions": conversions,
                "conversion_rate": conversions / max(total_sessions, 1),
                "conversion_types": conversion_types,
                "funnel_data": funnel_data
            }
        
        # When: 대시보드 데이터 수집
        
        # 사용자 데이터
        user_data = [
            {"id": "user-1", "age": 25, "last_active_days": 1, "registration_days": 30},
            {"id": "user-2", "age": 32, "last_active_days": 3, "registration_days": 15},
            {"id": "user-3", "age": 28, "last_active_days": 10, "registration_days": 5},
            {"id": "user-4", "age": 45, "last_active_days": 2, "registration_days": 60},
            {"id": "user-5", "age": 35, "last_active_days": 1, "registration_days": 3}
        ]
        
        # 행동 데이터
        behavior_data = [
            {"session_id": "s1", "action_type": "search", "timestamp": datetime(2024, 1, 15, 10, 0)},
            {"session_id": "s1", "action_type": "view", "timestamp": datetime(2024, 1, 15, 10, 5)},
            {"session_id": "s1", "action_type": "favorite", "timestamp": datetime(2024, 1, 15, 10, 10)},
            {"session_id": "s2", "action_type": "search", "timestamp": datetime(2024, 1, 15, 11, 0)},
            {"session_id": "s2", "action_type": "view", "timestamp": datetime(2024, 1, 15, 11, 2)},
            {"session_id": "s3", "action_type": "search", "timestamp": datetime(2024, 1, 15, 12, 0)}
        ]
        
        # 전환 데이터
        conversion_data = [
            {"session_id": "s1", "event_type": "funnel", "funnel_step": "awareness"},
            {"session_id": "s1", "event_type": "funnel", "funnel_step": "interest"},
            {"session_id": "s1", "event_type": "conversion", "conversion_type": "add_favorite"},
            {"session_id": "s2", "event_type": "funnel", "funnel_step": "awareness"},
            {"session_id": "s2", "event_type": "funnel", "funnel_step": "interest"},
            {"session_id": "s3", "event_type": "funnel", "funnel_step": "awareness"}
        ]
        
        # 메트릭 수집
        dashboard_data["user_metrics"] = collect_user_metrics(user_data)
        dashboard_data["behavior_metrics"] = collect_behavior_metrics(behavior_data)
        dashboard_data["conversion_metrics"] = collect_conversion_metrics(conversion_data)
        
        # Then: 대시보드 데이터 검증
        
        # 사용자 메트릭 검증
        user_metrics = dashboard_data["user_metrics"]
        assert user_metrics["total_users"] == 5
        assert user_metrics["active_users"] == 4  # last_active_days <= 7
        assert user_metrics["new_users"] == 2     # registration_days <= 7
        assert user_metrics["retention_rate"] == 0.8  # 4/5
        assert "age_distribution" in user_metrics
        
        # 행동 메트릭 검증
        behavior_metrics = dashboard_data["behavior_metrics"]
        assert behavior_metrics["total_sessions"] == 3
        assert behavior_metrics["avg_session_duration"] > 0
        assert behavior_metrics["avg_actions_per_session"] > 0
        assert "search" in behavior_metrics["popular_actions"]
        
        # 전환 메트릭 검증
        conversion_metrics = dashboard_data["conversion_metrics"]
        assert conversion_metrics["total_conversions"] == 1
        assert conversion_metrics["conversion_rate"] > 0
        assert "add_favorite" in conversion_metrics["conversion_types"]
        assert conversion_metrics["funnel_data"]["awareness"] == 3
        
        print("✅ 분석 대시보드 데이터 테스트 통과")
        
    def test_real_time_dashboard_updates(self):
        """실시간 대시보드 업데이트 테스트"""
        # Given: 실시간 대시보드 시스템
        real_time_data = {
            "current_active_users": 0,
            "live_actions": [],
            "trending_searches": {},
            "alerts": []
        }
        
        def update_active_users(user_count: int):
            """활성 사용자 수 업데이트"""
            real_time_data["current_active_users"] = user_count
        
        def add_live_action(action: Dict[str, Any]):
            """실시간 액션 추가"""
            action["timestamp"] = datetime.now()
            real_time_data["live_actions"].append(action)
            
            # 최근 100개만 유지
            if len(real_time_data["live_actions"]) > 100:
                real_time_data["live_actions"] = real_time_data["live_actions"][-100:]
            
            # 트렌딩 검색어 업데이트
            if action["action_type"] == "search":
                query = action.get("query", "")
                if query:
                    if query not in real_time_data["trending_searches"]:
                        real_time_data["trending_searches"][query] = 0
                    real_time_data["trending_searches"][query] += 1
        
        def check_alerts(current_metrics: Dict[str, Any]):
            """알림 체크"""
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
            
            real_time_data["alerts"].extend(alerts)
            
            # 최근 10개 알림만 유지
            if len(real_time_data["alerts"]) > 10:
                real_time_data["alerts"] = real_time_data["alerts"][-10:]
        
        def get_trending_searches(limit: int = 5) -> List[Dict[str, Any]]:
            """트렌딩 검색어 조회"""
            searches = real_time_data["trending_searches"]
            sorted_searches = sorted(searches.items(), key=lambda x: x[1], reverse=True)
            
            return [
                {"query": query, "count": count}
                for query, count in sorted_searches[:limit]
            ]
        
        # When: 실시간 데이터 업데이트 시뮬레이션
        
        # 활성 사용자 업데이트
        update_active_users(150)
        
        # 실시간 액션 추가
        actions = [
            {"action_type": "search", "query": "강남 맛집", "user_id": "user-1"},
            {"action_type": "search", "query": "홍대 카페", "user_id": "user-2"},
            {"action_type": "search", "query": "강남 맛집", "user_id": "user-3"},
            {"action_type": "view", "place_id": "place-1", "user_id": "user-1"},
            {"action_type": "search", "query": "이태원 술집", "user_id": "user-4"},
            {"action_type": "search", "query": "강남 맛집", "user_id": "user-5"}
        ]
        
        for action in actions:
            add_live_action(action)
        
        # 알림 체크
        check_alerts({"active_users": 1500, "error_rate": 0.08})
        
        trending = get_trending_searches(3)
        
        # Then: 실시간 데이터 검증
        assert real_time_data["current_active_users"] == 150
        assert len(real_time_data["live_actions"]) == 6
        
        # 트렌딩 검색어 검증
        assert len(trending) == 3
        assert trending[0]["query"] == "강남 맛집"  # 3번 검색
        assert trending[0]["count"] == 3
        
        # 알림 검증
        assert len(real_time_data["alerts"]) == 2
        alert_types = [alert["type"] for alert in real_time_data["alerts"]]
        assert "high_traffic" in alert_types
        assert "high_error_rate" in alert_types
        
        # 실시간 액션 타임스탬프 확인
        for action in real_time_data["live_actions"]:
            assert "timestamp" in action
            assert isinstance(action["timestamp"], datetime)
        
        print("✅ 실시간 대시보드 업데이트 테스트 통과")


def main():
    """사용자 행동 분석 및 대시보드 시스템 테스트 실행"""
    print("👥 사용자 행동 분석 및 대시보드 시스템 TDD 테스트 시작")
    print("=" * 70)
    
    test_classes = [
        TestUserBehaviorTracking(),
        TestBehaviorAnalytics(),
        TestDashboardSystem()
    ]
    
    total_passed = 0
    total_failed = 0
    
    for test_instance in test_classes:
        class_name = test_instance.__class__.__name__
        print(f"\n📊 {class_name} 테스트 실행")
        print("-" * 50)
        
        test_methods = [method for method in dir(test_instance) 
                       if method.startswith('test_')]
        
        for method_name in test_methods:
            try:
                if hasattr(test_instance, 'setup_method'):
                    test_instance.setup_method()
                
                test_method = getattr(test_instance, method_name)
                test_method()
                total_passed += 1
            except Exception as e:
                print(f"❌ {method_name} 실패: {e}")
                total_failed += 1
    
    print(f"\n📈 사용자 행동 분석 테스트 결과:")
    print(f"   ✅ 통과: {total_passed}")
    print(f"   ❌ 실패: {total_failed}")
    print(f"   📊 전체: {total_passed + total_failed}")
    
    if total_failed == 0:
        print("🏆 모든 사용자 행동 분석 테스트 통과!")
        return True
    else:
        print(f"⚠️ {total_failed}개 테스트 실패")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)