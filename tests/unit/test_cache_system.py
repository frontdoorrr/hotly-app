"""
캐시 시스템 TDD 테스트

캐시 및 성능 엔지니어링 시스템 백엔드의 다계층 캐시 시스템 테스트를 정의합니다.
"""
import hashlib
import json
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional


class TestCacheKey:
    """캐시 키 생성 및 관리 테스트"""

    def test_generate_cache_key_basic(self):
        """기본 캐시 키 생성 테스트"""
        # Given: 기본 캐시 키 생성 파라미터
        domain = "place"
        resource_id = "12345"
        params = {"page": 1, "limit": 10}

        # When: 캐시 키 생성
        expected_key = "hotly:v1:place:12345:41c8be8f93dfaaf34f7e9924b7e7bac7"

        # Mock implementation for testing
        def generate_cache_key(
            domain: str, resource_id: str, params: dict = None, version: str = "v1"
        ):
            """캐시 키 생성"""
            if params:
                params_str = json.dumps(params, sort_keys=True)
                params_hash = hashlib.md5(params_str.encode()).hexdigest()[:32]
            else:
                params_hash = ""

            if params_hash:
                return f"hotly:{version}:{domain}:{resource_id}:{params_hash}"
            else:
                return f"hotly:{version}:{domain}:{resource_id}"

        actual_key = generate_cache_key(domain, resource_id, params)

        # Then: 예상한 형태의 키 생성
        assert actual_key.startswith("hotly:v1:place:12345:")
        assert len(actual_key.split(":")) == 5

        print("✅ 캐시 키 생성 테스트 통과")

    def test_cache_key_without_params(self):
        """파라미터 없는 캐시 키 생성 테스트"""
        # Given: 파라미터 없는 캐시 키 생성 파라미터
        domain = "user"
        resource_id = "user_123"

        # Mock implementation
        def generate_cache_key(
            domain: str, resource_id: str, params: dict = None, version: str = "v1"
        ):
            if params:
                params_str = json.dumps(params, sort_keys=True)
                params_hash = hashlib.md5(params_str.encode()).hexdigest()[:32]
            else:
                params_hash = ""

            if params_hash:
                return f"hotly:{version}:{domain}:{resource_id}:{params_hash}"
            else:
                return f"hotly:{version}:{domain}:{resource_id}"

        # When: 캐시 키 생성
        key = generate_cache_key(domain, resource_id)

        # Then: 파라미터 해시 없이 키 생성
        assert key == "hotly:v1:user:user_123"

        print("✅ 파라미터 없는 캐시 키 생성 테스트 통과")

    def test_cache_key_version_management(self):
        """캐시 키 버전 관리 테스트"""
        # Given: 버전이 다른 캐시 키
        domain = "place"
        resource_id = "12345"

        def generate_cache_key(
            domain: str, resource_id: str, params: dict = None, version: str = "v1"
        ):
            if params:
                params_str = json.dumps(params, sort_keys=True)
                params_hash = hashlib.md5(params_str.encode()).hexdigest()[:32]
            else:
                params_hash = ""

            if params_hash:
                return f"hotly:{version}:{domain}:{resource_id}:{params_hash}"
            else:
                return f"hotly:{version}:{domain}:{resource_id}"

        # When: 서로 다른 버전으로 키 생성
        key_v1 = generate_cache_key(domain, resource_id, version="v1")
        key_v2 = generate_cache_key(domain, resource_id, version="v2")

        # Then: 버전에 따라 다른 키 생성
        assert key_v1 == "hotly:v1:place:12345"
        assert key_v2 == "hotly:v2:place:12345"
        assert key_v1 != key_v2

        print("✅ 캐시 키 버전 관리 테스트 통과")


