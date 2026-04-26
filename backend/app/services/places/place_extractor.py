"""ArchivedContent → Place 자동 추출 서비스."""

import hashlib
import logging
import re
from typing import List, Optional
from uuid import UUID

from app.crud.place import place as place_crud
from app.db.session import SessionLocal
from app.schemas.place import PlaceCategory, PlaceCreate
from app.services.maps.kakao_map_service import (
    ConfigError,
    KakaoMapService,
    KakaoMapServiceError,
)

logger = logging.getLogger(__name__)

_GENERIC_ENTITY_BLOCKLIST = {
    "맛집", "카페", "식당", "술집", "바", "음식점", "핫플",
    "cafe", "brunch", "restaurant", "bar",
}
_REGION_SUFFIX_RE = re.compile(r"^[가-힣]{1,4}(시|군|구|동|읍|면)(청|사무소|역)?$")
_NAME_DISPLAY_MAX = 80
_KEYWORD_FALLBACK_MAX = 20

_CATEGORY_KEYWORDS: List[tuple[PlaceCategory, List[str]]] = [
    (PlaceCategory.CAFE, ["카페", "커피", "coffee", "cafe"]),
    (
        PlaceCategory.RESTAURANT,
        ["식당", "맛집", "레스토랑", "음식", "밥집", "한식", "일식", "중식", "양식"],
    ),
    # "바" 단독은 "스타벅스", "바이럴" 등과 오매칭되므로 제외
    (PlaceCategory.BAR, ["술집", "펍", "이자카야"]),
    (PlaceCategory.ACCOMMODATION, ["호텔", "숙소", "펜션"]),
    (PlaceCategory.SHOPPING, ["쇼핑", "마트", "백화점", "편의점"]),
    (PlaceCategory.TOURIST_ATTRACTION, ["공원", "박물관", "미술관", "관광", "명소"]),
    (PlaceCategory.ENTERTAINMENT, ["영화", "볼링", "노래방", "공연"]),
]


def _infer_category(title: Optional[str], keywords: Optional[List[str]]) -> PlaceCategory:
    haystack = " ".join(filter(None, [title or "", *(keywords or [])])).lower()
    for category, signals in _CATEGORY_KEYWORDS:
        if any(signal in haystack for signal in signals):
            return category
    return PlaceCategory.OTHER


def _safe_str(value, max_len: int) -> Optional[str]:
    if value is None:
        return None
    s = str(value).strip()
    return s[:max_len] if s else None


def _extract_region_token(
    named_entities: List[str], keywords_main: List[str]
) -> Optional[str]:
    """named_entities/keywords_main에서 지역(구/동/시 등) 토큰을 추출."""
    candidates: List[str] = []
    for src in (named_entities or []):
        if not src:
            continue
        candidates.extend(str(src).split())
    for src in (keywords_main or []):
        if not src:
            continue
        candidates.extend(str(src).split())
    for token in candidates:
        token = token.strip()
        if _REGION_SUFFIX_RE.match(token):
            return token
    return None


def _choose_entity(named_entities: List[str]) -> Optional[str]:
    """named_entities에서 generic이 아닌 첫 토큰을 반환."""
    for entity in (named_entities or []):
        if not entity:
            continue
        text = str(entity).strip()
        if not text:
            continue
        if text.lower() in _GENERIC_ENTITY_BLOCKLIST:
            continue
        return text
    return None


def _build_keyword_candidates(
    name: Optional[str],
    named_entities: List[str],
    keywords_main: List[str],
) -> List[str]:
    """Kakao 키워드 검색에 시도할 후보 쿼리를 우선순위 순으로 생성."""
    region = _extract_region_token(named_entities, keywords_main)
    entity = _choose_entity(named_entities)
    short_name = (name or "").strip()[:_KEYWORD_FALLBACK_MAX]

    raw_candidates: List[Optional[str]] = []
    if region and entity:
        raw_candidates.append(f"{region} {entity}")
    if entity:
        raw_candidates.append(entity)
    if region and short_name:
        raw_candidates.append(f"{region} {short_name}")
    if short_name:
        raw_candidates.append(short_name)

    seen: set[str] = set()
    result: List[str] = []
    for cand in raw_candidates:
        if not cand:
            continue
        c = cand.strip()
        if not c or c in seen:
            continue
        seen.add(c)
        result.append(c)
    return result


def _pick_best_result(
    results: List[dict], entity: Optional[str]
) -> Optional[dict]:
    """Kakao 결과에서 entity 이름과 가장 잘 매칭되는 항목을 선택."""
    if not results:
        return None
    if entity:
        needle = entity.lower().replace(" ", "")
        for r in results:
            place_name = str(r.get("place_name") or "").lower().replace(" ", "")
            if needle and needle in place_name:
                if r.get("latitude") is not None and r.get("longitude") is not None:
                    return r
    first = results[0]
    if first.get("latitude") is not None and first.get("longitude") is not None:
        return first
    return None


def _choose_place_name(
    title: Optional[str], named_entities: List[str]
) -> Optional[str]:
    """place.name 컬럼에 들어갈 깔끔한 가게명을 결정."""
    entity = _choose_entity(named_entities)
    if entity:
        return entity[:_NAME_DISPLAY_MAX]
    if title:
        cleaned = title.strip()
        if cleaned:
            return cleaned[:_NAME_DISPLAY_MAX]
    return None


