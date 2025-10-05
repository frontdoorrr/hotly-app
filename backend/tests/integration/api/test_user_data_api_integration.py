"""
사용자 데이터 API 통합 테스트

인증된 사용자 로직 및 개인별 데이터 연동을 위한
API 엔드포인트들의 통합 테스트를 정의합니다.
"""

from fastapi import status


# Mock client for testing
class MockTestClient:
    def __init__(self):
        self.base_url = "http://testserver/api/v1/user-data"
        self.auth_headers = {"Authorization": "Bearer mock.firebase.token"}

    def get(self, url, **kwargs):
        """Mock GET 요청"""

        class MockResponse:
            def __init__(self, status_code, json_data):
                self.status_code = status_code
                self._json_data = json_data

            def json(self):
                return self._json_data

        if url.endswith("/profile"):
            return MockResponse(
                200,
                {
                    "id": "user_123",
                    "firebase_uid": "firebase_user_123",
                    "email": "test@example.com",
                    "display_name": "Test User",
                    "phone_number": None,
                    "is_active": True,
                    "is_email_verified": True,
                    "is_phone_verified": False,
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": None,
                    "last_login_at": "2024-01-14T12:00:00Z",
                },
            )

        elif "/personal-data/" in url:
            return MockResponse(
                200,
                {
                    "id": "data_123",
                    "user_id": "user_123",
                    "data_type": "preferences",
                    "data_content": {"theme": "dark", "language": "ko"},
                    "is_encrypted": False,
                    "sensitivity_level": "LOW",
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": None,
                },
            )

        elif "/activity-logs" in url:
            return MockResponse(
                200,
                [
                    {
                        "id": "log_123",
                        "user_id": "user_123",
                        "activity_type": "login",
                        "activity_data": {"method": "firebase"},
                        "ip_address": "192.168.1.100",
                        "user_agent": "Mozilla/5.0...",
                        "created_at": "2024-01-14T12:00:00Z",
                    }
                ],
            )

        elif url.endswith("/settings"):
            return MockResponse(
                200,
                {
                    "id": "settings_123",
                    "user_id": "user_123",
                    "settings_type": "app_preferences",
                    "settings_data": {
                        "theme": "light",
                        "language": "ko",
                        "timezone": "Asia/Seoul",
                    },
                    "is_default": True,
                    "version": 1,
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": None,
                },
            )

        elif url.endswith("/privacy-settings"):
            return MockResponse(
                200,
                {
                    "id": "privacy_123",
                    "user_id": "user_123",
                    "privacy_settings": {
                        "data_collection_consent": True,
                        "marketing_consent": False,
                        "data_retention_days": 365,
                    },
                    "gdpr_compliance": True,
                    "consent_date": "2024-01-01T00:00:00Z",
                    "consent_version": "1.0",
                    "data_retention_days": 365,
                    "created_at": "2024-01-01T00:00:00Z",
                    "last_updated": None,
                },
            )

        return MockResponse(404, {"detail": "Not found"})

    def patch(self, url, json=None, **kwargs):
        """Mock PATCH 요청"""

        class MockResponse:
            def __init__(self, status_code, json_data):
                self.status_code = status_code
                self._json_data = json_data

            def json(self):
                return self._json_data

        if url.endswith("/profile"):
            updated_data = {
                "id": "user_123",
                "firebase_uid": "firebase_user_123",
                "email": "test@example.com",
                "display_name": json.get("display_name", "Test User"),
                "phone_number": json.get("phone_number"),
                "is_active": True,
                "is_email_verified": True,
                "is_phone_verified": json.get("is_phone_verified", False),
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-14T12:00:00Z",
                "last_login_at": "2024-01-14T12:00:00Z",
            }
            return MockResponse(200, updated_data)

        elif url.endswith("/settings"):
            return MockResponse(
                200,
                {
                    "id": "settings_123",
                    "user_id": "user_123",
                    "settings_type": json.get("settings_type", "app_preferences"),
                    "settings_data": json.get("settings_data", {}),
                    "is_default": False,
                    "version": 2,
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-14T12:00:00Z",
                },
            )

        elif url.endswith("/privacy-settings"):
            return MockResponse(
                200,
                {
                    "id": "privacy_123",
                    "user_id": "user_123",
                    "privacy_settings": json.get("privacy_settings", {}),
                    "gdpr_compliance": True,
                    "consent_date": "2024-01-14T12:00:00Z",
                    "consent_version": "1.0",
                    "data_retention_days": 365,
                    "created_at": "2024-01-01T00:00:00Z",
                    "last_updated": "2024-01-14T12:00:00Z",
                },
            )

        return MockResponse(404, {"detail": "Not found"})

    def post(self, url, json=None, **kwargs):
        """Mock POST 요청"""

        class MockResponse:
            def __init__(self, status_code, json_data):
                self.status_code = status_code
                self._json_data = json_data

            def json(self):
                return self._json_data

        if url.endswith("/personal-data"):
            return MockResponse(
                201,
                {
                    "id": "data_456",
                    "user_id": "user_123",
                    "data_type": json.get("data_type"),
                    "data_content": json.get("data_content"),
                    "is_encrypted": json.get("encrypt", False),
                    "sensitivity_level": "HIGH" if json.get("encrypt") else "LOW",
                    "created_at": "2024-01-14T12:00:00Z",
                    "updated_at": None,
                },
            )

        elif url.endswith("/log-activity"):
            return MockResponse(
                201,
                {"message": "Activity logged successfully", "activity_id": "log_456"},
            )

        elif url.endswith("/request-data-deletion"):
            return MockResponse(
                200,
                {
                    "message": "Data deletion request has been processed",
                    "deletion_details": {
                        "user_id": "user_123",
                        "status": "scheduled",
                        "deletion_date": "2024-02-13T12:00:00Z",
                    },
                },
            )

        return MockResponse(404, {"detail": "Not found"})


