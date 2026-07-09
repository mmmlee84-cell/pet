"""시연/오프라인용 목업 장소 12곳 (성수동·애월).

소형견(4kg) 기준: ✅ 가능 4 · ⚠️ 조건부 5 · ❌ 불가 3.
petTour 원문만 정의하고 policy 는 normalize_policy 로 계산 → 전체 파이프라인이 그대로 동작.
"""

from __future__ import annotations

from .models import Place, RawPetTourFields
from .normalize import normalize_policy


def _img(seed: str) -> str:
    return f"https://images.unsplash.com/photo-{seed}?auto=format&fit=crop&w=800&q=60"


_SEEDS = [
    # ── ✅ 가능 (4) ──
    dict(content_id="1001", title="성수 펫라운지 카페", category="카페", lat=37.5446, lng=127.0559,
         address="서울 성동구 성수동2가 성수로 100", tel="02-000-1001", images=[_img("1517849845537-4d257902454a")],
         overview="반려견과 함께 편하게 쉴 수 있는 넓은 카페. 전용 놀이 공간이 있어요.",
         source="official", updated_at="2026-07-07",
         pet_tour=RawPetTourFields(acmpyTypeCd="동반가능", acmpyPsblCpam="모든 반려견 자유 동반 가능",
                                   etcAcmpyInfo="실내외 모두 동반 가능합니다.",
                                   relaPosesFclty="급수대, 배변봉투 비치, 반려동물 전용 공간")),
    dict(content_id="1002", title="애월 오션뷰 카페", category="카페", lat=33.4635, lng=126.3101,
         address="제주 제주시 애월읍 애월해안로 20", tel="064-000-1002", images=[_img("1442512595331-e89e73853f31")],
         overview="바다가 보이는 통창 카페. 소·중형견 실내 동반 가능.",
         source="official", updated_at="2026-07-05",
         pet_tour=RawPetTourFields(acmpyPsblCpam="소형견 및 중형견 동반 가능 (10kg 이하)",
                                   etcAcmpyInfo="실내 동반 가능합니다.", relaPosesFclty="급수대")),
    dict(content_id="1003", title="서울숲 반려견 놀이터", category="공원", lat=37.5443, lng=127.0374,
         address="서울 성동구 뚝섬로 273", tel="", images=[_img("1601758228041-f3b2795255f1")],
         overview="울타리가 있는 오프리시 반려견 놀이터와 산책로.",
         source="official", updated_at="2026-07-08",
         pet_tour=RawPetTourFields(acmpyPsblCpam="반려견 동반 자유",
                                   relaPosesFclty="반려견 놀이터, 급수대, 운동장, 배변봉투")),
    dict(content_id="1004", title="성수 루프탑 전망대", category="관광지", lat=37.5451, lng=127.0566,
         address="서울 성동구 아차산로 50", tel="", images=[_img("1507525428034-b723cf961d3e")],
         overview="성수 일대를 조망할 수 있는 루프탑. 반려견 환영.",
         source="report", updated_at="2026-07-01",
         pet_tour=RawPetTourFields(acmpyPsblCpam="반려견 환영",
                                   etcAcmpyInfo="별도 제한 없이 자유롭게 동반하실 수 있어요.")),
    # ── ⚠️ 조건부 (5) ──
    dict(content_id="2001", title="성수 브런치 카페", category="카페", lat=37.5439, lng=127.0552,
         address="서울 성동구 연무장길 33", tel="02-000-2001", images=[_img("1554118811-1e0d58224f24")],
         overview="브런치 맛집. 반려견 동반 가능하나 목줄 착용이 필요해요.",
         source="official", updated_at="2026-07-06",
         pet_tour=RawPetTourFields(acmpyPsblCpam="반려견 동반 가능", acmpyNeedMtr="매장 내 목줄 착용 필수",
                                   relaPosesFclty="급수대")),
    dict(content_id="2002", title="애월 감귤밭 카페", category="카페", lat=33.4611, lng=126.3125,
         address="제주 제주시 애월읍 유수암로 77", tel="", images=[_img("1521401830884-6c03c1c87ebb")],
         overview="감귤밭 뷰 카페. 소형견은 이동장 이용 시 동반 가능.",
         source="official", updated_at="2026-06-28",
         pet_tour=RawPetTourFields(acmpyPsblCpam="소형견 동반 가능", acmpyNeedMtr="실내에서는 이동장(캐리어) 필수")),
    dict(content_id="2003", title="서울숲길 파스타", category="음식점", lat=37.5455, lng=127.0401,
         address="서울 성동구 서울숲2길 18", tel="02-000-2003", images=[_img("1481931098730-318b6f776db0")],
         overview="야외 테라스가 있는 파스타 전문점.",
         source="report", updated_at="2026-07-03",
         pet_tour=RawPetTourFields(acmpyPsblCpam="반려견 동반 가능", acmpyTypeCd="야외공간동반",
                                   etcAcmpyInfo="야외 테라스에 한해 동반 가능합니다.")),
    dict(content_id="2004", title="애월 반려견 펜션", category="숙박", lat=33.4652, lng=126.3088,
         address="제주 제주시 애월읍 하귀로 5", tel="064-000-2004", images=[_img("1568605114967-8130f3a36994")],
         overview="마당 있는 반려견 동반 펜션.",
         source="official", updated_at="2026-07-04",
         pet_tour=RawPetTourFields(acmpyPsblCpam="반려견 동반 가능한 펜션", acmpyNeedMtr="예방접종 증명서 지참 필수",
                                   etcAcmpyInfo="동반 시 추가 요금 20,000원",
                                   relaPosesFclty="마당 운동장, 급수대, 발 세척 시설")),
    dict(content_id="2005", title="성수 아트갤러리", category="관광지", lat=37.5432, lng=127.0578,
         address="서울 성동구 성수이로 88", tel="", images=[_img("1531913764164-f85c52e6e654")],
         overview="현대미술 갤러리. 반려견 동반 관람 가능(안전 수칙 준수).",
         source="official", updated_at="2026-06-30",
         pet_tour=RawPetTourFields(acmpyPsblCpam="반려견 동반 가능", acmpyNeedMtr="입마개 및 목줄 착용 필수",
                                   relaAcdntRiskMtr="작품 보호를 위해 목줄을 짧게 유지해 주세요.")),
    # ── ❌ 불가 (3) ──
    dict(content_id="3001", title="성수 파인다이닝", category="음식점", lat=37.5428, lng=127.0541,
         address="서울 성동구 왕십리로 200", tel="02-000-3001", images=[_img("1414235077428-338989a2e8c0")],
         overview="코스 요리 전문점. 반려동물 동반은 어렵습니다.",
         source="official", updated_at="2026-06-20",
         pet_tour=RawPetTourFields(acmpyPsblCpam="반려동물 출입 불가 매장입니다.")),
    dict(content_id="3002", title="애월 고양이 전용 카페", category="카페", lat=33.4668, lng=126.3112,
         address="제주 제주시 애월읍 애월북서길 12", tel="", images=[_img("1495360010541-f48722b34f7f")],
         overview="고양이를 위한 전용 공간. 강아지 동반은 불가.",
         source="official", updated_at="2026-06-25",
         pet_tour=RawPetTourFields(acmpyPsblCpam="고양이 전용 공간입니다.", etcAcmpyInfo="강아지 동반은 불가합니다.")),
    dict(content_id="3003", title="성수 실내 전시몰", category="관광지", lat=37.5461, lng=127.0533,
         address="서울 성동구 성수일로 10", tel="", images=[_img("1519567241046-7f570eee3ce6")],
         overview="대형 실내 전시 공간. 안내견만 출입 가능.",
         source="official", updated_at="2026-06-18",
         pet_tour=RawPetTourFields(acmpyPsblCpam="반려동물 동반이 제한되는 공간입니다.",
                                   etcAcmpyInfo="안내견만 출입 가능합니다.")),
]


def _build(seed: dict) -> Place:
    return Place(policy=normalize_policy(seed["pet_tour"]), **seed)


MOCK_PLACES: list[Place] = [_build(s) for s in _SEEDS]


def get_mock_place(content_id: str) -> Place | None:
    return next((p for p in MOCK_PLACES if p.content_id == content_id), None)
