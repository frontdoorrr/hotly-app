"""코스 최적화 알고리즘 (Genetic Algorithm 기반)."""
import math
import random  # nosec B311  # Genetic Algorithm은 보안 목적이 아닌 최적화용
from dataclasses import dataclass
from typing import Dict, List, Optional

from app.schemas.course_recommendation import OptimizationMetrics
from app.services.maps.route_calculator import (
    RouteCalculator,
    RouteMatrix,
    TransportMethod,
)


@dataclass
class Place:
    """장소 정보."""

    id: str
    name: str
    latitude: float
    longitude: float
    category: str
    avg_stay_duration: int  # 평균 체류 시간 (분)


@dataclass
class OptimizationResult:
    """최적화 결과."""

    optimized_order: List[Place]
    optimization_score: float
    total_distance: int  # 미터
    total_duration: int  # 분
    metrics: OptimizationMetrics


class CourseOptimizer:
    """코스 최적화 엔진 (Genetic Algorithm)."""

    def __init__(self, route_calculator: Optional[RouteCalculator] = None) -> None:
        """초기화."""
        self.distance_weight = 0.4
        self.time_weight = 0.25
        self.variety_weight = 0.2
        self.preference_weight = 0.15

        # GA 파라미터
        self.population_size = 50
        self.generations = 100
        self.mutation_rate = 0.2
        self.elite_size = 5

        # RouteCalculator (실제 경로 계산용)
        self.route_calculator = route_calculator or RouteCalculator()
        self._route_matrix: Optional[RouteMatrix] = None
        self._place_id_to_index: Dict[str, int] = {}  # Place ID → Matrix Index 매핑

    def set_weights(
        self,
        distance: float = 0.4,
        time: float = 0.25,
        variety: float = 0.2,
        preference: float = 0.15,
    ) -> None:
        """가중치 설정."""
        self.distance_weight = distance
        self.time_weight = time
        self.variety_weight = variety
        self.preference_weight = preference

    async def optimize(
        self, places: List[Place], transport_method: str = "walking"
    ) -> OptimizationResult:
        """
        유전 알고리즘으로 최적 순서 찾기.

        Args:
            places: 방문할 장소 목록
            transport_method: 이동 수단

        Returns:
            최적화된 코스

        Raises:
            ValueError: 장소 개수가 범위 밖
        """
        # 입력 검증
        if len(places) < 3:
            raise ValueError("최소 3개 이상의 장소가 필요합니다")
        if len(places) > 6:
            raise ValueError("최대 6개까지 장소를 선택할 수 있습니다")

        # Place ID → Index 매핑 생성
        self._place_id_to_index = {p.id: i for i, p in enumerate(places)}

        # RouteMatrix 계산 (한 번만 계산하여 재사용)
        places_dict = [
            {
                "id": p.id,
                "name": p.name,
                "latitude": p.latitude,
                "longitude": p.longitude,
            }
            for p in places
        ]

        transport_enum = TransportMethod(transport_method)
        self._route_matrix = await self.route_calculator.calculate_route_matrix(
            places_dict, transport_enum
        )

        # 유전 알고리즘 실행
        best_order = self._run_genetic_algorithm(places, transport_method)

        # 메트릭 계산
        total_distance = self._calculate_total_distance(best_order)
        total_duration = self._calculate_total_duration(best_order, transport_method)
        metrics = self._calculate_metrics(best_order, transport_method)

        # 최적화 점수 계산
        optimization_score = metrics.overall_score

        return OptimizationResult(
            optimized_order=best_order,
            optimization_score=optimization_score,
            total_distance=total_distance,
            total_duration=total_duration,
            metrics=metrics,
        )

    def _run_genetic_algorithm(
        self, places: List[Place], transport_method: str
    ) -> List[Place]:
        """유전 알고리즘 실행."""
        # 초기 집단 생성
        population = self._create_initial_population(places)

        for generation in range(self.generations):
            # 적합도 평가
            fitness_scores = [
                self._evaluate_fitness(individual, transport_method)
                for individual in population
            ]

            # 엘리트 선택
            elite = self._select_elite(population, fitness_scores)

            # 새로운 세대 생성
            new_population = elite.copy()

            while len(new_population) < self.population_size:
                # 부모 선택 (토너먼트 선택)
                parent1 = self._tournament_selection(population, fitness_scores)
                parent2 = self._tournament_selection(population, fitness_scores)

                # 교차 (Order Crossover)
                child = self._crossover(parent1, parent2)

                # 돌연변이
                if random.random() < self.mutation_rate:  # nosec B311
                    child = self._mutate(child)

                new_population.append(child)

            population = new_population

        # 최종 세대에서 최고 개체 선택
        final_fitness = [
            self._evaluate_fitness(individual, transport_method)
            for individual in population
        ]
        best_idx = final_fitness.index(max(final_fitness))
        return population[best_idx]

    def _create_initial_population(self, places: List[Place]) -> List[List[Place]]:
        """초기 집단 생성 (무작위 순열)."""
        population = []
        for _ in range(self.population_size):
            individual = places.copy()
            random.shuffle(individual)
            population.append(individual)
        return population

    def _evaluate_fitness(
        self, individual: List[Place], transport_method: str
    ) -> float:
        """적합도 평가 (점수가 높을수록 좋음)."""
        # 거리 점수 (짧을수록 좋음)
        total_distance = self._calculate_total_distance(individual)
        max_possible_distance = self._estimate_max_distance(individual)
        distance_score = max(0, 100 * (1 - total_distance / max_possible_distance))

        # 시간 점수 (짧을수록 좋음)
        total_duration = self._calculate_total_duration(individual, transport_method)
        time_score = max(0, 100 * (1 - total_duration / (len(individual) * 150)))

        # 카테고리 다양성 점수
        variety_score = self._calculate_variety_score(individual)

        # 가중합
        fitness = (
            self.distance_weight * distance_score
            + self.time_weight * time_score
            + self.variety_weight * variety_score
        )

        return fitness

    def _calculate_variety_score(self, places: List[Place]) -> float:
        """카테고리 다양성 점수."""
        # 연속된 같은 카테고리에 페널티
        penalty = 0
        for i in range(len(places) - 1):
            if places[i].category == places[i + 1].category:
                penalty += 30  # 연속 같은 카테고리마다 -30점

        return max(0, 100 - penalty)

    def _select_elite(
        self, population: List[List[Place]], fitness_scores: List[float]
    ) -> List[List[Place]]:
        """엘리트 선택."""
        # 적합도 상위 N개 선택 (인덱스 기반으로 안전하게 정렬)
        indexed_scores = [(score, idx) for idx, score in enumerate(fitness_scores)]
        indexed_scores.sort(reverse=True, key=lambda x: x[0])
        elite_indices = [idx for _, idx in indexed_scores[: self.elite_size]]
        return [population[idx] for idx in elite_indices]

    def _tournament_selection(
        self, population: List[List[Place]], fitness_scores: List[float]
    ) -> List[Place]:
        """토너먼트 선택 (3개 중 최고 선택)."""
        tournament_size = 3
        indices = random.sample(range(len(population)), tournament_size)  # nosec B311
        tournament_fitness = [fitness_scores[i] for i in indices]
        winner_idx = indices[tournament_fitness.index(max(tournament_fitness))]
        return population[winner_idx].copy()

    def _crossover(self, parent1: List[Place], parent2: List[Place]) -> List[Place]:
        """순서 교차 (Order Crossover, OX)."""
        size = len(parent1)
        start, end = sorted(random.sample(range(size), 2))  # nosec B311

        # parent1에서 일부 구간 복사
        child: List[Place | None] = [None] * size
        child[start:end] = parent1[start:end]

        # parent2에서 나머지 채우기
        parent2_filtered = [p for p in parent2 if p not in child]
        j = 0
        for i in range(size):
            if child[i] is None:
                child[i] = parent2_filtered[j]
                j += 1

        # mypy를 위한 타입 체크 (None은 모두 채워짐)
        return [p for p in child if p is not None]

    def _mutate(self, individual: List[Place]) -> List[Place]:
        """돌연변이 (두 위치 교환)."""
        mutated = individual.copy()
        idx1, idx2 = random.sample(range(len(mutated)), 2)  # nosec B311
        mutated[idx1], mutated[idx2] = mutated[idx2], mutated[idx1]
        return mutated

    def _calculate_total_distance(self, places: List[Place]) -> int:
        """총 이동 거리 계산 (미터)."""
        if self._route_matrix is None:
            # Fallback: Haversine 직접 계산
            total: float = 0
            for i in range(len(places) - 1):
                dist = self.calculate_distance(
                    places[i].latitude,
                    places[i].longitude,
                    places[i + 1].latitude,
                    places[i + 1].longitude,
                )
                total += dist
            return int(total)

        # RouteMatrix 사용 (이미 계산된 경로 데이터)
        total = 0
        for i in range(len(places) - 1):
            current_idx = self._place_id_to_index.get(places[i].id)
            next_idx = self._place_id_to_index.get(places[i + 1].id)

            if current_idx is not None and next_idx is not None:
                total += self._route_matrix.distances[current_idx][next_idx]

        return total

    def _calculate_total_duration(
        self, places: List[Place], transport_method: str
    ) -> int:
        """총 소요 시간 계산 (분)."""
        # 체류 시간
        stay_duration = sum(p.avg_stay_duration for p in places)

        # 이동 시간
        travel_duration = 0

        if self._route_matrix is not None:
            # RouteMatrix의 duration 사용 (초 단위 → 분 단위 변환)
            for i in range(len(places) - 1):
                current_idx = self._place_id_to_index.get(places[i].id)
                next_idx = self._place_id_to_index.get(places[i + 1].id)

                if current_idx is not None and next_idx is not None:
                    duration_seconds = self._route_matrix.durations[current_idx][
                        next_idx
                    ]
                    travel_duration += int(duration_seconds / 60)
        else:
            # Fallback: 거리 기반 추정
            for i in range(len(places) - 1):
                dist = self.calculate_distance(
                    places[i].latitude,
                    places[i].longitude,
                    places[i + 1].latitude,
                    places[i + 1].longitude,
                )
                travel_duration += self._estimate_travel_time(dist, transport_method)

        return stay_duration + travel_duration

    def _estimate_travel_time(self, distance: float, transport_method: str) -> int:
        """이동 시간 추정 (분)."""
        # 평균 속도 (km/h)
        speeds = {
            "walking": 4,  # 도보 4km/h
            "transit": 20,  # 대중교통 20km/h
            "driving": 30,  # 자동차 30km/h
            "mixed": 15,  # 혼합 15km/h
        }

        speed = speeds.get(transport_method, 4)
        distance_km = distance / 1000
        time_hours = distance_km / speed
        time_minutes = int(time_hours * 60)

        return time_minutes

    def _estimate_max_distance(self, places: List[Place]) -> float:
        """최대 가능 거리 추정 (최악의 경우)."""
        # 모든 장소 쌍 간 거리 중 최대값들의 합
        distances = []
        for i in range(len(places)):
            for j in range(i + 1, len(places)):
                dist = self.calculate_distance(
                    places[i].latitude,
                    places[i].longitude,
                    places[j].latitude,
                    places[j].longitude,
                )
                distances.append(dist)

        # 상위 N-1개 거리의 합 (최악의 경로)
        distances.sort(reverse=True)
        return sum(distances[: len(places) - 1])

    def calculate_distance(
        self, lat1: float, lon1: float, lat2: float, lon2: float
    ) -> float:
        """
        두 지점 간 거리 계산 (Haversine formula).

        Args:
            lat1, lon1: 시작점 위도/경도
            lat2, lon2: 도착점 위도/경도

        Returns:
            거리 (미터)
        """
        R = 6371000  # 지구 반지름 (미터)

        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)

        a = (
            math.sin(delta_phi / 2) ** 2
            + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        distance = R * c
        return distance

    def _calculate_metrics(
        self, places: List[Place], transport_method: str
    ) -> OptimizationMetrics:
        """최적화 메트릭 계산."""
        # 거리 점수
        total_distance = self._calculate_total_distance(places)
        max_distance = self._estimate_max_distance(places)
        distance_score = max(0, 100 * (1 - total_distance / max_distance))

        # 시간 점수
        total_duration = self._calculate_total_duration(places, transport_method)
        time_score = max(0, 100 * (1 - total_duration / (len(places) * 150)))

        # 다양성 점수
        variety_score = self._calculate_variety_score(places)

        # 선호도 점수 (현재는 기본값)
        preference_score = 70.0

        # 종합 점수 (가중치 합으로 정규화하여 0-100 범위 보장)
        weight_sum = (
            self.distance_weight
            + self.time_weight
            + self.variety_weight
            + self.preference_weight
        )

        if weight_sum > 0:
            overall_score = (
                self.distance_weight * distance_score
                + self.time_weight * time_score
                + self.variety_weight * variety_score
                + self.preference_weight * preference_score
            ) / weight_sum
        else:
            overall_score = 0.0

        # 0-100 범위 보장
        overall_score = min(100.0, max(0.0, overall_score))

        return OptimizationMetrics(
            distance_score=round(distance_score, 2),
            time_score=round(time_score, 2),
            variety_score=round(variety_score, 2),
            preference_score=round(preference_score, 2),
            overall_score=round(overall_score, 2),
        )
