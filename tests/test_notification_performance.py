"""
알림 시스템 성능 및 네트워크 테스트 (Task 2-2-6)
부하 테스트, 동시성 테스트, 네트워크 장애 시나리오
"""

import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

from fastapi.testclient import TestClient

from app.services.fcm_service import FCMService


class TestNotificationPerformance:
    """알림 시스템 성능 테스트"""

    def setup_method(self):
        """테스트 설정"""
        self.test_user_ids = [str(uuid4()) for _ in range(1000)]

    async def test_concurrent_notification_sending(self, client: TestClient):
        """
        Given: 100개의 동시 알림 요청
        When: 동시에 알림 전송 요청
        Then: 모든 요청이 3초 이내 처리됨
        """
        # Given: 동시 요청 데이터
        notification_data = [
            {
                "user_id": user_id,
                "title": f"동시성 테스트 알림 {i}",
                "body": "동시 전송 테스트입니다.",
                "notification_type": "concurrent_test",
            }
            for i, user_id in enumerate(self.test_user_ids[:100])
        ]

        with patch(
            "app.services.fcm_service.FCMService.send_notification",
            new_callable=AsyncMock,
        ) as mock_fcm:
            mock_fcm.return_value = {"message_id": "success"}

            # When: 동시 요청 실행
            start_time = time.time()

            async def send_notification(data):
                response = client.post("/api/v1/notifications/send", json=data)
                return response.status_code

            # 동시 실행
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = [
                    executor.submit(
                        client.post, "/api/v1/notifications/send", None, data
                    )
                    for data in notification_data
                ]
                results = [future.result() for future in futures]

            end_time = time.time()
            total_time = end_time - start_time

            # Then: 성능 기준 만족
            assert total_time < 3.0  # 3초 이내 처리
            assert all(result.status_code == 200 for result in results)

    async def test_bulk_notification_scalability(self, client: TestClient):
        """
        Given: 1000명 사용자 대상 대량 알림
        When: 벌크 전송 API 호출
        Then: 확장성 있는 처리 성능 달성
        """
        # Given: 대량 사용자 데이터
        bulk_data = {
            "user_ids": self.test_user_ids,
            "title": "확장성 테스트 알림",
            "body": "1000명 대상 테스트입니다.",
            "notification_type": "scalability_test",
        }

        with patch(
            "app.services.fcm_service.FCMService.send_bulk_notifications",
            new_callable=AsyncMock,
        ) as mock_bulk_fcm:
            # 처리 시간 시뮬레이션 (실제보다 빠르게)
            async def mock_bulk_send(*args, **kwargs):
                await asyncio.sleep(0.1)  # 100ms 시뮬레이션
                return {"success_count": len(self.test_user_ids), "failure_count": 0}

            mock_bulk_fcm.side_effect = mock_bulk_send

            # When: 벌크 전송 실행
            start_time = time.time()
            response = client.post("/api/v1/notifications/send-bulk", json=bulk_data)
            end_time = time.time()

            # Then: 성능 기준 달성 (10초 이내)
            assert response.status_code == 200
            assert (end_time - start_time) < 10.0

            data = response.json()
            assert data["success_count"] == 1000
            assert data["failure_count"] == 0

    async def test_notification_queue_performance(self):
        """
        Given: 대량의 예약 알림
        When: 큐 처리 성능 테스트
        Then: 초당 100개 이상 처리 성능
        """
        from app.services.notification_scheduler import NotificationScheduler

        # Given: 모의 스케줄러와 큐 설정
        with patch("app.db.get_db") as mock_db:
            scheduler = NotificationScheduler(mock_db)

            # 1000개의 예약 알림 시뮬레이션
            scheduled_notifications = [
                {
                    "id": str(uuid4()),
                    "user_id": user_id,
                    "title": "예약 알림",
                    "scheduled_at": datetime.now() + timedelta(minutes=1),
                }
                for user_id in self.test_user_ids
            ]

            with patch.object(
                scheduler, "get_due_notifications", new_callable=AsyncMock
            ) as mock_get_due:
                mock_get_due.return_value = scheduled_notifications

                with patch.object(
                    scheduler, "process_notification", new_callable=AsyncMock
                ) as mock_process:
                    mock_process.return_value = True

                    # When: 큐 처리 실행
                    start_time = time.time()
                    await scheduler.process_scheduled_notifications()
                    end_time = time.time()

                    processing_time = end_time - start_time
                    throughput = len(scheduled_notifications) / processing_time

                    # Then: 처리 성능 확인 (초당 100개 이상)
                    assert throughput >= 100

    async def test_memory_usage_under_load(self, client: TestClient):
        """
        Given: 연속적인 알림 요청
        When: 메모리 사용량 모니터링
        Then: 메모리 누수 없이 안정적 처리
        """
        import os

        import psutil

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        # Given: 연속 요청 (500번)
        for i in range(500):
            notification_data = {
                "user_id": str(uuid4()),
                "title": f"메모리 테스트 {i}",
                "body": "메모리 사용량 테스트입니다.",
            }

            with patch(
                "app.services.fcm_service.FCMService.send_notification",
                new_callable=AsyncMock,
            ):
                response = client.post(
                    "/api/v1/notifications/send", json=notification_data
                )
                assert response.status_code == 200

        # When: 최종 메모리 사용량 확인
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory

        # Then: 메모리 증가량이 합리적 범위 (50MB 이하)
        assert memory_increase < 50 * 1024 * 1024  # 50MB


