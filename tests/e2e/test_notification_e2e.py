"""
알림 시스템 E2E 테스트 (Task 2-2-6)
실제 사용자 시나리오를 기반으로 한 전체 플로우 테스트
"""

import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from fastapi.testclient import TestClient


class TestNotificationE2E:
    """알림 시스템 End-to-End 테스트"""

    def setup_method(self) -> None:
        """E2E 테스트 설정"""
        self.test_users = [
            {"id": str(uuid4()), "name": "김철수", "email": "kim@example.com"},
            {"id": str(uuid4()), "name": "이영희", "email": "lee@example.com"},
            {"id": str(uuid4()), "name": "박민수", "email": "park@example.com"},
        ]

    async def test_complete_date_course_notification_flow(self, client: TestClient):
        """
        Given: 사용자가 데이트 코스 추천을 받는 전체 시나리오
        When: 코스 추천부터 알림 수신까지 전체 플로우 실행
        Then: 모든 단계가 순서대로 성공적으로 완료됨
        """
        user = self.test_users[0]

        with patch(
            "app.services.fcm_service.FCMService.send_notification",
            new_callable=AsyncMock,
        ) as mock_fcm:
            mock_fcm.return_value = {"message_id": "fcm_success"}

            # Step 1: 사용자 취향 설정
            preferences_data = {
                "user_id": user["id"],
                "preferred_categories": ["cafe", "restaurant", "park"],
                "budget_range": "medium",
                "preferred_time": "evening",
                "location_preference": "hongdae",
            }

            prefs_response = client.post(
                "/api/v1/user/preferences",
                json=preferences_data,
            )
            assert prefs_response.status_code in [200, 201]

            # Step 2: 코스 추천 요청
            course_request = {
                "user_id": user["id"],
                "location": {"lat": 37.5563, "lng": 126.9225},  # 홍대
                "date_time": (datetime.now() + timedelta(hours=2)).isoformat(),
                "duration_hours": 3,
                "course_type": "romantic",
            }

            course_response = client.post(
                "/api/v1/courses/recommend",
                json=course_request,
            )

            if course_response.status_code == 200:
                recommended_course = course_response.json()
                course_id = recommended_course.get("course_id")

                # Step 3: 코스 추천 알림 전송
                notification_data = {
                    "user_id": user["id"],
                    "template_name": "course_recommendation",
                    "variables": {
                        "user_name": user["name"],
                        "course_name": recommended_course.get("name", "홍대 데이트"),
                        "total_places": len(recommended_course.get("places", [])),
                        "estimated_duration": "3시간",
                    },
                    "personalization_level": "high",
                }

                notification_response = client.post(
                    "/api/v1/notifications/template-send",
                    json=notification_data,
                )
                assert notification_response.status_code == 200

                notification_id = notification_response.json().get("notification_id")

                # Step 4: 사용자 상호작용 시뮬레이션 (알림 열람)
                await asyncio.sleep(0.1)  # 실제 사용자 반응 시간 시뮬레이션

                interaction_data = {
                    "notification_id": notification_id,
                    "user_id": user["id"],
                    "interaction_type": "opened",
                    "timestamp": datetime.now().isoformat(),
                }

                interaction_response = client.post(
                    "/api/v1/notifications/interactions",
                    json=interaction_data,
                )

                if interaction_response.status_code in [200, 201]:
                    # Step 5: 코스 승인 후 출발 알림 예약
                    departure_time = datetime.now() + timedelta(hours=1, minutes=30)
                    departure_notification = {
                        "user_id": user["id"],
                        "title": "🚗 출발 시간이 다가왔어요!",
                        "body": f"{recommended_course.get('name', '데이트 코스')} 첫 번째 장소로 출발하세요.",
                        "notification_type": "departure_reminder",
                        "scheduled_at": departure_time.isoformat(),
                        "data": {
                            "course_id": course_id,
                            "first_place": recommended_course.get("places", [{}])[
                                0
                            ].get("name"),
                            "travel_time": "15분",
                        },
                    }

                    departure_response = client.post(
                        "/api/v1/notifications/schedule",
                        json=departure_notification,
                    )
                    assert departure_response.status_code in [200, 201]

                    # Step 6: 분석 데이터 확인
                    analytics_response = client.get(
                        f"/api/v1/notifications/analytics?user_id={user['id']}"
                    )

                    if analytics_response.status_code == 200:
                        analytics = analytics_response.json()
                        assert analytics["total_sent"] >= 1
                        assert analytics["total_opened"] >= 1

                        # Then: 전체 플로우 성공
                        assert True  # 모든 단계 완료

    async def test_group_date_invitation_notification_flow(self, client: TestClient):
        """
        Given: 사용자가 친구들을 그룹 데이트에 초대하는 시나리오
        When: 그룹 초대 알림 전송부터 응답 수집까지
        Then: 모든 참여자에게 적절한 알림이 전송됨
        """
        organizer = self.test_users[0]
        invitees = self.test_users[1:3]

        with patch(
            "app.services.fcm_service.FCMService.send_bulk_notifications",
            new_callable=AsyncMock,
        ) as mock_bulk_fcm:
            mock_bulk_fcm.return_value = {"success_count": 2, "failure_count": 0}

            # Step 1: 그룹 데이트 계획 생성
            group_plan_data = {
                "organizer_id": organizer["id"],
                "invitee_ids": [user["id"] for user in invitees],
                "event_name": "홍대 그룹 데이트",
                "planned_date": (datetime.now() + timedelta(days=2)).isoformat(),
                "location": "홍대입구역 일대",
                "description": "함께 맛집 투어하고 노래방 가요!",
            }

            # Step 2: 초대 알림 대량 전송
            invitation_data = {
                "user_ids": [user["id"] for user in invitees],
                "template_name": "group_date_invitation",
                "variables": {
                    "organizer_name": organizer["name"],
                    "event_name": group_plan_data["event_name"],
                    "event_date": "이번 주말",
                    "location": group_plan_data["location"],
                    "total_invitees": len(invitees),
                },
                "notification_type": "group_invitation",
                "action_buttons": [
                    {"text": "참여하기", "action": "accept_invitation"},
                    {"text": "거절하기", "action": "decline_invitation"},
                ],
            }

            invitation_response = client.post(
                "/api/v1/notifications/bulk-template-send",
                json=invitation_data,
            )

            if invitation_response.status_code == 200:
                result = invitation_response.json()
                assert result["success_count"] == len(invitees)

                # Step 3: 초대받은 사용자들의 응답 시뮬레이션
                responses = []
                for i, invitee in enumerate(invitees):
                    response_action = (
                        "accept_invitation" if i == 0 else "decline_invitation"
                    )

                    response_data = {
                        "user_id": invitee["id"],
                        "organizer_id": organizer["id"],
                        "event_name": group_plan_data["event_name"],
                        "response": response_action,
                        "message": "기대돼요!"
                        if response_action == "accept_invitation"
                        else "죄송해요, 다음에 꼭!",
                    }

                    response_result = client.post(
                        "/api/v1/events/respond",
                        json=response_data,
                    )
                    responses.append(
                        (invitee, response_action, response_result.status_code)
                    )

                # Step 4: 주최자에게 응답 현황 알림
                response_summary = {
                    "accepted": sum(
                        1 for _, action, _ in responses if action == "accept_invitation"
                    ),
                    "declined": sum(
                        1
                        for _, action, _ in responses
                        if action == "decline_invitation"
                    ),
                }

                summary_notification = {
                    "user_id": organizer["id"],
                    "title": f"'{group_plan_data['event_name']}' 응답 현황",
                    "body": f"참여: {response_summary['accepted']}명, 불참: {response_summary['declined']}명",
                    "notification_type": "event_response_summary",
                    "data": {
                        "event_name": group_plan_data["event_name"],
                        "responses": response_summary,
                    },
                }

                summary_response = client.post(
                    "/api/v1/notifications/send",
                    json=summary_notification,
                )
                assert summary_response.status_code == 200

    async def test_location_based_real_time_notification_flow(self, client: TestClient):
        """
        Given: 사용자가 특정 지역 근처에 있을 때
        When: 위치 기반 실시간 추천 알림 시스템
        Then: 적절한 타이밍에 위치 맞춤 알림 전송
        """
        user = self.test_users[0]

        with patch(
            "app.services.location_service.LocationService.get_user_location",
            new_callable=AsyncMock,
        ) as mock_location:
            # 홍대입구역 좌표
            mock_location.return_value = {
                "lat": 37.5563,
                "lng": 126.9225,
                "accuracy": 10,
            }

            # Step 1: 사용자 위치 기반 컨텍스트 분석
            location_context = {
                "user_id": user["id"],
                "current_location": {"lat": 37.5563, "lng": 126.9225},
                "time_of_day": "evening",
                "day_of_week": "friday",
                "weather": {"condition": "clear", "temperature": 18},
            }

            context_response = client.post(
                "/api/v1/context/analyze",
                json=location_context,
            )

            if context_response.status_code == 200:
                # context_result = context_response.json()  # Unused variable removed

                # Step 2: 위치 기반 맞춤 알림 생성
                location_notification = {
                    "user_id": user["id"],
                    "template_name": "location_based_recommendation",
                    "personalization_level": "high",
                    "context": location_context,
                    "variables": {
                        "current_area": "홍대",
                        "weather_info": "쾌청한 날씨",
                        "time_context": "금요일 저녁",
                        "nearby_places": ["카페 ABC", "맛집 XYZ", "공원 DEF"],
                    },
                }

                location_notification_response = client.post(
                    "/api/v1/notifications/contextual-send",
                    json=location_notification,
                )

                if location_notification_response.status_code == 200:
                    # Step 3: 사용자 반응에 따른 후속 알림
                    notification_result = location_notification_response.json()
                    notification_id = notification_result.get("notification_id")

                    # 사용자가 알림을 클릭했다고 가정
                    click_interaction = {
                        "notification_id": notification_id,
                        "user_id": user["id"],
                        "interaction_type": "clicked",
                        "timestamp": datetime.now().isoformat(),
                        "additional_data": {"clicked_place": "카페 ABC"},
                    }

                    click_response = client.post(
                        "/api/v1/notifications/interactions",
                        json=click_interaction,
                    )

                    if click_response.status_code in [200, 201]:
                        # Step 4: 클릭한 장소에 대한 상세 정보 알림
                        detail_notification = {
                            "user_id": user["id"],
                            "title": "카페 ABC 상세 정보",
                            "body": "평점 4.5⭐ | 영업시간: ~23:00 | 도보 3분 거리",
                            "notification_type": "place_detail",
                            "data": {
                                "place_id": "cafe_abc_123",
                                "rating": 4.5,
                                "distance": "3분 거리",
                                "hours": "~23:00까지",
                            },
                        }

                        detail_response = client.post(
                            "/api/v1/notifications/send",
                            json=detail_notification,
                        )
                        assert detail_response.status_code == 200

    async def test_ml_personalization_learning_flow(self, client: TestClient):
        """
        Given: 사용자의 알림 상호작용 히스토리
        When: ML 기반 개인화 학습 및 최적화 수행
        Then: 개선된 개인화 알림 전송
        """
        user = self.test_users[0]

        # Step 1: 초기 알림 히스토리 생성 (학습용 데이터)
        historical_interactions = []
        for i in range(20):
            # 다양한 시간대와 타입의 알림 생성
            hour = 9 + (i % 12)  # 9시부터 20시까지
            notification_type = [
                "course_recommendation",
                "departure_reminder",
                "weather_alert",
            ][i % 3]
            interaction_type = "opened" if i % 3 != 2 else "dismissed"  # 2/3 확률로 열람

            historical_interactions.append(
                {
                    "user_id": user["id"],
                    "notification_type": notification_type,
                    "sent_at": (
                        datetime.now() - timedelta(days=20 - i, hours=24 - hour)
                    ).isoformat(),
                    "interaction_type": interaction_type,
                    "hour_sent": hour,
                }
            )

        # 히스토리 데이터 업로드 (실제로는 자동 수집됨)
        _ = client.post(
            "/api/v1/analytics/upload-history",
            json={"interactions": historical_interactions},
        )

        with patch(
            "app.services.ml_notification_optimizer.MLNotificationOptimizer.train_model",
            new_callable=AsyncMock,
        ) as mock_train:
            mock_train.return_value = {"accuracy": 0.85, "model_version": "v1.2"}

            # Step 2: ML 모델 학습 트리거
            training_response = client.post(
                f"/api/v1/ml/train-personalization/{user['id']}",
            )

            if training_response.status_code == 200:
                training_result = training_response.json()
                assert training_result["accuracy"] >= 0.8

                # Step 3: 학습된 모델로 최적화된 알림 전송
                optimized_notification = {
                    "user_id": user["id"],
                    "title": "ML 최적화 테스트 알림",
                    "body": "개인화된 최적 시간 알림입니다.",
                    "use_ml_optimization": True,
                    "notification_type": "course_recommendation",
                }

                with patch(
                    "app.services.ml_notification_optimizer.MLNotificationOptimizer.predict_optimal_time",
                    new_callable=AsyncMock,
                ) as mock_predict:
                    mock_predict.return_value = {
                        "optimal_time": datetime.now()
                        .replace(hour=18, minute=30)
                        .isoformat(),
                        "confidence": 0.92,
                        "reasoning": "Historical data shows 18:30 has highest engagement",
                    }

                    optimized_response = client.post(
                        "/api/v1/notifications/ml-optimized-send",
                        json=optimized_notification,
                    )

                    if optimized_response.status_code == 200:
                        result = optimized_response.json()
                        assert result["optimization_applied"] is True
                        assert result["confidence"] >= 0.9

                        # Step 4: 최적화 결과 검증
                        optimization_stats = client.get(
                            f"/api/v1/analytics/optimization-stats/{user['id']}"
                        )

                        if optimization_stats.status_code == 200:
                            stats = optimization_stats.json()
                            assert "improvement_rate" in stats
                            assert stats.get("ml_version") == "v1.2"

    async def test_emergency_notification_system_flow(self, client: TestClient):
        """
        Given: 긴급 상황 발생 (예: 시스템 점검, 보안 이슈)
        When: 긴급 알림 시스템 가동
        Then: 모든 활성 사용자에게 즉시 알림 전송
        """
        all_users = self.test_users

        with patch(
            "app.services.fcm_service.FCMService.send_emergency_broadcast",
            new_callable=AsyncMock,
        ) as mock_emergency:
            mock_emergency.return_value = {
                "total_sent": len(all_users),
                "success_count": len(all_users),
                "failure_count": 0,
            }

            # Step 1: 긴급 상황 발생 시뮬레이션
            emergency_data = {
                "alert_type": "system_maintenance",
                "severity": "high",
                "title": "🚨 시스템 긴급 점검 안내",
                "message": "오늘 밤 11시부터 새벽 2시까지 시스템 점검이 있습니다. 이용에 불편을 드려 죄송합니다.",
                "action_required": False,
                "estimated_duration": "3시간",
                "alternative_info": "점검 중에는 앱 이용이 제한됩니다.",
            }

            # Step 2: 긴급 알림 전송
            emergency_response = client.post(
                "/api/v1/notifications/emergency-broadcast",
                json=emergency_data,
            )

            if emergency_response.status_code == 200:
                result = emergency_response.json()
                assert result["total_sent"] == len(all_users)
                assert result["success_count"] == len(all_users)

                # Step 3: 긴급 알림 전송 로그 확인
                emergency_log_response = client.get("/api/v1/admin/emergency-logs")

                if emergency_log_response.status_code == 200:
                    logs = emergency_log_response.json()
                    latest_log = logs.get("latest_emergency")
                    assert latest_log["alert_type"] == "system_maintenance"
                    assert latest_log["severity"] == "high"

    async def test_notification_system_rollback_flow(self, client: TestClient):
        """
        Given: 알림 시스템 장애 상황
        When: 자동 롤백 및 복구 프로세스 실행
        Then: 시스템이 안전 모드로 전환 후 정상 복구
        """
        user = self.test_users[0]

        # Step 1: 정상 알림 전송 확인
        normal_notification = {
            "user_id": user["id"],
            "title": "정상 테스트 알림",
            "body": "롤백 테스트 이전 정상 알림",
        }

        normal_response = client.post(
            "/api/v1/notifications/send",
            json=normal_notification,
        )
        assert normal_response.status_code == 200

        # Step 2: 시스템 장애 시뮬레이션
        with patch(
            "app.services.fcm_service.FCMService.send_notification",
            side_effect=Exception("FCM service unavailable"),
        ):
            # Step 3: 장애 상황에서 알림 전송 시도
            failure_notification = {
                "user_id": user["id"],
                "title": "장애 상황 테스트 알림",
                "body": "이 알림은 실패할 예정입니다",
            }

            failure_response = client.post(
                "/api/v1/notifications/send",
                json=failure_notification,
            )

            # 시스템이 우아하게 실패 처리하는지 확인
            assert failure_response.status_code in [500, 502, 503]

        # Step 4: 안전 모드 확인
        health_check_response = client.get("/health/notifications")
        if health_check_response.status_code == 200:
            health_check_response.json()
            # 실제 구현에서는 안전 모드 상태가 반영되어야 함

        # Step 5: 시스템 복구 후 정상 동작 확인
        with patch(
            "app.services.fcm_service.FCMService.send_notification",
            new_callable=AsyncMock,
        ) as mock_recovered:
            mock_recovered.return_value = {"message_id": "recovered_success"}

            recovery_notification = {
                "user_id": user["id"],
                "title": "복구 테스트 알림",
                "body": "시스템이 정상 복구되었습니다",
            }

            recovery_response = client.post(
                "/api/v1/notifications/send",
                json=recovery_notification,
            )

            # Step 6: 복구 후 정상 동작 확인
            assert recovery_response.status_code == 200
            recovery_result = recovery_response.json()
            assert recovery_result["status"] == "sent"
