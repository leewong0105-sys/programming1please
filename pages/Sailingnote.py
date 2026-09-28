# pages/Sailingnote.py

import streamlit as st
import pandas as pd
import os
from datetime import datetime, date


# =========================================================
# 기본 설정
# =========================================================

LOG_FILE = "log.csv"


# =========================================================
# 페이지 디자인
# =========================================================

st.markdown(
    """
    <style>

    /* 전체 배경 */
    .stApp {
        background-color: #07111f;
        color: #f4efe2;
    }

    /* 본문 너비 */
    .block-container {
        max-width: 1150px;
        padding-top: 3rem;
        padding-bottom: 4rem;
    }

    /* 제목 */
    .page-title {
        color: #d8b66a;
        font-size: 3rem;
        font-weight: 700;
        letter-spacing: 0.06em;
        margin-bottom: 5px;
    }

    .page-subtitle {
        color: #9daaba;
        font-size: 1rem;
        margin-bottom: 35px;
    }

    /* 통계 카드 */
    .stat-card {
        background: #0d1b2a;
        border: 1px solid #33485e;
        border-radius: 15px;
        padding: 22px;
        height: 130px;
    }

    .stat-title {
        color: #9daaba;
        font-size: 0.85rem;
        margin-bottom: 10px;
        letter-spacing: 0.08em;
    }

    .stat-value {
        color: #f1d58b;
        font-size: 1.8rem;
        font-weight: 700;
    }

    /* 섹션 제목 */
    .section-title {
        color: #d8b66a;
        font-size: 1.35rem;
        font-weight: 700;
        margin-top: 35px;
        margin-bottom: 15px;
    }

    /* 오늘의 항해 */
    .today-card {
        background: #0b1928;
        border: 1px solid #8e743d;
        border-radius: 15px;
        padding: 25px;
        margin-top: 20px;
    }

    .today-label {
        color: #9daaba;
        font-size: 0.85rem;
        margin-bottom: 8px;
    }

    .today-value {
        color: #f4efe2;
        font-size: 1.4rem;
        font-weight: 600;
    }

    /* 구분선 */
    hr {
        border-color: #26384a !important;
        margin-top: 30px;
        margin-bottom: 30px;
    }

    /* 데이터프레임 */
    [data-testid="stDataFrame"] {
        border: 1px solid #26384a;
        border-radius: 10px;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# 제목
# =========================================================

st.markdown(
    '<div class="page-title">⚓ SAILING LOG</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="page-subtitle">'
    '지금까지의 공부 항해를 한눈에 확인하는 항해일지'
    '</div>',
    unsafe_allow_html=True
)


# =========================================================
# log.csv 읽기
# =========================================================

if not os.path.exists(LOG_FILE):

    st.markdown(
        """
        <div class="today-card">

            <div class="today-label">
                LOGBOOK
            </div>

            <div class="today-value">
                ⚓ 아직 항해 기록이 없습니다.
            </div>

            <div style="
                color:#9daaba;
                margin-top:10px;
                line-height:1.7;
            ">
                메인 페이지에서 공부를 시작하면<br>
                이곳에 항해 기록이 자동으로 쌓입니다.
            </div>

        </div>
        """,
        unsafe_allow_html=True
    )

    st.stop()


try:

    df = pd.read_csv(
        LOG_FILE,
        encoding="utf-8-sig"
    )

except Exception as e:

    st.error(
        "항해일지 파일을 읽는 중 문제가 발생했습니다."
    )

    st.caption(
        f"오류 내용: {e}"
    )

    st.stop()


# =========================================================
# 기록이 비어 있는 경우
# =========================================================

if df.empty:

    st.markdown(
        """
        <div class="today-card">

            <div class="today-label">
                LOGBOOK
            </div>

            <div class="today-value">
                ⚓ 아직 항해 기록이 없습니다.
            </div>

            <div style="
                color:#9daaba;
                margin-top:10px;
            ">
                메인 페이지에서 공부를 시작해보세요.
            </div>

        </div>
        """,
        unsafe_allow_html=True
    )

    st.stop()


# =========================================================
# 데이터 정리
# =========================================================

required_columns = [
    "날짜",
    "모드",
    "시작시각",
    "종료시각",
    "소요시간(분)",
    "전진거리(해리)"
]


# 필요한 열이 없는 경우
missing_columns = [
    column
    for column in required_columns
    if column not in df.columns
]


if missing_columns:

    st.error("log.csv의 형식이 예상과 다릅니다.")

    st.write(
        "없는 열:",
        ", ".join(missing_columns)
    )

    st.stop()


# 날짜
df["날짜"] = pd.to_datetime(
    df["날짜"],
    errors="coerce"
).dt.date


# 숫자
df["소요시간(분)"] = pd.to_numeric(
    df["소요시간(분)"],
    errors="coerce"
).fillna(0)


df["전진거리(해리)"] = pd.to_numeric(
    df["전진거리(해리)"],
    errors="coerce"
).fillna(0)


# 잘못된 날짜 제거
df = df.dropna(
    subset=["날짜"]
).copy()


if df.empty:
    st.warning("정상적인 날짜가 포함된 항해 기록이 없습니다.")
    st.stop()


# =========================================================
# 기본 통계
# =========================================================

total_minutes = df["소요시간(분)"].sum()

total_distance = df["전진거리(해리)"].sum()

total_sessions = len(df)

total_days = df["날짜"].nunique()

longest_session = df["소요시간(분)"].max()

average_session = df["소요시간(분)"].mean()


# =========================================================
# 시간 표시 함수
# =========================================================

def format_minutes(minutes):

    minutes = int(round(minutes))

    hours = minutes // 60
    mins = minutes % 60

    if hours > 0:
        return f"{hours}시간 {mins}분"

    return f"{mins}분"


# =========================================================
# 상단 통계
# =========================================================

st.markdown(
    '<div class="section-title">✦ 항해 기록</div>',
    unsafe_allow_html=True
)


col1, col2, col3, col4 = st.columns(4)


with col1:

    st.markdown(
        f"""
        <div class="stat-card">

            <div class="stat-title">
                TOTAL STUDY
            </div>

            <div class="stat-value">
                {format_minutes(total_minutes)}
            </div>

        </div>
        """,
        unsafe_allow_html=True
    )


with col2:

    st.markdown(
        f"""
        <div class="stat-card">

            <div class="stat-title">
                VOYAGE DISTANCE
            </div>

            <div class="stat-value">
                {total_distance:,.1f} NM
            </div>

        </div>
        """,
        unsafe_allow_html=True
    )


with col3:

    st.markdown(
        f"""
        <div class="stat-card">

            <div class="stat-title">
                STUDY DAYS
            </div>

            <div class="stat-value">
                {total_days}일
            </div>

        </div>
        """,
        unsafe_allow_html=True
    )


with col4:

    st.markdown(
        f"""
        <div class="stat-card">

            <div class="stat-title">
                VOYAGES
            </div>

            <div class="stat-value">
                {total_sessions}회
            </div>

        </div>
        """,
        unsafe_allow_html=True
    )


# =========================================================
# 가장 긴 집중
# =========================================================

st.markdown(
    '<div class="section-title">🧭 나의 항해 기록</div>',
    unsafe_allow_html=True
)


col1, col2 = st.columns(2)


with col1:

    st.markdown(
        f"""
        <div class="today-card">

            <div class="today-label">
                LONGEST VOYAGE
            </div>

            <div class="today-value">
                {format_minutes(longest_session)}
            </div>

            <div style="
                color:#9daaba;
                margin-top:8px;
            ">
                가장 오래 집중한 한 번의 항해
            </div>

        </div>
        """,
        unsafe_allow_html=True
    )


with col2:

    st.markdown(
        f"""
        <div class="today-card">

            <div class="today-label">
                AVERAGE VOYAGE
            </div>

            <div class="today-value">
                {format_minutes(average_session)}
            </div>

            <div style="
                color:#9daaba;
                margin-top:8px;
            ">
                한 번의 항해에서 평균적으로 공부한 시간
            </div>

        </div>
        """,
        unsafe_allow_html=True
    )


# =========================================================
# 날짜별 공부 기록
# =========================================================

st.markdown(
    '<div class="section-title">📅 날짜별 항해 기록</div>',
    unsafe_allow_html=True
)


daily = (
    df.groupby("날짜")
    .agg(
        공부시간=("소요시간(분)", "sum"),
        항해횟수=("모드", "count"),
        전진거리=("전진거리(해리)", "sum")
    )
    .reset_index()
)


daily = daily.sort_values(
    "날짜",
    ascending=False
)


daily_display = daily.copy()


daily_display["날짜"] = daily_display[
    "날짜"
].apply(
    lambda x: x.strftime("%Y-%m-%d")
)


daily_display["공부시간"] = daily_display[
    "공부시간"
].apply(format_minutes)


daily_display["전진거리"] = daily_display[
    "전진거리"
].apply(
    lambda x: f"{x:,.1f} NM"
)


daily_display.columns = [
    "날짜",
    "공부시간",
    "항해횟수",
    "전진거리"
]


st.dataframe(
    daily_display,
    use_container_width=True,
    hide_index=True
)


# =========================================================
# 최근 14일 공부량
# =========================================================

st.markdown(
    '<div class="section-title">🌊 최근 항해 흐름</div>',
    unsafe_allow_html=True
)


latest_date = max(df["날짜"])

start_date = latest_date


recent_days = pd.date_range(
    end=pd.Timestamp(latest_date),
    periods=14,
    freq="D"
).date


recent_df = (
    df[df["날짜"].isin(recent_days)]
    .groupby("날짜")["소요시간(분)"]
    .sum()
)


chart_df = pd.DataFrame(
    index=recent_days
)


chart_df["공부시간(분)"] = [
    recent_df.get(day, 0)
    for day in recent_days
]


chart_df.index = [
    day.strftime("%m/%d")
    for day in chart_df.index
]


st.bar_chart(
    chart_df,
    use_container_width=True
)


# =========================================================
# 공부 모드 분석
# =========================================================

st.markdown(
    '<div class="section-title">⚓ 항해 방식</div>',
    unsafe_allow_html=True
)


mode_df = (
    df.groupby("모드")
    .agg(
        항해횟수=("모드", "count"),
        공부시간=("소요시간(분)", "sum"),
        전진거리=("전진거리(해리)", "sum")
    )
    .reset_index()
)


mode_display = mode_df.copy()


mode_display["공부시간"] = mode_display[
    "공부시간"
].apply(format_minutes)


mode_display["전진거리"] = mode_display[
    "전진거리"
].apply(
    lambda x: f"{x:,.1f} NM"
)


mode_display.columns = [
    "항해 방식",
    "항해 횟수",
    "공부시간",
    "전진거리"
]


st.dataframe(
    mode_display,
    use_container_width=True,
    hide_index=True
)


# =========================================================
# 모드별 차트
# =========================================================

mode_chart = mode_df.set_index("모드")[
    ["공부시간"]
]


st.bar_chart(
    mode_chart,
    use_container_width=True
)


# =========================================================
# 상세 항해 기록
# =========================================================

st.markdown(
    '<div class="section-title">📖 전체 항해일지</div>',
    unsafe_allow_html=True
)


detail_df = df.copy()


detail_df = detail_df.sort_values(
    ["날짜", "시작시각"],
    ascending=[False, False]
)


detail_df["날짜"] = detail_df[
    "날짜"
].apply(
    lambda x: x.strftime("%Y-%m-%d")
)


detail_df["소요시간(분)"] = detail_df[
    "소요시간(분)"
].apply(
    lambda x: f"{x:.0f}분"
)


detail_df["전진거리(해리)"] = detail_df[
    "전진거리(해리)"
].apply(
    lambda x: f"{x:.1f} NM"
)


detail_df = detail_df[
    [
        "날짜",
        "모드",
        "시작시각",
        "종료시각",
        "소요시간(분)",
        "전진거리(해리)"
    ]
]


st.dataframe(
    detail_df,
    use_container_width=True,
    hide_index=True
)


# =========================================================
# 마지막 문구
# =========================================================

st.markdown("---")

st.markdown(
    """
    <div style="
        text-align:center;
        color:#718095;
        padding:20px;
        line-height:1.8;
    ">
        ⚓ Every minute is one nautical mile.<br>
        오늘의 항해가 내일의 목적지가 됩니다.
    </div>
    """,
    unsafe_allow_html=True
)
