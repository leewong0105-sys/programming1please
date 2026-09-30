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
    """현재 시간을 한국 시간으로 가져옵니다."""
    return datetime.now(KST)


# =========================================================
# 기본 설정
# =========================================================

LOG_FILE = "log.csv"

# 공부 1분 = 1해리
NAUTICAL_MILES_PER_MINUTE = 1.0

# 출발 항구는 부산으로 설정
BUSAN = {
    "name": "부산",
    "country": "대한민국",
    "lat": 35.1796,
    "lon": 129.0756
}


# =========================================================
# 목적지 목록
# =========================================================

# 지정 항로와 자유형에서 사용할 세계의 주요 항구들
DESTINATIONS = {
    "도쿄": {
        "country": "일본",
        "lat": 35.6762,
        "lon": 139.6503
    },
    "상하이": {
        "country": "중국",
        "lat": 31.2304,
        "lon": 121.4737
    },
    "싱가포르": {
        "country": "싱가포르",
        "lat": 1.3521,
        "lon": 103.8198
    },
    "시드니": {
        "country": "호주",
        "lat": -33.8688,
        "lon": 151.2093
    },
    "호놀룰루": {
        "country": "미국",
        "lat": 21.3069,
        "lon": -157.8583
    },
    "밴쿠버": {
        "country": "캐나다",
        "lat": 49.2827,
        "lon": -123.1207
    },
    "로스앤젤레스": {
        "country": "미국",
        "lat": 34.0522,
        "lon": -118.2437
    },
    "런던": {
        "country": "영국",
        "lat": 51.5074,
        "lon": -0.1278
    },
    "파리": {
        "country": "프랑스",
        "lat": 48.8566,
        "lon": 2.3522
    },
    "뉴욕": {
        "country": "미국",
        "lat": 40.7128,
        "lon": -74.0060
    }
}


# =========================================================
# 뽀모도로용 항구
# =========================================================

# 뽀모도로에서는 가까운 국내 항구들을 따라 이동하도록 구성
POMODORO_PORTS = {
    "울산": {
        "country": "대한민국",
        "lat": 35.5384,
        "lon": 129.3114
    },
    "포항": {
        "country": "대한민국",
        "lat": 36.0190,
        "lon": 129.3435
    },
    "동해": {
        "country": "대한민국",
        "lat": 37.5247,
        "lon": 129.1143
    },
    "속초": {
        "country": "대한민국",
        "lat": 38.2070,
        "lon": 128.5918
    }
}

POMODORO_ROUTE = [
    BUSAN,
    {
        "name": "울산",
        **POMODORO_PORTS["울산"]
    },
    {
        "name": "포항",
        **POMODORO_PORTS["포항"]
    },
    {
        "name": "동해",
        **POMODORO_PORTS["동해"]
    },
    {
        "name": "속초",
        **POMODORO_PORTS["속초"]
    }
]


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
    12: "마차부자리"
}


# =========================================================
# 거리 계산
# =========================================================

def haversine_nm(lat1, lon1, lat2, lon2):
    """
    두 위치 사이의 거리를 해리(NM)로 계산합니다.

    지구가 둥글기 때문에 단순히 위도/경도를 빼는 대신
    하버사인 공식을 사용합니다.
    """

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

    c = 2 * math.atan2(
        math.sqrt(a),
        math.sqrt(1 - a)
    )

    km = earth_radius_km * c

    # 1해리 = 1.852km
    return km / 1.852


def get_destination_distance(destination):
    """부산에서 목적지까지의 거리를 해리로 계산합니다."""

    info = DESTINATIONS[destination]

    return haversine_nm(
        BUSAN["lat"],
        BUSAN["lon"],
        info["lat"],
        info["lon"]
    )


# =========================================================
# 달의 위상
# =========================================================

