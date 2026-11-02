import streamlit as st
import plotly.graph_objects as go
from html import escape

# 청해해운 관제 센터: main.py의 세션 상태를 읽기만 하는 모니터링 페이지
START_YEAR, END_YEAR, START_EMISSION = 2026, 2050, 100
CHECKPOINTS = {2030: 80, 2040: 30, 2050: 0}

RESEARCH = [
    ("alternative_fuel", "차세대 무탄소 연료 추진 기술", [5, 7, 8], "⚗"),
    ("capture", "선상 탄소 포집 기술", [4, 6, 8], "♢"),
    ("efficiency", "에너지 효율 개선 기술", [4, 5, 6], "▱"),
    ("wind", "풍력 보조 추진 기술", [3, 5, 7], "≋"),
    ("shore_power", "육상 전력 공급 기술", [3, 5, 7], "⌁"),
    ("hydrogen", "청정 수소·연료전지 기술", [4, 6, 7], "▣"),
]
TRANSPORT = [
    (1, "화물 적재함 확장", "모든 항해 수익 +10%"),
    (2, "대형 선체로 교체", "모든 항해 수익 +25%"),
    (3, "자동화 하역 시스템", "정박비 할인 연구"),
    (4, "자율운항선박", "자동 운항 기능 해금"),
]

def num(v, default=0):
    try: return int(v or 0)
    except (TypeError, ValueError): return default

def money(v):
    v = num(v); sign = "-" if v < 0 else ""; v = abs(v)
    eok, rem = divmod(v, 100_000_000); man = rem // 10_000
    if eok and man: return f"{sign}{eok:,}억 {man:,}만원"
    if eok: return f"{sign}{eok:,}억원"
    if man: return f"{sign}{man:,}만원"
    return f"{sign}{v:,}원"

def status(ship):
    return ship.get("status", ship.get("phase", "docked"))

def status_label(ship):
    return {"outbound":"항해 중","sailing":"항해 중","returning":"귀항 중","docked":"정박 중"}.get(status(ship),"상태 확인 중")

def status_color(ship):
    return {"outbound":"#2868bd","sailing":"#2868bd","returning":"#18a596","docked":"#8b98a8"}.get(status(ship),"#8b98a8")

def chart_style(fig):
    fig.update_layout(height=245, margin=dict(l=5,r=10,t=8,b=8),
        paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#173653",size=11),showlegend=False,
        xaxis=dict(showgrid=False,zeroline=False,tickfont=dict(color="#91a0af")),
        yaxis=dict(showgrid=True,gridcolor="#e8edf3",zeroline=False,tickfont=dict(color="#91a0af")))
    return fig

st.set_page_config(page_title="청해해운 관제 센터", page_icon="🚢", layout="wide")
if not st.session_state.get("started", False):
    st.info("게임을 시작하면 관제 센터에서 회사 운영 현황을 확인할 수 있습니다.")
    st.stop()

year = num(st.session_state.get("year"), START_YEAR)
money_now = num(st.session_state.get("money"))
phase = st.session_state.get("phase", "docked")
company = escape(str(st.session_state.get("company_name") or "청해해운"))
fleet = st.session_state.get("fleet", []) or []
history = [x for x in (st.session_state.get("history", []) or []) if isinstance(x, dict)]
events = st.session_state.get("event_log", []) or []
levels = st.session_state.get("research_levels", {}) or {}
bought = set(st.session_state.get("bought_tr", []) or [])
transport_levels = st.session_state.get("transport_levels", {}) or {}

reduction, done_stages = 0, 0
for tid, _, stages, _ in RESEARCH:
    lv = num(levels.get(tid))
    if tid == "alternative_fuel":
        lv = max(lv, num(levels.get("ammonia")), num(levels.get("methanol")))
    lv = max(0, min(3, lv))
    done_stages += lv
    reduction += sum(stages[:lv])
emission = max(0, START_EMISSION-reduction)
goal_progress = max(0, min(100, round((START_EMISSION-emission)/START_EMISSION*100)))
next_checkpoint_year = next((y for y in sorted(CHECKPOINTS) if year < y), None)
remaining_reduction = (
    max(0, emission - CHECKPOINTS[next_checkpoint_year])
    if next_checkpoint_year is not None else emission
)