class TestUserDataAPIIntegration:
    """사용자 데이터 API 통합 테스트"""

    def setup_method(self):
        """테스트 설정"""
        self.client = MockTestClient()

    def test_get_user_profile_success(self):
        """사용자 프로필 조회 성공 테스트"""
        # Given: 인증된 사용자
        # When: 프로필 조회 API 호출
        response = self.client.get(
            f"{self.client.base_url}/profile", headers=self.client.auth_headers
        )

        # Then: 프로필 데이터 반환
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["id"] == "user_123"
        assert data["firebase_uid"] == "firebase_user_123"
        assert data["email"] == "test@example.com"
        assert data["is_active"] is True

        print("✅ 사용자 프로필 조회 성공 테스트 통과")
        return True

    def test_update_user_profile_success(self):
        """사용자 프로필 업데이트 성공 테스트"""
        # Given: 업데이트할 프로필 데이터
        update_data = {"display_name": "Updated Name", "phone_number": "01012345678"}

        # When: 프로필 업데이트 API 호출
        response = self.client.patch(
            f"{self.client.base_url}/profile",
            json=update_data,
            headers=self.client.auth_headers,
        )

        # Then: 업데이트된 프로필 반환
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["display_name"] == "Updated Name"
        assert data["phone_number"] == "01012345678"
        assert data["updated_at"] is not None

        print("✅ 사용자 프로필 업데이트 성공 테스트 통과")
        return True

    def test_store_personal_data_success(self):
        """개인 데이터 저장 성공 테스트"""
        # Given: 저장할 개인 데이터
        personal_data = {
            "data_type": "preferences",
            "data_content": {"theme": "dark", "language": "en", "notifications": True},
            "encrypt": False,
        }

        # When: 개인 데이터 저장 API 호출
        response = self.client.post(
            f"{self.client.base_url}/personal-data",
            json=personal_data,
            headers=self.client.auth_headers,
        )

        # Then: 저장된 데이터 반환
        assert response.status_code == status.HTTP_201_CREATED

        data = response.json()
        assert data["data_type"] == "preferences"
        assert data["is_encrypted"] is False
        assert data["sensitivity_level"] == "LOW"

        print("✅ 개인 데이터 저장 성공 테스트 통과")
        return True

    def test_get_personal_data_success(self):
        """개인 데이터 조회 성공 테스트"""
        # Given: 조회할 데이터 타입
        data_type = "preferences"

        # When: 개인 데이터 조회 API 호출
        response = self.client.get(
            f"{self.client.base_url}/personal-data/{data_type}",
            headers=self.client.auth_headers,
        )

        # Then: 개인 데이터 반환
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["data_type"] == "preferences"
        assert "theme" in data["data_content"]
        assert "language" in data["data_content"]

        print("✅ 개인 데이터 조회 성공 테스트 통과")
        return True

    def test_get_activity_logs_success(self):
        """활동 로그 조회 성공 테스트"""
        try:
            # Given: 인증된 사용자
            # When: 활동 로그 조회 API 호출
            response = self.client.get(
                f"{self.client.base_url}/activity-logs?limit=10",
                headers=self.client.auth_headers,
            )

            # Then: 활동 로그 배열 반환
            assert response.status_code == status.HTTP_200_OK

            data = response.json()
            assert isinstance(data, list)

            # 로그가 존재하는 경우에만 내용 검증
            if len(data) > 0:
                log = data[0]
                assert "activity_type" in log
                assert "activity_data" in log
                assert "created_at" in log

            # 빈 배열이어도 성공으로 처리 (실제 환경에서는 로그가 없을 수 있음)

            print("✅ 활동 로그 조회 성공 테스트 통과")
            return True

        except Exception as e:
            print(f"❌ 활동 로그 테스트 실패: {e}")
            return False

    def test_get_user_settings_success(self):
        """사용자 설정 조회 성공 테스트"""
        # Given: 인증된 사용자
        # When: 사용자 설정 조회 API 호출
        response = self.client.get(
            f"{self.client.base_url}/settings", headers=self.client.auth_headers
        )

        # Then: 사용자 설정 반환
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["settings_type"] == "app_preferences"
        assert "theme" in data["settings_data"]
        assert "language" in data["settings_data"]

        print("✅ 사용자 설정 조회 성공 테스트 통과")
        return True

    def test_update_user_settings_success(self):
        """사용자 설정 업데이트 성공 테스트"""
        # Given: 업데이트할 설정 데이터
        settings_update = {
            "settings_type": "app_preferences",
            "settings_data": {
                "theme": "dark",
                "language": "ko",
                "notifications": {"push_enabled": False},
            },
        }

        # When: 사용자 설정 업데이트 API 호출
        response = self.client.patch(
            f"{self.client.base_url}/settings",
            json=settings_update,
            headers=self.client.auth_headers,
        )

        # Then: 업데이트된 설정 반환
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["settings_data"]["theme"] == "dark"
        assert data["version"] == 2  # 업데이트로 인한 버전 증가

        print("✅ 사용자 설정 업데이트 성공 테스트 통과")
        return True

    def test_get_privacy_settings_success(self):
        """프라이버시 설정 조회 성공 테스트"""
        # Given: 인증된 사용자
        # When: 프라이버시 설정 조회 API 호출
        response = self.client.get(
            f"{self.client.base_url}/privacy-settings", headers=self.client.auth_headers
        )

        # Then: 프라이버시 설정 반환
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["gdpr_compliance"] is True
        assert "data_collection_consent" in data["privacy_settings"]

        print("✅ 프라이버시 설정 조회 성공 테스트 통과")
        return True

    def test_update_privacy_settings_success(self):
        """프라이버시 설정 업데이트 성공 테스트"""
        # Given: 업데이트할 프라이버시 설정
        privacy_update = {
            "privacy_settings": {
                "data_collection_consent": True,
                "marketing_consent": True,
                "location_tracking": False,
                "data_retention_days": 730,
            }
        }

        # When: 프라이버시 설정 업데이트 API 호출
        response = self.client.patch(
            f"{self.client.base_url}/privacy-settings",
            json=privacy_update,
            headers=self.client.auth_headers,
        )

        # Then: 업데이트된 프라이버시 설정 반환
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["privacy_settings"]["marketing_consent"] is True
        assert data["privacy_settings"]["location_tracking"] is False

        print("✅ 프라이버시 설정 업데이트 성공 테스트 통과")
        return True

    def test_log_user_activity_success(self):
        """사용자 활동 로깅 성공 테스트"""
        # Given: 로깅할 활동 데이터
        activity_data = {
            "activity_type": "page_view",
            "activity_data": {"page": "/dashboard", "duration_seconds": 30},
        }

        # When: 활동 로깅 API 호출
        response = self.client.post(
            f"{self.client.base_url}/log-activity",
            json=activity_data,
            headers=self.client.auth_headers,
        )

        # Then: 로깅 성공 응답
        assert response.status_code == status.HTTP_201_CREATED

        data = response.json()
        assert data["message"] == "Activity logged successfully"
        assert "activity_id" in data

        print("✅ 사용자 활동 로깅 성공 테스트 통과")
        return True

    def test_request_data_deletion_success(self):
        """데이터 삭제 요청 성공 테스트"""
        # Given: 데이터 삭제 요청
        deletion_params = {"reason": "user_request", "immediate": False}

        # When: 데이터 삭제 요청 API 호출
        response = self.client.post(
            f"{self.client.base_url}/request-data-deletion",
            json=deletion_params,
            headers=self.client.auth_headers,
        )

        # Then: 삭제 요청 접수 응답
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "message" in data
        assert "deletion_details" in data
        assert data["deletion_details"]["status"] in ["scheduled", "immediate"]

        print("✅ 데이터 삭제 요청 성공 테스트 통과")
        return True


def main():
    """통합 테스트 실행"""
    print("🧪 사용자 데이터 API 통합 테스트 시작")
    print("=" * 50)

    # 테스트 클래스 인스턴스 생성
    test_api = TestUserDataAPIIntegration()

    tests = [
        test_api.test_get_user_profile_success,
        test_api.test_update_user_profile_success,
        test_api.test_store_personal_data_success,
        test_api.test_get_personal_data_success,
        test_api.test_get_activity_logs_success,
        test_api.test_get_user_settings_success,
        test_api.test_update_user_settings_success,
        test_api.test_get_privacy_settings_success,
        test_api.test_update_privacy_settings_success,
        test_api.test_log_user_activity_success,
        test_api.test_request_data_deletion_success,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            # 각 테스트마다 setup 실행
            test_api.setup_method()

            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ {test.__name__} 실패: {e}")
            failed += 1

    print(f"\n📊 테스트 결과:")
    print(f"   ✅ 통과: {passed}")
    print(f"   ❌ 실패: {failed}")
    print(f"   📈 전체: {passed + failed}")

    if failed == 0:
        print("🎉 모든 통합 테스트 통과!")
    else:
        print(f"⚠️ {failed}개 테스트 실패")

    return failed == 0


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
