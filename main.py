import streamlit as st
import pandas as pd
import math
import os
import random
from datetime import datetime, timedelta, timezone

import plotly.graph_objects as go


# =========================================================
# 페이지 기본 설정
# =========================================================

st.set_page_config(
    page_title="Celestial Logbook",
    page_icon="⚓",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# =========================================================
# 한국 시간
# =========================================================

KST = timezone(timedelta(hours=9))


def get_kst_now():
    return datetime.now(KST)


# =========================================================
# 기본 설정
# =========================================================

LOG_FILE = "log.csv"

# 공부 1분 = 1해리
NAUTICAL_MILES_PER_MINUTE = 1.0

BUSAN_LAT = 35.1796
BUSAN_LON = 129.0756


# =========================================================
# 목적지
# =========================================================

DESTINATIONS = {
    "도쿄": {"country": "일본", "lat": 35.6762, "lon": 139.6503},
    "상하이": {"country": "중국", "lat": 31.2304, "lon": 121.4737},
    "싱가포르": {"country": "싱가포르", "lat": 1.3521, "lon": 103.8198},
    "시드니": {"country": "호주", "lat": -33.8688, "lon": 151.2093},
    "호놀룰루": {"country": "미국", "lat": 21.3069, "lon": -157.8583},
    "밴쿠버": {"country": "캐나다", "lat": 49.2827, "lon": -123.1207},
    "로스앤젤레스": {"country": "미국", "lat": 34.0522, "lon": -118.2437},
    "런던": {"country": "영국", "lat": 51.5074, "lon": -0.1278},
    "파리": {"country": "프랑스", "lat": 48.8566, "lon": 2.3522},
    "뉴욕": {"country": "미국", "lat": 40.7128, "lon": -74.0060},
}

POMODORO_DESTINATION = {
    "lat": 38.2070,
    "lon": 128.5918,
    "name": "속초",
}


# =========================================================
# 별자리
# =========================================================

CONSTELLATIONS = {
    1: "오리온자리",
    2: "큰개자리",
    3: "쌍둥이자리",
    4: "사자자리",
    5: "처녀자리",
    6: "목동자리",
    7: "전갈자리",
    8: "궁수자리",
    9: "백조자리",
    10: "페가수스자리",
    11: "황소자리",
    12: "마차부자리",
}


# =========================================================
# 거리 계산
# =========================================================

def haversine_nm(lat1, lon1, lat2, lon2):
    """두 지점 사이의 거리를 해리(NM)로 계산"""

    earth_radius_km = 6371.0

    lat1 = math.radians(lat1)
    lon1 = math.radians(lon1)
    lat2 = math.radians(lat2)
    lon2 = math.radians(lon2)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1)
        * math.cos(lat2)
        * math.sin(dlon / 2) ** 2
    )

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    km = earth_radius_km * c

    return km / 1.852


def get_destination_distance(destination):
    info = DESTINATIONS[destination]

    return haversine_nm(
        BUSAN_LAT,
        BUSAN_LON,
        info["lat"],
        info["lon"],
    )


# =========================================================
# 달의 위상
# =========================================================

def get_moon_phase(date_value):

    reference = datetime(2000, 1, 6)

    target = datetime(
        date_value.year,
        date_value.month,
        date_value.day,
    )

    days = (target - reference).days
    synodic_month = 29.53058867
    phase = (days % synodic_month) / synodic_month

    if phase < 0.03:
        return "🌑 신월"
    elif phase < 0.22:
        return "🌒 초승달"
    elif phase < 0.28:
        return "🌓 상현달"
    elif phase < 0.47:
        return "🌔 차오르는 달"
    elif phase < 0.53:
        return "🌕 보름달"
    elif phase < 0.72:
        return "🌖 기우는 달"
    elif phase < 0.78:
        return "🌗 하현달"
    else:
        return "🌘 그믐달"


# =========================================================
# log.csv 초기화
# =========================================================

