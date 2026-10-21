import time
import random
from pathlib import Path
import streamlit as st
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
    {"name": "도쿄", "years": 1, "income": 15 * MONEY_SCALE},
    {"name": "상하이", "years": 1, "income": 20 * MONEY_SCALE},
    {"name": "싱가포르", "years": 2, "income": 45 * MONEY_SCALE},
    {"name": "로테르담", "years": 3, "income": 80 * MONEY_SCALE},
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

CHECKPOINTS = {2030: 80, 2040: 30, 2050: 0}
AUTO_ROUTE = ["로테르담", "싱가포르", "상하이", "도쿄"]

# 실제 지리 좌표: 위도, 경도
PORT_COORDS = {
    "부산": (35.1796, 129.0756),
    "도쿄": (35.6762, 139.6503),
    "상하이": (31.2304, 121.4737),
    "싱가포르": (1.3521, 103.8198),
    "로테르담": (51.9244, 4.4777),
}

# 대륙을 가로지르지 않도록 바다를 따라가는 단순화 항로 경유점
SEA_ROUTES = {
    "도쿄": [PORT_COORDS["부산"], (34.5, 132.0), (34.8, 136.5), PORT_COORDS["도쿄"]],
    "상하이": [PORT_COORDS["부산"], (34.2, 127.0), (32.5, 125.5), PORT_COORDS["상하이"]],
    "싱가포르": [PORT_COORDS["부산"], (30.0, 125.0), (25.0, 121.0), (20.0, 117.0), (14.0, 112.0), (8.0, 108.0), PORT_COORDS["싱가포르"]],
    "로테르담": [PORT_COORDS["부산"], (30.0, 125.0), (22.0, 120.0), (15.0, 115.0), (8.0, 105.0), (1.5, 103.5), (-5.0, 105.0), (-10.0, 110.0), (-20.0, 95.0), (-30.0, 65.0), (-25.0, 35.0), (-10.0, 15.0), (5.0, 5.0), (20.0, -5.0), (35.0, -10.0), (43.0, -8.0), (48.0, -3.0), PORT_COORDS["로테르담"]],
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
    reduction = sum(item["reduction"] for item in EQUIPMENT if item["id"] in st.session_state.bought_eq)
    return max(0, START_EMISSION - reduction)


def income_multiplier():
    multiplier = 1.0
    if 1 in st.session_state.bought_tr:
        multiplier += 0.10
    if 2 in st.session_state.bought_tr:
        multiplier += 0.25
    return multiplier


def actual_income(destination_name):
    destination = next(item for item in DESTINATIONS if item["name"] == destination_name)
    return round(destination["income"] * income_multiplier())


def actual_years(destination_name):
    destination = next(item for item in DESTINATIONS if item["name"] == destination_name)
    reduction = 1 if 3 in st.session_state.bought_tr else 0
    return max(1, destination["years"] - reduction)


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
    destination_name = st.session_state.dest
    if destination_name is None:
        st.session_state.phase = "docked"
        return

    duration = actual_years(destination_name)
    voyage_income = st.session_state.voyage_income or actual_income(destination_name)
    st.session_state.money += voyage_income
    st.session_state.year = min(st.session_state.year + duration, END_YEAR)
    add_history()
    emission = current_emission()
    passed_messages = []

    for checkpoint_year in sorted(CHECKPOINTS):
        if st.session_state.year >= checkpoint_year and checkpoint_year not in st.session_state.checked:
            limit = CHECKPOINTS[checkpoint_year]
            if emission > limit:
                st.session_state.phase = "ended"
                st.session_state.result = "fail"
                st.session_state.fail_reason = (
                    f"{checkpoint_year}년 점검 실패: 배출량 {emission}% (기준 {limit}% 이하)"
                )
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

    st.session_state.phase = "docked"
    st.session_state.dest = None
    st.session_state.pos = 0
    st.session_state.total = 0
    if st.session_state.auto_on:
        st.session_state.auto_idx = (st.session_state.auto_idx + 1) % len(AUTO_ROUTE)
    arrival_message = f"{destination_name} 도착! 운임 {money_label(voyage_income)}을 받았습니다."
    st.session_state.msg = " ".join(passed_messages + [arrival_message]) if passed_messages else arrival_message
    st.session_state.weather = None
    st.session_state.voyage_income = 0


def finish_return():
    st.session_state.phase = "docked"
    st.session_state.dest = None
    st.session_state.pos = 0
    st.session_state.total = 0
    st.session_state.msg = "회항 완료. 운임은 받지 않았고 연도도 그대로입니다."


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
        zoom = 3 if dest_name == "로테르담" else (4 if dest_name == "싱가포르" else 5)
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
    .stApp { background-color: #071521; color: #f3f0e7; }
    h1, h2, h3, p, label, div, span { color: #f3f0e7; }
    [data-testid="stMetric"] { background: #102536; border: 1px solid #29485b; padding: 14px; border-radius: 12px; }
    .stButton > button { color: #ffffff !important; background: #17465a; border: 1px solid #47788b; border-radius: 9px; }
    .stButton > button:disabled { color: #a6b3bb !important; background: #253541; }
    div[data-baseweb="tab-list"] button { color: #f3f0e7 !important; }

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

st.title("🚢 탄소중립 선박 경영")
st.caption("수익을 얻어 선박을 개선하고, 2050년 탄소중립을 달성하세요.")
if not st.session_state.started:
    st.markdown("## 바다를 항해하며 탄소중립에 도전하세요")
    st.write("**목표:** 목적지로 화물을 운송해 돈을 벌고, 탄소 감축 설비를 구매해 배출량을 0%로 만드세요.")
    st.write("**중간 점검:** 2030년 배출량 80% 이하, 2040년 30% 이하, 2050년 0%를 달성해야 합니다.")
    st.write("**조작법:** 목적지를 선택해 항해하고, 도착할 때마다 번 돈으로 설비와 운송 기능을 강화하세요.")
    st.info("게임에서는 이해를 돕기 위해 감축량과 수치를 단순화했습니다.")
    if st.button("게임 시작", key="start_game", type="primary", use_container_width=True):
        st.session_state.started = True
        st.session_state.phase = "docked"
        st.rerun()
    st.stop()

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
next_checkpoint = next((year for year in sorted(CHECKPOINTS) if year not in st.session_state.checked), None)
if next_checkpoint is None:
    st.info("모든 중간 점검을 통과했습니다.")
else:
    st.markdown(f"**다음 점검: {next_checkpoint}년 (배출량 {CHECKPOINTS[next_checkpoint]}% 이하)**")

if st.session_state.msg:
    st.success(st.session_state.msg)
    st.session_state.msg = ""

st.subheader("실제 지도와 항로")
st.caption("실제 지리 좌표와 OpenStreetMap 지도를 사용합니다. 선박은 항해 중 지도 위에서 이동하며, 매번 출항할 때 해상 기상이 무작위로 결정됩니다.")
map_event = st.plotly_chart(
    make_route_map(), use_container_width=True, key="live_route_map",
    on_select="rerun", selection_mode="points",
)
# 지도에서 목적지 핀을 선택하면 아래에 해당 항구 정보가 표시된다.
try:
    selected_points = map_event.selection.points
    if selected_points:
        point = selected_points[-1]
        point_index = point.get("point_index", point.get("pointIndex"))
        if point_index is not None and 0 <= int(point_index) < len(["부산"] + [d["name"] for d in DESTINATIONS]):
            picked = (["부산"] + [d["name"] for d in DESTINATIONS])[int(point_index)]
            if picked != "부산":
                st.session_state.selected_port = picked
except (AttributeError, TypeError, KeyError, ValueError):
    pass
if st.session_state.phase in ("sailing", "returning") and st.session_state.weather_note:
    st.info(f"🌦️ 해상 기상: {st.session_state.weather} — {st.session_state.weather_note}")
if st.session_state.phase == "sailing":
    st.write(f"🚢 항해 중 · {st.session_state.dest} 방향 · {st.session_state.pos}/{st.session_state.total}초")
elif st.session_state.phase == "returning":
    st.write(f"↩️ 회항 중 · 부산으로 복귀 · {st.session_state.pos}/{st.session_state.total}초")
else:
    st.write("⚓ 정박 중 — 목적지를 선택해 출항하세요.")

st.subheader("항구 정보")
selected_port = st.session_state.selected_port
can_choose = st.session_state.phase == "docked"
if selected_port and selected_port in [d["name"] for d in DESTINATIONS]:
    destination = next(d for d in DESTINATIONS if d["name"] == selected_port)
    years = actual_years(selected_port)
    income = actual_income(selected_port)
    features = {
        "도쿄": "가까운 항로라 빠르게 운임을 확보할 수 있습니다.",
        "상하이": "동아시아 주요 무역항으로, 짧은 항해와 중간 수준의 운임이 특징입니다.",
        "싱가포르": "동남아시아의 주요 환적항으로, 항해 기간은 길지만 운임이 큽니다.",
        "로테르담": "유럽의 대형 항만으로, 가장 긴 항해와 높은 운임을 제공합니다.",
    }
    st.markdown(f"### 📍 {selected_port} 항구")
    info_cols = st.columns(3)
    info_cols[0].metric("예상 항해 기간", f"{years}년")
    info_cols[1].metric("예상 운임", money_label(income))
    info_cols[2].metric("현재 배출량", f"{current_emission()}%")
    st.write(features[selected_port])
    if st.button(f"🚢 {selected_port}로 출항", key="selected_port_depart", disabled=not can_choose, use_container_width=True):
        start_voyage(selected_port)
        st.rerun()
else:
    st.info("지도에서 부산이 아닌 목적지 핀(📍)을 선택하면 항구 정보와 출항 버튼이 나타납니다.")

if 4 in st.session_state.bought_tr:
    st.toggle("자동 운항", key="auto_on", disabled=st.session_state.phase != "docked",
              help="항해 사이에 다음 항로를 직접 출발시킬 수 있습니다.")
    if st.session_state.auto_on:
        next_auto_dest = AUTO_ROUTE[st.session_state.auto_idx % len(AUTO_ROUTE)]
        st.caption(f"다음 자동 항로: {next_auto_dest}")
        st.button("▶ 다음 자동 항해 출발", key="start_auto_voyage",
                  disabled=st.session_state.phase != "docked", use_container_width=True,
                  on_click=start_auto_voyage)

st.subheader("업그레이드 상점")
eq_tab, tr_tab = st.tabs(["탄소 감축 설비", "운송 강화"])
with eq_tab:
    for item in EQUIPMENT:
        bought = item["id"] in st.session_state.bought_eq
        enough_money = st.session_state.money >= item["price"]
        row = st.columns([4, 1, 1])
        with row[0]:
            st.markdown(f"**{item['name']}**")
            st.caption(f"{item['effect']} · 가격 {money_label(item['price'])}")
            if not bought and not enough_money:
                st.caption("자금 부족")
        with row[1]:
            if bought:
                st.button("구매 완료", key=f"eq_done_{item['id']}", disabled=True, use_container_width=True)
            else:
                st.button("구매", key=f"eq_{item['id']}",
                          disabled=(st.session_state.phase != "docked" or not enough_money),
                          use_container_width=True, on_click=buy_equipment, args=(item["id"],))
        with row[2]:
            st.write(money_label(item["price"]))
        st.divider()
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

if st.session_state.phase == "sailing":
    st.button("⏸ 일시정지(회항)", key="pause_voyage", use_container_width=True, on_click=pause_voyage)

# 화면을 모두 그린 뒤 1초에 한 칸씩 이동한다.
if st.session_state.phase == "sailing":
    time.sleep(1)
    st.session_state.pos += 1
    if st.session_state.pos >= st.session_state.total:
        arrive()
    st.rerun()
elif st.session_state.phase == "returning":
    time.sleep(1)
    st.session_state.pos -= 1
    if st.session_state.pos <= 0:
        finish_return()
    st.rerun()
