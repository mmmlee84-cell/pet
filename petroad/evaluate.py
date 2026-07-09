"""통과 판정 (TypeScript lib/evaluate.ts 포팅).

우선순위: NO > UNKNOWN > COND > OK
"""

from __future__ import annotations

from .models import Pet, PetPolicy, Verdict


def evaluate(pet: Pet, policy: PetPolicy) -> Verdict:
    no_reasons: list[str] = []
    cond_reasons: list[str] = []

    # 1) 명백한 불가
    if policy.allowed_species is not None and pet.species not in policy.allowed_species:
        allowed = "·".join(policy.allowed_species) if policy.allowed_species else "없음"
        no_reasons.append(f"{pet.species} 동반 불가 (허용: {allowed})")

    if policy.max_weight_kg is not None and pet.weight_kg > policy.max_weight_kg:
        no_reasons.append(f"체중 초과 ({pet.weight_kg}kg > 최대 {policy.max_weight_kg}kg)")

    if policy.size_class is not None and pet.size_class not in policy.size_class:
        no_reasons.append(f"크기 미허용 ({pet.size_class}견 · 허용: {'·'.join(policy.size_class)})")

    if _matches_breed_restriction(pet, policy):
        no_reasons.append(f"견종 제한 대상 ({'·'.join(policy.breed_restrictions)})")

    if no_reasons:
        return Verdict("NO", no_reasons)

    # 2) 정보 부족 → 확인 필요 (오판 금지)
    if policy.confidence == "low":
        return Verdict("UNKNOWN", ["동반조건 정보가 불충분합니다 · 방문 전 매장 확인을 권장해요"])
    if policy.allowed_species is None and not policy.raw_text.strip():
        return Verdict("UNKNOWN", ["동반 가능 반려동물 정보가 없습니다 · 확인이 필요해요"])

    # 3) 조건부
    if policy.outdoor_only:
        cond_reasons.append("야외·테라스만 동반 가능")
    if policy.carrier_required:
        cond_reasons.append("이동장(캐리어) 필수")
    if policy.muzzle_required:
        cond_reasons.append("입마개 필수")
    if policy.leash_required:
        cond_reasons.append("목줄 착용 필수")
    if policy.vaccine_required:
        cond_reasons.append(
            "예방접종 증빙 필요(완료됨)" if pet.vaccinated else "예방접종 증빙 필요(미완료)"
        )
    if policy.extra_fee:
        cond_reasons.append("추가 요금 발생")

    if cond_reasons:
        return Verdict("COND", cond_reasons)

    # 4) 제약 없음
    return Verdict("OK", [])


def _matches_breed_restriction(pet: Pet, policy: PetPolicy) -> bool:
    if not policy.breed_restrictions:
        return False
    breed = (pet.breed or "").strip()
    for restriction in policy.breed_restrictions:
        if breed and (restriction in breed or breed in restriction):
            return True
        if restriction == "대형견" and pet.size_class == "대형":
            return True
    return False
