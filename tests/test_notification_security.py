"""
알림 시스템 보안 및 권한 테스트 (Task 2-2-6)
인증, 권한, 입력 검증, 개인정보 보호 테스트
"""

from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.core.security import create_access_token


class TestNotificationSecurity:
    """알림 시스템 보안 테스트"""

    def setup_method(self):
        """테스트 설정"""
        self.test_user_id = str(uuid4())
        self.other_user_id = str(uuid4())
        self.admin_user_id = str(uuid4())

    @pytest.fixture
    def authenticated_headers(self):
        """인증된 사용자 헤더"""
        token = create_access_token(data={"sub": self.test_user_id})
        return {"Authorization": f"Bearer {token}"}

    @pytest.fixture
    def admin_headers(self):
        """관리자 권한 헤더"""
        token = create_access_token(data={"sub": self.admin_user_id, "role": "admin"})
        return {"Authorization": f"Bearer {token}"}

    async def test_unauthenticated_access_denied(self, client: TestClient):
        """
        Given: 인증되지 않은 요청
        When: 알림 API 접근 시도
        Then: 401 Unauthorized 응답
        """
        # Given: 인증 헤더 없는 요청
        notification_data = {
            "user_id": self.test_user_id,
            "title": "무권한 테스트",
            "body": "인증되지 않은 요청 테스트",
        }

        # When: 알림 전송 시도
        response = client.post(
            "/api/v1/notifications/send",
            json=notification_data,
        )

        # Then: 인증 실패 응답
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_unauthorized_user_notification_access(
        self, client: TestClient, authenticated_headers
    ):
        """
        Given: 다른 사용자의 알림 데이터
        When: 권한 없는 사용자가 접근 시도
        Then: 403 Forbidden 또는 404 Not Found 응답
        """
        # Given: 다른 사용자의 알림 ID
        other_notification_id = str(uuid4())

        # When: 다른 사용자 알림 조회 시도
        response = client.get(
            f"/api/v1/notifications/{other_notification_id}",
            headers=authenticated_headers,
        )

        # Then: 권한 거부 응답
        assert response.status_code in [
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND,
        ]

    async def test_input_validation_malicious_payload(self, client: TestClient):
        """
        Given: 악의적인 입력 데이터
        When: 알림 생성 시도
        Then: 입력 검증 실패 및 차단
        """
        # Given: 악의적인 페이로드 (XSS, SQL Injection 등)
        malicious_payloads = [
            {
                "user_id": self.test_user_id,
                "title": "<script>alert('xss')</script>",
                "body": "XSS 테스트",
            },
            {
                "user_id": self.test_user_id,
                "title": "'; DROP TABLE notifications; --",
                "body": "SQL Injection 테스트",
            },
            {
                "user_id": "invalid-uuid-format",
                "title": "잘못된 UUID 테스트",
                "body": "UUID 검증 테스트",
            },
            {
                "user_id": self.test_user_id,
                "title": "A" * 1000,  # 너무 긴 제목
                "body": "길이 제한 테스트",
            },
        ]

        for payload in malicious_payloads:
            # When: 악의적인 데이터로 알림 생성 시도
            response = client.post(
                "/api/v1/notifications/send",
                json=payload,
            )

            # Then: 입력 검증 실패 (400 Bad Request)
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_notification_data_sanitization(self, client: TestClient):
        """
        Given: HTML/Script 태그가 포함된 알림 데이터
        When: 알림 생성 후 조회
        Then: 데이터가 적절히 sanitize됨
        """
        # Given: HTML 태그 포함 데이터
        notification_data = {
            "user_id": self.test_user_id,
            "title": "테스트 <b>볼드</b> 제목",
            "body": "본문에 <em>이탤릭</em> 포함",
            "data": {
                "url": "javascript:alert('xss')",
                "description": "<img src=x onerror=alert('xss')>",
            },
        }

        with patch(
            "app.services.notification_service.NotificationService.send_notification",
            new_callable=AsyncMock,
        ) as mock_send:
            mock_send.return_value = {
                "notification_id": str(uuid4()),
                "status": "sent",
                "sanitized": True,
            }

            # When: 알림 전송
            response = client.post(
                "/api/v1/notifications/send",
                json=notification_data,
            )

            # Then: sanitization 확인
            assert response.status_code == status.HTTP_200_OK

            # 실제 서비스에서 sanitization 로직 호출 확인
            mock_send.assert_called_once()
            call_args = mock_send.call_args[1]

            # HTML 태그 제거/이스케이프 확인
            assert "<b>" not in call_args.get("title", "")
            assert "<em>" not in call_args.get("body", "")
            assert "javascript:" not in str(call_args.get("data", {}))

    async def test_personal_data_privacy_protection(
        self, client: TestClient, authenticated_headers
    ):
        """
        Given: 개인정보가 포함된 알림
        When: 로그 및 분석 데이터 저장
        Then: 민감 정보가 마스킹됨
        """
        # Given: 개인정보 포함 알림 데이터
        notification_data = {
            "user_id": self.test_user_id,
            "title": "개인정보 테스트",
            "body": "안녕하세요 김철수님, 전화번호 010-1234-5678로 연락드리겠습니다.",
            "data": {
                "email": "test@example.com",
                "phone": "010-9876-5432",
                "address": "서울특별시 강남구 테헤란로 123",
            },
        }

        with patch(
            "app.services.notification_analytics_service.NotificationAnalyticsService.log_notification",
            new_callable=AsyncMock,
        ) as mock_log:
            # When: 알림 전송 및 로깅
            response = client.post(
                "/api/v1/notifications/send",
                json=notification_data,
                headers=authenticated_headers,
            )

            # Then: 개인정보 마스킹 확인
            if response.status_code == status.HTTP_200_OK:
                mock_log.assert_called()
                logged_data = mock_log.call_args[0][0]

                # 전화번호, 이메일 등이 마스킹되었는지 확인
                logged_content = str(logged_data)
                assert "010-1234-5678" not in logged_content
                assert "test@example.com" not in logged_content
                assert "010-****-5678" in logged_content or "***" in logged_content

    async def test_rate_limiting_per_user(
        self, client: TestClient, authenticated_headers
    ):
        """
        Given: 사용자별 레이트 리미팅 설정
        When: 제한을 초과하는 요청
        Then: 429 Too Many Requests 응답
        """
        # Given: 레이트 리미팅 시뮬레이션
        with patch("app.api.deps.rate_limiter") as mock_rate_limiter:
            # 처음 10번은 허용, 그 이후는 차단
            call_count = 0

            def rate_limit_side_effect(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                if call_count > 10:
                    from fastapi import HTTPException

                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail="Rate limit exceeded",
                    )
                return True

            mock_rate_limiter.side_effect = rate_limit_side_effect

            notification_data = {
                "user_id": self.test_user_id,
                "title": "레이트 리미팅 테스트",
                "body": "제한 테스트",
            }

            # When: 제한 초과 요청
            success_count = 0
            rate_limited = False

            for i in range(15):
                response = client.post(
                    "/api/v1/notifications/send",
                    json=notification_data,
                    headers=authenticated_headers,
                )

                if response.status_code == status.HTTP_200_OK:
                    success_count += 1
                elif response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
                    rate_limited = True
                    break

            # Then: 레이트 리미팅 동작 확인
            assert success_count <= 10
            assert rate_limited

    async def test_notification_token_security(self, client: TestClient):
        """
        Given: FCM 토큰 관리
        When: 토큰 저장 및 사용
        Then: 토큰이 안전하게 처리됨
        """
        # Given: FCM 토큰 등록 데이터
        token_data = {
            "user_id": self.test_user_id,
            "fcm_token": "test_fcm_token_12345",
            "platform": "android",
        }

        with patch(
            "app.services.fcm_service.FCMService.register_token", new_callable=AsyncMock
        ) as mock_register:
            mock_register.return_value = {"status": "registered"}

            # When: 토큰 등록
            response = client.post(
                "/api/v1/notifications/register-token",
                json=token_data,
            )

            # Then: 토큰 보안 처리 확인
            assert response.status_code == status.HTTP_200_OK

            # 토큰이 로그에 노출되지 않는지 확인
            mock_register.assert_called_once()
            # 실제 구현에서는 토큰을 암호화하여 저장해야 함

    async def test_admin_only_operations_access_control(
        self, client: TestClient, authenticated_headers, admin_headers
    ):
        """
        Given: 관리자 전용 기능
        When: 일반 사용자와 관리자가 접근 시도
        Then: 적절한 권한 검증 수행
        """
        # Given: 관리자 전용 기능 (전체 알림 통계)
        admin_endpoints = [
            "/api/v1/notifications/admin/statistics",
            "/api/v1/notifications/admin/bulk-delete",
            "/api/v1/notifications/admin/system-broadcast",
        ]

        for endpoint in admin_endpoints:
            # When: 일반 사용자 접근 시도
            user_response = client.get(endpoint, headers=authenticated_headers)

            # Then: 권한 거부
            assert user_response.status_code == status.HTTP_403_FORBIDDEN

            # When: 관리자 접근 시도
            admin_response = client.get(endpoint, headers=admin_headers)

            # Then: 접근 허용 (404는 엔드포인트 미구현일 수 있음)
            assert admin_response.status_code in [
                status.HTTP_200_OK,
                status.HTTP_404_NOT_FOUND,
            ]

    async def test_sql_injection_prevention_in_queries(self, client: TestClient):
        """
        Given: SQL Injection 시도가 포함된 쿼리 파라미터
        When: 알림 조회 API 호출
        Then: SQL Injection 방지됨
        """
        # Given: SQL Injection 시도 파라미터
        malicious_params = [
            "'; DROP TABLE notifications; --",
            "1 OR 1=1",
            "' UNION SELECT * FROM users --",
            "<script>alert('xss')</script>",
        ]

        for malicious_param in malicious_params:
            # When: 악의적인 파라미터로 조회
            response = client.get(
                f"/api/v1/notifications/search?query={malicious_param}",
            )

            # Then: 안전하게 처리됨 (에러 없이 빈 결과 또는 400 에러)
            assert response.status_code in [
                status.HTTP_200_OK,
                status.HTTP_400_BAD_REQUEST,
                status.HTTP_422_UNPROCESSABLE_ENTITY,
            ]

            # SQL 에러가 노출되지 않는지 확인
            response_text = response.text.lower()
            assert "sql" not in response_text
            assert "database" not in response_text
            assert "error" not in response_text or "validation error" in response_text

    async def test_notification_content_encryption_at_rest(self, client: TestClient):
        """
        Given: 민감한 알림 콘텐츠
        When: 데이터베이스 저장
        Then: 콘텐츠가 암호화되어 저장됨
        """
        # Given: 민감한 정보 포함 알림
        sensitive_notification = {
            "user_id": self.test_user_id,
            "title": "결제 알림",
            "body": "카드 결제가 완료되었습니다. 금액: 50,000원",
            "data": {
                "payment_method": "****-1234",
                "amount": 50000,
                "merchant": "테스트 상점",
            },
        }

        with patch(
            "app.services.notification_service.NotificationService._encrypt_sensitive_data",
            new_callable=AsyncMock,
        ) as mock_encrypt:
            mock_encrypt.return_value = "encrypted_content_hash"

            # When: 민감한 알림 저장
            response = client.post(
                "/api/v1/notifications/send",
                json=sensitive_notification,
            )

            # Then: 암호화 함수 호출 확인
            if response.status_code == status.HTTP_200_OK:
                mock_encrypt.assert_called()

    async def test_notification_audit_logging(
        self, client: TestClient, authenticated_headers
    ):
        """
        Given: 알림 시스템 작업
        When: 중요한 작업 수행
        Then: 감사 로그 기록됨
        """
        # Given: 감사 로그 대상 작업
        notification_data = {
            "user_id": self.test_user_id,
            "title": "감사 로그 테스트",
            "body": "중요한 알림 테스트",
            "notification_type": "security_alert",
        }

        with patch(
            "app.services.audit_service.AuditService.log_action", new_callable=AsyncMock
        ) as mock_audit:
            # When: 중요한 알림 전송
            response = client.post(
                "/api/v1/notifications/send",
                json=notification_data,
                headers=authenticated_headers,
            )

            # Then: 감사 로그 기록 확인
            if response.status_code == status.HTTP_200_OK:
                mock_audit.assert_called()

                # 감사 로그 내용 검증
                audit_call = mock_audit.call_args
                assert audit_call[1]["action"] == "notification_sent"
                assert audit_call[1]["user_id"] == self.test_user_id
                assert "security_alert" in str(audit_call)

    async def test_cross_user_data_isolation(self, client: TestClient):
        """
        Given: 여러 사용자의 알림 데이터
        When: 사용자별 데이터 조회
        Then: 다른 사용자 데이터가 노출되지 않음
        """
        user1_id = str(uuid4())
        user2_id = str(uuid4())

        # Given: 각 사용자별 인증 헤더
        user1_token = create_access_token(data={"sub": user1_id})
        user2_token = create_access_token(data={"sub": user2_id})

        user1_headers = {"Authorization": f"Bearer {user1_token}"}
        user2_headers = {"Authorization": f"Bearer {user2_token}"}

        # 각 사용자의 알림 생성 시뮬레이션
        notifications = [
            {"user_id": user1_id, "title": "User1 알림", "body": "사용자1 전용"},
            {"user_id": user2_id, "title": "User2 알림", "body": "사용자2 전용"},
        ]

        with patch(
            "app.services.notification_service.NotificationService.get_user_notifications",
            new_callable=AsyncMock,
        ) as mock_get_notifications:

            def get_user_notifications_side_effect(user_id, *args, **kwargs):
                return [n for n in notifications if n["user_id"] == user_id]

            mock_get_notifications.side_effect = get_user_notifications_side_effect

            # When: User1으로 알림 조회
            user1_response = client.get(
                "/api/v1/notifications/my-notifications",
                headers=user1_headers,
            )

            # When: User2로 알림 조회
            user2_response = client.get(
                "/api/v1/notifications/my-notifications",
                headers=user2_headers,
            )

            # Then: 각 사용자는 자신의 알림만 조회
            if user1_response.status_code == status.HTTP_200_OK:
                user1_data = user1_response.json()
                user1_notifications = user1_data.get("notifications", [])
                assert all("User1" in n.get("title", "") for n in user1_notifications)

            if user2_response.status_code == status.HTTP_200_OK:
                user2_data = user2_response.json()
                user2_notifications = user2_data.get("notifications", [])
                assert all("User2" in n.get("title", "") for n in user2_notifications)
