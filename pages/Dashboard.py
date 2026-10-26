import streamlit as st
import plotly.graph_objects as go

# ============================================================
# 탄소중립 선박 경영 대시보드
# 주의: 게임 진행 로직은 수정하지 않고, main.py의 세션 상태만 읽습니다.
# ============================================================

START_YEAR = 2026
END_YEAR = 2050
START_EMISSION = 100
CHECKPOINTS = {2030: 80, 2040: 30, 2050: 0}

# main.py의 설비 ID와 동일하게 유지합니다.
EQUIPMENT = [
    {"id": 1, "name": "선체 코팅·프로펠러 개선", "price": 15_000_000, "reduction": 10, "effect": "배출량 10%p 감축"},
    {"id": 2, "name": "폐열 회수 장치", "price": 25_000_000, "reduction": 10, "effect": "배출량 10%p 감축"},
    {"id": 3, "name": "지상전력공급장치", "price": 30_000_000, "reduction": 10, "effect": "배출량 10%p 감축"},
    {"id": 4, "name": "풍력 보조 돛", "price": 40_000_000, "reduction": 15, "effect": "배출량 15%p 감축"},
    {"id": 5, "name": "LNG 이중연료 엔진", "price": 60_000_000, "reduction": 15, "effect": "배출량 15%p 감축"},
    {"id": 6, "name": "암모니아·메탄올 엔진", "price": 100_000_000, "reduction": 20, "effect": "배출량 20%p 감축"},
    {"id": 7, "name": "탄소 포집 장치", "price": 130_000_000, "reduction": 20, "effect": "배출량 20%p 감축"},
]

TRANSPORT = [
    {"id": 1, "name": "화물 적재함 확장", "price": 20_000_000, "effect": "모든 항해 수익 +10%"},
    {"id": 2, "name": "대형 선체로 교체", "price": 60_000_000, "effect": "모든 항해 수익 +25%"},
    {"id": 3, "name": "고속 엔진", "price": 50_000_000, "effect": "항해 기간 1년 단축(최소 1년)"},
    {"id": 4, "name": "자율운항선박", "price": 100_000_000, "effect": "자동 운항 기능 해금"},
]


def money_label(amount):
    """게임의 원 단위 금액을 만원/억원 단위로 표시합니다."""
    try:
        amount = int(amount or 0)
    except (TypeError, ValueError):
        amount = 0
    amount = max(0, amount)
    eok = amount // 100_000_000
    man = (amount % 100_000_000) // 10_000
    if eok and man:
        return f"{eok}억 {man:,}만원"
    if eok:
        return f"{eok}억원"
    if man:
        return f"{man:,}만원"
    return f"{amount:,}원"


def phase_label(phase):
    return {
        "docked": "부산항 정박 중",
        "sailing": "목적지로 항해 중",
        "returning": "부산항으로 귀항 중",
        "ended": "게임 종료",
    }.get(phase, "상태 확인 중")


def read_number(key, default=0):
    try:
        return int(st.session_state.get(key, default) or 0)
    except (TypeError, ValueError):
        return default


