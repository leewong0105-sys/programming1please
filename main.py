import random
import json
import streamlit as st
import streamlit.components.v1 as components
import plotly.graph_objects as go

# =========================
# 게임 상수
# =========================
START_YEAR = 2026
END_YEAR = 2050
MONEY_SCALE = 1_000_000  # 게임 금액 1단위 = 100만 원
START_MONEY = 30 * MONEY_SCALE  # 시작 자금 3,000만 원
START_EMISSION = 100
SEC_PER_YEAR = 5  # 1년은 5초, 배는 1초에 한 칸 이동

DESTINATIONS = [
    {"name": "도쿄", "years": 1, "income": 15 * MONEY_SCALE, "fee": 2 * MONEY_SCALE},
    {"name": "상하이", "years": 1, "income": 20 * MONEY_SCALE, "fee": 2.5 * MONEY_SCALE},
    {"name": "타이베이", "years": 1, "income": 18 * MONEY_SCALE, "fee": 2 * MONEY_SCALE},
    {"name": "홍콩", "years": 2, "income": 32 * MONEY_SCALE, "fee": 3 * MONEY_SCALE},
    {"name": "싱가포르", "years": 2, "income": 45 * MONEY_SCALE, "fee": 4 * MONEY_SCALE},
    {"name": "로테르담", "years": 3, "income": 80 * MONEY_SCALE, "fee": 3.5 * MONEY_SCALE},
    {"name": "로스앤젤레스", "years": 3, "income": 75 * MONEY_SCALE, "fee": 4 * MONEY_SCALE},
]

EQUIPMENT = [
    {"id": 1, "name": "선체 코팅·프로펠러 개선", "price": 15 * MONEY_SCALE, "reduction": 10, "effect": "배출량 10%p 감축"},
    {"id": 2, "name": "폐열 회수 장치", "price": 25 * MONEY_SCALE, "reduction": 10, "effect": "배출량 10%p 감축"},
    {"id": 3, "name": "지상전력공급장치", "price": 30 * MONEY_SCALE, "reduction": 10, "effect": "배출량 10%p 감축"},
    {"id": 4, "name": "풍력 보조 돛", "price": 40 * MONEY_SCALE, "reduction": 15, "effect": "배출량 15%p 감축"},
    {"id": 5, "name": "LNG 이중연료 엔진", "price": 60 * MONEY_SCALE, "reduction": 15, "effect": "배출량 15%p 감축"},
    {"id": 6, "name": "암모니아·메탄올 엔진", "price": 100 * MONEY_SCALE, "reduction": 20, "effect": "배출량 20%p 감축"},
    {"id": 7, "name": "탄소 포집 장치", "price": 130 * MONEY_SCALE, "reduction": 20, "effect": "배출량 20%p 감축"},
]

TRANSPORT = [
    {"id": 1, "name": "화물 적재함 확장", "price": 20 * MONEY_SCALE, "effect": "모든 항해 수익 +10%"},
    {"id": 2, "name": "대형 선체로 교체", "price": 60 * MONEY_SCALE, "effect": "모든 항해 수익 +25%"},
    {"id": 3, "name": "고속 엔진", "price": 50 * MONEY_SCALE, "effect": "모든 항해 기간 1년 단축 (최소 1년)"},
    {"id": 4, "name": "자율운항선박", "price": 100 * MONEY_SCALE, "effect": "자동 운항 기능 해금"},
]


# 선종별 추가 구매 비용 및 게임용 특수 목적지
# 선종마다 첫 구매 가격을 다르게 설정했다. (게임 밸런스용 금액이며 실제 선박 시세는 아님)
SHIP_TYPES = {
    "기본 화물선": {"base_price": 60 * MONEY_SCALE, "kind": "일반", "description": "일반 항구 간 기본 화물 운송"},
    "컨테이너선": {"base_price": 120 * MONEY_SCALE, "kind": "일반", "description": "컨테이너 화물 운송"},
    "어선": {"base_price": 35 * MONEY_SCALE, "kind": "어선", "description": "어장으로 이동해 조업 후 어획물 판매"},
    "탱크선": {"base_price": 180 * MONEY_SCALE, "kind": "특수", "description": "액체 화물 운송"},
    "케미컬 탱커": {"base_price": 220 * MONEY_SCALE, "kind": "특수", "description": "화학제품 전문 운송"},
    "LNG선": {"base_price": 280 * MONEY_SCALE, "kind": "특수", "description": "액화천연가스 운송"},
}
# 같은 선종을 추가로 살 때마다 해당 선종의 기본 가격 15%만큼 비싸진다.
SHIP_PRICE_STEP_RATE = 0.15