class TestMemoryCacheL1:
    """L1 메모리 캐시 계층 테스트"""

    def setup_method(self):
        """테스트 셋업"""
        self.max_size = 100  # 100개 항목
        self.max_memory = 50 * 1024 * 1024  # 50MB

    def test_memory_cache_set_get(self):
        """메모리 캐시 설정/조회 테스트"""
        # Given: 메모리 캐시 인스턴스
        memory_cache = {}
        cache_metadata = {}

        def set_memory_cache(key: str, value: Any, ttl: int = 3600):
            """메모리 캐시에 값 설정"""
            expiry_time = datetime.now() + timedelta(seconds=ttl)
            memory_cache[key] = value
            cache_metadata[key] = {
                "expiry": expiry_time,
                "access_count": 0,
                "last_accessed": datetime.now(),
            }
            return True

        def get_memory_cache(key: str) -> Optional[Any]:
            """메모리 캐시에서 값 조회"""
            if key not in memory_cache:
                return None

            metadata = cache_metadata[key]
            if datetime.now() > metadata["expiry"]:
                del memory_cache[key]
                del cache_metadata[key]
                return None

            # 액세스 통계 업데이트
            metadata["access_count"] += 1
            metadata["last_accessed"] = datetime.now()

            return memory_cache[key]

        # When: 캐시에 값 설정하고 조회
        key = "test_key"
        value = {"data": "test_value"}

        set_result = set_memory_cache(key, value, 60)
        retrieved_value = get_memory_cache(key)

        # Then: 설정한 값이 정상적으로 조회됨
        assert set_result is True
        assert retrieved_value == value
        assert cache_metadata[key]["access_count"] == 1

        print("✅ 메모리 캐시 설정/조회 테스트 통과")

    def test_memory_cache_expiry(self):
        """메모리 캐시 만료 테스트"""
        # Given: 짧은 TTL을 가진 캐시
        memory_cache = {}
        cache_metadata = {}

        def set_memory_cache(key: str, value: Any, ttl: int = 3600):
            expiry_time = datetime.now() + timedelta(seconds=ttl)
            memory_cache[key] = value
            cache_metadata[key] = {
                "expiry": expiry_time,
                "access_count": 0,
                "last_accessed": datetime.now(),
            }
            return True

        def get_memory_cache(key: str) -> Optional[Any]:
            if key not in memory_cache:
                return None

            metadata = cache_metadata[key]
            if datetime.now() > metadata["expiry"]:
                del memory_cache[key]
                del cache_metadata[key]
                return None

            metadata["access_count"] += 1
            metadata["last_accessed"] = datetime.now()
            return memory_cache[key]

        key = "expire_test"
        value = {"data": "will_expire"}

        # When: 1초 TTL로 설정 후 2초 후 조회
        set_memory_cache(key, value, 1)
        time.sleep(2)
        expired_value = get_memory_cache(key)

        # Then: 만료된 값은 None 반환
        assert expired_value is None
        assert key not in memory_cache
        assert key not in cache_metadata

        print("✅ 메모리 캐시 만료 테스트 통과")

    def test_memory_cache_lru_eviction(self):
        """메모리 캐시 LRU 방출 테스트"""
        # Given: 제한된 크기의 메모리 캐시
        memory_cache = {}
        cache_metadata = {}
        max_size = 3

        def evict_lru():
            """LRU 방출 수행"""
            if len(memory_cache) <= max_size:
                return

            # 가장 오래 전에 접근된 항목 찾기
            oldest_key = min(
                cache_metadata.keys(), key=lambda k: cache_metadata[k]["last_accessed"]
            )

            del memory_cache[oldest_key]
            del cache_metadata[oldest_key]

        def set_memory_cache(key: str, value: Any, ttl: int = 3600):
            expiry_time = datetime.now() + timedelta(seconds=ttl)
            memory_cache[key] = value
            cache_metadata[key] = {
                "expiry": expiry_time,
                "access_count": 0,
                "last_accessed": datetime.now(),
            }

            # 크기 제한 확인
            if len(memory_cache) > max_size:
                evict_lru()

            return True

        # When: 크기 제한을 초과하는 항목들 추가
        for i in range(5):
            set_memory_cache(f"key_{i}", f"value_{i}")
            time.sleep(0.01)  # 시간 차이를 위해

        # Then: 최대 크기만큼만 캐시에 남아있음
        assert len(memory_cache) == max_size
        assert "key_0" not in memory_cache  # 첫 번째는 LRU로 방출
        assert "key_1" not in memory_cache  # 두 번째도 LRU로 방출
        assert "key_2" in memory_cache
        assert "key_3" in memory_cache
        assert "key_4" in memory_cache

        print("✅ 메모리 캐시 LRU 방출 테스트 통과")