def get_moon_phase(date_value):

    reference = datetime(2000, 1, 6)

    target = datetime(
        date_value.year,
        date_value.month,
        date_value.day
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
                "전진거리(해리)"
            ]
        )

        empty_df.to_csv(
            LOG_FILE,
            index=False,
            encoding="utf-8-sig"
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

    minutes = max(
        0,
        seconds / 60
    )

    # 소수 첫째 자리까지 저장
    minutes = round(minutes, 1)

    # 공부 시간 → 항해 거리
    distance = (
        minutes * NAUTICAL_MILES_PER_MINUTE
    )

    new_row = pd.DataFrame(
        [{
            "날짜": start_time.strftime("%Y-%m-%d"),
            "모드": mode,
            "시작시각": start_time.strftime("%H:%M:%S"),
            "종료시각": end_time.strftime("%H:%M:%S"),
            "소요시간(분)": minutes,
            "전진거리(해리)": round(distance, 1)
        }]
    )

    initialize_log_file()

    new_row.to_csv(
        LOG_FILE,
        mode="a",
        header=False,
        index=False,
        encoding="utf-8-sig"
    )


# =========================================================
# 세션 상태
# =========================================================

# 타이머가 실행 중인지
if "timer_running" not in st.session_state:
    st.session_state.timer_running = False

# 현재 출항 구간의 시작 시각
if "start_time" not in st.session_state:
    st.session_state.start_time = None

# 정박했을 때 확정된 누적 시간
if "elapsed_seconds" not in st.session_state:
    st.session_state.elapsed_seconds = 0

# 현재 선택된 공부 모드
if "selected_mode" not in st.session_state:
    st.session_state.selected_mode = "자유형"

# 지정 항로의 목적지
if "selected_destination" not in st.session_state:
    st.session_state.selected_destination = "도쿄"

# 자유형에서 사용할 무작위 목적지
if "free_destination" not in st.session_state:
    st.session_state.free_destination = random.choice(
        list(DESTINATIONS.keys())
    )

# 이전에 선택했던 모드
if "last_mode" not in st.session_state:
    st.session_state.last_mode = "자유형"

# 뽀모도로 기록 상태
if "pomodoro_saved" not in st.session_state:
    st.session_state.pomodoro_saved = False


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
    unsafe_allow_html=True
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
        unsafe_allow_html=True
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
        unsafe_allow_html=True
    )

    st.divider()

    st.markdown("### ⚓ 항해 모드")

    mode = st.radio(
        "공부 방식을 선택하세요.",
        [
            "자유형",
            "지정 항로",
            "뽀모도로"
        ],
        index=[
            "자유형",
            "지정 항로",
            "뽀모도로"
        ].index(
            st.session_state.selected_mode
        ),
        label_visibility="collapsed"
    )

    # 자유형으로 들어갈 때 새로운 목적지를 하나 뽑습니다.
    if (
        mode == "자유형"
        and st.session_state.last_mode != "자유형"
    ):
        st.session_state.free_destination = random.choice(
            list(DESTINATIONS.keys())
        )

    st.session_state.selected_mode = mode
    st.session_state.last_mode = mode

    # 지정 항로라면 목적지를 직접 선택
    if mode == "지정 항로":

        destination = st.selectbox(
            "목적지",
            list(DESTINATIONS.keys()),
            index=list(
                DESTINATIONS.keys()
            ).index(
                st.session_state.selected_destination
            )
        )

        st.session_state.selected_destination = destination

        distance = get_destination_distance(
            destination
        )

        st.caption(
            f"부산 → {destination} 약 {distance:,.0f} NM"
        )

    # 자유형이라면 무작위 목적지를 보여줌
    elif mode == "자유형":

        st.caption(
            f"이번 자유 항해의 목적지: "
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
        unsafe_allow_html=True
    )


# =========================================================
# 제목
# =========================================================

st.markdown(
    '<div class="main-title">CELESTIAL LOGBOOK</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">공부를 항해로 바꾸는 나만의 항해일지</div>',
    unsafe_allow_html=True
)


