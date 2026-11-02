import random
import json
import html
import streamlit as st
import streamlit.components.v1 as components
import plotly.graph_objects as go

# =========================
# 게임 상수
# =========================
START_YEAR = 2026
END_YEAR = 2050
MONEY_SCALE = 1_000_000  # 게임 금액 1단위 = 100만 원
START_MONEY = 80 * MONEY_SCALE  # 시작 자금 8,000만원
START_EMISSION = 100
TURN_YEARS = 1  # 다음 해로 버튼 한 번에 진행할 게임 연수
MAX_FLEET_SIZE = 5  # 회사가 보유할 수 있는 최대 선박 수
MAX_FISHING_SHIPS = 2  # 어선은 최대 2척

DESTINATIONS = [
    {"name": "도쿄", "years": 1, "income": 15 * MONEY_SCALE, "fee": 2 * MONEY_SCALE},
    {"name": "상하이", "years": 1, "income": 17 * MONEY_SCALE, "fee": 2.5 * MONEY_SCALE},
    {"name": "타이베이", "years": 1, "income": 16 * MONEY_SCALE, "fee": 2 * MONEY_SCALE},
    {"name": "홍콩", "years": 2, "income": 32 * MONEY_SCALE, "fee": 3 * MONEY_SCALE},
    {"name": "싱가포르", "years": 2, "income": 36 * MONEY_SCALE, "fee": 4 * MONEY_SCALE},
    {"name": "로테르담", "years": 3, "income": 57 * MONEY_SCALE, "fee": 3.5 * MONEY_SCALE},
    {"name": "로스앤젤레스", "years": 3, "income": 54 * MONEY_SCALE, "fee": 4 * MONEY_SCALE},
]

TRANSPORT = [
    {"id": 1, "name": "화물 적재함 확장", "price": 25 * MONEY_SCALE, "effect": "모든 항해 수익 +10%"},
    {"id": 2, "name": "대형 선체로 교체", "price": 80 * MONEY_SCALE, "effect": "모든 항해 수익 +25%"},
    {"id": 3, "name": "자동화 하역 시스템", "price": 15 * MONEY_SCALE, "effect": "부산항을 포함한 정박비 1단계당 25% 할인 (최대 75%)"},
    {"id": 4, "name": "자율운항선박", "price": 30 * MONEY_SCALE, "effect": "정박 중인 모든 선박이 이전 자동 항로로 재출항"},
]


# 선종별 추가 구매 비용 및 게임용 특수 목적지
# 선종마다 첫 구매 가격을 다르게 설정했다. (게임 밸런스용 금액이며 실제 선박 시세는 아님)
SHIP_TYPES = {
    "기본 화물선": {"base_price": 60 * MONEY_SCALE, "kind": "일반", "description": "일반 항구 간 기본 화물 운송"},
    "컨테이너선": {"base_price": 90 * MONEY_SCALE, "kind": "일반", "description": "컨테이너 화물 운송"},
    "어선": {"base_price": 35 * MONEY_SCALE, "kind": "어선", "description": "어장으로 이동해 조업 후 어획물 판매"},
    "탱크선": {"base_price": 100 * MONEY_SCALE, "kind": "특수", "description": "액체 화물 운송"},
    "케미컬 탱커": {"base_price": 110 * MONEY_SCALE, "kind": "특수", "description": "화학제품 전문 운송"},
    "LNG선": {"base_price": 130 * MONEY_SCALE, "kind": "특수", "description": "액화천연가스 운송"},
}


RESEARCH_TECHS = [
    {"id": "alternative_fuel", "name": "차세대 무탄소 연료 추진 기술", "stages": [
        {"price": 10 * MONEY_SCALE, "reduction": 5, "label": "1단계 · 기초 연구"},
        {"price": 30 * MONEY_SCALE, "reduction": 7, "label": "2단계 · 실증 연구"},
        {"price": 140 * MONEY_SCALE, "reduction": 8, "label": "3단계 · 상용화 완성"}]},
    {"id": "capture", "name": "선상 탄소 포집 기술", "stages": [
        {"price": 10 * MONEY_SCALE, "reduction": 4, "label": "1단계 · 원리 연구"},
        {"price": 30 * MONEY_SCALE, "reduction": 6, "label": "2단계 · 장치 실증"},
        {"price": 140 * MONEY_SCALE, "reduction": 8, "label": "3단계 · 상용화 완성"}]},
    {"id": "efficiency", "name": "에너지 효율 개선 기술", "stages": [
        {"price": 7 * MONEY_SCALE, "reduction": 4, "label": "1단계 · 효율 분석"},
        {"price": 20 * MONEY_SCALE, "reduction": 5, "label": "2단계 · 시스템 개선"},
        {"price": 90 * MONEY_SCALE, "reduction": 6, "label": "3단계 · 고효율 완성"}]},
    {"id": "wind", "name": "풍력 보조 추진 기술", "stages": [
        {"price": 7 * MONEY_SCALE, "reduction": 3, "label": "1단계 · 풍력 실험"},
        {"price": 20 * MONEY_SCALE, "reduction": 5, "label": "2단계 · 해상 실증"},
        {"price": 90 * MONEY_SCALE, "reduction": 7, "label": "3단계 · 상용화 완성"}]},
    {"id": "shore_power", "name": "육상 전력 공급 기술", "stages": [
        {"price": 7 * MONEY_SCALE, "reduction": 3, "label": "1단계 · 접속 연구"},
        {"price": 20 * MONEY_SCALE, "reduction": 5, "label": "2단계 · 항만 실증"},
        {"price": 90 * MONEY_SCALE, "reduction": 7, "label": "3단계 · 상용화 완성"}]},
    {"id": "hydrogen", "name": "청정 수소·연료전지 기술", "stages": [
        {"price": 10 * MONEY_SCALE, "reduction": 4, "label": "1단계 · 기초 연구"},
        {"price": 30 * MONEY_SCALE, "reduction": 6, "label": "2단계 · 실증 연구"},
        {"price": 140 * MONEY_SCALE, "reduction": 7, "label": "3단계 · 상용화 완성"}]},
]

SPECIAL_PORTS = {
    "LNG 터미널": {"ship_types": ["LNG선"], "years": 2, "income": 65 * MONEY_SCALE, "fee": 5 * MONEY_SCALE,
                    "coords": (1.3, 104.0), "description": "LNG선 전용 터미널(게임용 목적지)"},
    "화학제품 터미널": {"ship_types": ["케미컬 탱커"], "years": 2, "income": 55 * MONEY_SCALE, "fee": 4 * MONEY_SCALE,
                         "coords": (22.3, 114.2), "description": "케미컬 탱커 전용 터미널(게임용 목적지)"},
    "원유 터미널": {"ship_types": ["탱크선"], "years": 2, "income": 60 * MONEY_SCALE, "fee": 4 * MONEY_SCALE,
                    "coords": (25.0, 55.0), "description": "탱크선 전용 터미널(게임용 목적지)"},
}
FISHING_GROUNDS = {
    "동해 어장": {"years": 1, "income": 11 * MONEY_SCALE, "fee": 0, "coords": (38.0, 132.0),
                  "description": "동해 어장에서 조업 후 귀항해 어획물을 판매합니다."},
    "북태평양 어장": {"years": 2, "income": 25 * MONEY_SCALE, "fee": 0, "coords": (40.0, 155.0),
                      "description": "먼바다 어장에서 조업하는 장거리 어업입니다."},
}

CHECKPOINTS = {2030: 80, 2040: 30, 2050: 0}
AUTO_ROUTE = ["로테르담", "싱가포르", "상하이", "도쿄"]

# 실제 지리 좌표: 위도, 경도
PORT_COORDS = {
    "부산": (35.1796, 129.0756),
    "도쿄": (35.6762, 139.6503),
    "상하이": (31.2304, 121.4737),
    "싱가포르": (1.3521, 103.8198),
    "로테르담": (51.9244, 4.4777),
    "타이베이": (25.0330, 121.5654),
    "홍콩": (22.3193, 114.1694),
    "로스앤젤레스": (33.7405, -118.2720),
}

# 대륙을 가로지르지 않도록 바다를 따라가는 단순화 항로 경유점
SEA_ROUTES = {
    "도쿄": [PORT_COORDS["부산"], (34.5, 132.0), (34.8, 136.5), PORT_COORDS["도쿄"]],
    "상하이": [PORT_COORDS["부산"], (34.2, 127.0), (32.5, 125.5), PORT_COORDS["상하이"]],
    "싱가포르": [PORT_COORDS["부산"], (30.0, 125.0), (25.0, 121.0), (20.0, 117.0), (14.0, 112.0), (8.0, 108.0), PORT_COORDS["싱가포르"]],
    "로테르담": [PORT_COORDS["부산"], (30.0, 125.0), (22.0, 120.0), (15.0, 115.0), (8.0, 105.0), (1.5, 103.5), (-5.0, 105.0), (-10.0, 110.0), (-20.0, 95.0), (-30.0, 65.0), (-25.0, 35.0), (-10.0, 15.0), (5.0, 5.0), (20.0, -5.0), (35.0, -10.0), (43.0, -8.0), (48.0, -3.0), PORT_COORDS["로테르담"]],
    "타이베이": [PORT_COORDS["부산"], (32.0, 126.0), (28.0, 124.0), PORT_COORDS["타이베이"]],
    "홍콩": [PORT_COORDS["부산"], (30.0, 125.0), (25.0, 121.0), PORT_COORDS["홍콩"]],
    "로스앤젤레스": [PORT_COORDS["부산"], (30.0, 145.0), (25.0, 170.0), (30.0, -160.0), (33.0, -140.0), (34.0, -120.0), PORT_COORDS["로스앤젤레스"]],
    "LNG 터미널": [PORT_COORDS["부산"], (30.0, 125.0), (20.0, 118.0), (10.0, 110.0), SPECIAL_PORTS["LNG 터미널"]["coords"]],
    "화학제품 터미널": [PORT_COORDS["부산"], (30.0, 125.0), (25.0, 121.0), SPECIAL_PORTS["화학제품 터미널"]["coords"]],
    "원유 터미널": [PORT_COORDS["부산"], (25.0, 125.0), (20.0, 110.0), (15.0, 90.0), SPECIAL_PORTS["원유 터미널"]["coords"]],
    "동해 어장": [PORT_COORDS["부산"], (37.0, 130.0), FISHING_GROUNDS["동해 어장"]["coords"]],
    "북태평양 어장": [PORT_COORDS["부산"], (35.0, 140.0), (38.0, 150.0), FISHING_GROUNDS["북태평양 어장"]["coords"]],
}


def new_ship_state(ship_id, name, ship_type, price):
    """선박별 운항 상태를 만든다. 회사 공통 값은 이 딕셔너리에 넣지 않는다."""
    return {
        "id": ship_id, "name": name, "type": ship_type, "price": price,
        "status": "docked", "phase": "docked", "dest": None,
        "years_left": 0, "leg_years": 0, "trip_elapsed": 0, "waiting_for_turn": False, "pos": 0, "total": 0,
        "weather": None, "weather_note": "", "voyage_income": 0,
        "returning_income": 0, "port_fee_paid": 0, "event_cooldown": 0,
        "last_event_title": None,
        "voyage_event_count": 0, "event_log": [], "emergency_quest_bonus": 0, "emergency_quest_year": None,
    }


def get_ship(ship_id=None):
    fleet = st.session_state.get("fleet", [])
    if ship_id is None:
        ship_id = st.session_state.get("selected_ship_id", 1)
    return next((ship for ship in fleet if ship.get("id") == ship_id), None)


def active_ships():
    return [ship for ship in st.session_state.get("fleet", [])
            if ship.get("status", ship.get("phase", "docked")) in ("outbound", "returning")]


def set_ship_status(ship, status):
    """새 status를 기준으로 기존 이벤트/표시 코드와의 호환용 phase도 동기화한다."""
    ship["status"] = status
    ship["phase"] = {"outbound": "sailing", "returning": "returning", "docked": "docked"}[status]


def sync_ship_map_progress(ship):
    """턴제 진행률을 기존 지도 코드가 읽는 pos/total 형식으로 변환한다."""
    status = ship.get("status", "docked")
    if status not in ("outbound", "returning"):
        ship["pos"], ship["total"] = 0, 0
        return
    leg_years = max(1, int(ship.get("leg_years", 1)))
    years_left = max(0, min(leg_years, int(ship.get("years_left", leg_years))))
    # pos는 항상 해당 구간의 경과 비율이다. 지도 쪽에서 귀항 방향만 반전한다.
    progress = 1 - years_left / leg_years
    ship["total"] = 1000
    ship["pos"] = round(max(0.0, min(1.0, progress)) * ship["total"])


def ensure_fleet_fields():
    """기존 세션의 선박 상태를 턴제 status/years_left 구조로 이전한다."""
    fleet = st.session_state.get("fleet", [])
    legacy_phase = st.session_state.get("phase", "docked")
    legacy_fields = {
        "dest": st.session_state.get("dest"),
        "weather": st.session_state.get("weather"), "weather_note": st.session_state.get("weather_note", ""),
        "voyage_income": st.session_state.get("voyage_income", 0),
        "returning_income": st.session_state.get("returning_income", 0),
        "port_fee_paid": st.session_state.get("port_fee_paid", 0),
        "event_cooldown": st.session_state.get("event_cooldown", 0),
        "voyage_event_count": st.session_state.get("voyage_event_count", 0),
        "event_log": st.session_state.get("event_log", []).copy(),
    }
    for ship in fleet:
        defaults = new_ship_state(ship.get("id", 1), ship.get("name", "선박"),
                                  ship.get("type", "기본 화물선"), ship.get("price", 0))
        had_status = ship.get("status") in ("docked", "outbound", "returning")
        old_phase = ship.get("phase", legacy_phase if ship.get("id") == st.session_state.get("selected_ship_id", 1) else "docked")
        for key, value in defaults.items():
            if key not in ship:
                ship[key] = value.copy() if isinstance(value, list) else value
        # 기존 세션에서 사용 중이던 선박 한 척을 새 구조로 변환한다.
        if not had_status:
            ship["status"] = {"sailing": "outbound", "returning": "returning"}.get(old_phase, "docked")
        if ship.get("status") in ("outbound", "returning") and not ship.get("dest") and ship.get("id") == st.session_state.get("selected_ship_id", 1):
            ship.update(legacy_fields)
        if ship.get("status") in ("outbound", "returning"):
            if int(ship.get("leg_years", 0)) <= 0:
                old_total = max(1, int(ship.get("total", 1)))
                old_pos = max(0, int(ship.get("pos", 0)))
                remaining_fraction = max(0.0, min(1.0, (old_total - old_pos) / old_total))
                duration = max(1, actual_years(ship.get("dest")))
                ship["leg_years"] = duration
                ship["years_left"] = max(1, round(duration * remaining_fraction))
            set_ship_status(ship, ship["status"])
        else:
            ship["years_left"] = 0
            ship["leg_years"] = 0
            set_ship_status(ship, "docked")
        sync_ship_map_progress(ship)


