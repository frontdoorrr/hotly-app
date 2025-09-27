"""
Redis 기반 다계층 캐시 매니저 (Task 4-1)

캐시 시스템의 핵심 구현체로, L1(메모리), L2(디스크), L3(Redis) 캐시 계층을 관리합니다.
캐시 및 성능 엔지니어링 시스템의 백엔드 구현을 제공합니다.
"""
import asyncio
import hashlib
import json
import gzip
import base64
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import logging
from functools import wraps
from abc import ABC, abstractmethod

import redis.asyncio as redis
from pydantic import BaseSettings

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class CacheStats:
    """캐시 통계 데이터"""
    hit_count: int = 0
    miss_count: int = 0
    set_count: int = 0
    delete_count: int = 0
    error_count: int = 0
    response_times: List[float] = field(default_factory=list)
    
    @property
    def total_requests(self) -> int:
        return self.hit_count + self.miss_count
    
    @property
    def hit_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return self.hit_count / self.total_requests
    
    @property
    def avg_response_time(self) -> float:
        if not self.response_times:
            return 0.0
        return sum(self.response_times) / len(self.response_times)


class CacheKeyManager:
    """캐시 키 생성 및 관리"""
    
    @staticmethod
    def generate_key(domain: str, resource_id: str, params: Optional[Dict] = None, version: str = "v1") -> str:
        """
        캐시 키 생성
        
        Args:
            domain: 도메인 (place, user, course 등)
            resource_id: 리소스 ID
            params: 추가 파라미터
            version: API 버전
            
        Returns:
            생성된 캐시 키
        """
        if params:
            params_str = json.dumps(params, sort_keys=True)
            params_hash = hashlib.md5(params_str.encode()).hexdigest()[:16]
            return f"hotly:{version}:{domain}:{resource_id}:{params_hash}"
        else:
            return f"hotly:{version}:{domain}:{resource_id}"
    
    @staticmethod
    def parse_key(key: str) -> Dict[str, str]:
        """캐시 키 파싱"""
        parts = key.split(":")
        if len(parts) >= 4:
            return {
                "prefix": parts[0],
                "version": parts[1],
                "domain": parts[2],
                "resource_id": parts[3],
                "params_hash": parts[4] if len(parts) > 4 else None
            }
        return {}


class CompressionManager:
    """데이터 압축 관리"""
    
    @staticmethod
    def compress_data(data: Any) -> str:
        """데이터 압축"""
        try:
            json_str = json.dumps(data, ensure_ascii=False)
            json_bytes = json_str.encode('utf-8')
            compressed = gzip.compress(json_bytes)
            return base64.b64encode(compressed).decode('utf-8')
        except Exception as e:
            logger.error(f"Data compression failed: {e}")
            raise
    
    @staticmethod
    def decompress_data(compressed_data: str) -> Any:
        """데이터 압축 해제"""
        try:
            compressed_bytes = base64.b64decode(compressed_data.encode('utf-8'))
            decompressed_bytes = gzip.decompress(compressed_bytes)
            json_str = decompressed_bytes.decode('utf-8')
            return json.loads(json_str)
        except Exception as e:
            logger.error(f"Data decompression failed: {e}")
            raise