def initialize_log_file():

    if not os.path.exists(LOG_FILE):

        empty_df = pd.DataFrame(
            columns=[
                "날짜",
                "모드",
                "시작시각",
                "종료시각",
                "소요시간(분)",
                "전진거리(해리)",
            ]
        )

        empty_df.to_csv(
            LOG_FILE,
            index=False,
            encoding="utf-8-sig",
        )


# =========================================================
# 공부 기록 저장
# =========================================================

def save_session(start_time, end_time, mode):

    if start_time is None:
        return

    seconds = (
        end_time - start_time
    ).total_seconds()

    minutes = max(0, seconds / 60)
    minutes = round(minutes, 1)

    distance = minutes * NAUTICAL_MILES_PER_MINUTE

    new_row = pd.DataFrame(
        [{
            "날짜": start_time.strftime("%Y-%m-%d"),
            "모드": mode,
            "시작시각": start_time.strftime("%H:%M:%S"),
            "종료시각": end_time.strftime("%H:%M:%S"),
            "소요시간(분)": minutes,
            "전진거리(해리)": round(distance, 1),
        }]
    )

    initialize_log_file()

    new_row.to_csv(
        LOG_FILE,
        mode="a",
        header=False,
        index=False,
        encoding="utf-8-sig",
    )


# =========================================================
# 세션 상태
# =========================================================

if "timer_running" not in st.session_state:
    st.session_state.timer_running = False

if "start_time" not in st.session_state:
    st.session_state.start_time = None

if "elapsed_seconds" not in st.session_state:
    st.session_state.elapsed_seconds = 0

if "selected_mode" not in st.session_state:
    st.session_state.selected_mode = "자유형"

if "selected_destination" not in st.session_state:
    st.session_state.selected_destination = "도쿄"

if "free_destination" not in st.session_state:
    st.session_state.free_destination = None


# =========================================================
# CSS
# =========================================================

st.markdown(
    """
<style>

.stApp {
    background-color: #07111f;
    color: #f4efe2;
}

.block-container {
    max-width: 1100px;
    padding-top: 3rem;
    padding-bottom: 4rem;
}

section[data-testid="stSidebar"] {
    background-color: #091827;
    border-right: 1px solid #b99a55;
}

.main-title {
    color: #d8b66a;
    font-size: 3.2rem;
    font-weight: 700;
    letter-spacing: 0.06em;
}

.subtitle {
    color: #9daaba;
    margin-bottom: 30px;
}

.info-card {
    background-color: #0d1b2a;
    border: 1px solid #33485e;
    border-radius: 15px;
    padding: 20px;
    margin-bottom: 15px;
}

.card-title {
    color: #9daaba;
    font-size: 0.8rem;
    letter-spacing: 0.1em;
    margin-bottom: 8px;
}

.card-value {
    color: #f1d58b;
    font-size: 1.4rem;
    font-weight: 700;
}

.section-title {
    color: #d8b66a;
    font-size: 1.3rem;
    font-weight: 700;
    margin-top: 30px;
    margin-bottom: 15px;
}

</style>
""",
    unsafe_allow_html=True,
)


# =========================================================
# 사이드바
# =========================================================