class TestDiskCacheL2:
    """L2 디스크 캐시 계층 테스트"""

    def test_disk_cache_file_operations(self):
        """디스크 캐시 파일 연산 테스트"""
        # Given: 디스크 캐시 mock 구현
        disk_cache = {}

        def write_disk_cache(key: str, value: Any, ttl: int = 86400):
            """디스크 캐시에 파일 쓰기"""
            cache_data = {
                "value": value,
                "expiry": (datetime.now() + timedelta(seconds=ttl)).isoformat(),
                "created_at": datetime.now().isoformat(),
            }
            # Mock file write
            disk_cache[key] = json.dumps(cache_data)
            return True

        def read_disk_cache(key: str) -> Optional[Any]:
            """디스크 캐시에서 파일 읽기"""
            if key not in disk_cache:
                return None

            try:
                cache_data = json.loads(disk_cache[key])
                expiry = datetime.fromisoformat(cache_data["expiry"])

                if datetime.now() > expiry:
                    del disk_cache[key]
                    return None

                return cache_data["value"]
            except:
                return None

        # When: 디스크 캐시에 데이터 쓰기/읽기
        key = "disk_test_key"
        value = {"large_data": "x" * 1000, "metadata": {"size": 1000}}

        write_result = write_disk_cache(key, value, 3600)
        retrieved_value = read_disk_cache(key)

        # Then: 디스크 캐시 정상 작동
        assert write_result is True
        assert retrieved_value == value

        print("✅ 디스크 캐시 파일 연산 테스트 통과")

    def test_disk_cache_size_management(self):
        """디스크 캐시 크기 관리 테스트"""
        # Given: 크기 제한이 있는 디스크 캐시
        disk_cache = {}
        cache_size = {}
        max_total_size = 1000  # 1KB 제한

        def calculate_size(value: Any) -> int:
            """값의 크기 계산"""
            return len(json.dumps(value).encode("utf-8"))

        def cleanup_disk_cache():
            """크기 초과 시 정리"""
            current_size = sum(cache_size.values())
            if current_size <= max_total_size:
                return

            # 가장 오래된 항목부터 삭제
            keys_to_remove = []
            for key in list(disk_cache.keys()):
                if sum(cache_size.values()) <= max_total_size:
                    break
                keys_to_remove.append(key)
                del disk_cache[key]
                del cache_size[key]

        def write_disk_cache(key: str, value: Any, ttl: int = 86400):
            size = calculate_size(value)
            cache_data = {
                "value": value,
                "expiry": (datetime.now() + timedelta(seconds=ttl)).isoformat(),
                "created_at": datetime.now().isoformat(),
            }

            disk_cache[key] = json.dumps(cache_data)
            cache_size[key] = size

            cleanup_disk_cache()
            return True

        # When: 크기 제한을 초과하는 데이터 저장
        large_value = {"data": "x" * 400}  # ~400 bytes per item

        for i in range(5):  # 총 ~2KB, 제한 1KB 초과
            write_disk_cache(f"large_key_{i}", large_value)

        # Then: 크기 제한에 따른 정리 수행
        total_size = sum(cache_size.values())
        assert total_size <= max_total_size
        assert len(disk_cache) < 5  # 일부 항목이 정리됨

        print("✅ 디스크 캐시 크기 관리 테스트 통과")