class L1MemoryCache:
    """L1 메모리 캐시 (RAM)"""
    
    def __init__(self, max_size: int = 1000, max_memory_mb: int = 100):
        self.max_size = max_size
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.cache: Dict[str, Any] = {}
        self.metadata: Dict[str, Dict] = {}
        self.access_order: List[str] = []
        
    def _estimate_size(self, data: Any) -> int:
        """데이터 크기 추정"""
        try:
            return len(json.dumps(data).encode('utf-8'))
        except:
            return 1024  # 기본 추정치
    
    def _evict_lru(self):
        """LRU 방출"""
        if not self.access_order:
            return
            
        # 메모리 사용량 체크
        current_memory = sum(
            self.metadata[key].get("size", 0) 
            for key in self.cache.keys()
        )
        
        while (len(self.cache) > self.max_size or 
               current_memory > self.max_memory_bytes) and self.access_order:
            
            oldest_key = self.access_order.pop(0)
            if oldest_key in self.cache:
                removed_size = self.metadata[oldest_key].get("size", 0)
                del self.cache[oldest_key]
                del self.metadata[oldest_key]
                current_memory -= removed_size
    
    def get(self, key: str) -> Optional[Any]:
        """메모리 캐시에서 데이터 조회"""
        if key not in self.cache:
            return None
        
        metadata = self.metadata[key]
        
        # TTL 체크
        if metadata["expires_at"] and datetime.now() > metadata["expires_at"]:
            self._remove(key)
            return None
        
        # 접근 순서 업데이트 (LRU)
        if key in self.access_order:
            self.access_order.remove(key)
        self.access_order.append(key)
        
        # 통계 업데이트
        metadata["access_count"] += 1
        metadata["last_accessed"] = datetime.now()
        
        return self.cache[key]
    
    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """메모리 캐시에 데이터 설정"""
        try:
            size = self._estimate_size(value)
            expires_at = datetime.now() + timedelta(seconds=ttl) if ttl > 0 else None
            
            # 기존 데이터 제거
            if key in self.cache:
                self._remove(key)
            
            # 새 데이터 추가
            self.cache[key] = value
            self.metadata[key] = {
                "size": size,
                "created_at": datetime.now(),
                "expires_at": expires_at,
                "access_count": 0,
                "last_accessed": datetime.now()
            }
            self.access_order.append(key)
            
            # 용량 초과 시 LRU 방출
            self._evict_lru()
            
            return True
        except Exception as e:
            logger.error(f"L1 cache set error: {e}")
            return False
    
    def _remove(self, key: str):
        """키 삭제"""
        if key in self.cache:
            del self.cache[key]
            del self.metadata[key]
            if key in self.access_order:
                self.access_order.remove(key)
    
    def delete(self, key: str) -> bool:
        """메모리 캐시에서 데이터 삭제"""
        if key in self.cache:
            self._remove(key)
            return True
        return False
    
    def clear(self):
        """전체 캐시 삭제"""
        self.cache.clear()
        self.metadata.clear()
        self.access_order.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """캐시 통계 조회"""
        total_memory = sum(meta.get("size", 0) for meta in self.metadata.values())
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "memory_usage_bytes": total_memory,
            "max_memory_bytes": self.max_memory_bytes,
            "memory_usage_mb": total_memory / (1024 * 1024),
            "usage_rate": len(self.cache) / self.max_size,
            "memory_rate": total_memory / self.max_memory_bytes
        }