# ----------------------------
# 화면 스타일
# ----------------------------
st.markdown(
    """
    <style>
    .block-container {padding-top: 1.5rem; padding-bottom: 2.5rem;}
    h1, h2, h3, p, label, [data-testid="stMetricLabel"], [data-testid="stMetricValue"] {
        color: #172b3a;
    }
    .dash-hero {
        padding: 1.35rem 1.5rem; margin-bottom: 1rem; border-radius: 18px;
        background: linear-gradient(120deg, #e6f7f8 0%, #f2f7ff 55%, #fff8e9 100%);
        border: 1px solid #d8e7eb;
    }
    .dash-hero h1 {margin: 0 0 .35rem 0; color: #123247;}
    .dash-hero p {margin: 0; color: #486273;}
    .section-note {color: #5e7280; font-size: .9rem;}
    div[data-testid="stMetric"] {
        background: #ffffff; border: 1px solid #e1e9ee; border-radius: 14px;
        padding: 12px 14px; box-shadow: 0 2px 8px rgba(18,50,71,.04);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="dash-hero">
      <h1>🚢 선박 경영 대시보드</h1>
      <p>회사의 경영 상태, 탄소 감축 성과, 현재 선박에 적용된 기술을 확인합니다.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# Dashboard는 main.py의 init()이 만든 세션 상태를 읽기만 합니다.
# 대시보드를 먼저 열었거나 아직 게임을 시작하지 않았다면 안전하게 안내합니다.
if "started" not in st.session_state:
    st.info("게임 상태를 찾을 수 없습니다. 먼저 메인 페이지에서 게임을 시작한 뒤 대시보드를 열어 주세요.")
    st.stop()

if not st.session_state.get("started", False):
    st.info("아직 게임을 시작하지 않았어요. 메인 페이지에서 **게임 시작**을 눌러 주세요.")
    st.stop()

phase = st.session_state.get("phase", "docked")
year = read_number("year", START_YEAR)
money = read_number("money", 0)
bought_eq_ids = set(st.session_state.get("bought_eq", []) or [])
bought_tr_ids = set(st.session_state.get("bought_tr", []) or [])
history = st.session_state.get("history", []) or []
event_log = st.session_state.get("event_log", []) or []
destination = st.session_state.get("dest")

bought_equipment = [item for item in EQUIPMENT if item["id"] in bought_eq_ids]
bought_transport = [item for item in TRANSPORT if item["id"] in bought_tr_ids]
total_reduction = sum(item["reduction"] for item in bought_equipment)
emission = max(0, START_EMISSION - total_reduction)

# ----------------------------
# 1. 경영 현황 KPI
# ----------------------------
st.subheader("💼 회사 경영 현황")
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("현재 연도", f"{year}년")
k2.metric("보유 자금", money_label(money))
k3.metric("현재 탄소 배출량", f"{emission}%")
k4.metric("보유 감축 설비", f"{len(bought_equipment)}개")
k5.metric("선박 상태", phase_label(phase))

if phase in ("sailing", "returning"):
    progress = min(100, max(0, int(read_number("pos") / max(1, read_number("total", 1)) * 100)))
    travel_name = destination or "목적지 확인 중"
    current_income = read_number("returning_income", read_number("voyage_income", 0))
    st.info(
        f"🚢 현재 {travel_name} 항로를 운항 중입니다. 진행도 **{progress}%** · "
        f"현재 항해 예상 운임 **{money_label(current_income)}**"
    )

st.divider()

# ----------------------------
# 2. 탄소 감축 성과와 IMO 목표
# ----------------------------
st.subheader("🌱 탄소중립 달성 현황")
left, right = st.columns([1.65, 1])

with left:
    if history:
        years = []
        emissions = []
        for item in history:
            if not isinstance(item, dict):
                continue
            try:
                years.append(int(item.get("year", START_YEAR)))
                emissions.append(int(item.get("emission", START_EMISSION)))
            except (TypeError, ValueError):
                continue

        # 현재 설비 적용 결과도 마지막 지점으로 표시합니다.
        if not years:
            years, emissions = [START_YEAR], [START_EMISSION]
        if years[-1] != year or emissions[-1] != emission:
            years.append(year)
            emissions.append(emission)

        fig_emission = go.Figure()
        fig_emission.add_trace(go.Scatter(
            x=years, y=emissions, mode="lines+markers", name="실제 배출량",
            line=dict(color="#168c91", width=3), marker=dict(size=7),
            hovertemplate="%{x}년<br>배출량 %{y}%<extra></extra>",
        ))
        for target_year, target_emission in CHECKPOINTS.items():
            if target_year < END_YEAR:
                fig_emission.add_trace(go.Scatter(
                    x=[target_year, END_YEAR], y=[target_emission, target_emission],
                    mode="lines", name=f"{target_year}년 목표 {target_emission}%",
                    line=dict(dash="dash", width=1.5),
                    hoverinfo="skip",
                ))
            else:
                fig_emission.add_trace(go.Scatter(
                    x=[target_year], y=[target_emission], mode="markers",
                    name=f"{target_year}년 목표 {target_emission}%",
                    marker=dict(symbol="diamond", size=10), hoverinfo="skip",
                ))
        fig_emission.update_layout(
            height=360, margin=dict(l=12, r=12, t=28, b=10),
            xaxis_title="게임 연도", yaxis_title="탄소 배출량(%)",
            yaxis=dict(range=[-3, 105], dtick=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig_emission, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("아직 탄소 배출량 기록이 없습니다.")

with right:
    st.markdown("#### IMO 감축 목표")
    for target_year, target_value in CHECKPOINTS.items():
        if year >= target_year:
            status = "달성" if emission <= target_value else "미달성"
            icon = "✅" if status == "달성" else "❌"
        else:
            status = "목표 대기 중"
            icon = "⏳"
        st.markdown(
            f"**{target_year}년**　{icon} {status}  \n"
            f"목표 배출량: **{target_value}% 이하**"
        )
    st.caption(f"최초 배출량 100% → 현재 배출량 {emission}% · 총 감축량 {total_reduction}%p")

st.divider()

# ----------------------------
# 3. 내 선박 현황: 실제 구매한 설비/업그레이드만 표시
# ----------------------------
st.subheader("⚓ 내 선박 현황")
col_eq, col_tr = st.columns(2)

with col_eq:
    st.markdown("#### 🌿 탄소 감축 설비")
    if bought_equipment:
        for item in bought_equipment:
            with st.container(border=True):
                row1, row2 = st.columns([3, 1])
                row1.markdown(f"**{item['name']}**")
                row1.caption(item["effect"])
                row2.metric("구매 비용", money_label(item["price"]))
        st.success(f"총 감축량: **{total_reduction}%p** · 현재 배출량: **{emission}%**")
    else:
        st.info("아직 구매한 탄소 감축 설비가 없습니다.")

with col_tr:
    st.markdown("#### 🛠️ 선박 업그레이드")
    if bought_transport:
        for item in bought_transport:
            with st.container(border=True):
                row1, row2 = st.columns([3, 1])
                row1.markdown(f"**{item['name']}**")
                row1.caption(item["effect"])
                row2.metric("구매 비용", money_label(item["price"]))
    else:
        st.info("아직 구매한 선박 업그레이드가 없습니다.")

st.divider()

# ----------------------------
# 4. 항해/경영 기록
# main.py에는 완료 항해별 항구 방문 기록이나 누적 항해 시간 기록이
# 별도로 저장되지 않으므로, 해당 통계는 임의로 만들어 표시하지 않습니다.
# ----------------------------
st.subheader("🧭 항해 및 경영 기록")
record_col, event_col = st.columns([1.25, 1])

with record_col:
    st.markdown("#### 📉 경영 기록")
    valid_history = [item for item in history if isinstance(item, dict)]
    if valid_history:
        rows = []
        for index, item in enumerate(valid_history, start=1):
            rows.append({
                "기록": index,
                "연도": f"{item.get('year', START_YEAR)}년",
                "보유 자금": money_label(item.get("money", 0)),
                "탄소 배출량": f"{item.get('emission', START_EMISSION)}%",
            })
        st.dataframe(rows[::-1], use_container_width=True, hide_index=True)
        st.caption("최근 기록부터 표시합니다. 이 기록은 게임에서 실제로 저장된 시점의 자금과 배출량입니다.")
    else:
        st.info("아직 표시할 경영 기록이 없습니다.")

with event_col:
    st.markdown("#### ⚠️ 최근 이벤트")
    if event_log:
        for log in reversed(event_log[-8:]):
            st.markdown(f"- {log}")
    else:
        st.info("아직 발생한 이벤트가 없습니다.")

st.divider()

# ----------------------------
# 5. 실제 상태에 따른 경영 코멘트
# ----------------------------
st.subheader("🧠 경영 분석")
comments = []
next_checkpoint = next((target_year for target_year in sorted(CHECKPOINTS) if target_year not in (st.session_state.get("checked", []) or [])), None)

if emission == 0:
    comments.append(("success", "🎉 탄소중립 달성! 현재 배출량이 0%입니다."))
elif next_checkpoint is not None:
    target_value = CHECKPOINTS[next_checkpoint]
    if year < next_checkpoint:
        comments.append(("info", f"📅 다음 점검은 {next_checkpoint}년이며, 목표 배출량은 {target_value}% 이하입니다."))
    elif emission > target_value:
        comments.append(("warning", f"⚠️ 현재 배출량 {emission}%가 {next_checkpoint}년 목표 {target_value}%를 초과합니다. 감축 설비를 검토하세요."))

if money < 20_000_000:
    comments.append(("warning", "💰 보유 자금이 2,000만원 미만입니다. 다음 출항 전 정박 비용과 설비 구매 비용을 함께 고려하세요."))
elif money >= 100_000_000:
    comments.append(("info", "💼 보유 자금이 1억원 이상입니다. 장기적인 탄소 감축 투자 계획을 검토할 수 있습니다."))

if not comments:
    comments.append(("info", "⚓ 항해를 진행하고 설비를 구매하면 실제 게임 기록에 맞춰 경영 분석이 업데이트됩니다."))

for kind, message in comments:
    if kind == "success":
        st.success(message)
    elif kind == "warning":
        st.warning(message)
    else:
        st.info(message)

st.caption("※ 이 대시보드는 현재 게임 세션에 저장된 데이터를 사용합니다. 게임을 새로 시작하거나 세션이 초기화되면 기록도 초기화됩니다.")
