"""
랭킹 실험 프레임워크 서비스 (Task 2-3-4)

A/B 테스트를 통한 검색 랭킹 알고리즘 성능 비교 및 최적화
- 실험 설계 및 관리
- 사용자 분할 및 배정
- 실험 결과 수집 및 분석
- 통계적 유의성 검정
- 자동 승자 결정 및 배포
"""

import hashlib
import json
import logging
import random
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4

import numpy as np
from scipy import stats
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import CacheService
from app.schemas.search_ranking import RankingFactor

logger = logging.getLogger(__name__)


class ExperimentStatus(str, Enum):
    """실험 상태"""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class VariantType(str, Enum):
    """변형 타입"""
    CONTROL = "control"
    TREATMENT = "treatment"


class MetricType(str, Enum):
    """지표 타입"""
    CLICK_THROUGH_RATE = "click_through_rate"
    DWELL_TIME = "dwell_time"
    CONVERSION_RATE = "conversion_rate"
    USER_SATISFACTION = "user_satisfaction"
    SEARCH_SUCCESS_RATE = "search_success_rate"
    REVENUE = "revenue"


class RankingExperimentService:
    """랭킹 실험 서비스"""
    
    def __init__(self, db: AsyncSession, cache_service: CacheService):
        """서비스 초기화"""
        self.db = db
        self.cache = cache_service
        
        # 실험 설정
        self.default_confidence_level = 0.95
        self.default_minimum_sample_size = 1000
        self.default_minimum_runtime_days = 7
        self.default_maximum_runtime_days = 30
        
        # 통계적 검정 설정
        self.alpha = 0.05  # 유의수준
        self.beta = 0.2    # 검정력 (1-beta = 0.8)
        self.minimum_effect_size = 0.05  # 최소 효과 크기
    
    async def create_experiment(
        self,
        name: str,
        description: str,
        variants: List[Dict[str, Any]],
        target_metrics: List[str],
        traffic_allocation: Optional[Dict[str, float]] = None,
        targeting_criteria: Optional[Dict[str, Any]] = None,
        estimated_duration_days: Optional[int] = None
    ) -> str:
        """
        새로운 랭킹 실험 생성
        
        Args:
            name: 실험 이름
            description: 실험 설명
            variants: 실험 변형들
            target_metrics: 목표 지표들
            traffic_allocation: 트래픽 할당 비율
            targeting_criteria: 타겟팅 조건
            estimated_duration_days: 예상 실행 기간
            
        Returns:
            실험 ID
        """
        try:
            experiment_id = str(uuid4())
            
            # 기본 트래픽 할당 설정
            if not traffic_allocation:
                num_variants = len(variants)
                equal_split = 1.0 / num_variants
                traffic_allocation = {
                    variant['name']: equal_split 
                    for variant in variants
                }
            
            # 실험 메타데이터 구성
            experiment_data = {
                'id': experiment_id,
                'name': name,
                'description': description,
                'status': ExperimentStatus.DRAFT.value,
                'variants': variants,
                'target_metrics': target_metrics,
                'traffic_allocation': traffic_allocation,
                'targeting_criteria': targeting_criteria or {},
                'estimated_duration_days': estimated_duration_days or self.default_minimum_runtime_days,
                'created_at': datetime.utcnow().isoformat(),
                'created_by': 'system',
                'sample_size_target': self.default_minimum_sample_size,
                'confidence_level': self.default_confidence_level
            }
            
            # 실험 데이터 저장
            await self.cache.set(
                f"experiment:{experiment_id}",
                experiment_data,
                ttl=86400 * 30  # 30일
            )
            
            # 활성 실험 목록에 추가
            active_experiments = await self.cache.get("active_experiments") or []
            active_experiments.append(experiment_id)
            await self.cache.set("active_experiments", active_experiments, ttl=86400 * 30)
            
            logger.info(f"Created ranking experiment: {name} (ID: {experiment_id})")
            
            return experiment_id
            
        except Exception as e:
            logger.error(f"Failed to create experiment: {e}")
            raise
    
    async def start_experiment(self, experiment_id: str) -> bool:
        """실험 시작"""
        try:
            experiment = await self._get_experiment(experiment_id)
            if not experiment:
                logger.error(f"Experiment not found: {experiment_id}")
                return False
            
            if experiment['status'] != ExperimentStatus.DRAFT.value:
                logger.error(f"Cannot start experiment in status: {experiment['status']}")
                return False
            
            # 실험 유효성 검증
            if not await self._validate_experiment(experiment):
                return False
            
            # 실험 시작
            experiment['status'] = ExperimentStatus.ACTIVE.value
            experiment['started_at'] = datetime.utcnow().isoformat()
            experiment['end_at'] = (
                datetime.utcnow() + 
                timedelta(days=experiment['estimated_duration_days'])
            ).isoformat()
            
            # 실험별 결과 저장소 초기화
            await self._initialize_experiment_storage(experiment_id)
            
            # 업데이트된 실험 저장
            await self.cache.set(
                f"experiment:{experiment_id}",
                experiment,
                ttl=86400 * 30
            )
            
            logger.info(f"Started experiment: {experiment_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to start experiment: {e}")
            return False
    
    async def assign_user_to_variant(
        self,
        experiment_id: str,
        user_id: UUID,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        사용자를 실험 변형에 할당
        
        Args:
            experiment_id: 실험 ID
            user_id: 사용자 ID
            context: 사용자 컨텍스트
            
        Returns:
            할당된 변형 이름 (또는 None)
        """
        try:
            experiment = await self._get_experiment(experiment_id)
            if not experiment or experiment['status'] != ExperimentStatus.ACTIVE.value:
                return None
            
            # 타겟팅 조건 확인
            if not await self._check_targeting_criteria(user_id, experiment, context):
                return None
            
            # 이미 할당된 변형 확인
            assignment_key = f"experiment_assignment:{experiment_id}:{user_id}"
            existing_assignment = await self.cache.get(assignment_key)
            if existing_assignment:
                return existing_assignment['variant']
            
            # 새로운 할당 결정
            variant = self._determine_variant_assignment(experiment, user_id)
            
            # 할당 정보 저장
            assignment_data = {
                'experiment_id': experiment_id,
                'user_id': str(user_id),
                'variant': variant,
                'assigned_at': datetime.utcnow().isoformat(),
                'context': context or {}
            }
            
            await self.cache.set(
                assignment_key,
                assignment_data,
                ttl=86400 * 31  # 실험보다 조금 더 오래 보관
            )
            
            # 실험 참가자 수 업데이트
            await self._increment_participant_count(experiment_id, variant)
            
            return variant
            
        except Exception as e:
            logger.error(f"Failed to assign user to variant: {e}")
            return None
    
    async def record_experiment_event(
        self,
        experiment_id: str,
        user_id: UUID,
        event_type: str,
        event_data: Dict[str, Any],
        timestamp: Optional[datetime] = None
    ) -> bool:
        """
        실험 이벤트 기록
        
        Args:
            experiment_id: 실험 ID
            user_id: 사용자 ID
            event_type: 이벤트 타입
            event_data: 이벤트 데이터
            timestamp: 이벤트 발생 시간
            
        Returns:
            기록 성공 여부
        """
        try:
            # 사용자 변형 할당 확인
            assignment_key = f"experiment_assignment:{experiment_id}:{user_id}"
            assignment = await self.cache.get(assignment_key)
            
            if not assignment:
                return False
            
            # 이벤트 데이터 구성
            event_record = {
                'experiment_id': experiment_id,
                'user_id': str(user_id),
                'variant': assignment['variant'],
                'event_type': event_type,
                'event_data': event_data,
                'timestamp': (timestamp or datetime.utcnow()).isoformat()
            }
            
            # 이벤트 저장
            events_key = f"experiment_events:{experiment_id}"
            events = await self.cache.get(events_key) or []
            events.append(event_record)
            
            # 이벤트 수 제한 (메모리 관리)
            if len(events) > 10000:
                events = events[-10000:]
            
            await self.cache.set(events_key, events, ttl=86400 * 31)
            
            # 실시간 지표 업데이트
            await self._update_realtime_metrics(experiment_id, assignment['variant'], event_record)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to record experiment event: {e}")
            return False
    
    async def get_experiment_results(self, experiment_id: str) -> Optional[Dict[str, Any]]:
        """실험 결과 조회"""
        try:
            experiment = await self._get_experiment(experiment_id)
            if not experiment:
                return None
            
            # 실험 데이터 수집
            events = await self.cache.get(f"experiment_events:{experiment_id}") or []
            assignments = await self._get_experiment_assignments(experiment_id)
            
            # 변형별 결과 분석
            variant_results = {}
            for variant_name in experiment['traffic_allocation'].keys():
                variant_results[variant_name] = await self._analyze_variant_results(
                    experiment, variant_name, events, assignments
                )
            
            # 통계적 유의성 검정
            statistical_tests = await self._perform_statistical_tests(
                experiment, variant_results
            )
            
            # 전체 결과 구성
            results = {
                'experiment_id': experiment_id,
                'experiment_name': experiment['name'],
                'status': experiment['status'],
                'duration': self._calculate_experiment_duration(experiment),
                'total_participants': len(assignments),
                'variant_results': variant_results,
                'statistical_tests': statistical_tests,
                'conclusion': self._generate_experiment_conclusion(statistical_tests),
                'analyzed_at': datetime.utcnow().isoformat()
            }
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to get experiment results: {e}")
            return None
    
    async def check_experiment_completion(self, experiment_id: str) -> bool:
        """실험 완료 조건 확인"""
        try:
            experiment = await self._get_experiment(experiment_id)
            if not experiment or experiment['status'] != ExperimentStatus.ACTIVE.value:
                return False
            
            # 최소 실행 시간 확인
            started_at = datetime.fromisoformat(experiment['started_at'])
            min_duration = timedelta(days=self.default_minimum_runtime_days)
            
            if datetime.utcnow() - started_at < min_duration:
                return False
            
            # 최대 실행 시간 확인
            max_duration = timedelta(days=self.default_maximum_runtime_days)
            if datetime.utcnow() - started_at >= max_duration:
                logger.info(f"Experiment {experiment_id} reached maximum duration")
                return True
            
            # 샘플 크기 확인
            assignments = await self._get_experiment_assignments(experiment_id)
            if len(assignments) < experiment['sample_size_target']:
                return False
            
            # 통계적 유의성 확인
            results = await self.get_experiment_results(experiment_id)
            if results and results['statistical_tests']:
                for test in results['statistical_tests'].values():
                    if test.get('statistically_significant', False):
                        logger.info(f"Experiment {experiment_id} reached statistical significance")
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to check experiment completion: {e}")
            return False
    
    async def stop_experiment(self, experiment_id: str, reason: str = "manual") -> bool:
        """실험 중지"""
        try:
            experiment = await self._get_experiment(experiment_id)
            if not experiment:
                return False
            
            # 실험 상태 업데이트
            experiment['status'] = ExperimentStatus.COMPLETED.value
            experiment['completed_at'] = datetime.utcnow().isoformat()
            experiment['completion_reason'] = reason
            
            # 최종 결과 생성 및 저장
            final_results = await self.get_experiment_results(experiment_id)
            if final_results:
                experiment['final_results'] = final_results
            
            # 업데이트된 실험 저장
            await self.cache.set(
                f"experiment:{experiment_id}",
                experiment,
                ttl=86400 * 90  # 완료된 실험은 90일간 보관
            )
            
            # 활성 실험 목록에서 제거
            active_experiments = await self.cache.get("active_experiments") or []
            if experiment_id in active_experiments:
                active_experiments.remove(experiment_id)
                await self.cache.set("active_experiments", active_experiments, ttl=86400 * 30)
            
            logger.info(f"Stopped experiment: {experiment_id} (reason: {reason})")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop experiment: {e}")
            return False
    
    async def get_user_experiment_config(self, user_id: UUID) -> Dict[str, str]:
        """사용자별 실험 설정 조회"""
        try:
            user_config = {}
            active_experiments = await self.cache.get("active_experiments") or []
            
            for experiment_id in active_experiments:
                assignment_key = f"experiment_assignment:{experiment_id}:{user_id}"
                assignment = await self.cache.get(assignment_key)
                
                if assignment:
                    user_config[experiment_id] = assignment['variant']
            
            return user_config
            
        except Exception as e:
            logger.error(f"Failed to get user experiment config: {e}")
            return {}
    
    async def _get_experiment(self, experiment_id: str) -> Optional[Dict[str, Any]]:
        """실험 데이터 조회"""
        return await self.cache.get(f"experiment:{experiment_id}")
    
    async def _validate_experiment(self, experiment: Dict[str, Any]) -> bool:
        """실험 유효성 검증"""
        # 변형 검증
        if not experiment.get('variants') or len(experiment['variants']) < 2:
            logger.error("Experiment must have at least 2 variants")
            return False
        
        # 트래픽 할당 검증
        allocation_sum = sum(experiment['traffic_allocation'].values())
        if abs(allocation_sum - 1.0) > 0.01:
            logger.error(f"Traffic allocation sum must equal 1.0, got {allocation_sum}")
            return False
        
        # 목표 지표 검증
        if not experiment.get('target_metrics'):
            logger.error("Experiment must have target metrics")
            return False
        
        return True
    
    async def _check_targeting_criteria(
        self,
        user_id: UUID,
        experiment: Dict[str, Any],
        context: Optional[Dict[str, Any]]
    ) -> bool:
        """타겟팅 조건 확인"""
        targeting = experiment.get('targeting_criteria', {})
        
        if not targeting:
            return True  # 타겟팅 조건이 없으면 모든 사용자 포함
        
        # 사용자 속성 기반 필터링
        if 'user_segments' in targeting:
            # 실제 구현에서는 사용자 세그먼트 확인
            pass
        
        # 컨텍스트 기반 필터링
        if context and 'required_context' in targeting:
            required = targeting['required_context']
            for key, value in required.items():
                if context.get(key) != value:
                    return False
        
        return True
    
    def _determine_variant_assignment(self, experiment: Dict[str, Any], user_id: UUID) -> str:
        """변형 할당 결정"""
        # 사용자 ID 기반 해시를 사용하여 일관된 할당
        user_hash = hashlib.md5(
            f"{experiment['id']}:{user_id}".encode()
        ).hexdigest()
        
        # 해시를 0-1 범위의 값으로 변환
        hash_value = int(user_hash[:8], 16) / (16**8)
        
        # 트래픽 할당 비율에 따라 변형 결정
        cumulative_allocation = 0.0
        for variant_name, allocation in experiment['traffic_allocation'].items():
            cumulative_allocation += allocation
            if hash_value <= cumulative_allocation:
                return variant_name
        
        # 기본값 (첫 번째 변형)
        return list(experiment['traffic_allocation'].keys())[0]
    
    async def _initialize_experiment_storage(self, experiment_id: str):
        """실험별 저장소 초기화"""
        # 이벤트 저장소
        await self.cache.set(f"experiment_events:{experiment_id}", [], ttl=86400 * 31)
        
        # 실시간 지표 저장소
        await self.cache.set(f"experiment_metrics:{experiment_id}", {}, ttl=86400 * 31)
    
    async def _increment_participant_count(self, experiment_id: str, variant: str):
        """참가자 수 증가"""
        metrics_key = f"experiment_metrics:{experiment_id}"
        metrics = await self.cache.get(metrics_key) or {}
        
        if 'participant_counts' not in metrics:
            metrics['participant_counts'] = {}
        
        metrics['participant_counts'][variant] = metrics['participant_counts'].get(variant, 0) + 1
        
        await self.cache.set(metrics_key, metrics, ttl=86400 * 31)
    
    async def _update_realtime_metrics(
        self,
        experiment_id: str,
        variant: str,
        event_record: Dict[str, Any]
    ):
        """실시간 지표 업데이트"""
        metrics_key = f"experiment_metrics:{experiment_id}"
        metrics = await self.cache.get(metrics_key) or {}
        
        event_type = event_record['event_type']
        
        # 변형별 이벤트 카운터
        if 'event_counts' not in metrics:
            metrics['event_counts'] = {}
        
        if variant not in metrics['event_counts']:
            metrics['event_counts'][variant] = {}
        
        metrics['event_counts'][variant][event_type] = (
            metrics['event_counts'][variant].get(event_type, 0) + 1
        )
        
        await self.cache.set(metrics_key, metrics, ttl=86400 * 31)
    
    async def _get_experiment_assignments(self, experiment_id: str) -> List[Dict[str, Any]]:
        """실험 할당 목록 조회"""
        # 실제 구현에서는 더 효율적인 조회 방법 필요
        # 여기서는 간단한 캐시 패턴 스캔
        assignments = []
        
        # 캐시에서 할당 데이터 수집 (실제로는 DB나 전용 저장소 사용)
        # 이는 예시 구현이며, 프로덕션에서는 최적화 필요
        
        return assignments
    
    async def _analyze_variant_results(
        self,
        experiment: Dict[str, Any],
        variant_name: str,
        events: List[Dict[str, Any]],
        assignments: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """변형별 결과 분석"""
        variant_events = [e for e in events if e.get('variant') == variant_name]
        variant_assignments = [a for a in assignments if a.get('variant') == variant_name]
        
        results = {
            'variant_name': variant_name,
            'participant_count': len(variant_assignments),
            'event_counts': {},
            'conversion_metrics': {},
            'performance_metrics': {}
        }
        
        # 이벤트 카운트
        for event in variant_events:
            event_type = event['event_type']
            results['event_counts'][event_type] = results['event_counts'].get(event_type, 0) + 1
        
        # 전환율 계산
        if results['participant_count'] > 0:
            click_events = results['event_counts'].get('click', 0)
            conversion_events = results['event_counts'].get('conversion', 0)
            
            results['conversion_metrics'] = {
                'click_through_rate': click_events / results['participant_count'],
                'conversion_rate': conversion_events / results['participant_count']
            }
        
        return results
    
    async def _perform_statistical_tests(
        self,
        experiment: Dict[str, Any],
        variant_results: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """통계적 유의성 검정"""
        tests = {}
        
        # 컨트롤 그룹과 처리 그룹 식별
        control_variant = None
        treatment_variants = []
        
        for variant_name, variant_data in variant_results.items():
            variant_info = next(
                (v for v in experiment['variants'] if v['name'] == variant_name),
                None
            )
            if variant_info and variant_info.get('type') == VariantType.CONTROL.value:
                control_variant = variant_name
            else:
                treatment_variants.append(variant_name)
        
        if not control_variant or not treatment_variants:
            return tests
        
        # 각 처리 그룹과 컨트롤 그룹 간의 비교
        control_results = variant_results[control_variant]
        
        for treatment_variant in treatment_variants:
            treatment_results = variant_results[treatment_variant]
            
            # 클릭률 비교 (비율 검정)
            test_result = self._perform_proportion_test(
                control_results, treatment_results, 'click_through_rate'
            )
            
            tests[f"{control_variant}_vs_{treatment_variant}"] = test_result
        
        return tests
    
    def _perform_proportion_test(
        self,
        control_results: Dict[str, Any],
        treatment_results: Dict[str, Any],
        metric: str
    ) -> Dict[str, Any]:
        """비율 검정 수행"""
        try:
            control_rate = control_results['conversion_metrics'].get(metric, 0)
            treatment_rate = treatment_results['conversion_metrics'].get(metric, 0)
            
            control_n = control_results['participant_count']
            treatment_n = treatment_results['participant_count']
            
            if control_n < 30 or treatment_n < 30:
                return {
                    'metric': metric,
                    'test_type': 'proportion_test',
                    'statistically_significant': False,
                    'insufficient_sample_size': True,
                    'p_value': None,
                    'effect_size': treatment_rate - control_rate,
                    'confidence_interval': None
                }
            
            # Z 검정 수행
            control_successes = int(control_rate * control_n)
            treatment_successes = int(treatment_rate * treatment_n)
            
            # scipy.stats를 사용한 비율 검정
            z_stat, p_value = stats.proportions_ztest(
                [control_successes, treatment_successes],
                [control_n, treatment_n]
            )
            
            # 효과 크기 (절대 차이)
            effect_size = treatment_rate - control_rate
            
            # 신뢰구간 계산
            se = np.sqrt(
                (control_rate * (1 - control_rate) / control_n) +
                (treatment_rate * (1 - treatment_rate) / treatment_n)
            )
            
            ci_lower = effect_size - 1.96 * se
            ci_upper = effect_size + 1.96 * se
            
            return {
                'metric': metric,
                'test_type': 'proportion_test',
                'statistically_significant': p_value < self.alpha,
                'p_value': float(p_value),
                'z_statistic': float(z_stat),
                'effect_size': effect_size,
                'confidence_interval': [ci_lower, ci_upper],
                'control_rate': control_rate,
                'treatment_rate': treatment_rate,
                'control_sample_size': control_n,
                'treatment_sample_size': treatment_n
            }
            
        except Exception as e:
            logger.error(f"Failed to perform proportion test: {e}")
            return {
                'metric': metric,
                'test_type': 'proportion_test',
                'error': str(e),
                'statistically_significant': False
            }
    
    def _generate_experiment_conclusion(self, statistical_tests: Dict[str, Dict[str, Any]]) -> str:
        """실험 결론 생성"""
        if not statistical_tests:
            return "No statistical tests performed"
        
        significant_tests = [
            test for test in statistical_tests.values()
            if test.get('statistically_significant', False)
        ]
        
        if not significant_tests:
            return "No statistically significant differences found"
        
        # 가장 큰 효과 크기를 가진 테스트 찾기
        best_test = max(
            significant_tests,
            key=lambda t: abs(t.get('effect_size', 0))
        )
        
        effect_size = best_test.get('effect_size', 0)
        if effect_size > 0:
            return f"Treatment variant shows significant improvement (effect size: {effect_size:.4f})"
        else:
            return f"Control variant performs better (effect size: {effect_size:.4f})"
    
    def _calculate_experiment_duration(self, experiment: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """실험 실행 기간 계산"""
        if 'started_at' not in experiment:
            return None
        
        started_at = datetime.fromisoformat(experiment['started_at'])
        end_time = datetime.utcnow()
        
        if experiment['status'] == ExperimentStatus.COMPLETED.value:
            end_time = datetime.fromisoformat(experiment['completed_at'])
        
        duration = end_time - started_at
        
        return {
            'total_seconds': duration.total_seconds(),
            'days': duration.days,
            'hours': duration.total_seconds() / 3600,
            'started_at': experiment['started_at'],
            'end_time': end_time.isoformat()
        }