RESEARCH_TECHS = [
    {"id": "ammonia", "name": "암모니아 추진 기술", "stages": [
        {"price": 10 * MONEY_SCALE, "reduction": 3, "label": "1단계 · 기초 연구"},
        {"price": 25 * MONEY_SCALE, "reduction": 5, "label": "2단계 · 실증 연구"},
        {"price": 50 * MONEY_SCALE, "reduction": 7, "label": "3단계 · 상용화 완성"}]},
    {"id": "methanol", "name": "메탄올 추진 기술", "stages": [
        {"price": 12 * MONEY_SCALE, "reduction": 3, "label": "1단계 · 기초 연구"},
        {"price": 28 * MONEY_SCALE, "reduction": 5, "label": "2단계 · 실증 연구"},
        {"price": 55 * MONEY_SCALE, "reduction": 7, "label": "3단계 · 상용화 완성"}]},
    {"id": "capture", "name": "선상 탄소 포집 기술", "stages": [
        {"price": 15 * MONEY_SCALE, "reduction": 2, "label": "1단계 · 원리 연구"},
        {"price": 35 * MONEY_SCALE, "reduction": 5, "label": "2단계 · 장치 실증"},
        {"price": 65 * MONEY_SCALE, "reduction": 7, "label": "3단계 · 상용화 완성"}]},
    {"id": "efficiency", "name": "에너지 효율 개선 기술", "stages": [
        {"price": 8 * MONEY_SCALE, "reduction": 3, "label": "1단계 · 효율 분석"},
        {"price": 20 * MONEY_SCALE, "reduction": 5, "label": "2단계 · 시스템 개선"},
        {"price": 45 * MONEY_SCALE, "reduction": 7, "label": "3단계 · 고효율 완성"}]},
    {"id": "wind", "name": "풍력 보조 추진 기술", "stages": [
        {"price": 10 * MONEY_SCALE, "reduction": 3, "label": "1단계 · 풍력 실험"},
        {"price": 25 * MONEY_SCALE, "reduction": 5, "label": "2단계 · 해상 실증"},
        {"price": 50 * MONEY_SCALE, "reduction": 7, "label": "3단계 · 상용화 완성"}]},
    {"id": "shore_power", "name": "육상 전력 공급 기술", "stages": [
        {"price": 12 * MONEY_SCALE, "reduction": 3, "label": "1단계 · 접속 연구"},
        {"price": 30 * MONEY_SCALE, "reduction": 5, "label": "2단계 · 항만 실증"},
        {"price": 55 * MONEY_SCALE, "reduction": 7, "label": "3단계 · 상용화 완성"}]},
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
    "동해 어장": {"years": 1, "income": 22 * MONEY_SCALE, "fee": 1 * MONEY_SCALE, "coords": (38.0, 132.0),
                  "description": "동해 어장에서 조업 후 귀항해 어획물을 판매합니다."},
    "북태평양 어장": {"years": 2, "income": 42 * MONEY_SCALE, "fee": 2 * MONEY_SCALE, "coords": (40.0, 155.0),
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


def init():
    """모든 페이지에서 공유하는 세션 상태를 초기화한다."""
    defaults = {
        "started": False,
        "phase": "docked",
        "year": START_YEAR,
        "money": START_MONEY,
        "bought_eq": [],
        "bought_tr": [],
        "dest": None,
        "pos": 0,
        "total": 0,
        "auto_on": False,
        "auto_idx": 0,
        "checked": [],
        "history": [{"year": START_YEAR, "money": START_MONEY, "emission": START_EMISSION}],
        "result": None,
        "fail_reason": "",
        "msg": "",
        "balloons_shown": False,
        "weather": None,
        "voyage_income": 0,
        "weather_note": "",
        "selected_port": None,
        "event_pending": None,
        "event_cooldown": 0,
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


def reset_game():
    defaults = {
        "started": False,
        "phase": "docked",
        "year": START_YEAR,
        "money": START_MONEY,
        "bought_eq": [],
        "bought_tr": [],
        "dest": None,
        "pos": 0,
        "total": 0,
        "auto_on": False,
        "auto_idx": 0,
        "checked": [],
        "history": [{"year": START_YEAR, "money": START_MONEY, "emission": START_EMISSION}],
        "result": None,
        "fail_reason": "",
        "msg": "",
        "balloons_shown": False,
        "weather": None,
        "voyage_income": 0,
        "weather_note": "",
        "selected_port": None,
        "event_pending": None,
        "event_cooldown": 0,
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


def money_label(amount):
    """원 단위 금액을 한국어 큰 단위로 읽기 쉽게 표시한다."""
    amount = max(0, int(amount))
    eok = amount // 100_000_000
    man = (amount % 100_000_000) // 10_000
    if eok and man:
        return f"{eok}억 {man:,}만원"
    if eok:
        return f"{eok}억원"
    if man:
        return f"{man:,}만원"
    return f"{amount:,}원"


def current_emission():
    reduction = 0
    levels = st.session_state.get("research_levels", {})
    for tech in RESEARCH_TECHS:
        level = int(levels.get(tech["id"], 0))
        reduction += sum(stage["reduction"] for stage in tech["stages"][:level])
    # 구형 저장 상태와의 호환을 위해 기존 설비 구매 기록도 계산에 포함한다.
    reduction += sum(item["reduction"] for item in EQUIPMENT if item["id"] in st.session_state.get("bought_eq", []))
    return max(0, START_EMISSION - reduction)


def selected_ship():
    fleet = st.session_state.get("fleet", [])
    wanted = st.session_state.get("selected_ship_id", 1)
    return next((ship for ship in fleet if ship["id"] == wanted), fleet[0] if fleet else None)


def ship_price(ship_type):
    count = sum(1 for ship in st.session_state.get("fleet", []) if ship["type"] == ship_type)
    base_price = SHIP_TYPES[ship_type]["base_price"]
    return int(base_price * (1 + SHIP_PRICE_STEP_RATE * count))


def buy_ship(ship_type, ship_name):
    ship_name = (ship_name or "").strip()
    if st.session_state.phase != "docked":
        return
    if not ship_name:
        st.session_state.msg = "선박 이름을 입력해 주세요."
        return
    if any(s["name"].casefold() == ship_name.casefold() for s in st.session_state.fleet):
        st.session_state.msg = "이미 사용 중인 선박 이름입니다."
        return
    price = ship_price(ship_type)
    if st.session_state.money < price:
        st.session_state.msg = "선박을 구매할 자금이 부족합니다."
        return
    ship = {"id": st.session_state.next_ship_id, "name": ship_name, "type": ship_type, "price": price}
    st.session_state.money -= price
    st.session_state.fleet.append(ship)
    st.session_state.next_ship_id += 1
    st.session_state.selected_ship_id = ship["id"]
    if ship_type in ("LNG선", "탱크선", "케미컬 탱커"):
        st.session_state.unlocked_special_ports = sorted(set(
            st.session_state.unlocked_special_ports +
            [name for name, data in SPECIAL_PORTS.items() if ship_type in data["ship_types"]]
        ))
    st.session_state.msg = f"{ship_name} 구매 완료! ({ship_type})"
    add_history()


def research_next_stage(tech_id):
    if st.session_state.phase != "docked":
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


def actual_income(destination_name):
    destination = next((item for item in DESTINATIONS if item["name"] == destination_name), None)
    if destination is None:
        destination = SPECIAL_PORTS.get(destination_name) or FISHING_GROUNDS.get(destination_name)
    if destination is None:
        return 0
    return round(destination["income"] * income_multiplier())


def actual_years(destination_name):
    destination = next((item for item in DESTINATIONS if item["name"] == destination_name), None)
    if destination is None:
        destination = SPECIAL_PORTS.get(destination_name) or FISHING_GROUNDS.get(destination_name)
    if destination is None:
        return 1
    reduction = 1 if 3 in st.session_state.bought_tr else 0
    return max(1, destination["years"] - reduction)


def port_benefit(destination_name):
    """게임용 항만 인센티브를 계산한다. 실제 항만 요금 자체가 아닌 단순화된 게임 규칙이다."""
    emission = current_emission()
    bought_eq = st.session_state.bought_eq
    result = {"discount_percent": 0, "arrival_bonus": 0, "note": ""}

    if destination_name == "싱가포르":
        # MPA Green Ship Programme의 저탄소 연료 기준을 단순화해 반영.
        # 게임에서는 LNG 엔진을 20%, 암모니아·메탄올 엔진을 30% 감면 자격으로 간주한다.
        if 6 in bought_eq:
            result.update(discount_percent=30,
                          note="저탄소 연료 인센티브(게임 규칙): 정박비 30% 감면")
        elif 5 in bought_eq:
            result.update(discount_percent=20,
                          note="LNG 연료 인센티브(게임 규칙): 정박비 20% 감면")
        else:
            result["note"] = "감면 조건: LNG 이중연료 엔진 또는 암모니아·메탄올 엔진 필요"

    elif destination_name == "로테르담":
        # 일반 외항선의 Green Award 자격을 자동으로 단정하지 않고, 게임용 환경 성과 조건을 별도로 둔다.
        if emission <= 30 and len(bought_eq) >= 3:
            result.update(discount_percent=15,
                          note="환경 성과 인센티브(게임 규칙): 정박비 15% 감면")
        else:
            result["note"] = "게임 내 감면 조건: 탄소 감축 설비 3개 이상 구매 및 배출량 30% 이하"

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
    fee = round(int(destination["fee"]) * (100 - benefit["discount_percent"]) / 100)
    return fee, benefit


def add_history():
    st.session_state.history.append({
        "year": int(st.session_state.year),
        "money": int(st.session_state.money),
        "emission": int(current_emission()),
    })


def start_voyage(destination_name):
    if st.session_state.phase != "docked":
        return
    duration = actual_years(destination_name)
    weather_options = [
        {"name": "순풍", "seconds": -1, "income_rate": 1.05,
         "description": "순풍을 만났습니다! 항해가 1초 빨라지고 운임이 5% 증가합니다."},
        {"name": "잔잔한 바다", "seconds": 0, "income_rate": 1.0,
         "description": "바다가 잔잔합니다. 항해와 운임에 변화가 없습니다."},
        {"name": "짙은 안개", "seconds": 1, "income_rate": 1.0,
         "description": "짙은 안개로 항해가 1초 지연됩니다."},
        {"name": "폭풍", "seconds": 2, "income_rate": 0.90,
         "description": "폭풍을 만났습니다! 항해가 2초 지연되고 운임이 10% 감소합니다."},
    ]
    weather = random.choices(weather_options, weights=[2, 3, 3, 3], k=1)[0]  # 악천후가 조금 더 자주 발생하도록 조정
    st.session_state.dest = destination_name
    st.session_state.pos = 0
    st.session_state.total = max(1, duration * SEC_PER_YEAR + weather["seconds"])
    st.session_state.weather = weather["name"]
    st.session_state.weather_note = weather["description"]
    st.session_state.voyage_income = round(actual_income(destination_name) * weather["income_rate"])
    st.session_state.port_fee_paid = 0
    st.session_state.returning_income = st.session_state.voyage_income
    st.session_state.event_pending = None
    st.session_state.event_cooldown = 3  # 출항 직후에는 이벤트가 바로 뜨지 않음
    st.session_state.phase = "sailing"
    st.session_state.msg = weather["description"]


def start_auto_voyage():
    if st.session_state.phase != "docked" or not st.session_state.auto_on:
        return
    destination_name = AUTO_ROUTE[st.session_state.auto_idx % len(AUTO_ROUTE)]
    start_voyage(destination_name)


def pause_voyage():
    if st.session_state.phase == "sailing":
        st.session_state.phase = "returning"
        st.session_state.msg = "회항을 시작합니다."


def buy_equipment(item_id):
    if st.session_state.phase != "docked":
        return
    item = next(item for item in EQUIPMENT if item["id"] == item_id)
    if item_id in st.session_state.bought_eq or st.session_state.money < item["price"]:
        return
    st.session_state.money -= item["price"]
    st.session_state.bought_eq.append(item_id)
    add_history()
    st.session_state.msg = f"{item['name']} 구매 완료!"
    if current_emission() == 0:
        st.session_state.phase = "ended"
        st.session_state.result = "success"
        st.session_state.msg = "모든 탄소 배출을 감축했습니다. 탄소중립 달성!"


def buy_transport(item_id):
    if st.session_state.phase != "docked":
        return
    item = next(item for item in TRANSPORT if item["id"] == item_id)
    if item_id in st.session_state.bought_tr or st.session_state.money < item["price"]:
        return
    st.session_state.money -= item["price"]
    st.session_state.bought_tr.append(item_id)
    st.session_state.msg = f"{item['name']} 구매 완료!"
    add_history()


def arrive():
    """해외 항구 도착: 정박비를 내고 부산으로 귀항한다. 운임은 귀항 완료 후 지급."""
    destination_name = st.session_state.dest
    if destination_name is None:
        st.session_state.phase = "docked"
        return

    destination = next((item for item in DESTINATIONS if item["name"] == destination_name), None)
    if destination is None:
        destination = SPECIAL_PORTS.get(destination_name) or FISHING_GROUNDS.get(destination_name)
    if destination is None:
        st.session_state.phase = "docked"
        return
    # 항만 혜택을 실제 게임 자금 계산에 반영한다. 요금·보상은 게임용 단순화 수치다.
    if destination_name in [d["name"] for d in DESTINATIONS]:
        port_fee, benefit = discounted_port_fee(destination_name)
    else:
        port_fee = int(destination.get("fee", 0))
        benefit = {"discount_percent": 0, "arrival_bonus": 0, "note": destination.get("description", "게임용 목적지")}
    fee_note = benefit["note"]
    st.session_state.money -= port_fee
    st.session_state.port_fee_paid += port_fee
    if benefit["arrival_bonus"]:
        st.session_state.money += int(benefit["arrival_bonus"])
        fee_note += f" · 항만 친환경 보너스 {money_label(benefit['arrival_bonus'])} 지급"
    st.session_state.year = min(st.session_state.year + actual_years(destination_name), END_YEAR)
    add_history()

    # 귀항도 별도의 출항이므로 날씨를 새로 판정한다.
    return_weather_options = [
        {"name": "순풍", "seconds": -1, "income_rate": 1.00,
         "description": "귀항 중 순풍입니다. 부산으로 조금 빠르게 돌아갑니다."},
        {"name": "잔잔한 바다", "seconds": 0, "income_rate": 1.00,
         "description": "귀항 중 바다가 잔잔합니다."},
        {"name": "짙은 안개", "seconds": 1, "income_rate": 1.00,
         "description": "귀항 중 짙은 안개로 항해가 지연됩니다."},
        {"name": "폭풍", "seconds": 2, "income_rate": 0.90,
         "description": "귀항 중 폭풍을 만났습니다. 항해가 지연되고 화물 운임이 10% 감소합니다."},
    ]
    return_weather = random.choices(return_weather_options, weights=[2, 3, 3, 3], k=1)[0]
    st.session_state.weather = return_weather["name"]
    st.session_state.weather_note = return_weather["description"]
    if return_weather["income_rate"] < 1:
        st.session_state.returning_income = round(st.session_state.returning_income * return_weather["income_rate"])
    st.session_state.phase = "returning"
    st.session_state.pos = 0
    st.session_state.total = max(1, actual_years(destination_name) * SEC_PER_YEAR + return_weather["seconds"])
    st.session_state.event_pending = None
    st.session_state.event_cooldown = 2
    st.session_state.voyage_event_count = 0
    st.session_state.msg = f"{destination_name} 도착! 정박비 {money_label(port_fee)} 지출. 귀항 날씨: {return_weather['name']}. {fee_note} 운임은 부산 도착 후 정산됩니다."


def settle_return():
    """부산항 귀항 후 운임과 비용을 정산하고 다음 운항을 준비한다."""
    destination_name = st.session_state.dest
    income = int(st.session_state.returning_income or 0)
    busan_fee = 1 * MONEY_SCALE
    st.session_state.money -= busan_fee
    st.session_state.money += income
    st.session_state.year = min(st.session_state.year + actual_years(destination_name), END_YEAR)
    add_history()
    emission = current_emission()
    passed_messages = []

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
            passed_messages.append(f"{checkpoint_year}년 점검 통과!")

    if st.session_state.year >= END_YEAR:
        st.session_state.phase = "ended"
        if emission == 0:
            st.session_state.result = "success"
        else:
            st.session_state.result = "fail"
            st.session_state.fail_reason = f"2050년 최종 점검 실패: 배출량 {emission}% (기준 0%)"
        st.session_state.msg = " ".join(passed_messages)
        return

    if st.session_state.auto_on:
        st.session_state.auto_idx = (st.session_state.auto_idx + 1) % len(AUTO_ROUTE)
    st.session_state.msg = " ".join(passed_messages + [
        f"부산항 귀항 완료! 운임 {money_label(income)} 지급, 부산항 정박비 {money_label(busan_fee)} 차감."
    ])
    st.session_state.phase = "docked"
    st.session_state.dest = None
    st.session_state.pos = 0
    st.session_state.total = 0
    st.session_state.weather = None
    st.session_state.weather_note = ""
    st.session_state.voyage_income = 0
    st.session_state.returning_income = 0
    st.session_state.port_fee_paid = 0
    st.session_state.event_pending = None


def finish_return():
    settle_return()


def trigger_random_event():
    """시연용 이벤트를 발생시킨다. 선택 결과는 성공/실패 판정에 따라 달라질 수 있다."""
    events = [
        {
            "title": "긴급 운송 계약",
            "description": "긴급 화물을 추가 운송하면 보너스를 받을 수 있습니다. 일정에 맞추지 못하면 위약금이 발생합니다.",
            "choices": [
                {"label": "계약 수락", "success_chance": 0.75, "success_delta": 8 * MONEY_SCALE,
                 "fail_delta": -3 * MONEY_SCALE, "success": "긴급 운송 계약 성공! 보너스 800만원을 받았습니다.",
                 "failure": "납기 지연으로 위약금 300만원을 냈습니다."},
                {"label": "거절", "delta": 0, "result": "계약을 거절하고 기존 항해를 계속합니다."},
            ],
        },
        {
            "title": "엔진 이상 경고",
            "description": "지금 점검하면 비용이 들지만, 방치하면 더 큰 손실이 날 수 있습니다.",
            "choices": [
                {"label": "긴급 점검 (-300만원)", "delta": -3 * MONEY_SCALE,
                 "result": "엔진을 점검했습니다. 큰 고장을 예방했습니다."},
                {"label": "운항 강행", "success_chance": 0.45, "success_delta": 0,
                 "fail_delta": -8 * MONEY_SCALE, "success": "다행히 엔진이 버텼습니다. 추가 비용 없이 항해합니다.",
                 "failure": "엔진 고장! 수리비 800만원을 부담했습니다."},
            ],
        },
        {
            "title": "해적 위험 경보",
            "description": "의심 선박이 감지됐습니다. 안전을 확보할지, 위험을 감수할지 선택하세요.",
            "choices": [
                {"label": "보안 호위 요청 (-200만원)", "delta": -2 * MONEY_SCALE,
                 "result": "호위 서비스를 이용해 안전하게 통과했습니다."},
                {"label": "항로 유지", "success_chance": 0.50, "success_delta": 4 * MONEY_SCALE,
                 "fail_delta": -10 * MONEY_SCALE, "success": "위험을 무사히 통과했습니다. 일정 보너스 400만원을 얻었습니다.",
                 "failure": "해적 피해로 화물과 장비 일부가 손상됐습니다. 손실 1,000만원이 발생했습니다."},
            ],
        },
    ]
    event = random.choice(events).copy()
    st.session_state.event_pending = event


def resolve_event(choice_index):
    event = st.session_state.event_pending
    if not event:
        return
    choice = event["choices"][choice_index]

    if "success_chance" in choice:
        if random.random() < choice["success_chance"]:
            delta = int(choice.get("success_delta", 0))
            result = choice["success"]
        else:
            delta = int(choice.get("fail_delta", 0))
            result = choice["failure"]
    else:
        delta = int(choice.get("delta", 0))
        result = choice.get("result", "선택을 적용했습니다.")

    # 비용 선택 시 보유 자금보다 더 많이 빠져나가지 않도록 제한한다.
    if delta < 0:
        delta = -min(st.session_state.money, abs(delta))
    st.session_state.money += delta
    st.session_state.event_log.append(f"{event['title']}: {result}")
    st.session_state.msg = result
    st.session_state.event_pending = None
    st.session_state.event_cooldown = 2
    st.session_state.voyage_event_count = st.session_state.get("voyage_event_count", 0) + 1
    add_history()


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
        marker={"size": [16 if name == "부산" else 20 for name in pin_names],
                "color": ["#ff6b6b" if name == "부산" else "#e2bd67" for name in pin_names]},
        text=["⚓ 부산" if name == "부산" else f"📍 {name}" for name in pin_names],
        textposition="top right",
        textfont={"color": "#ffffff", "size": 12},
        customdata=pin_names,
        name="항구 핀",
        hovertemplate="%{customdata}<br>클릭해서 항구 정보 보기<extra></extra>",
    ))

    dest_name = st.session_state.dest
    if dest_name in SEA_ROUTES:
        route = SEA_ROUTES[dest_name]
        total = max(1, int(st.session_state.total))
        fraction = min(1.0, max(0.0, st.session_state.pos / total))
        if st.session_state.phase == "returning":
            fraction = 1.0 - fraction
        ship_lat, ship_lon = route_position(route, fraction)
        route_lats = [p[0] for p in route]
        route_lons = [p[1] for p in route]
        fig.add_trace(go.Scattermap(
            lat=route_lats, lon=route_lons, mode="lines",
            line={"width": 4, "color": "#42c7d9"}, name="바닷길", hoverinfo="skip",
        ))
        # 경유점을 따라 이동한 항로를 표시
        travelled_route = []
        for i, point in enumerate(route):
            travelled_route.append(point)
            if i < len(route) - 1:
                seg_start = sum((((route[j+1][0]-route[j][0])**2 + (route[j+1][1]-route[j][1])**2)**0.5) for j in range(i))
                seg_len = ((route[i+1][0]-route[i][0])**2 + (route[i+1][1]-route[i][1])**2)**0.5
                if fraction * sum((((route[j+1][0]-route[j][0])**2 + (route[j+1][1]-route[j][1])**2)**0.5) for j in range(len(route)-1)) <= seg_start + seg_len:
                    travelled_route.append((ship_lat, ship_lon))
                    break
        fig.add_trace(go.Scattermap(
            lat=[p[0] for p in travelled_route], lon=[p[1] for p in travelled_route],
            mode="lines", line={"width": 5, "color": "#f2c14e"}, name="이동한 바닷길", hoverinfo="skip",
        ))
        fig.add_trace(go.Scattermap(
            lat=[ship_lat], lon=[ship_lon], mode="markers+text",
            marker={"size": 18, "color": "#ff6b6b", "symbol": "circle"},
            text=["🚢 선박"], textposition="bottom right",
            textfont={"color": "#ffffff", "size": 12}, name="현재 선박 위치",
            hovertemplate="현재 선박 위치<extra></extra>",
        ))

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

if st.session_state.phase == "ended":
    if st.session_state.result == "success":
        st.success("🎉 성공! 탄소중립 목표를 달성했습니다.")
        st.write("선박을 개선해 배출량 0%를 달성했습니다. 지속 가능한 해운을 위한 항해가 성공적으로 끝났습니다.")
        if not st.session_state.balloons_shown:
            st.balloons()
            st.session_state.balloons_shown = True
    else:
        st.error("항해 실패")
        st.write(st.session_state.fail_reason or "점검 기준을 충족하지 못했습니다.")
    c1, c2, c3 = st.columns(3)
    c1.metric("최종 연도", f"{st.session_state.year}년")
    c2.metric("보유 자금", money_label(st.session_state.money))
    c3.metric("현재 배출량", f"{current_emission()}%")
    if st.button("다시 시작", key="restart_game", type="primary", use_container_width=True):
        reset_game()
        st.rerun()
    st.stop()

emission = current_emission()
c1, c2, c3 = st.columns(3)
c1.metric("현재 연도", f"{st.session_state.year}년")
c2.metric("보유 자금", money_label(st.session_state.money))
c3.metric("배출량", f"{emission}%")

with st.expander("🏢 회사 및 선단 관리", expanded=True):
    st.markdown(
        f"**{st.session_state.company_name}**  ·  선주 **{st.session_state.captain_name}**",
        help="회사명과 선주 이름은 로그인 화면에서 설정합니다."
    )
    st.markdown("**보유 선박**")
    for ship in st.session_state.fleet:
        st.write(f"🚢 **{ship['name']}** · {ship['type']} · 구매가 {money_label(ship['price'])}")
    st.selectbox(
        "관리할 선박",
        options=[ship["id"] for ship in st.session_state.fleet],
        format_func=lambda sid: next(s["name"] + " · " + s["type"] for s in st.session_state.fleet if s["id"] == sid),
        key="selected_ship_id",
    )
    with st.form("buy_ship_form", clear_on_submit=True):
        st.markdown("**신규 선박 구매**")
        new_type = st.selectbox("선박 종류", list(SHIP_TYPES.keys()))
        new_name = st.text_input("선박 이름", placeholder="예: 푸른 항해호")
        st.caption(f"예상 구매 비용: {money_label(ship_price(new_type))} · {SHIP_TYPES[new_type]['description']}")
        submitted = st.form_submit_button("선박 구매", disabled=st.session_state.phase != "docked", use_container_width=True)
        if submitted:
            buy_ship(new_type, new_name)
            st.rerun()

next_checkpoint = next((year for year in sorted(CHECKPOINTS) if year not in st.session_state.checked), None)
if next_checkpoint is None:
    st.info("모든 중간 점검을 통과했습니다.")
else:
    st.markdown(f"**다음 점검: {next_checkpoint}년 (배출량 {CHECKPOINTS[next_checkpoint]}% 이하)**")

if st.session_state.msg:
    st.success(st.session_state.msg)
    st.session_state.msg = ""

# 항해 진행은 fragment에서만 1초마다 갱신한다.
# 지도 렌더링은 fragment 바깥에 두어, 매초 iframe/지도 인스턴스가 재생성되지 않게 한다.
@st.fragment(run_every="1s")
def advance_voyage_clock():
    if st.session_state.phase not in ("sailing", "returning") or st.session_state.event_pending:
        return

    if st.session_state.event_cooldown > 0:
        st.session_state.event_cooldown -= 1
    elif random.random() < 0.12:
        trigger_random_event()
        st.rerun()
        return

    st.session_state.pos += 1
    if st.session_state.pos >= st.session_state.total:
        if st.session_state.phase == "sailing":
            arrive()
        else:
            finish_return()
        st.rerun()

advance_voyage_clock()

# 이벤트 선택창은 반드시 지도 바로 위에 표시한다.
if st.session_state.event_pending and st.session_state.phase in ("sailing", "returning"):
    event = st.session_state.event_pending
    with st.container(border=True):
        st.subheader(f"⚠️ 긴급 상황: {event['title']}")
        st.write(event["description"])
        event_cols = st.columns(len(event["choices"]))
        for i, choice in enumerate(event["choices"]):
            event_cols[i].button(
                choice["label"], key=f"event_choice_{event['title']}_{i}",
                use_container_width=True, on_click=resolve_event, args=(i,)
            )

st.subheader("실제 지도와 항로")
st.caption("항해 중에는 지도 배경과 항구 핀을 유지하고 선박만 이동합니다. 목적지 선택은 정박 중 지도에서 할 수 있습니다.")

if st.session_state.phase in ("sailing", "returning") and st.session_state.dest in SEA_ROUTES:
    # 단일 main.py 안에 지도 HTML/JavaScript를 포함한다. 별도 파일은 필요 없다.
    map_config = {
        "ports": [
            {"name": name, "lat": coords[0], "lon": coords[1]}
            for name, coords in PORT_COORDS.items()
        ],
        "route": SEA_ROUTES[st.session_state.dest],
        "destination": st.session_state.dest,
        "phase": st.session_state.phase,
        "pos": int(st.session_state.pos),
        "total": max(1, int(st.session_state.total)),
        "paused": bool(st.session_state.event_pending),
    }
    config_json = json.dumps(map_config, ensure_ascii=False).replace("</", "<\\/")
    map_html = r'''<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<style>
html,body{margin:0;padding:0;background:#071521;font-family:sans-serif}#map{height:600px;width:100%;border-radius:10px;overflow:hidden}
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
 const route=C.route||[];
 const routeLine=L.polyline(route,{color:'#42c7d9',weight:4,opacity:.95}).addTo(map);
 const travelled=L.polyline([],{color:'#f2c14e',weight:5,opacity:.95}).addTo(map);
 const shipIcon=L.divIcon({className:'ship-icon-wrap',html:'<div class="ship-icon">🚢</div>',iconSize:[34,34],iconAnchor:[17,17]});
 const ship=L.marker(route[0]||[35.1796,129.0756],{icon:shipIcon,interactive:false,zIndexOffset:1000}).addTo(map);
 if(route.length>1) map.fitBounds(L.latLngBounds(route),{padding:[35,35],maxZoom:5,animate:false});
 function pointAt(f){
   if(route.length<2)return route[0]||[35.1796,129.0756];
   const lens=[];let sum=0;for(let i=0;i<route.length-1;i++){const d=Math.hypot(route[i+1][0]-route[i][0],route[i+1][1]-route[i][1]);lens.push(d);sum+=d;}
   let target=Math.max(0,Math.min(1,f))*sum;
   for(let i=0;i<lens.length;i++){if(target<=lens[i]||i===lens.length-1){const t=lens[i]?target/lens[i]:0;return [route[i][0]+(route[i+1][0]-route[i][0])*t,route[i][1]+(route[i+1][1]-route[i][1])*t];}target-=lens[i];}
   return route[route.length-1];
 }
 function partialPath(progress,returning){
   const f=returning?1-progress:progress;const p=pointAt(f);
   if(!returning){const out=[route[0]];for(let i=1;i<route.length;i++){const a=route[i-1],b=route[i];const fa=distanceFraction(i-1),fb=distanceFraction(i);if(f>=fb)out.push(b);else if(f>fa){out.push(p);break;}else break;}if(out.length===1&&f>0)out.push(p);else if(out[out.length-1]!==p && f<1)out.push(p);return out;}
   const out=[p];for(let i=route.length-2;i>=0;i--){if(distanceFraction(i)<f)out.push(route[i]);}return out;
 }
 const fractions=[0];let totalLen=0;for(let i=0;i<route.length-1;i++){totalLen+=Math.hypot(route[i+1][0]-route[i][0],route[i+1][1]-route[i][1]);fractions.push(totalLen);}
 function distanceFraction(i){return totalLen?fractions[i]/totalLen:0;}
 const total=Math.max(1,Number(C.total)||1);let base= Math.max(0,Math.min(total,Number(C.pos)||0));let started=performance.now();let paused=!!C.paused;
 function draw(progress){const f=C.phase==='returning'?1-progress:progress;ship.setLatLng(pointAt(f));travelled.setLatLngs(partialPath(progress,C.phase==='returning'));}
 function tick(now){let progress=base/total;if(!paused)progress=Math.min(1,(base+(now-started)/1000)/total);draw(progress);if(!paused&&progress<1)requestAnimationFrame(tick);}
 draw(base/total);if(!paused)requestAnimationFrame(tick);
 setTimeout(()=>map.invalidateSize(),80);
})();
</script></body></html>'''.replace("__CONFIG__", config_json)
    components.html(map_html, height=620, scrolling=False)
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
            port_names = ["부산"] + [d["name"] for d in DESTINATIONS]
            if point_index is not None and 0 <= int(point_index) < len(port_names):
                picked = port_names[int(point_index)]
                st.session_state.selected_port = None if picked == "부산" else picked
    except (AttributeError, TypeError, KeyError, ValueError):
        pass

if st.session_state.phase in ("sailing", "returning") and st.session_state.weather_note:
    st.info(f"🌦️ 해상 기상: {st.session_state.weather} — {st.session_state.weather_note}")
if st.session_state.phase == "sailing":
    st.write(f"🚢 항해 중 · {st.session_state.dest} 방향 · {st.session_state.pos}/{st.session_state.total}초")
elif st.session_state.phase == "returning":
    st.write(f"↩️ 부산으로 귀항 중 · {st.session_state.pos}/{st.session_state.total}초")
else:
    st.write("⚓ 부산항 정박 중 — 목적지를 선택해 출항하세요.")


st.subheader("항구 정보")
selected_port = st.session_state.selected_port
can_choose = st.session_state.phase == "docked"
ship = selected_ship()
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
        "로테르담": "항만은 Green Award 및 환경 데이터·선박별 조건에 따른 인센티브를 운영합니다. 실제 해상 운항 선박의 할인은 선종과 요금 구성요소 등 별도 자격이 필요하므로, 게임은 친환경 설비와 배출량을 이용한 단순화 규칙을 사용합니다.",
        "타이베이": "대만 북부의 주요 항만입니다.",
        "홍콩": "아시아의 주요 항만이자 환적 거점입니다.",
        "로스앤젤레스": "Port of Los Angeles의 ESI 프로그램은 등록된 선박의 ESI 점수 구간에 따라 입항별 인센티브를 제공합니다. 게임은 실제 ESI 점수를 계산하지 않고 배출량을 시연용 대체 기준으로 사용합니다.",
    }
    if selected_port in [d["name"] for d in DESTINATIONS]:
        current_fee, current_benefit = discounted_port_fee(selected_port)
    else:
        current_fee = int(destination.get("fee", 0))
        current_benefit = {"discount_percent": 0, "arrival_bonus": 0, "note": destination.get("description", "게임용 목적지")}
    suffix = " 어장" if selected_port in FISHING_GROUNDS else " 항구"
    st.markdown(f"### 📍 {selected_port}{suffix}")
    info_cols = st.columns(3)
    info_cols[0].metric("예상 항해 기간", f"{years}년")
    info_cols[1].metric("예상 운임", money_label(income))
    info_cols[2].metric("적용 정박비", money_label(current_fee),
                        delta=(f"{current_benefit['discount_percent']}% 감면" if current_benefit["discount_percent"] else None),
                        delta_color="normal")
    st.write(features.get(selected_port, destination.get("description", "게임용 목적지입니다.")))
    st.info(f"**게임 내 혜택:** {current_benefit['note'] or '현재 적용 가능한 별도 혜택 없음'}")
    official_sources = {
        "싱가포르": "https://www.mpa.gov.sg/finance-e-services/tariff-fees-and-charges/ocean-going-vessels/port-dues-concessions",
        "로테르담": "https://www.portofrotterdam.com/en/sea-shipping/seaport-dues/green-award-discount",
        "로스앤젤레스": "https://portoflosangeles.org/environment/air-quality/environmental-ship-index",
    }
    if selected_port in official_sources:
        st.markdown(f"[항만 공식 출처 보기]({official_sources[selected_port]})")
    st.caption(f"기본 게임 정박비 {money_label(destination['fee'])} · 혜택 적용 후 정박비 {money_label(current_fee)}. 부산항 정박비 {money_label(1 * MONEY_SCALE)}는 별도이며 운임은 부산 귀항 후 지급됩니다. 실제 항만 요금과 자격 조건을 그대로 계산하는 시스템이 아니라, 공식 제도를 참고해 단순화한 게임 규칙입니다.")
    departure_label = f"🎣 {selected_port} 조업 출항" if selected_port in FISHING_GROUNDS else f"🚢 {selected_port}로 출항"
    if st.button(departure_label, key="selected_port_depart", disabled=not can_choose, use_container_width=True):
        start_voyage(selected_port)
        st.rerun()
else:
    st.info("지도에서 목적지 핀을 선택하거나 아래 목록에서 현재 선박이 이용할 수 있는 목적지를 선택하세요.")
    if available_destinations:
        manual_port = st.selectbox("목적항 / 어장 선택", available_destinations, key="manual_destination")
        if st.button("목적지 정보 보기", key="manual_destination_pick", disabled=not can_choose, use_container_width=True):
            st.session_state.selected_port = manual_port
            st.rerun()
    else:
        st.warning("이 선박이 이용할 수 있는 특수 목적지가 없습니다.")

if 4 in st.session_state.bought_tr:
    st.toggle("자동 운항", key="auto_on", disabled=st.session_state.phase != "docked",
              help="항해 사이에 다음 항로를 직접 출발시킬 수 있습니다.")
    if st.session_state.auto_on:
        next_auto_dest = AUTO_ROUTE[st.session_state.auto_idx % len(AUTO_ROUTE)]
        st.caption(f"다음 자동 항로: {next_auto_dest}")
        st.button("▶ 다음 자동 항해 출발", key="start_auto_voyage",
                  disabled=st.session_state.phase != "docked", use_container_width=True,
                  on_click=start_auto_voyage)

if st.session_state.event_log:
    with st.expander("📜 최근 해상 사건 기록"):
        for event_line in st.session_state.event_log[-8:][::-1]:
            st.write(f"• {event_line}")

st.subheader("업그레이드 상점")
eq_tab, tr_tab = st.tabs(["탄소 기술 연구", "운송 강화"])
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
                    disabled=(st.session_state.phase != "docked" or st.session_state.money < stage["price"]),
                    use_container_width=True, on_click=research_next_stage, args=(tech["id"],)
                )
            else:
                st.success("기술 연구 완료")
with tr_tab:

    for item in TRANSPORT:
        bought = item["id"] in st.session_state.bought_tr
        enough_money = st.session_state.money >= item["price"]
        row = st.columns([4, 1, 1])
        with row[0]:
            st.markdown(f"**{item['name']}**")
            st.caption(f"{item['effect']} · 가격 {money_label(item['price'])}")
            if not bought and not enough_money:
                st.caption("자금 부족")
        with row[1]:
            if bought:
                st.button("구매 완료", key=f"tr_done_{item['id']}", disabled=True, use_container_width=True)
            else:
                st.button("구매", key=f"tr_{item['id']}",
                          disabled=(st.session_state.phase != "docked" or not enough_money),
                          use_container_width=True, on_click=buy_transport, args=(item["id"],))
        with row[2]:
            st.write(money_label(item["price"]))
        st.divider()