def init():
    """모든 페이지에서 공유하는 세션 상태를 초기화한다."""
    defaults = {
        "started": False,
        "turn_animation_ships": [],
        "phase": "docked",
        "year": START_YEAR,
        "money": START_MONEY,
        "bought_eq": [],
        "bought_tr": [],
        "transport_levels": {},
        "annual_quest": None,
        "annual_quest_year": None,
        "dest": None,
        "pos": 0,
        "total": 0,
        "auto_on": False,
        "auto_idx": 0,
        "checked": [],
        "history": [{"year": START_YEAR, "money": START_MONEY, "emission": START_EMISSION}],
        "voyage_count": 0,
        "cumulative_voyage_income": 0,
        "result": None,
        "fail_reason": "",
        "msg": "",
        "return_feedback": "",
        "balloons_shown": False,
        "weather": None,
        "voyage_income": 0,
        "weather_note": "",
        "selected_port": None,
        "event_pending": None,
        "event_cooldown": 0,
        "last_event_title": None,
        "voyage_event_count": 0,
        "port_fee_paid": 0,
        "returning_income": 0,
        "event_log": [],
        "research_levels": {},
        "fleet": [{"id": 1, "name": "푸른 항해호", "type": "기본 화물선", "price": 0}],
        "next_ship_id": 2,
        "selected_ship_id": 1,
        "company_name": "노스스타 해운",
        "captain_name": "선장",
        "unlocked_special_ports": [],
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value.copy() if isinstance(value, (list, dict)) else value
    if "transport_levels" not in st.session_state:
        st.session_state.transport_levels = {}
    if "annual_quest" not in st.session_state:
        st.session_state.annual_quest = None
    if "annual_quest_year" not in st.session_state:
        st.session_state.annual_quest_year = None
    ensure_fleet_fields()


def reset_game():
    defaults = {
        "started": False,
        "turn_animation_ships": [],
        "phase": "docked",
        "year": START_YEAR,
        "money": START_MONEY,
        "bought_eq": [],
        "bought_tr": [],
        "transport_levels": {},
        "annual_quest": None,
        "annual_quest_year": None,
        "dest": None,
        "pos": 0,
        "total": 0,
        "auto_on": False,
        "auto_idx": 0,
        "checked": [],
        "history": [{"year": START_YEAR, "money": START_MONEY, "emission": START_EMISSION}],
        "voyage_count": 0,
        "cumulative_voyage_income": 0,
        "result": None,
        "fail_reason": "",
        "msg": "",
        "return_feedback": "",
        "balloons_shown": False,
        "weather": None,
        "voyage_income": 0,
        "weather_note": "",
        "selected_port": None,
        "event_pending": None,
        "event_cooldown": 0,
        "last_event_title": None,
        "voyage_event_count": 0,
        "port_fee_paid": 0,
        "returning_income": 0,
        "event_log": [],
        "research_levels": {},
        "fleet": [{"id": 1, "name": "푸른 항해호", "type": "기본 화물선", "price": 0}],
        "next_ship_id": 2,
        "selected_ship_id": 1,
        "company_name": "노스스타 해운",
        "captain_name": "선장",
        "unlocked_special_ports": [],
    }
    for key, value in defaults.items():
        st.session_state[key] = value.copy() if isinstance(value, (list, dict)) else value
    ensure_fleet_fields()


def money_label(amount):
    """원 단위 금액을 한국어 큰 단위로 읽기 쉽게 표시한다."""
    amount = int(amount)
    sign = "-" if amount < 0 else ""
    amount = abs(amount)
    eok = amount // 100_000_000
    man = (amount % 100_000_000) // 10_000
    if eok and man:
        return f"{sign}{eok}억 {man:,}만원"
    if eok:
        return f"{sign}{eok}억원"
    if man:
        return f"{sign}{man:,}만원"
    return f"{sign}{amount:,}원"


def current_emission():
    """연구 기술 6종의 효과만으로 배출량을 계산한다."""
    reduction = 0
    levels = st.session_state.get("research_levels", {})
    for tech in RESEARCH_TECHS:
        level = int(levels.get(tech["id"], 0))
        # 구버전 저장 데이터의 암모니아/메탄올 연구 진행도는 통합 연료 연구에 반영한다.
        if tech["id"] == "alternative_fuel":
            level = max(level, int(levels.get("ammonia", 0)), int(levels.get("methanol", 0)))
        level = max(0, min(level, len(tech["stages"])))
        reduction += sum(stage["reduction"] for stage in tech["stages"][:level])
    return max(0, START_EMISSION - reduction)


def selected_ship():
    fleet = st.session_state.get("fleet", [])
    wanted = st.session_state.get("selected_ship_id", 1)
    return next((ship for ship in fleet if ship["id"] == wanted), fleet[0] if fleet else None)


def ship_price(ship_type):
    base_price = SHIP_TYPES[ship_type]["base_price"]
    levels = st.session_state.get("research_levels", {})
    completed_stages = sum(max(0, int(levels.get(tech["id"], 0))) for tech in RESEARCH_TECHS)
    return int(base_price * (1 + 0.04 * completed_stages))


def buy_ship(ship_type, ship_name):
    ship_name = (ship_name or "").strip()
    st.session_state.purchase_feedback = ""
    st.session_state.purchase_feedback_type = "error"
    if st.session_state.phase == "ended":
        return
    if len(st.session_state.fleet) >= MAX_FLEET_SIZE:
        st.session_state.purchase_feedback = f"보유 가능한 선박은 최대 {MAX_FLEET_SIZE}척입니다."
        return
    if ship_type == "어선" and sum(1 for vessel in st.session_state.fleet if vessel.get("type") == "어선") >= MAX_FISHING_SHIPS:
        st.session_state.purchase_feedback = f"어선은 최대 {MAX_FISHING_SHIPS}척까지만 보유할 수 있습니다."
        return
    if not ship_name:
        st.session_state.purchase_feedback = "선박 이름을 입력해 주세요."
        return
    if any(s["name"].casefold() == ship_name.casefold() for s in st.session_state.fleet):
        st.session_state.purchase_feedback = "이미 사용 중인 선박 이름입니다."
        return
    price = ship_price(ship_type)
    if st.session_state.money < price:
        st.session_state.purchase_feedback = "선박을 구매할 자금이 부족합니다."
        return
    ship = new_ship_state(st.session_state.next_ship_id, ship_name, ship_type, price)
    st.session_state.money -= price
    st.session_state.fleet.append(ship)
    st.session_state.next_ship_id += 1
    # selected_ship_id는 관리 카드의 selectbox 위젯이 사용하므로,
    # 구매 버튼을 누른 현재 실행에서는 직접 변경하지 않고 다음 실행에서 반영한다.
    st.session_state.pending_selected_ship_id = ship["id"]
    if ship_type in ("LNG선", "탱크선", "케미컬 탱커"):
        st.session_state.unlocked_special_ports = sorted(set(
            st.session_state.unlocked_special_ports +
            [name for name, data in SPECIAL_PORTS.items() if ship_type in data["ship_types"]]
        ))
    st.session_state.purchase_feedback = f"{ship_name} 구매 완료! ({ship_type})"
    st.session_state.purchase_feedback_type = "success"
    add_history()


def rename_ship(ship_id, new_name):
    new_name = (new_name or "").strip()
    ship = next((s for s in st.session_state.fleet if s["id"] == ship_id), None)
    if not ship:
        return
    if not new_name:
        st.session_state.msg = "선박 이름을 입력해 주세요."
        return
    if any(s["id"] != ship_id and s["name"].casefold() == new_name.casefold() for s in st.session_state.fleet):
        st.session_state.msg = "이미 사용 중인 선박 이름입니다. 다른 이름을 입력해 주세요."
        return
    old_name = ship["name"]
    ship["name"] = new_name
    st.session_state.msg = f"선박 이름을 {old_name}에서 {new_name}(으)로 변경했습니다."


def sell_ship(ship_id):
    # 회사 운영을 위해 마지막 남은 선박은 판매할 수 없다.
    if len(st.session_state.get("fleet", [])) <= 1:
        st.session_state.msg = "선박이 1척만 남아 있을 때는 판매할 수 없습니다. 먼저 다른 선박을 구매해 주세요."
        return
    ship = next((s for s in st.session_state.fleet if s["id"] == ship_id), None)
    if not ship:
        return
    if ship.get("status", ship.get("phase", "docked")) != "docked":
        st.session_state.msg = "운항 중인 선박은 판매할 수 없습니다. 부산항에 정박시킨 뒤 판매해 주세요."
        return
    # 연도에 따라 구매가의 70~80%를 환급한다.
    refund_rate = 0.70 + ((int(st.session_state.year) + int(ship["id"])) % 11) / 100
    refund = int(int(ship.get("price", 0)) * refund_rate)
    st.session_state.money += refund
    st.session_state.fleet.remove(ship)
    # 선택 위젯이 생성된 뒤 selected_ship_id를 직접 바꾸면 Streamlit 오류가 난다.
    # 다음 실행에서 위젯 생성 전에 남은 선박을 선택하도록 예약한다.
    if st.session_state.get("selected_ship_id") == ship_id:
        st.session_state.pending_selected_ship_id = st.session_state.fleet[0]["id"]
    st.session_state.selected_port = None
    st.session_state.msg = f"{ship['name']} 판매 완료! 구매가의 {round(refund_rate*100)}%인 {money_label(refund)}을 받았습니다."
    add_history()


def research_next_stage(tech_id):
    if st.session_state.phase == "ended":
        return
    tech = next((t for t in RESEARCH_TECHS if t["id"] == tech_id), None)
    if tech is None:
        return
    level = int(st.session_state.research_levels.get(tech_id, 0))
    if level >= len(tech["stages"]):
        return
    stage = tech["stages"][level]
    if st.session_state.money < stage["price"]:
        st.session_state.msg = "연구비가 부족합니다."
        return
    st.session_state.money -= stage["price"]
    st.session_state.research_levels[tech_id] = level + 1
    st.session_state.msg = f"{tech['name']} {level + 1}단계 연구 완료! 회사 전체 배출량 -{stage['reduction']}%p"
    add_history()
    if current_emission() == 0:
        st.session_state.phase = "ended"
        st.session_state.result = "success"
        st.session_state.msg = "회사 전체 배출량 0% 달성! 탄소중립 성공!"


def income_multiplier():
    multiplier = 1.0
    if 1 in st.session_state.bought_tr:
        multiplier += 0.10
    if 2 in st.session_state.bought_tr:
        multiplier += 0.25
    return multiplier


def actual_income(destination_name, ship=None):
    destination = next((item for item in DESTINATIONS if item["name"] == destination_name), None)
    if destination is None:
        destination = SPECIAL_PORTS.get(destination_name) or FISHING_GROUNDS.get(destination_name)
    if destination is None:
        return 0
    ship = ship or selected_ship()
    vessel_type = ship.get("type") if ship else "기본 화물선"
    type_multiplier = 1.15 if vessel_type == "컨테이너선" and destination_name in [d["name"] for d in DESTINATIONS] else 1.0
    return round(destination["income"] * income_multiplier() * type_multiplier)


def actual_years(destination_name):
    destination = next((item for item in DESTINATIONS if item["name"] == destination_name), None)
    if destination is None:
        destination = SPECIAL_PORTS.get(destination_name) or FISHING_GROUNDS.get(destination_name)
    if destination is None:
        return 1
    return max(1, destination["years"])


def handling_discount_percent():
    level = max(0, min(3, int(st.session_state.get("transport_levels", {}).get("handling", 0))))
    return level * 25


QUEST_YEARS = (2028, 2032, 2036, 2040, 2044, 2048)

def generate_annual_quest(year):
    """4년 간격으로, 현재 보유 선종 중 하나에 맞는 의뢰를 생성한다."""
    if int(year) not in QUEST_YEARS:
        return
    owned_types = list(dict.fromkeys(v.get("type") for v in st.session_state.fleet))
    if not owned_types:
        return
    ship_type = random.choice(owned_types)
    if ship_type == "어선":
        destination = random.choice(list(FISHING_GROUNDS))
        base_fare = FISHING_GROUNDS[destination]["income"]
    else:
        destination_data = random.choice(DESTINATIONS)
        destination = destination_data["name"]
        base_fare = destination_data["income"]
    vessel_bonus = 1.15 if ship_type == "컨테이너선" and ship_type != "어선" else 1.0
    reward = round(base_fare * income_multiplier() * vessel_bonus * 1.25)
    st.session_state.annual_quest = {
        "year": int(year), "destination": destination, "ship_type": ship_type,
        "reward": reward, "status": "open", "ship_id": None,
    }
    st.session_state.annual_quest_year = int(year)

def accept_annual_quest(ship_id):
    quest = st.session_state.get("annual_quest")
    ship = get_ship(ship_id)
    if not quest or quest.get("status") != "open" or not ship:
        return
    if ship.get("type") != quest["ship_type"]:
        st.session_state.msg = f"이 의뢰는 {quest['ship_type']}만 수락할 수 있습니다."
        return
    if ship.get("status", "docked") != "docked":
        st.session_state.msg = "부산항에 정박 중인 선박만 의뢰를 수락할 수 있습니다."
        return
    if st.session_state.phase == "ended":
        return
    if not assign_destination(quest["destination"], ship):
        return
    start_voyage(quest["destination"], ship)
    if ship.get("status") == "outbound":
        base_income = int(actual_income(quest["destination"], ship))
        weather_rate = float(ship.get("income_weather_rate", 1.0))
        target_income = int(quest["reward"])
        # 의뢰 보상(기본 운임 × 업그레이드 배율 × 1.25)에 맞춰 차액을 귀항 때 지급한다.
        ship["emergency_quest_bonus"] = max(0, round(target_income * weather_rate) - round(base_income * weather_rate))
        ship["emergency_quest_year"] = quest["year"]
        quest["status"] = "accepted"
        quest["ship_id"] = ship["id"]
        # 긴급 의뢰 수락 알림은 일반 상단 메시지와 분리해 턴 진행 영역 아래에 표시한다.
        st.session_state.quest_accept_feedback = f"{quest['year']}년 긴급 의뢰 수락! {ship['name']}이(가) {quest['destination']}으로 출항합니다."


def port_benefit(destination_name):
    """게임용 항만 인센티브를 계산한다. 실제 항만 요금 자체가 아닌 단순화된 게임 규칙이다."""
    emission = current_emission()
    levels = st.session_state.get("research_levels", {})
    fuel_level = max(int(levels.get("alternative_fuel", 0)), int(levels.get("ammonia", 0)), int(levels.get("methanol", 0)))
    researched_techs = sum(1 for tech in RESEARCH_TECHS if int(levels.get(tech["id"], 0)) > 0)
    result = {"discount_percent": 0, "arrival_bonus": 0, "note": ""}

    if destination_name == "싱가포르":
        # 연구 진행도에 따른 게임용 친환경 운항 인센티브.
        if fuel_level >= 3:
            result.update(discount_percent=30,
                          note="무탄소 연료 연구 완료 인센티브(게임 규칙): 정박비 30% 감면")
        elif fuel_level >= 1:
            result.update(discount_percent=20,
                          note="대체 연료 연구 인센티브(게임 규칙): 정박비 20% 감면")
        else:
            result["note"] = "감면 조건: 차세대 무탄소 연료 추진 기술 연구 필요"

    elif destination_name == "로테르담":
        if emission <= 30 and researched_techs >= 3:
            result.update(discount_percent=15,
                          note="환경 성과 인센티브(게임 규칙): 정박비 15% 감면")
        else:
            result["note"] = "게임 내 감면 조건: 연구 기술 3종 이상 착수 및 배출량 30% 이하"

    elif destination_name == "로스앤젤레스":
        # 실제 ESI 점수를 배출량만으로 계산할 수 없으므로, 배출량은 시연용 대체 기준으로만 사용.
        if emission <= 30:
            result.update(arrival_bonus=3_500_000,
                          note="ESI 유사 친환경 운항 보너스(게임 규칙): 350만원 지급")
        elif emission <= 50:
            result.update(arrival_bonus=1_050_000,
                          note="ESI 유사 친환경 운항 보너스(게임 규칙): 105만원 지급")
        else:
            result["note"] = "게임 내 보너스 조건: 배출량 50% 이하"

    return result


def discounted_port_fee(destination_name):
    destination = next(item for item in DESTINATIONS if item["name"] == destination_name)
    benefit = port_benefit(destination_name)
    handling = handling_discount_percent()
    total_discount = min(100, int(benefit["discount_percent"]) + handling)
    if handling:
        benefit["note"] = (benefit["note"] + " · " if benefit["note"] else "") + f"자동화 하역 시스템 {handling}% 할인"
    fee = round(int(destination["fee"]) * (100 - total_discount) / 100)
    benefit["discount_percent"] = total_discount
    return fee, benefit


def add_history():
    st.session_state.history.append({
        "year": int(st.session_state.year),
        "money": int(st.session_state.money),
        "emission": int(current_emission()),
    })



def show_annual_quest_panel():
    """턴 진행 버튼과 도착 알림 아래에 긴급 의뢰 패널을 표시한다."""
    quest = st.session_state.get("annual_quest")
    if not quest or quest.get("status") != "open" or st.session_state.phase == "ended":
        return
    with st.container(border=True):
        st.markdown(f"### 📦 {quest['year']}년 긴급 운송 요청")
        st.write(f"**목적지:** {quest['destination']}항")
        st.write(f"**요구 선박:** {quest['ship_type']}")
        st.write(f"**긴급 운임:** {money_label(quest['reward'])}")
        eligible = [v for v in st.session_state.fleet
                    if v.get("type") == quest["ship_type"] and v.get("status", "docked") == "docked"]
        if eligible:
            chosen_id = st.selectbox(
                "의뢰에 투입할 선박", [v["id"] for v in eligible],
                format_func=lambda sid: next(v["name"] for v in eligible if v["id"] == sid),
                key=f"quest_ship_popup_{quest['year']}"
            )
            left, right = st.columns(2)
            with left:
                if st.button("의뢰 수락", key=f"accept_quest_popup_{quest['year']}", type="primary", use_container_width=True):
                    accept_annual_quest(chosen_id)
                    st.rerun()
            with right:
                if st.button("거절", key=f"decline_quest_popup_{quest['year']}", use_container_width=True):
                    quest["status"] = "declined"
                    st.rerun()
        else:
            st.warning(f"현재 부산항에 정박 중인 {quest['ship_type']}이 없어 수락할 수 없습니다.")
            if st.button("확인", key=f"close_quest_popup_{quest['year']}", use_container_width=True):
                quest["status"] = "declined"
                st.rerun()

def assign_destination(destination_name, ship=None):
    """선택한 정박 선박에 목적지를 배정한다. 실제 출항은 출항 버튼으로 시작한다."""
    ship = ship or selected_ship()
    if not ship or ship.get("status", ship.get("phase", "docked")) != "docked":
        return False
    ship_type = ship.get("type", "기본 화물선")
    if destination_name in FISHING_GROUNDS and ship_type != "어선":
        st.session_state.msg = "어장에는 어선만 목적지를 배정할 수 있습니다."
        return False
    if ship_type == "어선" and destination_name not in FISHING_GROUNDS:
        st.session_state.msg = "어선은 지정된 어장으로만 목적지를 배정할 수 있습니다."
        return False
    if destination_name in SPECIAL_PORTS and ship_type not in SPECIAL_PORTS[destination_name]["ship_types"]:
        st.session_state.msg = "이 특수 항구는 해당 선종만 이용할 수 있습니다."
        return False
    ship["dest"] = destination_name
    st.session_state.selected_port = destination_name
    # 목적지를 새로 선택하면 이전의 목적지 미선택 경고를 즉시 해제한다.
    st.session_state.show_empty_destination_warning = False
    st.session_state.confirm_empty_destination_turn = False
    return True


def start_voyage(destination_name, ship=None):
    """선택한 선박의 목적지만 설정하고 출항 애니메이션을 시작한다. 연도는 진행하지 않는다."""
    ship = ship or selected_ship()
    if not ship or ship.get("status", ship.get("phase", "docked")) != "docked" or st.session_state.phase == "ended":
        return
    ship_type = ship.get("type", "기본 화물선")
    if destination_name in FISHING_GROUNDS and ship_type != "어선":
        st.session_state.msg = "어장에는 어선만 출항할 수 있습니다."
        return
    if ship_type == "어선" and destination_name not in FISHING_GROUNDS:
        st.session_state.msg = "어선은 지정된 어장으로만 출항할 수 있습니다."
        return
    if destination_name in SPECIAL_PORTS and ship_type not in SPECIAL_PORTS[destination_name]["ship_types"]:
        st.session_state.msg = "이 특수 항구는 해당 선종만 이용할 수 있습니다."
        return
    if destination_name not in [item["name"] for item in DESTINATIONS] and destination_name not in SPECIAL_PORTS and destination_name not in FISHING_GROUNDS:
        st.session_state.msg = "유효하지 않은 목적지입니다."
        return
    duration = actual_years(destination_name)
    weather_options = [
        {"name": "순풍", "income_rate": 1.05,
         "description": "순풍을 만났습니다! 운임이 5% 증가합니다."},
        {"name": "잔잔한 바다", "income_rate": 1.0,
         "description": "바다가 잔잔합니다. 운임에 변화가 없습니다."},
        {"name": "짙은 안개", "income_rate": 1.0,
         "description": "짙은 안개가 끼었지만 운임에는 변화가 없습니다."},
        {"name": "폭풍", "income_rate": 0.90,
         "description": "폭풍으로 운임이 10% 감소합니다."},
    ]
    weather = random.choices(weather_options, weights=[2, 3, 3, 3], k=1)[0]
    ship.update({
        "dest": destination_name, "years_left": max(1, int(duration)),
        "leg_years": max(1, int(duration)), "trip_elapsed": 0,
        "waiting_for_turn": True,
        "weather": weather["name"], "weather_note": weather["description"],
        "voyage_income": round(actual_income(destination_name, ship) * weather["income_rate"]),
        "income_weather_rate": weather["income_rate"],
        "port_fee_paid": 0, "returning_income": round(actual_income(destination_name, ship) * weather["income_rate"]),
        "event_cooldown": 3, "voyage_event_count": 0,
    })
    set_ship_status(ship, "outbound")
    sync_ship_map_progress(ship)
    st.session_state.msg = f"{ship['name']} 출항! {weather['description']}"


def cancel_departure(ship=None):
    """다음 해로 진행하기 전 출항 준비를 취소하고 목적지 선택 상태로 되돌린다."""
    ship = ship or selected_ship()
    if not ship:
        return
    if (ship.get("status", ship.get("phase")) == "outbound"
            and int(ship.get("trip_elapsed", 0)) == 0
            and ship.get("waiting_for_turn", False)):
        ship.update({
            "dest": None, "years_left": 0, "leg_years": 0,
            "trip_elapsed": 0, "waiting_for_turn": False,
            "weather": None, "weather_note": "", "voyage_income": 0,
            "returning_income": 0, "port_fee_paid": 0,
            "event_cooldown": 0, "voyage_event_count": 0, "emergency_quest_bonus": 0, "emergency_quest_year": None,
        })
        set_ship_status(ship, "docked")
        sync_ship_map_progress(ship)
        st.session_state.selected_port = None
        st.session_state.msg = "출항을 취소했습니다. 목적지를 다시 선택할 수 있습니다."


def start_auto_voyage(ship=None):
    """자율운항 구매 후 정박 중인 일반 선박을 차례로 자동 출항시킨다."""
    if not st.session_state.auto_on or 4 not in st.session_state.bought_tr:
        return
    candidates = [ship] if ship else list(st.session_state.fleet)
    launched = []
    for vessel in candidates:
        if not vessel or vessel.get("status", "docked") != "docked" or vessel.get("type") == "어선":
            continue
        destination_name = vessel.get("last_auto_destination")
        if destination_name not in [item["name"] for item in DESTINATIONS]:
            destination_name = AUTO_ROUTE[st.session_state.auto_idx % len(AUTO_ROUTE)]
        if destination_name not in [item["name"] for item in DESTINATIONS]:
            continue
        start_voyage(destination_name, vessel)
        if vessel.get("status") == "outbound":
            vessel["auto_route_enabled"] = True
            vessel["last_auto_destination"] = destination_name
            launched.append(vessel["name"])
            st.session_state.auto_idx = (st.session_state.auto_idx + 1) % len(AUTO_ROUTE)
    if launched:
        st.session_state.msg = "자율운항 출항: " + ", ".join(launched)


def pause_voyage(ship=None):
    ship = ship or selected_ship()
    if ship and ship.get("status", ship.get("phase")) == "outbound":
        duration = max(1, actual_years(ship.get("dest")))
        ship["years_left"] = duration
        ship["leg_years"] = duration
        set_ship_status(ship, "returning")
        sync_ship_map_progress(ship)
        st.session_state.msg = f"{ship['name']} 회항을 시작합니다."


def buy_transport(item_id):
    if st.session_state.phase == "ended":
        return
    item = next(item for item in TRANSPORT if item["id"] == item_id)
    if item_id == 3:
        levels = st.session_state.setdefault("transport_levels", {})
        level = int(levels.get("handling", 0))
        prices = [15, 25, 40]
        if level >= 3 or st.session_state.money < prices[level] * MONEY_SCALE:
            return
        cost = prices[level] * MONEY_SCALE
        st.session_state.money -= cost
        levels["handling"] = level + 1
        if 3 not in st.session_state.bought_tr:
            st.session_state.bought_tr.append(3)
        st.session_state.msg = f"자동화 하역 시스템 {level + 1}단계 완료! 모든 항구 및 부산항 정박비 {25 * (level + 1)}% 할인."
    else:
        if item_id in st.session_state.bought_tr or st.session_state.money < item["price"]:
            return
        st.session_state.money -= item["price"]
        st.session_state.bought_tr.append(item_id)
        st.session_state.msg = f"{item['name']} 구매 완료!"
    add_history()


def arrive(ship):
    """해외 항구 도착: 해당 선박의 정박비를 처리하고 귀항시킨다."""
    destination_name = ship.get("dest")
    if not destination_name:
        set_ship_status(ship, "docked")
        return
    destination = next((item for item in DESTINATIONS if item["name"] == destination_name), None)
    if destination is None:
        destination = SPECIAL_PORTS.get(destination_name) or FISHING_GROUNDS.get(destination_name)
    if destination is None:
        set_ship_status(ship, "docked")
        return
    if destination_name in [d["name"] for d in DESTINATIONS]:
        port_fee, benefit = discounted_port_fee(destination_name)
    elif destination_name in FISHING_GROUNDS:
        port_fee = 0
        benefit = {"discount_percent": 0, "arrival_bonus": 0, "note": "어장은 정박비가 없습니다."}
    else:
        base_fee = int(destination.get("fee", 0))
        discount = handling_discount_percent()
        port_fee = round(base_fee * (100 - discount) / 100)
        benefit = {"discount_percent": discount, "arrival_bonus": 0, "note": f"자동화 하역 시스템 {discount}% 할인" if discount else destination.get("description", "게임용 목적지")}
    st.session_state.money -= int(port_fee)
    ship["port_fee_paid"] = int(ship.get("port_fee_paid", 0)) + int(port_fee)
    fee_note = benefit["note"]
    if benefit["arrival_bonus"]:
        st.session_state.money += int(benefit["arrival_bonus"])
        fee_note += f" · 항만 친환경 보너스 {money_label(benefit['arrival_bonus'])} 지급"
    add_history()

    return_weather_options = [
        {"name": "순풍", "income_rate": 1.05, "description": "귀항 중 순풍으로 운임이 5% 증가합니다."},
        {"name": "잔잔한 바다", "income_rate": 1.00, "description": "귀항 중 바다가 잔잔합니다."},
        {"name": "짙은 안개", "income_rate": 1.00, "description": "귀항 중 짙은 안개가 끼었지만 운임 변화는 없습니다."},
        {"name": "폭풍", "income_rate": 0.90, "description": "귀항 중 폭풍으로 운임이 10% 감소합니다."},
    ]
    return_weather = random.choices(return_weather_options, weights=[2, 3, 3, 3], k=1)[0]
    ship["weather"] = return_weather["name"]
    ship["weather_note"] = return_weather["description"]
    if return_weather["income_rate"] < 1:
        ship["returning_income"] = round(ship.get("returning_income", 0) * return_weather["income_rate"])
        ship["income_weather_rate"] = float(ship.get("income_weather_rate", 1.0)) * return_weather["income_rate"]
    return_duration = max(1, actual_years(destination_name))
    # 왕복 전체 기간을 유지한다. 여기서 편도 기간을 다시 더하지 않는다.
    ship["years_left"] = max(0, int(ship.get("years_left", return_duration)))
    ship["leg_years"] = max(1, int(ship.get("leg_years", return_duration)))
    set_ship_status(ship, "returning")
    sync_ship_map_progress(ship)
    ship["event_cooldown"] = 2
    ship["voyage_event_count"] = 0
    arrival_message = f"{ship['name']} 목적지 도착! 정박비 {money_label(port_fee)} 지출 · 귀항 날씨: {return_weather['name']} · {fee_note} 운임은 부산 도착 후 정산됩니다."
    previous_feedback = st.session_state.get("return_feedback", "")
    st.session_state.return_feedback = (previous_feedback + "  " + arrival_message).strip()


def settle_return(ship):
    """부산항 귀항 후 해당 선박만 정산한다. 연도/점검은 통합 시계만 담당한다."""
    if not ship or ship.get("status", ship.get("phase")) != "returning":
        return
    # 출항 시 적용한 선종·운송 강화·날씨와 항해 중 이벤트 운임 조정을 그대로 정산한다.
    income = int(ship.get("returning_income", 0) or 0)
    busan_fee = round(1 * MONEY_SCALE * (100 - handling_discount_percent()) / 100)
    st.session_state.money -= busan_fee
    quest_bonus = int(ship.get("emergency_quest_bonus", 0) or 0)
    income += quest_bonus
    st.session_state.money += income
    st.session_state.voyage_count = int(st.session_state.get("voyage_count", 0)) + 1
    st.session_state.cumulative_voyage_income = int(st.session_state.get("cumulative_voyage_income", 0)) + income
    add_history()
    ship_name = ship.get("name", "선박")
    quest_note = f" (긴급 의뢰 보상 포함 +{money_label(quest_bonus)})" if quest_bonus else ""
    ship.update({"dest": None, "years_left": 0, "leg_years": 0,
                 "trip_elapsed": 0, "waiting_for_turn": False,
                 "weather": None, "weather_note": "", "voyage_income": 0,
                 "returning_income": 0, "port_fee_paid": 0, "event_cooldown": 0,
                 "emergency_quest_bonus": 0, "emergency_quest_year": None})
    set_ship_status(ship, "docked")
    sync_ship_map_progress(ship)
    settlement_message = f"{ship_name} 부산항 귀항 완료! 운임 {money_label(income)} 지급{quest_note}, 부산항 정박비 {money_label(busan_fee)} 차감."
    previous_feedback = st.session_state.get("return_feedback", "")
    st.session_state.return_feedback = (previous_feedback + "  " + settlement_message).strip()


def finish_return(ship):
    settle_return(ship)


def check_year_checkpoint():
    """연도가 바뀐 순간에만 한 번 호출한다."""
    emission = current_emission()
    messages = []
    for checkpoint_year in sorted(CHECKPOINTS):
        if st.session_state.year >= checkpoint_year and checkpoint_year not in st.session_state.checked:
            limit = CHECKPOINTS[checkpoint_year]
            if emission > limit:
                st.session_state.phase = "ended"
                st.session_state.result = "fail"
                st.session_state.fail_reason = f"{checkpoint_year}년 점검 실패: 배출량 {emission}% (기준 {limit}% 이하)"
                st.session_state.msg = ""
                return
            st.session_state.checked.append(checkpoint_year)
            messages.append(f"{checkpoint_year}년 점검 통과!")
    if st.session_state.year >= END_YEAR:
        st.session_state.phase = "ended"
        if emission == 0:
            st.session_state.result = "success"
        else:
            st.session_state.result = "fail"
            st.session_state.fail_reason = f"2050년 최종 점검 실패: 배출량 {emission}% (기준 0%)"
    if messages:
        st.session_state.msg = " ".join(messages)
    add_history()


def event_condition_government(ship):
    return current_emission() <= 70


def event_condition_big_client(ship):
    return current_emission() <= 60


def event_condition_research_lab(ship):
    levels = st.session_state.get("research_levels", {})
    return any(int(levels.get(tech["id"], 0)) < len(tech["stages"]) for tech in RESEARCH_TECHS)


def event_condition_strike(ship):
    return bool(ship and ship.get("phase") == "sailing")


def event_condition_dolphins(ship):
    return bool(ship and ship.get("phase") in ("sailing", "returning"))


def event_condition_always(ship):
    return bool(ship and ship.get("phase") in ("sailing", "returning"))


def trigger_random_event(ship=None):
    """조건을 만족하는 이벤트 중 하나를 선택한다. 직전 이벤트는 연속 발생하지 않는다."""
    travelling = active_ships()
    if ship is None:
        eligible_ships = [s for s in travelling if int(s.get("event_cooldown", 0)) <= 0]
        if not eligible_ships:
            return
        ship = random.choice(eligible_ships)
    if not ship or ship.get("phase") not in ("sailing", "returning"):
        return

    events = [
        {"title": "엔진 이상 경고", "condition": event_condition_always,
         "description": "지금 점검하면 비용이 들지만, 방치하면 더 큰 손실이 날 수 있습니다.",
         "choices": [
             {"label": "긴급 점검 (-300만원)", "delta": -3 * MONEY_SCALE, "result": "엔진을 점검했습니다. 큰 고장을 예방했습니다."},
             {"label": "운항 강행", "success_chance": 0.45, "success_delta": 0, "fail_delta": -8 * MONEY_SCALE,
              "success": "다행히 엔진이 버텼습니다. 추가 비용 없이 항해합니다.", "failure": "엔진 고장! 수리비 800만원을 부담했습니다."}]},
        {"title": "해적 위험 경보", "condition": event_condition_always,
         "description": "의심 선박이 감지됐습니다. 안전을 확보할지, 위험을 감수할지 선택하세요.",
         "choices": [
             {"label": "보안 호위 요청 (-200만원)", "delta": -2 * MONEY_SCALE, "result": "호위 서비스를 이용해 안전하게 통과했습니다."},
             {"label": "항로 유지", "success_chance": 0.50, "success_delta": 4 * MONEY_SCALE, "fail_delta": -10 * MONEY_SCALE,
              "success": "위험을 무사히 통과했습니다. 일정 보너스 400만원을 얻었습니다.", "failure": "해적 피해로 화물과 장비 일부가 손상됐습니다. 손실 1,000만원이 발생했습니다."}]},
        {"title": "정부 친환경 보조금 심사", "condition": event_condition_government,
         "description": "회사의 친환경 전환 성과를 인정받아 정부 보조금 심사 결과가 나왔습니다.",
         "choices": [{"label": "확인", "effect": "government_grant"}]},
        {"title": "대형 화주의 러브콜", "condition": event_condition_big_client,
         "description": "대형 화주가 제안했습니다. 이번 항해 운임을 높이거나 계약금을 즉시 받을 수 있습니다.",
         "choices": [
             {"label": "운임 20% 인상", "effect": "income_percent", "percent": 20},
             {"label": "계약금 300만원 받기", "delta": 3 * MONEY_SCALE, "result": "계약금 300만원을 즉시 받았습니다."}]},
        {"title": "연구소 신기술 시범 제안", "condition": event_condition_research_lab,
         "description": "연구소가 미완료 탄소 기술의 무료 시범 연구를 제안했습니다. 수락 성공 확률은 50%입니다.",
         "choices": [
             {"label": "시범 연구 수락", "effect": "free_research_chance", "success_chance": 0.5},
             {"label": "거절", "delta": 0, "result": "시범 연구 제안을 거절했습니다. 변화는 없습니다."}]},
        {"title": "항만 파업", "condition": event_condition_strike,
         "description": "목적지 항만에서 파업이 발생했습니다. 기다리거나 우회 하역을 선택할 수 있습니다.",
         "choices": [
             {"label": "파업이 끝날 때까지 대기 (운임 -10%)", "effect": "income_percent", "percent": -10},
             {"label": "다른 항구로 우회·하역 (-400만원)", "delta": -4 * MONEY_SCALE, "result": "우회 하역을 선택했습니다. 비용 400만원이 발생했지만 추가 지연은 없습니다."}]},
        {"title": "돌고래 떼", "condition": event_condition_dolphins,
         "description": "돌고래 떼가 배를 따라옵니다. 보고 지나가면 운이 좋아질지도 모릅니다.",
         "choices": [{"label": "확인", "effect": "dolphin_luck"}]},
    ]
    last_title = st.session_state.get("last_event_title")
    candidates = [e for e in events if e["title"] != last_title and e["condition"](ship)]
    if not candidates:
        return
    event = random.choice(candidates).copy()
    event["ship_id"] = ship["id"]
    event["ship_name"] = ship["name"]
    event["ship_type"] = ship["type"]
    st.session_state.event_pending = event


def resolve_event(choice_index):
    event = st.session_state.event_pending
    if not event:
        return
    if choice_index < 0 or choice_index >= len(event.get("choices", [])):
        return
    choice = event["choices"][choice_index]
    ship = get_ship(event.get("ship_id"))
    effect = choice.get("effect")
    result = choice.get("result", "선택을 적용했습니다.")
    delta = int(choice.get("delta", 0))

    # 기존 delta / success_chance 이벤트 호환
    if "success_chance" in choice and effect not in ("free_research_chance",):
        if random.random() < choice["success_chance"]:
            delta, result = int(choice.get("success_delta", delta)), choice.get("success", result)
        else:
            delta, result = int(choice.get("fail_delta", 0)), choice.get("failure", result)

    if effect == "government_grant":
        emission = current_emission()
        if emission <= 30:
            delta, result = 10 * MONEY_SCALE, "친환경 성과 우수! 정부 보조금 1,000만원을 받았습니다."
        elif emission <= 50:
            delta, result = 5 * MONEY_SCALE, "친환경 성과를 인정받아 정부 보조금 500만원을 받았습니다."
        else:
            delta, result = 2 * MONEY_SCALE, "정부 보조금 200만원을 받았습니다."
    elif effect == "income_percent":
        if ship:
            old_income = int(ship.get("returning_income", 0))
            percent = float(choice.get("percent", 0))
            ship["returning_income"] = max(0, round(old_income * (1 + percent / 100)))
            ship["voyage_income"] = ship["returning_income"]
            result = f"이번 항해 예상 운임이 {percent:+g}% 조정되었습니다. ({money_label(old_income)} → {money_label(ship['returning_income'])})"
    elif effect == "free_research_chance":
        if random.random() < float(choice.get("success_chance", 0.5)):
            levels = st.session_state.get("research_levels", {})
            available = [t for t in RESEARCH_TECHS if int(levels.get(t["id"], 0)) < len(t["stages"])]
            if available:
                tech = random.choice(available)
                level = int(levels.get(tech["id"], 0))
                stage = tech["stages"][level]
                levels[tech["id"]] = level + 1
                st.session_state.research_levels = levels
                result = f"시범 연구 성공! {tech['name']} {level + 1}단계를 무료로 완료해 배출량을 {stage['reduction']}%p 감축했습니다."
            else:
                result = "완료할 연구가 없어 시범 연구 효과가 발생하지 않았습니다."
        else:
            delta, result = -2 * MONEY_SCALE, "시범 연구에 실패했습니다. 연구 지원 비용 200만원이 발생했습니다."
    elif effect == "dolphin_luck":
        if random.choice([True, False]):
            delta = random.randint(1, 3) * MONEY_SCALE
            result = f"돌고래의 행운! 소액 보너스 {money_label(delta)}을 받았습니다."
        else:
            delta = 1 * MONEY_SCALE
            result = "돌고래 떼를 발견했습니다. 기분 좋은 조업 보너스 100만원을 받았습니다."

    st.session_state.money += delta
    if ship:
        ship.setdefault("event_log", []).append(f"{event['title']}: {result}")
        ship["event_cooldown"] = 8
        ship["voyage_event_count"] = ship.get("voyage_event_count", 0) + 1
    st.session_state.event_log.append(f"{event.get('ship_name', '선박')} ({event.get('ship_type', '')}) · {event['title']}: {result}")
    st.session_state.last_event_title = event["title"]
    st.session_state.msg = result
    st.session_state.event_pending = None
    add_history()
    if current_emission() == 0 and st.session_state.phase != "ended":
        st.session_state.phase = "ended"
        st.session_state.result = "success"
        st.session_state.msg += " 회사 전체 배출량 0% 달성! 탄소중립 성공!"


def route_position(route, fraction):
    """경유점으로 구성된 바닷길을 따라 현재 선박 위치를 계산한다."""
    if fraction <= 0:
        return route[0]
    if fraction >= 1:
        return route[-1]
    lengths = []
    for a, b in zip(route, route[1:]):
        lengths.append(((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2) ** 0.5)
    total_length = sum(lengths) or 1
    target = fraction * total_length
    travelled = 0
    for i, length in enumerate(lengths):
        if travelled + length >= target:
            part = (target - travelled) / (length or 1)
            a, b = route[i], route[i + 1]
            return (a[0] + (b[0] - a[0]) * part, a[1] + (b[1] - a[1]) * part)
        travelled += length
    return route[-1]


def make_route_map():
    """OpenStreetMap 위에 항구 핀과 바닷길을 표시한다."""
    fig = go.Figure()
    # 부산은 출발항, 나머지는 클릭해서 고를 수 있는 목적지 핀
    destination_names = [d["name"] for d in DESTINATIONS]
    pin_names = ["부산"] + destination_names
    fig.add_trace(go.Scattermap(
        lat=[PORT_COORDS[name][0] for name in pin_names],
        lon=[PORT_COORDS[name][1] for name in pin_names],
        mode="markers+text",
        marker={"size": [19 if name == "부산" else 23 for name in pin_names],
                "color": ["#ff6b6b" if name == "부산" else "#f2c14e" for name in pin_names]},
        text=["⚓ 부산" if name == "부산" else f"📍 {name}" for name in pin_names],
        textposition="top right",
        textfont={"color": "#071521", "size": 15},
        customdata=pin_names,
        name="항구 핀",
        hovertemplate="%{customdata}<br>클릭해서 항구 정보 보기<extra></extra>",
    ))

    # 정박 지도에서도 항해 중인 모든 선박의 현재 위치를 표시한다.
    for ship in active_ships():
        dest_name = ship.get("dest")
        route = SEA_ROUTES.get(dest_name)
        if not route:
            continue
        leg_years = max(1, int(ship.get("leg_years", 1)))
        years_left = max(0, min(leg_years, int(ship.get("years_left", leg_years))))
        fraction = 1.0 - years_left / leg_years
        if ship.get("status", ship.get("phase")) == "returning":
            fraction = 1.0 - fraction
        ship_lat, ship_lon = route_position(route, fraction)
        fig.add_trace(go.Scattermap(
            lat=[p[0] for p in route], lon=[p[1] for p in route], mode="lines",
            line={"width": 3, "color": "#42c7d9"}, name=f"{ship['name']} 항로", hoverinfo="skip",
        ))
        fig.add_trace(go.Scattermap(
            lat=[ship_lat], lon=[ship_lon], mode="markers+text",
            marker={"size": 18, "color": "#ff6b6b", "symbol": "circle"},
            text=[f"🚢 {ship['name']}"], textposition="bottom right",
            textfont={"color": "#ffffff", "size": 12}, name=f"{ship['name']} 위치",
            hovertemplate=f"{ship['name']} · {ship.get('type', '')}<extra></extra>",
        ))
    selected = selected_ship()
    dest_name = selected.get("dest") if selected else None

    if dest_name in PORT_COORDS:
        center_lat = (PORT_COORDS["부산"][0] + PORT_COORDS[dest_name][0]) / 2
        center_lon = (PORT_COORDS["부산"][1] + PORT_COORDS[dest_name][1]) / 2
        zoom = 2 if dest_name in ("로테르담", "로스앤젤레스") else (4 if dest_name in ("싱가포르", "홍콩") else 5)
    else:
        center_lat, center_lon, zoom = 30, 125, 3
    fig.update_layout(
        map={"style": "open-street-map", "center": {"lat": center_lat, "lon": center_lon}, "zoom": zoom},
        uirevision="keep-user-map-view",
        clickmode="event+select",
        height=600, margin={"l": 0, "r": 0, "t": 10, "b": 0},
        paper_bgcolor="#071521", plot_bgcolor="#071521",
        font={"color": "#f3f0e7"}, legend={"orientation": "h", "y": 0.02},
    )
    return fig


# 페이지 설정은 다른 Streamlit 명령보다 먼저 호출한다.
st.set_page_config(page_title="탄소중립 선박 경영", page_icon="🚢", layout="wide")
init()

st.markdown("""
<style>
    .stApp { background-color: #f3f6fc; color: #172033; }
    [data-testid="stMainBlockContainer"] { max-width: 1500px; padding-top: 1.2rem; }
    h1 { font-size: 1.8rem !important; font-weight: 750 !important; letter-spacing: -0.04em; }
    h2, h3 { letter-spacing: -0.025em; }
    [data-testid="stMetric"] { min-height: 104px; display: flex; flex-direction: column; justify-content: center; }
    [data-testid="stMetricLabel"] p { color: #69778d !important; font-size: .78rem !important; }
    [data-testid="stMetricValue"] { color: #172033 !important; font-weight: 750 !important; }
    [data-testid="stVerticalBlockBorderWrapper"] { border-color: #e1e7f0 !important; border-radius: 14px !important; }
    .stButton > button { min-height: 2.65rem; font-weight: 650; box-shadow: 0 3px 9px rgba(40,85,217,.10); }
    div[data-baseweb="select"] > div, .stTextInput input { border-radius: 9px !important; }
    div[data-testid="stTabs"] button { font-weight: 650; }
    h1, h2, h3, p, label, div, span { color: #172033; }
    [data-testid="stMetric"] { background: #ffffff; border: 1px solid #dce3ed; padding: 14px; border-radius: 12px; box-shadow: 0 2px 8px rgba(20,45,80,.04); }
    .stButton > button { color: #ffffff !important; background: #2855d9; border: 1px solid #2855d9; border-radius: 9px; }
    .stButton > button:disabled { color: #7b8798 !important; background: #e8edf5; border-color: #d4dce8; }
    div[data-baseweb="tab-list"] button { color: #172033 !important; }
    [data-testid="stExpander"] { background: #ffffff; border: 1px solid #dce3ed; border-radius: 12px; }
    [data-testid="stAlert"] p { color: #172033 !important; }

    /* 왼쪽 기본 페이지 목록은 밝은 배경과 검은 글자로 표시 */
    [data-testid="stSidebar"] {
        background-color: #f4f5f8 !important;
    }
    [data-testid="stSidebar"] *,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] a,
    [data-testid="stSidebar"] button,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {
        color: #111111 !important;
    }
    [data-testid="stSidebarNav"] a {
        background-color: transparent !important;
    }
    [data-testid="stSidebarNav"] a[aria-current="page"] {
        background-color: #dfe4ed !important;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

if not st.session_state.started:
    st.markdown("""
    <div style="background:linear-gradient(135deg,#081a35 0%,#123d78 62%,#1e56b5 100%);padding:34px 36px;border-radius:20px;color:white;margin:4px 0 24px 0;box-shadow:0 14px 35px rgba(8,26,53,.18)">
      <div style="font-size:12px;letter-spacing:3px;font-weight:800;color:#a9c7ff">MARITIME ZERO · MANAGEMENT SIMULATOR</div>
      <div style="font-size:32px;font-weight:800;letter-spacing:-1px;margin:12px 0 8px;color:white">탄소중립 선박 경영</div>
      <div style="font-size:15px;line-height:1.7;color:#e2ecff">해운회사를 설립하고 선단을 운영해 2050년 탄소중립에 도전하세요.</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("## 회사 설립 및 선주 등록")
    st.write("**목표:** 선박을 운영해 수익을 얻고, 단계별 기술을 연구해 2050년 탄소중립을 달성하세요.")
    login_col1, login_col2 = st.columns(2)
    with login_col1:
        st.text_input("해운 회사 이름", key="company_name")
    with login_col2:
        st.text_input("사용자 이름", key="captain_name")
    st.write("**중간 점검:** 2030년 배출량 80% 이하, 2040년 30% 이하, 2050년 0%를 달성해야 합니다.")
    st.write("**조작법:** 부산에서 출항해 해외 항구에 정박한 뒤, 다시 부산으로 돌아오면 운임을 정산합니다. 항해 중 사건은 선택지를 고르기 전까지 시간이 멈춥니다.")
    st.info("게임에서는 이해를 돕기 위해 감축량과 수치를 단순화했습니다.")
    if st.button("회사 설립 후 게임 시작", key="start_game", type="primary", use_container_width=True):
        if not st.session_state.company_name.strip() or not st.session_state.captain_name.strip():
            st.error("해운회사 이름과 선주 이름을 모두 입력해 주세요.")
        else:
            st.session_state.started = True
            st.session_state.phase = "docked"
            if (st.session_state.get("annual_quest") is None
                    and st.session_state.year in QUEST_YEARS):
                generate_annual_quest(st.session_state.year)
            st.rerun()
    st.stop()

# =========================
# 최종 엔딩 화면: 기존 게임 UI와 분리된 전용 화면
# =========================
if st.session_state.phase == "ended":
    company = html.escape(str(st.session_state.get("company_name", "해운 회사")))
    emission = int(current_emission())
    reduction_rate = max(0, min(100, round((START_EMISSION - emission) / max(1, START_EMISSION) * 100)))
    final_money = money_label(st.session_state.money)
    total_income = money_label(st.session_state.get("cumulative_voyage_income", 0))
    fleet_count = len(st.session_state.get("fleet", []))
    voyage_count = int(st.session_state.get("voyage_count", 0))
    success = st.session_state.result == "success"
    if success:
        subtitle = "더 나은 바다를 향한 당신의 항해가\n마침내 탄소중립의 항구에 도착했습니다."
        status_label, target_title = "VOYAGE COMPLETE", "탄소중립 목표 달성"
        target_desc = "지속 가능한 해운의 새로운 기준을 완성했습니다."
    else:
        subtitle = "도전은 여기서 마무리되었지만,\n더 나은 바다를 향한 여정은 계속됩니다."
        status_label, target_title = "VOYAGE ENDED", "최종 운항 결과"
        target_desc = html.escape(str(st.session_state.get("fail_reason") or "이번 항해를 마무리했습니다."))
    banner_image = "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAQDAwMDAgQDAwMEBAQFBgoGBgUFBgwICQcKDgwPDg4MDQ0PERYTDxAVEQ0NExoTFRcYGRkZDxIbHRsYHRYYGRj/2wBDAQQEBAYFBgsGBgsYEA0QGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBj/wAARCAGJAkwDASIAAhEBAxEB/8QAHQAAAgIDAQEBAAAAAAAAAAAAAAECAwQFBgcICf/EAEkQAAEEAAQDBQMJBgQFAwQDAAEAAgMRBBIhMQVBUQYTImFxBzKBCBQYI0KRlKHhFTNSscHRJEPi8BY0ZHSSJVRiY3KTolOEsv/EABsBAAMBAQEBAQAAAAAAAAAAAAABAgMEBQYH/8QALxEAAgEEAQQCAgEEAQUBAAAAAAECAwQRMSEFEhVBE2EiUTIGFBZxIyRCUoGRov/aAAwDAQACEQMRAD8A+/teiNeiVotBI9eiNeiVotAD16I16JWnaADXokd0Wi0AFnonr0StF+SAHr0Rr0StFoAevRGvRK0WgB69EteiLRaAC/JAukWgHRAD16I16JWi0APXojXoladoANeiNeiLRaADXolr0TtK0AAuynr0SvVO0DYa9Ea9ErRfkgQ9eiNeiV+SL8kAPXojXolaLQAHbZBukboKMjQc09eiXxRr5IEPXojXolqi0APXojXolfki0APXojXolfknaAFr0QLTSGyBj16I16ISvyQIevRGvRK0WgB69Ea9EtUWUAPXojXolZ6JoAXPZPXolzT1QAa9Ea9EIQAa9Ea9EJaoAevRGvRK0WUAGvRF+SLRfkgBIQUJobBCEJiyCEIQAIQhAAhCEAfPX0yPZP8Awca/C/qj6Y/sn/g41+F/Vfn+EUvtF0C2+z5fy9c/QKP5YfsqkJys4zp/0v6qz6X/ALLP4OMfhv1XwHhN3LJWsf6dtWs8mcus10fef0v/AGWfwcY/Dfqj6X/ss/g4x+G/VfBWiE/8dtfsF1m4PvT6YHsr/g4x+G/VL6YHss/h4x+F/VfBiR0Sf9O2v2Hmbg+9Ppgeyz+HjH4b9UfTA9lf8PGPwv6r4KQj/HrX7DzNwfev0wPZX/Dxj8N+qPpgeyv+HjH4b9V8E0ikf49a/YeZuD71+mD7K/4eM/hf1R9ML2V/w8Z/C/qvglCX+PWv2Hmbg+9vpg+yv+HjP4X9UfTC9lX8PGPwv6r4JKXxS/x61+w8zcH3x9ML2VfwcY/C/ql9ML2VV7vGfwv6r4IrzQUf49bfY/M1z73+mD7Kv4eM/hf1THywfZUdQzjH4X9V8Deg/JM2G6FJ/wBP2q/YeZuD76Pyv/ZaCPq+Ma6/8t+qj9ML2V62zjAr/pv1Xwe5wexz3NIDWhoPmq3xmOJuajYuwo8DbfYeZuD7zPyw/ZUD7nGT/wD1f1UpPlgeyuMgObxjUX/yv6r4FaSHhw1FpyOMsxdRGqXgbb7DzFwffB+WD7KwwOycYIP/AE36qTflgeyt7mtazjBJ2Awv6r4GjF0y9z9ylGHMxedprJrdaJPoNv8AYeYrn3mflieyoHWPjP4X9VJ/ywfZXG7K+PjINX/yv6r4EcM0rjd63oEiS551KPBW32LzNc+/G/LB9lb2Oe2PjJa3c/NdvzS+mF7Ksgdk4yAdv8L+q+BgajIzEA6eRUpGnIH8gcoCT6HbfYeZuD73+mH7KtabxnQ/+1/VI/LE9lINZeMX/wBr+q+CspMBkNanYVooO7vuGuBOck5kvCWy/YeZuD74PyxPZSPscZPphf1S+mN7KP4OM/hf1XwECQdNUqGf1HII8Jb/AGPzNwff30xvZRlvJxj8L+qk/wCWH7KmNaSzjFOFj/C/qvgTJULTr4tDoi3PcxhdtoL5JeEt/snzNx9H30fljeykfY4z+F/VH0xfZTzZxn8L+q+AjZkN8lIsJLQLs8keEt/sPM3H0fff0xfZTV5OM1/2v6pfTF9lGXNk4z+F/VfBEjcuHYdbKoJ8J3S8Lb/Y11m4+j7+HyxfZSfscZ/C/wCpI/LH9k4NGPjV/wDa/wCpfAniaBe5FiwouAzjQE+iXhbf7DzNwffx+WN7KALyca/C/qj6Y/soqyzjVf8Aa/qvgF1HTRI+pS8Lbh5m4P0AZ8sX2VSEhkXGiQLr5r+qiflj+ygOrJxn1+a7/mvgfCTy4cSuiNZ25HHKNlS4eKwp8NQB9arn399Mf2Ufwca/C/6laPlgeyz5u2fu+M5HGh/hd/zX5+j3CT/JXRhowwIJu0eGoCfWrg++Ppj+yjNl7vjN/wDa/qg/LG9lA3Zxj8L+q+Aj7981Fx8SPD0A8zcP9H379Mn2Tg+5xm/+1/VH0yfZP/Bxn8L+q+AXiyNdFXqHc0eHtx+ZuPo/QJ3yyPZO2rbxk+mF/VB+WV7Jx9jjX4T/AFL8/wB5t98lB1ZtdR6JeIoDXWa5+gP0zPZNf7vjX4T9VM/LI9k4F5eM6/8AS/qvz6LR3grZWOdVXyS8RQB9YuPWD9AfpkeycmsnGvwv6pH5ZPsnBox8a/Cf6l+f4Iom0UKNgfcl4igT5m4+j9Afpkeyir7vjX4X/Um35ZHsodszjWgv/lP1X5+t0B/smCWxkAed1qk+k0BeauD7/wDpleybMBk4zr/0v6od8sn2UN3Zxr8L/qX5/wATg2a3DMCOajLTsxHTQUNUvE0BrrNxk/QEfLL9k38HGvwn6oPyy/ZKDWTjV/8Aa/qvgGOInBme2+9lA5nTdUEEuJ6I8VQH5mvk/QV3yy/ZMKBZxr8J/qR9Mn2T5M2TjX4T/Uvz5sucDW3krLsZf6I8VQG+s10foAPlmeyX+DjX4T9Uz8sv2TAX3fGfwv6r8+W22QnT4hTcdNd/IJeLoA+s3B+gY+WZ7JjszjP4T9U2/LL9krzTWca/C/6l+fTHUxxREKt39FL6ZQF5q4P0DPyzfZKDRj41+F/VP6Znsl7vPk41X/afqvz3kreh9ylIC2Fo015UjxlEfmK5+go+Wb7JSPc41+E/1JH5Z/skBrJxr8J/qX59VbL/AKKhxObl9yXjaILrFds2ITSG6a+wPOMnCfaWSsbCfaWStoaMZbIoQhUJAkU0jukxiQhCQAhCEARQhCABCEKcACRTSO6AF8Ex7p2SU2gCMn+amWh7LpczcOxmYeLxEBQlIMMbdzSTXAFheDoefNDgDE91GyaCyYyLm5YWuIoOPhFqLLDS8jw7fFTa0yPLaIDRarskZeV6BMBsDg0vbfh5q7OSJC59mgAk2MuicGgWNxf9FW5zmMc0irPRJiZX4Q1xdudj0U3hohZ9WGuA5D3k+6MkgjjGfS9B96iS50lAnQUAeShiLMMwTSmGtNweiUbDPjBGXAZnEC1GNxZLmaSOVqUAygzVoLF9CkxkA13du/hBokdeSjbgC0FXwOAcGysJYSXGtL0WPIbkLmggE6KWIi05WOdlsu0DuiTQXPDRqd6UpMvctcwEDY31ThLGlxeDdaUkU9Dc4ugZEQ0BpvzUA42QdgNEwSCdKCTmjVBBIBvdB3MKbWOMUkt5cunqUnuIgY11Zq09Faxhdw0vBbQfqOZ81LY8FVXhS4v8QNAeSgcphHhOYblA9zQ+qmWjugL1KQipxcQLJNIAGc5j8UaAEapA0NdbQwAC35uWwUnsJjzja6S0vQGh1UxGTIGjXmkGSoEtGW90iCXVak5hc+2i0m3nsgqQ2Te3KfAbCk0uoM/3ai2i7UUpOO3VBJB9h+wsGtFXmBHJXAeFxPNUhvjFjQHVSUgdrWlc02UISeZ6hEzmuecoocvRQaSRzQMGENvM03e6jLV6KdADXdVkF8mnRSNPLBoJAd080zqU2V3eqgbDrGyA2TLQSKKsc05b5Ktpv1V5LTh6okqSHsqj8bqQ+9fuTjBAc7YBKyTXVJh7EwfVWQFU4mgNuiuqtFW9pLgFLKRIeCMBVOJsqRdyKJGjQApAkEfhbqmTRN8lFtiOuakGksLiPJJif2V3b7OyZJsgBJgGajqrKyuLVLG+Cp/hjAGitaB83Vcos5QmAQ0C/gkJlcgIy2pyasFp5S8eiCC4UeSRWSJ0hAVOUnWlc+ycvkqiSDQSHEz0IQvoDQycJ9pZKxsL9pZK2hoxlsWwSTOmhSVCQJFNIqRiQhCABCEIAiTaEfehAAhCEmAIQkDqkABWRBrnBrhY/qoLIwzPFncARqQOlbKZaGiuamitTl3obKU7iyGNh3DbKrdZeSQSTqdUpXlxLje43WYwaTHLnBslvNJosmQimhX4gAU4ObrTco8t1jgtaHhwOuzQkBMSU90jhqRY0RI0CNshBOYHn0TnaQGE7FlgdFBzw6GNpIppSEx4aQxGSSr8FC+VowoaZPdJN1V7hKTRjRycAkRWV/K6+5SwYyCHvyN0vTnSte9ow4gabLnB5Pw2UXPLJxLHdA2P6qLGvzF7gQRZ1FKREDWUNsgnn0SkyZh3Y8IFX1VhDXYglz8zQDr1VOYCEih5eSTEVEkkNHVWggMbsTzVZ3BqlJgbRu7rSkinokQGOad+ZQ7VxOoHMKJBc4NA12HmthiI2wcNZhslzFxe93TySbE0a+QgvFEnSlY19YfLepO1KtrcxrpqpxkZDYsnzRsRAUZKqweStzVE7MAeQ8lBlBw0JvUqT3NcNjWbQpMRUwE614RuVIgZL6nZIE5S0bE7Ica3SY8kSASaNK6RuQNcH2C2rCqY0yStjbVuPNZXEGGOfuS5p7sAeHZS2NoxbFeHRRG+qkOV0k6wdOSRGiwtbm0SfVCjvoroIXPBeaIYMzlQ8jNegvWksiSDeLNyulUNZP5q1oLRrR8lV7rjpokUhOOuuycQD31YA80nVSGihZG6CskruMm9SapVhu+6kbz+SR5pMEQBN0DonYMlckrDRdKQFMtIb/ZJjQeYVj3hxDQ0Chy5pQuYPE5ocANiotFEmtT+ShmYHwspVtdco6KyTQUq2XYAbZSGiRsy0NUTtLXgGweaVnOKsap4q9wb81I/ZB4qjvooDV/K1YG3AHh2vPRVgG7QUhOJD1e2+7LddVQ4nvaVsbjnopMUioDLKG81dPlsZLutVW4HvQedolLiC66UsWxMYXknoouI1V0YLWZjzWO/96RyKQ47MnDOa3Dynu2uJAAeT7uvJVNPjN7bKzQYcNBVLDrSkWcgTbna+ii1pIsqZae7sAJNIDRZQV6MpCEL6A1MnC7OWSsfCjRyyFtDRjLYikmUlQkCKtCFIxUkmUkACEIQAqQUWgoASEIQAJCr3TQpAFdC4jDyAepPlap5KUV6uABA6qZaGgIcxzgaJI1QSHyN7z3R0UHOLpCeZ1VsjG5R3broDVZgRJ8Nu3GmUjZRcLyWNyrQA9zmnXK3UBRYHSTFzT7gJHwSETlkDyGhoAYNlj1qSQa5UFa14ERGpLjZIUcn17Q85QdSpYbYiO8eRo3K0c1F7s2XRtjorHub3TWs230CTA57mxZdSdOqQFmLjiiEbYn5zlBPkovlBwrG5TYYbN3eqgQ9xsCqGrgeWyrJ8WmrfM6KcAZIhj/ZxmYbfnyuFcuSw36aLKLwIAxrswNErGe3NbrA1pTgPYzHcOeq6J4ZpfNo4Nygk36IJBja0AADod1BtBxB6IDIwDJM4ga+8fJW3cDnufpdNHVKJpMZIlaHO0o9FB+waSNOnJJiYNNNcBzCbdI3baqO0ZA1vmrnGOr7vuzlAa0cz1SArYXFpDTqBSliWiJ7WN/h19UoWkye9VC1E26W7BI1vzSYiTgAQ0DUDmq3ajbW6Vj3l7i5x8Tt0nEF12AkBBjXh+cD3edbKU0jpXlzjZTcHNY4CwOfmqLp4NpMB0WiyrI9ySOSjLbTlKsw4BD3O5DT1SYbJZywOa0kB26prNMBWnkrHtc1oNg2OShGAcxdppopFERBLy3zVcwIGnJTiY9z3FrToNVB9k1e6BpAbcy62UnkCJo3NbdEA6a/coPL5JgKs+STHtg0WNdCiQEaBZEOHdK17h4WMFucRssZ1usjZLI/ZU45hXRW/wCWFUAM+itrUC9EMctDb0GylyUaNGlMD6sDmVDM2VgFztUgS2Q1p5qTQWg0k7VnqkNEaJn0NDmpTlrpKjJyjqlFYeS7oouPjKTKWxHRoaNlEaaoaRmokqcliPfdIMlbbdITdqW0ljkoRZjIQrm6k6KQlwJ2r8yrcfqwOqHOon1U3hoygpMQPeWQNaqstta5WTjwivuUAai15pDQ3EFoo6qLbvQKLTZKti942UmN8IsdrASK6KoM0Ck9xDKHVSD2gURqkQi1CE6X0B0GThTQcVkLHw2zlkLaGjGWxFJMpKiQQhHNJlCKSZSSAEIQgAUTupHZRQAIQhAAhCNUmAKTTy66KKmADG0Efa1Uy0MheQ2OXOldYGFGYF1D81ANDonuuqqxaUji6naN05LN8gi0ACFxceQ25noqmucx79TThqBzVz2EVFYLWU53qqoaMzg3mCPhuoBkmtIiYHeGzYIVUmrwHO8rWU1gY18gfZaKA8ysV1DXf15pbENrw8NAbsBdbKxj44o+8BuR90QfdCUBaMK5pJskVpzCi1tmQOyA0kBFrHBgefdutUQgGcSU3KH3R2Tc572tZeYtGwRAB3mhAP8ANJgnyKTKXyBpBaCSK5qD4nMbb9Na9E3132UbNNb7q2NoljMkjuRNHr0UgYwAy2bzDZOOyH7ZfTdRIoj+hTshhbZA6JAOOu8tzbBGwUd30BqfzTB05ptLY35iDtbaSYhNAD6fddFdIGFjHNOpGvkh0b2El7SC5tm/5qGhYKSERAIB1+KcQa6Qh7g3TbqjOcgj6G/NIMIYXkb6IAHUHeSife0pWPMYa3IHN08VncpMAeMoAzE1ZKTEyL3kxUdQq2NzEGtlOYZCY7HhNaJQg904nYKWUtESc0lamlNttGTz1UY9H2VNxuSxokSyyZ7XZa08IsBUnwx7aKRrug4ncpzMdH9W8i6GxUgiMT3Ma4MJaH6OrmFW/KX+HYaKYOVuxVeYd3tRQUhg226oqGxJH5IbIQ0hugO6kLEdn4JMZMFzIiwE67i1U4ODMynmsX1UJbyUpJT5IMB1NKRNWDuiMnKBWyk+s+yMlN+iTSO6Noc+6PlSemQCrJUJAWvDefNQZkmi2EVqqnHLQ6FXZqqlCVoBab0PMJMcdiNCUEajmoW3OSdlNzWkkMvKOZUABqCEMpFd6qcpPdajZVkGwa0tN7y8UKtSymsslhiPETfRTZYNVfko4fw2CrAQ6U3skxS2UVcjhXNSfeZprZApsjnDqo5yQVIiRpzjagaDdSpt1CrlcGupJjjvAqDee6mzQm0AB0WbmosdlYTzKQ3yTbTnWdNdlVJIO8KviflYa5rDeC+QuvmpFE2SYQAmvojYyMNs5ZCx8L9pZC2hoxlsR3ST0tJUyQSpNCTKEeiSZpJIAQhCAA7JV5pnZKkAJClsolAAhCEmAK2Cs5cdMoVSnGL3dl52ploCLHEPObUdFMRmSUNaL0zEdFAAmzd81IOfGx2UkFw1d5dFm0A3yAOOUkgivVSjgd3x2BYzMVUwNMjAQS29gLKvjAfPKC4+6dN70UtDFARbgcxF2Bax3k3zNaC99FJti37UpNaXRlxJFu000PVTpiYmNDw4hx8IvU80o3gQvY6mkixpdqURoPaGEnqP6qgizlFb7pCLIyRZ1silkYB0QmfndlJFMJ1UO7LcJ3jhq73Td2reGsLsY1xbbGWbI0GhUSY1sw5zlneAANdVFuYtJ2F6Kc0jnh4oauLiepVbXHJQPOggGJlufVHRNxzPJ+ARmdGHgHR3hdSidGiuSQDAIBF31QKdI3M0lo0ITzkQlo+1qURkllZTbjSTEZkrM+BOKLiDnyNbfKljxvcY+5DQdc2g1VmLcbDLJyjZUx6MLvFZClCIjQl1gOHIqYaTVWqw0ueA0anksvDuZE6ZpvPkpruh5/khgYm7tNAnGQH246WkbaaG5GqHHK3SkkJkHnNI6qq0s2uXlyTJoWeaGUTmOw6IK9EwARy0VZBMoBKs+xp1tVggkutSSXSua6TN3YDdqUJbyjNvV35IJ0BPND3Zi0HkN1ICsvLczidNLVcooK0ENJdV6U2+SrmytjoG9KJ80mUtlLPE00r3G2Ab0KVETSKHIlXPIz2NkehyHoWgVVKDiSK3UzQaLOtqsHU9VLJQR6sPkeaRsuCGGyQndFSx+yYccwPMKDiS61JotxN7qL6a9tG0hLZNujd9VGeUyysBG2isdYbZKxwbmBvVJgiyQ6ihXLRQcSGA9U3m3fFRlPu+SQIKHdl1Klop1lZTy0w0FTE28ztC1o1SZcWSioPN7dVMEZXdSlkqEnVKAjvhsQFLIZB1NNXarf4Xg8ldiC0yOcBQu6AUHDNDmSLROJwLdlRN4pbTByt3KUYzSWUmC/ZYXfVUNKQ0NMV2lMPCKRGPAQpyIjew1VL9Hmip0XGgToqHe+Uioo26EIX0RoZGG2cshY+G2cshbQ0Yy2LXySRRQqJBCEJMoV+SL8gikkgC0IQgASTOyVIALSTpJAAhCEMAO2ilHqctWVFWwh9ucNgLKmWgKqoZrG9AFWMJaHAmx/VJ1O1G7jdJNaKdmNVy6rEBWBEG5bedbWUHMidIQ0XWXp6/zVWHDRK10jRQBIJ5nokDmeC4gNI1O6ljKXuHd5RpZVveH5qyMkaEkfFVyBuemuBF9FJ1PFUdNAhiYw2VuFM4Ja15yeqrAzMDQ33dyFkSvbLg2ZLDW0A3z5qhjqfRuuqkGjMdM2Xu4u7tkceUNAG/VYrXiPMMt2KvZSDjFI7nY5oAvDvBGzhSiSApmLe8cWtytOoHklHKGuaRGwZWkDTdWYiTvKsWGtDAVTG0OkIO9aIwITzbvzSFl380Gg/a+Wqti8N6DXn0SDRU46UrMOxzyS3UN1KqfoTTrF0LWfgWwx4WaeUnvKAY0DTU0bUyeAwYszs7w51UeQPJZGPmgklaMKzJG1oaLO/X81iSay9a/JD3AnXfklgSfGCyAtE47wkMqjW6VuYRbS3S6RY+btAFk81Y4/WRySkuqiR6KQZU8OE2WtTy6JSBojbQN62ryTNirByOlNjyChjy101R6Boq+vmlkEUeFzQANQNSkNPuSjsDU/BN50vl6KmDJsLe6fobvToqmmnkVusojJw+Pxg5zmrmFihrnSAN1JKkC537sdQqWNLnjqrZm5XOYDdaE+ahE7I++YCTEh6WWkbKuYistDyVoGZxeb11WM8h0muuqllR2Sa1zXEEURpSmSAbpKZ5fMX0BZuggDM20gYpNWB2mvLom0VDmOt7JPNihuiy2OjtyUgRYbcQFJ4o1QBVcA/xGp0VslZy7dSD2DdAVEi5Lr7kxQFJNNAm90CwN5urOiroBxc3dSZ4n6glROmZtJMENviBJpVPOuvVWsIaCSNFU4gurbW1LKWy5o+r1CoYdCPNZbXvbgywVTudLGF94OikF9FpIENElQisAuryU5v3O43SYS2LId97SJWiE1AjVVgnNl5IlLibKi11eKtVLZolwJxGfKD8VdGGlt8xosYlxmAH3LOjFM1G6TYp8IqdRfXRLOWC6TkblmtRe4ZgOqRKINPjrXVQe2nnRWgt7/0SkIL9kFozkIQvojQyML9pZCx8Ns5X6raGjGWw0STPokqJBCEJFC080k/glokAIRohAAdkgmhAAdlG0ykgAQhCADStVIECI0dyBSjr0Tz+DKdrUy0BZC3vHEuHhaCVFjTISNG14iSk1wbGQGm6pSijzg0NWiyL3WICGgYHkluulbKT3t7twY3yukn1LIXa6cugpQeW5m9OdFSBJ2RhBaMxI3IQG1CZHaOOgCgbIyg2Bqm4Wa0A6WgTCIk3CXAD3tdtE2Bnz5lCmgjR2qhG252m6bdZla6jinPcQ4N5/wAlIxyXLiHhhqzoK2SYHvxDYGkOGarCTGyPZI7k1tknmkJcuGIDfEHZg7oK2UyEVStDZixpzEOO2yTHZXkirPNScGulFmgT9yhLlLiW0AdgEsjIu1cCdh0Uy7u4iKdmdrd6UotHhJ13pSc0GZrZNQdD5JMXAnMJiLiaG1cysnvsnDy0MAJIaXXyGtKmW3SuaTma3Qa8k5XiXZoYAKACTDJAEkOrYlV2MxBVhccgFAUOXNV7OvokIsDqjyFu6k6+71+9LMXkCikfeoDW9B1Ukl0rO7giflyhzf6rGkIcxZ2MidBh44XEF1ZiL93yWAPE4gkChakaE0jLRCD4iABzTYwue2waJ3HRN2VmId3TjQ0BKMj2BJrKTdBQYKNpvcAAG35nqm1tjehzKAGDmO2aykcgZdnMdKpEdl9NGw3S3OgUgWwTsha45MziKBOwWELfKTateaYeRtRhDg/QeLzSyUgcSTqRsrGisMDYoqtxHeKxx+qDbtJsTKyB3gJOiyMTGyKGICRsjizM6uRPJY+UZgRyNokfmeoYIrjO4/NTa7NJQQ5obVa6WpQNqblaQMcorZIMLGAuHvCwpTUH1RPL4qDbII5cikxLRHNlbp0TygtskXWyYcA2+d6KLnFzaO6QEQDkzUKKgwZpbOqmQ1sPmVCH97ZSZfrJmzyZWCgKIoDosRurs3RXS+IVyCqj8N2RSgmIpDbxrshtudQd96g9xJtRYefVLJWOAkut9PJGgYD/ACTdQdok++61KRSKIwXy5td1swBkaOaw8OwBnmr7IOnNSyKvLE4/WEc1TKdboZgnmAlJJVROZ180kCiN1ZQeajodbU5Y3CioZHDQBM0yjZoQnS+iKMjDfaV6ow32letoaMZbEbpJM+qSokEIQkNBqkb6BNFJDIoQhAAhCEACRPJNI0gBJ8kctEckgF8FJgzE7UBfqoqbQQ0uHMUFMwImnDQ+dAKyKiyY0B4dLKgHO93ypSLqg7sEb2fNZAOM+B4aQC8gVzVLjlHxpWQuylxzAHlYVclk1fPdLAEhkbzOo0IQH0+yAdK1ChZ2CsyVAZcta5QSeaTEAA7oXJWY1QQbEJbVjNdqLHAPa41XNWU17i3OADrZ5BSMg0vc4RtcRm80FoE7YntsC7DeaIy5s7S0t3oWpNDxiCNiQb1UsCOKNyWGBl8gqnZO4ZlJLqObTZOVxcW5ibA28lAZnnK2zpaWAJRWS6hQbraQa50t6k7qLQTsf1UryvvySExuY4lzg00D9yGuLH5t9NinG8m25jR1cAkRUPeciaGm6TFgiCXkAny1QRlFFTibRzBmYDVRku60B6dFLAcQFF5Boc62VsDe8xI8YaBrdqjNljLA46nVZ3DHQRmaSeie7IY2tydP6qWBViJDJIbObzCxMrWFxOt6BWuNSnL+arefARQ15pAhNe8e6eVKA1kDWgkq2IAQvkLh6FVMcWPLgRaBoclB2h0vZXCNzcL3jhTSaHmqeln4qec92GA6BSwZbhWYY4eaWV787RQYPVYxdTstUmwta4g7cgq5PCVOB7G8AgAJi9SeQpEYz0NyTVc7TkBjmLTuNKRkGVV4wOSk52ugRls6bhQolwHmpYi2M0DmGlKqvG3NVE6kdFKRwFNCi7Wq0SY0WvyukJjsM2FpRijmNeqiPd1N+SmNIhspySyMjszzpSAXdzlJoA3Sg4kvq/vUpMoADb21SKwICwBqkQBIRe26kw5WAnS9lU4+LokwSyxvOeQMGyk5uQ0oxjdxofFDidD1Usb/AEN5N6FV2cpBpNxAKre+iAFI0gc8NZl5lEZqPLzVZBLidSrYmE7WTz0SLa4E7VorRWuaPm4OhNKt9VpVDdQkxA7ut9EmycN6LInNDDVZuiiZCSQbv+S2nZ7F5sQzBTws7uaShMdDH6FbTtX2bjwmOw+M4Y18mFnj0lcd3DfRKXalstUpPLwci4kOyq+KIucBVrc8P7Hcd4lgxjIcFlwxJueZ7Y2ab6uIRxLh/wCxsHFIyfv3uNOcxvgGnI81K50TJPBPjHZ3GcKwcc+Nkw7S5rT3bZLcLF1S0RniFCwNFusRhuI8S4XhHz41khlLnNa4guaNrOlrDm4HDFJkfOHEDejqpckuBxhxlj2T3O6ALTX0wy/DD3leqMP9pXraGjGWxGkkz6JKiQQhCGNAlaZ2S/3upGJCEIAEIQgBbmkULRuUUgBpFNI7IASdkNOpS0TAt4A5qJAMEZQC7UqQY3u8xFk+EUU5HZZTpdNrXkVUXA0sgAtIeLNhOQNdO8Nyho2UntcYGvIOp3UQQwGwHE9UARYC52UAm+QVskhfh2tIdYOhNbKLXZRmrQ6Woknu2i+propYEdq19VfC1tvcSWtDSSTQKo26a9VkFhhwg8UZ7wX5gKWJEYARiQb0aMxpUyOcZS8fasq+Gbu8LKxosvoE9AqW5BZfmPQBQNsg7xNLgNtCUmuLGmRvSrSLzkLNtbTeS2AMNVdoYBC9rY35m2SPCeikAHMN7hQZbW9RdkK6KN0jZHWGhos/2UsTKmymNz2srxiiaU3FnzFrcxMgJBB2aFSMve2RZ6KdEmtaHmkDLoQ8td3eoaAT0VDrc4u3s2pseY7I1Jbl1U2MBwb5TdggBSxFAcC0eHY6q6NwjaSWg3oL5KkCyeSm/MXAVy0SYEc2VxAANitUPrJQAKDZdSQAL9ToEkBKRze7aNjzAWPoX0OSsddqoGiSRSBonrseSH1YIRmtgFDTpzSeKYCeakBgU+lXMeWqsbbx/wDaN1Q9wc+xp0tSUlyZGGcxrc7gbHu0lOfryddfvQxpDRruFF5z2bPqpE3yANMcL1UWO1sqRNQjqkHjugwAdbSYEHut1kKQFstR35KxlkFJsCAoeGlYSe6Dq0tQePrKBU55gYmRNaBW55lSGMlYIzWQoONpuIpU5taS2Wl7JknKBySOp9VMscIwa35LYYHgnEMZg3YqLD3ENA55Dcx6NvU/BTkMN6MSJ4Y2Rpa1zXNAsjb0WPI/xjXYJ4qObDEtc0gXvySweFn4hi2QRNtzqACmTxsqMGypxLnVrflqsvA8H4lxF7m4PBzTlmrsjCco813PD+wDcDxeuMzxDDCISF0brc4HkBXwXcftnA9n+ys0XA8I6DKBlcQA5/VR+cv4o2jTjH+bPOMD7PMfIzCz8RxWHwUMzwHtkeO8jZ/EW9Fv5eyfZjhsAbCMRxeWRpbHIXiOMaHUAa/muD45xnEYrHPlL5Xzudb3uddXyT7P8bxcXE48O8TyxzSNZlbqRZ2aDp8E4Rw8zZMnlfgijjXB8Zgsa5rMNJ3BIyvAsC/NV4bhmHlwjY3G5y4gkj3fNfZ/Hfk/4rj/AGV4fwwdqeE8E4rPF3sHDMQ0GSTSwHag36A0vmuLs2/sp2t4twTtdwmRmKwcvc5tXBj+VVuCKIPQrmVzGpJqBvO2lRSbNEGTHBYbCwYUviwry55Aaczv7LE4lxzHOdUzXNYBUTXj3R5WumbAe6nhbhXQsc4fVtr6roT99rHxvZ7CcdwNsxveYtsbnMcXj6yvjoNNt1UoJbMUpSONdx7ik+HjwPzmR0LTbWONgffssvi2IPEZ45NY2NaGiOyRYFE1e607sM/CTuZNcb2miD1Q18ksgZGHOcrUmlhGcopG6wne4bBuxLIw6IeESEgZTeqBxGYj6iKV7OTnPaCfvWqjeIWyQ4iRzAWm2gA2eS2eG4RxFuCieeD454kbna4RGiD0PNZPG2NJv2UhNFUhfVCL8Ps5XqjD/aV62hoxlsWqSe2qSokEIQgaBL4J7pVRUjEhCEACEIQAgmkOiaABCOaV60gA/wB7K2FmZ1tNOCq+Cm33TV3zpRPQEZDchIJJ5mkqOW+Xoig6QCidUOoOIBzdNFkAOcXMy2fIJBpzNvRuxTa3Mb0AA3KbmU1tWSeSTAk4ARNeH3qaFbBVuLixmZwIA0A5KTg1sbQM17EEKMdCSj0pITBga57QdBzKuxby6XQENDaA6qlzWBwBPIE3/JTEjXYprn1lGgClhlESMjMosl2rh0VbaF5tDyCm+5JnG9L3pQNNdenxUiIbnzUXG3EHkrWhur32W1y01VAaC7+iTLX7MpxIZbbyuGqQc8YVwzU0nUdSpzv7wtPdlrctAKiwRRG2ylkeyABz3uVaQ4VsAR1UGDwl1gV1RKfFQdYGm1JAxmrokUslsgZw0w5iS45qWL6qRytw7TlIs79VLDI2sDcxdvpSg5xzXqaUvEIvECGnUFQjbmlANm9gAkMlK0Mogg5henJRcGispOo/NSxAYHABziRodNihlta2QC6KkQTRuhtjxrosdxJAV8jmukBBL9NSqHVXQpFBTnPA2Cscc2JDcoaAKJVLXHJY2U2CntzCwTr6IYxOoWAfj1VTAS+jzWRiXNdKTG3K37IVQALhZAHVRkaLZRlFNJOmuiqF31TJBGlb7hRiylzrdSRKQb2LQQQ0HaxskT4yrWtzO8WvJS2D4KgDXJXuDGsAbd1ZKjGzNKGAbWVGZwaatLIYYmvDXk3qqXG7IoEqouL3iuazoOHYmd3hYQDpbtAobRqo54Fg8DicfiG4fCwvlleaDGiyVssT2O7R4Vr34jg+LYxh8T+70C9F4VPwfstwuGHg+HM+Olb9Zj3NsA7EN9NlyXGeOdqcZhnQtxswY8kmMHISed9fRJQlJZRq+yHDN3w/s/guEcCje/CsxHEHMD3vkAe2InYN866rrezHZ4Y3hcmLxs8mIn7y4zM2m7cwvG+EY/ihxzYxO9vdkF0bzlzAG9ua9bwvbeDhnDoppJZMRiJGGo6AjjrYgAeiUpJLtWzSnH8u6WjfH2e9nsc8HHYOOV43awENC4OTi/Y/gfFcbgOGYZseKY8sjkc0U07U3oV18PHsbxjsdiMa2Z0OZmUHkfPyXnuH9nubJxKR2dweAGONBztPeJ8yemyxUcvM2dE3x200drgeA4njeJbxTGvbDGI9AyTxEAafBbCbhWEf3JbDhA1gq5j75Om16lcp2f7P8VwLZI8ZJJ4naSROOni90B1aea3MDYyXloBnwjiG53/vCT0/spnVekx06S9o8w7X8GdwHtRiWPhDGyvzsyt8NELE4BxXDcG7T8N4m3C9+cLiGTuZ/HlcDX5Lv+J8GPEsK9k0uIm4k9xtr2aEn7Gu2+9rScO7K44d9hp+FSuaGhrJITWX+I67j0Wc5rHJDpS7srjB9b4rA+yb2me0DgftgHb84J+GZE5/DHOayTvIzmDd8wOpBAu180e3PtaO0Xtq4r2lwD34bBYl3chgoZ2xgNDjXMkX126LS8TwMuBfhMLwrByxFu76ouF7kCiFzmMwWOxMxwXEnulDC4RZCfq7Nmgd9fNctCioPuydNxXlOPbgxHScUx0cU8uLdirAZmLtWg8itZEOIYXGiSBro3RuOoFgefp/ddtw7gOKwnDcSIIyZYqEhyA6Ov8A/ZSm7NYzEQRnDRyta892GGK7Ohd4ro1XmuqVTHJyKm3wcNiYJJZ3Z5DiZifEYvECSrWYTEYSA4iTCuDSPC83Xp6r1HgXs04lxjEvdh8mDyEPdJJGCQBp4hsPgFmz9le1sPYrE4MtbDhQ8skfA2ny+KwKOmTS6FeYWUquRu19nmvGMDg+CYPhmNgx7MZxKYjEODGtdBE3k0hwtx62AN91jY7tHx/G412KxuOxT5XgGy4sAHINA0A6ALMfw/Hz4wPxeFe7EtaIohIDqR9oacgs/D9l554BLi+8bI7+Ma0l8iRPwv0aBCEL7A5C/D7OV6ow+zleto6MZbBIikfFBVEiQhCSGgSKfxQkMihCEAHJCEIAEIQgA5pHe00r1QAc1ZtAK0JOqgnbchzHXkploCDA5z8oBtDjqBqMvVSYCKfdC+ShIQXFw2JWTAbBoAa33UpGnPvetXaQ/db/AJKx5aAxoOYjc0pYEJWZAzxAki9OSeHvvxlcA7kVF7aF2ENsAHNSRLHLRmIbtzvmRzVd/ao1yU3NqHOQLcVBrRRs6AaKQED5EhScKAzAnnShZcK6KV1FqbJP3JMCDnlwI6nZIAXr0U4og+bK4gACyouovporX8lAxtebok9EnCn0Ug01ZJ30T3d1JQyXwNpytJoXtqo6EEk/qpFxDcpFdVGqGtX0UjHR00IJ0HmruIwjDS/Ng/MWAX6kXoqWkh7XEnQ2DtSliZDM585BbmJO5NqG+RorBzRgEk1tfJWYZ7YsS57259NNeaWQsqMZXHLmNG6VeTMQGuGuqGMk8EgP0JeCQpzRshaxjJc5y2SOR6KtznFoF6AUNE4G944+INyi/VQLaKwKjLjy6qbxF+zmuDiXl5sVsFD35CAaTke7umsNBrboJMpcFDSMlVralepJKiK3TZbnAbZjVlLJTJxtdI85WOdQvQbBDDQc3KNdbKtdcLnNjeSNi4aWOipiOagGm7OwtST9Ire6mloQLyUBupw4ebE4wQwML5HGg0Ls8D2HMeEixfFpMmcZmYVv7xw8zyWcppGsKcpHHYeF0jiMpceWizGYYR42CDFO7lsjgHOdplBOp+5dh8yxUHC24fhuFwmEFG3Tayl13vS1WN7H8ZxeKaIDNipHNDi5rbaOoJUpylzgp00nwa/ik/Cvnk+E4bggYWeATAlzpK53yWBgeCYviBeWNeGxttxDSa8vVep9mfZ1guFwfP8AjBE0obZjOrQfLqVvZeEvxwkbg7wmH0HgaGA/EKG3pHQqC2ziezHZHBcKhfxLjj8K0FtNw8ht/rvosPicvZ/C4qSTuWGCQnJEH5nEdfCSutxPZYYvFvbJCyR7qaZrtra2+KyOGezvCQ4xmLnxBsOsRRtFX115IjFR5kwcZSeIrg5vs9g8fxjA5MEe6jE7Wx95EQIwd7HRdDxnhHAOC8WwuJxnFs+ILTE6Puw8yk7U0bHzXYYrBxFow7BO1725QYhRutCSFpeHdkcMztI3iWOY6aWP3TK6hm5bJSqya3g2jRSess1GP4OOJsjfi+CFsOQxxPhLWSDnmdQVXBOxsvDZXPghmmzEODJnBwDRz0rfkvRS2PBYSfGzSCRoFNY3QM9EsJHNisKcXLL3TJW24MGprb8lko8ZNWlnByeJjkj4A7ARxmBr3OdOzu3OIHTwg38CngsP3HZ7CMie7ECN9sOIbly2d8vUcrXUM4Zg8Y58wYHucKLoxu3oSatSbhcPn75xjZDAS4QxWb9Ss0uS2v0YzODRQ8POLxE0r5Dr3szyefIdEoeDYd/GI8QyMOblJyg0DpuaWziw54hI+bEBxa4U2MuNN6KGLkdDHHwrCysZK91ODBWVqfas8Db45KpeG4A42RszRJiZGeIRg+BoFENKy+EcJ+bYdkWHjbhcK1h8I97ys+iyYcIzDzMc9+Z9ZC4lW42aNmGdD70knhpu+XzWUsI0S9mjn7N8PazE9w0xvmGr26E0didySjh3DuFYKCQviZlYO7a50YJLq116rZ4uTDYPDQObhw4Zcou73pKOI4ru5HRNEcbszIYtAD1PVKKS5Jf5M1j+FxSQ4bhsJjjaXd68BmYO1u3Xv+i3TOG8G77ujG0DuspkLbLR5DlzWEybF43tTJEHSxxCOmRNaNT6rbTTYLBxtwOFwfjleS4lxJeRpZJ6Ik1LgKaw3I10eGwcuGbiuGRMwOBieWnvBbpK0LjfPoFtWsjBbhcDgmuw4jzh5Hh152dyVg4h4fgw98LZQ11CIA0DsDXPdbQxlvDoRiZMzmt1YLAv0Czk1jCNYR9mkxHBeHsx7uKY1mHYWf5rqOS+QVLZuFwWzBcKjniJzCR7LLvyWH2nnhxMeHwbonNgkPj7u81rS4nsrxjHYgyw8e4jg4mgMZDG/RrQNOSyjyYTqPOEj57QhC+3PFZfh/tK9UwVblct46MXsR2StM7JJiBCEJIaBCEiaSYxIQn8EAJCEIAEIQgARWqEIAEiQGVz6po0KmWhMTXAeZ2UHE0VJx8IS0LhosmMtd4YWxD1NqDsoIA9TRUm011u1KUYa/EBpGhKTExuZQDc46k1sovA7suLtboN/qpSlpkysBoWNSovAEdjW9z/AEUZERcTkF6pMYXg1y1JRl+rJ5KzNkw2UEW7cDcBIaKPQ6k8lIUXNaXEC9Sp4eMPzvcDTW2COtqs+8SNVOQZJ9d4e7s8gSdVUbzdFIEm7OwUXaPUggZ75zXXL1VxyR4puUZhpvzVR0LToeasZI5ry4U5xFElJgS8PeOlyBwsgC1VYJBu+ZClVHKSKUQATqfRSLJKd5cQTuRsFW57XMDWtIDfPcpyHXxDloqb0AJUspFkQp5s1Y+9Qd79WrHltZmjQc1DK4tzltA9eaQIsIIgD9Mp2UY3GN1DSxSufNFPNGwxsgYAB4f5qlzSH02jvRKkMERpISeR5pSW4BxGp1WRhsJiMY9sULC58hpordd1wbsE6MNxPHZBE2AgiKrzjz+KzlPBpCk5HJ8P7McV4nB3uHwpbGBZkkOVtdbW8wXYmKGcu4ljYnMq2jD5i4n4gUPNd1jceJcJHheHsjaKru62HksvhfDMj2zyHKMu2yHwss6Iwi3hI8x4l2be4yQ8NE8rgbDKzaeo5ro+w3ZEMwc0/FsO0vkIDWP+wOa7+HDxwQkQttzjuDvqrMQ5kODzS6DQFoNa+qwk88I6I0IxeWc7FwjhXBnvxWCwTGTPOWN2WyOp1CDE+R9zPLiSdVmSvkxU+d2Yt2HNbLBYJjomukjBIPQq12wWXsGnN4WjUQ8DlxOL+cOYKB0zcl0GGwAEsbjlbG1vI0XlZDW6tNhoB1FJSMbI8Pc9xa0WA3f0WcqvdwaRpKJgmJ2O4s5r3+AA6gaBZXdxSObFFA5waadnJA9fNQwmRsRDWd2995gTr5LJDhE5oc8ZWjUXzWUqno0jBlGLZJcUWHYxkQ1pvXqspznYfhbnQAzTtGl8yq3ylsoAaCa68k8PLJ87kjcPqzZaf6KJTLUGURxY3EOfLPiJWUaytNcvJZ7cMzDsbnLyK101PxUmvjAy59Dv6qGImdNIWhtjUWTzpZupkahhEGskxcskk8WWEAsiYdQdFldyTgI4i/LkGuXRVwvb3YL3k5LryWRnEjKa8VdBKVT0VGJEy5Y443v1yglobmUcXJNHlihgzMd7xOgA9E3OijkFEZhVnqsDHYx8L6kLGsftZokkqPkQNNI2jgWQujbLkzAC2nYeqwcNhIJ+KS4gvNtIaCXHQgbrCbjYTKS6dpc0VkBvTqtnDLG9rnNcBmJ5a2p+XGcE8NmXi8RhYQ1k+IdGTYD62+KrE7X/AFIAjkDC5j6u+i1fFn/O4HRZiCBlt+lu3B9NFp8L2gY3g8OIxzg3EMtr2A3TgNvisHNsqU8P6NtLJLNxSPFvmtrGA6uBFmgQRyq10mGkd3EMpa3uydeVFeW8I4tiO0HEpZMOGB2FkPeD3czTzI9D+S6rG8RkiMcDcS3uZW27K/3CNL/knKfAqf7OqkIhHziB4Ej/AAts0cv+ytTAcdNio5pXxQsYS2jqaOv81z2L7VxOkbHFI95ewQtlBujZ1/JbDBtdHwZ3znG3LG4SulojKAaolNTSWR93c8HTuY8v7xryI2t0cNOfVZEmaaEOY9xc1t2DZ8za5XFdoYZ8BFDhJInOkdbAZC2jzGYXRWTgeOum4qzh03esdlLHB50sDWuqzUi854RspG4XGvjnw0gc+6dbgb/VbPujlb3cLqrqV59hoMVg+175MM5keDkec5dIG0eQr1XQHtTw5pyO4kGvbo4N8VHnqLU9/IQ54aPldA3QmF94fPF8H2tFcqYPtK5bR0ZMW4QRSOSLTELkhCEkNAirQkTSGMKRSLHVGiQCCEItAAN0IQgAQhCABBFRh3UoUXKZaAQNuF196bmkSEEt9QVEJ0CTf5LJgTAb3YcQbJ6oi0fnNADzSN5Qa0ApNhGR13daKWJgG95L4XUBrZKHOIjER0F5kQgOktwsAaqDzmeS299PRQxCFhtbjdAdTRoNTvzVgdUBZu5x1sclTfgrogETzNbCwMzB2uY3puhmWnEuo1sURszROdY05JaMBJaTyCTGQYWh5vYj4pOLTJmoAJj3PNQOrhqoAdtqvNMmn+EJDTVA1JLrv1SYmXua1sAe2iDoSeqpabFDfoFJxHdaOp17JWWgZNCoBCmkElb6ClVXMemqkQQ/K4a81a59xENYBehpJsoVteWRBpu9aN36KMmYvrx+E0B0WVwjCulxokLQIh7znDQenVdH3WFwGFbDDEC4uzd69gJcPTks8tvCRoqeVlnIxQySEtaCS40edLpIuyD3NbNisVFhIaBuU+I/BXsxb/2h84cQG1QbHGG/FWy4tkuZ8gdKdrfRUVIVPaJVSKkopZN1w4dmOEuimwkEuImiGXO42L9Ffie0wxjwx2Dc4OdkvOBeq5WDikcGIdBPGXxg+FgBFH1BW4wuP4LE5kj8JM+jmy0dD11K5uUsrZ60EuE9GzgxmNOMibhcJFGBQIL73W+mbxwPZ3OIgeytRIa1+C08HHOFvxDI48M4Pc4ZTkAoX6ro/nLQKEZJrmQsk5y/kzaahH+CKWv4+PdkwzCNhZI/ktRiuMSxzyRcQnijLHBvhdZ+C3zcSwVcR+9eW9rJn/tqQtGVve3vaapd3CZlOeMcHUM4l2jJLsFiY3YW/AHtBJ/us/D8c4zNiHMwmMh7xld4x0eUfBedcL41jYGtcyd2p1BOn3Lp8HxjCyzTyYkd1M9tNN2LSq05qJdKUW+DpcRxPizLmkxLmTAX4AHNA9KWTBxPtBkHesYGtPv0CCPTktFieItwgikIE7XMq8wseqrPan6wFsUgA3p265YvO2dPw1Jcxjk6SHEcZdi3YmKWN8btDWhC0HHcTjmcaeG4hzfCLGYjUrHxXanLhJXRQyMJYcpz7LVYTiWI4hgIMZipc8j26kc9a/osakmtMpVK1tyqeWZQxPEfC442QuF/5hUMTxfinD8JJi2Y6QuYBqXk6oExDbsm75bLA47KXdm8SK1oaqKU3KSTFU6hcSg4ujjJsuF9v8c6Rwxc5lY4AlpFH4FdRhu1mJxGHaIMTBHITla2RupXjmClIlIzUQ0brdYbFOY5rmuo3uNF6rs4zXDPMVzOm0mewQY/iwjecQ2JjqvMzUFcZjePcQZxKYDFTNGbZkhAWPhO1eIw0ZZO8SsOh01C1WJ4hE7FyP7ogOde4XlV6U4S5PpOlTjNtm2PHuIOOuLxB9ZCsTinazH8Pgin70uMj+7zTHMD8FrxjY6ruvzWj7UTCWLh4azKPnA1tZRTbwzvv1FUJYwn+z0AcQmLjIZHB7mi8riFP9pYrNYxElchnK1vzeX3RPyGnRLuJR4TOfzXPKpL0fm07Km5P/qcP/TLeLdscdwXuHNla8zyZHNkNlw57rdFspzVkbmcXOA2J0XmnbaKSPEcIc52e5jpfOwuu/xQcR85quWYp1FJxTR6LsqVSlGE6+Me+TexRSwyufEWML9HZNLWv4p2jl4JPhcK6CJzZiQS5xu9AB95Cws2K+zif/3K5PtgZTxrhBlcXkPFAOu/G1TCMm8MdvY06cs06/c/0d8+ScDuu8DWg6AOsAq39oY75uYHYqQxu95ubQrXuxMeZ1hw1I9PJQGKirdw81g3Lk8OfT+sdz/Bmc7j8XCp8PFjMLBPC4ulJc6nWK2K67h3aPhPHIHYnD4WNmJgosY9/dn1teTdpcQwz4ER5gQH2Sbvb7lTw/HyMka9shjcNAea9W3tfkp5ye9b3Fa3pxhWXPs9ygxuGdJLBNw2SJ0mrnF7qvqHKZdhmNa3BMwUTKFta3N4uetrgOGdusThx3WMPfMaNC46j4rdYPttwN+Fa53Eo8Kf/wCNzST6rx+oUq9PHae1RuqbXceGgWnSKpC/UT5guw/2lcqcP9pXLWOjJirRFeaLRvyTYhIRyQkhoEFCRSwMKHVHPco0ReiAEhCEACKRSEACEIQAKLt1Lkouq6Uy0BEaclItpgd+SAPPRK9fJZMAJ8FVSlY7oAFRdQ2JTqmA66jopEwjDjmI2G6js70VsNlpFgDcqLXVmJaCa5qWIg5wvTb+qgTpoCCpcgQNwo6urdIaJx3lGXVRkOmUfcp3ljaQK9FE6vzfekxexHKI2taNeaqcbOim40a5lIAOla0aVqbUMZblAwgvVx3VbPAA/QnzU3uDgA3S9wpTta1wa0UABfmpApBLpCSmQ1xA1vnajqLrmnrmB/2UMAunlbXh+AY8xz4qLMzdsZ0z+vknwvBNxGIM0sYLTTWN6utdC2AgukGv2XWKqllJr2b0qeXkmIYzMxsGHY1rBTaGgCxMZiWSS+BujTV9StlD3Yw0bmZnyPvLlI2/ipYHEYmwTtYD7wzEltG/NcdWaUsI9ezhmWJGGZa1LQoyTB+HcMoHmi//AJBVYqXusI53gOwWffJ8ZPSqwgotpIwC0/tKib1G5W5BaI3XRPkVn4fsLjZRHijxCL6xuejGdFtcB2TxWFxYlkxGGmYL8LmHXRXFYWDyG3Jms4a5juK4VpLScw0JtejBgP8Als+4LkJ448BxfC4d2HiL3yjxM0/ousBcDq0/FyS2NPJcGt/gYF49xzCS8T7c43CMmbAyNxd1tevNdZ1jB+K8P7Xhze1+JmotqRwOU0tYRzk57hvKwzOZ2YdGABjmf+P6q7/h+Runz9pry/VcaOJt2yzf+ameJAD3Z/8AzUSpye2NfKmszOi4Vxh8U0+FfH3+WSmWaqvVbCXjBhdUnDZGnzI1XL8K4bjOJCefChjAX1T30dvitvHwbjbY8j3QSM/hdKT/AEXLUowWzpXUqkH2/IkZmI40yfATRDBOGZhFkjRZXAH12YwWjQQw7eq0uL4HjY8M+VrR4WlzmiS9h6LJ4Rhce/s/hHQxsLC3w3JXM+SwnShj8Tmu6ju4/wDJWSSOi74AVS1/aOWuymKNDUAXeo1VQwfE7vuWf/lP9lg8bgx8XA8QZsOCwkC2yXWqzpQSkjhpWlKMu6Nxn65NTh8rWsflFmMWTz3WY2estBaiGRwc5pJIAFeSymSUQDfwXuQwdFR5M6aYuhcBQJOi3jsM1lNIjByi6F8lyznWNQaXQftmNlMGCkAA6g3p6rgvoSljsR7nRa1Om5fI8GWYw4ZT3Qs/whc72qhyQcPkaxpHf1Y05Lb/ALcgvXCydeX91pe0uNZjBw9seHe2sRzqjp6rzqdGspJyjwexeXlu6TUHlnTh0pAAJHQA+SA6UbuOnMkroo2uELP/AEg6NFkhmunqpBocdeEHyADP7rJ0kfP+etI8Ojn/AOHmfa9z34nhQJOkh16mwukcJA4jObvbNstZ7QmAcc4MP2eYT3mopvi1b5r0JrcF3IvgkoNa2xp/qiosRSRflbaKU50+H6OQJlA0cf8AyXOdoGmTtFwhsofIe9AHi0PjF/kvUh+zw6v2HNXlG3n8V5727dB/xZwN0HDZsOBJZDmgF/iGwtKlnuFPqVtXi6dGGJej0ItwJcc2BjAB18Db+9Sa3hhDv8BFoaAyBYH7cwRFfs3F3zuNv91L9t4AGhwzFDbXu2/3WHwrGz5qVLqmXiMjmO2rMNHxPAdxAWHI8uI0B1C0EUgaDWmtrZdt+J4Wfi2DeIpMP9W8ESgNvUbarQxzRlttlH3r2rNKNPZ3/HXlBKonk2UuJyteRd1V3utL37hFGM1eHYm+ZWbJIxzCLbt1WrkivL4Dt/UrSuoySRrRpTX80bFGqEL6c4i6D7SuVEGuZXrWOjJi+5G3RHxRXmmISDsjkhJDQJc00c02MXNB2TS/3spASYqkkIAEIR8EACEIQAKDip/BReLcNCploBsBLCRp/VDK1JKCS3w8+iWuQD71kxIi+yaNK0/VtaKFgVsq9C8E8k3FxBJN3zUsZY1jDhb1Lr102VbqHuqWciHugNzmPmq6OY3ySZIE0FWPzUj72icgoggqRocrcmVlgmtfJBNuBDQOWigDb7OqmfBuFIMjIMrybB8wlCM8lnbmnIQYgACFGLSNzswFDbqpBDcM0mVoUS4B2nNTZpJoVGQgm2ih0UgiDuo6qV+I3oFCxlrnalu3mkx+zsOHRMbMyBj2DIwNDtwDVn+a3pwcYkFTZX1zFAnquU4XLG7DiTKSAAyQDTXYH0W7e5sZa+J8szgyg1wOX71hUR3UmY3EHl2KDGtgLmEN8B5D4qjHYhxkjc85jlrVV4t/e909kMcTL1Dbsm9dVY8tIDHkaDQ0uacUjrp3MKL7pvCMMYkHk37lh8UcJeG5QGavaNvNblsDDVUfgtfxjDA8JtlZg9uwrms47OiXU7eou2Mj1PCQ5MDCwtZ4Y2g0PJXtZpeVqxsK8/MobDf3befkFkZ75NWmTnyjj+O5me0DhrAG0542K7Nxykg0D6rh+MBz/aXw1xDQAfNdwW3vRTa/RMSbWuNEf/6Xiva4H/iPEhwH7x3Ne1NaSNKpeM9q6PaGdpy/vHbLalvBzXT0zjgARsFKRtNuh9y28WGi7prjG1Wuw8L/ALAW/wAOUc7ukno3XYaIfsrEExg/W7n0XWBsQB+qb5eS5ngDRFw6QRty3JuD5LbCR9XmK8S44m0zmq29xVl3QhwW8Ta0cGxbjHR7l2oPktdwBrv+GcFTK+r+8WVZxGT/ANGxRcXEd06vuWt4PNIzs9gmsto7oHU77rnymjpodGrXMHTmu034zF3hr71q+01M7NYgvadctEHRS+cTAXnN/Ba7tDiHu7NYi8x90gk6IppKaNof01O3fyOS4ONL8Y6Uuw5GUgBXxu4n3ZLqLuQUcM5ghYMhtZjXt6O+5eq5NHrUrWE1lmI6TicT2vmLRHmAJFc16XDwOCWJkgwbSXNsEv309V51jXxnCD3s3eMqhXML0aPE45sLGtkkDQ0BoJHRebe1JpJxZ6lha01JppDHZ6I5rwDLGnv/AKrm+1+AGCPC2sgdG12J5GwV04xOO1p7tuoXLds5sS9/DBIX6T2NAuOlWqSmlKTOy+tqfwy7IrJ6OGT92wgOFAbnVWBs+Uk3965Y8S4nloTu22Nf2TbxTihGVuIca30ark0fFv8Apu5k8prk0ntCD28e4IJTJ+9v827LtHP4o1jj3U3/AMbAK897VTz4rtJwT51I9wE1aDX3m7UvV5cXhmx0yV+etnOcFFVJpcnoU61HpsVSuopv/RqTieJtItklaZvCCuF7azzTdr+BCQSAiTQEeY2C9QjkwTmHvsS4ejnarzn2gmBvbPgL8PNKRnqySftBZ0otS2dVHqVlXqKFGmlL/RviHFxpj/e3KC3/AOm8lO3OdYbIR5g2i3kmmS6eRXGfdQhwuTge3ni4vwtkzngFshNjbVa6EwNAAett24DZ+03CWPdLkyPF1WlhEHB+GOGskw+J/svatmvjWT4bqt/StLiUZmE12HI/eBYWLlrEkNmNADkujbwThJBzTSj4/otNj8MyLHvjhneWNoAloW2f0ef5mhcfjFaMpCEL608ouw/2lcdlTBzVy1joyYcktL0TS1CYhIQhJACEITZQrRp/so57ItSAadCjQo+9HwQAk/vRSSABCBunyQAaqO7qJoeaeii4qZaADRfoaCYAEebN8EtaCRzAkUfRZMCIU6uPNfOlE+5tR9VPMKbTaDfPdSwE9wzg7UFEu0Ou5TJLjZ6pSEOfpoEiSIF2Sl5UpgUzMdL21UK1J0+9SBKNrTM0Gg29Sm9wdJYGl6KIvl/NSa0HM8nUbBSNkHgXlJ1UTWWuW6bbfiNdrspuoucRz0pSA4mFzgAQXHWrVb9HnXQFWxvdExzm0MwpVO0bupARBpxHI9EaUAHK3vj827oAAHVx6qpoBabSYzLw2J+bPzs1cTtehHRbvA41rpg57Gta9xawk2fQ9FzINN0uysrCY5+Cxkc7Gh2U2WuOhUN+0XCTT5O6OBw/zN7wwFmpIYbIctM6bwZJGgkGtOqzMJjpMZK3FYMZ4yPrYg76xp8xzaqsbJ3uIEji2y2qaKXHUi28ne5UVH/m0YzZ8pFF3oVj8SxAm4eGloBsc/JXtLL0e2/VY/EAPmWYODvEBV6pRTyZdthjNPZofnOKZoMVLo6vfP8AdZMeMxWW/nM2++c/3WNWed1A0TdUsiNuTQ1RPNdUY5H38I2XZ5z5+2WDc57pKd9txK9fABHuN+9eU9nIw3tfgw2iCdV6r3RNbLnqRwzopNNEgG/wAehXjfakNdx6QMaATI+9d17GY3cqI9V4x2iGTtFLYAp79AVdBcnPd6Rro2/VgEn0U6IYTVIYMzGEXRNq0MsEHqvRiuDy5vDIOnnihaIpHtGcZspUzisUHuy4iWvUqE7agDKNucAKV7YA0gXZrVcvZFzeUdnzVFTWJFEk+LewxunkLXCiCbC6jh/B4pOEYZzIJcvdjZ5H9dlo3RigL08l1OAxBi4ZAwSOGVg0K4L+moxWDOcripH8G2/or/YhH+TN/wDkP91pu1fDRhezE0hEzXZwAC8kFdO3Gvv9/XPVaHtlic/ZaZvfFw7xtAbLzqK/NE0qd5Ga7+7ByHD8FhcRhWvlc/MSb8RCz2cLwOb97LvtnWowcmMjgHde7ryWa3E8T2A89l6jpSb4Z3t0881GhcVwOFw+DjfHNLmMjRRdfNdm1gEbT88m90bu8lwmOlxkkETMRYb3jeXmu4Ebi0Zc5bQ16rzrym8JNn0fRO192Hn/AGWZR/7yb/yH9lzvaoHvuGj5zI/NNseWy6AwvOlOWg7SMLMbwq3GjPzHouKlHE0ep1N4t5uK5OtPBQWV8+xJsa+7/ZNnBBGKbj8SPVjTenos3vM3+ca3Us4P+efvUuoj8yl1TqKbxk4Dtdhn4bj/AAhoxcsly6F7R4dW9AF2LxOMrf2nKbu/A3T8lzHbENd2n4A0zUO9q98viaummia17vrtiTtVorPMUfa9DtaV9S77uHc/ss+vrL+0nkeTG/2XHdqzIe1vA4/neepPC4tHh8Q8l1rYmC/rhYdoAuT7SRgdteBN75gzSbnl4lnRX5ZPXuOl2VvFTpU0pHThuM1rHuNf/TH9kEYstcDj3eIUT3YW2Zg2nNeJoEdFL5i3JQxQ+5czzrB6iu7fH8l/9PPe1MBHFOHvfOJHwxOynIBz5rCjxuIHu5a60t52tiyccw0QkbJcR5VWq0LIi1zgdK572vpun0lUpJtH5t19wncya5RYOM4xhI+roc6WO2aTG3iZHDM460NFXiIXU4ga1dKWBD24FgyD4la1aUYM5LOjB5aRkIQhfQiLYOavVMG5Vy1joyYJa800gPNMQkJlJJACEITKFr1SopnfdFeakA12RrzTISqkAGiSd+qNEAFeaKFI+KOXVACG6Tt1JRd1Uy0JivxWlRJ31ReuiVeSyYw0OqLOWkjtSN6AI+9ICwtDQASeqgBmfTQd1MnxEX+ag0kPsGlLJE/3iADV7FLdwAFIJ8Z6pVrd/mpGSkGXTXz0TAHdhzryjoeai43qN/VIEmmkqRoTMmfM4GvIqJ0kpSYCZKP3pPZT9wdd+qTExu0NHqoOsEgjVSBJJO1IBLnZnGypYiJbVWpluWHX3jrXkouNyWnmdlIB+CRRUDrd/cmHZpPXmj7NDknAwOmbZoXqSoaHszuHcQxXCse3F4U25u97FbccU4dxWcHGvOFyvs5SBmzblc45x752U0D06KDWm3O5DUpFqb09HSYns40YqV2A4hHOMoe1odqQdtlrpcFj8JKXS4R5A3IJIWujmkhmE8UhbI2qcDqKWbBx3iUeKEj8Q6RoOoJ0ItLONo0jKOlwQZkcHW4tJN0p5RYp5I89V6I6Ds7xHDwy9xh+9LA+SNrgDqq3djuESOzRmRrS3NYOnotI1Y4IlRnvJyvZZoPaXD+J1h1ixXIr1IsfrTvzXEN7LxRzQys4i+MvNeHXL8VfJ2ZxbpXPPHcU0gnQO5cjusasFJ5ydFGbisHYhkmTRw2Xj/aKJ54xI4lur36hdq/spj4+HmT/AIixNgXlzG/5rDPYzEvwTcXLxISkgnK9l1fn1WcEovYVu6ppHGYeLwsBHKlbG1zswynQ0tu/spjooDiWYq4Bu4t2KqZwWeUtdFjG1qDQ/NejDLXB5VSOHya2ePMY+oeNCsoRkuJ2pZJ4ROyExSSRveDYcLtVM4XjxMAMUwADW+azjSl3OWDSVWCio5IOjOUEGwR0W9hkwDMHE2QnP3YBtaY8OxxnkZ3zQALFHRXOhxDnhjLfQAsHfRcfULecorCO3pjhUlJOp2m3EvDy3R/LqVpe1xwsvZiRsLiXZ26Dbmn3WJDjGWO22zBVY3BYrF8NfAxpJJDqJFUCvOp2tSM08HqVqdKEHJV8/wDs5/hxg+ZsBc4OrVbJgw5I8TrRD2fxcQBHdtJHul2oUncPxsW4jJ3BB5L0HZzfJ4M3bT/lJmDxURfNoQ1x1mZ/NeoxcO4IYYy/GOzECyX1/RebHCvnlZHJVBwJ1rZd4w4AwNdJjmB9a+ILjuKE4cduSpXs7eKVtLg2R4bwDKP8Y4knlIP7LiO3mGwWExnBhg5nPubUOINbeS6UScIp18TjAFf5jVy/apmHn4hwsYbExyNjlt4DgcosarkUZ55gdNj1S5q1Yxqy4NycS5o01NdEDEOvU/ClScW0vcGPjcBzBCBO5wLgWkG9QuKVOp/4n6FD+2wuUcv2pcR2m4G98rLdJqDpXjC7GSYyPc7OwX06LlOP4aXE9puE4hrmBjHAF1ih4huuqOPBFZ4yOodpv6p1oTUVwY2k6fyVO2XBISgTayNJ3/L1XJdpT3nbjgZuMePavPmurGNBGYFlHZcxx3Dz4jtVwjGNa0xtdmceQF81FKE+5/iPqdSDo4yn/wCzsxjpBuxu/wB6l8+DMufKL2AN1qsR3EKeQHitQKd+aceKLXuHeA53Zic2wUOFTOj5l9Ojz/wf/o53tXN3/G8KaZ4YHAZTZOvNahkeVpBsarado3GXi0M9tymMixVb9VrmSjIKcw3yzBfTdNXbSXceB1JNVO1Rx9CMYtxo6iljwNDcO0V+SzHPdG0Oc5l71mvRSMPdtaGvsFtgq7iHdLKJtKjgnkw0IQvZNC6Dcq5UwblXLWOjJglYTUfNMQXaEISQAhCEx5CtUIQkxgarVLSkztslrW1JAGnkhLX/AGU9atABSP8AeyVlP1QAaqDlKh1USNSploTI+oQRpYCdc+QSWTGIAlyG+9sd0XQKcZaJLIsdEgG6gNL9Em0NXJuIJNDdI76qSSO7zQ1Scbfy9EykHEOFcvJSNDcDWbbySZlDS5zteib3OLvXXYKtxGagpKRIGgdN068HxQa7oNN5uaD7umwCTIIOOm33JR6A2aAUxqzVRAJBIUDAizaAaJ1USSSNU3UTSGNCPu3SI2t7pxdYPIdUAkt1QBWmtKRrgTTrevRBNDKDofzUmAGM+RVbiM2g2Uh7LDlGHY2gHGySFWHUCDeqe9C0n2AL3SYybJHxtMrZCHHQG9gF3nZftdBLAzBcVnZAY25WyO2ePPzXADKGEOuzsqiMpvzUOJpCq4nrsbeF4mR8/D8THMxz+UlajyWWMZhX4eZt08vEZLtKf5Lx+CeWGnseWhrg8Adeq3+G7SiSaP8AaLHEBwcXx0DfUpf7NlVR6tmL5onuLQ7Kc7Drf9ldM0PwrwXMygXlbzXHcM41h+KQY2OTENc5xBaY5MpDNr5equ4f2s4dg8O/vpHFjXdy11CpCOe6ya5OmMkzbOxffxuxOf8Aw0YyiFreuhWBguGB8M000jYgXF8eU6nypZWEn4XxWBkvDpg8tBc+NjqvnRVuLxUUM0WJjjBmcAxzABdeXmumnXwsROapQUnlmpxODeMsj2yhjtKOgWDjIzHEe7DsuwB3XZ6SYWUzuZne0ERu+xosabhLTCyWEiRpHiFc/JdFK8WcSOStYtrMDkmBjW04vcQBQrl6q3uI3sDmPDSdDTqJWVPh3YXFFjnO7t40sbeSohjcw0S1zQb1q13RfdymeY6covDKzhXmEsGZrm7Wdx6p962Nwj7gOZzOxCywI3sDmyUXH7lR4WYh0HilB951aIyS4taMKNwxOPLTG6O/dI5tCtxHDiYMrWP7zNbSBsFnxxRlrXMYLqtDqArGNzyAwyvDR7weNEdwvjyuTmxgXxOJewZweanHhy6Y2ymka0aC3OIwUD5e9ZKTbc2ZjfOqSEALwO6cQd7FCuqfDRg6ckzQjA5oXN+bNcL0JAJJ9Viv4Q/ETlzmhuUkURS6TECNsBdHGTlJNAafBa9s2Pxs2ZzBlB90BS4RfGBfJOGmazDcKmhDz3JINAEUVsP2W7uXCFzXNcOux6ea2DIZ8Lh7Lg0ONhvP+SxZMbiyXvytDXODQ5woDXYUj4oLSG61R7bNVj+HyHBljYgXnYGqVeC4MMJwcSTtc+V5stHJb7ExSRSRTSNYTIaBy3QWWZHHDAxtaS2qbVgKP7enJ92AVxVhFpM5qDhc2IjiyGWOOO/Fy+Nqk8JxEWBMc7i+Nvuub4tL8tl0D2GTEAyh7AehsK5uGhbmbA55NHVvi1OlVyCfwQ/Qv7yq88nD4iKVsYyB4LRlFnWlGDhvEnYTxTFpJzVrYHqumfhRBL3b67y9zdBbBmGjbHLG4l8gbuNWhZf2cG8m/k6sVwzisRgXNwTHSvcbIAPMKOG4LNiy5md0Zj1D+oXSvwUMzmtxJLSPER5dVl/VfM3ExZYW+HfXyTVqn9Ih9Qnv2c1gOECWOSKWWR84NNe66+CxpcNLhpDFKZXvG5sroInPidETTNCdQTQtZ7+D4eSV0p7zxnNr5qnbqSxEULuSk3JnEoQhUe8XQblXKmD7SuWsdGTBLyTOyXwTEIoQhIB0khCEAIQjmhlAlqmdktOSQBSaQBtNAC5p0itUuaAD/eyifeKkN9lB3vFTNcAFmiEhRsXskTQTumZQFiBBMAg3W+yWnwUrBNAIAemUG9eiWtgjdABugphvgL3aAaeqkkpcfHulvr/RBFm/6I+yNPyUlB5/0UXUSP7J0a6/BRcSTspGibvev+iHXVc0abIZuLCTJYzXcga3z0UNQK1U3UTeyrafEdVAIXIqA39VZIKG+6rYdeSTKWiZ0NI23QdZApH3SSkID4Ggg6HWgqjpqmTYrojmL2UjQMFvs7eai4l0lEqYoAqHuuNlJiIudTwFKg5oFaqAGeQgdNVNmhJPokUL3W1zCmQ3u21RNaqFAnakXQ1U4Arsh2hOqi4E6qTmkAOS0LaSwaJk4MTiMLK2XDyvie3ZzDS7Ph/bDBu4efn2GlGMAymaIDLe1nzXDGw6rUhQI01u1MoplxqOJ6OO1I4dww4nNJxHwNFxisun2jyK1/8Ax8/DRh7WTYih7hGXK67q9b+5clFjcVh45WwTOY2UZXgfaHmsnB4jhw4dPHjcOXzkERua3w69VHakaKu2dZj/AGhcPx2AaJcDI3ECry1RKi7imGjjGJgeySMgF3Mt9V5+/DnIX20AaV+ihhp58PKO6ndGCaOlj7l1W9d0+DluKKrcnpkfGMEGxsMrJM+uUAaDe0sLxeKdzz3fdU6mae8Oq4ebiPCnYcf4N8eIaNXxPytcetJjiHd4aOWi/wDgDX2QfOl2xuIvZxu2kkdkztDFh2uk0jfmIsi2kc9VusNxCLFRifDTtki3JGt+VLg8JxgYoPgmwcMrXN1jr3fNZxmdwUGfh00YioZ25rNaaHTqq786M+3t4eztYnYfvBJG4NeDqMtXaboch72JriCSXG7C4H9v4yW3ShxYTYcDdfFbOHjE2GnjlqbERnpR/lSaaeiG3HaOqeWFwBgdWXxNFVfkgYFkI7/C5W2NWndc3i+1bY5GTnD5mE0Axvi9K8lhR9s2xufGQ9jnHwiVNzx7Eqeee07J7i1ueSEVVEB138FjsbhcZhaDCxjXe4Qd+oXNDtmMxbjcOHDdpaNlqcb2nfjcax9ywsjHhyHLrfNS6iQ3Qb5wdviIxHA2GR+eESA5makeXks3D8Nw8DX4rC5/HVg9AtPw3jnD3sDO/jBc2pWTWLPksx3aDCw4lsEJaWMvws1qhqbVZzoyjBLOUZkWFdMY2yTRtppdVWXa9eSnJhTDG2PDuaCTqCP6rFHEMNjyY4nMzkiywFpI9P67LIa+DuWF2IcxsZIBynQ+afcxKMdYNZj8FMxxcS5uvQu19Vc9pJiih1Y6yZKJ06Gh1Wbi5pW4QYiPGRmInTM2xfmsHCYpk0TvmssXziP3msbrXStf6KlJmDgk+DFnwz5MW0QvYSXZSTpty1WJxN8mGxjMG0C3O8RNFbaDHwYriRwbJPrWm3sJy6LHl4Pg8TiniHESd+HWQ4ist7DRNyZHxJmNh4S7w4sQkkbQa0OQK27MJNKwObbWjQAa0Fjt4Zg8Ji2OjjdDpTWmTxOPM8lbJOWvyd93WXTLX81UZNITprPJ5ohCFkfSl0GmZXKmDXMrlrHRkwOyXNPVHqmIXwSQhDAEIQkhoEeaEIYxa9EX5BNFJACEIQAKJ3TvVGvkgAA0UXbqag/dKegK3bodsmfdS3CxYA0CtUDQ6obvSR3SAlqNUE6UbrogGyk4A2FLJFEM0hBFaalIucTV6DlSiDWg6I13NUpKEeYAS3eLUhqbUSPEpH6Jkc03aFRAt1AqTa7yjqEmQxuBayzvyVIOtc1dN7uwKpbWYkgKBxCU8rUBQH9kyCRaBqdAkyideG+iCRk21KZNDVRdoeqRLINBJI5pna99FJpyNcNNVHMMuUKRsV6jqiUW0a6oIIcLpPKX5iKpoSY/ZSxxz7+qsd7t9VWwVIVI3euyRTJN1cL2SlNnfQJsPiOii4WQ0dUmIJPcFHQKpvvBWygA6bKvlySLWhSDxXspAOLc1oe22XoiM6AHRSwk+CINuDXcyrJAMzsoAvpoqyLku9FY7fQhIhkaoWTusd4s6K9xttBUUSeSRccrkr7oE0aWTgnMwvEoppmZ4g4ZxW4UCLIGicgvakJ4eSnJvg7c9nTPhxj+DzxzxE1bRWvQ+a5nixxeHkkgbh3gPOZ3h5jf4KnA8Rx2Aew4XFSxNa8PyNccpry26roMZ2yhx0/+L4S3KRTjG6nbLqjXUl2y4OZ0u2XcuTjMPiTFOcxdTt91v8MS/C97hnSBjj4zrXUKiLh/COKYl3zJ0uHkvMYpDenkea6XhOCweELnd3G4AFr4nHQ9HC+a1oQln6JuqsWtcnN8Rw+LnmhMbiymkklxABCx8TKPnMWKeW5w0Nc1wu6XojJMHi8H3ckLJoclZu6aHgHnQ5rz7j3CGYTiTYMHO6WJ7Q9oeMrm3yITrRceUFvNS4bKsT3Ij74Ppjm1lVuFex+GL5GB7NC4HU16qk8CxTo3d+9kTmttsZdeZa+eTGMYI5IywAUA3/eqw7pR/KSN1GM12xkbOfG95issTMsWWmsOtq/BmRkQJ8UbSHZSdviubEsjbAcVscJiXd2I3TlunmKSp18yyx1LfC4NxHimslMsDnRyN8e2uu/NVN7SY7DzGQzua46AFthw81p8TjppMS4vBd9kG+Sx2RTTAuL8tDmnK4eoihax/wC86GbtdjsVB8zc76pwpzQ1PD8WlggbM+RzJozla9pOYj15rS4SCaIGVsYc4a1V5grMVO52ED2xSZS685FD0SVWWMsUqFPUUbLD9ocRg+Ot4jis0uY3q7Wl2Te33B5j3guIuGVxLKIHwXlTnvlfeU9KpNmHlcCbqt7UwupxfBVWxpyXJ2fFu1GCxEuTBtcABYcRXotNiOO8UfKC/GOuh9pYBwko4a2cyNOR1Zf15rCdMXOsjXzVTuZ55ClZ0sYR1CEIXpgXQfaVypg+0rlojJh8Uq13TOyQ+CYgKSDuhDAEIQkhoEIQgYIQhNgCEISAXxT+KR2TTAFW/dWKt/vLOYET7iQGiHFO9Fkx+gbQKid1JujdhZUTodQVLJGLDbKQN2mT4MoJIS2Hmkx4IEeJImlIeJyibtSPAx7qWmbZMHl/VFW+t1IaBuhJpPlSRsEhSaBrfwUslg6nMBAqlQdGq12jALN8+ipIseSkcRsNxnVABBHmpNFMoDVDTpdaJMbHJpSiNTpsm/xN8kMAGpSEI8yVFraKbjTvVPaMlSG0KQ6hQBNVtaLsWkHEnXZBSQEalJxogkqVhzxSjKKOyTGtk2OaGuLmkuOx6JNomxqUmUI/NNgIGg3UsRF48VE6qDq1TJuUAkeqb22dgkUuCVZogDyCg002uandRAc1VqTyUiRNlXqnM4E6aACk48ocS5QdtfVJi9lQNgi1FlFxAQ4nN/PVNugspGr0WZTmBQ+wTvXmVIEcv5qFn/ZSZkRaHDmPgUzvXJWVlZqDZ1olJmr+Veqljy/RAtMbxJC7I8agjdZcfH8VGf8AEhz9KBadz1KxpT4h/dQyh5rSt1pCrKGgcYzX5I6NvGoZMCB34jeQGgtOvxKwMXisJBxB2L7x0zj4G27NXUlaGRgz0NuQVThrst3dykuUTTtIJ8M6xnH+HzSS/O2klzQCdCdP5LW4vEYCZ7GQTEtGwI2WiANXp8ErN3f5pO5b4ZpGzjF5TNs6CFuDJMbWyA5mu6hQYYmh0cjLzUbHJYTMQ4sLZCSPVb6HstxGbADGR4mIxOGYuj8dDoa5+SUZKT4Q5LsX5M1DvmmHc4EZjegtSwz2TPa3NkN7dVk4/s+7CYb518+jmBFgNaQSfitO0uDQ42L2USbpvlFx7akfxZ1Xc5HxSg+AGtVVj8jsPcYYxpvnYPwWlg4jiImiPvHOZexVuIxRxQEUTC2vsgro+aMo4OX4JRll6MCYluJ0cQW+S2EDon4aRrh4stgjUfFYuPwZwr2F07HueLLQdWqiN8wGWOxemi5VLtk0ztaU4ppm2kkiee7vR3ivloFqJGCOQggOvW1cWYqxE2y46BWu4Y8UXzAki9OXkqalU0iIuNPbN2jmhMDmvZMi6D7StVUO7latEZMDslr0TSo9UCCykmbpJAAhCEkNAhCExghCEACEISAEIQmAKp/vq1VSfvKWctC9kTqg6N1TISKyZRJo8IUXfvNdgpDQhwI0UXkHWxZUskjXiRd2m3VR2JFpMoQ0KW7rP80aJsaXuDRXx0UjERRtME5rCskDY3ABwefLZQGrtqCkUtESSXIs1SCafaG7ElSIlNTmggVQ1VQIpSe6yAVA1mpSNDYatMKLtDSY1pAbHVNpIkDkmT5pNFijzUhoVZknggVaYFPB5JPP3qQxyVl1DKpUMg0UHAl+itGjEFS0RZpqN1GQlzr5oJy7hDQdykwWsjaLFJtJYCDzSbqUSg5bqlLEtkALkJTNk1zQzRik0gOJr70gYHehuqwHZtygut+nNW5RkFJYHnCIXpROqcjvACKHKgq9nDraJXJMEirfr5q3Le2wUGaOPmrGjwkJMqQthQKG6HVRcSCCp7x5joVOCWMOBBI06qxsTmYcSOFAnQnmqWixVq4k9yIyduXRSyWzHebcOhSeC077pP8A3lJvpzN0ItawU1bvRJzQRVKQFWSmQR6oLKTBbCWu25KgsIKzW3zR3YOhSLU8GAR5LO4bxnifCZHP4fi3wl3vAUQfgdFRLAWHQlUlpG9pptaNMqS5M7G8b4lxC/nU4dfRgH8lr8qALedaTqim25ctgoKP8UJjXGQC10nBn4PhzPncvdSySCrcfdXO0bUDeYaq6dTseTOrT+VducG/xPzPjnFxh8NPHhiQdZXU0u9Vp8VhcXwvHOgxDMr2+eh8x1CxjQ0Wzw/FpO4ZhsfGMXhmjRjzTm+jtwiU1N5ZUabhHC0ZWFxEADmOALqBDt6WT85wcYoGydTqtfM3gcj2vwuKxkF6lsrA6viCsN8eBa8huIe8XoQ2lt8zSwYOhGTyzfjdS2CiN1JeqIth3KtVUO5Vq0RkwS06oOyidkCJadUkm+8md0gBCEIYAhCEIaBCEIYMEIQhAgQhCbBgqn/vFaq5PfKznoSFu6uii67QPePoh3urEtDbeUqBvZA2UftJMRJpq1G90cio8wkxsfPn9ymWOaAHAi9Qq/tK+f7H/wBqkZUgAg2f5BVu5ob7ykUtE93oJAdXJIe8VF3vKQJPFkUoj94D0UhyUHc1IiTyHu23SutEm7oO6BoNyFI6AlRb7yfIpMJaA+6q2mnaqX2VA81LGiP27HVWH1VbeXqp8/ikORBwtwCmfCzRQH7wKx+ykJaCOgHaXai8kgA3omP3ag730CRKMW8NFm9kngtedD9yBv8AEfzUJf8AmHJMa2NlukoKw6OI10VeH/eOSd/zBSE94F/mWoym3UpDdQPvhSaIlHq8NKscadVKEX7wqTvf+CTM5Pkrfq4BT3FDkon3wpD3ikN+hxN3cAm52t0pR/uiq3bKRY5KSLkNJOIAy9N1Me8VTL9pBaJkZm2EjYq1OL9yoO2QNbJfZ9UNA1BKOTUcypE2RkHVRLWuYbGysl9wKB90oHFlAhLnW3VVyRuYdllQ/wBUYncJZLUmmYgBBBIUXaON81c33lXL76MmmeSsNrUhI2pJP5ILEdBfNRv/AOITdsoj3QhFI//Z"
    st.markdown(f'''
<style>
.end-wrap{{color:#18324f;background:#fff;margin:0 auto}}
.end-topbar{{display:flex;justify-content:space-between;align-items:center;padding:16px 4px 20px;gap:12px}}
.end-brand{{font-size:15px;letter-spacing:2px;font-weight:800;color:#173d66}}
.end-brand small{{color:#91a0ad;font-size:10px;letter-spacing:2px;margin-left:12px;border-left:1px solid #d8e0e8;padding-left:12px}}
.end-status{{color:#168f89;font-size:11px;font-weight:800;letter-spacing:1.5px}}
.end-hero{{min-height:310px;display:grid;grid-template-columns:44% 56%;overflow:hidden;background:linear-gradient(110deg,#0d3769,#164d86 53%,#0d5b6b)}}
.end-hero-copy{{padding:42px 34px;color:white;display:flex;flex-direction:column;justify-content:center}}
.end-eyebrow{{color:#56d4c4;letter-spacing:2px;font-size:10px;font-weight:800;margin-bottom:18px}}
.end-title{{font-size:clamp(36px,5vw,58px);line-height:1.1;font-weight:850;letter-spacing:-2px;margin:0 0 18px;color:white}}
.end-subtitle{{white-space:pre-line;color:#d3e2f2;line-height:1.9;font-size:15px}}
.end-rule{{height:3px;width:180px;margin-top:24px;background:linear-gradient(90deg,#20c4b2 0 34%,rgba(255,255,255,.22) 34% 100%)}}
.end-hero-image{{min-height:310px;background-image:linear-gradient(90deg,rgba(17,65,112,.22),rgba(5,35,65,.08)),url('{banner_image}');background-size:cover;background-position:center}}
.end-section{{padding:34px 28px 28px;border-bottom:1px solid #e3e9ef}}
.end-section-head{{display:flex;align-items:center;gap:14px;margin-bottom:28px}}
.end-icon{{width:48px;height:48px;display:flex;align-items:center;justify-content:center;border-radius:5px;background:#e6f5f3;color:#138f86;font-size:23px}}
.end-kicker{{color:#96a2ae;font-size:10px;letter-spacing:2px;font-weight:800;margin-bottom:5px}}
.end-heading{{color:#193653;font-size:22px;font-weight:800}}
.end-carbon-grid{{display:grid;grid-template-columns:1fr 1fr 210px;gap:24px;align-items:center}}
.end-metric-label{{color:#8b98a5;font-size:13px;margin-bottom:5px}}
.end-start{{font-size:44px;line-height:1.1;color:#a1adba;font-weight:750}}
.end-final{{font-size:54px;line-height:1.05;color:#119b8e;font-weight:850}}
.end-unit{{color:#9aa6b2;font-size:11px}}
.end-progress-title{{color:#9aa6b2;font-size:10px;letter-spacing:1px;font-weight:800;margin-bottom:14px}}
.end-track{{height:9px;background:#e7eef1;border-radius:20px;overflow:hidden}}
.end-fill{{height:100%;width:0%;border-radius:20px;background:linear-gradient(90deg,#8fb6c2,#18aa9c);animation:endFill 2.8s cubic-bezier(.2,.75,.25,1) .25s forwards}}
@keyframes endFill{{from{{width:0%}}to{{width:{reduction_rate}%}}}}
.end-progress-note{{color:#15988d;font-size:11px;text-align:right;font-weight:800;margin-top:9px}}
.end-target{{margin-top:24px;padding:17px 20px;border:1px solid #cce8e3;border-left:4px solid #1b9d91;background:#f1faf8;border-radius:4px;display:flex;align-items:center;gap:14px}}
.end-target-mark{{width:34px;height:34px;border-radius:50%;background:#159d91;color:white;display:flex;align-items:center;justify-content:center;flex:none}}
.end-target-title{{color:#16877f;font-weight:800;margin-bottom:4px}}
.end-target-desc{{color:#829b9a;font-size:12px}}
.end-bottom-grid{{display:grid;grid-template-columns:1fr 1fr}}
.end-bottom-card{{padding:30px 28px}}
.end-bottom-card+.end-bottom-card{{border-left:1px solid #e1e7ed}}
.end-stat-pair{{display:grid;grid-template-columns:1fr 1fr;gap:22px}}
.end-stat+.end-stat{{border-left:1px solid #e0e7ed;padding-left:26px}}
.end-stat-value{{color:#183653;font-size:clamp(20px,2.4vw,30px);font-weight:800;margin-top:9px;overflow-wrap:anywhere}}
.end-footer{{background:#f4f8fb;padding:24px 28px}}
.end-quote{{border-left:4px solid #168e9a;padding-left:18px;color:#425b72;font-size:14px;font-weight:700;line-height:1.7}}
.end-quote small{{display:block;color:#94a1ad;font-weight:400;font-size:11px;margin-top:5px}}
@media(max-width:700px){{.end-hero{{grid-template-columns:1fr}}.end-hero-copy{{padding:30px 24px}}.end-hero-image{{min-height:190px}}.end-carbon-grid{{grid-template-columns:1fr 1fr}}.end-carbon-progress{{grid-column:1/-1;grid-row:2}}.end-bottom-grid{{grid-template-columns:1fr}}.end-bottom-card+.end-bottom-card{{border-left:0;border-top:1px solid #e1e7ed}}.end-topbar{{align-items:flex-start;flex-direction:column}}}}
</style>
<div class="end-wrap">
 <div class="end-topbar"><div class="end-brand">{company}<small>NET ZERO VOYAGE</small></div><div class="end-status">● &nbsp;{status_label}</div></div>
 <div class="end-hero"><div class="end-hero-copy"><div class="end-eyebrow">THE FINAL PORT OF CALL</div><div class="end-title">항해 종료</div><div class="end-subtitle">{subtitle}</div><div class="end-rule"></div></div><div class="end-hero-image"></div></div>
 <section class="end-section"><div class="end-section-head"><div class="end-icon">♧</div><div><div class="end-kicker">ENVIRONMENTAL IMPACT</div><div class="end-heading">탄소 감축 성과</div></div></div>
 <div class="end-carbon-grid"><div><div class="end-metric-label">항해 시작</div><div class="end-start">{START_EMISSION}</div><div class="end-unit">탄소 배출량</div></div><div class="end-carbon-progress"><div class="end-progress-title">CARBON REDUCTION JOURNEY</div><div class="end-track"><div class="end-fill"></div></div><div class="end-progress-note">-{reduction_rate}% 감축</div></div><div style="border-left:1px solid #dce5e9;padding-left:28px"><div class="end-metric-label">최종 탄소 배출량</div><div class="end-final">{emission}</div><div class="end-unit">{'NET ZERO' if emission == 0 else 'FINAL EMISSION'}</div></div></div>
 <div class="end-target"><div class="end-target-mark">{'✓' if success else '!'}</div><div><div class="end-target-title">{target_title}</div><div class="end-target-desc">{target_desc}</div></div></div></section>
 <div class="end-bottom-grid"><section class="end-bottom-card"><div class="end-section-head"><div class="end-icon" style="background:#eaf1fb;color:#27619a">▣</div><div><div class="end-kicker">BUSINESS PERFORMANCE</div><div class="end-heading">기업 경영 성과</div></div></div><div class="end-stat-pair"><div class="end-stat"><div class="end-metric-label">최종 보유 자금</div><div class="end-stat-value">₩ {final_money}</div></div><div class="end-stat"><div class="end-metric-label">누적 운항 수익</div><div class="end-stat-value">₩ {total_income}</div></div></div></section>
 <section class="end-bottom-card"><div class="end-section-head"><div class="end-icon">♧</div><div><div class="end-kicker">FLEET OPERATIONS</div><div class="end-heading">선단 운영 성과</div></div></div><div class="end-stat-pair"><div class="end-stat"><div class="end-metric-label">최종 보유 선박 수</div><div class="end-stat-value">{fleet_count} <span style="font-size:14px;font-weight:500;color:#8796a5">척</span></div></div><div class="end-stat"><div class="end-metric-label">총 운항 횟수</div><div class="end-stat-value">{voyage_count} <span style="font-size:14px;font-weight:500;color:#8796a5">회</span></div></div></div></section></div>
 <div class="end-footer"><div class="end-quote">“바다를 바꾸는 것은 거대한 파도가 아니라, 올바른 방향으로 이어진 항해입니다.”<small>당신의 선택이 지속 가능한 바다의 내일을 만들었습니다.</small></div></div>
</div>
''', unsafe_allow_html=True)
    if st.button("메인 화면으로 돌아가기　 →", key="restart_game", type="primary", use_container_width=True):
        reset_game()
        st.rerun()
    st.stop()

st.markdown(f"""
<div style="display:flex;align-items:center;justify-content:space-between;gap:16px;background:#ffffff;border:1px solid #e1e7f0;border-radius:15px;padding:16px 20px;margin-bottom:18px;box-shadow:0 3px 12px rgba(20,45,80,.035)">
 <div style="display:flex;align-items:center;gap:13px"><div style="width:42px;height:42px;border-radius:12px;background:#2855d9;color:white;display:flex;align-items:center;justify-content:center;font-size:22px">▥</div><div><div style="font-weight:800;letter-spacing:1.5px;color:#172033;font-size:14px">{st.session_state.company_name.upper()}</div><div style="font-size:10px;letter-spacing:2px;color:#7a879a">MARITIME GROUP</div></div></div>
 <div style="text-align:right"><div style="font-size:11px;color:#7a879a">선주</div><div style="font-size:14px;font-weight:750;color:#172033">{st.session_state.captain_name}</div></div>
</div>
""", unsafe_allow_html=True)
st.title("관제 센터")
st.caption("선단 운영 현황을 확인하고, 수익과 탄소 감축 기술을 관리하세요.")

def advance_turn():
    """목적지 미배정 경고를 거친 뒤 실제로 1년 진행한다."""
    st.session_state.return_feedback = ""
    if st.session_state.phase == "ended":
        return
    if not st.session_state.get("show_empty_destination_warning", False):
        if not any(ship.get("dest") for ship in st.session_state.get("fleet", [])):
            st.session_state.show_empty_destination_warning = True
            return
    st.session_state.show_empty_destination_warning = False
    st.session_state.confirm_empty_destination_turn = False

    old_year = int(st.session_state.year)
    new_year = min(END_YEAR, old_year + 1)
    if new_year == old_year:
        return
    st.session_state.year = new_year
    # 이전 연도 의뢰는 다음 해로 넘어가면 자동 만료된다. 지정된 연도에만 새 의뢰를 만든다.
    old_quest = st.session_state.get("annual_quest")
    if old_quest and old_quest.get("status") == "open":
        old_quest["status"] = "expired"
    if new_year in QUEST_YEARS and st.session_state.get("annual_quest_year") != new_year:
        generate_annual_quest(new_year)
    animation_ships = []

    for ship in list(st.session_state.fleet):
        status = ship.get("status", ship.get("phase", "docked"))
        if status not in ("outbound", "returning"):
            continue
        if ship.get("waiting_for_turn", False):
            ship["waiting_for_turn"] = False

        dest = ship.get("dest")
        duration = max(1, int(ship.get("leg_years", actual_years(dest))))
        elapsed_before = max(0, int(ship.get("trip_elapsed", 0)))
        elapsed_after = min(duration, elapsed_before + 1)
        ship["trip_elapsed"] = elapsed_after
        ship["years_left"] = max(0, duration - elapsed_after)

        # 지도는 왕복 항로 전체를 따라 이번 1년분만 재생한다.
        one_way = SEA_ROUTES.get(dest, [PORT_COORDS["부산"]])
        round_trip = list(one_way) + list(reversed(one_way[:-1]))
        animation_ships.append({
            "id": ship["id"], "name": ship["name"], "type": ship["type"],
            # 왕복 전체 항로를 기준으로, 이번 버튼에서 1년분(전체의 1/N)만 재생한다.
            "route": round_trip, "destination": dest, "phase": "outbound",
            "pos": elapsed_before * 5, "end": elapsed_after * 5,
            "total": duration * 5, "turn_step": True, "paused": False,
        })

        # 항해 시간은 왕복 총 기간이다. 기간의 절반 지점에서 목적지에 도착하고,
        # 남은 기간은 귀항에 사용한다. 1년짜리 항로는 그해 안에 왕복을 마친다.
        arrival_year = (duration + 1) // 2
        if status == "outbound" and elapsed_after >= arrival_year:
            arrive(ship)
            ship["trip_elapsed"] = elapsed_after
            ship["years_left"] = max(0, duration - elapsed_after)
            if ship["years_left"] == 0:
                settle_return(ship)
        elif status == "returning" and elapsed_after >= duration:
            settle_return(ship)
        else:
            sync_ship_map_progress(ship)

    # 선박별 이벤트 대기 턴을 줄이고, 항해 중일 때 턴당 최대 1건(30%) 발생시킨다.
    for vessel in active_ships():
        vessel["event_cooldown"] = max(0, int(vessel.get("event_cooldown", 0)) - 1)
    if st.session_state.get("event_pending") is None and active_ships() and random.random() < 0.30:
        trigger_random_event()

    # 자율운항을 켠 선박은 부산 귀항 후 다음 턴 진행 시 자동 재출항한다.
    if st.session_state.auto_on and 4 in st.session_state.bought_tr:
        start_auto_voyage()

    st.session_state.turn_animation_ships = animation_ships
    check_year_checkpoint()


# 턴제에서는 자동 시계를 사용하지 않는다. 버튼을 누르기 전까지 연도와 선박 시간이 멈춰 있다.
emission = current_emission()
c1, c2, c3 = st.columns(3)
c1.metric("현재 연도", f"{st.session_state.year}년")
c2.metric("보유 자금", money_label(st.session_state.money))
c3.metric("배출량", f"{emission}%")
next_checkpoint = next((year for year in sorted(CHECKPOINTS) if year not in st.session_state.checked), None)
if next_checkpoint is None:
    st.info("모든 중간 점검을 통과했습니다.")
else:
    st.markdown(f"**다음 점검: {next_checkpoint}년 (배출량 {CHECKPOINTS[next_checkpoint]}% 이하)**")
# 선박 구매 직후 선택할 선박은 위젯이 생성되기 전에 반영한다.
_pending_ship_id = st.session_state.pop("pending_selected_ship_id", None)
if _pending_ship_id is not None:
    st.session_state.selected_ship_id = _pending_ship_id

with st.expander("🏢 회사 및 선단 관리", expanded=True):
    st.markdown(
        f"**{st.session_state.company_name}**  ·  선주 **{st.session_state.captain_name}**",
        help="회사명과 선주 이름은 로그인 화면에서 설정합니다."
    )
    st.markdown(f"**보유 선박 ({len(st.session_state.fleet)}/{MAX_FLEET_SIZE})**")
    for ship in st.session_state.fleet:
        ship_status = ship.get("status", "docked")
        if ship_status == "docked" and ship.get("dest"):
            ship_status_label = "출항 대기 중"
        else:
            ship_status_label = {"docked": "부산항 정박", "outbound": "항해 중", "returning": "귀항 중"}.get(ship_status, "정박")
        st.write(f"🚢 **{ship['name']}** · {ship['type']} · 구매가 {money_label(ship['price'])} · 상태: {ship_status_label}")
    if st.session_state.fleet:
        managed = selected_ship()
        if managed:
            with st.form(f"rename_ship_form_{managed['id']}"):
                edited_name = st.text_input("선박 이름 변경", value=managed["name"], key=f"rename_ship_name_{managed['id']}")
                rename_submit = st.form_submit_button("이름 변경", use_container_width=True)
                if rename_submit:
                    rename_ship(managed["id"], edited_name)
                    st.rerun()
            sell_rate = 0.70 + ((int(st.session_state.year) + int(managed["id"])) % 11) / 100
            st.caption(f"올해 예상 중고 판매 환급률: {round(sell_rate*100)}% · 예상 환급액 {money_label(int(managed.get('price',0)*sell_rate))}")
            cannot_sell = len(st.session_state.fleet) <= 1 or managed.get("status", "docked") != "docked"
            if st.button("선택한 선박 판매", key=f"sell_ship_{managed['id']}", disabled=cannot_sell, use_container_width=True):
                sell_ship(managed["id"])
                st.rerun()
            if len(st.session_state.fleet) <= 1:
                st.caption("최소 1척은 보유해야 하므로 마지막 선박은 판매할 수 없습니다.")
            elif managed.get("status", "docked") != "docked":
                st.caption("운항 중인 선박은 판매할 수 없습니다.")
    else:
        st.info("보유 선박이 없습니다. 아래 선박 구매 메뉴에서 새 선박을 구매하세요.")

if st.session_state.msg:
    st.success(st.session_state.msg)
    st.session_state.msg = ""



# 이벤트 선택창은 반드시 지도 바로 위에 표시한다.
if st.session_state.event_pending and st.session_state.phase != "ended":
    event = st.session_state.event_pending
    with st.container(border=True):
        st.subheader(f"⚠️ 긴급 상황: {event['title']}")
        st.markdown(f"**발생 선박:** {event.get('ship_name', '선박')} · {event.get('ship_type', '선종 미상')}")
        st.write(event["description"])
        event_cols = st.columns(len(event["choices"]))
        for i, choice in enumerate(event["choices"]):
            event_cols[i].button(
                choice["label"], key=f"event_choice_{event['title']}_{i}",
                use_container_width=True, on_click=resolve_event, args=(i,)
            )

st.subheader("선박 상태 현황")
status_rows = []
for vessel in st.session_state.fleet:
    vphase = vessel.get("status", "docked")
    if vphase == "docked" and vessel.get("dest"):
        status_label = "출항 대기 중"
    else:
        status_label = {"docked": "부산항 정박", "outbound": "항해 중", "returning": "귀항 중"}.get(vphase, vphase)
    if vphase == "outbound":
        remaining_label = f"목적지까지 {max(0, int(vessel.get('years_left', 0)))}년"
    elif vphase == "returning":
        remaining_label = f"부산까지 {max(0, int(vessel.get('years_left', 0)))}년"
    else:
        remaining_label = "—"
    status_rows.append({"이름": vessel.get("name", "선박"), "선종": vessel.get("type", "—"),
                        "상태": status_label, "목적지": vessel.get("dest") or "부산", "남은 시간": remaining_label})
st.dataframe(status_rows, hide_index=True, use_container_width=True)

map_col, info_col = st.columns([2.15, 1], gap="medium")

with map_col:
    st.subheader("실제 지도와 항로")
    st.caption("항해 중에는 지도 배경과 항구 핀을 유지하고 선박만 이동합니다. 목적지 선택은 정박 중 지도에서 할 수 있습니다.")

    turn_animation_ships = st.session_state.get("turn_animation_ships", [])
    travelling_ships = turn_animation_ships if turn_animation_ships else active_ships()
    if travelling_ships:
        # 기존 Leaflet iframe/JS 이동 방식을 유지한다. 출항 직후에는 멈춰 있고, 턴 버튼으로만 애니메이션을 재생한다.
        map_config = {
            "ports": [{"name": name, "lat": coords[0], "lon": coords[1]} for name, coords in PORT_COORDS.items()],
            "ships": (
                # 이번 턴의 애니메이션 스냅샷을 그대로 JS에 전달한다.
                # 여기서 일반 선박 상태로 다시 변환하면 end/turn_step/왕복 항로가 사라져
                # 기존 Leaflet 애니메이션이 재생되지 않는다.
                [{"id": ship["id"], "name": ship["name"], "type": ship["type"],
                  "route": ship["route"], "destination": ship.get("destination"),
                  "phase": ship.get("phase", "outbound"), "pos": ship["pos"],
                  "end": ship["end"], "total": ship["total"],
                  "turn_step": ship.get("turn_step", True), "paused": ship.get("paused", False)}
                 for ship in turn_animation_ships]
                if turn_animation_ships else
                [{"id": ship["id"], "name": ship["name"], "type": ship["type"],
                  "route": SEA_ROUTES.get(ship.get("dest"), [PORT_COORDS["부산"]]),
                  "destination": ship.get("dest"), "phase": ship.get("status", "docked"),
                  "pos": round((max(1, int(ship.get("leg_years", 1))) - max(0, min(max(1, int(ship.get("leg_years", 1))), int(ship.get("years_left", 0))))) * 5),
                  "total": max(1, int(ship.get("leg_years", 1))) * 5,
                  "paused": bool(st.session_state.event_pending or ship.get("waiting_for_turn", False))}
                 for ship in active_ships()]
            ),
            "paused": bool(st.session_state.event_pending),
        }
        config_json = json.dumps(map_config, ensure_ascii=False).replace("</", "<\\/")
        map_html = r'''<!doctype html>
    <html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
    <style>
    html,body{margin:0;padding:0;background:#071521;font-family:sans-serif}#map{height:430px;width:100%;border-radius:10px;overflow:hidden}
    .ship-icon{font-size:25px;line-height:32px;text-align:center;width:34px;height:34px;filter:drop-shadow(0 1px 2px #000)}
    .leaflet-tooltip.port-label{background:rgba(7,21,33,.94);color:#fff;border:1px solid #678091;box-shadow:none;font-weight:600}.leaflet-tooltip.port-label:before{display:none}
    .leaflet-control-attribution{font-size:9px!important}
    </style></head><body><div id="map" aria-label="선박 항로 지도"></div>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script><script>
    (function(){
     const C=__CONFIG__;
     const map=L.map('map',{zoomControl:true,preferCanvas:true}).setView([30,125],3);
     L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:18,attribution:'&copy; OpenStreetMap'}).addTo(map);
     const portsLayer=L.layerGroup().addTo(map);
     (C.ports||[]).forEach(p=>{
       const b=p.name==='부산';
       L.circleMarker([p.lat,p.lon],{radius:b?8:7,color:b?'#ff6b6b':'#b68d30',weight:2,fillColor:b?'#ff6b6b':'#f2c14e',fillOpacity:.95}).addTo(portsLayer)
        .bindTooltip((b?'⚓ ':'📍 ')+p.name,{permanent:true,direction:'top',className:'port-label',offset:[0,-5]});
     });
     const shipIcon=L.divIcon({className:'ship-icon-wrap',html:'<div class="ship-icon">🚢</div>',iconSize:[34,34],iconAnchor:[17,17]});
     const moving=[];
     function pointAt(route,f){
       if(!route||route.length<2)return (route&&route[0])||[35.1796,129.0756];
       const lens=[];let sum=0;for(let i=0;i<route.length-1;i++){const d=Math.hypot(route[i+1][0]-route[i][0],route[i+1][1]-route[i][1]);lens.push(d);sum+=d;}
       let target=Math.max(0,Math.min(1,f))*sum;
       for(let i=0;i<lens.length;i++){if(target<=lens[i]||i===lens.length-1){const t=lens[i]?target/lens[i]:0;return [route[i][0]+(route[i+1][0]-route[i][0])*t,route[i][1]+(route[i+1][1]-route[i][1])*t];}target-=lens[i];}
       return route[route.length-1];
     }
     function partialPath(route,progress,returning){
       if(!route||route.length<2)return route||[];
       const f=returning?1-progress:progress;const p=pointAt(route,f);const out=[route[0]];
       const lens=[];let sum=0;for(let i=0;i<route.length-1;i++){const d=Math.hypot(route[i+1][0]-route[i][0],route[i+1][1]-route[i][1]);lens.push(d);sum+=d;}
       let target=f*sum, travelled=0;
       for(let i=0;i<lens.length;i++){if(target<=travelled+lens[i]){out.push(p);break;}out.push(route[i+1]);travelled+=lens[i];}
       if(returning){const back=[p];let accumulated=0;for(let i=route.length-2;i>=0;i--){accumulated+=lens[i];if(accumulated<=(1-f)*sum)back.push(route[i]);}return back;}
       return out;
     }
     (C.ships||[]).forEach((S,index)=>{
       const route=S.route||[[35.1796,129.0756]];
       if(route.length>1)L.polyline(route,{color:['#42c7d9','#a78bfa','#fb923c','#34d399','#f472b6'][index%5],weight:3,opacity:.9}).addTo(map);
       const travelled=L.polyline([],{color:'#f2c14e',weight:4,opacity:.95}).addTo(map);
       const ship=L.marker(route[0]||[35.1796,129.0756],{icon:shipIcon,interactive:false,zIndexOffset:1000+index}).addTo(map);
       ship.bindTooltip(S.name+' · '+S.type,{permanent:true,direction:'top',offset:[0,-15]});
       moving.push({S,route,ship,travelled,
         base:Math.max(0,Math.min(Math.max(1,Number(S.total)||1),Number(S.pos)||0)),
         end:Math.max(0,Math.min(Math.max(1,Number(S.total)||1),Number(S.end ?? S.total)||0)),
         total:Math.max(1,Number(S.total)||1),started:performance.now(),
         turnStep:!!S.turn_step,paused:!!C.paused||!!S.paused});
     });
     const allPoints=[];(C.ships||[]).forEach(S=>(S.route||[]).forEach(p=>allPoints.push(p)));
     if(allPoints.length>1)map.fitBounds(L.latLngBounds(allPoints),{padding:[35,35],maxZoom:5,animate:false});
     function tick(now){
       let again=false;
       moving.forEach(M=>{
         let progress=M.base/M.total;
         if(!M.paused){
           if(M.turnStep){
             // 다음 해로 클릭 한 번당 1.5초 동안 해당 1년 구간만 이동한다.
             const start=M.base/M.total, end=M.end/M.total;
             const t=Math.min(1,Math.max(0,(now-M.started)/1500));
             progress=start+(end-start)*t;
           }else{
             progress=Math.min(1,(M.base+(now-M.started)/1000)/M.total);
           }
         }
         const f=M.S.phase==='returning'?1-progress:progress;
         M.ship.setLatLng(pointAt(M.route,f));
         M.travelled.setLatLngs(partialPath(M.route,progress,M.S.phase==='returning'));
         if(!M.paused&&(M.turnStep?progress<(M.end/M.total):progress<1))again=true;
       });
       if(again)requestAnimationFrame(tick);
     }
     tick(performance.now());
     setTimeout(()=>map.invalidateSize(),80);
    })();
    </script></body></html>'''.replace("__CONFIG__", config_json)
        components.html(map_html, height=450, scrolling=False)
        if turn_animation_ships:
            st.session_state.turn_animation_ships = []
            # 이번 턴 애니메이션이 끝난 뒤에는 다음 해로를 누를 때까지 정지한다.
            for vessel in st.session_state.fleet:
                if vessel.get("status") in ("outbound", "returning"):
                    vessel["waiting_for_turn"] = True
    else:
        # 정박 중에는 기존 Plotly 지도를 사용해 핀 클릭으로 목적지를 고르는 기능을 유지한다.
        map_event = st.plotly_chart(
            make_route_map(), use_container_width=True, key="live_route_map",
            on_select="rerun", selection_mode="points",
        )
        try:
            selected_points = map_event.selection.points
            if selected_points:
                point = selected_points[-1]
                point_index = point.get("point_index", point.get("pointIndex"))
                # Scattermap 이벤트에서는 customdata가 더 안정적으로 전달되므로 우선 사용한다.
                picked = point.get("customdata")
                if isinstance(picked, (list, tuple)):
                    picked = picked[0] if picked else None
                if not picked and point_index is not None:
                    pin_names = ["부산"] + [d["name"] for d in DESTINATIONS]
                    if 0 <= int(point_index) < len(pin_names):
                        picked = pin_names[int(point_index)]
                if picked:
                    if picked == "부산":
                        st.session_state.selected_port = None
                        st.session_state.show_empty_destination_warning = False
                    elif assign_destination(picked, selected_ship()):
                        st.session_state.show_empty_destination_warning = False
        except (AttributeError, TypeError, KeyError, ValueError):
            pass


    if st.session_state.get("show_empty_destination_warning", False):
        st.markdown("<div style='background:#fff1f2;border:1px solid #ef4444;color:#b91c1c;padding:12px 14px;border-radius:10px;font-weight:700;margin:8px 0'>⚠️ 아직 목적지를 선택하지 않았습니다. 정말 진행하시겠습니까?</div>", unsafe_allow_html=True)
        # 목적지를 선택하면 assign_destination()에서 이 경고가 즉시 해제된다.
        if st.button("그래도 다음 해로 진행", key="confirm_empty_destination_turn_button", type="primary", use_container_width=True, disabled=(st.session_state.phase == "ended")):
            st.session_state.confirm_empty_destination_turn = True
            advance_turn()
            st.rerun()
    # 목적지 미배정 경고가 표시된 동안에는 확인 버튼만 보여 준다.
    # 진행이 완료되어 경고 상태가 해제되면 일반적인 다음 해로 버튼이 다시 나타난다.
    if not st.session_state.get("show_empty_destination_warning", False):
        st.button("다음 해로 ▶", key="advance_turn_button", type="primary",
                   disabled=(st.session_state.phase == "ended"),
                   use_container_width=True, on_click=advance_turn)
    if st.session_state.get("return_feedback"):
        st.success(st.session_state.return_feedback)
    if st.session_state.get("quest_accept_feedback"):
        st.success(st.session_state.quest_accept_feedback)
        st.session_state.quest_accept_feedback = ""
    st.caption(f"버튼 한 번에 {TURN_YEARS}년 진행합니다. 항해 준비 중에는 시간이 흐르지 않습니다.")
    # 긴급 의뢰 팝업의 표시 방식과 위치는 유지한다.
    if (st.session_state.get("annual_quest")
            and st.session_state.annual_quest.get("status") == "open"
            and st.session_state.phase != "ended"):
        show_annual_quest_panel()

with info_col:
    current_ship = selected_ship()
    if current_ship and current_ship.get("status", current_ship.get("phase")) in ("outbound", "returning") and current_ship.get("weather_note"):
        st.info(f"🌦️ {current_ship['name']} 기상: {current_ship['weather']} — {current_ship['weather_note']}")
    if current_ship and current_ship.get("status", current_ship.get("phase")) == "outbound":
        st.write(f"🚢 {current_ship['name']} 항해 중 · {current_ship.get('dest')} 방향 · 남은 {current_ship.get('years_left', 0)}년 / 총 {current_ship.get('leg_years', 0)}년")
    elif current_ship and current_ship.get("status", current_ship.get("phase")) == "returning":
        st.write(f"↩️ {current_ship['name']} 부산으로 귀항 중 · 남은 {current_ship.get('years_left', 0)}년 / 총 {current_ship.get('leg_years', 0)}년")
    else:
        st.write("⚓ 선택한 선박은 부산항 정박 중 — 목적지를 선택해 출항하세요.")


    # 참고 이미지처럼 오른쪽에 운항 명령 카드를 구성한다. 게임 로직과 지도는 변경하지 않는다.
    st.markdown("<div style='letter-spacing:2px;font-size:11px;color:#8a94a6;font-weight:700'>VOYAGE CONTROL</div>", unsafe_allow_html=True)
    st.markdown("## 운항 명령")
    if st.session_state.fleet:
        st.selectbox(
            "배정 선박",
            options=[item["id"] for item in st.session_state.fleet],
            format_func=lambda sid: next(item["name"] + " · " + item["type"] for item in st.session_state.fleet if item["id"] == sid),
            key="selected_ship_id",
        )
    ship = selected_ship()
    if ship and not st.session_state.selected_port and ship.get("dest"):
        st.session_state.selected_port = ship.get("dest")
    selected_port = st.session_state.selected_port
    can_choose = bool(ship and ship.get("status", ship.get("phase", "docked")) == "docked" and st.session_state.phase != "ended")
    if ship:
        st.caption(f"현재 선택 선박: {ship['name']} · 배정 목적지: {ship.get('dest') or '미배정'}")
    ship_type = ship["type"] if ship else "기본 화물선"
    available_special_ports = [
        name for name in st.session_state.unlocked_special_ports
        if name in SPECIAL_PORTS and ship_type in SPECIAL_PORTS[name]["ship_types"]
    ]
    available_destinations = [d["name"] for d in DESTINATIONS]
    if ship_type in ("LNG선", "탱크선", "케미컬 탱커"):
        available_destinations += available_special_ports
    if ship_type == "어선":
        available_destinations = list(FISHING_GROUNDS)

    with st.container(border=True):
        st.caption("출발항")
        st.markdown("### 🔵 부산 신항")
        st.caption("KR PUS · 대한민국")
        st.markdown("<div style='height:1px;background:#e5e7eb;margin:12px 0'></div>", unsafe_allow_html=True)
        st.caption("목적항")
        if can_choose and available_destinations:
            with st.expander("목적항 선택 / 변경", expanded=not (selected_port and selected_port in available_destinations)):
                default_index = available_destinations.index(selected_port) if selected_port in available_destinations else 0
                picked_port = st.selectbox("목적항", available_destinations, index=default_index, key="destination_dropdown")
                if st.button("목적항 설정", key="destination_dropdown_apply", use_container_width=True):
                    if assign_destination(picked_port, ship):
                        st.session_state.msg = f"{ship['name']}의 목적지가 {picked_port}(으)로 설정되었습니다. 출항 버튼을 눌러 운항을 시작하세요."
                    st.rerun()
        if selected_port and selected_port in available_destinations:
            destination = next((d for d in DESTINATIONS if d["name"] == selected_port), None)
            if destination is None:
                destination = SPECIAL_PORTS.get(selected_port) or FISHING_GROUNDS.get(selected_port)
            years = actual_years(selected_port)
            income = actual_income(selected_port)
            features = {
                "도쿄": "일본의 주요 국제 무역항입니다.",
                "상하이": "중국의 주요 국제 무역항이자 대형 컨테이너 항만입니다.",
                "싱가포르": "MPA Green Ship Programme은 요건을 충족하고 사전 등록한 선박에 연료·기술 조건에 따라 항만 요금 감면을 제공합니다. 게임에서는 기존 엔진 업그레이드를 자격의 단순화된 대리 기준으로 사용합니다.",
                "로테르담": "항만은 Green Award 및 환경 데이터·선박별 조건에 따른 인센티브를 운영합니다. 게임은 실제 요금 자격을 단순화해 적용합니다.",
                "타이베이": "대만 북부의 주요 항만입니다.",
                "홍콩": "아시아의 주요 항만이자 환적 거점입니다.",
                "로스앤젤레스": "Port of Los Angeles의 ESI 프로그램은 등록된 선박의 ESI 점수 구간에 따라 입항별 인센티브를 제공합니다. 게임은 이를 단순화해 적용합니다.",
            }
            if selected_port in [d["name"] for d in DESTINATIONS]:
                current_fee, current_benefit = discounted_port_fee(selected_port)
            elif selected_port in FISHING_GROUNDS:
                current_fee = 0
                current_benefit = {"discount_percent": 0, "arrival_bonus": 0, "note": "어장은 정박비가 없습니다."}
            else:
                base_fee = int(destination.get("fee", 0))
                handling = handling_discount_percent()
                current_fee = round(base_fee * (100 - handling) / 100)
                current_benefit = {"discount_percent": handling, "arrival_bonus": 0, "note": f"자동화 하역 시스템 {handling}% 할인" if handling else destination.get("description", "게임용 목적지")}
            suffix = " 어장" if selected_port in FISHING_GROUNDS else " 항구"
            st.markdown(f"### 📍 {selected_port}{suffix}  ⌄")
            st.caption(destination.get("code", "목적지 · 항해 경로"))
            st.markdown("<div style='height:1px;background:#e5e7eb;margin:12px 0'></div>", unsafe_allow_html=True)
            st.caption("배정 선박")
            st.markdown(f"### 🚢 {ship.get('name', '선박 미배정') if ship else '선박 미배정'}")
            st.caption(f"{ship_type} · 부산 귀항 후 운임 정산")
            st.markdown("<div style='height:1px;background:#e5e7eb;margin:12px 0'></div>", unsafe_allow_html=True)
            estimate_cols = st.columns(2)
            estimate_cols[0].caption("◷  예상 운항")
            estimate_cols[0].markdown(f"**{years}년**")
            estimate_cols[1].caption("₩  예상 수익")
            estimate_cols[1].markdown(f"**{money_label(income)}**")
            st.markdown("<div style='height:1px;background:#e5e7eb;margin:12px 0'></div>", unsafe_allow_html=True)
            st.caption(f"⚓ 적용 정박비  **{money_label(current_fee)}**" + (f" · {current_benefit['discount_percent']}% 감면" if current_benefit["discount_percent"] else ""))
            st.write(features.get(selected_port, destination.get("description", "게임용 목적지입니다.")))
            st.info(f"**게임 내 혜택:** {current_benefit['note'] or '현재 적용 가능한 별도 혜택 없음'}")
            official_sources = {
                "싱가포르": "https://www.mpa.gov.sg/finance-e-services/tariff-fees-and-charges/ocean-going-vessels/port-dues-concessions",
                "로테르담": "https://www.portofrotterdam.com/en/sea-shipping/seaport-dues/green-award-discount",
                "로스앤젤레스": "https://portoflosangeles.org/environment/air-quality/environmental-ship-index",
            }
            if selected_port in official_sources:
                st.markdown(f"[항만 공식 출처 보기]({official_sources[selected_port]})")
            st.caption(f"기본 정박비 {money_label(destination['fee'])} · 혜택 적용 후 {money_label(current_fee)}. 부산항 정박비는 별도이며 운임은 부산 귀항 후 지급됩니다. 실제 항만 요금과 자격 조건을 참고해 단순화한 게임 규칙입니다.")
            departure_label = f"🎣 {selected_port} 조업 출항" if selected_port in FISHING_GROUNDS else "🚢 출항 명령  ›"
            if st.button(departure_label, key="selected_port_depart", disabled=not can_choose, use_container_width=True, type="primary"):
                start_voyage(selected_port)
                st.rerun()
            if (ship and ship.get("status", ship.get("phase")) == "outbound"
                    and int(ship.get("trip_elapsed", 0)) == 0
                    and ship.get("waiting_for_turn", False)):
                if st.button("↩ 출항 취소 · 목적지 재설정", key="cancel_departure_button", use_container_width=True):
                    cancel_departure(ship)
                    st.rerun()
        else:
            pending_ship = selected_ship()
            if (pending_ship and pending_ship.get("status", pending_ship.get("phase")) == "outbound"
                    and int(pending_ship.get("trip_elapsed", 0)) == 0
                    and pending_ship.get("waiting_for_turn", False)):
                if st.button("↩ 출항 취소 · 목적지 재설정", key="cancel_departure_button_empty", use_container_width=True):
                    cancel_departure(pending_ship)
                    st.rerun()
            st.info("지도에서 목적지 핀을 선택하거나 목적항 선택 메뉴를 열어 목적지를 설정하세요.")
            if available_destinations:
                manual_port = st.selectbox("목적항 / 어장 선택", available_destinations, key="manual_destination")
                if st.button("목적지 배정 / 정보 보기", key="manual_destination_pick", disabled=not can_choose, use_container_width=True):
                    if assign_destination(manual_port, ship):
                        st.session_state.msg = f"{ship['name']}의 목적지가 {manual_port}(으)로 설정되었습니다."
                    st.rerun()
            else:
                st.warning("이 선박이 이용할 수 있는 특수 목적지가 없습니다.")

    if 4 in st.session_state.bought_tr:
        st.toggle("자동 운항", key="auto_on", disabled=(not current_ship or current_ship.get("status", ship.get("phase", "docked")) != "docked" or st.session_state.phase == "ended"),
                  help="정박 중인 일반 선박을 자동 항로로 출발시키고, 귀항 후 자동으로 다음 항로에 재출항합니다.")
        if st.session_state.auto_on:
            next_auto_dest = AUTO_ROUTE[st.session_state.auto_idx % len(AUTO_ROUTE)]
            st.caption(f"다음 자동 항로: {next_auto_dest}")
            st.button("▶ 정박 선박 자동 출항", key="start_auto_voyage",
                      disabled=(not current_ship or current_ship.get("status", ship.get("phase", "docked")) != "docked" or st.session_state.phase == "ended"), use_container_width=True,
                      on_click=start_auto_voyage)

if st.session_state.event_log:
    with st.expander("📜 최근 해상 사건 기록"):
        for event_line in st.session_state.event_log[-8:][::-1]:
            st.write(f"• {event_line}")

st.subheader("업그레이드 상점")
eq_tab, tr_tab, ship_tab = st.tabs(["탄소 기술 연구", "운송 강화", "선박 구매"])
with eq_tab:
    st.caption("각 기술은 1단계부터 순서대로 연구합니다. 연구 효과는 회사 전체에 적용되며 수치는 게임용 단순화 값입니다.")
    for tech in RESEARCH_TECHS:
        level = int(st.session_state.research_levels.get(tech["id"], 0))
        with st.container(border=True):
            st.markdown(f"**{tech['name']}**")
            st.caption(f"연구 진행: {level}/{len(tech['stages'])}단계")
            for i, stage in enumerate(tech["stages"]):
                mark = "✅" if i < level else ("➡️" if i == level else "🔒")
                st.write(f"{mark} {stage['label']} · 탄소 감축 -{stage['reduction']}%p · 연구비 {money_label(stage['price'])}")
            if level < len(tech["stages"]):
                stage = tech["stages"][level]
                st.button(
                    f"{stage['label']} 연구하기", key=f"research_{tech['id']}",
                    disabled=(st.session_state.phase == "ended" or st.session_state.money < stage["price"]),
                    use_container_width=True, on_click=research_next_stage, args=(tech["id"],)
                )
            else:
                st.success("기술 연구 완료")
with tr_tab:

    for item in TRANSPORT:
        row = st.columns([4, 1, 1])
        if item["id"] == 3:
            level = int(st.session_state.get("transport_levels", {}).get("handling", 0))
            prices = [15, 25, 40]
            next_price = prices[level] * MONEY_SCALE if level < 3 else 0
            with row[0]:
                st.markdown(f"**{item['name']}**")
                st.caption(f"현재 {level}/3단계 · 정박비 {level * 25}% 할인 · 모든 항구 적용, 어장은 무료")
                st.caption(item["effect"])
            with row[1]:
                if level >= 3:
                    st.button("연구 완료", key="tr_done_3", disabled=True, use_container_width=True)
                else:
                    st.button(f"{level + 1}단계", key=f"tr_3_{level}", disabled=(st.session_state.phase == "ended" or st.session_state.money < next_price), use_container_width=True, on_click=buy_transport, args=(3,))
            with row[2]:
                st.write("완료" if level >= 3 else money_label(next_price))
        else:
            bought = item["id"] in st.session_state.bought_tr
            enough_money = st.session_state.money >= item["price"]
            with row[0]:
                st.markdown(f"**{item['name']}**")
                st.caption(f"{item['effect']} · 가격 {money_label(item['price'])}")
                if not bought and not enough_money:
                    st.caption("자금 부족")
            with row[1]:
                if bought:
                    st.button("구매 완료", key=f"tr_done_{item['id']}", disabled=True, use_container_width=True)
                else:
                    st.button("구매", key=f"tr_{item['id']}", disabled=(st.session_state.phase == "ended" or not enough_money), use_container_width=True, on_click=buy_transport, args=(item["id"],))
            with row[2]:
                st.write(money_label(item["price"]))
        st.divider()
with ship_tab:
    st.caption(f"새 선박을 구매하면 회사 선단에 추가됩니다. 현재 {len(st.session_state.fleet)}/{MAX_FLEET_SIZE}척 보유 중이며, 최대 {MAX_FLEET_SIZE}척까지 구매할 수 있습니다. 어선은 최대 {MAX_FISHING_SHIPS}척입니다. 운항할 선박은 운항 명령 카드의 배정 선박에서 선택할 수 있습니다.")
    with st.container(border=True):
        st.markdown("### 🚢 신규 선박 구매")
        with st.form("buy_ship_form", clear_on_submit=True):
            new_type = st.selectbox("선박 종류", list(SHIP_TYPES.keys()))
            new_name = st.text_input("선박 이름", placeholder="예: 푸른 항해호")
            st.caption(f"예상 구매 비용: {money_label(ship_price(new_type))} · 연구 완료 {sum(int(v) for v in st.session_state.research_levels.values())}단계 기준 · {SHIP_TYPES[new_type]['description']}")
            submitted = st.form_submit_button("선박 구매", disabled=(st.session_state.phase == "ended"), use_container_width=True, type="primary")
            if submitted:
                buy_ship(new_type, new_name)
                st.rerun()
        # 선박 구매와 관련된 모든 안내는 구매 버튼 바로 아래에 표시한다.
        purchase_feedback = st.session_state.get("purchase_feedback", "")
        if purchase_feedback:
            if st.session_state.get("purchase_feedback_type") == "success":
                st.success(purchase_feedback)
            else:
                st.error(purchase_feedback)

