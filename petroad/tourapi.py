"""한국관광공사 「반려동물 동반여행 서비스」(KorPetTourService1, 기관 B551011) 클라이언트.

- 서비스키(TOUR_API_KEY)는 서버(파이썬)에서만 사용.
- 키가 없거나 PETROAD_DATA_SOURCE=mock 이면 목업 폴백 → 키 없이도 동작.
- 실 API 실패 시에도 목업으로 폴백해 데모가 끊기지 않음.

※ 엔드포인트/필드명은 공공데이터포털 최신 명세로 재확인 필요.
"""

from __future__ import annotations

import math
import os
from concurrent.futures import ThreadPoolExecutor

import requests

from .models import Place, PlaceCategory, RawPetTourFields
from .mock_places import MOCK_PLACES, get_mock_place
from .normalize import normalize_policy

BASE = "https://apis.data.go.kr/B551011/KorPetTourService2"
COMMON = {"MobileOS": "ETC", "MobileApp": "PetRoad", "_type": "json",
          "numOfRows": "50", "pageNo": "1", "arrange": "A"}

_CONTENT_TYPE_TO_CATEGORY: dict[str, PlaceCategory] = {
    "12": "관광지", "14": "관광지", "28": "공원", "32": "숙박", "38": "관광지", "39": "음식점",
}


def data_source_mode() -> str:
    forced = os.getenv("PETROAD_DATA_SOURCE", "auto")
    if forced == "mock":
        return "mock"
    if forced == "live":
        return "live"
    return "live" if os.getenv("TOUR_API_KEY") else "mock"


def _category_of(content_type_id: str = "", title: str = "") -> PlaceCategory:
    base = _CONTENT_TYPE_TO_CATEGORY.get(content_type_id)
    if base:
        if base == "음식점" and any(k in title.lower() for k in ("카페", "커피", "coffee", "cafe")):
            return "카페"
        return base
    if "카페" in title or "커피" in title:
        return "카페"
    if any(k in title for k in ("공원", "숲", "놀이터")):
        return "공원"
    return "기타"


def _iso(v: str) -> str:
    if len(v) >= 8 and v[:8].isdigit():
        return f"{v[:4]}-{v[4:6]}-{v[6:8]}"
    return "1970-01-01"


def _request(operation: str, params: dict) -> dict:
    key = os.getenv("TOUR_API_KEY", "")
    query = {**COMMON, **params, "serviceKey": key}
    res = requests.get(f"{BASE}/{operation}", params=query, timeout=20)
    res.raise_for_status()
    try:
        return res.json()
    except ValueError as exc:  # 인증 실패 시 XML/plain 응답
        raise RuntimeError(f"TourAPI 비정상 응답(인증키/파라미터 확인): {res.text[:120]}") from exc


def _items(json_obj: dict) -> list[dict]:
    body = (json_obj or {}).get("response", {}).get("body", {})
    items = body.get("items")
    if not items:
        return []
    item = items.get("item")
    if not item:
        return []
    return item if isinstance(item, list) else [item]


def _map_list_item(raw: dict) -> Place:
    def s(k: str) -> str:
        v = raw.get(k)
        return "" if v is None else str(v)

    pet_tour = RawPetTourFields()  # 목록엔 상세 동반정보 없음
    return Place(
        content_id=s("contentid"), title=s("title"),
        category=_category_of(s("contenttypeid"), s("title")),
        lat=float(s("mapy") or 0), lng=float(s("mapx") or 0),
        address=" ".join(filter(None, [s("addr1"), s("addr2")])),
        tel=s("tel"), images=[x for x in [s("firstimage") or s("firstimage2")] if x],
        source="official", updated_at=_iso(s("modifiedtime")),
        pet_tour=pet_tour, policy=normalize_policy(pet_tour),
    )


def _pick_pet_fields(raw: dict) -> RawPetTourFields:
    def g(k: str) -> str:
        v = raw.get(k)
        return "" if v is None else str(v)

    return RawPetTourFields(
        acmpyTypeCd=g("acmpyTypeCd"), acmpyPsblCpam=g("acmpyPsblCpam"),
        acmpyNeedMtr=g("acmpyNeedMtr"), etcAcmpyInfo=g("etcAcmpyInfo"),
        relaAcdntRiskMtr=g("relaAcdntRiskMtr"), relaPosesFclty=g("relaPosesFclty"),
        relaRntlPrdlst=g("relaRntlPrdlst"), relaPurcPrdlst=g("relaPurcPrdlst"),
    )


def haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    R = 6371000
    d_lat = math.radians(lat2 - lat1)
    d_lng = math.radians(lng2 - lng1)
    a = (math.sin(d_lat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lng / 2) ** 2)
    return 2 * R * math.asin(math.sqrt(a))


def _filter_mock(keyword: str = "", category: str = "", lat: float | None = None,
                 lng: float | None = None, radius: float = 100000.0) -> list[Place]:
    result = list(MOCK_PLACES)
    if keyword:
        kw = keyword.strip()
        result = [p for p in result if kw in p.title or kw in p.address]
    if category and category != "전체":
        result = [p for p in result if p.category == category]
    if lat is not None and lng is not None:
        scored = [(p, haversine(lat, lng, p.lat, p.lng)) for p in result]
        result = [p for p, d in sorted(scored, key=lambda x: x[1]) if d <= radius]
    return result


# ───────── 공개 API ─────────

def fetch_places(keyword: str = "", area_code: str = "", content_type_id: str = "",
                 lat: float | None = None, lng: float | None = None,
                 radius: float = 5000.0) -> tuple[list[Place], str]:
    """(장소목록, 실제소스) 반환. 실제소스는 'live'|'mock'|'live→mock'."""
    if data_source_mode() == "mock":
        return _filter_mock(keyword, "", lat, lng, radius or 100000.0), "mock"

    operation = "areaBasedList2"
    params: dict = {}
    if lat is not None and lng is not None:
        operation = "locationBasedList2"
        params.update(mapX=str(lng), mapY=str(lat), radius=str(int(radius or 5000)))
    elif keyword:
        operation = "searchKeyword2"
        params["keyword"] = keyword
    elif area_code:
        params["areaCode"] = area_code
    if content_type_id:
        params["contentTypeId"] = content_type_id

    try:
        data = _request(operation, params)
        places = [p for p in map(_map_list_item, _items(data)) if p.content_id]
        _enrich_policies(places)  # 목록엔 동반조건이 없어 상세(detailPetTour2)로 보강
        return places, "live"
    except Exception as exc:  # noqa: BLE001 — 데모 지속을 위해 폴백
        print(f"[tourapi] fetch_places fallback to mock: {exc}")
        return _filter_mock(keyword, "", lat, lng, radius or 100000.0), "live→mock"


def _fetch_pet_tour(content_id: str) -> RawPetTourFields | None:
    try:
        items = _items(_request("detailPetTour2", {"contentId": content_id}))
        return _pick_pet_fields(items[0]) if items else None
    except Exception:  # noqa: BLE001
        return None


def _enrich_policies(places: list[Place], limit: int = 24) -> None:
    """목록 장소에 동반조건(detailPetTour2)을 병렬로 채워 policy 를 재계산한다."""
    subset = places[:limit]
    if not subset:
        return
    with ThreadPoolExecutor(max_workers=8) as ex:
        fields_list = list(ex.map(lambda p: _fetch_pet_tour(p.content_id), subset))
    for place, fields in zip(subset, fields_list):
        if fields is not None:
            place.pet_tour = fields
            place.policy = normalize_policy(fields)


def fetch_place_detail(content_id: str) -> tuple[Place | None, str]:
    if data_source_mode() == "mock":
        return get_mock_place(content_id), "mock"
    try:
        # KorService2 의 detailCommon2 는 구식 YN 파라미터를 받지 않는다(모든 항목 기본 반환).
        common = _request("detailCommon2", {"contentId": content_id})
        c_items = _items(common)
        if not c_items:
            return get_mock_place(content_id), "live→mock"
        c = c_items[0]

        try:
            pet = _items(_request("detailPetTour2", {"contentId": content_id}))
        except Exception:  # noqa: BLE001
            pet = []
        pet_fields = _pick_pet_fields(pet[0]) if pet else RawPetTourFields()

        def s(k: str) -> str:
            v = c.get(k)
            return "" if v is None else str(v)

        place = Place(
            content_id=content_id, title=s("title"),
            category=_category_of(s("contenttypeid"), s("title")),
            lat=float(s("mapy") or 0), lng=float(s("mapx") or 0),
            address=" ".join(filter(None, [s("addr1"), s("addr2")])),
            tel=s("tel"), overview=s("overview"),
            images=[x for x in [s("firstimage")] if x],
            source="official", updated_at=_iso(s("modifiedtime")),
            pet_tour=pet_fields, policy=normalize_policy(pet_fields),
        )
        return place, "live"
    except Exception as exc:  # noqa: BLE001
        print(f"[tourapi] fetch_place_detail fallback to mock: {exc}")
        return get_mock_place(content_id), "live→mock"