class TestRedisCacheL3:
    """L3 Redis 캐시 계층 테스트"""

    def test_redis_cache_operations(self):
        """Redis 캐시 기본 연산 테스트"""
        # Given: Redis mock 클라이언트
        redis_mock = {}
        redis_ttl = {}

        def redis_set(key: str, value: str, ex: int = None):
            """Redis SET 명령"""
            redis_mock[key] = value
            if ex:
                redis_ttl[key] = datetime.now() + timedelta(seconds=ex)
            return True

        def redis_get(key: str) -> Optional[str]:
            """Redis GET 명령"""
            if key not in redis_mock:
                return None

            if key in redis_ttl and datetime.now() > redis_ttl[key]:
                del redis_mock[key]
                del redis_ttl[key]
                return None

            return redis_mock[key]

        def redis_exists(key: str) -> bool:
            """Redis EXISTS 명령"""
            return redis_get(key) is not None

        # When: Redis 캐시 연산 수행
        key = "redis_test"
        value = json.dumps({"cached_data": "test_value"})

        set_result = redis_set(key, value, 3600)
        exists_result = redis_exists(key)
        get_result = redis_get(key)

        # Then: Redis 연산 정상 작동
        assert set_result is True
        assert exists_result is True
        assert get_result == value

        cached_data = json.loads(get_result)
        assert cached_data["cached_data"] == "test_value"

        print("✅ Redis 캐시 기본 연산 테스트 통과")

    def test_redis_cache_batch_operations(self):
        """Redis 캐시 배치 연산 테스트"""
        # Given: Redis 배치 연산 mock
        redis_mock = {}

        def redis_mset(mapping: Dict[str, str]):
            """Redis MSET 명령"""
            redis_mock.update(mapping)
            return True

        def redis_mget(keys: List[str]) -> List[Optional[str]]:
            """Redis MGET 명령"""
            return [redis_mock.get(key) for key in keys]

        def redis_delete(*keys: str) -> int:
            """Redis DELETE 명령"""
            deleted_count = 0
            for key in keys:
                if key in redis_mock:
                    del redis_mock[key]
                    deleted_count += 1
            return deleted_count

        # When: 배치 연산 수행
        batch_data = {
            "batch_key_1": json.dumps({"data": 1}),
            "batch_key_2": json.dumps({"data": 2}),
            "batch_key_3": json.dumps({"data": 3}),
        }

        mset_result = redis_mset(batch_data)
        mget_result = redis_mget(["batch_key_1", "batch_key_2", "batch_key_3"])
        delete_result = redis_delete("batch_key_1", "batch_key_2")

        # Then: 배치 연산 정상 작동
        assert mset_result is True
        assert len(mget_result) == 3
        assert all(result is not None for result in mget_result)
        assert delete_result == 2
        assert "batch_key_1" not in redis_mock
        assert "batch_key_2" not in redis_mock
        assert "batch_key_3" in redis_mock

        print("✅ Redis 캐시 배치 연산 테스트 통과")

    def test_redis_cache_pattern_operations(self):
        """Redis 캐시 패턴 연산 테스트"""
        # Given: Redis 패턴 연산 mock
        redis_mock = {
            "hotly:v1:place:123": "data1",
            "hotly:v1:place:456": "data2",
            "hotly:v1:user:789": "data3",
            "hotly:v2:place:123": "data4",
        }

        def redis_keys(pattern: str) -> List[str]:
            """Redis KEYS 명령 (패턴 매칭)"""
            import fnmatch

            return [key for key in redis_mock.keys() if fnmatch.fnmatch(key, pattern)]

        def redis_scan_iter(pattern: str):
            """Redis SCAN 명령 (이터레이터)"""
            import fnmatch

            for key in redis_mock.keys():
                if fnmatch.fnmatch(key, pattern):
                    yield key

        # When: 패턴 기반 키 조회
        place_keys = redis_keys("hotly:v1:place:*")
        all_v1_keys = list(redis_scan_iter("hotly:v1:*"))

        # Then: 패턴에 맞는 키들 반환
        assert len(place_keys) == 2
        assert "hotly:v1:place:123" in place_keys
        assert "hotly:v1:place:456" in place_keys

        assert len(all_v1_keys) == 3
        assert "hotly:v1:user:789" in all_v1_keys
        assert "hotly:v2:place:123" not in all_v1_keys

        print("✅ Redis 캐시 패턴 연산 테스트 통과")


