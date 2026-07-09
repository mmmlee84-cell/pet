"""펫로드(PetRoad) — Streamlit 앱.

헛걸음 없는 반려동물 동반여행: 내 반려동물 기준으로 장소 입장 가능 여부를 도착 전에 판정.
실행:  streamlit run streamlit_app/app.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# 실행 방식(streamlit run / AppTest / python)과 무관하게 petroad 패키지 임포트 보장
sys.path.insert(0, str(Path(__file__).resolve().parent))

import pandas as pd
import streamlit as st

try:
    from dotenv import load_dotenv

    _root = Path(__file__).resolve().parents[1]
    load_dotenv(_root / ".env")
    load_dotenv(_root / ".env.local")  # Next.js 와 키 공유
    load_dotenv(Path(__file__).resolve().parent / ".env")
except Exception:  # noqa: BLE001
    pass

from petroad.evaluate import evaluate
from petroad.models import VERDICT_META, Pet, Place
from petroad.tourapi import data_source_mode, fetch_places

ROOT = Path(__file__).resolve().parents[1]
# 대문 이미지: 배포 시 자체 완결되도록 streamlit_app 내부를 우선 탐색 → 없으면 루트
HERO_IMG = next(
    (p for p in (Path(__file__).resolve().parent / "dc.png", ROOT / "dc.png") if p.exists()),
    Path(__file__).resolve().parent / "dc.png",
)

CATEGORIES = ["전체", "카페", "음식점", "관광지", "공원", "숙박"]
SPECIES = ["개", "고양이", "기타"]
SIZES = ["소형", "중형", "대형"]

st.set_page_config(page_title="펫로드 · 반려동물 동반여행", page_icon="🐾", layout="wide")


# ───────────────────── 배포용 키 주입 ─────────────────────
def _bootstrap_secret_key() -> None:
    """배포(Streamlit Cloud) 시 Settings→Secrets 의 TOUR_API_KEY 를 환경변수로 주입.
    우선순위: 사이드바 입력 > Streamlit Secrets > 로컬 .env
    (사이드바 입력은 이후 렌더에서 os.environ 을 직접 덮어쓴다.)"""
    try:
        key = st.secrets.get("TOUR_API_KEY", "")  # secrets.toml 없으면 예외/빈값
    except Exception:  # noqa: BLE001
        key = ""
    if key and not os.getenv("TOUR_API_KEY"):
        os.environ["TOUR_API_KEY"] = str(key).strip()


_bootstrap_secret_key()


# ───────────────────── 데이터 로딩(캐시) ─────────────────────
def _source_tag() -> str:
    # 데이터 소스/키가 바뀌면 캐시가 무효화되도록 태그에 포함
    return f"{data_source_mode()}|{bool(os.getenv('TOUR_API_KEY'))}"


@st.cache_data(ttl=300, show_spinner="장소 정보를 불러오는 중…")
def load_places(keyword: str, source_tag: str):
    return fetch_places(keyword=keyword)


def get_places(keyword: str = ""):
    return load_places(keyword, _source_tag())


# ───────────────────── 세션 상태 ─────────────────────
def _init_state() -> None:
    st.session_state.setdefault("pets", [])
    st.session_state.setdefault("active_pet", 0)
    st.session_state.setdefault("favorites", set())
    st.session_state.setdefault("courses", [])  # [{"title": str, "stops": [content_id]}]


_init_state()


def active_pet() -> Pet | None:
    pets = st.session_state["pets"]
    if not pets:
        return None
    idx = min(st.session_state["active_pet"], len(pets) - 1)
    return pets[idx]


def verdict_of(place: Place):
    pet = active_pet()
    return evaluate(pet, place.policy) if pet else None


# ───────────────────── UI 헬퍼 ─────────────────────
def verdict_badge_html(status: str, big: bool = False) -> str:
    meta = VERDICT_META[status]
    pad = "6px 14px" if big else "3px 10px"
    fs = "1.05rem" if big else "0.8rem"
    return (
        f"<span style='background:{meta['color']};color:#fff;border-radius:999px;"
        f"padding:{pad};font-size:{fs};font-weight:700;white-space:nowrap;'>"
        f"{meta['emoji']} {meta['label']}</span>"
    )


def render_header() -> None:
    # 대문: 투명 PNG(dc.png)를 작게 가운데 정렬 + 제목
    if HERO_IMG.exists():
        left, mid, right = st.columns([1, 1, 1])
        with mid:
            st.image(str(HERO_IMG), width=260)
    st.markdown(
        "<div style='text-align:center'>"
        "<h1 style='margin:0.1rem 0 0'>펫로드 <span style='color:#f26722'>🐾</span></h1>"
        "<p style='color:#6b7280;margin:0 0 0.6rem'>헛걸음 없는 반려동물 동반여행 — "
        "우리 아이가 <b>실제로 들어갈 수 있는지</b> 도착 전에 판정해요.</p>"
        "</div>",
        unsafe_allow_html=True,
    )


def render_sidebar() -> None:
    with st.sidebar:
        st.header("🐶 내 반려동물")
        pets = st.session_state["pets"]

        if pets:
            names = [f"{p.name} ({p.weight_kg:g}kg·{p.size_class})" for p in pets]
            idx = st.radio(
                "판정 기준 반려동물", range(len(pets)),
                format_func=lambda i: names[i],
                index=min(st.session_state["active_pet"], len(pets) - 1),
            )
            st.session_state["active_pet"] = idx
            if st.button("이 반려동물 삭제", width="stretch"):
                pets.pop(idx)
                st.session_state["active_pet"] = 0
                st.rerun()
        else:
            st.info("반려동물을 등록하면 장소마다 통과 판정을 볼 수 있어요.")

        with st.expander("➕ 반려동물 추가", expanded=not pets):
            with st.form("add_pet", clear_on_submit=True):
                name = st.text_input("이름", placeholder="예: 콩이")
                c1, c2 = st.columns(2)
                species = c1.selectbox("종", SPECIES)
                size = c2.selectbox("크기", SIZES)
                breed = st.text_input("품종(선택)", placeholder="예: 말티즈")
                weight = st.number_input("체중(kg)", min_value=0.0, max_value=100.0,
                                         value=5.0, step=0.5)
                vacc = st.checkbox("예방접종 완료")
                if st.form_submit_button("등록", width="stretch") and name.strip():
                    pets.append(Pet(name=name.strip(), species=species, breed=breed.strip(),
                                    weight_kg=float(weight), size_class=size, vaccinated=vacc))
                    st.session_state["active_pet"] = len(pets) - 1
                    st.rerun()

        st.divider()
        with st.expander("🔑 API 키 설정", expanded=not os.getenv("TOUR_API_KEY")):
            key_in = st.text_input(
                "관광공사 서비스키 (Decoding)",
                value=os.getenv("TOUR_API_KEY", ""),
                type="password",
                placeholder="공공데이터포털에서 발급한 인증키 붙여넣기",
                help="data.go.kr → '반려동물 동반여행 서비스' 활용신청 → 일반 인증키(Decoding) 값",
            )
            if key_in.strip():
                os.environ["TOUR_API_KEY"] = key_in.strip()
            st.caption("키가 없어도 목업 데이터로 정상 동작합니다.")

        mode = data_source_mode()
        label = "🟢 실데이터(TourAPI)" if mode == "live" else "🟡 목업 데이터"
        st.caption(f"데이터 소스: {label}")


# ───────────────────── 장소 카드 ─────────────────────
@st.dialog("현장 검증 제보")
def report_dialog(place: Place) -> None:
    st.write(f"**{place.title}** 방문 경험을 알려주세요.")
    opts = ["실제로 입장할 수 있었어요", "입장이 거부됐어요", "이동장이 필요했어요",
            "야외만 가능했어요", "추가 요금이 있었어요"]
    for o in opts:
        st.checkbox(o, key=f"rep_{place.content_id}_{o}")
    st.text_input("추가 메모(선택)", key=f"repnote_{place.content_id}")
    if st.button("제보 보내기", width="stretch"):
        st.success("제보 감사합니다! 다른 보호자들의 헛걸음을 막아줘요 🙌")


def render_place_card(place: Place, *, in_course: str | None = None) -> None:
    v = verdict_of(place)
    with st.container(border=True):
        top = st.columns([0.62, 0.38])
        with top[0]:
            st.markdown(f"**{place.title}**  \n<span style='color:#6b7280;font-size:0.85rem'>"
                        f"{place.category} · {place.address}</span>", unsafe_allow_html=True)
        with top[1]:
            if v:
                st.markdown(
                    f"<div style='text-align:right'>{verdict_badge_html(v.status)}</div>",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown("<div style='text-align:right;color:#9ca3af;font-size:0.8rem'>"
                            "반려동물 등록 필요</div>", unsafe_allow_html=True)

        if v and v.reasons:
            st.markdown("<span style='font-size:0.85rem'>· "
                        + " · ".join(v.reasons) + "</span>", unsafe_allow_html=True)

        src = "관광공사 인증" if place.source == "official" else "사용자 제보"
        conf = {"high": "정보 충실", "medium": "정보 보통", "low": "정보 부족"}[place.policy.confidence]
        st.caption(f"🛡 {src} · 🕑 {place.updated_at} 확인 · {conf}")

        with st.expander("동반조건 상세"):
            pol = place.policy
            rows = {
                "체중 제한": f"{pol.max_weight_kg:g}kg 이하" if pol.max_weight_kg else "제한 없음/미표기",
                "허용 크기": "·".join(f"{s}견" for s in pol.size_class) if pol.size_class else "제한 없음/미표기",
                "동반 가능": ("미표기(확인 필요)" if pol.allowed_species is None
                          else "동반 불가" if not pol.allowed_species else "·".join(pol.allowed_species)),
                "이용 공간": "야외·테라스만" if pol.outdoor_only else "실내 가능",
                "이동장": "필수" if pol.carrier_required else "불필요/미표기",
                "목줄": "필수" if pol.leash_required else "불필요/미표기",
                "입마개": "필수" if pol.muzzle_required else "불필요/미표기",
                "예방접종": "필요" if pol.vaccine_required else "불필요/미표기",
                "추가요금": "있음" if pol.extra_fee else "없음/미표기",
            }
            st.table(pd.DataFrame({"항목": list(rows), "내용": list(rows.values())}))
            if pol.breed_restrictions:
                st.markdown(f"🚫 **견종 제한:** {'·'.join(pol.breed_restrictions)}")
            if pol.facilities:
                st.markdown("✨ **구비시설:** " + " · ".join(pol.facilities))
            if pol.raw_text:
                st.caption("원문: " + pol.raw_text.replace("\n", " "))

        actions = st.columns(3)
        fav = st.session_state["favorites"]
        is_fav = place.content_id in fav
        if actions[0].button("⭐ 즐겨찾기" if not is_fav else "★ 해제",
                             key=f"fav_{place.content_id}_{in_course}", width="stretch"):
            fav.discard(place.content_id) if is_fav else fav.add(place.content_id)
            st.rerun()
        if actions[1].button("📍 코스에 추가", key=f"add_{place.content_id}_{in_course}",
                             width="stretch"):
            _add_to_course(place)
        if actions[2].button("🚩 제보", key=f"rep_{place.content_id}_{in_course}",
                             width="stretch"):
            report_dialog(place)


def _add_to_course(place: Place) -> None:
    courses = st.session_state["courses"]
    if not courses:
        courses.append({"title": "새 코스", "stops": []})
    if place.content_id not in courses[-1]["stops"]:
        courses[-1]["stops"].append(place.content_id)
    st.toast(f"'{courses[-1]['title']}'에 {place.title} 추가됨", icon="📍")


# ───────────────────── 지도 ─────────────────────
def render_map(places: list[Place]) -> None:
    pts = [p for p in places if p.lat and p.lng]
    if not pts:
        st.info("표시할 장소가 없어요.")
        return
    rows = []
    for p in pts:
        v = verdict_of(p)
        color = VERDICT_META[v.status]["color"] if v else "#94a3b8"
        rows.append({"lat": p.lat, "lon": p.lng, "color": color})
    df = pd.DataFrame(rows)
    st.map(df, latitude="lat", longitude="lon", color="color", size=60)
    if active_pet():
        st.caption("🟢 가능 · 🟠 조건부 · 🔴 불가 · 🔵 확인 필요")
    else:
        st.caption("반려동물을 등록하면 핀 색상이 통과 판정에 따라 바뀝니다.")


# ───────────────────── 탭 ─────────────────────
def tab_explore() -> None:
    c = st.columns([0.5, 0.28, 0.22])
    keyword = c[0].text_input("검색", placeholder="지역·장소 (예: 성수동, 애월)",
                              label_visibility="collapsed")
    category = c[1].selectbox("카테고리", CATEGORIES, label_visibility="collapsed")
    view = c[2].radio("보기", ["지도+목록", "목록만"], horizontal=True, label_visibility="collapsed")

    f = st.columns(3)
    passable_only = f[0].checkbox("우리 아이 통과만")
    indoor_ok = f[1].checkbox("실내 가능")
    free_only = f[2].checkbox("추가요금 없음")

    places, source = get_places(keyword)
    pet = active_pet()

    def keep(p: Place) -> bool:
        if category != "전체" and p.category != category:
            return False
        if indoor_ok and p.policy.outdoor_only:
            return False
        if free_only and p.policy.extra_fee:
            return False
        if passable_only and pet and evaluate(pet, p.policy).status == "NO":
            return False
        return True

    filtered = [p for p in places if keep(p)]
    if source == "live→mock":
        st.warning("실데이터 호출에 실패해 목업 데이터로 표시합니다. (API 키/승인 상태 확인)", icon="⚠️")
    st.caption(f"{len(filtered)}곳")

    if view == "지도+목록":
        render_map(filtered)

    if not filtered:
        st.info("조건에 맞는 장소가 없어요. 필터를 조정해 보세요.")
    for p in filtered:
        render_place_card(p)


def tab_favorites() -> None:
    fav = st.session_state["favorites"]
    if not fav:
        st.info("⭐ 즐겨찾기가 비어 있어요. 탐색 탭에서 별표를 눌러 저장해 보세요.")
        return
    places, _ = get_places()
    for p in [p for p in places if p.content_id in fav]:
        render_place_card(p, in_course="fav")


def tab_courses() -> None:
    courses = st.session_state["courses"]
    pet = active_pet()

    cc = st.columns([0.6, 0.4])
    new_title = cc[0].text_input("새 코스 이름", placeholder="예: 성수 오후 나들이",
                                 label_visibility="collapsed")
    if cc[1].button("➕ 코스 만들기", width="stretch"):
        courses.append({"title": new_title.strip() or "새 코스", "stops": []})
        st.rerun()

    if pet and st.button("✨ 통과 코스 자동 생성"):
        places, _ = get_places()
        passable = [p for p in places if evaluate(pet, p.policy).status != "NO"][:4]
        if passable:
            courses.append({"title": f"{pet.name} 통과 코스",
                            "stops": [p.content_id for p in passable]})
            st.rerun()

    if not courses:
        st.info("🗺️ 아직 만든 코스가 없어요. 탐색 탭에서 '코스에 추가'를 누르거나 자동 생성해 보세요.")
        return

    places, _ = get_places()
    by_id = {p.content_id: p for p in places}
    for ci, course in enumerate(courses):
        stops = [by_id[s] for s in course["stops"] if s in by_id]
        has_no = pet and any(evaluate(pet, s.policy).status == "NO" for s in stops)
        summary = ""
        if pet and stops:
            summary = " · ❌ 일부 통과 불가" if has_no else f" · ✅ {pet.name} 전체 통과"
        head = st.columns([0.85, 0.15])
        head[0].subheader(f"{course['title']}  \n:gray[{len(stops)}곳{summary}]")
        if head[1].button("삭제", key=f"delc_{ci}"):
            courses.pop(ci)
            st.rerun()
        for i, s in enumerate(stops, 1):
            v = evaluate(pet, s.policy) if pet else None
            badge = verdict_badge_html(v.status) if v else ""
            st.markdown(f"{i}. **{s.title}** &nbsp; {badge}", unsafe_allow_html=True)
        st.divider()


# ───────────────────── 메인 ─────────────────────
render_header()
render_sidebar()
t1, t2, t3 = st.tabs(["🔎 탐색", "⭐ 즐겨찾기", "🗺️ 내 코스"])
with t1:
    tab_explore()
with t2:
    tab_favorites()
with t3:
    tab_courses()