class PlaceExtractorService:
    """ArchivedContent 데이터로부터 Place를 추출해 DB에 저장한다."""

    async def extract_and_create(
        self,
        *,
        content_type: str,
        title: Optional[str],
        url: str,
        platform: str,
        keywords_main: Optional[List[str]],
        named_entities: Optional[List[str]],
        type_specific_data: Optional[dict],
        user_id: UUID,
    ) -> None:
        """아카이브 데이터를 Place로 변환해 저장한다. 모든 예외를 내부에서 처리한다."""
        if content_type != "place":
            return

        try:
            await self._run(
                title=title,
                url=url,
                platform=platform,
                keywords_main=keywords_main,
                named_entities=named_entities,
                type_specific_data=type_specific_data or {},
                user_id=user_id,
            )
        except Exception:
            logger.exception(
                "Place extraction failed for url=%s user_id=%s", url, user_id
            )

    async def _run(
        self,
        *,
        title: Optional[str],
        url: str,
        platform: str,
        keywords_main: Optional[List[str]],
        named_entities: Optional[List[str]],
        type_specific_data: dict,
        user_id: UUID,
    ) -> None:
        # 기존 의미의 raw_name — source_content_hash 입력 보존용 (dedup 호환)
        raw_name = (title or "").strip() or (
            (named_entities or [None])[0] if named_entities else None
        )
        if not raw_name:
            logger.info("Skipping place extraction: no usable name for url=%s", url)
            return

        # place.name 컬럼에 저장할 깔끔한 표시명
        display_name = _choose_place_name(title, named_entities or []) or raw_name

        tsd = type_specific_data
        address = _safe_str(tsd.get("address"), 500)

        keywords: List[str] = list(keywords_main or [])[:10]
        menus = tsd.get("menus")
        if isinstance(menus, list):
            keywords += [str(m) for m in menus[:5] if m]
        keywords = list(dict.fromkeys(keywords))[:15]  # 중복 제거, max 15

        website = _safe_str(tsd.get("website"), 500)
        if website and not website.startswith(("http://", "https://")):
            website = None

        source_hash = hashlib.sha256(
            f"{raw_name}_{address or ''}_{url}".encode()
        ).hexdigest()

        # 캡션이 entity와 다르면 description으로 보존
        description: Optional[str] = None
        if title and title.strip() and title.strip() != display_name:
            description = title.strip()[:2000]

        place_create = PlaceCreate(
            name=display_name[:255],
            description=description,
            address=address,
            phone=_safe_str(tsd.get("phone"), 50),
            website=website,
            opening_hours=_safe_str(tsd.get("hours"), 2000),
            price_range=_safe_str(tsd.get("price_range"), 50),
            category=_infer_category(title, keywords_main),
            keywords=keywords,
            source_url=url,
            source_platform=platform,
            source_content_hash=source_hash,
            ai_confidence=0.8 if address else 0.5,
        )

        latitude, longitude = await self._get_coordinates(
            name=display_name,
            address=address,
            named_entities=named_entities or [],
            keywords_main=keywords_main or [],
        )
        if latitude is not None and longitude is not None:
            place_create.latitude = latitude
            place_create.longitude = longitude

        db = SessionLocal()
        try:
            existing = place_crud.get_by_source_hash(
                db, user_id=user_id, source_content_hash=source_hash
            )
            if existing:
                logger.info(
                    "Place already exists for source_content_hash=%s, skipping",
                    source_hash,
                )
                return

            created = place_crud.create_with_user(db, obj_in=place_create, user_id=user_id)
            if latitude is None or longitude is None:
                logger.warning(
                    "Place created without coordinates: id=%s name=%s url=%s",
                    created.id,
                    created.name,
                    url,
                )
            else:
                logger.info(
                    "Place created: id=%s name=%s lat=%s lng=%s",
                    created.id,
                    created.name,
                    latitude,
                    longitude,
                )
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    async def _get_coordinates(
        self,
        *,
        name: str,
        address: Optional[str],
        named_entities: List[str],
        keywords_main: List[str],
    ) -> tuple[Optional[float], Optional[float]]:
        try:
            kakao = KakaoMapService()
        except ConfigError:
            logger.error("KAKAO_API_KEY not configured — skipping geocoding")
            return None, None

        if address:
            try:
                coords = await kakao._address_to_coordinate_async(address)
                return coords["latitude"], coords["longitude"]
            except ValueError:
                logger.info(
                    "Address not found in Kakao: %r, trying keyword search", address
                )
            except Exception as exc:
                logger.warning("Kakao geocoding failed for address %r: %s", address, exc)

        entity = _choose_entity(named_entities)
        candidates = _build_keyword_candidates(name, named_entities, keywords_main)
        for kw in candidates:
            try:
                results = await kakao._search_places_async(kw, None, None, None, 5)
            except Exception as exc:
                logger.warning("Kakao keyword search failed for %r: %s", kw, exc)
                continue
            picked = _pick_best_result(results or [], entity)
            if picked:
                logger.info(
                    "Kakao keyword hit: query=%r picked=%r",
                    kw,
                    picked.get("place_name"),
                )
                return picked["latitude"], picked["longitude"]

        logger.info(
            "Kakao keyword search exhausted candidates=%s", candidates
        )
        return None, None