# =========================================================
# 상단 정보 카드
# =========================================================

col1, col2, col3 = st.columns(3)


with col1:

    st.markdown(
        f"""
        <div class="info-card">
            <div class="card-title">CURRENT MODE</div>
            <div class="card-value">
                {mode}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


with col2:

    if mode == "지정 항로":

        destination_text = (
            st.session_state.selected_destination
        )

    elif mode == "자유형":

        destination_text = (
            st.session_state.free_destination
        )

    else:

        destination_text = "속초"

    st.markdown(
        f"""
        <div class="info-card">
            <div class="card-title">DESTINATION</div>
            <div class="card-value">
                {destination_text}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


with col3:

    if mode == "뽀모도로":
        voyage_text = "25 MIN"
    else:
        voyage_text = "FREE"

    st.markdown(
        f"""
        <div class="info-card">
            <div class="card-title">VOYAGE</div>
            <div class="card-value">
                {voyage_text}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


# =========================================================
# 현재까지 공부한 시간 계산
# =========================================================

def get_elapsed_seconds():

    # 정박 중이면 마지막으로 저장된 누적 시간 사용
    if not st.session_state.timer_running:

        return st.session_state.elapsed_seconds

    # 출항 중인데 시작 시간이 없다면 안전하게 처리
    if st.session_state.start_time is None:

        return st.session_state.elapsed_seconds

    now = get_kst_now()

    current_seconds = int(
        (
            now
            - st.session_state.start_time
        ).total_seconds()
    )

    return (
        st.session_state.elapsed_seconds
        + max(0, current_seconds)
    )


# =========================================================
# 시간 → MM:SS
# =========================================================

def format_time(seconds):

    seconds = max(
        0,
        int(seconds)
    )

    minutes = seconds // 60
    seconds = seconds % 60

    return f"{minutes:02d}:{seconds:02d}"


# =========================================================
# 타이머 표시
# =========================================================

@st.fragment(run_every=1)
def show_timer():

    elapsed = get_elapsed_seconds()

    # 뽀모도로에서는 남은 시간을 보여줍니다.
    if st.session_state.selected_mode == "뽀모도로":

        total = 25 * 60

        remaining = max(
            0,
            total - elapsed
        )

        timer_text = format_time(
            remaining
        )

    else:

        # 자유형 / 지정 항로는 누적 시간을 보여줍니다.
        timer_text = format_time(
            elapsed
        )

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
        unsafe_allow_html=True
    )


show_timer()


# =========================================================
# 출항 / 정박 / 초기화 버튼
# =========================================================

button1, button2, button3 = st.columns(3)


with button1:

    # 이미 공부한 시간이 있다면 다시 출항으로 표시
    start_label = (
        "⚓ 다시 출항"
        if st.session_state.elapsed_seconds > 0
        else "⚓ 출항"
    )

    start_clicked = st.button(
        start_label,
        key="start_timer_button",
        use_container_width=True,
        disabled=st.session_state.timer_running
    )


with button2:

    stop_clicked = st.button(
        "⏸ 정박",
        key="stop_timer_button",
        use_container_width=True,
        disabled=not st.session_state.timer_running
    )


with button3:

    reset_clicked = st.button(
        "↻ 초기화",
        key="reset_timer_button",
        use_container_width=True
    )


# =========================================================
# 출항
# =========================================================

if start_clicked:

    # 출항 버튼을 누른 순간부터 시간 측정
    st.session_state.start_time = get_kst_now()

    st.session_state.timer_running = True

    st.session_state.pomodoro_saved = False

    st.rerun()


# =========================================================
# 정박
# =========================================================

if stop_clicked:

    now = get_kst_now()

    if st.session_state.start_time is not None:

        # 이번 출항 구간에서 공부한 시간
        current_seconds = int(
            (
                now
                - st.session_state.start_time
            ).total_seconds()
        )

        current_seconds = max(
            0,
            current_seconds
        )

        # 기존 누적 시간에 이번 구간 추가
        st.session_state.elapsed_seconds += (
            current_seconds
        )

        # 항해일지에 기록
        save_session(
            st.session_state.start_time,
            now,
            st.session_state.selected_mode
        )

    # 정박 상태
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

    st.session_state.pomodoro_saved = False

    # 자유형을 초기화하면 다음 항해에 새로운 목적지를 배정
    if mode == "자유형":

        st.session_state.free_destination = random.choice(
            list(DESTINATIONS.keys())
        )

    st.rerun()


# =========================================================
# 현재 상태 표시
# =========================================================

if st.session_state.timer_running:

    st.info("⚓ 항해 중입니다.")

else:

    if st.session_state.elapsed_seconds > 0:

        st.success(
            "⏸ 정박 중입니다. 다시 출항하면 이어서 진행합니다."
        )

    else:

        st.caption(
            "출항 버튼을 누르면 항해가 시작됩니다."
        )


# =========================================================
# 항해 위치 계산
# =========================================================

def interpolate_great_circle(
    start,
    end,
    fraction
):
    """
    출발지와 목적지 사이의 중간 위치를 계산합니다.

    단순한 직선 보간이 아니라
    지구가 둥글다는 것을 고려한 대권 보간입니다.

    fraction:
        0.0 → 출발지
        0.5 → 중간
        1.0 → 목적지
    """

    fraction = max(
        0.0,
        min(1.0, fraction)
    )

    lat1 = math.radians(
        start["lat"]
    )

    lon1 = math.radians(
        start["lon"]
    )

    lat2 = math.radians(
        end["lat"]
    )

    lon2 = math.radians(
        end["lon"]
    )

    # 위도/경도를 3차원 좌표로 변환
    x1 = math.cos(lat1) * math.cos(lon1)
    y1 = math.cos(lat1) * math.sin(lon1)
    z1 = math.sin(lat1)

    x2 = math.cos(lat2) * math.cos(lon2)
    y2 = math.cos(lat2) * math.sin(lon2)
    z2 = math.sin(lat2)

    # 두 지점 사이의 각도
    dot = (
        x1 * x2
        + y1 * y2
        + z1 * z2
    )

    dot = max(
        -1.0,
        min(1.0, dot)
    )

    omega = math.acos(dot)

    # 두 위치가 거의 같으면 그대로 반환
    if abs(omega) < 1e-10:

        return {
            "lat": start["lat"],
            "lon": start["lon"]
        }

    sin_omega = math.sin(omega)

    a = (
        math.sin(
            (1 - fraction) * omega
        )
        / sin_omega
    )

    b = (
        math.sin(
            fraction * omega
        )
        / sin_omega
    )

    x = a * x1 + b * x2
    y = a * y1 + b * y2
    z = a * z1 + b * z2

    lat = math.atan2(
        z,
        math.sqrt(
            x * x + y * y
        )
    )

    lon = math.atan2(
        y,
        x
    )

    return {
        "lat": math.degrees(lat),
        "lon": math.degrees(lon)
    }


def make_great_circle_points(
    start,
    end,
    count=80
):
    """지도에 표시할 부드러운 항로 점들을 만듭니다."""

    latitudes = []
    longitudes = []

    for i in range(count + 1):

        fraction = i / count

        point = interpolate_great_circle(
            start,
            end,
            fraction
        )

        latitudes.append(
            point["lat"]
        )

        longitudes.append(
            point["lon"]
        )

    return latitudes, longitudes


# =========================================================
# 현재 항해 정보 계산
# =========================================================

def get_current_voyage():

    # -----------------------------------------------------
    # 자유형
    # -----------------------------------------------------

    if mode == "자유형":

        destination_name = (
            st.session_state.free_destination
        )

        destination_info = (
            DESTINATIONS[destination_name]
        )

        destination = {
            "name": destination_name,
            "country": destination_info["country"],
            "lat": destination_info["lat"],
            "lon": destination_info["lon"]
        }

        route_distance = get_destination_distance(
            destination_name
        )

        # 공부 시간 → 항해 거리
        distance_traveled = (
            get_elapsed_seconds() / 60
        ) * NAUTICAL_MILES_PER_MINUTE

        progress = (
            min(
                distance_traveled / route_distance,
                1.0
            )
            if route_distance > 0
            else 0
        )

        current_position = (
            interpolate_great_circle(
                BUSAN,
                destination,
                progress
            )
        )

        return {
            "start": BUSAN,
            "destination": destination,
            "route_distance": route_distance,
            "distance_traveled": distance_traveled,
            "progress": progress,
            "current": current_position,
            "route_points": [
                BUSAN,
                destination
            ]
        }

    # -----------------------------------------------------
    # 지정 항로
    # -----------------------------------------------------

    if mode == "지정 항로":

        destination_name = (
            st.session_state.selected_destination
        )

        destination_info = (
            DESTINATIONS[destination_name]
        )

        destination = {
            "name": destination_name,
            "country": destination_info["country"],
            "lat": destination_info["lat"],
            "lon": destination_info["lon"]
        }

        route_distance = get_destination_distance(
            destination_name
        )

        distance_traveled = (
            get_elapsed_seconds() / 60
        ) * NAUTICAL_MILES_PER_MINUTE

        progress = (
            min(
                distance_traveled / route_distance,
                1.0
            )
            if route_distance > 0
            else 0
        )

        current_position = (
            interpolate_great_circle(
                BUSAN,
                destination,
                progress
            )
        )

        return {
            "start": BUSAN,
            "destination": destination,
            "route_distance": route_distance,
            "distance_traveled": distance_traveled,
            "progress": progress,
            "current": current_position,
            "route_points": [
                BUSAN,
                destination
            ]
        }

    # -----------------------------------------------------
    # 뽀모도로
    # -----------------------------------------------------

    route = POMODORO_ROUTE

    total_route_distance = 0.0

    leg_distances = []

    # 각 항구 사이의 거리를 계산
    for index in range(
        len(route) - 1
    ):

        leg_distance = haversine_nm(
            route[index]["lat"],
            route[index]["lon"],
            route[index + 1]["lat"],
            route[index + 1]["lon"]
        )

        leg_distances.append(
            leg_distance
        )

        total_route_distance += (
            leg_distance
        )

    distance_traveled = (
        get_elapsed_seconds() / 60
    ) * NAUTICAL_MILES_PER_MINUTE

    distance_traveled = min(
        distance_traveled,
        total_route_distance
    )

    # 현재 어느 항구 구간에 있는지 계산
    remaining_distance = (
        distance_traveled
    )

    current_position = route[0]

    for index, leg_distance in enumerate(
        leg_distances
    ):

        if remaining_distance <= leg_distance:

            fraction = (
                remaining_distance / leg_distance
                if leg_distance > 0
                else 0
            )

            current_position = (
                interpolate_great_circle(
                    route[index],
                    route[index + 1],
                    fraction
                )
            )

            break

        remaining_distance -= (
            leg_distance
        )

        current_position = (
            route[index + 1]
        )

    progress = (
        distance_traveled
        / total_route_distance
        if total_route_distance > 0
        else 0
    )

    return {
        "start": route[0],
        "destination": route[-1],
        "route_distance": total_route_distance,
        "distance_traveled": distance_traveled,
        "progress": min(progress, 1.0),
        "current": current_position,
        "route_points": route
    }


# =========================================================
# Plotly 세계지도 만들기
# =========================================================

def create_voyage_map(voyage):
    """현재 항해 상태를 Plotly 세계지도에 표시합니다."""

    figure = go.Figure()

    # -----------------------------------------------------
    # 예정 항로
    # -----------------------------------------------------

    route_lat = []
    route_lon = []

    route_points = voyage["route_points"]

    for index in range(
        len(route_points) - 1
    ):

        start = route_points[index]
        end = route_points[index + 1]

        leg_lat, leg_lon = (
            make_great_circle_points(
                start,
                end,
                count=50
            )
        )

        # 여러 구간을 하나의 선으로 잘못 연결하지 않도록
        # 구간 사이에 None을 넣습니다.
        if index > 0:

            route_lat.append(None)
            route_lon.append(None)

        route_lat.extend(leg_lat)
        route_lon.extend(leg_lon)

    figure.add_trace(
        go.Scattergeo(
            lat=route_lat,
            lon=route_lon,
            mode="lines",
            line=dict(
                color="#8e743d",
                width=2,
                dash="dash"
            ),
            name="예정 항로",
            hoverinfo="skip"
        )
    )

    # -----------------------------------------------------
    # 지금까지 지나온 항해 궤적
    # -----------------------------------------------------

    traveled_fraction = (
        voyage["progress"]
    )

    track_lat = []
    track_lon = []

    # 뽀모도로는 여러 항구를 거치므로
    # 각 구간별로 지나온 궤적을 계산합니다.
    if mode == "뽀모도로":

        route = voyage["route_points"]

        target_distance = (
            voyage["distance_traveled"]
        )

        passed_distance = 0.0

        track_lat.append(
            route[0]["lat"]
        )

        track_lon.append(
            route[0]["lon"]
        )

        for index in range(
            len(route) - 1
        ):

            start = route[index]
            end = route[index + 1]

            leg_distance = haversine_nm(
                start["lat"],
                start["lon"],
                end["lat"],
                end["lon"]
            )

            # 해당 구간을 이미 전부 지나갔다면
            if (
                target_distance
                >= passed_distance + leg_distance
            ):

                leg_lat, leg_lon = (
                    make_great_circle_points(
                        start,
                        end,
                        count=25
                    )
                )

                track_lat.extend(
                    leg_lat[1:]
                )

                track_lon.extend(
                    leg_lon[1:]
                )

            else:

                # 현재 구간에서 얼마나 이동했는지 계산
                remaining = max(
                    0,
                    target_distance
                    - passed_distance
                )

                fraction = (
                    remaining / leg_distance
                    if leg_distance > 0
                    else 0
                )

                current = (
                    interpolate_great_circle(
                        start,
                        end,
                        fraction
                    )
                )

                track_lat.append(
                    current["lat"]
                )

                track_lon.append(
                    current["lon"]
                )

                break

            passed_distance += (
                leg_distance
            )

    else:

        # 일반 항로는 부산 → 목적지 전체를 계산
        track_lat, track_lon = (
            make_great_circle_points(
                voyage["start"],
                voyage["destination"],
                count=60
            )
        )

        point_count = max(
            1,
            int(
                len(track_lat)
                * traveled_fraction
            )
        )

        track_lat = (
            track_lat[:point_count]
        )

        track_lon = (
            track_lon[:point_count]
        )

        current = voyage["current"]

        if not track_lat:

            track_lat = [
                voyage["start"]["lat"]
            ]

            track_lon = [
                voyage["start"]["lon"]
            ]

        # 현재 선박 위치를 궤적 마지막에 추가
        if (
            abs(
                track_lat[-1]
                - current["lat"]
            ) > 1e-6
            or
            abs(
                track_lon[-1]
                - current["lon"]
            ) > 1e-6
        ):

            track_lat.append(
                current["lat"]
            )

            track_lon.append(
                current["lon"]
            )

    # 궤적이 있다면 지도에 표시
    if track_lat:

        figure.add_trace(
            go.Scattergeo(
                lat=track_lat,
                lon=track_lon,
                mode="lines",
                line=dict(
                    color="#d8b66a",
                    width=4
                ),
                name="항해 궤적",
                hoverinfo="skip"
            )
        )

    # -----------------------------------------------------
    # 출발항
    # -----------------------------------------------------

    figure.add_trace(
        go.Scattergeo(
            lat=[
                voyage["start"]["lat"]
            ],
            lon=[
                voyage["start"]["lon"]
            ],
            mode="markers+text",
            text=[
                voyage["start"]["name"]
            ],
            textposition="bottom center",
            marker=dict(
                size=9,
                color="#f4efe2"
            ),
            textfont=dict(
                color="#f4efe2",
                size=11
            ),
            name="출발항",
            hovertemplate=(
                "출발항: %{text}<br>"
                "위도: %{lat:.2f}<br>"
                "경도: %{lon:.2f}"
                "<extra></extra>"
            )
        )
    )

    # -----------------------------------------------------
    # 목적지
    # -----------------------------------------------------

    figure.add_trace(
        go.Scattergeo(
            lat=[
                voyage["destination"]["lat"]
            ],
            lon=[
                voyage["destination"]["lon"]
            ],
            mode="markers+text",
            text=[
                voyage["destination"]["name"]
            ],
            textposition="top center",
            marker=dict(
                size=12,
                color="#d8b66a",
                symbol="diamond"
            ),
            textfont=dict(
                color="#f1d58b",
                size=12
            ),
            name="목적지",
            hovertemplate=(
                "목적지: %{text}<br>"
                "위도: %{lat:.2f}<br>"
                "경도: %{lon:.2f}"
                "<extra></extra>"
            )
        )
    )

    # -----------------------------------------------------
    # 현재 선박
    # -----------------------------------------------------

    current = voyage["current"]

    status = (
        "항해 중"
        if st.session_state.timer_running
        else "정박 중"
    )

    figure.add_trace(
        go.Scattergeo(
            lat=[
                current["lat"]
            ],
            lon=[
                current["lon"]
            ],
            mode="markers+text",
            text=["🚢"],
            textposition="middle center",
            marker=dict(
                size=22,
                color="#d8b66a",
                line=dict(
                    color="#ffffff",
                    width=1
                )
            ),
            textfont=dict(
                size=16
            ),
            name="현재 선박",
            hovertemplate=(
                f"{status}<br>"
                "현재 위도: %{lat:.2f}<br>"
                "현재 경도: %{lon:.2f}"
                "<extra></extra>"
            )
        )
    )

    # -----------------------------------------------------
    # 세계지도 디자인
    # -----------------------------------------------------

    figure.update_geos(
        projection_type="natural earth",

        # 육지
        showland=True,
        landcolor="#102235",

        # 바다
        showocean=True,
        oceancolor="#06101c",

        # 호수
        showlakes=True,
        lakecolor="#06101c",

        # 국가 경계
        showcountries=True,
        countrycolor="#34475a",

        # 해안선
        showcoastlines=True,
        coastlinecolor="#53677a",
        coastlinewidth=0.7,

        # 지도 테두리
        showframe=False
    )

    figure.update_layout(

        height=560,

        margin=dict(
            l=0,
            r=0,
            t=10,
            b=0
        ),

        paper_bgcolor="#07111f",

        plot_bgcolor="#07111f",

        font=dict(
            color="#f4efe2"
        ),

        legend=dict(
            bgcolor="rgba(7,17,31,0.85)",
            bordercolor="#33485e",
            borderwidth=1
        ),

        # 지도를 새로 그려도
        # 사용자가 보고 있던 확대 상태가 최대한 유지되도록 설정
        uirevision="voyage-map"
    )

    return figure


# =========================================================
# 항해 지도
# =========================================================

# 지도도 타이머처럼 1초마다 다시 계산합니다.
# 따라서 공부 중에는 선박이 조금씩 이동합니다.
@st.fragment(run_every=1)
def show_voyage_map():

    voyage = get_current_voyage()

    st.markdown(
        '<div class="section-title">🧭 현재 항해 지도</div>',
        unsafe_allow_html=True
    )

    st.caption(
        "공부한 시간이 1분당 1해리의 가상 항해 거리로 변환됩니다."
    )

    map_figure = create_voyage_map(
        voyage
    )

    st.plotly_chart(
        map_figure,
        use_container_width=True,
        config={
            "displayModeBar": False
        }
    )

    # -----------------------------------------------------
    # 현재 항해 현황
    # -----------------------------------------------------

    current = voyage["current"]

    if (
        voyage["distance_traveled"]
        >= voyage["route_distance"]
    ):

        voyage_status = "🏁 목적지 도착"

    elif st.session_state.timer_running:

        voyage_status = "⚓ 항해 중"

    else:

        voyage_status = "⏸ 정박 중"

    st.markdown(
        '<div class="section-title">📜 항해 현황</div>',
        unsafe_allow_html=True
    )

    info1, info2, info3, info4 = (
        st.columns(4)
    )

    with info1:

        st.metric(
            "현재 위치",
            (
                f"{current['lat']:.1f}° / "
                f"{current['lon']:.1f}°"
            )
        )

    with info2:

        st.metric(
            "항해 거리",
            (
                f"{voyage['distance_traveled']:,.1f} NM"
            )
        )

    with info3:

        remaining_distance = max(
            0,
            voyage["route_distance"]
            - voyage["distance_traveled"]
        )

        st.metric(
            "남은 거리",
            (
                f"{remaining_distance:,.1f} NM"
            )
        )

    with info4:

        st.metric(
            "항해 상태",
            voyage_status
        )

    # 진행률 막대
    st.progress(
        min(
            max(
                voyage["progress"],
                0.0
            ),
            1.0
        )
    )

    st.caption(
        f"부산 → "
        f"{voyage['destination']['name']}  |  "
        f"진행률 "
        f"{voyage['progress'] * 100:.1f}%"
    )


show_voyage_map()


# =========================================================
# 지정 항로 안내
# =========================================================

if mode == "지정 항로":

    st.markdown(
        '<div class="section-title">🧭 지정 항로</div>',
        unsafe_allow_html=True
    )

    st.write(
        f"부산에서 "
        f"{st.session_state.selected_destination}까지의 "
        "가상 항로를 따라 공부합니다."
    )


# =========================================================
# 자유형 안내
# =========================================================

elif mode == "자유형":

    st.markdown(
        '<div class="section-title">🌊 자유 항해</div>',
        unsafe_allow_html=True
    )

    st.write(
        f"이번 항해는 부산에서 "
        f"{st.session_state.free_destination} "
        "방향으로 진행됩니다. "
        "초기화하거나 다음 자유 항해를 시작하면 "
        "새로운 목적지가 무작위로 정해집니다."
    )


# =========================================================
# 뽀모도로 안내
# =========================================================

else:

    st.markdown(
        '<div class="section-title">🍅 뽀모도로 항해</div>',
        unsafe_allow_html=True
    )

    route = " → ".join(
        port["name"]
        for port in POMODORO_ROUTE
    )

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
                25분 집중하면 부산에서 속초 방향으로
                항해 거리가 누적됩니다.
            </div>

        </div>
        """,
        unsafe_allow_html=True
    )


# =========================================================
# 마지막 안내
# =========================================================

st.markdown("---")

st.markdown(
    '<div class="section-title">✦ 항해 안내</div>',
    unsafe_allow_html=True
)

st.write(
    "공부한 시간은 실제 GPS가 아니라 "
    "학습 진행도를 표현하기 위한 가상 항해 거리입니다."
)

st.write(
    "정박해도 현재 위치와 누적 시간은 그대로 유지되며, "
    "다시 출항하면 그 위치에서 항해가 이어집니다."
)
