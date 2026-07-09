"""자유 텍스트 동반조건 → 구조화 PetPolicy (TypeScript lib/normalize.ts 포팅).

원칙: 언급이 없거나 불확실하면 None / low-confidence 로 남긴다.
      (거짓 판정보다 "확인 필요"가 안전하다.)
"""

from __future__ import annotations

import re

from .models import Confidence, PetPolicy, RawPetTourFields, SizeClass, Species

# ── 종 (일반 "반려동물"은 종 미특정 → dog 에 포함하지 않음) ──
RE_DOG = re.compile(r"강아지|반려견|애견|소형견|중형견|대형견|견종|멍멍이|댕댕이|\b개\b")
RE_CAT = re.compile(r"고양이|반려묘|냥이|길냥")
RE_PETS_GENERAL = re.compile(r"반려동물|애완동물")

# ── 명시적 금지 ("제한 없이" 같은 부정은 제외) ──
RE_DOG_DENY = re.compile(
    r"(?:강아지|반려견|애견|대형견|개)(?:는|은|만|\s)*(?:동반|출입|입장)?(?:은|는|이)?\s*"
    r"(?:불가능|불가|금지|받지\s*않|안\s*됩|제한\s*됩|제한\s*되|제한\s*대상)"
)
RE_CAT_DENY = re.compile(
    r"(?:고양이|반려묘|냥)(?:는|은|만|\s)*(?:동반|출입|입장)?(?:은|는|이)?\s*"
    r"(?:불가능|불가|금지|받지\s*않|안\s*됩)"
)
RE_ALL_PETS_DENY = re.compile(
    r"(?:반려동물|애완동물|모든\s*동물)[^.\n]{0,8}(?:전면\s*)?"
    r"(?:동반\s*불가|출입\s*불가|입장\s*불가|불가능|금지|제한(?!\s*없)|불가|받지\s*않|안\s*됩)"
)

# ── 조건 ──
RE_CARRIER = re.compile(r"이동장|케이지|캐리어|이동\s*가방|이동가방")
RE_LEASH = re.compile(r"목줄|리드\s*줄|리드줄|가슴\s*줄|하네스")
RE_MUZZLE = re.compile(r"입마개")
RE_VACCINE = re.compile(r"예방\s*접종|예방접종|광견병|접종\s*증명|백신|접종\s*완료")
RE_EXTRA_FEE = re.compile(r"추가\s*요금|추가\s*비용|별도\s*요금|입장료|이용료|보증금|유료")
RE_INDOOR_NO = re.compile(r"실내\s*(?:는)?\s*(?:불가|금지|출입\s*불가|이용\s*불가|입장\s*불가)")
RE_OUTDOOR_ONLY = re.compile(
    r"(?:야외|실외|테라스|옥외)\s*(?:공간)?\s*(?:에\s*한|만|한함|한정|만\s*가능|만\s*이용|만\s*동반)"
)

FACILITY_KEYWORDS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"급수(?:대|기)|음수대"), "급수대"),
    (re.compile(r"놀이터|놀이\s*시설|운동장|운동\s*공간"), "놀이터"),
    (re.compile(r"배변\s*(?:봉투|패드|봉지)"), "배변용품"),
    (re.compile(r"전용\s*(?:공간|구역|시설|공원)|반려동물\s*전용"), "전용공간"),
    (re.compile(r"펜스|울타리"), "펜스"),
    (re.compile(r"포토\s*존|포토존"), "포토존"),
    (re.compile(r"샤워|발\s*세척|세족"), "세족시설"),
    (re.compile(r"주차"), "주차장"),
    (re.compile(r"쉼터|휴게"), "휴게공간"),
]

BREED_RESTRICT_KEYWORDS = ["맹견", "대형견", "투견", "사냥개", "특정견종", "특정 견종"]

_EMPTY_RE = re.compile(r"^(?:없음|-|해당\s*없음|없습니다|N/?A)?$", re.IGNORECASE)


def _detect_species(text: str) -> list[Species] | None:
    allow: set[Species] = set()
    if RE_CAT.search(text):
        allow.add("고양이")
    if RE_DOG.search(text):
        allow.add("개")
    if RE_DOG_DENY.search(text):
        allow.discard("개")
    if RE_CAT_DENY.search(text):
        allow.discard("고양이")
    if RE_ALL_PETS_DENY.search(text) and not allow:
        return []
    if not allow and (RE_DOG_DENY.search(text) or RE_CAT_DENY.search(text)):
        return []
    if not allow:
        return None
    # 정렬로 결정적 결과 (고양이, 개 순 → 개, 고양이로 통일)
    order = {"개": 0, "고양이": 1, "기타": 2}
    return sorted(allow, key=lambda s: order[s])


