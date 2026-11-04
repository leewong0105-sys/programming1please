import streamlit as st
import plotly.graph_objects as go
from html import escape


# ============================================================
# 1. 기본 설정 및 게임 데이터 기준값
# ============================================================
# 이 파일은 '투더넷 (To The Net Zero) - 탄소중립 선박 경영 시뮬레이터'
# 프로젝트의 대시보드 화면을 담당합니다.
#
# 대시보드는 메인 게임의 데이터를 읽어서 보여 주는 조회 전용 페이지입니다.
# 따라서 이 파일에서는 선박을 출항시키거나, 자금을 변경하거나,
# 연구를 진행하는 등 실제 게임 상태를 바꾸는 작업을 하지 않습니다.

START_YEAR = 2026
END_YEAR = 2050
START_EMISSION = 100

# 탄소 배출량의 중간 목표입니다.
# 예: 2030년에는 80% 이하, 2040년에는 30% 이하,
# 2050년에는 0%가 되도록 관리하는 것을 목표로 합니다.
CHECKPOINTS = {
    2030: 80,
    2040: 30,
    2050: 0,
}

# 대시보드에 표시할 탄소 감축 연구 목록입니다.
# 각 항목의 구성:
# (메인 게임에서 사용하는 연구 ID, 화면에 표시할 이름,
#  연구 단계별 감축량, 화면에 표시할 아이콘)
RESEARCH = [
    ("alternative_fuel", "차세대 무탄소 연료 추진 기술", [5, 7, 8], "⚗"),
    ("capture", "선상 탄소 포집 기술", [4, 6, 8], "♢"),
    ("efficiency", "에너지 효율 개선 기술", [4, 5, 6], "▱"),
    ("wind", "풍력 보조 추진 기술", [3, 5, 7], "≋"),
    ("shore_power", "육상 전력 공급 기술", [3, 5, 7], "⌁"),
    ("hydrogen", "청정 수소·연료전지 기술", [4, 6, 7], "▣"),
]

# 대시보드에 표시할 선박 업그레이드 목록입니다.
# 자율운항선박 항목은 요청에 따라 목록에서 제거했습니다.
TRANSPORT = [
    (1, "화물 적재함 확장", "모든 항해 수익 +10%"),
    (2, "대형 선체로 교체", "모든 항해 수익 +25%"),
    (3, "자동화 하역 시스템", "정박비 할인 연구"),
]


# ============================================================
# 2. 공통 데이터 처리 함수
# ============================================================
def to_int(value, default=0):
    """값을 정수로 변환합니다. 변환할 수 없으면 기본값을 반환합니다."""
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def format_money(value):
    """
    게임 내부의 금액을 한국식 금액 문자열로 바꿉니다.

    게임 데이터는 정수로 저장되지만, 대시보드에서는
    '3천만원', '1억 2,000만원'처럼 읽기 쉬운 형태로 표시합니다.
    """
    amount = to_int(value)
    sign = "-" if amount < 0 else ""
    amount = abs(amount)

    hundred_million, remainder = divmod(amount, 100_000_000)
    ten_thousand = remainder // 10_000

    if hundred_million and ten_thousand:
        return f"{sign}{hundred_million:,}억 {ten_thousand:,}만원"
    if hundred_million:
        return f"{sign}{hundred_million:,}억원"
    if ten_thousand:
        return f"{sign}{ten_thousand:,}만원"

    return f"{sign}{amount:,}원"


def get_ship_status(ship):
    """선박 데이터에서 현재 상태를 가져옵니다."""
    return ship.get("status", ship.get("phase", "docked"))


def get_ship_status_label(ship):
    """내부 상태 코드를 화면에 표시할 한국어 문구로 변환합니다."""
    status_labels = {
        "outbound": "항해 중",
        "sailing": "항해 중",
        "returning": "귀항 중",
        "docked": "정박 중",
    }
    return status_labels.get(get_ship_status(ship), "상태 확인 중")


def get_ship_status_color(ship):
    """선박 상태에 따라 대시보드 카드의 강조 색상을 정합니다."""
    status_colors = {
        "outbound": "#2868bd",
        "sailing": "#2868bd",
        "returning": "#18a596",
        "docked": "#8b98a8",
    }
    return status_colors.get(get_ship_status(ship), "#8b98a8")