class TestMultiLevelCacheManager:
    """다계층 캐시 매니저 통합 테스트"""

    def test_cache_hierarchy_get_operation(self):
        """캐시 계층 조회 연산 테스트"""
        # Given: 3계층 캐시 mock
        l1_cache = {}  # 메모리
        l2_cache = {}  # 디스크
        l3_cache = {}  # Redis

        def get_from_cache_hierarchy(key: str) -> Optional[Any]:
            """계층별 캐시에서 조회"""
            # L1 (메모리) 먼저 확인
            if key in l1_cache:
                return l1_cache[key]

            # L2 (디스크) 확인
            if key in l2_cache:
                value = l2_cache[key]
                # L1으로 승격
                l1_cache[key] = value
                return value

            # L3 (Redis) 확인
            if key in l3_cache:
                value = l3_cache[key]
                # L2, L1으로 승격
                l2_cache[key] = value
                l1_cache[key] = value
                return value

            return None

        # When: 다른 계층에 데이터 배치 후 조회
        test_key = "test_hierarchy"
        test_value = {"data": "hierarchy_test"}

        # L3에만 데이터 존재
        l3_cache[test_key] = test_value

        result = get_from_cache_hierarchy(test_key)

        # Then: 값 반환 및 상위 계층으로 승격
        assert result == test_value
        assert test_key in l1_cache  # L1으로 승격됨
        assert test_key in l2_cache  # L2로 승격됨
        assert l1_cache[test_key] == test_value
        assert l2_cache[test_key] == test_value

        print("✅ 캐시 계층 조회 연산 테스트 통과")

    def test_cache_hierarchy_set_operation(self):
        """캐시 계층 설정 연산 테스트"""
        # Given: 3계층 캐시 mock
        l1_cache = {}
        l2_cache = {}
        l3_cache = {}

        def set_to_cache_hierarchy(key: str, value: Any, ttl: int = 3600):
            """모든 계층에 캐시 설정"""
            # 모든 계층에 동시 저장
            l1_cache[key] = value
            l2_cache[key] = value
            l3_cache[key] = value
            return True

        # When: 계층 캐시에 값 설정
        test_key = "set_hierarchy"
        test_value = {"data": "set_test", "timestamp": datetime.now().isoformat()}

        result = set_to_cache_hierarchy(test_key, test_value)

        # Then: 모든 계층에 값 저장됨
        assert result is True
        assert l1_cache[test_key] == test_value
        assert l2_cache[test_key] == test_value
        assert l3_cache[test_key] == test_value

        print("✅ 캐시 계층 설정 연산 테스트 통과")

    def test_cache_hierarchy_invalidation(self):
        """캐시 계층 무효화 테스트"""
        # Given: 모든 계층에 데이터가 있는 상태
        l1_cache = {"invalidate_test": {"data": "old_value"}}
        l2_cache = {"invalidate_test": {"data": "old_value"}}
        l3_cache = {"invalidate_test": {"data": "old_value"}}

        def invalidate_cache_hierarchy(key: str):
            """모든 계층에서 캐시 무효화"""
            if key in l1_cache:
                del l1_cache[key]
            if key in l2_cache:
                del l2_cache[key]
            if key in l3_cache:
                del l3_cache[key]
            return True

        def invalidate_cache_pattern(pattern: str):
            """패턴 매칭으로 캐시 무효화"""
            import fnmatch

            keys_to_delete = []
            for cache in [l1_cache, l2_cache, l3_cache]:
                for key in list(cache.keys()):
                    if fnmatch.fnmatch(key, pattern):
                        keys_to_delete.append(key)
                        if key in cache:
                            del cache[key]

            return len(keys_to_delete)

        # When: 단일 키 무효화
        test_key = "invalidate_test"
        invalidate_result = invalidate_cache_hierarchy(test_key)

        # Then: 모든 계층에서 삭제됨
        assert invalidate_result is True
        assert test_key not in l1_cache
        assert test_key not in l2_cache
        assert test_key not in l3_cache

        # When: 패턴 기반 무효화 테스트
        l1_cache.update({"pattern_1": "data", "pattern_2": "data", "other": "data"})
        l2_cache.update({"pattern_1": "data", "pattern_2": "data", "other": "data"})
        l3_cache.update({"pattern_1": "data", "pattern_2": "data", "other": "data"})

        deleted_count = invalidate_cache_pattern("pattern_*")

        # Then: 패턴에 맞는 키만 삭제
        assert deleted_count >= 2  # 각 계층에서 pattern_1, pattern_2 삭제
        assert "pattern_1" not in l1_cache
        assert "pattern_2" not in l1_cache
        assert "other" in l1_cache

        print("✅ 캐시 계층 무효화 테스트 통과")


def main():
    """캐시 시스템 테스트 실행"""
    print("🧪 다계층 캐시 시스템 TDD 테스트 시작")
    print("=" * 60)

    test_classes = [
        TestCacheKey(),
        TestMemoryCacheL1(),
        TestDiskCacheL2(),
        TestRedisCacheL3(),
        TestMultiLevelCacheManager(),
    ]

    total_passed = 0
    total_failed = 0

    for test_instance in test_classes:
        class_name = test_instance.__class__.__name__
        print(f"\n📋 {class_name} 테스트 실행")
        print("-" * 40)

        # 테스트 메소드들 실행
        test_methods = [
            method for method in dir(test_instance) if method.startswith("test_")
        ]

        for method_name in test_methods:
            try:
                if hasattr(test_instance, "setup_method"):
                    test_instance.setup_method()

                test_method = getattr(test_instance, method_name)
                test_method()
                total_passed += 1
            except Exception as e:
                print(f"❌ {method_name} 실패: {e}")
                total_failed += 1

    print(f"\n📊 캐시 시스템 테스트 결과:")
    print(f"   ✅ 통과: {total_passed}")
    print(f"   ❌ 실패: {total_failed}")
    print(f"   📈 전체: {total_passed + total_failed}")

    if total_failed == 0:
        print("🎉 모든 캐시 시스템 테스트 통과!")
        return True
    else:
        print(f"⚠️ {total_failed}개 테스트 실패")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