st.markdown("""
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
.analysis{background:linear-gradient(120deg,#164c91,#10386e);border-radius:17px;color:white;padding:22px;min-height:270px}
.analysis *{color:inherit}.ak{color:#72d6ce;font-size:10px;letter-spacing:2px;font-weight:900}.at{font-size:20px;font-weight:900;margin-top:8px}
.note{background:#ffffff17;border:1px solid #ffffff20;border-radius:10px;padding:11px;margin-top:9px;font-size:10px;line-height:1.65}
.note strong{color:#8ce2d8}
.stTabs [data-baseweb="tab-list"]{gap:4px;background:#eef3f8;border-radius:10px;padding:4px}
.stTabs [data-baseweb="tab"]{border-radius:8px}
@media(max-width:800px){.dashtitle{font-size:24px}.dashhead{padding-left:1.2rem;padding-right:1.2rem}.kpi{height:auto;min-height:105px}}
</style>
""", unsafe_allow_html=True)

# 헤더
st.markdown(f"""<div class="dashhead"><div class="eyebrow">OPERATIONS　—　{year}</div>
<div style="display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap">
<div><div class="dashtitle">{company} 관제 센터</div><div class="sub">선대 운영과 탄소중립 전환 현황을 실시간으로 관리합니다.</div></div>
<div style="display:flex;align-items:center;gap:16px"><span class="live">● LIVE</span><span class="sub">{year}년</span></div></div></div>""", unsafe_allow_html=True)

# KPI
a,b,c=st.columns(3)
initial_money=num(history[0].get("money")) if history else money_now
delta=money_now-initial_money
prev_em=num(history[-2].get("emission"),START_EMISSION) if len(history)>1 else START_EMISSION
em_delta=emission-prev_em
with a: st.markdown(f'<div class="kpi kpiblue"><div class="kl">현재 게임 연도</div><div class="kv">{year}</div><div class="kf">2026 — 2050 탄소중립 항해</div></div>',unsafe_allow_html=True)
with b: st.markdown(f'<div class="kpi"><div class="kl">현재 보유 자금</div><div class="kv">{money(money_now)}</div><div class="kf">초기 자금 대비 {"+" if delta>=0 else ""}{money(delta)}</div></div>',unsafe_allow_html=True)
with c: st.markdown(f'<div class="kpi"><div class="kl">현재 탄소 배출량</div><div class="kv">{emission}<span style="font-size:14px"> %</span></div><div class="kf">전 기록 대비 {abs(em_delta)}%p {"감소" if em_delta<0 else "증가" if em_delta>0 else "변화 없음"}</div></div>',unsafe_allow_html=True)

st.markdown("<div style='height:15px'></div>",unsafe_allow_html=True)

# 선박 현황
st.markdown('<div class="panel"><div class="ptitle">⚓ 선박 현황</div><div class="psub">총 보유 선박의 현재 운항 상태를 확인합니다.</div>',unsafe_allow_html=True)
if fleet:
    cols=st.columns(min(3,len(fleet)))
    for i,ship in enumerate(fleet):
        s=status(ship); color=status_color(ship); bg="#eaf2fb" if s in ("outbound","sailing") else "#e8f8f5" if s=="returning" else "#eef1f4"
        dest=ship.get("dest") or "목적지 미배정"; current="부산" if s=="docked" else ("항해 중" if s in ("outbound","sailing") else dest)
        total=max(1,num(ship.get("total"),100)); pos=max(0,num(ship.get("pos")))
        prog=max(0,min(100,round(pos/total*100))) if s in ("outbound","returning","sailing") else 100
        if s=="returning": prog=100-prog
        remain=f"{num(ship.get('years_left'))}년 남음" if s in ("outbound","returning","sailing") else "출항 대기"
        with cols[i%len(cols)]:
            st.markdown(f"""<div class="ship" style="--c:{color};--bg:{bg}">
<div class="shiptop"><span style="font-size:11px;color:#b0bbc5;font-weight:800">{i+1:02d}　🚢</span><span class="pill">{status_label(ship)}</span></div>
<div class="shipname">{escape(str(ship.get('name','선박')))}</div><div class="shiptype">{escape(str(ship.get('type','선종 미상')))}</div>
<div class="route"><div><div class="rl">현재 위치</div><div class="rp">{escape(str(current))}</div></div><div style="font-size:21px;color:#8ca3b9">→</div>
<div style="text-align:right"><div class="rl">목적지</div><div class="rp">{escape(str(dest))}</div></div></div>
<div class="bar"><div style="width:{prog}%"></div></div><div class="foot"><span>운항 진행률 {prog}%</span><span>{remain}</span></div></div>""",unsafe_allow_html=True)
else: st.caption("등록된 선박이 없습니다.")
st.markdown("</div>",unsafe_allow_html=True)