def style_chart(figure):
    """대시보드의 그래프들이 같은 글꼴과 배경 스타일을 사용하도록 설정합니다."""
    figure.update_layout(
        height=245,
        margin=dict(l=5, r=10, t=8, b=8),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#173653", size=11),
        showlegend=False,
        xaxis=dict(
            showgrid=False,
            zeroline=False,
            tickfont=dict(color="#91a0af"),
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="#e8edf3",
            zeroline=False,
            tickfont=dict(color="#91a0af"),
        ),
    )
    return figure


# ============================================================
# 3. 메인 게임 데이터 읽기 및 계산
# ============================================================
def load_dashboard_data():
    """
    메인 게임의 세션 상태를 읽어 대시보드에서 사용할 데이터로 정리합니다.

    st.session_state는 Streamlit 페이지 사이에서 공유되는 저장 공간입니다.
    이 함수는 값을 읽고 정리하기만 하며, 원본 게임 데이터를 수정하지 않습니다.
    """
    history = [
        item
        for item in (st.session_state.get("history", []) or [])
        if isinstance(item, dict)
    ]

    return {
        "year": to_int(st.session_state.get("year"), START_YEAR),
        "money": to_int(st.session_state.get("money")),
        "phase": st.session_state.get("phase", "docked"),
        "company": escape(str(st.session_state.get("company_name") or "투더넷")),
        "fleet": st.session_state.get("fleet", []) or [],
        "history": history,
        "events": st.session_state.get("event_log", []) or [],
        "research_levels": st.session_state.get("research_levels", {}) or {},
        "bought_transport": set(st.session_state.get("bought_tr", []) or []),
        "transport_levels": st.session_state.get("transport_levels", {}) or {},
    }


def calculate_emission_status(research_levels):
    """
    연구 진행 단계를 바탕으로 현재 탄소 배출량과 감축 진행률을 계산합니다.

    각 연구의 단계별 감축량은 RESEARCH에 정의된 값을 사용합니다.
    이 계산은 대시보드 표시용이며 메인 게임의 연구 데이터는 변경하지 않습니다.
    """
    total_reduction = 0
    completed_stages = 0

    for research_id, _, stage_reductions, _ in RESEARCH:
        level = to_int(research_levels.get(research_id))

        # 대체 연료 연구는 메인 게임에서 암모니아·메탄올 연구 ID로
        # 저장되는 경우도 있으므로, 세 값 중 가장 높은 단계를 사용합니다.
        if research_id == "alternative_fuel":
            level = max(
                level,
                to_int(research_levels.get("ammonia")),
                to_int(research_levels.get("methanol")),
            )

        # 연구 단계가 0~3 범위를 벗어나더라도 계산 오류가 나지 않도록 제한합니다.
        level = max(0, min(3, level))

        completed_stages += level
        total_reduction += sum(stage_reductions[:level])

    current_emission = max(0, START_EMISSION - total_reduction)
    progress = max(
        0,
        min(
            100,
            round((START_EMISSION - current_emission) / START_EMISSION * 100),
        ),
    )

    return current_emission, completed_stages, progress


def calculate_management_targets(year, current_emission):
    """현재 연도에서 다음 탄소 감축 목표까지 필요한 감축량을 계산합니다."""
    next_year = next(
        (target_year for target_year in sorted(CHECKPOINTS) if year < target_year),
        None,
    )

    if next_year is None:
        remaining_reduction = current_emission
    else:
        remaining_reduction = max(
            0,
            current_emission - CHECKPOINTS[next_year],
        )

    return next_year, remaining_reduction


