"""펫로드(PetRoad) 공용 도메인 모델 (Streamlit 버전)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Optional

Species = Literal["개", "고양이", "기타"]
SizeClass = Literal["소형", "중형", "대형"]
PlaceCategory = Literal["관광지", "음식점", "카페", "숙박", "공원", "기타"]
Source = Literal["official", "report"]
Confidence = Literal["high", "medium", "low"]
VerdictStatus = Literal["OK", "COND", "NO", "UNKNOWN"]


@dataclass
class Pet:
    name: str
    species: Species = "개"
    breed: str = ""
    weight_kg: float = 5.0
    size_class: SizeClass = "소형"
    vaccinated: bool = False


@dataclass
class RawPetTourFields:
    acmpyTypeCd: str = ""
    acmpyPsblCpam: str = ""
    acmpyNeedMtr: str = ""
    etcAcmpyInfo: str = ""
    relaAcdntRiskMtr: str = ""
    relaPosesFclty: str = ""
    relaRntlPrdlst: str = ""
    relaPurcPrdlst: str = ""

    def values(self) -> list[str]:
        return [
            self.acmpyTypeCd,
            self.acmpyPsblCpam,
            self.acmpyNeedMtr,
            self.etcAcmpyInfo,
            self.relaAcdntRiskMtr,
            self.relaPosesFclty,
            self.relaRntlPrdlst,
            self.relaPurcPrdlst,
        ]


@dataclass
class PetPolicy:
    allowed_species: Optional[list[Species]]  # None = 미언급, [] = 명시적 없음
    max_weight_kg: Optional[float]
    size_class: Optional[list[SizeClass]]
    carrier_required: bool
    outdoor_only: bool
    leash_required: bool
    muzzle_required: bool
    vaccine_required: bool
    extra_fee: bool
    breed_restrictions: list[str]
    facilities: list[str]
    raw_text: str
    confidence: Confidence


@dataclass
class Verdict:
    status: VerdictStatus
    reasons: list[str] = field(default_factory=list)


@dataclass
class Place:
    content_id: str
    title: str
    category: PlaceCategory
    lat: float
    lng: float
    address: str
    images: list[str]
    source: Source
    updated_at: str
    pet_tour: RawPetTourFields
    policy: PetPolicy
    tel: str = ""
    overview: str = ""


VERDICT_META: dict[str, dict[str, str]] = {
    "OK": {"label": "입장 가능", "emoji": "✅", "color": "#22c55e"},
    "COND": {"label": "조건부 가능", "emoji": "⚠️", "color": "#f59e0b"},
    "NO": {"label": "입장 불가", "emoji": "❌", "color": "#ef4444"},
    "UNKNOWN": {"label": "확인 필요", "emoji": "❔", "color": "#3b82f6"},
}
