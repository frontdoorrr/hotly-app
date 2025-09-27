"""
로깅 및 중앙집중식 관리 시스템

구조화된 로깅, 중앙집중식 로그 관리, 로그 수집 및 분석 기능을 제공합니다.
TDD 방식으로 개발된 프로덕션 레디 로깅 시스템입니다.
"""

import json
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

# from app.core.config import settings


class LogLevel(str, Enum):
    """로그 레벨"""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class LogEntry:
    """구조화된 로그 항목"""

    timestamp: str
    level: str
    message: str
    service: str
    version: str
    trace_id: Optional[str] = None
    user_id: Optional[str] = None
    extra_fields: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        data = asdict(self)
        if self.extra_fields:
            data.update(self.extra_fields)
            del data["extra_fields"]
        return {k: v for k, v in data.items() if v is not None}


class StructuredLogger:
    """구조화된 로깅 시스템"""

    def __init__(self, service_name: str = "hotly-app", version: str = "1.0.0"):
        self.service_name = service_name
        self.version = version
        self.sensitive_fields = ["password", "token", "api_key", "credit_card"]

    def create_structured_log(
        self,
        level: str,
        message: str,
        trace_id: str = None,
        user_id: str = None,
        extra_fields: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """구조화된 로그 생성"""
        log_entry = LogEntry(
            timestamp=datetime.now().isoformat(),
            level=level.upper(),
            message=message,
            service=self.service_name,
            version=self.version,
            trace_id=trace_id,
            user_id=user_id,
            extra_fields=extra_fields,
        )

        return log_entry.to_dict()

    def mask_sensitive_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """민감정보 마스킹"""
        masked_data = data.copy()

        for field in self.sensitive_fields:
            if field in masked_data:
                value = str(masked_data[field])
                if len(value) > 4:
                    masked_data[field] = f"{value[:2]}***{value[-2:]}"
                else:
                    masked_data[field] = "***"

        # 중첩된 딕셔너리도 처리
        for key, value in masked_data.items():
            if isinstance(value, dict):
                masked_data[key] = self.mask_sensitive_data(value)

        return masked_data


class RequestTracer:
    """요청 추적 시스템"""

    def __init__(self):
        self.traces: Dict[str, Dict] = {}
        self._lock = threading.Lock()

    def start_trace(self, request_id: str) -> str:
        """요청 추적 시작"""
        trace_id = f"trace-{uuid.uuid4().hex[:8]}"

        with self._lock:
            self.traces[trace_id] = {
                "request_id": request_id,
                "start_time": datetime.now(),
                "logs": [],
                "status": "active",
            }

        return trace_id

    def add_trace_log(
        self, trace_id: str, level: str, message: str, extra: Dict = None
    ):
        """추적에 로그 추가"""
        with self._lock:
            if trace_id in self.traces:
                log_entry = {
                    "timestamp": datetime.now(),
                    "level": level,
                    "message": message,
                    **(extra or {}),
                }
                self.traces[trace_id]["logs"].append(log_entry)

    def end_trace(self, trace_id: str, status: str = "completed"):
        """요청 추적 종료"""
        with self._lock:
            if trace_id in self.traces:
                trace = self.traces[trace_id]
                trace["status"] = status
                trace["end_time"] = datetime.now()
                trace["duration_ms"] = (
                    trace["end_time"] - trace["start_time"]
                ).total_seconds() * 1000

    def get_trace(self, trace_id: str) -> Optional[Dict]:
        """추적 정보 조회"""
        with self._lock:
            return self.traces.get(trace_id)


class LogCollector:
    """중앙집중식 로그 수집기"""

    def __init__(self):
        self.services: Dict[str, Dict] = {}
        self.total_logs = 0
        self.log_buffer: List[Dict] = []
        self._lock = threading.Lock()

    def collect_log(self, service_name: str, log_entry: Dict[str, Any]):
        """로그 수집"""
        with self._lock:
            if service_name not in self.services:
                self.services[service_name] = {
                    "log_count": 0,
                    "last_log_time": None,
                    "error_count": 0,
                    "warning_count": 0,
                }

            service_stats = self.services[service_name]
            service_stats["log_count"] += 1
            service_stats["last_log_time"] = datetime.now()

            level = log_entry.get("level", "").upper()
            if level == "ERROR":
                service_stats["error_count"] += 1
            elif level == "WARNING":
                service_stats["warning_count"] += 1

            self.total_logs += 1
            self.log_buffer.append({"service": service_name, **log_entry})

    def get_service_stats(self, service_name: str) -> Dict[str, Any]:
        """서비스별 로그 통계"""
        with self._lock:
            return self.services.get(service_name, {})

    def get_total_stats(self) -> Dict[str, Any]:
        """전체 로그 통계"""
        with self._lock:
            return {
                "total_logs": self.total_logs,
                "total_services": len(self.services),
                "log_buffer_size": len(self.log_buffer),
            }


class LogSearchEngine:
    """로그 검색 및 필터링 엔진"""

    def __init__(self):
        self.log_database: List[Dict] = []
        self._lock = threading.Lock()

    def add_log_entry(
        self, level: str, message: str, service: str, extra: Dict = None
    ) -> Dict:
        """로그 항목 추가"""
        with self._lock:
            entry = {
                "id": len(self.log_database) + 1,
                "timestamp": datetime.now(),
                "level": level,
                "message": message,
                "service": service,
                **(extra or {}),
            }
            self.log_database.append(entry)
            return entry

    def search_logs(
        self,
        level: str = None,
        service: str = None,
        message_contains: str = None,
        time_from: datetime = None,
        time_to: datetime = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """로그 검색"""
        with self._lock:
            results = []

            for log in self.log_database:
                # 레벨 필터
                if level and log["level"] != level:
                    continue

                # 서비스 필터
                if service and log["service"] != service:
                    continue

                # 메시지 검색
                if (
                    message_contains
                    and message_contains.lower() not in log["message"].lower()
                ):
                    continue

                # 시간 범위 필터
                if time_from and log["timestamp"] < time_from:
                    continue
                if time_to and log["timestamp"] > time_to:
                    continue

                results.append(log)

                if len(results) >= limit:
                    break

            return results


class LogRotationManager:
    """로그 로테이션 및 아카이빙 관리자"""

    def __init__(self, max_log_size: int = 1000, max_files: int = 3):
        self.max_log_size = max_log_size
        self.max_files = max_files
        self.storage = {"current_logs": [], "archived_files": [], "current_size": 0}
        self._lock = threading.Lock()

    def add_log_entry(self, log_entry: Dict[str, Any]):
        """로그 항목 추가"""
        with self._lock:
            log_size = len(json.dumps(log_entry))

            # 로테이션 필요한지 체크
            if self.storage["current_size"] + log_size > self.max_log_size:
                self._rotate_logs()

            self.storage["current_logs"].append(log_entry)
            self.storage["current_size"] += log_size

    def _rotate_logs(self):
        """로그 로테이션 (internal method)"""
        if self.storage["current_logs"]:
            # 현재 로그를 아카이브로 이동
            archived_file = {
                "filename": f"app-{datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
                "logs": self.storage["current_logs"].copy(),
                "size": self.storage["current_size"],
                "archived_at": datetime.now(),
            }

            self.storage["archived_files"].append(archived_file)

            # 최대 파일 수 초과 시 오래된 파일 삭제
            while len(self.storage["archived_files"]) > self.max_files:
                removed_file = self.storage["archived_files"].pop(0)
                print(f"Archived file deleted: {removed_file['filename']}")

            # 현재 로그 초기화
            self.storage["current_logs"] = []
            self.storage["current_size"] = 0

    def get_log_statistics(self) -> Dict[str, Any]:
        """로그 통계"""
        with self._lock:
            total_logs = len(self.storage["current_logs"])
            total_size = self.storage["current_size"]

            for archived in self.storage["archived_files"]:
                total_logs += len(archived["logs"])
                total_size += archived["size"]

            return {
                "current_logs_count": len(self.storage["current_logs"]),
                "current_size": self.storage["current_size"],
                "archived_files_count": len(self.storage["archived_files"]),
                "total_logs": total_logs,
                "total_size": total_size,
            }


class CentralizedLoggingService:
    """중앙집중식 로깅 서비스"""

    def __init__(self):
        self.structured_logger = StructuredLogger()
        self.request_tracer = RequestTracer()
        self.log_collector = LogCollector()
        self.search_engine = LogSearchEngine()
        self.rotation_manager = LogRotationManager()
        self.executor = ThreadPoolExecutor(max_workers=4)

    def log(
        self,
        level: LogLevel,
        message: str,
        trace_id: str = None,
        user_id: str = None,
        service: str = None,
        extra_fields: Dict[str, Any] = None,
    ):
        """로그 기록"""
        service_name = service or self.structured_logger.service_name

        # 구조화된 로그 생성
        log_entry = self.structured_logger.create_structured_log(
            level=level.value,
            message=message,
            trace_id=trace_id,
            user_id=user_id,
            extra_fields=extra_fields,
        )

        # 민감정보 마스킹
        if extra_fields:
            log_entry = self.structured_logger.mask_sensitive_data(log_entry)

        # 비동기로 로그 처리
        self.executor.submit(self._process_log, service_name, log_entry)

    def _process_log(self, service_name: str, log_entry: Dict[str, Any]):
        """로그 처리 (내부 메서드)"""
        # 로그 수집
        self.log_collector.collect_log(service_name, log_entry)

        # 검색 엔진에 추가
        self.search_engine.add_log_entry(
            level=log_entry["level"],
            message=log_entry["message"],
            service=service_name,
            extra=log_entry,
        )

        # 로테이션 관리자에 추가
        self.rotation_manager.add_log_entry(log_entry)

    def start_request_trace(self, request_id: str) -> str:
        """요청 추적 시작"""
        return self.request_tracer.start_trace(request_id)

    def add_trace_log(
        self, trace_id: str, level: LogLevel, message: str, extra: Dict = None
    ):
        """추적 로그 추가"""
        self.request_tracer.add_trace_log(trace_id, level.value, message, extra)

    def end_request_trace(self, trace_id: str, status: str = "completed"):
        """요청 추적 종료"""
        self.request_tracer.end_trace(trace_id, status)

    def get_trace(self, trace_id: str) -> Optional[Dict]:
        """추적 정보 조회"""
        return self.request_tracer.get_trace(trace_id)

    def search_logs(self, **kwargs) -> List[Dict[str, Any]]:
        """로그 검색"""
        return self.search_engine.search_logs(**kwargs)

    def get_service_stats(self, service_name: str) -> Dict[str, Any]:
        """서비스 통계 조회"""
        return self.log_collector.get_service_stats(service_name)

    def get_system_stats(self) -> Dict[str, Any]:
        """시스템 통계 조회"""
        collector_stats = self.log_collector.get_total_stats()
        rotation_stats = self.rotation_manager.get_log_statistics()

        return {
            **collector_stats,
            **rotation_stats,
            "total_traces": len(self.request_tracer.traces),
        }


# 글로벌 로깅 서비스 인스턴스
logging_service = CentralizedLoggingService()


def get_logging_service() -> CentralizedLoggingService:
    """로깅 서비스 인스턴스 조회"""
    return logging_service


# 편의 함수들
def log_info(message: str, trace_id: str = None, user_id: str = None, **kwargs):
    """INFO 레벨 로그"""
    logging_service.log(
        LogLevel.INFO, message, trace_id=trace_id, user_id=user_id, extra_fields=kwargs
    )


def log_error(message: str, trace_id: str = None, user_id: str = None, **kwargs):
    """ERROR 레벨 로그"""
    logging_service.log(
        LogLevel.ERROR, message, trace_id=trace_id, user_id=user_id, extra_fields=kwargs
    )


def log_warning(message: str, trace_id: str = None, user_id: str = None, **kwargs):
    """WARNING 레벨 로그"""
    logging_service.log(
        LogLevel.WARNING,
        message,
        trace_id=trace_id,
        user_id=user_id,
        extra_fields=kwargs,
    )


def log_debug(message: str, trace_id: str = None, user_id: str = None, **kwargs):
    """DEBUG 레벨 로그"""
    logging_service.log(
        LogLevel.DEBUG, message, trace_id=trace_id, user_id=user_id, extra_fields=kwargs
    )