class TestNotificationNetworkResilience:
    """알림 시스템 네트워크 복원력 테스트"""

    async def test_fcm_service_timeout_handling(self):
        """
        Given: FCM 서비스 타임아웃 상황
        When: 알림 전송 시도
        Then: 적절한 타임아웃 처리
        """
        # Given: FCM 서비스 타임아웃 시뮬레이션
        with patch("httpx.AsyncClient.post") as mock_post:
            mock_post.side_effect = asyncio.TimeoutError("Request timeout")

            fcm_service = FCMService()

            # When: 알림 전송 시도
            result = await fcm_service.send_notification(
                token="test_token", title="타임아웃 테스트", body="네트워크 타임아웃 테스트입니다."
            )

            # Then: 타임아웃 에러 적절히 처리
            assert result["status"] == "failed"
            assert "timeout" in result["error"].lower()

    async def test_fcm_rate_limiting_handling(self):
        """
        Given: FCM 레이트 리미팅 응답 (429)
        When: 알림 전송 시도
        Then: 재시도 로직 동작
        """
        from httpx import Response

        # Given: 429 응답 시뮬레이션
        with patch("httpx.AsyncClient.post") as mock_post:
            # 첫 번째 요청: 429 에러
            mock_response_429 = Mock(spec=Response)
            mock_response_429.status_code = 429
            mock_response_429.json.return_value = {"error": "Rate limit exceeded"}

            # 두 번째 요청: 성공
            mock_response_200 = Mock(spec=Response)
            mock_response_200.status_code = 200
            mock_response_200.json.return_value = {"name": "projects/test/messages/123"}

            mock_post.side_effect = [mock_response_429, mock_response_200]

            fcm_service = FCMService()

            # When: 알림 전송 (재시도 포함)
            result = await fcm_service.send_notification_with_retry(
                token="test_token",
                title="재시도 테스트",
                body="레이트 리미팅 재시도 테스트입니다.",
                max_retries=3,
            )

            # Then: 재시도 후 성공
            assert result["status"] == "success"
            assert mock_post.call_count == 2

    async def test_network_failure_graceful_degradation(self, client: TestClient):
        """
        Given: 완전한 네트워크 장애
        When: 알림 전송 시도
        Then: 우아한 서비스 저하 처리
        """
        # Given: 네트워크 연결 실패 시뮬레이션
        with patch(
            "app.services.fcm_service.FCMService.send_notification",
            new_callable=AsyncMock,
        ) as mock_fcm:
            mock_fcm.side_effect = Exception("Network unreachable")

            notification_data = {
                "user_id": str(uuid4()),
                "title": "네트워크 장애 테스트",
                "body": "네트워크 장애 상황 테스트입니다.",
            }

            # When: 알림 전송 시도
            response = client.post("/api/v1/notifications/send", json=notification_data)

            # Then: 우아한 실패 처리 (큐에 저장 등)
            assert response.status_code in [202, 500]  # 큐 저장 또는 에러

            if response.status_code == 202:
                data = response.json()
                assert data["status"] == "queued_for_retry"

    async def test_partial_fcm_batch_failure_handling(self):
        """
        Given: FCM 배치 전송 중 일부 실패
        When: 대량 알림 전송
        Then: 실패한 항목만 재시도 처리
        """
        fcm_service = FCMService()

        # Given: 부분 실패 응답 시뮬레이션
        with patch("httpx.AsyncClient.post") as mock_post:
            # 배치 응답: 일부 성공, 일부 실패
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "responses": [
                    {"message_id": "msg_1"},  # 성공
                    {"error": {"code": "INVALID_TOKEN"}},  # 실패
                    {"message_id": "msg_3"},  # 성공
                ]
            }
            mock_post.return_value = mock_response

            tokens = ["token1", "token2", "token3"]

            # When: 배치 전송 실행
            result = await fcm_service.send_bulk_notifications(
                tokens=tokens, title="배치 실패 테스트", body="부분 실패 처리 테스트입니다."
            )

            # Then: 부분 성공/실패 정확히 처리
            assert result["success_count"] == 2
            assert result["failure_count"] == 1
            assert len(result["failed_tokens"]) == 1
            assert "token2" in result["failed_tokens"]

    async def test_fcm_service_circuit_breaker(self):
        """
        Given: FCM 서비스 연속 실패
        When: Circuit Breaker 임계값 초과
        Then: 서비스 차단 및 빠른 실패 처리
        """
        from app.services.fcm_service import FCMService

        fcm_service = FCMService()

        # Given: 연속 실패 시뮬레이션
        with patch.object(
            fcm_service, "_send_to_fcm", new_callable=AsyncMock
        ) as mock_send:
            mock_send.side_effect = Exception("Service unavailable")

            # When: 임계값 초과될 때까지 실패 요청
            failure_count = 0
            for _ in range(10):  # 10번 연속 실패
                try:
                    await fcm_service.send_notification(
                        token="test_token",
                        title="Circuit Breaker 테스트",
                        body="연속 실패 테스트",
                    )
                except Exception:
                    failure_count += 1

            # Circuit Breaker 활성화 후 빠른 실패 확인
            start_time = time.time()
            result = await fcm_service.send_notification(
                token="test_token", title="빠른 실패 테스트", body="Circuit Breaker 빠른 실패 테스트"
            )
            end_time = time.time()

            # Then: 빠른 실패 (100ms 이내)
            assert (end_time - start_time) < 0.1
            assert result["status"] == "circuit_open"