with st.sidebar:

    st.markdown(
        """
        <div style="
            color:#d8b66a;
            font-size:1.35rem;
            font-weight:700;
            margin-bottom:10px;
        ">
            ⚓ CELESTIAL LOGBOOK
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div style="
            color:#9daaba;
            line-height:1.6;
            margin-bottom:20px;
        ">
        공부한 시간을 항해 거리로 바꾸어
        나만의 항해일지를 만들어보세요.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    st.markdown("### ⚓ 항해 모드")

    mode = st.radio(
        "공부 방식을 선택하세요.",
        ["자유형", "지정 항로", "뽀모도로"],
        index=[
            "자유형",
            "지정 항로",
            "뽀모도로",
        ].index(st.session_state.selected_mode),
        label_visibility="collapsed",
    )

    st.session_state.selected_mode = mode

    if mode == "지정 항로":

        destination = st.selectbox(
            "목적지",
            list(DESTINATIONS.keys()),
            index=list(DESTINATIONS.keys()).index(
                st.session_state.selected_destination
            ),
        )

        st.session_state.selected_destination = destination

        distance = get_destination_distance(destination)

        st.caption(
            f"부산 → {destination} 약 {distance:,.0f} NM"
        )

    elif mode == "자유형":

        if st.session_state.free_destination is None:
            st.session_state.free_destination = random.choice(
                list(DESTINATIONS.keys())
            )

        st.caption(
            f"이번 자유 항해 목적지: "
            f"{st.session_state.free_destination}"
        )

    st.divider()

    today = get_kst_now().date()

    st.markdown("### 오늘의 하늘")

    st.markdown(
        f"""
        <div style="
            color:#f4efe2;
            line-height:1.8;
        ">
        📅 {today.strftime("%Y년 %m월 %d일")}<br>
        ✦ {CONSTELLATIONS[today.month]}<br>
        {get_moon_phase(today)}
        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# 제목
# =========================================================

st.markdown(
    '<div class="main-title">CELESTIAL LOGBOOK</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="subtitle">공부를 항해로 바꾸는 나만의 항해일지</div>',
    unsafe_allow_html=True,
)


# =========================================================
# 상단 정보
# =========================================================

col1, col2, col3 = st.columns(3)

with col1:

    st.markdown(
        f"""
        <div class="info-card">
            <div class="card-title">CURRENT MODE</div>
            <div class="card-value">{mode}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


with col2:

    if mode == "지정 항로":
        destination_text = st.session_state.selected_destination
    elif mode == "자유형":
        destination_text = (
            st.session_state.free_destination or "자유 항해"
        )
    else:
        destination_text = "25분 항해"

    st.markdown(
        f"""
        <div class="info-card">
            <div class="card-title">DESTINATION</div>
            <div class="card-value">{destination_text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


with col3:

    voyage_text = "25 MIN" if mode == "뽀모도로" else "FREE"

    st.markdown(
        f"""
        <div class="info-card">
            <div class="card-title">VOYAGE</div>
            <div class="card-value">{voyage_text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# 경과 시간
# =========================================================

def get_elapsed_seconds():

    # 정박 상태에서는 마지막으로 확정된 시간을 그대로 표시
    if not st.session_state.timer_running:
        return st.session_state.elapsed_seconds

    if st.session_state.start_time is None:
        return st.session_state.elapsed_seconds

    now = get_kst_now()

    current_seconds = int(
        (
            now - st.session_state.start_time
        ).total_seconds()
    )

    return (
        st.session_state.elapsed_seconds
        + max(0, current_seconds)
    )


def format_time(seconds):

    seconds = max(0, int(seconds))

    minutes = seconds // 60
    seconds = seconds % 60

    return f"{minutes:02d}:{seconds:02d}"


# =========================================================
# 대권항로 계산
# =========================================================

def great_circle_point(
    lat1,
    lon1,
    lat2,
    lon2,
    fraction,
):
    """두 지점 사이를 대권항로 기준으로 보간"""

    fraction = max(0.0, min(1.0, fraction))

    lat1_r = math.radians(lat1)
    lon1_r = math.radians(lon1)
    lat2_r = math.radians(lat2)
    lon2_r = math.radians(lon2)

    x1 = math.cos(lat1_r) * math.cos(lon1_r)
    y1 = math.cos(lat1_r) * math.sin(lon1_r)
    z1 = math.sin(lat1_r)

    x2 = math.cos(lat2_r) * math.cos(lon2_r)
    y2 = math.cos(lat2_r) * math.sin(lon2_r)
    z2 = math.sin(lat2_r)

    dot = max(
        -1.0,
        min(1.0, x1 * x2 + y1 * y2 + z1 * z2),
    )

    angle = math.acos(dot)

    if angle < 1e-10:
        return lat1, lon1

    sin_angle = math.sin(angle)

    a = math.sin((1 - fraction) * angle) / sin_angle
    b = math.sin(fraction * angle) / sin_angle

    x = a * x1 + b * x2
    y = a * y1 + b * y2
    z = a * z1 + b * z2

    lat = math.degrees(
        math.atan2(
            z,
            math.sqrt(x * x + y * y),
        )
    )

    lon = math.degrees(
        math.atan2(y, x)
    )

    return lat, lon


def build_great_circle_track(
    start_lat,
    start_lon,
    end_lat,
    end_lon,
    points=100,
):

    lats = []
    lons = []

    for i in range(points + 1):

        fraction = i / points

        lat, lon = great_circle_point(
            start_lat,
            start_lon,
            end_lat,
            end_lon,
            fraction,
        )

        lats.append(lat)
        lons.append(lon)

    return lats, lons


# =========================================================
# 현재 항해 정보
# =========================================================

def get_current_voyage():

    elapsed_seconds = get_elapsed_seconds()

    distance_travelled = (
        elapsed_seconds / 60
    ) * NAUTICAL_MILES_PER_MINUTE

    if mode == "지정 항로":

        destination_name = (
            st.session_state.selected_destination
        )

        destination = DESTINATIONS[destination_name]

    elif mode == "자유형":

        if st.session_state.free_destination is None:
            st.session_state.free_destination = random.choice(
                list(DESTINATIONS.keys())
            )

        destination_name = st.session_state.free_destination
        destination = DESTINATIONS[destination_name]

    else:

        destination_name = POMODORO_DESTINATION["name"]
        destination = POMODORO_DESTINATION

    total_distance = haversine_nm(
        BUSAN_LAT,
        BUSAN_LON,
        destination["lat"],
        destination["lon"],
    )

    progress = (
        distance_travelled / total_distance
        if total_distance > 0
        else 0
    )

    progress = max(
        0.0,
        min(1.0, progress),
    )

    current_lat, current_lon = great_circle_point(
        BUSAN_LAT,
        BUSAN_LON,
        destination["lat"],
        destination["lon"],
        progress,
    )

    remaining_distance = max(
        0.0,
        total_distance - distance_travelled,
    )

    return {
        "destination_name": destination_name,
        "destination_lat": destination["lat"],
        "destination_lon": destination["lon"],
        "total_distance": total_distance,
        "distance_travelled": min(
            distance_travelled,
            total_distance,
        ),
        "remaining_distance": remaining_distance,
        "progress": progress,
        "current_lat": current_lat,
        "current_lon": current_lon,
    }


# =========================================================
# 지도 만들기
# =========================================================

def create_voyage_map(voyage):

    destination_lat = voyage["destination_lat"]
    destination_lon = voyage["destination_lon"]

    route_lats, route_lons = build_great_circle_track(
        BUSAN_LAT,
        BUSAN_LON,
        destination_lat,
        destination_lon,
    )

    traveled_count = max(
        2,
        int(100 * voyage["progress"]) + 1,
    )

    traveled_lats = route_lats[:traveled_count]
    traveled_lons = route_lons[:traveled_count]

    fig = go.Figure()

    # 전체 예정 항로
    fig.add_trace(
        go.Scattergeo(
            lat=route_lats,
            lon=route_lons,
            mode="lines",
            line=dict(
                width=2,
                dash="dot",
            ),
            name="예정 항로",
            hoverinfo="skip",
        )
    )

    # 지금까지 이동한 항로
    fig.add_trace(
        go.Scattergeo(
            lat=traveled_lats,
            lon=traveled_lons,
            mode="lines",
            line=dict(width=4),
            name="항해 기록",
            hoverinfo="skip",
        )
    )

    # 출발항
    fig.add_trace(
        go.Scattergeo(
            lat=[BUSAN_LAT],
            lon=[BUSAN_LON],
            mode="markers+text",
            text=["부산"],
            textposition="bottom center",
            marker=dict(
                size=9,
                symbol="circle",
            ),
            name="출발항",
        )
    )

    # 목적지
    fig.add_trace(
        go.Scattergeo(
            lat=[destination_lat],
            lon=[destination_lon],
            mode="markers+text",
            text=[voyage["destination_name"]],
            textposition="top center",
            marker=dict(
                size=11,
                symbol="diamond",
            ),
            name="목적지",
        )
    )

    # 현재 선박
    fig.add_trace(
        go.Scattergeo(
            lat=[voyage["current_lat"]],
            lon=[voyage["current_lon"]],
            mode="markers",
            marker=dict(
                size=14,
                symbol="star",
            ),
            name="현재 선박",
            hovertemplate=(
                "현재 위치<br>"
                "위도 %{lat:.2f}°<br>"
                "경도 %{lon:.2f}°"
                "<extra></extra>"
            ),
        )
    )

    fig.update_geos(
        projection_type="natural earth",
        showland=True,
        landcolor="#122234",
        showocean=True,
        oceancolor="#06111d",
        showcountries=True,
        countrycolor="#405064",
        showcoastlines=True,
        coastlinecolor="#65778b",
        showlakes=True,
        lakecolor="#06111d",
        bgcolor="#07111f",
    )

    fig.update_layout(
        height=560,
        margin=dict(
            l=0,
            r=0,
            t=20,
            b=0,
        ),
        paper_bgcolor="#07111f",
        plot_bgcolor="#07111f",
        font=dict(
            color="#f4efe2",
        ),
        legend=dict(
            bgcolor="rgba(7,17,31,0.75)",
        ),
    )

    return fig


# =========================================================
# 타이머 + 지도
# =========================================================
# 중요:
# 타이머와 지도를 같은 fragment 안에 넣는다.
# 지도는 1초마다 정상적으로 갱신되면서
# 타이머도 같은 주기로 함께 갱신된다.

@st.fragment(run_every=1)
def show_voyage():

    elapsed = get_elapsed_seconds()

    # 뽀모도로는 25분 카운트다운
    if st.session_state.selected_mode == "뽀모도로":

        total = 25 * 60

        remaining = max(
            0,
            total - elapsed,
        )

        timer_text = format_time(remaining)

    else:

        timer_text = format_time(elapsed)

    # -------------------------------
    # 타이머
    # -------------------------------

    st.markdown(
        f"""
        <div style="
            background:#081522;
            border:1px solid #8e743d;
            border-radius:18px;
            padding:40px 20px;
            margin:25px 0;
            text-align:center;
        ">

            <div style="
                color:#9daaba;
                font-size:14px;
                letter-spacing:3px;
                margin-bottom:12px;
            ">
                CURRENT VOYAGE
            </div>

            <div style="
                color:#f1d58b;
                font-size:72px;
                font-weight:700;
                line-height:1.1;
                font-family:monospace;
            ">
                {timer_text}
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )

    # -------------------------------
    # 지도
    # -------------------------------

    voyage = get_current_voyage()

    st.markdown(
        '<div class="section-title">🗺️ CURRENT VOYAGE</div>',
        unsafe_allow_html=True,
    )

    fig = create_voyage_map(voyage)

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={
            "displayModeBar": False,
        },
    )

    # -------------------------------
    # 항해 정보
    # -------------------------------

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "현재 위치",
            (
                f'{voyage["current_lat"]:.2f}°'
                f' / '
                f'{voyage["current_lon"]:.2f}°'
            ),
        )

    with col2:
        st.metric(
            "항해 거리",
            f'{voyage["distance_travelled"]:,.1f} NM',
        )

    with col3:
        st.metric(
            "남은 거리",
            f'{voyage["remaining_distance"]:,.1f} NM',
        )

    with col4:
        st.metric(
            "진행률",
            f'{voyage["progress"] * 100:.1f}%',
        )

    if st.session_state.timer_running:
        st.info(
            f'⚓ 항해 중 — 부산 → {voyage["destination_name"]}'
        )
    else:
        if elapsed > 0:
            st.success(
                "⏸ 정박 중 — 현재 위치에서 닻을 내렸습니다."
            )
        else:
            st.caption(
                "출항 버튼을 누르면 선박이 항해를 시작합니다."
            )


# =========================================================
# 타이머 + 지도 표시
# =========================================================

show_voyage()


# =========================================================
# 버튼
# =========================================================

button1, button2, button3 = st.columns(3)

with button1:

    start_clicked = st.button(
        (
            "⚓ 다시 출항"
            if st.session_state.elapsed_seconds > 0
            else "⚓ 출항"
        ),
        use_container_width=True,
        disabled=st.session_state.timer_running,
        key="start_timer_button",
    )

with button2:

    stop_clicked = st.button(
        "⏸ 정박",
        use_container_width=True,
        disabled=not st.session_state.timer_running,
        key="stop_timer_button",
    )

with button3:

    reset_clicked = st.button(
        "↻ 초기화",
        use_container_width=True,
        key="reset_timer_button",
    )


# =========================================================
# 출항
# =========================================================

if start_clicked:

    # 현재 시각부터 새로운 구간을 시작한다.
    st.session_state.start_time = get_kst_now()
    st.session_state.timer_running = True

    # 자유형은 출항할 때 목적지를 새로 정한다.
    if st.session_state.selected_mode == "자유형":

        st.session_state.free_destination = random.choice(
            list(DESTINATIONS.keys())
        )

    st.rerun()


# =========================================================
# 정박
# =========================================================

if stop_clicked:

    now = get_kst_now()
    start = st.session_state.start_time

    if start is not None:

        segment_seconds = int(
            (
                now - start
            ).total_seconds()
        )

        segment_seconds = max(
            0,
            segment_seconds,
        )

        # 이번 구간을 누적 시간에 더한다.
        st.session_state.elapsed_seconds += segment_seconds

        # 항해일지에 기록한다.
        save_session(
            start,
            now,
            st.session_state.selected_mode,
        )

    # 정박 상태로 변경
    st.session_state.start_time = None
    st.session_state.timer_running = False

    st.rerun()


# =========================================================
# 초기화
# =========================================================

if reset_clicked:

    st.session_state.timer_running = False
    st.session_state.start_time = None
    st.session_state.elapsed_seconds = 0

    # 자유형 목적지도 다시 정한다.
    st.session_state.free_destination = None

    st.rerun()


# =========================================================
# 지정 항로 진행도
# =========================================================

if mode == "지정 항로":

    initialize_log_file()

    try:

        log_df = pd.read_csv(
            LOG_FILE,
            encoding="utf-8-sig",
        )

        if len(log_df) > 0:

            total_distance = pd.to_numeric(
                log_df["전진거리(해리)"],
                errors="coerce",
            ).fillna(0).sum()

        else:

            total_distance = 0

    except Exception:

        total_distance = 0

    destination_distance = get_destination_distance(
        st.session_state.selected_destination
    )

    progress = min(
        total_distance / destination_distance,
        1.0,
    )

    st.markdown(
        '<div class="section-title">🧭 항로 진행도</div>',
        unsafe_allow_html=True,
    )

    st.progress(progress)

    col1, col2 = st.columns(2)

    with col1:

        st.metric(
            "현재까지 전진",
            f"{total_distance:,.1f} NM",
        )

    with col2:

        st.metric(
            "목적지까지",
            f"{destination_distance:,.0f} NM",
        )


# =========================================================
# 뽀모도로 안내
# =========================================================

if mode == "뽀모도로":

    st.markdown(
        '<div class="section-title">🍅 뽀모도로 항해</div>',
        unsafe_allow_html=True,
    )

    route = "부산 → 속초"

    st.markdown(
        f"""
        <div class="info-card">

            <div class="card-title">
                CURRENT ROUTE
            </div>

            <div style="
                color:#f4efe2;
                font-size:1.15rem;
                margin-bottom:10px;
            ">
                {route}
            </div>

            <div style="
                color:#9daaba;
                line-height:1.7;
            ">
                25분 동안 집중하는 동안 선박이 항해합니다.
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# 안내
# =========================================================

st.markdown("---")

st.markdown(
    '<div class="section-title">✦ 항해 안내</div>',
    unsafe_allow_html=True,
)

if mode == "자유형":

    st.write(
        "자유롭게 공부하고 정박하면 해당 시간이 항해일지에 기록됩니다."
    )

elif mode == "지정 항로":

    st.write(
        f"부산에서 {st.session_state.selected_destination}까지의 "
        "가상 항로를 따라 공부합니다."
    )

else:

    st.write(
        "25분 동안 집중하면 뽀모도로 항해를 진행합니다."
    )
