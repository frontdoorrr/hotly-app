"""ArchivedContent → Place 자동 추출 서비스."""

import hashlib
import logging
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
        name = (title or "").strip() or (
            (named_entities or [None])[0] if named_entities else None
        )
        if not name:
            logger.info("Skipping place extraction: no usable name for url=%s", url)
            return

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
            f"{name}_{address or ''}_{url}".encode()
        ).hexdigest()

        place_create = PlaceCreate(
            name=name[:255],
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

        latitude, longitude = await self._get_coordinates(name, address)
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
        self, name: str, address: Optional[str]
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

        try:
            results = await kakao._search_places_async(name, None, None, None, 3)
            if results and results[0].get("latitude") is not None:
                return results[0]["latitude"], results[0]["longitude"]
        except Exception as exc:
            logger.warning("Kakao keyword search failed for %r: %s", name, exc)

        return None, None
