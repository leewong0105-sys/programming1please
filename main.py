# main.py

import streamlit as st
import pandas as pd
import math
import os
from datetime import datetime, timedelta, timezone


# =========================================================
# 기본 설정
# =========================================================

st.set_page_config(
    page_title="Celestial Logbook",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =========================================================
# 한국 시간
# =========================================================

KST = timezone(timedelta(hours=9))


def get_kst_now():
    """현재 한국 시간을 반환"""
    return datetime.now(KST)


# =========================================================
# 데이터 설정
# =========================================================

LOG_FILE = "log.csv"

# 공부 1분 = 1해리
NAUTICAL_MILES_PER_MINUTE = 1.0


# =========================================================
# 항해 목적지
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
# 해리 계산
# =========================================================

def haversine_nm(lat1, lon1, lat2, lon2):
    """
    두 지점 사이의 거리를 해리(NM)로 계산
    """

    R = 6371.0  # 지구 반지름(km)

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

    km = R * c

    # 1해리 = 1.852km
    nm = km / 1.852

    return nm


# =========================================================
# 부산 기준 목적지 거리
# =========================================================

BUSAN_LAT = 35.1796
BUSAN_LON = 129.0756


def get_destination_distance(destination):
    """부산에서 목적지까지의 거리를 해리로 계산"""

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
    """
    날짜를 기준으로 대략적인 달의 위상을 계산
    """

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
# 로그 파일 생성
# =========================================================

def initialize_log_file():
    """log.csv가 없으면 새로 생성"""

    if not os.path.exists(LOG_FILE):

        df = pd.DataFrame(
            columns=[
                "날짜",
                "모드",
                "시작시각",
                "종료시각",
                "소요시간(분)",
                "전진거리(해리)"
            ]
        )

        df.to_csv(
            LOG_FILE,
            index=False,
            encoding="utf-8-sig"
        )


# =========================================================
# 공부 기록 저장
# =========================================================

def save_session(start_time, end_time, mode):
    """공부 세션을 log.csv에 저장"""

    duration_seconds = (
        end_time - start_time
    ).total_seconds()

    minutes = max(
        0,
        round(duration_seconds / 60, 1)
    )

    distance = minutes * NAUTICAL_MILES_PER_MINUTE

    new_data = pd.DataFrame(
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

    new_data.to_csv(
        LOG_FILE,
        mode="a",
        header=False,
        index=False,
        encoding="utf-8-sig"
    )


# =========================================================
# 세션 상태 초기화
# =========================================================

if "timer_running" not in st.session_state:
    st.session_state.timer_running = False

if "timer_finished" not in st.session_state:
    st.session_state.timer_finished = False

if "start_time" not in st.session_state:
    st.session_state.start_time = None

if "selected_mode" not in st.session_state:
    st.session_state.selected_mode = "자유형"

if "selected_destination" not in st.session_state:
    st.session_state.selected_destination = "도쿄"

if "last_saved_start" not in st.session_state:
    st.session_state.last_saved_start = None


# =========================================================
# CSS
# =========================================================

st.markdown(
    """
    <style>

    /* 전체 배경 */
    .stApp {
        background-color: #07111f;
        color: #f4efe2;
    }

    /* 메인 영역 */
    .block-container {
        max-width: 1100px;
        padding-top: 3rem;
        padding-bottom: 4rem;
    }

    /* 사이드바 */
    section[data-testid="stSidebar"] {
        background-color: #091827;
        border-right: 1px solid #b99a55;
    }

    /* 제목 */
    .main-title {
        font-size: 3.5rem;
        font-weight: 700;
        color: #d8b66a;
        letter-spacing: 0.05em;
        margin-bottom: 0.2rem;
    }

    .subtitle {
        color: #aeb8c4;
        font-size: 1.05rem;
        margin-bottom: 2.5rem;
    }

    /* 카드 */
    .info-card {
        background-color: #0d1b2a;
        border: 1px solid #31465d;
        border-radius: 14px;
        padding: 22px;
        margin-bottom: 18px;
    }

    .card-title {
        color: #d8b66a;
        font-size: 0.9rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        margin-bottom: 8px;
    }

    .card-value {
        color: #f4efe2;
        font-size: 1.5rem;
        font-weight: 600;
    }

    /* 타이머 */
    .timer-box {
        background-color: #081522;
        border: 1px solid #8e743d;
        border-radius: 18px;
        padding: 45px 20px;
        text-align: center;
        margin: 25px 0;
    }

    .timer-label {
        color: #aeb8c4;
        font-size: 0.95rem;
        letter-spacing: 0.15em;
        margin-bottom: 10px;
    }

    .timer-number {
        color: #f1d58b;
        font-size: 5rem;
        font-weight: 700;
        letter-spacing: 0.05em;
        line-height: 1;
    }

    /* 구분선 */
    hr {
        border-color: #26384a !important;
    }

    /* 버튼 */
    .stButton > button {
        border-radius: 10px;
        min-height: 45px;
        font-weight: 600;
    }

    /* 입력창 */
    div[data-baseweb="select"] > div {
        background-color: #0d1b2a;
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
            font-size:1.4rem;
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
            color:#aeb8c4;
            font-size:0.9rem;
            line-height:1.6;
            margin-bottom:25px;
        ">
        공부한 시간을 항해 거리로 바꾸어<br>
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
        index=0,
        label_visibility="collapsed"
    )

    st.session_state.selected_mode = mode

    if mode == "지정 항로":

        destination = st.selectbox(
            "목적지",
            list(DESTINATIONS.keys())
        )

        st.session_state.selected_destination = destination

        destination_distance = get_destination_distance(
            destination
        )

        st.caption(
            f"부산 → {destination} "
            f"약 {destination_distance:,.0f} NM"
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
# 메인 제목
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
# 현재 상태 카드
# =========================================================

col1, col2, col3 = st.columns(3)

with col1:

    st.markdown(
        f"""
        <div class="info-card">
            <div class="card-title">CURRENT MODE</div>
            <div class="card-value">
                {st.session_state.selected_mode}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


with col2:

    if mode == "지정 항로":

        target_text = st.session_state.selected_destination

    elif mode == "뽀모도로":

        target_text = "25분 항해"

    else:

        target_text = "자유 항해"

    st.markdown(
        f"""
        <div class="info-card">
            <div class="card-title">DESTINATION</div>
            <div class="card-value">
                {target_text}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


with col3:

    if mode == "뽀모도로":
        duration_text = "25 min"
    else:
        duration_text = "자유 시간"

    st.markdown(
        f"""
        <div class="info-card">
            <div class="card-title">VOYAGE</div>
            <div class="card-value">
                {duration_text}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


# =========================================================
# 타이머 계산 함수
# =========================================================

def get_elapsed_seconds():

    if st.session_state.start_time is None:
        return 0

    now = get_kst_now()

    elapsed = (
        now - st.session_state.start_time
    ).total_seconds()

    return max(0, int(elapsed))


# =========================================================
# 타이머 영역
# =========================================================

elapsed_seconds = get_elapsed_seconds()


# 뽀모도로는 25분 제한
if mode == "뽀모도로":

    total_seconds = 25 * 60

    remaining_seconds = max(
        0,
        total_seconds - elapsed_seconds
    )

    minutes = remaining_seconds // 60
    seconds = remaining_seconds % 60

    timer_text = f"{minutes:02d}:{seconds:02d}"

else:

    minutes = elapsed_seconds // 60
    seconds = elapsed_seconds % 60

    timer_text = f"{minutes:02d}:{seconds:02d}"


st.markdown(
    f"""
    <div class="timer-box">
        <div class="timer-label">
            CURRENT VOYAGE
        </div>
        <div class="timer-number">
            {timer_text}
        </div>
    </div>
    """,
    unsafe_allow_html=True
)


# =========================================================
# 타이머 상태 표시
# =========================================================

if st.session_state.timer_running:

    if mode == "뽀모도로":

        st.info("⚓ 25분 항해 중입니다. 집중하세요.")

    else:

        st.info("⚓ 항해 중입니다. 공부에 집중하세요.")

elif st.session_state.timer_finished:

    st.success("⚓ 항해가 완료되었습니다.")

else:

    st.caption(
        "출항 버튼을 누르면 공부 시간이 항해 거리로 기록됩니다."
    )


# =========================================================
# 버튼
# =========================================================

button_col1, button_col2, button_col3 = st.columns(3)


# ---------------------------------------------------------
# 출항
# ---------------------------------------------------------

with button_col1:

    start_clicked = st.button(
        "⚓ 출항",
        use_container_width=True,
        disabled=st.session_state.timer_running
    )


# ---------------------------------------------------------
# 잠시 정박
# ---------------------------------------------------------

with button_col2:

    stop_clicked = st.button(
        "⏸ 정박",
        use_container_width=True,
        disabled=not st.session_state.timer_running
    )


# ---------------------------------------------------------
# 초기화
# ---------------------------------------------------------

with button_col3:

    reset_clicked = st.button(
        "↻ 초기화",
        use_container_width=True
    )


# =========================================================
# 출항 처리
# =========================================================

if start_clicked:

    st.session_state.start_time = get_kst_now()

    st.session_state.timer_running = True

    st.session_state.timer_finished = False

    st.session_state.last_saved_start = None

    st.rerun()


# =========================================================
# 정박 처리
# =========================================================

if stop_clicked:

    if st.session_state.start_time is not None:

        end_time = get_kst_now()

        # 이미 저장된 세션인지 확인
        if (
            st.session_state.last_saved_start
            != st.session_state.start_time
        ):

            save_session(
                st.session_state.start_time,
                end_time,
                mode
            )

            st.session_state.last_saved_start = (
                st.session_state.start_time
            )

    st.session_state.timer_running = False

    st.session_state.timer_finished = True

    st.rerun()


# =========================================================
# 초기화 처리
# =========================================================

if reset_clicked:

    st.session_state.timer_running = False

    st.session_state.timer_finished = False

    st.session_state.start_time = None

    st.session_state.last_saved_start = None

    st.rerun()


# =========================================================
# 뽀모도로 자동 종료
# =========================================================

if (
    st.session_state.timer_running
    and mode == "뽀모도로"
    and elapsed_seconds >= 25 * 60
):

    end_time = (
        st.session_state.start_time
        + timedelta(minutes=25)
    )

    if (
        st.session_state.last_saved_start
        != st.session_state.start_time
    ):

        save_session(
            st.session_state.start_time,
            end_time,
            mode
        )

        st.session_state.last_saved_start = (
            st.session_state.start_time
        )

    st.session_state.timer_running = False

    st.session_state.timer_finished = True

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

        if not log_df.empty:

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

    st.markdown("---")

    st.markdown("### 🧭 항로 진행도")

    st.progress(progress)

    progress_col1, progress_col2 = st.columns(2)

    with progress_col1:

        st.metric(
            "현재까지 전진",
            f"{total_distance:,.1f} NM"
        )

    with progress_col2:

        st.metric(
            "목적지까지",
            f"{destination_distance:,.0f} NM"
        )

    if progress >= 1:

        st.success(
            f"🎉 {st.session_state.selected_destination}에 도착했습니다!"
        )

    else:

        remaining = destination_distance - total_distance

        st.caption(
            f"목적지까지 약 {remaining:,.1f} NM 남았습니다."
        )


# =========================================================
# 뽀모도로 설명
# =========================================================

if mode == "뽀모도로":

    st.markdown("---")

    st.markdown("### 🍅 뽀모도로 항해")

    route_text = " → ".join(POMODORO_ROUTE)

    st.markdown(
        f"""
        <div class="info-card">

        <div class="card-title">CURRENT ROUTE</div>

        <div style="
            color:#f4efe2;
            font-size:1.15rem;
            margin-bottom:12px;
        ">
        {route_text}
        </div>

        <div style="
            color:#aeb8c4;
            line-height:1.7;
        ">
        25분 집중 공부를 완료하면 하나의 항해 기록이 남습니다.
        </div>

        </div>
        """,
        unsafe_allow_html=True
    )


# =========================================================
# 오늘의 안내
# =========================================================

st.markdown("---")

st.markdown("### ✦ 항해 안내")

if mode == "자유형":

    st.write(
        "원하는 만큼 자유롭게 공부하세요. "
        "정박 버튼을 누르면 공부 시간이 항해일지에 기록됩니다."
    )

elif mode == "지정 항로":

    st.write(
        f"부산에서 {st.session_state.selected_destination}까지의 "
        "가상 항로를 따라 공부합니다."
    )

else:

    st.write(
        "25분 동안 집중하고 항해 기록을 남겨보세요."
    )


# =========================================================
# 자동 새로고침
# =========================================================

if st.session_state.timer_running:

    try:

        st.fragment(run_every=1)

    except Exception:

        pass
