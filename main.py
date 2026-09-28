# pages/Sailingnote.py

import streamlit as st
import pandas as pd
import os
from datetime import date, timedelta


# ============================================================
# 기본 설정
# ============================================================

st.set_page_config(
    page_title="항해일지",
    page_icon="⚓",
    layout="wide",
)


# log.csv 위치
LOG_FILE = "log.csv"


# ============================================================
# 디자인 CSS
# ============================================================

st.markdown(
    """
    <style>
    /* 전체 배경 */
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

    /* 전체 콘텐츠 폭 */
    .block-container {
        max-width: 1100px;
        padding-top: 2.5rem;
        padding-bottom: 4rem;
    }

    /* 제목 */
    h1, h2, h3 {
        color: #E8E2D5 !important;
        letter-spacing: -0.02em;
    }

    /* 상단 작은 제목 */
    .page-label {
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

    /* 골드 라인 */
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

    /* 통계 카드 */
    div[data-testid="stMetric"] {
        background: rgba(13, 29, 47, 0.92);
        border: 1px solid rgba(199, 166, 90, 0.24);
        border-radius: 14px;
        padding: 1rem;
    }

    div[data-testid="stMetricLabel"] {
        color: #8F9BA8 !important;
    }

    div[data-testid="stMetricValue"] {
        color: #E8D09A !important;
    }

    /* 섹션 카드 */
    .section-card {
        background: rgba(10, 24, 39, 0.88);
        border: 1px solid rgba(199, 166, 90, 0.18);
        border-radius: 16px;
        padding: 1.4rem;
        margin-top: 1rem;
        margin-bottom: 1rem;
    }

    .section-description {
        color: #8F9BA8;
        font-size: 0.85rem;
        margin-top: -0.5rem;
        margin-bottom: 1rem;
    }

    /* 안내문 */
    .empty-box {
        background: rgba(13, 29, 47, 0.92);
        border: 1px solid rgba(199, 166, 90, 0.25);
        border-radius: 16px;
        padding: 2rem;
        text-align: center;
        color: #B9C2CC;
        margin-top: 2rem;
    }

    .empty-title {
        color: #E8D09A;
        font-size: 1.2rem;
        margin-bottom: 0.5rem;
    }

    /* 작은 설명 */
    .small-note {
        color: #788696;
        font-size: 0.78rem;
    }

    /* dataframe 글자 */
    [data-testid="stDataFrame"] {
        border-radius: 12px;
        overflow: hidden;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# 함수
# ============================================================

def load_log():
    """
    log.csv를 읽어오는 함수.
    파일이 없거나 읽는 데 문제가 있으면 빈 DataFrame을 반환한다.
    """

    required_columns = [
        "날짜",
        "모드",
        "시작시각",
        "종료시각",
        "소요시간(분)",
        "전진거리(해리)",
    ]

    if not os.path.exists(LOG_FILE):
        return pd.DataFrame(columns=required_columns)

    try:
        df = pd.read_csv(
            LOG_FILE,
            encoding="utf-8-sig",
        )

        # 필요한 컬럼이 빠져 있다면 빈 값으로 추가
        for column in required_columns:
            if column not in df.columns:
                df[column] = None

        df = df[required_columns].copy()

        return df

    except Exception:
        return pd.DataFrame(columns=required_columns)


def calculate_longest_streak(date_series):
    """
    공부 기록이 하루도 빠지지 않고 이어진
    가장 긴 연속 공부일을 계산한다.
    """

    if len(date_series) == 0:
        return 0

    # 날짜 중복 제거 후 정렬
    dates = sorted(
        set(
            pd.to_datetime(
                date_series,
                errors="coerce",
            ).dropna().dt.date
        )
    )

    if not dates:
        return 0

    longest = 1
    current = 1

    for i in range(1, len(dates)):
        difference = (
            dates[i] - dates[i - 1]
        ).days

        if difference == 1:
            current += 1
        else:
            current = 1

        longest = max(longest, current)

    return longest


def prepare_dataframe(df):
    """
    숫자/날짜 컬럼을 계산하기 편한 형태로 변환한다.
    """

    if df.empty:
        return df

    df = df.copy()

    # 날짜 변환
    df["날짜"] = pd.to_datetime(
        df["날짜"],
        errors="coerce",
    ).dt.date

    # 시작/종료 시각 변환
    df["시작시각_계산용"] = pd.to_datetime(
        df["시작시각"],
        errors="coerce",
    )

    df["종료시각_계산용"] = pd.to_datetime(
        df["종료시각"],
        errors="coerce",
    )

    # 숫자로 변환
    df["소요시간(분)"] = pd.to_numeric(
        df["소요시간(분)"],
        errors="coerce",
    ).fillna(0)

    df["전진거리(해리)"] = pd.to_numeric(
        df["전진거리(해리)"],
        errors="coerce",
    ).fillna(0)

    # 날짜가 없는 잘못된 행 제거
    df = df.dropna(subset=["날짜"])

    return df


def make_daily_table(df):
    """
    날짜별 통계를 만든다.
    """

    if df.empty:
        return pd.DataFrame()

    daily = (
        df.groupby("날짜")
        .agg(
            그날총공부시간분=(
                "소요시간(분)",
                "sum",
            ),
            그날시작시각=(
                "시작시각_계산용",
                "min",
            ),
            그날종료시각=(
                "종료시각_계산용",
                "max",
            ),
            그날최대집중시간분=(
                "소요시간(분)",
                "max",
            ),
            그날총전진거리해리=(
                "전진거리(해리)",
                "sum",
            ),
        )
        .reset_index()
    )

    # 최신 날짜가 위로 오도록 정렬
    daily = daily.sort_values(
        "날짜",
        ascending=False,
    )

    # 화면에 보여줄 이름으로 변경
    daily = daily.rename(
        columns={
            "날짜": "날짜",
            "그날총공부시간분": "총 공부시간(분)",
            "그날시작시각": "시작시각",
            "그날종료시각": "종료시각",
            "그날최대집중시간분": "최대 집중시간(분)",
            "그날총전진거리해리": "총 전진거리(해리)",
        }
    )

    # 시각을 보기 편하게 변경
    daily["시작시각"] = daily["시작시각"].dt.strftime(
        "%Y-%m-%d %H:%M"
    )

    daily["종료시각"] = daily["종료시각"].dt.strftime(
        "%Y-%m-%d %H:%M"
    )

    # 숫자 정리
    daily["총 공부시간(분)"] = daily[
        "총 공부시간(분)"
    ].round(1)

    daily["최대 집중시간(분)"] = daily[
        "최대 집중시간(분)"
    ].round(1)

    daily["총 전진거리(해리)"] = daily[
        "총 전진거리(해리)"
    ].round(1)

    return daily


# ============================================================
# 데이터 불러오기
# ============================================================

df = load_log()

df = prepare_dataframe(df)


# ============================================================
# 헤더
# ============================================================

st.markdown(
    '<div class="page-label">SAILING NOTE</div>',
    unsafe_allow_html=True,
)

st.title("⚓ 항해일지")

st.markdown(
    """
    <div class="subtitle">
        지금까지의 공부 항로를 돌아보고,
        얼마나 멀리 항해했는지 확인해 보세요.
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="gold-line"></div>',
    unsafe_allow_html=True,
)


