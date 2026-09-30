# main.py

import streamlit as st
import pandas as pd
import math
import os
from datetime import datetime, timedelta, timezone


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


# =========================================================
# 목적지
# =========================================================

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
# 뽀모도로 항로
# =========================================================

POMODORO_ROUTE = [
    "부산",
    "울산",
    "포항",
    "동해",
    "속초"
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
    """두 위치 사이의 거리를 해리로 계산"""

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

    return km / 1.852


BUSAN_LAT = 35.1796
BUSAN_LON = 129.0756


def get_destination_distance(destination):

    info = DESTINATIONS[destination]

    return haversine_nm(
        BUSAN_LAT,
        BUSAN_LON,
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

    # 너무 짧은 기록은 0분으로 저장
    minutes = round(minutes, 1)

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

if "timer_running" not in st.session_state:
    st.session_state.timer_running = False

if "start_time" not in st.session_state:
    st.session_state.start_time = None

# 정박할 때 확정되는 누적 시간
if "elapsed_seconds" not in st.session_state:
    st.session_state.elapsed_seconds = 0

if "selected_mode" not in st.session_state:
    st.session_state.selected_mode = "자유형"

if "selected_destination" not in st.session_state:
    st.session_state.selected_destination = "도쿄"

# 현재 출항 구간이 이미 저장되었는지 확인
if "current_session_saved" not in st.session_state:
    st.session_state.current_session_saved = False


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

.timer-box {
    background-color: #081522;
    border: 1px solid #8e743d;
    border-radius: 18px;
    padding: 45px 20px;
    margin: 25px 0;
    text-align: center;
}

.timer-label {
    color: #9daaba;
    font-size: 0.9rem;
    letter-spacing: 0.18em;
    margin-bottom: 15px;
}

.timer-number {
    color: #f1d58b;
    font-size: 5rem;
    font-weight: 700;
    line-height: 1;
    font-variant-numeric: tabular-nums;
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

    st.session_state.selected_mode = mode

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
# 상단 정보
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
        destination_text = st.session_state.selected_destination

    elif mode == "뽀모도로":
        destination_text = "25분 항해"

    else:
        destination_text = "자유 항해"

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
# 현재까지의 실제 경과 시간
# =========================================================

def get_elapsed_seconds():

    # 정박 상태
    if not st.session_state.timer_running:

        return st.session_state.elapsed_seconds

    # 출항 상태인데 시작 시간이 없다면
    if st.session_state.start_time is None:

        return st.session_state.elapsed_seconds

    now = get_kst_now()

    current_seconds = (
        now - st.session_state.start_time
    ).total_seconds()

    return (
        st.session_state.elapsed_seconds
        + max(0, int(current_seconds))
    )


# =========================================================
# 타이머 상태
# =========================================================

if "timer_running" not in st.session_state:
    st.session_state.timer_running = False

if "start_time" not in st.session_state:
    st.session_state.start_time = None

# 정박했을 때 확정된 누적 초
if "elapsed_seconds" not in st.session_state:
    st.session_state.elapsed_seconds = 0

if "pomodoro_saved" not in st.session_state:
    st.session_state.pomodoro_saved = False


# =========================================================
# 현재까지 공부한 시간 계산
# =========================================================

def get_elapsed_seconds():

    # 정박 상태
    if not st.session_state.timer_running:
        return st.session_state.elapsed_seconds

    # 출항 상태인데 시작 시간이 없으면
    if st.session_state.start_time is None:
        return st.session_state.elapsed_seconds

    now = get_kst_now()

    current_seconds = int(
        (now - st.session_state.start_time).total_seconds()
    )

    return (
        st.session_state.elapsed_seconds
        + max(0, current_seconds)
    )


# =========================================================
# 시간 → MM:SS
# =========================================================

def format_time(seconds):

    seconds = max(0, int(seconds))

    minutes = seconds // 60
    seconds = seconds % 60

    return f"{minutes:02d}:{seconds:02d}"


# =========================================================
# 타이머 표시
# =========================================================

@st.fragment(run_every=1)
def show_timer():

    elapsed = get_elapsed_seconds()

    # ---------------------------------------------
    # 뽀모도로
    # ---------------------------------------------

    if st.session_state.selected_mode == "뽀모도로":

        total = 25 * 60

        remaining = max(
            0,
            total - elapsed
        )

        timer_text = format_time(remaining)

    # ---------------------------------------------
    # 일반 타이머
    # ---------------------------------------------

    else:

        timer_text = format_time(elapsed)

    # ---------------------------------------------
    # 화면
    # ---------------------------------------------

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
# 버튼
# =========================================================

col1, col2, col3 = st.columns(3)


with col1:

    start_clicked = st.button(
        "⚓ 출항",
        use_container_width=True,
        disabled=st.session_state.timer_running
    )


with col2:

    stop_clicked = st.button(
        "⏸ 정박",
        use_container_width=True,
        disabled=not st.session_state.timer_running
    )


with col3:

    reset_clicked = st.button(
        "↻ 초기화",
        use_container_width=True
    )


# =========================================================
# 출항
# =========================================================

if start_clicked:

    # 지금부터 새로운 시간 측정 시작
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

        # 이번 출항 구간의 시간
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

        # 누적 시간에 추가
        st.session_state.elapsed_seconds += (
            current_seconds
        )

        # 기록 저장
        save_session(
            st.session_state.start_time,
            now,
            st.session_state.selected_mode
        )

    # 정박
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

    st.rerun()
            

# =========================================================
# 상태 표시
# =========================================================

if st.session_state.timer_running:

    st.info("⚓ 항해 중입니다.")

else:

    if st.session_state.elapsed_seconds > 0:

        st.success("⏸ 정박 중입니다. 다시 출항하면 이어서 진행합니다.")

    else:

        st.caption("출항 버튼을 누르면 항해가 시작됩니다.")


# =========================================================
# 버튼
# =========================================================

button1, button2, button3 = st.columns(3)


with button1:

    start_clicked = st.button(
        "⚓ 출항",
        use_container_width=True,
        disabled=st.session_state.timer_running
    )


with button2:

    stop_clicked = st.button(
        "⏸ 정박",
        use_container_width=True,
        disabled=not st.session_state.timer_running
    )


with button3:

    reset_clicked = st.button(
        "↻ 초기화",
        use_container_width=True
    )


# =========================================================
# 출항
# =========================================================

if start_clicked:

    # 지금부터 새로운 구간 시작
    st.session_state.start_time = get_kst_now()

    st.session_state.timer_running = True

    st.session_state.current_session_saved = False

    st.rerun()


# =========================================================
# 정박
# =========================================================

if stop_clicked:

    now = get_kst_now()

    start = st.session_state.start_time

    if start is not None:

        # 이번 구간의 실제 공부 시간
        segment_seconds = (
            now - start
        ).total_seconds()

        segment_seconds = max(
            0,
            int(segment_seconds)
        )

        # 누적 시간에 추가
        st.session_state.elapsed_seconds += (
            segment_seconds
        )

        # 이번 구간을 항해일지에 저장
        save_session(
            start,
            now,
            st.session_state.selected_mode
        )

    # 정박
    st.session_state.start_time = None

    st.session_state.timer_running = False

    st.session_state.current_session_saved = True

    st.rerun()


# =========================================================
# 초기화
# =========================================================

if reset_clicked:

    st.session_state.timer_running = False

    st.session_state.start_time = None

    st.session_state.elapsed_seconds = 0

    st.session_state.current_session_saved = False

    st.rerun()


# =========================================================
# 지정 항로 진행도
# =========================================================

if mode == "지정 항로":

    initialize_log_file()

    try:

        log_df = pd.read_csv(
            LOG_FILE,
            encoding="utf-8-sig"
        )

        if len(log_df) > 0:

            total_distance = pd.to_numeric(
                log_df["전진거리(해리)"],
                errors="coerce"
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
        1.0
    )

    st.markdown(
        '<div class="section-title">🧭 항로 진행도</div>',
        unsafe_allow_html=True
    )

    st.progress(progress)

    col1, col2 = st.columns(2)

    with col1:

        st.metric(
            "현재까지 전진",
            f"{total_distance:,.1f} NM"
        )

    with col2:

        st.metric(
            "목적지까지",
            f"{destination_distance:,.0f} NM"
        )


# =========================================================
# 뽀모도로 안내
# =========================================================

if mode == "뽀모도로":

    st.markdown(
        '<div class="section-title">🍅 뽀모도로 항해</div>',
        unsafe_allow_html=True
    )

    route = " → ".join(POMODORO_ROUTE)

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
                25분 집중하면 하나의 항해 기록이 저장됩니다.
            </div>

        </div>
        """,
        unsafe_allow_html=True
    )


# =========================================================
# 안내
# =========================================================

st.markdown("---")

st.markdown(
    '<div class="section-title">✦ 항해 안내</div>',
    unsafe_allow_html=True
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
        "25분 동안 집중하면 자동으로 항해가 종료되고 기록됩니다."
    )
