"""
종합적인 알림 시스템 통합 테스트 (Task 2-2-6)
TDD Red phase: 알림 시스템 전체 플로우 테스트 작성
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.models.user import User


class TestNotificationSystemIntegration:
    """알림 시스템 통합 테스트 - 전체 플로우 검증"""

    def setup_method(self):
        """테스트 데이터 준비"""
        self.test_user_id = str(uuid4())
        self.test_notification_id = str(uuid4())

    @pytest.fixture
    def mock_user(self):
        """테스트 사용자 객체"""
        return User(
            id=self.test_user_id,
            email="test@example.com",
            firebase_uid="firebase_test_uid",
            is_active=True,
            created_at=datetime.now(),
        )

    @pytest.fixture
    def mock_fcm_response(self):
        """FCM 응답 모킹"""
        return {
            "name": "projects/test-project/messages/12345",
            "message_id": "fcm_msg_12345",
        }

    async def test_end_to_end_notification_flow(
        self, client: TestClient, mock_user, mock_fcm_response
    ):
        """
        Given: 사용자와 알림 데이터가 준비됨
        When: 알림 생성부터 전송까지 전체 플로우 실행
        Then: 모든 단계가 성공적으로 완료됨
        """
        with patch(
            "app.services.fcm_service.FCMService.send_notification",
            new_callable=AsyncMock,
        ) as mock_fcm:
            mock_fcm.return_value = mock_fcm_response

            # Given: 알림 생성 데이터
            notification_data = {
                "user_id": self.test_user_id,
                "title": "데이트 코스 추천",
                "body": "오늘 저녁 홍대 데이트 어때요?",
                "notification_type": "course_recommendation",
                "priority": "normal",
                "data": {"course_id": "course_123"},
            }

            # When: 알림 생성 API 호출
            response = client.post(
                "/api/v1/notifications/send",
                json=notification_data,
            )

            # Then: 성공적인 응답
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "notification_id" in data
            assert data["status"] == "sent"

            # FCM 서비스 호출 확인
            mock_fcm.assert_called_once()

    async def test_bulk_notification_sending(
        self, client: TestClient, mock_fcm_response
    ):
        """
        Given: 여러 사용자 대상 알림 데이터
        When: 대량 알림 전송 API 호출
        Then: 모든 사용자에게 알림 전송 성공
        """
        with patch(
            "app.services.fcm_service.FCMService.send_bulk_notifications",
            new_callable=AsyncMock,
        ) as mock_bulk_fcm:
            mock_bulk_fcm.return_value = {"success_count": 3, "failure_count": 0}

            # Given: 대량 알림 데이터
            bulk_data = {
                "user_ids": [str(uuid4()) for _ in range(3)],
                "title": "주말 데이트 추천",
                "body": "이번 주말 특별한 장소를 추천해드려요!",
                "notification_type": "weekend_recommendation",
            }

            # When: 대량 알림 전송
            response = client.post(
                "/api/v1/notifications/send-bulk",
                json=bulk_data,
            )

            # Then: 성공적인 대량 전송
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success_count"] == 3
            assert data["failure_count"] == 0

    async def test_scheduled_notification_creation_and_execution(
        self, client: TestClient, mock_user, mock_fcm_response
    ):
        """
        Given: 예약 알림 데이터
        When: 예약 알림 생성 후 스케줄러 실행
        Then: 예약된 시간에 알림 전송 성공
        """
        # Given: 1시간 후 예약 알림
        scheduled_time = datetime.now() + timedelta(hours=1)
        notification_data = {
            "user_id": self.test_user_id,
            "title": "데이트 출발 알림",
            "body": "1시간 후 데이트 시간입니다!",
            "notification_type": "departure_reminder",
            "scheduled_at": scheduled_time.isoformat(),
        }

        # When: 예약 알림 생성
        response = client.post(
            "/api/v1/notifications/schedule",
            json=notification_data,
        )

        # Then: 예약 알림 생성 성공
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert "notification_id" in data
        assert data["status"] == "scheduled"
        assert data["scheduled_at"] == scheduled_time.isoformat()

        # When: 스케줄러 실행 (시뮬레이션)
        with patch(
            "app.services.notification_scheduler.NotificationScheduler.process_scheduled_notifications",
            new_callable=AsyncMock,
        ) as mock_scheduler:
            mock_scheduler.return_value = {"processed": 1, "failed": 0}

            scheduler_response = client.post("/api/v1/notifications/process-scheduled")

            # Then: 스케줄러 실행 성공
            assert scheduler_response.status_code == status.HTTP_200_OK

    async def test_personalized_notification_generation(
        self, client: TestClient, mock_user
    ):
        """
        Given: 사용자 개인화 데이터
        When: 개인화 알림 생성 요청
        Then: 사용자 맞춤 알림 콘텐츠 생성
        """
        # Given: 개인화 알림 요청 데이터
        personalized_data = {
            "user_id": self.test_user_id,
            "template_name": "course_recommendation",
            "personalization_level": "high",
            "context": {
                "weather": {"condition": "rain", "temperature": 15},
                "time_of_day": "evening",
                "location": {"district": "홍대", "lat": 37.5563, "lng": 126.9225},
            },
        }

        # When: 개인화 알림 생성
        response = client.post(
            "/api/v1/notifications/personalized",
            json=personalized_data,
        )

        # Then: 개인화 알림 생성 성공
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "personalization_applied" in data
        assert data["personalization_applied"] is True
        assert "홍대" in data["content"]["body"]
        assert "비" in data["content"]["body"]  # 날씨 반영

    async def test_ab_testing_notification_variants(
        self, client: TestClient, mock_user
    ):
        """
        Given: A/B 테스트 설정된 알림
        When: 사용자별 알림 전송
        Then: 사용자마다 다른 변형 알림 수신
        """
        # Given: A/B 테스트 생성
        ab_test_data = {
            "test_name": "greeting_style_test",
            "variants": [
                {"name": "formal", "greeting": "안녕하세요"},
                {"name": "casual", "greeting": "안녕!"},
            ],
            "traffic_split": [0.5, 0.5],
        }

        test_response = client.post(
            "/api/v1/ab-tests/create",
            json=ab_test_data,
        )
        assert test_response.status_code == status.HTTP_201_CREATED

        # When: A/B 테스트 적용된 알림 전송
        notification_data = {
            "user_id": self.test_user_id,
            "template_name": "greeting_notification",
            "ab_test_name": "greeting_style_test",
        }

        response = client.post(
            "/api/v1/notifications/ab-test-send",
            json=notification_data,
        )

        # Then: A/B 테스트 변형 적용된 알림 생성
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "ab_test_variant" in data
        assert data["ab_test_variant"] in ["formal", "casual"]

    async def test_notification_analytics_tracking(self, client: TestClient, mock_user):
        """
        Given: 전송된 알림
        When: 사용자 상호작용 발생
        Then: 분석 데이터 정확히 수집됨
        """
        # Given: 알림 전송
        notification_data = {
            "user_id": self.test_user_id,
            "title": "테스트 알림",
            "body": "분석 테스트용 알림입니다.",
        }

        send_response = client.post(
            "/api/v1/notifications/send",
            json=notification_data,
        )
        notification_id = send_response.json()["notification_id"]

        # When: 사용자 상호작용 기록
        interaction_data = {
            "notification_id": notification_id,
            "user_id": self.test_user_id,
            "interaction_type": "opened",
            "timestamp": datetime.now().isoformat(),
        }

        interaction_response = client.post(
            "/api/v1/notifications/interactions",
            json=interaction_data,
        )

        # Then: 상호작용 기록 성공
        assert interaction_response.status_code == status.HTTP_201_CREATED

        # When: 분석 데이터 조회
        analytics_response = client.get(
            f"/api/v1/notifications/analytics?user_id={self.test_user_id}"
        )

        # Then: 분석 데이터 정확히 반영
        assert analytics_response.status_code == status.HTTP_200_OK
        analytics_data = analytics_response.json()
        assert analytics_data["total_sent"] >= 1
        assert analytics_data["total_opened"] >= 1

    async def test_notification_failure_handling_and_retry(
        self, client: TestClient, mock_user
    ):
        """
        Given: FCM 전송 실패 상황
        When: 알림 전송 시도
        Then: 실패 처리 및 재시도 로직 동작
        """
        # Given: FCM 전송 실패 시뮬레이션
        with patch(
            "app.services.fcm_service.FCMService.send_notification",
            new_callable=AsyncMock,
        ) as mock_fcm:
            mock_fcm.side_effect = Exception("FCM connection failed")

            notification_data = {
                "user_id": self.test_user_id,
                "title": "실패 테스트 알림",
                "body": "FCM 실패 상황 테스트",
            }

            # When: 알림 전송 시도
            response = client.post(
                "/api/v1/notifications/send",
                json=notification_data,
            )

            # Then: 실패 응답 및 재시도 큐 등록 확인
            # (구현에 따라 500 또는 202 응답 가능)
            assert response.status_code in [
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                status.HTTP_202_ACCEPTED,
            ]

            if response.status_code == status.HTTP_202_ACCEPTED:
                data = response.json()
                assert data["status"] == "queued_for_retry"

    async def test_notification_settings_integration(
        self, client: TestClient, mock_user
    ):
        """
        Given: 사용자 알림 설정
        When: 알림 전송 시도
        Then: 설정에 따른 알림 필터링 동작
        """
        # Given: 사용자 알림 설정 (특정 타입 비활성화)
        settings_data = {
            "user_id": self.test_user_id,
            "push_enabled": True,
            "course_recommendations_enabled": False,  # 코스 추천 알림 비활성화
            "quiet_hours_start": "23:00",
            "quiet_hours_end": "08:00",
        }

        settings_response = client.post(
            "/api/v1/notifications/settings",
            json=settings_data,
        )
        assert settings_response.status_code == status.HTTP_200_OK

        # When: 비활성화된 타입의 알림 전송 시도
        notification_data = {
            "user_id": self.test_user_id,
            "title": "코스 추천",
            "body": "새로운 코스를 추천해드려요!",
            "notification_type": "course_recommendation",
        }

        response = client.post(
            "/api/v1/notifications/send",
            json=notification_data,
        )

        # Then: 알림 차단 또는 필터링 처리
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST]

        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            assert data["status"] in ["blocked", "filtered"]

    async def test_ml_timing_optimization_integration(
        self, client: TestClient, mock_user
    ):
        """
        Given: ML 타이밍 최적화 활성화
        When: 개인화 알림 전송 요청
        Then: 최적화된 시간으로 예약 전송
        """
        # Given: ML 최적화 설정 활성화
        optimization_data = {
            "user_id": self.test_user_id,
            "enable_timing_optimization": True,
            "notification_type": "course_recommendation",
        }

        # When: 최적화된 알림 전송 요청
        response = client.post(
            "/api/v1/notifications/optimized-send",
            json=optimization_data,
        )

        # Then: 최적화된 시간으로 알림 예약
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "optimized_time" in data
        assert "confidence_score" in data
        assert data["confidence_score"] >= 0.0

    async def test_notification_template_system_integration(
        self, client: TestClient, mock_user
    ):
        """
        Given: 알림 템플릿 시스템
        When: 템플릿 기반 알림 생성
        Then: 변수가 올바르게 치환된 알림 생성
        """
        # Given: 알림 템플릿 생성
        template_data = {
            "name": "course_invitation",
            "title_template": "{{friend_name}}님이 {{course_name}} 코스를 공유했어요!",
            "body_template": "{{course_description}} 함께 가보실래요?",
            "notification_type": "course_share",
            "required_variables": ["friend_name", "course_name", "course_description"],
        }

        template_response = client.post(
            "/api/v1/notification-templates",
            json=template_data,
        )
        assert template_response.status_code == status.HTTP_201_CREATED

        # When: 템플릿 기반 알림 전송
        templated_notification = {
            "user_id": self.test_user_id,
            "template_name": "course_invitation",
            "variables": {
                "friend_name": "김철수",
                "course_name": "홍대 데이트 코스",
                "course_description": "로맨틱한 카페와 맛집이 있는 홍대 코스",
            },
        }

        response = client.post(
            "/api/v1/notifications/template-send",
            json=templated_notification,
        )

        # Then: 변수가 치환된 알림 생성
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "김철수" in data["rendered_content"]["title"]
        assert "홍대 데이트 코스" in data["rendered_content"]["title"]

    async def test_notification_history_and_status_tracking(
        self, client: TestClient, mock_user
    ):
        """
        Given: 여러 알림 전송
        When: 알림 히스토리 조회
        Then: 정확한 전송 이력 및 상태 조회
        """
        # Given: 여러 알림 전송
        notifications = []
        for i in range(3):
            notification_data = {
                "user_id": self.test_user_id,
                "title": f"테스트 알림 {i + 1}",
                "body": f"{i + 1}번째 테스트 알림입니다.",
            }

            response = client.post(
                "/api/v1/notifications/send",
                json=notification_data,
            )
            if response.status_code == status.HTTP_200_OK:
                notifications.append(response.json()["notification_id"])

        # When: 알림 히스토리 조회
        history_response = client.get(
            f"/api/v1/notifications/history?user_id={self.test_user_id}&limit=10"
        )

        # Then: 정확한 히스토리 조회
        assert history_response.status_code == status.HTTP_200_OK
        history_data = history_response.json()
        assert len(history_data["notifications"]) >= len(notifications)

        # 각 알림의 상태 확인
        for notification in history_data["notifications"]:
            assert "status" in notification
            assert notification["status"] in ["sent", "delivered", "failed", "queued"]

    async def test_notification_system_performance_under_load(self, client: TestClient):
        """
        Given: 대량의 동시 알림 요청
        When: 시스템 부하 테스트
        Then: 성능 저하 없이 처리
        """
        # Given: 100개의 동시 알림 요청 데이터
        user_ids = [str(uuid4()) for _ in range(100)]

        # When: 대량 알림 전송 (성능 테스트)
        bulk_data = {
            "user_ids": user_ids,
            "title": "성능 테스트 알림",
            "body": "대량 전송 테스트입니다.",
            "notification_type": "performance_test",
        }

        with patch(
            "app.services.fcm_service.FCMService.send_bulk_notifications",
            new_callable=AsyncMock,
        ) as mock_bulk:
            mock_bulk.return_value = {"success_count": 100, "failure_count": 0}

            import time

            start_time = time.time()

            response = client.post(
                "/api/v1/notifications/send-bulk",
                json=bulk_data,
            )

            end_time = time.time()
            processing_time = end_time - start_time

            # Then: 성능 기준 만족 (5초 이내 처리)
            assert response.status_code == status.HTTP_200_OK
            assert processing_time < 5.0

            data = response.json()
            assert data["success_count"] == 100
            assert data["failure_count"] == 0