# ============================================================
# 기록이 하나도 없는 경우
# ============================================================

if df.empty:

    st.markdown(
        """
        <div class="empty-box">
            <div class="empty-title">
                ⚓ 아직 기록이 없어요.
            </div>

            오늘의 항해를 먼저 시작해보세요!
            <br><br>

            <span class="small-note">
                공부 세션을 완료하고
                「항해일지에 기록하기」를 누르면
                이곳에 기록이 쌓입니다.
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.stop()


# ============================================================
# 상단 요약 지표
# ============================================================

st.subheader("⚓ 항해 기록 요약")

total_distance = df[
    "전진거리(해리)"
].sum()

total_study_days = df[
    "날짜"
].nunique()

longest_streak = calculate_longest_streak(
    df["날짜"]
)

longest_session = df[
    "소요시간(분)"
].max()


metric1, metric2, metric3, metric4 = st.columns(4)

with metric1:
    st.metric(
        label="총 누적 항해 거리",
        value=f"{total_distance:,.1f} 해리",
    )

with metric2:
    st.metric(
        label="총 공부일수",
        value=f"{total_study_days:,}일",
    )

with metric3:
    st.metric(
        label="최장 연속 기록일",
        value=f"{longest_streak:,}일",
    )

with metric4:
    st.metric(
        label="최대 집중시간",
        value=f"{longest_session:,.1f}분",
    )


# ============================================================
# 날짜별 기록
# ============================================================

st.markdown(
    '<div class="gold-line"></div>',
    unsafe_allow_html=True,
)

st.subheader("⚓ 날짜별 항해 기록")

st.markdown(
    """
    <div class="section-description">
        같은 날의 여러 세션은 하나의 항해 기록으로 합산됩니다.
    </div>
    """,
    unsafe_allow_html=True,
)

daily_df = make_daily_table(df)

st.dataframe(
    daily_df,
    use_container_width=True,
    hide_index=True,
    column_config={
        "날짜": st.column_config.DateColumn(
            "날짜",
            format="YYYY-MM-DD",
        ),
        "총 공부시간(분)": st.column_config.NumberColumn(
            "총 공부시간(분)",
            format="%.1f",
        ),
        "최대 집중시간(분)": st.column_config.NumberColumn(
            "최대 집중시간(분)",
            format="%.1f",
        ),
        "총 전진거리(해리)": st.column_config.NumberColumn(
            "총 전진거리(해리)",
            format="%.1f",
        ),
    },
)


# ============================================================
# 최근 14일 공부 추이
# ============================================================

st.markdown(
    '<div class="gold-line"></div>',
    unsafe_allow_html=True,
)

st.subheader("⚓ 최근 14일 항해 추이")

st.markdown(
    """
    <div class="section-description">
        최근 14일 동안 하루에 얼마나 공부했는지 보여줍니다.
        기록이 없는 날은 0분으로 표시됩니다.
    </div>
    """,
    unsafe_allow_html=True,
)


today = date.today()

recent_dates = [
    today - timedelta(days=i)
    for i in range(13, -1, -1)
]

# 날짜별 공부시간 합계
daily_minutes = (
    df.groupby("날짜")["소요시간(분)"]
    .sum()
)

chart_data = pd.DataFrame(
    {
        "날짜": recent_dates,
        "공부시간(분)": [
            daily_minutes.get(
                target_date,
                0,
            )
            for target_date in recent_dates
        ],
    }
)

chart_data = chart_data.set_index("날짜")

st.bar_chart(
    chart_data,
    y="공부시간(분)",
    use_container_width=True,
)


# ============================================================
# 모드별 공부시간 비중
# ============================================================

st.markdown(
    '<div class="gold-line"></div>',
    unsafe_allow_html=True,
)

st.subheader("⚓ 항해 방식별 공부시간")

st.markdown(
    """
    <div class="section-description">
        지금까지 기록한 공부시간이 어떤 항해 방식으로 이루어졌는지 보여줍니다.
    </div>
    """,
    unsafe_allow_html=True,
)


mode_order = [
    "자유형",
    "지정",
    "뽀모도로",
]

mode_data = (
    df.groupby("모드")["소요시간(분)"]
    .sum()
    .reindex(
        mode_order,
        fill_value=0,
    )
    .reset_index()
)

mode_data.columns = [
    "모드",
    "누적 공부시간(분)",
]

mode_data["누적 공부시간(분)"] = (
    mode_data["누적 공부시간(분)"]
    .round(1)
)

total_mode_minutes = mode_data[
    "누적 공부시간(분)"
].sum()

if total_mode_minutes > 0:
    mode_data["비중"] = (
        mode_data["누적 공부시간(분)"]
        / total_mode_minutes
        * 100
    ).round(1)
else:
    mode_data["비중"] = 0


left, right = st.columns([1, 1.5])

with left:

    display_mode = mode_data.copy()

    display_mode["비중"] = (
        display_mode["비중"]
        .map(lambda x: f"{x:.1f}%")
    )

    st.dataframe(
        display_mode,
        use_container_width=True,
        hide_index=True,
    )


with right:

    mode_chart = mode_data[
        ["모드", "누적 공부시간(분)"]
    ].set_index("모드")

    st.bar_chart(
        mode_chart,
        y="누적 공부시간(분)",
        use_container_width=True,
    )


# ============================================================
# 하단 안내
# ============================================================

st.markdown(
    '<div class="gold-line"></div>',
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="small-note">
        항해일지는 main.py에서 「항해일지에 기록하기」를
        누른 세션을 기준으로 계산됩니다.
    </div>
    """,
    unsafe_allow_html=True,
)