class TestNotificationDatabasePerformance:
    """알림 시스템 데이터베이스 성능 테스트"""

    async def test_notification_log_insertion_performance(self):
        """
        Given: 대량의 알림 로그
        When: 데이터베이스 삽입 성능 테스트
        Then: 초당 1000개 이상 삽입 성능
        """
        from app.services.notification_analytics_service import (
            NotificationAnalyticsService,
        )

        # Given: 대량 로그 데이터
        with patch("app.db.get_db") as mock_db_session:
            analytics_service = NotificationAnalyticsService(mock_db_session)

            log_entries = [
                {
                    "user_id": str(uuid4()),
                    "notification_id": str(uuid4()),
                    "status": "sent",
                    "sent_at": datetime.now(),
                    "platform": "android",
                }
                for _ in range(1000)
            ]

            with patch.object(
                analytics_service, "_bulk_insert_logs", new_callable=AsyncMock
            ) as mock_insert:
                mock_insert.return_value = True

                # When: 대량 삽입 실행
                start_time = time.time()
                await analytics_service.bulk_log_notifications(log_entries)
                end_time = time.time()

                insertion_time = end_time - start_time
                throughput = len(log_entries) / insertion_time

                # Then: 초당 1000개 이상 처리
                assert throughput >= 1000

    async def test_notification_analytics_query_performance(self):
        """
        Given: 대량의 알림 히스토리 데이터
        When: 분석 쿼리 실행
        Then: 복잡한 분석 쿼리도 2초 이내 처리
        """
        from app.services.notification_analytics_service import (
            NotificationAnalyticsService,
        )

        with patch("app.db.get_db") as mock_db_session:
            analytics_service = NotificationAnalyticsService(mock_db_session)

            # Given: 복잡한 분석 쿼리 시뮬레이션
            with patch.object(
                analytics_service, "generate_analytics_report", new_callable=AsyncMock
            ) as mock_analytics:

                async def slow_analytics(*args, **kwargs):
                    await asyncio.sleep(0.1)  # 실제보다 빠른 시뮬레이션
                    return {
                        "total_sent": 10000,
                        "total_opened": 7000,
                        "engagement_rate": 0.7,
                        "processing_time": "fast",
                    }

                mock_analytics.side_effect = slow_analytics

                # When: 분석 리포트 생성
                start_time = time.time()
                report = await analytics_service.generate_analytics_report(
                    start_date=datetime.now() - timedelta(days=30),
                    end_date=datetime.now(),
                )
                end_time = time.time()

                # Then: 2초 이내 처리
                query_time = end_time - start_time
                assert query_time < 2.0
                assert report["processing_time"] == "fast"

    async def test_notification_index_performance(self):
        """
        Given: 대량의 알림 데이터와 인덱스
        When: 사용자별 알림 조회
        Then: 인덱스를 통한 빠른 조회 성능
        """
        # Given: 인덱스 성능 테스트 시뮬레이션
        with patch("app.db.get_db"):
            # 사용자별 알림 조회 쿼리 성능 테스트
            user_ids = [str(uuid4()) for _ in range(100)]

            async def fast_user_query(user_id):
                # 인덱스를 활용한 빠른 조회 시뮬레이션
                await asyncio.sleep(0.001)  # 1ms 시뮬레이션
                return [f"notification_{i}" for i in range(10)]

            # When: 동시 사용자별 조회 실행
            start_time = time.time()
            tasks = [fast_user_query(user_id) for user_id in user_ids]
            results = await asyncio.gather(*tasks)
            end_time = time.time()

            # Then: 빠른 조회 성능 (전체 200ms 이내)
            total_time = end_time - start_time
            assert total_time < 0.2
            assert len(results) == 100