# ============================================================
# 4. 대시보드 디자인 적용
# ============================================================
def apply_dashboard_style():
    """
    대시보드 전체에서 사용할 CSS 디자인을 적용합니다.

    CSS는 화면의 색상, 여백, 글자 크기, 카드 모양 등을 꾸미는 코드입니다.
    아래 스타일은 기존 대시보드의 디자인을 유지하기 위한 것입니다.
    """
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;600;700;800;900&display=swap');
        .stApp{background:#edf3f9;color:#173653;font-family:'Noto Sans KR',sans-serif}
        [data-testid="stMainBlockContainer"]{max-width:1500px;padding:0 1.35rem 2.5rem}
        .block-container{padding-top:.7rem}
        h1,h2,h3,p,label{color:#173653}
        .dashhead{background:linear-gradient(105deg,#fff 0%,#fff 68%,#f4f8ff 100%);margin:0 -1.35rem 1.4rem;padding:1.1rem 2.7rem 1.3rem;border-bottom:1px solid #dfe7f0}
        .eyebrow{color:#4e7eaf;font-size:11px;letter-spacing:2.4px;font-weight:800}
        .dashtitle{font-size:30px;font-weight:900;letter-spacing:-1.2px;margin-top:7px;color:#153451}
        .sub{color:#8795a4;font-size:12px}
        .live{display:inline-block;border:1px solid #c9eee8;color:#168f83;background:#e9f8f6;border-radius:20px;padding:7px 13px;font-size:11px;font-weight:800}
        .panel{background:white;border:1px solid #dce5ee;border-radius:17px;padding:19px 20px;box-shadow:0 3px 12px #1b395809;margin-bottom:16px}
        .ptitle{font-size:17px;font-weight:850;color:#193b5a}.psub{font-size:11px;color:#98a5b1;margin-top:3px}
        .kpi{height:118px;background:white;border:1px solid #dce5ee;border-radius:16px;padding:17px 19px}
        .kpiblue{background:linear-gradient(120deg,#1553a4,#174987);border:0}
        .kl{font-size:12px;color:#8d9baa}.kv{font-size:27px;font-weight:900;color:#173653;line-height:1.4}
        .kpiblue .kl,.kpiblue .kv{color:white}.kf{font-size:10px;color:#1b9b91;font-weight:700;margin-top:6px}
        .kpiblue .kf{color:#b9d7ff}
        .ship{background:#fbfcfe;border:1px solid #dce5ed;border-left:4px solid var(--c);border-radius:13px;padding:14px;min-height:220px}
        .shiptop{display:flex;justify-content:space-between}.pill{background:var(--bg);color:var(--c);padding:5px 9px;border-radius:20px;font-size:10px;font-weight:800}
        .shipname{font-size:15px;font-weight:850;margin-top:15px;color:#1b3854}.shiptype{font-size:11px;color:#91a0ad}
        .route{display:flex;justify-content:space-between;align-items:center;border-top:1px solid #e7edf2;margin-top:14px;padding-top:12px}
        .rl{font-size:9px;color:#a1acb7}.rp{font-size:11px;font-weight:750;color:#405a70}
        .bar{height:4px;background:#e4ebf1;border-radius:8px;margin-top:13px;overflow:hidden}.bar>div{height:100%;background:var(--c)}
        .foot{display:flex;justify-content:space-between;color:#9aa7b3;font-size:9px;margin-top:7px}
        .ri{display:flex;align-items:center;gap:12px;padding:12px;margin-top:9px;background:#fafbfd;border:1px solid #e1e8ef;border-radius:11px}
        .ri.done{background:#f0faf8;border-color:#ccebe5}.ricon{width:39px;height:39px;flex:0 0 39px;border-radius:10px;background:#eaf2fb;color:#3675b5;display:flex;align-items:center;justify-content:center;font-size:18px}
        .ri.done .ricon{background:#dff5f1;color:#159d90}.rname{font-size:11px;font-weight:800;color:#304b63}.rmeta{font-size:9px;color:#9aa7b2;margin-top:4px}
        .dots{display:flex;gap:4px}.dot{width:15px;height:4px;border-radius:5px;background:#dce4ec}.dot.on{background:#2868b8}.ri.done .dot.on{background:#1aa596}
        .up{display:flex;align-items:center;gap:10px;padding:13px 12px;margin-top:9px;background:#f8fbfe;border:1px solid #dce7f0;border-radius:10px}
        .check{width:30px;height:30px;display:flex;align-items:center;justify-content:center;border-radius:8px;background:#2366b8;color:white;font-weight:900}
        .check.off{background:#edf1f5;color:#b8c1ca}.uname{font-size:11px;font-weight:800;color:#41586d}.umeta{font-size:9px;color:#a0acb7;margin-top:3px}
        .ustate{margin-left:auto;font-size:9px;color:#3474ae;font-weight:800;white-space:nowrap}.ustate.off{color:#aab4be}
        .chartbox{background:#fbfcfe;border:1px solid #e0e8ef;border-radius:14px;padding:15px}
        .ct{font-size:14px;font-weight:800;color:#405970}.cv{font-size:23px;font-weight:900;color:#173653;margin-top:4px}
        .event{background:#fbfcfe;border:1px solid #e1e8ef;border-left:4px solid #2b70bd;border-radius:11px;padding:14px;margin-top:10px;font-size:11px;color:#435b70}
        .st-key-analysis_card{background:linear-gradient(120deg,#164c91,#10386e);border-radius:17px;color:white;padding:22px;min-height:270px}
        .st-key-analysis_card [data-testid="stMarkdownContainer"]{color:white}.ak{color:#72d6ce;font-size:10px;letter-spacing:2px;font-weight:900}.at{font-size:20px;font-weight:900;margin-top:8px}
        .note{background:#ffffff17;border:1px solid #ffffff20;border-radius:10px;padding:11px;margin-top:9px;font-size:10px;line-height:1.65}
        .note strong{color:#8ce2d8}
        .stTabs [data-baseweb="tab-list"]{gap:4px;background:#eef3f8;border-radius:10px;padding:4px}
        .stTabs [data-baseweb="tab"]{border-radius:8px}
        @media(max-width:800px){.dashtitle{font-size:24px}.dashhead{padding-left:1.2rem;padding-right:1.2rem}.kpi{height:auto;min-height:105px}}
        </style>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# 5. 대시보드 화면 출력 함수
# ============================================================
def render_header(year, company):
    """프로젝트명과 회사명, 현재 게임 연도를 화면 맨 위에 표시합니다."""
    st.markdown(
        f"""
        <div class="dashhead">
            <div class="eyebrow">TO THE NET ZERO　—　{year}</div>
            <div style="display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap">
                <div>
                    <div class="dashtitle">투더넷 (To The Net Zero)</div>
                    <div class="sub">탄소중립 선박 경영 시뮬레이터 · {company} 운영 관제</div>
                </div>
                <div style="display:flex;align-items:center;gap:16px">
                    <span class="live">● LIVE</span>
                    <span class="sub">{year}년</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_kpi(year, money_now, emission, history):
    """현재 연도, 보유 자금, 탄소 배출량을 요약 카드로 표시합니다."""
    initial_money = to_int(history[0].get("money")) if history else money_now
    money_change = money_now - initial_money

    previous_emission = (
        to_int(history[-2].get("emission"), START_EMISSION)
        if len(history) > 1
        else START_EMISSION
    )
    emission_change = emission - previous_emission

    col_year, col_money, col_emission = st.columns(3)

    with col_year:
        st.markdown(
            f'<div class="kpi kpiblue"><div class="kl">현재 게임 연도</div>'
            f'<div class="kv">{year}</div>'
            f'<div class="kf">2026 — 2050 탄소중립 항해</div></div>',
            unsafe_allow_html=True,
        )

    with col_money:
        st.markdown(
            f'<div class="kpi"><div class="kl">현재 보유 자금</div>'
            f'<div class="kv">{format_money(money_now)}</div>'
            f'<div class="kf">초기 자금 대비 '
            f'{"+" if money_change >= 0 else ""}{format_money(money_change)}</div></div>',
            unsafe_allow_html=True,
        )

    with col_emission:
        change_label = (
            "감소" if emission_change < 0
            else "증가" if emission_change > 0
            else "변화 없음"
        )
        st.markdown(
            f'<div class="kpi"><div class="kl">현재 탄소 배출량</div>'
            f'<div class="kv">{emission}<span style="font-size:14px"> %</span></div>'
            f'<div class="kf">전 기록 대비 {abs(emission_change)}%p {change_label}</div></div>',
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height:15px'></div>", unsafe_allow_html=True)


def render_fleet(fleet):
    """보유 선박마다 선박 종류, 상태, 위치, 목적지, 진행률을 표시합니다."""
    st.markdown(
        '<div class="panel"><div class="ptitle">⚓ 선박 현황</div>'
        '<div class="psub">총 보유 선박의 현재 운항 상태를 확인합니다.</div>',
        unsafe_allow_html=True,
    )

    if not fleet:
        st.caption("등록된 선박이 없습니다.")
    else:
        columns = st.columns(min(3, len(fleet)))

        for index, ship in enumerate(fleet):
            ship_status = get_ship_status(ship)
            status_color = get_ship_status_color(ship)
            background_color = (
                "#eaf2fb" if ship_status in ("outbound", "sailing")
                else "#e8f8f5" if ship_status == "returning"
                else "#eef1f4"
            )

            destination = ship.get("dest") or "목적지 미배정"
            current_location = (
                "부산" if ship_status == "docked"
                else "항해 중" if ship_status in ("outbound", "sailing")
                else destination
            )

            total_distance = max(1, to_int(ship.get("total"), 100))
            current_position = max(0, to_int(ship.get("pos")))

            progress = (
                max(0, min(100, round(current_position / total_distance * 100)))
                if ship_status in ("outbound", "returning", "sailing")
                else 100
            )

            if ship_status == "returning":
                progress = 100 - progress

            remaining_text = (
                f"{to_int(ship.get('years_left'))}년 남음"
                if ship_status in ("outbound", "returning", "sailing")
                else "출항 대기"
            )

            with columns[index % len(columns)]:
                st.markdown(
                    f"""
                    <div class="ship" style="--c:{status_color};--bg:{background_color}">
                        <div class="shiptop">
                            <span style="font-size:11px;color:#b0bbc5;font-weight:800">{index + 1:02d}　🚢</span>
                            <span class="pill">{get_ship_status_label(ship)}</span>
                        </div>
                        <div class="shipname">{escape(str(ship.get('name', '선박')))}</div>
                        <div class="shiptype">{escape(str(ship.get('type', '선종 미상')))}</div>
                        <div class="route">
                            <div>
                                <div class="rl">현재 위치</div>
                                <div class="rp">{escape(str(current_location))}</div>
                            </div>
                            <div style="font-size:21px;color:#8ca3b9">→</div>
                            <div style="text-align:right">
                                <div class="rl">목적지</div>
                                <div class="rp">{escape(str(destination))}</div>
                            </div>
                        </div>
                        <div class="bar"><div style="width:{progress}%"></div></div>
                        <div class="foot">
                            <span>운항 진행률 {progress}%</span>
                            <span>{remaining_text}</span>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    st.markdown("</div>", unsafe_allow_html=True)


def render_research(research_levels, completed_stages):
    """탄소 감축 연구 6종의 연구 단계와 완료 여부를 표시합니다."""
    st.markdown(
        f'<div class="panel"><div class="ptitle">⚗️ 탄소 감축 연구</div>'
        f'<div class="psub">회사 전체에 적용되는 6개 연구 기술의 진행 상황</div>'
        f'<div style="text-align:right;color:#8494a5;font-size:10px;font-weight:800">'
        f'{completed_stages} / 18단계 완료</div>',
        unsafe_allow_html=True,
    )

    for research_id, name, _, icon in RESEARCH:
        level = to_int(research_levels.get(research_id))

        if research_id == "alternative_fuel":
            level = max(
                level,
                to_int(research_levels.get("ammonia")),
                to_int(research_levels.get("methanol")),
            )

        level = max(0, min(3, level))
        is_complete = level == 3

        # 연구 단계 수에 맞춰 작은 진행 표시 점 3개를 만듭니다.
        progress_dots = "".join(
            f'<span class="dot {"on" if stage < level else ""}"></span>'
            for stage in range(3)
        )
        completion_mark = (
            '<span style="color:#18a596">●</span>' if is_complete else ""
        )
        status_text = "연구 완료" if is_complete else f"현재 {level}단계"

        st.markdown(
            f'<div class="ri {"done" if is_complete else ""}">'
            f'<div class="ricon">{icon}</div>'
            f'<div style="flex:1;min-width:0">'
            f'<div class="rname">{escape(name)} {completion_mark}</div>'
            f'<div class="rmeta">{status_text}</div></div>'
            f'<div style="width:55px"><div class="dots">{progress_dots}</div></div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)


def render_upgrades(bought_transport, transport_levels):
    """구매한 선박 업그레이드만 메인 게임 데이터에 따라 표시합니다."""
    st.markdown(
        '<div class="panel"><div class="ptitle">🔧 선박 업그레이드</div>'
        '<div class="psub">구매한 강화 항목을 확인합니다.</div>',
        unsafe_allow_html=True,
    )

    for upgrade_id, name, effect in TRANSPORT:
        if upgrade_id == 3:
            # 자동화 하역 시스템은 단계별 연구이므로 별도 단계 정보를 읽습니다.
            level = max(0, min(3, to_int(transport_levels.get("handling"))))
            is_owned = level > 0
            detail = f"정박비 {level * 10}% 할인" if is_owned else effect
            state_text = f"{level}/3단계" if is_owned else "미구매"
        else:
            is_owned = upgrade_id in bought_transport
            detail = effect
            state_text = "구매 완료" if is_owned else "미구매"

        check_class = "" if is_owned else "off"
        check_mark = "✓" if is_owned else "−"
        state_class = "" if is_owned else "off"

        st.markdown(
            f'<div class="up"><div class="check {check_class}">{check_mark}</div>'
            f'<div><div class="uname">{escape(name)}</div>'
            f'<div class="umeta">{escape(detail)}</div></div>'
            f'<div class="ustate {state_class}">{state_text}</div></div>',
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)


def render_management_history(history, year, money_now, emission):
    """연도별 자금·탄소 배출량 그래프와 과거 기록 표를 표시합니다."""
    st.markdown(
        '<div class="panel"><div class="ptitle">📊 경영 기록</div>'
        '<div class="psub">연도별 핵심 경영 지표 추이</div>',
        unsafe_allow_html=True,
    )

    graph_tab, record_tab = st.tabs(["지표 그래프", "과거 기록"])

    with graph_tab:
        yearly_data = {}

        for item in history:
            recorded_year = to_int(item.get("year"), START_YEAR)
            yearly_data[recorded_year] = (
                to_int(item.get("money")),
                to_int(item.get("emission"), START_EMISSION),
            )

        # 현재 연도의 값은 세션 상태의 최신 값으로 덮어씁니다.
        yearly_data[year] = (money_now, emission)

        years = sorted(yearly_data)
        money_values = [
            yearly_data[recorded_year][0] / 100_000_000
            for recorded_year in years
        ]
        emission_values = [
            yearly_data[recorded_year][1]
            for recorded_year in years
        ]

        money_change = (
            (money_values[-1] - money_values[0]) / money_values[0] * 100
            if money_values and money_values[0]
            else 0
        )
        emission_change = (
            (emission_values[-1] - emission_values[0]) / emission_values[0] * 100
            if emission_values and emission_values[0]
            else 0
        )

        money_column, emission_column = st.columns(2)

        with money_column:
            st.markdown(
                f'<div class="chartbox"><div class="ct">보유 자금 변화</div>'
                f'<div class="sub">단위: 억 원</div>'
                f'<div class="cv">{format_money(money_now)}</div>'
                f'<div style="text-align:right;color:#159d90;font-size:10px;font-weight:800">'
                f'{money_change:+.1f}%</div>',
                unsafe_allow_html=True,
            )

            money_figure = go.Figure(
                go.Scatter(
                    x=years,
                    y=money_values,
                    mode="lines+markers",
                    line=dict(color="#2868b8", width=3),
                    marker=dict(
                        size=7,
                        color="white",
                        line=dict(color="#2868b8", width=2),
                    ),
                    fill="tozeroy",
                    fillcolor="rgba(40,104,184,.10)",
                    hovertemplate="%{x}년<br>%{y:,.1f}억 원<extra></extra>",
                )
            )
            st.plotly_chart(
                style_chart(money_figure),
                use_container_width=True,
                config={"displayModeBar": False},
                key="dash_money",
            )
            st.markdown("</div>", unsafe_allow_html=True)

        with emission_column:
            st.markdown(
                f'<div class="chartbox"><div class="ct">탄소 배출량 변화</div>'
                f'<div class="sub">단위: 게임 배출량(%)</div>'
                f'<div class="cv">{emission}%</div>'
                f'<div style="text-align:right;color:#159d90;font-size:10px;font-weight:800">'
                f'{emission_change:+.1f}%</div>',
                unsafe_allow_html=True,
            )

            emission_figure = go.Figure(
                go.Scatter(
                    x=years,
                    y=emission_values,
                    mode="lines+markers",
                    line=dict(color="#1aa596", width=3),
                    marker=dict(
                        size=7,
                        color="white",
                        line=dict(color="#1aa596", width=2),
                    ),
                    fill="tozeroy",
                    fillcolor="rgba(26,165,150,.11)",
                    hovertemplate="%{x}년<br>배출량 %{y}%<extra></extra>",
                )
            )
            emission_figure.update_yaxes(range=[0, 105])
            st.plotly_chart(
                style_chart(emission_figure),
                use_container_width=True,
                config={"displayModeBar": False},
                key="dash_emission",
            )
            st.markdown("</div>", unsafe_allow_html=True)

    with record_tab:
        if history:
            records = [
                {
                    "연도": f"{to_int(item.get('year'), START_YEAR)}년",
                    "보유 자금": format_money(item.get("money")),
                    "탄소 배출량": (
                        f"{to_int(item.get('emission'), START_EMISSION)}%"
                    ),
                }
                for item in reversed(history)
            ]
            st.dataframe(
                records,
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.caption("아직 저장된 경영 기록이 없습니다.")

    st.markdown("</div>", unsafe_allow_html=True)


def build_management_advice(phase, year, money_now, emission, next_checkpoint_year):
    """현재 경영 상태와 탄소 감축 목표를 바탕으로 안내 문구를 만듭니다."""
    if phase == "ended":
        return [
            (
                "최종 상태",
                "게임이 종료되었습니다. 최종 성과는 엔딩 화면에서 확인할 수 있습니다.",
            )
        ]

    advice = []

    if money_now < 20_000_000:
        advice.append(
            (
                "자금 흐름",
                "보유 자금이 2,000만원 미만입니다. 다음 항해 전 운영 비용을 고려하세요.",
            )
        )
    elif money_now >= 100_000_000:
        advice.append(
            (
                "자금 흐름",
                f"보유 자금은 {format_money(money_now)}입니다. "
                "향후 연구 및 선단 운영 계획을 검토할 수 있습니다.",
            )
        )
    else:
        advice.append(
            (
                "자금 흐름",
                "현재 보유 자금과 항해 수익을 바탕으로 안정적인 운영을 이어가고 있습니다.",
            )
        )

    if emission == 0:
        advice.append(
            (
                "탄소 감축",
                "탄소중립 목표를 달성했습니다. 연구 성과가 회사 전체 배출량에 반영되었습니다.",
            )
        )
    elif next_checkpoint_year is not None:
        target_emission = CHECKPOINTS[next_checkpoint_year]
        advice.append(
            (
                "탄소 감축",
                f"{next_checkpoint_year}년 목표는 {target_emission}% 이하입니다. "
                f"목표 달성까지 {max(0, emission - target_emission)}%p 추가 감축이 필요합니다.",
            )
        )
    else:
        advice.append(
            (
                "탄소 감축",
                f"현재 배출량은 {emission}%입니다. "
                f"2050년 탄소중립까지 {emission}%p 감축이 필요합니다.",
            )
        )

    return advice


def render_recent_events(events):
    """최근에 발생한 이벤트 기록을 최대 3개까지 표시합니다."""
    st.markdown(
        '<div class="panel"><div class="ptitle">♧ 최근 이벤트</div>'
        '<div class="psub">최근 발생한 주요 경영 이벤트</div>',
        unsafe_allow_html=True,
    )

    if events:
        for event in reversed(events[-3:]):
            st.markdown(
                f'<div class="event">{escape(str(event))}</div>',
                unsafe_allow_html=True,
            )
    else:
        st.caption("아직 발생한 이벤트가 없습니다.")

    st.markdown("</div>", unsafe_allow_html=True)


def render_management_analysis(
    phase,
    year,
    money_now,
    emission,
    goal_progress,
    remaining_reduction,
    next_checkpoint_year,
):
    """탄소 감축 진행률과 현재 경영 상태에 대한 안내를 표시합니다."""
    advice = build_management_advice(
        phase,
        year,
        money_now,
        emission,
        next_checkpoint_year,
    )

    # 안내 문구를 HTML 카드에 넣기 전, 특수문자가 HTML 코드로 해석되지 않도록 처리합니다.
    notes_html = "".join(
        f'<div class="note"><strong>{escape(title)}</strong>　'
        f'{escape(message)}</div>'
        for title, message in advice
    )

    # key가 지정된 Streamlit 컨테이너를 분석 카드의 바깥 상자로 사용합니다.
    with st.container(key="analysis_card"):
        st.markdown(
            '<div class="ak">SMART GUIDANCE</div>'
            '<div class="at">경영 분석</div>',
            unsafe_allow_html=True,
        )

        ring_column, summary_column = st.columns(
            [1, 1.25],
            vertical_alignment="center",
        )

        with ring_column:
            # 도넛 그래프의 두 값은 목표 진행률과 아직 남은 비율입니다.
            ring_figure = go.Figure(
                go.Pie(
                    values=[goal_progress, 100 - goal_progress],
                    hole=0.76,
                    marker=dict(
                        colors=["#62d7ca", "rgba(255,255,255,0.16)"],
                        line=dict(width=0),
                    ),
                    sort=False,
                    direction="clockwise",
                    hovertemplate="%{label}: %{value}%<extra></extra>",
                    labels=["감축 진행", "남은 비율"],
                    textinfo="none",
                )
            )
            ring_figure.update_layout(
                height=165,
                margin=dict(l=0, r=0, t=0, b=0),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                showlegend=False,
                font=dict(color="white"),
                annotations=[
                    dict(
                        text=(
                            f"<b>{goal_progress}%</b><br>"
                            "<span style='font-size:10px'>목표 진행</span>"
                        ),
                        x=0.5,
                        y=0.5,
                        showarrow=False,
                        font=dict(size=20, color="white"),
                    )
                ],
            )
            st.plotly_chart(
                ring_figure,
                use_container_width=True,
                config={"displayModeBar": False},
                key="dash_goal_ring",
            )

        with summary_column:
            st.markdown(
                f'<div style="padding:12px 2px;color:white">'
                f'<div style="font-size:10px;color:#b5cee7">탄소 감축 목표</div>'
                f'<div style="font-size:19px;font-weight:900;margin-top:5px">'
                f'{emission}% 배출</div>'
                f'<div style="font-size:10px;color:#b5cee7;margin-top:4px">'
                f'현재 목표까지 {remaining_reduction}%p 남음</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

        st.markdown(notes_html, unsafe_allow_html=True)


# ============================================================
# 6. 메인 실행 함수
# ============================================================
def main():
    """
    대시보드 페이지의 전체 실행 순서를 관리합니다.

    1) 페이지 기본 설정
    2) 게임 시작 여부 확인
    3) 게임 데이터 읽기 및 계산
    4) 디자인 적용
    5) 각 대시보드 영역을 순서대로 화면에 표시
    """
    st.set_page_config(
        page_title="투더넷 | 탄소중립 선박 경영 시뮬레이터",
        page_icon="🚢",
        layout="wide",
    )

    # 메인 게임을 아직 시작하지 않았다면 대시보드를 표시할 데이터가 없습니다.
    # 안내 메시지를 보여 주고 st.stop()으로 이 페이지의 나머지 실행을 중단합니다.
    if not st.session_state.get("started", False):
        st.info("게임을 시작하면 투더넷 관제 센터에서 회사 운영 현황을 확인할 수 있습니다.")
        st.stop()

    # 메인 게임의 데이터를 읽어 대시보드에서 사용할 변수에 정리합니다.
    dashboard_data = load_dashboard_data()

    current_year = dashboard_data["year"]
    current_money = dashboard_data["money"]
    current_phase = dashboard_data["phase"]
    company_name = dashboard_data["company"]
    fleet = dashboard_data["fleet"]
    history = dashboard_data["history"]
    events = dashboard_data["events"]
    research_levels = dashboard_data["research_levels"]
    bought_transport = dashboard_data["bought_transport"]
    transport_levels = dashboard_data["transport_levels"]

    # 연구 단계에서 현재 배출량과 전체 목표 진행률을 계산합니다.
    current_emission, completed_stages, goal_progress = calculate_emission_status(
        research_levels
    )
    next_checkpoint_year, remaining_reduction = calculate_management_targets(
        current_year,
        current_emission,
    )

    # 화면 스타일을 먼저 적용한 뒤, 각 영역을 위에서 아래 순서로 표시합니다.
    apply_dashboard_style()

    render_header(current_year, company_name)
    render_kpi(
        current_year,
        current_money,
        current_emission,
        history,
    )
    render_fleet(fleet)

    research_column, upgrade_column = st.columns([1.2, 1])

    with research_column:
        render_research(research_levels, completed_stages)

    with upgrade_column:
        render_upgrades(bought_transport, transport_levels)

    render_management_history(
        history,
        current_year,
        current_money,
        current_emission,
    )

    event_column, analysis_column = st.columns([0.9, 1.1])

    with event_column:
        render_recent_events(events)

    with analysis_column:
        render_management_analysis(
            current_phase,
            current_year,
            current_money,
            current_emission,
            goal_progress,
            remaining_reduction,
            next_checkpoint_year,
        )

    # 이 안내 문구는 대시보드가 게임 조작 화면이 아니라
    # 운영 데이터를 확인하는 화면이라는 점을 사용자에게 알려 줍니다.
    st.caption(
        "※ 투더넷 관제 센터는 운영 데이터 조회 전용 화면입니다. "
        "출항·귀항·구매·연구 등 게임 조작은 메인 화면에서 진행합니다."
    )


# 이 파일을 Streamlit 페이지로 실행했을 때만 대시보드를 표시합니다.
main()