def _detect_max_weight(text: str) -> float | None:
    maxima: list[float] = []
    for m in re.finditer(r"(\d+(?:\.\d+)?)\s*(?:kg|킬로그램|킬로|㎏)\s*(이하|미만|까지|이내)?", text, re.I):
        value = float(m.group(1))
        after = text[m.end(): m.end() + 3]
        if re.search(r"이상|초과", after):
            continue
        maxima.append(value)
    return min(maxima) if maxima else None


def _detect_size(text: str) -> list[SizeClass] | None:
    if re.search(r"소형(?:견|묘|동물)?\s*(?:만|에\s*한|한정|한함)", text):
        return ["소형"]
    sizes: list[SizeClass] = []
    if "소형" in text:
        sizes.append("소형")
    if re.search(r"중형", text) and not re.search(r"중형.*(불가|제한|금지)", text):
        sizes.append("중형")
    large_no = re.search(r"대형(?:견|동물)?\s*(?:불가|제한|금지|입장\s*불가)", text)
    if re.search(r"대형", text) and not large_no:
        sizes.append("대형")
    # 중복 제거 (순서 유지)
    seen: list[SizeClass] = []
    for s in sizes:
        if s not in seen:
            seen.append(s)
    return seen or None


def _detect_breed_restrictions(text: str) -> list[str]:
    found: list[str] = []
    for kw in BREED_RESTRICT_KEYWORDS:
        pattern = re.compile(
            kw + r"[^.\n]{0,10}(불가|제한|금지|입장\s*불가|출입\s*금지|동반\s*불가|안\s*됩|안됩)"
        )
        if pattern.search(text):
            label = "특정견종" if kw == "특정 견종" else kw
            if label not in found:
                found.append(label)
    return found


def _detect_facilities(text: str) -> list[str]:
    found: list[str] = []
    for pattern, label in FACILITY_KEYWORDS:
        if pattern.search(text) and label not in found:
            found.append(label)
    return found


def _join_raw(raw: RawPetTourFields) -> str:
    parts = []
    for v in raw.values():
        v = (v or "").strip()
        if v and not _EMPTY_RE.match(v):
            parts.append(v)
    return " \n ".join(parts)


def _score_confidence(text: str, policy: dict) -> Confidence:
    if not text.strip():
        return "low"
    signals = 0
    if policy["allowed_species"] is not None:
        signals += 1
    if policy["max_weight_kg"] is not None:
        signals += 1
    if policy["size_class"]:
        signals += 1
    if (
        policy["carrier_required"]
        or policy["outdoor_only"]
        or policy["leash_required"]
        or policy["muzzle_required"]
        or policy["vaccine_required"]
    ):
        signals += 1
    if policy["facilities"]:
        signals += 1

    if signals == 0:
        return "low"
    if signals >= 3 or (
        policy["allowed_species"] is not None
        and (policy["max_weight_kg"] is not None or policy["size_class"])
    ):
        return "high"
    return "medium"


def normalize_policy(raw: RawPetTourFields) -> PetPolicy:
    text = _join_raw(raw)
    species_text = " ".join(
        filter(None, [raw.acmpyPsblCpam, raw.etcAcmpyInfo, raw.acmpyTypeCd, text])
    )
    need_text = " ".join(filter(None, [raw.acmpyNeedMtr, raw.etcAcmpyInfo, text]))
    facility_text = " ".join(
        filter(None, [raw.relaPosesFclty, raw.relaRntlPrdlst, raw.relaPurcPrdlst, text])
    )

    partial = {
        "allowed_species": _detect_species(species_text),
        "max_weight_kg": _detect_max_weight(species_text),
        "size_class": _detect_size(species_text),
        "carrier_required": bool(RE_CARRIER.search(need_text)),
        "outdoor_only": bool(RE_INDOOR_NO.search(text) or RE_OUTDOOR_ONLY.search(text)),
        "leash_required": bool(RE_LEASH.search(need_text)),
        "muzzle_required": bool(RE_MUZZLE.search(need_text)),
        "vaccine_required": bool(RE_VACCINE.search(need_text)),
        "extra_fee": bool(RE_EXTRA_FEE.search(text)),
        "breed_restrictions": _detect_breed_restrictions(species_text),
        "facilities": _detect_facilities(facility_text),
    }

    return PetPolicy(
        **partial,
        raw_text=text,
        confidence=_score_confidence(text, partial),
    )