# 연구 및 업그레이드
rc,uc=st.columns([1.2,1])
with rc:
    st.markdown(f'<div class="panel"><div class="ptitle">⚗️ 탄소 감축 연구</div><div class="psub">회사 전체에 적용되는 6개 연구 기술의 진행 상황</div><div style="text-align:right;color:#8494a5;font-size:10px;font-weight:800">{done_stages} / 18단계 완료</div>',unsafe_allow_html=True)
    for tid,name,stages,icon in RESEARCH:
        lv=num(levels.get(tid))
        if tid=="alternative_fuel": lv=max(lv,num(levels.get("ammonia")),num(levels.get("methanol")))
        lv=max(0,min(3,lv)); complete=lv==3
        dots="".join(f'<span class="dot {"on" if j<lv else ""}"></span>' for j in range(3))
        st.markdown(f'<div class="ri {"done" if complete else ""}"><div class="ricon">{icon}</div><div style="flex:1;min-width:0"><div class="rname">{escape(name)} {"<span style=color:#18a596>●</span>" if complete else ""}</div><div class="rmeta">{"연구 완료" if complete else f"현재 {lv}단계"}</div></div><div style="width:55px"><div class="dots">{dots}</div></div></div>',unsafe_allow_html=True)
    st.markdown("</div>",unsafe_allow_html=True)
with uc:
    st.markdown('<div class="panel"><div class="ptitle">🔧 선박 업그레이드</div><div class="psub">구매한 강화 항목을 확인합니다.</div>',unsafe_allow_html=True)
    for tid,name,effect in TRANSPORT:
        if tid==3:
            lv=max(0,min(3,num(transport_levels.get("handling")))); owned=lv>0
            detail=f"정박비 {lv*10}% 할인" if owned else effect; state=f"{lv}/3단계" if owned else "미구매"
        else:
            owned=tid in bought; detail=effect; state="구매 완료" if owned else "미구매"
        st.markdown(f'<div class="up"><div class="check {"off" if not owned else ""}">{"✓" if owned else "−"}</div><div><div class="uname">{name}</div><div class="umeta">{detail}</div></div><div class="ustate {"off" if not owned else ""}">{state}</div></div>',unsafe_allow_html=True)
    st.markdown("</div>",unsafe_allow_html=True)

# 경영 기록
st.markdown('<div class="panel"><div class="ptitle">📊 경영 기록</div><div class="psub">연도별 핵심 경영 지표 추이</div>',unsafe_allow_html=True)
tg,th=st.tabs(["지표 그래프","과거 기록"])
with tg:
    by_year={}
    for item in history:
        by_year[num(item.get("year"),START_YEAR)]=(num(item.get("money")),num(item.get("emission"),START_EMISSION))
    by_year[year]=(money_now,emission)
    years=sorted(by_year)
    mvals=[by_year[y][0]/100_000_000 for y in years]; evals=[by_year[y][1] for y in years]
    mchange=((mvals[-1]-mvals[0])/mvals[0]*100) if mvals and mvals[0] else 0
    echange=((evals[-1]-evals[0])/evals[0]*100) if evals and evals[0] else 0
    l,r=st.columns(2)
    with l:
        st.markdown(f'<div class="chartbox"><div class="ct">보유 자금 변화</div><div class="sub">단위: 억 원</div><div class="cv">{money(money_now)}</div><div style="text-align:right;color:#159d90;font-size:10px;font-weight:800">{mchange:+.1f}%</div>',unsafe_allow_html=True)
        f=go.Figure(go.Scatter(x=years,y=mvals,mode="lines+markers",line=dict(color="#2868b8",width=3),marker=dict(size=7,color="white",line=dict(color="#2868b8",width=2)),fill="tozeroy",fillcolor="rgba(40,104,184,.10)",hovertemplate="%{x}년<br>%{y:,.1f}억 원<extra></extra>"))
        st.plotly_chart(chart_style(f),use_container_width=True,config={"displayModeBar":False},key="dash_money")
        st.markdown("</div>",unsafe_allow_html=True)
    with r:
        st.markdown(f'<div class="chartbox"><div class="ct">탄소 배출량 변화</div><div class="sub">단위: 게임 배출량(%)</div><div class="cv">{emission}%</div><div style="text-align:right;color:#159d90;font-size:10px;font-weight:800">{echange:+.1f}%</div>',unsafe_allow_html=True)
        f=go.Figure(go.Scatter(x=years,y=evals,mode="lines+markers",line=dict(color="#1aa596",width=3),marker=dict(size=7,color="white",line=dict(color="#1aa596",width=2)),fill="tozeroy",fillcolor="rgba(26,165,150,.11)",hovertemplate="%{x}년<br>배출량 %{y}%<extra></extra>"))
        f.update_yaxes(range=[0,105])
        st.plotly_chart(chart_style(f),use_container_width=True,config={"displayModeBar":False},key="dash_emission")
        st.markdown("</div>",unsafe_allow_html=True)