class L2DiskCache:
    """L2 디스크 캐시 (Local Storage)"""
    
    def __init__(self, cache_dir: str = "/tmp/hotly_cache", max_size_mb: int = 500):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.index_file = self.cache_dir / "index.json"
        self.index: Dict[str, Dict] = self._load_index()
    
    def _load_index(self) -> Dict[str, Dict]:
        """인덱스 파일 로드"""
        try:
            if self.index_file.exists():
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load cache index: {e}")
        return {}
    
    def _save_index(self):
        """인덱스 파일 저장"""
        try:
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(self.index, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save cache index: {e}")
    
    def _get_cache_file(self, key: str) -> Path:
        """캐시 파일 경로 생성"""
        safe_key = hashlib.sha256(key.encode()).hexdigest()
        return self.cache_dir / f"{safe_key}.cache"
    
    def _cleanup_expired(self):
        """만료된 캐시 정리"""
        current_time = datetime.now()
        expired_keys = []
        
        for key, metadata in self.index.items():
            expires_at_str = metadata.get("expires_at")
            if expires_at_str:
                expires_at = datetime.fromisoformat(expires_at_str)
                if current_time > expires_at:
                    expired_keys.append(key)
        
        for key in expired_keys:
            self.delete(key)
    
    def _cleanup_by_size(self):
        """크기 기반 정리"""
        current_size = sum(meta.get("size", 0) for meta in self.index.values())
        
        if current_size <= self.max_size_bytes:
            return
        
        # 오래된 순서로 정렬
        sorted_keys = sorted(
            self.index.keys(),
            key=lambda k: self.index[k].get("created_at", "")
        )
        
        for key in sorted_keys:
            if current_size <= self.max_size_bytes:
                break
            
            size = self.index[key].get("size", 0)
            self.delete(key)
            current_size -= size
    
    def get(self, key: str) -> Optional[Any]:
        """디스크 캐시에서 데이터 조회"""
        if key not in self.index:
            return None
        
        metadata = self.index[key]
        
        # TTL 체크
        expires_at_str = metadata.get("expires_at")
        if expires_at_str:
            expires_at = datetime.fromisoformat(expires_at_str)
            if datetime.now() > expires_at:
                self.delete(key)
                return None
        
        # 파일에서 데이터 읽기
        cache_file = self._get_cache_file(key)
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            # 압축된 데이터인지 확인
            if metadata.get("compressed", False):
                return CompressionManager.decompress_data(cache_data["data"])
            else:
                return cache_data["data"]
                
        except Exception as e:
            logger.error(f"Failed to read cache file {cache_file}: {e}")
            self.delete(key)
            return None
    
    def set(self, key: str, value: Any, ttl: int = 86400, compress: bool = True) -> bool:
        """디스크 캐시에 데이터 설정"""
        try:
            # 만료된 캐시 정리
            self._cleanup_expired()
            
            expires_at = datetime.now() + timedelta(seconds=ttl) if ttl > 0 else None
            
            # 데이터 압축 여부 결정
            if compress:
                compressed_data = CompressionManager.compress_data(value)
                cache_data = {"data": compressed_data}
            else:
                cache_data = {"data": value}
            
            # 파일에 저장
            cache_file = self._get_cache_file(key)
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False)
            
            # 인덱스 업데이트
            file_size = cache_file.stat().st_size
            self.index[key] = {
                "created_at": datetime.now().isoformat(),
                "expires_at": expires_at.isoformat() if expires_at else None,
                "size": file_size,
                "compressed": compress
            }
            
            self._save_index()
            
            # 크기 기반 정리
            self._cleanup_by_size()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to set disk cache: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """디스크 캐시에서 데이터 삭제"""
        if key not in self.index:
            return False
        
        try:
            cache_file = self._get_cache_file(key)
            if cache_file.exists():
                cache_file.unlink()
            
            del self.index[key]
            self._save_index()
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete cache file: {e}")
            return False
    
    def clear(self):
        """전체 캐시 삭제"""
        try:
            for cache_file in self.cache_dir.glob("*.cache"):
                cache_file.unlink()
            
            self.index.clear()
            self._save_index()
            
        except Exception as e:
            logger.error(f"Failed to clear disk cache: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """캐시 통계 조회"""
        total_size = sum(meta.get("size", 0) for meta in self.index.values())
        return {
            "file_count": len(self.index),
            "total_size_bytes": total_size,
            "total_size_mb": total_size / (1024 * 1024),
            "max_size_bytes": self.max_size_bytes,
            "max_size_mb": self.max_size_bytes / (1024 * 1024),
            "usage_rate": total_size / self.max_size_bytes if self.max_size_bytes > 0 else 0
        }


class L3RedisCache:
    """L3 Redis 캐시 (Distributed Cache)"""
    
    def __init__(self, redis_url: str = None):
        self.redis_url = redis_url or getattr(settings, 'REDIS_URL', 'redis://localhost:6379/0')
        self.redis_client: Optional[redis.Redis] = None
        self.connection_pool = None
    
    async def connect(self):
        """Redis 연결"""
        try:
            self.connection_pool = redis.ConnectionPool.from_url(
                self.redis_url,
                decode_responses=True,
                max_connections=20
            )
            self.redis_client = redis.Redis(connection_pool=self.connection_pool)
            
            # 연결 테스트
            await self.redis_client.ping()
            logger.info("Redis connected successfully")
            
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    async def disconnect(self):
        """Redis 연결 해제"""
        if self.redis_client:
            await self.redis_client.close()
        if self.connection_pool:
            await self.connection_pool.disconnect()
    
    async def get(self, key: str) -> Optional[Any]:
        """Redis에서 데이터 조회"""
        try:
            if not self.redis_client:
                await self.connect()
            
            data = await self.redis_client.get(key)
            if data is None:
                return None
            
            return json.loads(data)
            
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: int = 86400) -> bool:
        """Redis에 데이터 설정"""
        try:
            if not self.redis_client:
                await self.connect()
            
            data = json.dumps(value, ensure_ascii=False)
            
            if ttl > 0:
                await self.redis_client.setex(key, ttl, data)
            else:
                await self.redis_client.set(key, data)
            
            return True
            
        except Exception as e:
            logger.error(f"Redis set error: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Redis에서 데이터 삭제"""
        try:
            if not self.redis_client:
                await self.connect()
            
            result = await self.redis_client.delete(key)
            return result > 0
            
        except Exception as e:
            logger.error(f"Redis delete error: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Redis에 키 존재 여부 확인"""
        try:
            if not self.redis_client:
                await self.connect()
            
            result = await self.redis_client.exists(key)
            return result > 0
            
        except Exception as e:
            logger.error(f"Redis exists error: {e}")
            return False
    
    async def mget(self, keys: List[str]) -> List[Optional[Any]]:
        """Redis에서 다중 키 조회"""
        try:
            if not self.redis_client:
                await self.connect()
            
            results = await self.redis_client.mget(keys)
            return [json.loads(data) if data else None for data in results]
            
        except Exception as e:
            logger.error(f"Redis mget error: {e}")
            return [None] * len(keys)
    
    async def mset(self, mapping: Dict[str, Any], ttl: int = 86400) -> bool:
        """Redis에 다중 키 설정"""
        try:
            if not self.redis_client:
                await self.connect()
            
            # JSON 직렬화
            json_mapping = {
                key: json.dumps(value, ensure_ascii=False)
                for key, value in mapping.items()
            }
            
            # 배치 설정
            await self.redis_client.mset(json_mapping)
            
            # TTL 설정 (개별적으로)
            if ttl > 0:
                pipe = self.redis_client.pipeline()
                for key in mapping.keys():
                    pipe.expire(key, ttl)
                await pipe.execute()
            
            return True
            
        except Exception as e:
            logger.error(f"Redis mset error: {e}")
            return False
    
    async def keys(self, pattern: str) -> List[str]:
        """패턴으로 키 검색"""
        try:
            if not self.redis_client:
                await self.connect()
            
            return await self.redis_client.keys(pattern)
            
        except Exception as e:
            logger.error(f"Redis keys error: {e}")
            return []
    
    async def delete_pattern(self, pattern: str) -> int:
        """패턴 매칭으로 키 삭제"""
        try:
            keys = await self.keys(pattern)
            if not keys:
                return 0
            
            return await self.redis_client.delete(*keys)
            
        except Exception as e:
            logger.error(f"Redis delete pattern error: {e}")
            return 0
    
    async def get_stats(self) -> Dict[str, Any]:
        """Redis 통계 조회"""
        try:
            if not self.redis_client:
                await self.connect()
            
            info = await self.redis_client.info()
            return {
                "connected_clients": info.get("connected_clients", 0),
                "used_memory_mb": info.get("used_memory", 0) / (1024 * 1024),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "hit_rate": info.get("keyspace_hits", 0) / max(
                    info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0), 1
                )
            }
            
        except Exception as e:
            logger.error(f"Redis stats error: {e}")
            return {}


def cache_timing(func):
    """캐시 타이밍 데코레이터"""
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        try:
            result = await func(*args, **kwargs)
            return result
        finally:
            end_time = time.perf_counter()
            duration = (end_time - start_time) * 1000  # ms
            logger.debug(f"{func.__name__} took {duration:.2f}ms")
    
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            end_time = time.perf_counter()
            duration = (end_time - start_time) * 1000  # ms
            logger.debug(f"{func.__name__} took {duration:.2f}ms")
    
    return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper


class MultiLevelCacheManager:
    """다계층 캐시 매니저"""
    
    def __init__(
        self,
        l1_max_size: int = 1000,
        l1_max_memory_mb: int = 100,
        l2_cache_dir: str = "/tmp/hotly_cache",
        l2_max_size_mb: int = 500,
        redis_url: str = None
    ):
        self.l1_cache = L1MemoryCache(l1_max_size, l1_max_memory_mb)
        self.l2_cache = L2DiskCache(l2_cache_dir, l2_max_size_mb)
        self.l3_cache = L3RedisCache(redis_url)
        self.stats = CacheStats()
        self.key_manager = CacheKeyManager()
        
    async def connect(self):
        """캐시 시스템 연결 초기화"""
        await self.l3_cache.connect()
    
    async def disconnect(self):
        """캐시 시스템 연결 해제"""
        await self.l3_cache.disconnect()
    
    @cache_timing
    async def get(self, key: str) -> Tuple[Optional[Any], str]:
        """
        계층별 캐시에서 데이터 조회
        
        Returns:
            Tuple[data, cache_level]: 데이터와 캐시 레벨 ("L1", "L2", "L3", "MISS")
        """
        start_time = time.perf_counter()
        
        try:
            # L1 메모리 캐시 확인
            data = self.l1_cache.get(key)
            if data is not None:
                self.stats.hit_count += 1
                self.stats.response_times.append((time.perf_counter() - start_time) * 1000)
                return data, "L1"
            
            # L2 디스크 캐시 확인
            data = self.l2_cache.get(key)
            if data is not None:
                # L1으로 승격
                self.l1_cache.set(key, data, 3600)
                self.stats.hit_count += 1
                self.stats.response_times.append((time.perf_counter() - start_time) * 1000)
                return data, "L2"
            
            # L3 Redis 캐시 확인
            data = await self.l3_cache.get(key)
            if data is not None:
                # L2, L1으로 승격
                self.l2_cache.set(key, data, 86400)
                self.l1_cache.set(key, data, 3600)
                self.stats.hit_count += 1
                self.stats.response_times.append((time.perf_counter() - start_time) * 1000)
                return data, "L3"
            
            # 캐시 미스
            self.stats.miss_count += 1
            self.stats.response_times.append((time.perf_counter() - start_time) * 1000)
            return None, "MISS"
            
        except Exception as e:
            self.stats.error_count += 1
            logger.error(f"Cache get error for key {key}: {e}")
            return None, "ERROR"
    
    @cache_timing
    async def set(
        self,
        key: str,
        value: Any,
        l1_ttl: int = 3600,
        l2_ttl: int = 86400,
        l3_ttl: int = 604800
    ) -> bool:
        """
        모든 계층에 캐시 설정
        
        Args:
            key: 캐시 키
            value: 저장할 데이터
            l1_ttl: L1 TTL (초)
            l2_ttl: L2 TTL (초) 
            l3_ttl: L3 TTL (초)
        """
        try:
            # 모든 계층에 동시 저장
            results = await asyncio.gather(
                asyncio.create_task(asyncio.to_thread(self.l1_cache.set, key, value, l1_ttl)),
                asyncio.create_task(asyncio.to_thread(self.l2_cache.set, key, value, l2_ttl)),
                self.l3_cache.set(key, value, l3_ttl),
                return_exceptions=True
            )
            
            success_count = sum(1 for result in results if result is True)
            self.stats.set_count += 1
            
            # 최소 하나 성공하면 성공으로 간주
            return success_count > 0
            
        except Exception as e:
            self.stats.error_count += 1
            logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """모든 계층에서 캐시 삭제"""
        try:
            # 모든 계층에서 동시 삭제
            results = await asyncio.gather(
                asyncio.create_task(asyncio.to_thread(self.l1_cache.delete, key)),
                asyncio.create_task(asyncio.to_thread(self.l2_cache.delete, key)),
                self.l3_cache.delete(key),
                return_exceptions=True
            )
            
            success_count = sum(1 for result in results if result is True)
            self.stats.delete_count += 1
            
            return success_count > 0
            
        except Exception as e:
            self.stats.error_count += 1
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    async def invalidate_pattern(self, pattern: str) -> int:
        """패턴 매칭으로 캐시 무효화"""
        try:
            # L3에서 패턴으로 키 검색
            keys = await self.l3_cache.keys(pattern)
            
            # 각 계층에서 삭제
            delete_tasks = []
            for key in keys:
                delete_tasks.extend([
                    asyncio.create_task(asyncio.to_thread(self.l1_cache.delete, key)),
                    asyncio.create_task(asyncio.to_thread(self.l2_cache.delete, key)),
                    self.l3_cache.delete(key)
                ])
            
            if delete_tasks:
                await asyncio.gather(*delete_tasks, return_exceptions=True)
            
            return len(keys)
            
        except Exception as e:
            self.stats.error_count += 1
            logger.error(f"Cache invalidate pattern error for {pattern}: {e}")
            return 0
    
    async def warm_cache(self, data_map: Dict[str, Any]) -> int:
        """캐시 워밍"""
        try:
            warm_tasks = []
            for key, value in data_map.items():
                warm_tasks.append(self.set(key, value))
            
            results = await asyncio.gather(*warm_tasks, return_exceptions=True)
            success_count = sum(1 for result in results if result is True)
            
            logger.info(f"Cache warmed: {success_count}/{len(data_map)} keys")
            return success_count
            
        except Exception as e:
            logger.error(f"Cache warm error: {e}")
            return 0
    
    async def get_comprehensive_stats(self) -> Dict[str, Any]:
        """종합 캐시 통계 조회"""
        try:
            l1_stats = self.l1_cache.get_stats()
            l2_stats = self.l2_cache.get_stats()
            l3_stats = await self.l3_cache.get_stats()
            
            return {
                "overall": {
                    "hit_count": self.stats.hit_count,
                    "miss_count": self.stats.miss_count,
                    "total_requests": self.stats.total_requests,
                    "hit_rate": self.stats.hit_rate,
                    "set_count": self.stats.set_count,
                    "delete_count": self.stats.delete_count,
                    "error_count": self.stats.error_count,
                    "avg_response_time_ms": self.stats.avg_response_time
                },
                "l1_memory": l1_stats,
                "l2_disk": l2_stats,
                "l3_redis": l3_stats
            }
            
        except Exception as e:
            logger.error(f"Failed to get comprehensive stats: {e}")
            return {}
    
    def create_key(self, domain: str, resource_id: str, params: Optional[Dict] = None) -> str:
        """캐시 키 생성"""
        return self.key_manager.generate_key(domain, resource_id, params)


# 전역 캐시 매니저 인스턴스
cache_manager: Optional[MultiLevelCacheManager] = None


async def get_cache_manager() -> MultiLevelCacheManager:
    """캐시 매니저 싱글톤 인스턴스 반환"""
    global cache_manager
    if cache_manager is None:
        cache_manager = MultiLevelCacheManager()
        await cache_manager.connect()
    return cache_manager


async def cleanup_cache_manager():
    """캐시 매니저 정리"""
    global cache_manager
    if cache_manager:
        await cache_manager.disconnect()
        cache_manager = None


# 기존 인터페이스 호환성 유지


class CacheService(ABC):
    """캐시 서비스 추상 인터페이스"""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """값 조회"""
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """값 저장"""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """값 삭제"""
        pass
    
    @abstractmethod
    async def delete_pattern(self, pattern: str) -> int:
        """패턴 매칭하는 키들 삭제"""
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """키 존재 여부 확인"""
        pass
    
    @abstractmethod
    async def get_stats(self) -> Dict[str, Any]:
        """캐시 통계 반환"""
        pass


class RedisCacheService(CacheService):
    """Redis 기반 캐시 서비스"""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        """
        Redis 캐시 서비스 초기화
        
        Args:
            redis_client: Redis 클라이언트 (None이면 기본값 사용)
        """
        self.redis = redis_client or self._create_redis_client()
        self.stats = {
            'hit_count': 0,
            'miss_count': 0,
            'error_count': 0
        }
    
    def _create_redis_client(self) -> redis.Redis:
        """Redis 클라이언트 생성"""
        return redis.Redis(
            host=getattr(settings, 'REDIS_HOST', 'localhost'),
            port=getattr(settings, 'REDIS_PORT', 6379),
            db=getattr(settings, 'REDIS_DB', 0),
            password=getattr(settings, 'REDIS_PASSWORD', None),
            decode_responses=True
        )
    
    async def get(self, key: str) -> Optional[Any]:
        """값 조회"""
        try:
            value = await self.redis.get(key)
            if value is not None:
                self.stats['hit_count'] += 1
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value
            else:
                self.stats['miss_count'] += 1
                return None
        except Exception as e:
            logger.error(f"Redis get error for key {key}: {e}")
            self.stats['error_count'] += 1
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """값 저장"""
        try:
            # JSON 직렬화 시도
            if not isinstance(value, str):
                value = json.dumps(value, default=str)
            
            if ttl:
                await self.redis.setex(key, ttl, value)
            else:
                await self.redis.set(key, value)
            
            return True
        except Exception as e:
            logger.error(f"Redis set error for key {key}: {e}")
            self.stats['error_count'] += 1
            return False
    
    async def delete(self, key: str) -> bool:
        """값 삭제"""
        try:
            result = await self.redis.delete(key)
            return result > 0
        except Exception as e:
            logger.error(f"Redis delete error for key {key}: {e}")
            self.stats['error_count'] += 1
            return False
    
    async def delete_pattern(self, pattern: str) -> int:
        """패턴 매칭하는 키들 삭제"""
        try:
            keys = await self.redis.keys(pattern)
            if keys:
                deleted_count = await self.redis.delete(*keys)
                return deleted_count
            return 0
        except Exception as e:
            logger.error(f"Redis delete pattern error for pattern {pattern}: {e}")
            self.stats['error_count'] += 1
            return 0
    
    async def exists(self, key: str) -> bool:
        """키 존재 여부 확인"""
        try:
            result = await self.redis.exists(key)
            return result > 0
        except Exception as e:
            logger.error(f"Redis exists error for key {key}: {e}")
            self.stats['error_count'] += 1
            return False
    
    async def get_stats(self) -> Dict[str, Any]:
        """캐시 통계 반환"""
        total_requests = self.stats['hit_count'] + self.stats['miss_count']
        hit_rate = self.stats['hit_count'] / total_requests if total_requests > 0 else 0.0
        
        return {
            'hit_count': self.stats['hit_count'],
            'miss_count': self.stats['miss_count'],
            'error_count': self.stats['error_count'],
            'hit_rate': hit_rate,
            'total_requests': total_requests,
        }


class MemoryCacheService(CacheService):
    """메모리 기반 캐시 서비스 (테스트/개발용)"""
    
    def __init__(self):
        """메모리 캐시 서비스 초기화"""
        self.cache: Dict[str, Any] = {}
        self.expiry: Dict[str, datetime] = {}
        self.stats = {
            'hit_count': 0,
            'miss_count': 0,
            'error_count': 0
        }
    
    def _is_expired(self, key: str) -> bool:
        """키가 만료되었는지 확인"""
        if key not in self.expiry:
            return False
        return datetime.utcnow() > self.expiry[key]
    
    async def get(self, key: str) -> Optional[Any]:
        """값 조회"""
        try:
            if key in self.cache and not self._is_expired(key):
                self.stats['hit_count'] += 1
                return self.cache[key]
            else:
                # 만료된 키 정리
                if key in self.cache:
                    del self.cache[key]
                    if key in self.expiry:
                        del self.expiry[key]
                
                self.stats['miss_count'] += 1
                return None
        except Exception as e:
            logger.error(f"Memory cache get error for key {key}: {e}")
            self.stats['error_count'] += 1
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """값 저장"""
        try:
            self.cache[key] = value
            
            if ttl:
                self.expiry[key] = datetime.utcnow() + timedelta(seconds=ttl)
            elif key in self.expiry:
                del self.expiry[key]
            
            return True
        except Exception as e:
            logger.error(f"Memory cache set error for key {key}: {e}")
            self.stats['error_count'] += 1
            return False
    
    async def delete(self, key: str) -> bool:
        """값 삭제"""
        try:
            if key in self.cache:
                del self.cache[key]
                if key in self.expiry:
                    del self.expiry[key]
                return True
            return False
        except Exception as e:
            logger.error(f"Memory cache delete error for key {key}: {e}")
            self.stats['error_count'] += 1
            return False
    
    async def delete_pattern(self, pattern: str) -> int:
        """패턴 매칭하는 키들 삭제"""
        try:
            import re
            # 간단한 와일드카드를 정규식으로 변환
            regex_pattern = pattern.replace('*', '.*').replace('?', '.')
            compiled_pattern = re.compile(regex_pattern)
            
            keys_to_delete = [
                key for key in self.cache.keys() 
                if compiled_pattern.match(key)
            ]
            
            for key in keys_to_delete:
                del self.cache[key]
                if key in self.expiry:
                    del self.expiry[key]
            
            return len(keys_to_delete)
        except Exception as e:
            logger.error(f"Memory cache delete pattern error for pattern {pattern}: {e}")
            self.stats['error_count'] += 1
            return 0
    
    async def exists(self, key: str) -> bool:
        """키 존재 여부 확인"""
        try:
            return key in self.cache and not self._is_expired(key)
        except Exception as e:
            logger.error(f"Memory cache exists error for key {key}: {e}")
            self.stats['error_count'] += 1
            return False
    
    async def get_stats(self) -> Dict[str, Any]:
        """캐시 통계 반환"""
        total_requests = self.stats['hit_count'] + self.stats['miss_count']
        hit_rate = self.stats['hit_count'] / total_requests if total_requests > 0 else 0.0
        
        return {
            'hit_count': self.stats['hit_count'],
            'miss_count': self.stats['miss_count'],
            'error_count': self.stats['error_count'],
            'hit_rate': hit_rate,
            'total_requests': total_requests,
            'cache_size': len(self.cache),
        }


# 전역 캐시 서비스 인스턴스
_cache_service: Optional[CacheService] = None


async def get_cache_service() -> CacheService:
    """캐시 서비스 인스턴스 반환"""
    global _cache_service
    
    if _cache_service is None:
        # Redis 연결 시도, 실패하면 메모리 캐시로 대체
        try:
            redis_client = redis.Redis(
                host=getattr(settings, 'REDIS_HOST', 'localhost'),
                port=getattr(settings, 'REDIS_PORT', 6379),
                db=getattr(settings, 'REDIS_DB', 0),
                password=getattr(settings, 'REDIS_PASSWORD', None),
                decode_responses=True
            )
            
            # Redis 연결 테스트
            await redis_client.ping()
            _cache_service = RedisCacheService(redis_client)
            logger.info("Using Redis cache service")
            
        except Exception as e:
            logger.warning(f"Failed to connect to Redis, using memory cache: {e}")
            _cache_service = MemoryCacheService()
    
    return _cache_service


def get_cache_service_sync() -> CacheService:
    """동기식 캐시 서비스 반환 (테스트용)"""
    return MemoryCacheService()