import streamlit as st
import pandas as pd
import json
import os

# ══════════════════════════════════════════════
# 1. 페이지 설정
# ══════════════════════════════════════════════
st.set_page_config(page_title="성가대 배치 시스템", layout="wide")

ADMIN_PASSWORD = "immanuel"   # ← 비밀번호 변경 시 여기만 수정
PINK_DARK  = "#E91E8C"        # 진한 핑크 (이름 있는 무대 자리)
PINK_BG    = "#FCE4EC"        # 연한 핑크 배경
YELLOW     = "#FFF9C4"        # 빈 자리 노란색

st.markdown("""
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0, user-scalable=yes">
<style>
/* ── 전체 레이아웃 ── */
.block-container { padding: 0.3rem 0.3rem 2rem !important; max-width: 100% !important; }
html, body { overflow-x: auto !important; touch-action: pan-x pan-y pinch-zoom !important; }

/* ── 탭 ── */
.stTabs [data-baseweb="tab"] {
    font-size: 1.0rem !important; font-weight: 700 !important; padding: 6px 14px !important;
}

/* ── 사이드바 ── */
.stSidebar { min-width: 200px !important; }

/* ── 배치 테이블 공통 ── */
.choir-table {
    border-collapse: separate;
    border-spacing: 3px;
    width: max-content;          /* 가로 스크롤 허용 */
    margin: 0 auto;
}
.choir-table td {
    text-align: center;
    vertical-align: middle;
    font-weight: bold;
    border-radius: 6px;
    white-space: nowrap;
    padding: 0;
}

/* ── 셀 크기 (기본 / 세로) ── */
.cell-name {
    width: 58px; height: 42px;
    font-size: 0.82rem;
    border: 2px solid #999;
    cursor: default;
}
.cell-label {
    width: 32px; height: 42px;
    font-size: 0.85rem; font-weight: 900;
    color: #111; background: none; border: none;
}
.cell-col-header {
    width: 58px; height: 28px;
    font-size: 0.85rem; font-weight: 900;
    color: #d32f2f; background: none; border: none;
}

/* ── 셀 색상 ── */
.c-stage-filled { background-color: #E91E8C; color: #fff; border-color: #880E4F !important; }
.c-stage-empty  { background-color: #FFF9C4; color: #aaa; border-color: #ccc !important; }
.c-aud-filled   { background-color: #fff;    color: #111; border-color: #999 !important; }
.c-aud-empty    { background-color: #FFF9C4; color: #aaa; border-color: #ccc !important; }
.c-fixed        { background-color: #e0e0e0; color: #555; border-color: #bbb !important; }
.c-cross        { font-size: 1.4rem; background: none; border: none; }

/* ── 가로 모드 (landscape) ── */
@media (orientation: landscape) and (max-height: 520px) {
    .cell-name      { width: 46px; height: 32px; font-size: 0.68rem; }
    .cell-label     { width: 24px; height: 32px; font-size: 0.7rem; }
    .cell-col-header{ width: 46px; height: 22px; font-size: 0.68rem; }
    .stTabs [data-baseweb="tab"] { font-size: 0.82rem !important; padding: 4px 8px !important; }
    h4 { font-size: 0.9rem !important; margin: 2px 0 4px !important; }
}

/* ── 통계 카드 ── */
.stats-card {
    background: #f8f9fa; padding: 8px 10px;
    border-radius: 8px; border-left: 5px solid #d32f2f; margin-bottom: 8px;
    display: inline-block; min-width: 70px; margin-right: 6px;
    text-align: center;
}

/* ── 스크롤 래퍼 ── */
.scroll-wrap {
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
    padding-bottom: 8px;
}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════
# 2. 데이터 관리
# ══════════════════════════════════════════════
DATA_FILE = "choir_data.json"

def save_to_json():
    data = {"stage": st.session_state.stage_data, "audience": st.session_state.audience_data}
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)

def update_master_stage():
    for k in st.session_state.stage_keys:
        val = st.session_state.get(f"s_in_{k}")
        if val is not None:
            st.session_state.stage_data[k] = val
    save_to_json()

def update_master_audience():
    for k in st.session_state.audience_keys:
        val = st.session_state.get(f"a_in_{k}")
        if val is not None:
            st.session_state.audience_data[k] = val
    save_to_json()

def load_all_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                content = json.load(f)
                if isinstance(content, dict) and "stage" in content:
                    return content
        except:
            return None
    return None

@st.cache_data
def load_member_part_map():
    file_name = "choir_list.xlsx"
    if os.path.exists(file_name):
        try:
            df = pd.read_excel(file_name)
            n_col = 'name' if 'name' in df.columns else '이름'
            p_col = 'part' if 'part' in df.columns else '파트'
            return {
                str(row[n_col]).replace(" ", "").strip(): str(row[p_col]).strip()
                for _, row in df.iterrows()
            }
        except:
            return {}
    return {}

member_part_map = load_member_part_map()

# ══════════════════════════════════════════════
# 3. 구성 상수
# ══════════════════════════════════════════════
TIER_CONFIG = [
    {"lv": 4, "left": "Tenor",   "right": "Bass", "seats": 14, "solo": "TB"},
    {"lv": 3, "left": "Tenor",   "right": "Bass", "seats": 13, "solo": None},
    {"lv": 2, "left": "Soprano", "right": "Alto", "seats": 14, "solo": "SA"},
    {"lv": 1, "left": "Soprano", "right": "Alto", "seats": 13, "solo": None},
]
ROWS = ['A','B','C','D','E','F','G','H','I','J','K']
COLS = [30,29,28,27,26,25]
PART_ZONES  = {"Soprano":['D','C','B'], "Alto":['F','E'], "Tenor":['H','G'], "Bass":['J','I']}
FIXED_EMPTY = ["B_25","B_26"]

# ══════════════════════════════════════════════
# 4. 세션 초기화
# ══════════════════════════════════════════════
if 'initialized' not in st.session_state:
    st.session_state.stage_keys    = [f"T{t['lv']}_S{s}" for t in TIER_CONFIG for s in range(t['seats'])]
    st.session_state.audience_keys = [f"{r}_{c}" for r in ROWS for c in COLS]
    saved = load_all_data()
    st.session_state.stage_data    = saved["stage"]    if saved else {k:"" for k in st.session_state.stage_keys}
    st.session_state.audience_data = saved["audience"] if saved else {k:"" for k in st.session_state.audience_keys}
    st.session_state.swap_sel      = []
    st.session_state.is_admin      = False
    st.session_state.initialized   = True

# ══════════════════════════════════════════════
# 5. 사이드바: 로그인
# ══════════════════════════════════════════════
with st.sidebar:
    st.markdown("### 🔐 관리자 로그인")
    if not st.session_state.is_admin:
        pw = st.text_input("비밀번호", type="password", key="pw_input")
        if st.button("로그인", use_container_width=True):
            if pw == ADMIN_PASSWORD:
                st.session_state.is_admin = True
                st.rerun()
            else:
                st.error("비밀번호가 틀렸습니다.")
        st.info("📖 읽기 전용 모드")
    else:
        st.success("✅ 관리자 모드")
        if st.button("로그아웃", use_container_width=True):
            st.session_state.is_admin = False
            st.rerun()

is_admin = st.session_state.is_admin

# ══════════════════════════════════════════════
# 6. 헬퍼
# ══════════════════════════════════════════════
def execute_swap(id1, id2):
    d1 = st.session_state.stage_data    if id1.startswith("T") else st.session_state.audience_data
    d2 = st.session_state.stage_data    if id2.startswith("T") else st.session_state.audience_data
    d1[id1], d2[id2] = d2[id2], d1[id1]
    st.session_state.swap_sel = []
    save_to_json(); st.rerun()

def stage_cell_html(sid, name, swap_mode, swap_sel):
    """무대 셀 HTML 생성 (읽기전용 / 스왑 표시용)"""
    filled = bool(name.strip())
    cls = "c-stage-filled" if filled else "c-stage-empty"
    label = name if filled else "—"
    # 교체 선택 중이면 테두리 강조
    selected = sid in swap_sel
    border = "border: 3px solid #FFD700 !important;" if selected else ""
    return f'<td class="cell-name {cls}" style="{border}">{label}</td>'

def aud_cell_html(aid, name):
    """객석 셀 HTML 생성 (읽기전용)"""
    if aid.startswith("A_"):
        return '<td class="cell-name c-fixed">CH</td>'
    if aid in FIXED_EMPTY:
        return '<td class="cell-name c-fixed">공석</td>'
    filled = bool(name.strip())
    cls = "c-aud-filled" if filled else "c-aud-empty"
    label = name if filled else "—"
    return f'<td class="cell-name {cls}">{label}</td>'

# ══════════════════════════════════════════════
# 7. 탭
# ══════════════════════════════════════════════
tab1, tab2, tab3 = st.tabs(["🎭 무대 배치도", "🪑 객석 배치표", "📊 출석 통계"])

# ─────────────────────────────────────────────
# TAB 1: 무대 배치도
# ─────────────────────────────────────────────
with tab1:
    ro_tag = "" if is_admin else " &nbsp;🔒 읽기전용"
    st.markdown(f"<h4>✝️ 무대 배치도{ro_tag}</h4>", unsafe_allow_html=True)

    if is_admin:
        s_swap = st.toggle("🔄 자리 교체 모드", key="s_swap")
        if s_swap and st.session_state.swap_sel:
            st.info(f"선택: **{st.session_state.swap_sel[0]}** → 교체할 자리 선택")
    else:
        s_swap = False

    # ── 읽기전용 or 교체 모드: HTML 테이블 ──
    if not is_admin or s_swap:
        html = '<div class="scroll-wrap"><table class="choir-table">'

        # 십자가 행
        max_seats = max(t['seats'] for t in TIER_CONFIG)
        html += '<tr>'
        html += '<td class="cell-label"></td>'
        mid_idx = max_seats // 2
        for s in range(max_seats):
            if s == mid_idx:
                html += '<td class="cell-name c-cross" colspan="1">✝️</td>'
            else:
                html += '<td class="cell-name" style="background:none;border:none;"></td>'
        html += '</tr>'

        for t in TIER_CONFIG:
            html += '<tr>'
            html += f'<td class="cell-label">{t["lv"]}단</td>'
            for s in range(t['seats']):
                sid  = f"T{t['lv']}_S{s}"
                name = st.session_state.stage_data.get(sid, "")
                filled = bool(name.strip())
                cls = "c-stage-filled" if filled else "c-stage-empty"
                label = name if filled else "—"
                selected = sid in st.session_state.swap_sel
                border = "border:3px solid #FFD700!important;" if selected else ""

                if s_swap and is_admin:
                    # 버튼처럼 클릭 가능하게: form submit 방식
                    html += f'<td class="cell-name {cls}" style="{border} cursor:pointer;" title="{sid}">'
                    html += label + '</td>'
                else:
                    html += f'<td class="cell-name {cls}" style="{border}">{label}</td>'

            # 남은 열 채우기 (단 수가 적을 때)
            for _ in range(max_seats - t['seats']):
                html += '<td style="background:none;border:none;width:58px;"></td>'
            html += '</tr>'

        html += '</table></div>'
        st.markdown(html, unsafe_allow_html=True)

        # 교체 모드일 때: 버튼으로 자리 선택
        if s_swap and is_admin:
            st.markdown("---")
            st.markdown("**교체할 자리 선택 (버튼 클릭):**")
            for t in TIER_CONFIG:
                btn_cols = st.columns(t['seats'])
                for s in range(t['seats']):
                    sid  = f"T{t['lv']}_S{s}"
                    name = st.session_state.stage_data.get(sid, "")
                    label = f"{t['lv']}단-{s+1}\n{name}" if name else f"{t['lv']}단-{s+1}"
                    with btn_cols[s]:
                        if st.button(name or "—", key=f"sb_{sid}", use_container_width=True):
                            st.session_state.swap_sel.append(sid)
                            if len(st.session_state.swap_sel) == 2:
                                execute_swap(st.session_state.swap_sel[0], st.session_state.swap_sel[1])
                            st.rerun()

    # ── 편집 모드: text_input (관리자, 스왑 아닐 때) ──
    else:
        # 십자가
        st.markdown("<div style='text-align:center;font-size:2rem;margin:4px 0'>✝️</div>", unsafe_allow_html=True)

        for t in TIER_CONFIG:
            n = t['seats']
            cols = st.columns([0.8] + [1]*n, gap="small")
            cols[0].markdown(
                f"<div style='font-weight:900;font-size:1rem;text-align:center;line-height:44px'>{t['lv']}단</div>",
                unsafe_allow_html=True)
            mid = n // 2
            for s in range(n):
                sid  = f"T{t['lv']}_S{s}"
                w_key = f"s_in_{sid}"
                cur  = st.session_state.stage_data.get(sid, "")
                filled = bool(cur.strip())
                pg = t['left'] if s < mid else t['right']
                ph = "⭐" if t['solo'] and ((s < mid and s == mid-3) or (s >= mid and s == mid+2)) else pg[:1]
                if w_key not in st.session_state or st.session_state[w_key] != cur:
                    st.session_state[w_key] = cur
                # 핑크 마커
                if filled:
                    mid_str = f"pm-T{t['lv']}-S{s}"
                    cols[s+1].markdown(
                        f'<div id="{mid_str}" style="display:none"></div>'
                        f'<style>div#{mid_str}+div[data-testid="stTextInput"] input'
                        f'{{background:{PINK_DARK}!important;color:#fff!important}}</style>',
                        unsafe_allow_html=True)
                with cols[s+1]:
                    st.text_input("", key=w_key, placeholder=ph,
                                  label_visibility="collapsed", on_change=update_master_stage)

# ─────────────────────────────────────────────
# TAB 2: 객석 배치표
# ─────────────────────────────────────────────
with tab2:
    ro_tag = "" if is_admin else " &nbsp;🔒 읽기전용"
    st.markdown(f"<h4>🪑 객석 배치표{ro_tag}</h4>", unsafe_allow_html=True)

    if is_admin:
        if st.button("🔄 무대 명단 → 객석 자동 정렬 (뒷줄 우선)", use_container_width=True):
            p_groups = {p: [] for p in PART_ZONES}; p_groups["미등록"] = []
            for t in TIER_CONFIG:
                for s in range(t['seats']-1, -1, -1):
                    sid  = f"T{t['lv']}_S{s}"
                    name = st.session_state.get(f"s_in_{sid}", st.session_state.stage_data.get(sid,"")).strip()
                    if name:
                        part = member_part_map.get(name.replace(" ",""), "미등록")
                        if part in p_groups: p_groups[part].append(name)
                        else: p_groups["미등록"].append(name)
            for k in st.session_state.audience_keys:
                if not k.startswith("A_"):
                    val = "공석" if k in FIXED_EMPTY else ""
                    st.session_state.audience_data[k] = val
                    st.session_state[f"a_in_{k}"] = val
            for p_name, p_rows in PART_ZONES.items():
                names = p_groups[p_name]
                if not names: continue
                n_ptr = 0
                for r_label in p_rows:
                    if n_ptr >= len(names): break
                    for c_label in COLS:
                        aid = f"{r_label}_{c_label}"
                        if aid in FIXED_EMPTY: continue
                        if n_ptr < len(names):
                            st.session_state.audience_data[aid] = names[n_ptr]
                            st.session_state[f"a_in_{aid}"] = names[n_ptr]
                            n_ptr += 1
                        else: break
            save_to_json(); st.rerun()

        a_swap = st.toggle("🔄 객석 자리 교체 모드", key="a_swap")
    else:
        a_swap = False

    # ── 읽기전용 + 교체모드: HTML 테이블 ──
    if not is_admin or a_swap:
        html = '<div class="scroll-wrap"><table class="choir-table">'
        # 헤더
        html += '<tr><td class="cell-label"></td>'
        for c in COLS:
            html += f'<td class="cell-col-header">{c}</td>'
        html += '</tr>'

        for r in ROWS:
            html += f'<tr><td class="cell-label">{r}</td>'
            for c in COLS:
                aid  = f"{r}_{c}"
                name = st.session_state.audience_data.get(aid, "")
                html += aud_cell_html(aid, name)
            html += '</tr>'
        html += '</table></div>'
        st.markdown(html, unsafe_allow_html=True)

        # 교체 모드 버튼
        if a_swap and is_admin:
            st.markdown("---")
            st.markdown("**교체할 자리 선택 (버튼 클릭):**")
            hc = st.columns([0.8] + [1]*6)
            for i, c in enumerate(COLS):
                hc[i+1].markdown(f"<div style='text-align:center;font-weight:900;color:#d32f2f'>{c}</div>", unsafe_allow_html=True)
            for r in ROWS:
                rc = st.columns([0.8] + [1]*6)
                rc[0].markdown(f"<div style='text-align:center;font-weight:900;line-height:44px'>{r}</div>", unsafe_allow_html=True)
                for ci, c in enumerate(COLS):
                    aid  = f"{r}_{c}"
                    name = st.session_state.audience_data.get(aid, "")
                    with rc[ci+1]:
                        if r == 'A' or aid in FIXED_EMPTY:
                            st.button("—", key=f"af_{aid}", disabled=True, use_container_width=True)
                        else:
                            if st.button(name or "—", key=f"ab_{aid}", use_container_width=True):
                                st.session_state.swap_sel.append(aid)
                                if len(st.session_state.swap_sel) == 2:
                                    execute_swap(st.session_state.swap_sel[0], st.session_state.swap_sel[1])
                                st.rerun()

    # ── 편집 모드 ──
    else:
        hc = st.columns([0.8] + [1]*6)
        for i, c in enumerate(COLS):
            hc[i+1].markdown(f"<div style='text-align:center;font-weight:900;color:#d32f2f;font-size:0.9rem'>{c}</div>", unsafe_allow_html=True)
        for r in ROWS:
            rc = st.columns([0.8] + [1]*6)
            rc[0].markdown(f"<div style='text-align:center;font-weight:900;font-size:0.9rem;line-height:44px'>{r}</div>", unsafe_allow_html=True)
            for ci, c in enumerate(COLS):
                aid   = f"{r}_{c}"
                w_key = f"a_in_{aid}"
                cur   = st.session_state.audience_data.get(aid, "")
                with rc[ci+1]:
                    if r == 'A':
                        st.text_input("", value="CH", key=f"af_{aid}", disabled=True, label_visibility="collapsed")
                    elif aid in FIXED_EMPTY:
                        st.text_input("", value="공석", key=f"ae_{aid}", disabled=True, label_visibility="collapsed")
                    else:
                        if w_key not in st.session_state:
                            st.session_state[w_key] = cur
                        st.text_input("", key=w_key, placeholder=f"{r}{c}",
                                      label_visibility="collapsed", on_change=update_master_audience)

# ─────────────────────────────────────────────
# TAB 3: 출석 통계
# ─────────────────────────────────────────────
with tab3:
    st.markdown("<h4>📊 파트별 출석 통계</h4>", unsafe_allow_html=True)
    counts = {p: 0 for p in PART_ZONES}; counts["미등록"] = 0
    for name in st.session_state.stage_data.values():
        if name.strip():
            part = member_part_map.get(name.replace(" ",""), "미등록")
            if part in counts: counts[part] += 1
            else: counts["미등록"] += 1
    total = sum(counts.values())

    cards_html = ""
    for p, cnt in counts.items():
        cards_html += (
            f"<div class='stats-card'>"
            f"<div style='font-size:0.75rem;color:#666'>{p}</div>"
            f"<div style='font-size:1.2rem;font-weight:bold'>{cnt}명</div>"
            f"</div>"
        )
    st.markdown(cards_html, unsafe_allow_html=True)
    st.markdown(
        f"<div style='text-align:right;font-size:1.2rem;font-weight:bold;color:#d32f2f;margin-top:8px'>"
        f"총 출석: {total}명</div>", unsafe_allow_html=True)