with th:
    if history:
        st.dataframe([{"연도":f"{num(x.get('year'),START_YEAR)}년","보유 자금":money(x.get("money")),"탄소 배출량":f"{num(x.get('emission'),START_EMISSION)}%"} for x in reversed(history)],use_container_width=True,hide_index=True)
    else: st.caption("아직 저장된 경영 기록이 없습니다.")
st.markdown("</div>",unsafe_allow_html=True)

# 최근 이벤트와 경영 분석
ec,ac=st.columns([.9,1.1])
with ec:
    st.markdown('<div class="panel"><div class="ptitle">♧ 최근 이벤트</div><div class="psub">최근 발생한 주요 경영 이벤트</div>',unsafe_allow_html=True)
    if events:
        for entry in reversed(events[-3:]): st.markdown(f'<div class="event">{escape(str(entry))}</div>',unsafe_allow_html=True)
    else: st.caption("아직 발생한 이벤트가 없습니다.")
    st.markdown("</div>",unsafe_allow_html=True)
if phase=="ended":
    advice=[("최종 상태","게임이 종료되었습니다. 최종 성과는 엔딩 화면에서 확인할 수 있습니다.")]
else:
    advice=[]
    if money_now<20_000_000: advice.append(("자금 흐름","보유 자금이 2,000만원 미만입니다. 다음 항해 전 운영 비용을 고려하세요."))
    elif money_now>=100_000_000: advice.append(("자금 흐름",f"보유 자금은 {money(money_now)}입니다. 향후 연구 및 선단 운영 계획을 검토할 수 있습니다."))
    else: advice.append(("자금 흐름","현재 보유 자금과 항해 수익을 바탕으로 안정적인 운영을 이어가고 있습니다."))
    next_year=next((y for y in sorted(CHECKPOINTS) if year<y),None)
    if emission==0: advice.append(("탄소 감축","탄소중립 목표를 달성했습니다. 연구 성과가 회사 전체 배출량에 반영되었습니다."))
    elif next_year:
        target=CHECKPOINTS[next_year]; advice.append(("탄소 감축",f"{next_year}년 목표는 {target}% 이하입니다. 목표 달성까지 {max(0,emission-target)}%p 추가 감축이 필요합니다."))
    else: advice.append(("탄소 감축",f"현재 배출량은 {emission}%입니다. 2050년 탄소중립까지 {emission}%p 감축이 필요합니다."))
with ac:
    notes="".join(f'<div class="note"><strong>{escape(t)}</strong>　{escape(msg)}</div>' for t,msg in advice)
    st.markdown('<div class="analysis"><div class="ak">SMART GUIDANCE</div><div class="at">경영 분석</div>', unsafe_allow_html=True)
    ring_col, summary_col = st.columns([1, 1.25], vertical_alignment="center")
    with ring_col:
        ring = go.Figure(go.Pie(
            values=[goal_progress, 100-goal_progress], hole=0.76,
            marker=dict(colors=["#62d7ca", "rgba(255,255,255,0.16)"], line=dict(width=0)),
            sort=False, direction="clockwise",
            hovertemplate="%{label}: %{value}%<extra></extra>",
            labels=["감축 진행", "남은 비율"], textinfo="none",
        ))
        ring.update_layout(
            height=165, margin=dict(l=0, r=0, t=0, b=0),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            showlegend=False, font=dict(color="white"),
            annotations=[dict(text=f"<b>{goal_progress}%</b><br><span style='font-size:10px'>목표 진행</span>",
                              x=0.5, y=0.5, showarrow=False, font=dict(size=20, color="white"))],
        )
        st.plotly_chart(ring, use_container_width=True, config={"displayModeBar": False}, key="dash_goal_ring")
    with summary_col:
        st.markdown(
            f'<div style="padding:12px 2px;color:white">'
            f'<div style="font-size:10px;color:#b5cee7">탄소 감축 목표</div>'
            f'<div style="font-size:19px;font-weight:900;margin-top:5px">{emission}% 배출</div>'
            f'<div style="font-size:10px;color:#b5cee7;margin-top:4px">현재 목표까지 {remaining_reduction}%p 남음</div>'
            f'</div>', unsafe_allow_html=True
        )
    st.markdown(notes, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

st.caption("※ 관제 센터는 운영 데이터 조회 전용 화면입니다. 출항·귀항·구매·연구 등 게임 조작은 메인 화면에서 진행합니다.")
