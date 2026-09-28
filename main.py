import streamlit as st
import pandas as pd
import math
import random
import os
from datetime import datetime, date, timezone, timedelta


# ============================================================
# 기본 설정
# ============================================================

st.set_page_config(
    page_title="Celestial Logbook",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# 공부 1분 = 1해리
NAUTICAL_MILES_PER_MINUTE = 1.0

# 뽀모도로 고정 시간
POMODORO_MINUTES = 25

# 로그 파일
LOG_FILE = "log.csv"

# 한국(인천) 출발 좌표
INCHEON_LAT = 37.4602
INCHEON_LON = 126.4407

# ============================================================
# 목적지 목록
# ============================================================

DESTINATIONS = {
    "도쿄": {
        "country": "일본",
        "lat": 35.6762,
        "lon": 139.6503,
    },
    "상하이": {
        "country": "중국",
        "lat": 31.2304,
        "lon": 121.4737,
    },
    "싱가포르": {
        "country": "싱가포르",
        "lat": 1.3521,
        "lon": 103.8198,
    },
    "시드니": {
        "country": "호주",
        "lat": -33.8688,
        "lon": 151.2093,
    },
    "호놀룰루": {
        "country": "미국",
        "lat": 21.3069,
        "lon": -157.8583,
    },
    "밴쿠버": {
        "country": "캐나다",
        "lat": 49.2827,
        "lon": -123.1207,
    },
    "로스앤젤레스": {
        "country": "미국",
        "lat": 34.0522,
        "lon": -118.2437,
    },
    "런던": {
        "country": "영국",
        "lat": 51.5074,
        "lon": -0.1278,
    },
    "파리": {
        "country": "프랑스",
        "lat": 48.8566,
        "lon": 2.3522,
    },
    "뉴욕": {
        "country": "미국",
        "lat": 40.7128,
        "lon": -74.0060,
    },
}


# ============================================================
# 뽀모도로 국내 해역 순환 루트
# ============================================================

POMODORO_ROUTE = [
    {
        "name": "부산",
        "lat": 35.1796,
        "lon": 129.0756,
    },
    {
        "name": "울산",
        "lat": 35.5384,
        "lon": 129.3114,
    },
    {
        "name": "포항",
        "lat": 36.0190,
        "lon": 129.3435,
    },
    {
        "name": "동해",
        "lat": 37.5247,
        "lon": 129.1143,
    },
    {
        "name": "속초",
        "lat": 38.2070,
        "lon": 128.5918,
    },
]


# ============================================================
# 월별 대표 별자리
# ============================================================

CONSTELLATIONS = {
    1: ("겨울철", "오리온자리"),
    2: ("겨울철", "큰개자리"),
    3: ("봄철", "사자자리"),
    4: ("봄철", "목동자리"),
    5: ("봄철", "처녀자리"),
    6: ("여름철", "전갈자리"),
    7: ("여름철", "백조자리"),
    8: ("여름철", "독수리자리"),
    9: ("가을철", "페가수스자리"),
    10: ("가을철", "안드로메다자리"),
    11: ("가을철", "황소자리"),
    12: ("겨울철", "오리온자리"),
}


# ============================================================
# CSS
# ============================================================

st.markdown(
    """
    <style>
    .stApp {
        background:
            radial-gradient(
                circle at 50% -20%,
                rgba(184, 146, 61, 0.10),
                transparent 38%
            ),
            #071321;
        color: #E8E2D5;
    }

    .block-container {
        max-width: 1100px;
        padding-top: 2.5rem;
        padding-bottom: 4rem;
    }

    h1, h2, h3 {
        color: #E8E2D5 !important;
        letter-spacing: -0.02em;
    }

    .title {
        color: #C7A65A;
        font-size: 0.78rem;
        letter-spacing: 0.28em;
        text-transform: uppercase;
        margin-bottom: 0.4rem;
    }

    .subtitle {
        color: #9CA9B7;
        font-size: 0.95rem;
        margin-bottom: 2rem;
    }

    .gold-line {
        height: 1px;
        background: linear-gradient(
            90deg,
            transparent,
            #B8954A,
            transparent
        );
        margin: 1rem 0 2rem 0;
    }

    .metric-card {
        background: rgba(13, 29, 47, 0.92);
        border: 1px solid rgba(199, 166, 90, 0.24);
        border-radius: 14px;
        padding: 1.1rem 1.25rem;
        min-height: 110px;
    }

    .metric-label {
        color: #8F9BA8;
        font-size: 0.78rem;
        margin-bottom: 0.4rem;
    }

    .metric-value {
        color: #E8D09A;
        font-size: 1.65rem;
        font-weight: 600;
    }

    .section-card {
        background: rgba(10, 24, 39, 0.88);
        border: 1px solid rgba(199, 166, 90, 0.18);
        border-radius: 16px;
        padding: 1.4rem;
        margin-top: 1rem;
        margin-bottom: 1rem;
    }

    .destination {
        color: #D9C28A;
        font-size: 1.25rem;
        font-weight: 600;
    }

    .timer {
        color: #E8D09A;
        font-size: 4.5rem;
        font-weight: 300;
        letter-spacing: 0.04em;
        text-align: center;
        margin: 1.5rem 0;
    }

    .status {
        text-align: center;
        color: #9CA9B7;
        font-size: 0.9rem;
    }

    .success-box {
        background: rgba(64, 92, 65, 0.20);
        border: 1px solid rgba(144, 173, 118, 0.35);
        border-radius: 14px;
        padding: 1rem 1.2rem;
        color: #D8E5CE;
        margin: 1rem 0;
    }

    .sky-card {
        background:
            linear-gradient(
                145deg,
                rgba(15, 35, 57, 0.95),
                rgba(8, 20, 34, 0.95)
            );
        border: 1px solid rgba(199, 166, 90, 0.28);
        border-radius: 16px;
        padding: 1.5rem;
        margin-top: 1rem;
    }

    .sky-title {
        color: #C7A65A;
        font-size: 0.78rem;
        letter-spacing: 0.15em;
        margin-bottom: 0.8rem;
    }

    .sky-text {
        color: #D7DDE4;
        line-height: 1.8;
    }

    .route {
        color: #AEB8C3;
        font-size: 0.9rem;
        margin-top: 0.5rem;
    }

    div.stButton > button {
        border-radius: 10px;
        border: 1px solid #9F7F3F;
        background: #9F7F3F;
        color: #071321;
        font-weight: 600;
        min-height: 44px;
    }

    div.stButton > button:hover {
        border-color: #C7A65A;
        background: #C7A65A;
        color: #071321;
    }

    div[data-testid="stProgressBar"] > div > div > div {
        background-color: #B8954A;
    }

    .small-note {
        color: #788696;
        font-size: 0.78rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# 함수
# ============================================================

def get_kst_now():
    """현재 한국 시간."""
    return datetime.now(timezone(timedelta(hours=9)))


def format_datetime(dt):
    if dt is None:
        return "-"
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def format_duration(seconds):
    seconds = max(0, int(seconds))
    minutes = seconds // 60
    secs = seconds % 60
    return f"{minutes:02d}:{secs:02d}"


def haversine_nm(lat1, lon1, lat2, lon2):
    """
    하버사인 공식으로 두 좌표 사이의 대권항로 거리를 계산.
    결과 단위: 해리(NM)
    """
    earth_radius_km = 6371.0088

    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)

    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1_rad)
        * math.cos(lat2_rad)
        * math.sin(dlon / 2) ** 2
    )

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distance_km = earth_radius_km * c

    # 1 해리 = 1.852 km
    distance_nm = distance_km / 1.852

    return distance_nm


def get_moon_phase(target_date):
    """
    2000-01-06을 삭(New Moon) 기준일로 사용하는
    간소화된 달의 위상 계산.
    """
    reference = date(2000, 1, 6)

    days = (target_date - reference).days

    synodic_month = 29.53058867

    phase_day = days % synodic_month

    if phase_day < 1.84566:
        return "신월"
    elif phase_day < 7.38265:
        return "초승달"
    elif phase_day < 9.22331:
        return "상현달"
    elif phase_day < 14.76529:
        return "보름달"
    elif phase_day < 22.14794:
        return "하현달"
    elif phase_day < 27.68493:
        return "그믐달"
    else:
        return "신월"


def get_sky_information(target_date):
    phase = get_moon_phase(target_date)

    season, constellation = CONSTELLATIONS[target_date.month]

    phase_expression = {
        "신월": "달이 거의 보이지 않고",
        "초승달": "초승달이 떠 있고",
        "상현달": "반달인 상현달이 떠 있고",
        "보름달": "보름달이 떠 있고",
        "하현달": "반달인 하현달이 떠 있고",
        "그믐달": "그믐달이 떠 있고",
    }

    sentence = (
        f"오늘 밤하늘엔 {phase_expression[phase]} "
        f"{season} 대표 별자리인 {constellation}을 볼 수 있어요."
    )

    return phase, constellation, season, sentence


def load_log():
    columns = [
        "날짜",
        "모드",
        "시작시각",
        "종료시각",
        "소요시간(분)",
        "전진거리(해리)",
    ]

    if not os.path.exists(LOG_FILE):
        return pd.DataFrame(columns=columns)

    try:
        df = pd.read_csv(LOG_FILE)

        for column in columns:
            if column not in df.columns:
                df[column] = None

        return df[columns]

    except Exception:
        return pd.DataFrame(columns=columns)


def append_log(session_data):
    columns = [
        "날짜",
        "모드",
        "시작시각",
        "종료시각",
        "소요시간(분)",
        "전진거리(해리)",
    ]

    new_row = pd.DataFrame(
        [{
            "날짜": session_data["date"],
            "모드": session_data["mode"],
            "시작시각": format_datetime(session_data["start"]),
            "종료시각": format_datetime(session_data["end"]),
            "소요시간(분)": session_data["minutes"],
            "전진거리(해리)": session_data["distance"],
        }],
        columns=columns,
    )

    file_exists = os.path.exists(LOG_FILE)

    new_row.to_csv(
        LOG_FILE,
        mode="a",
        header=not file_exists,
        index=False,
        encoding="utf-8-sig",
    )


def get_today_logged_minutes(df):
    if df.empty:
        return 0.0

    today_str = get_kst_now().strftime("%Y-%m-%d")

    today_rows = df[df["날짜"].astype(str) == today_str]

    if today_rows.empty:
        return 0.0

    return pd.to_numeric(
        today_rows["소요시간(분)"],
        errors="coerce",
    ).fillna(0).sum()


def initialize_state():
    defaults = {
        "status": "대기",
        "mode": "자유형",

        "start_time": None,
        "end_time": None,

        "current_destination": None,
        "current_target_distance": None,

        "current_session_minutes": 0.0,
        "current_session_distance": 0.0,

        "completed_session": None,

        "pomodoro_index": 0,
        "pomodoro_today_count": 0,

        "log_df": load_log(),
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def start_session(mode, destination=None):
    now = get_kst_now()

    st.session_state.status = "진행"
    st.session_state.mode = mode
    st.session_state.start_time = now
    st.session_state.end_time = None

    st.session_state.current_session_minutes = 0.0
    st.session_state.current_session_distance = 0.0

    st.session_state.current_destination = destination

    if mode == "지정" and destination:
        target = DESTINATIONS[destination]

        st.session_state.current_target_distance = haversine_nm(
            INCHEON_LAT,
            INCHEON_LON,
            target["lat"],
            target["lon"],
        )

    else:
        st.session_state.current_target_distance = None

    st.session_state.completed_session = None


def finish_session(end_time=None):
    if st.session_state.start_time is None:
        return

    if end_time is None:
        end_time = get_kst_now()

    elapsed_seconds = (
        end_time - st.session_state.start_time
    ).total_seconds()

    elapsed_seconds = max(0, elapsed_seconds)

    minutes = elapsed_seconds / 60
    distance = minutes * NAUTICAL_MILES_PER_MINUTE

    # 뽀모도로는 최대 25분
    if st.session_state.mode == "뽀모도로":
        minutes = min(minutes, POMODORO_MINUTES)
        distance = minutes * NAUTICAL_MILES_PER_MINUTE

    st.session_state.current_session_minutes = minutes
    st.session_state.current_session_distance = distance
    st.session_state.end_time = end_time

    st.session_state.completed_session = {
        "date": end_time.strftime("%Y-%m-%d"),
        "mode": st.session_state.mode,
        "start": st.session_state.start_time,
        "end": end_time,
        "minutes": minutes,
        "distance": distance,
        "destination": st.session_state.current_destination,
    }

    # 뽀모도로 완료 시 다음 지점으로 이동
    if st.session_state.mode == "뽀모도로":
        st.session_state.pomodoro_today_count += 1
        st.session_state.pomodoro_index = (
            st.session_state.pomodoro_index + 1
        ) % len(POMODORO_ROUTE)

    st.session_state.status = "완료"


def save_current_session():
    session = st.session_state.completed_session

    if session is None:
        return

    append_log(session)

    st.session_state.log_df = load_log()

    st.session_state.completed_session = None
    st.session_state.start_time = None
    st.session_state.end_time = None
    st.session_state.current_session_minutes = 0.0
    st.session_state.current_session_distance = 0.0
    st.session_state.current_destination = None
    st.session_state.current_target_distance = None

    st.session_state.status = "대기"


# ============================================================
# 초기화
# ============================================================

initialize_state()

log_df = st.session_state.log_df


# ============================================================
# 헤더
# ============================================================

st.markdown(
    '<div class="title">CELESTIAL LOGBOOK</div>',
    unsafe_allow_html=True,
)

st.title("공부한 만큼, 항해한다")

st.markdown(
    '<div class="subtitle">'
    '공부 시간을 항해 거리로 환산해 오늘의 항로를 만들어 보세요.'
    '</div>',
    unsafe_allow_html=True,
)

st.markdown('<div class="gold-line"></div>', unsafe_allow_html=True)


# ============================================================
# 오늘 누적 항해 시간
# ============================================================

logged_minutes = get_today_logged_minutes(log_df)

# 완료됐지만 아직 기록하지 않은 현재 세션도 오늘 누적에 포함
unlogged_minutes = 0.0

if (
    st.session_state.status == "완료"
    and st.session_state.completed_session is not None
):
    unlogged_minutes = st.session_state.completed_session["minutes"]

today_total_minutes = logged_minutes + unlogged_minutes

hours = int(today_total_minutes // 60)
minutes = int(today_total_minutes % 60)

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">오늘 누적 항해 시간</div>
            <div class="metric-value">{hours:02d}시간 {minutes:02d}분</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col2:
    today_nm = today_total_minutes * NAUTICAL_MILES_PER_MINUTE

    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">오늘 누적 전진 거리</div>
            <div class="metric-value">{today_nm:,.1f} NM</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col3:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">현재 항해 상태</div>
            <div class="metric-value">{st.session_state.status}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# 진행 중 화면
# ============================================================

if st.session_state.status == "진행":

    @st.fragment(run_every=1)
    def running_timer():
        start = st.session_state.start_time
        now = get_kst_now()

        elapsed_seconds = (now - start).total_seconds()
        elapsed_seconds = max(0, elapsed_seconds)

        # 뽀모도로 25분 자동 완료
        if (
            st.session_state.mode == "뽀모도로"
            and elapsed_seconds >= POMODORO_MINUTES * 60
        ):
            finish_session(
                start + timedelta(minutes=POMODORO_MINUTES)
            )
            st.rerun()

        elapsed_minutes = elapsed_seconds / 60

        if st.session_state.mode == "뽀모도로":
            progress = min(
                elapsed_seconds / (POMODORO_MINUTES * 60),
                1.0,
            )
        elif (
            st.session_state.mode == "지정"
            and st.session_state.current_target_distance
        ):
            progress = min(
                (
                    elapsed_minutes
                    * NAUTICAL_MILES_PER_MINUTE
                    / st.session_state.current_target_distance
                ),
                1.0,
            )
        else:
            # 자유형은 특정 도착점이 없으므로 시간 진행률 표시
            # 60분을 하나의 참고 항로 단위로 사용
            progress = min(elapsed_minutes / 60, 1.0)

        st.markdown('<div class="section-card">', unsafe_allow_html=True)

        st.markdown(
            '<div class="status">현재 항해 중</div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            f'<div class="timer">{format_duration(elapsed_seconds)}</div>',
            unsafe_allow_html=True,
        )

        st.progress(progress)

        current_nm = elapsed_minutes * NAUTICAL_MILES_PER_MINUTE

        left, right = st.columns(2)

        with left:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-label">현재 전진 거리</div>
                    <div class="metric-value">{current_nm:,.1f} NM</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with right:

            if st.session_state.mode == "지정":
                target = st.session_state.current_target_distance

                if target:
                    percent = min(current_nm / target * 100, 100)

                    st.markdown(
                        f"""
                        <div class="metric-card">
                            <div class="metric-label">목적지까지</div>
                            <div class="metric-value">
                                {percent:.1f}%
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

            elif st.session_state.mode == "뽀모도로":
                remaining = max(
                    0,
                    POMODORO_MINUTES - elapsed_minutes,
                )

                st.markdown(
                    f"""
                    <div class="metric-card">
                        <div class="metric-label">남은 집중 시간</div>
                        <div class="metric-value">
                            {int(remaining):02d}분
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            else:
                st.markdown(
                    """
                    <div class="metric-card">
                        <div class="metric-label">현재 모드</div>
                        <div class="metric-value">자유 항해</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        st.markdown("</div>", unsafe_allow_html=True)

        # 목적지 정보
        if st.session_state.mode in ["자유형", "지정"]:
            destination = st.session_state.current_destination

            if destination:
                info = DESTINATIONS[destination]

                st.markdown(
                    f"""
                    <div class="section-card">
                        <div class="metric-label">현재 목적지</div>
                        <div class="destination">
                            {destination}
                        </div>
                        <div class="route">
                            {info["country"]}
                            · 위도 {info["lat"]:.4f}
                            · 경도 {info["lon"]:.4f}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        else:
            current = POMODORO_ROUTE[
                st.session_state.pomodoro_index
            ]

            next_index = (
                st.session_state.pomodoro_index + 1
            ) % len(POMODORO_ROUTE)

            next_point = POMODORO_ROUTE[next_index]

            st.markdown(
                f"""
                <div class="section-card">
                    <div class="metric-label">현재 순찰 구간</div>
                    <div class="destination">
                        {current["name"]}
                        → {next_point["name"]}
                    </div>
                    <div class="route">
                        오늘 제 {st.session_state.pomodoro_today_count + 1}번째 순찰
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        if st.button(
            "정지 / 도착",
            type="primary",
            use_container_width=True,
            key="stop_session",
        ):
            finish_session()
            st.rerun()


    running_timer()

    st.stop()


# ============================================================
# 완료 화면
# ============================================================

if st.session_state.status == "완료":

    session = st.session_state.completed_session

    st.subheader("항해 완료")

    destination_text = ""

    if session["destination"]:
        destination_text = (
            f" · 목적지 {session['destination']}"
        )

    if (
        session["mode"] == "지정"
        and st.session_state.current_target_distance
    ):
        target = st.session_state.current_target_distance

        if session["distance"] >= target:
            st.markdown(
                """
                <div class="success-box">
                    목적지에 도착했습니다.
                    오늘의 항로가 하나 완성되었습니다.
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            percent = (
                session["distance"]
                / target
                * 100
            )

            st.info(
                f"이번 세션은 목적지까지 "
                f"{percent:.1f}% 전진했습니다."
            )

    elif session["mode"] == "뽀모도로":
        st.markdown(
            """
            <div class="success-box">
                25분 순찰을 완료했습니다.
                다음 순찰 지점으로 항로가 이동했습니다.
            </div>
            """,
            unsafe_allow_html=True,
        )

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">시작 시각</div>
                <div class="metric-value" style="font-size:1rem">
                    {format_datetime(session["start"])}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">종료 시각</div>
                <div class="metric-value" style="font-size:1rem">
                    {format_datetime(session["end"])}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">소요 시간</div>
                <div class="metric-value">
                    {session["minutes"]:.1f}분
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col4:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">이번 세션 전진 거리</div>
                <div class="metric-value">
                    {session["distance"]:.1f} NM
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # --------------------------------------------------------
    # 천문 정보
    # --------------------------------------------------------

    phase, constellation, season, sky_sentence = (
        get_sky_information(
            session["end"].date()
        )
    )

    st.markdown(
        f"""
        <div class="sky-card">
            <div class="sky-title">TONIGHT'S SKY</div>

            <h3>천문 정보</h3>

            <div class="sky-text">
                <strong>달의 위상</strong> · {phase}<br>
                <strong>대표 별자리</strong> ·
                {season} {constellation}<br><br>
                {sky_sentence}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("")

    if st.button(
        "항해일지에 기록하기",
        type="primary",
        use_container_width=True,
        key="save_session",
    ):
        save_current_session()
        st.success(
            "항해일지에 기록했습니다."
        )
        st.rerun()

    st.stop()


# ============================================================
# 대기 상태
# ============================================================

st.subheader("출항 준비")

# ------------------------------------------------------------
# 모드 선택
# ------------------------------------------------------------

mode = st.segmented_control(
    "항해 방식",
    options=["자유형", "지정", "뽀모도로"],
    default=st.session_state.mode,
    key="mode_selector",
)

if mode is None:
    mode = "자유형"


# ------------------------------------------------------------
# 자유형
# ------------------------------------------------------------

selected_destination = None

if mode == "자유형":

    st.markdown(
        '<div class="section-card">',
        unsafe_allow_html=True,
    )

    st.markdown("#### 목적지 설정")

    destination_method = st.radio(
        "목적지를 어떻게 정할까요?",
        ["무작위 배정", "직접 선택"],
        horizontal=True,
        key="free_destination_method",
    )

    if destination_method == "무작위 배정":

        st.markdown(
            """
            <div class="small-note">
                출항하는 순간 10개의 항구 중 하나가 무작위로 배정됩니다.
            </div>
            """,
            unsafe_allow_html=True,
        )

    else:

        selected_destination = st.selectbox(
            "경유지 선택",
            list(DESTINATIONS.keys()),
            key="free_destination",
        )

    st.markdown(
        "</div>",
        unsafe_allow_html=True,
    )


# ------------------------------------------------------------
# 지정
# ------------------------------------------------------------

elif mode == "지정":

    st.markdown(
        '<div class="section-card">',
        unsafe_allow_html=True,
    )

    st.markdown("#### 목적지 지정")

    selected_destination = st.selectbox(
        "인천에서 출발할 목적지를 선택하세요.",
        list(DESTINATIONS.keys()),
        key="fixed_destination",
    )

    if selected_destination:

        destination = DESTINATIONS[selected_destination]

        distance = haversine_nm(
            INCHEON_LAT,
            INCHEON_LON,
            destination["lat"],
            destination["lon"],
        )

        estimated_minutes = (
            distance
            / NAUTICAL_MILES_PER_MINUTE
        )

        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">
                    인천 → {selected_destination} 대권항로
                </div>
                <div class="metric-value">
                    {distance:,.1f} NM
                </div>
                <div class="route">
                    현재 환산 속도 기준 약
                    {estimated_minutes:,.0f}분의 공부가 필요합니다.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        "</div>",
        unsafe_allow_html=True,
    )


# ------------------------------------------------------------
# 뽀모도로
# ------------------------------------------------------------

else:

    current = POMODORO_ROUTE[
        st.session_state.pomodoro_index
    ]

    next_index = (
        st.session_state.pomodoro_index + 1
    ) % len(POMODORO_ROUTE)

    next_point = POMODORO_ROUTE[next_index]

    st.markdown(
        f"""
        <div class="section-card">
            <div class="metric-label">국내 해역 순찰</div>

            <div class="destination">
                {current["name"]}
                → {next_point["name"]}
            </div>

            <div class="route">
                25분 집중 · 오늘 제
                {st.session_state.pomodoro_today_count + 1}번째 순찰
            </div>

            <br>

            <div class="small-note">
                부산 → 울산 → 포항 → 동해 → 속초 →
                다시 부산으로 이어지는 순환 항로입니다.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ------------------------------------------------------------
# 출항 버튼
# ------------------------------------------------------------

st.markdown("")

if st.button(
    "출항하기",
    type="primary",
    use_container_width=True,
    key="start_session",
):

    actual_destination = selected_destination

    if mode == "자유형":

        if st.session_state.free_destination_method == "무작위 배정":
            actual_destination = random.choice(
                list(DESTINATIONS.keys())
            )

    elif mode == "뽀모도로":

        current = POMODORO_ROUTE[
            st.session_state.pomodoro_index
        ]

        actual_destination = current["name"]

    start_session(
        mode=mode,
        destination=actual_destination,
    )

    st.rerun()


# ============================================================
# 하단 안내
# ============================================================

st.markdown('<div class="gold-line"></div>', unsafe_allow_html=True)

st.markdown(
    """
    <div class="small-note">
        공부 1분 = 1해리(NM) ·
        기록은 항해일지에 저장한 세션을 기준으로 누적됩니다.
    </div>
    """,
    unsafe_allow_html=True,
)
