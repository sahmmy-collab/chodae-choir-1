import streamlit as st
import pandas as pd
import json
import os

# ══════════════════════════════════════════════
# 1. 페이지 설정
# ══════════════════════════════════════════════
st.set_page_config(page_title="성가대 배치 시스템", layout="wide")

ADMIN_PASSWORD = "immanuel"   # ← 원하는 비밀번호로 변경하세요
PINK   = "#F48FB1"            # 진한 핑크 (이름 있는 무대 자리)

# ── 전역 CSS ──────────────────────────────────
st.markdown("""
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0, user-scalable=yes">
<style>
/* ── 기본 레이아웃 ── */
.block-container { padding: 0.5rem 0.5rem 2rem !important; }
.stTextInput { margin-bottom: 4px !important; }
.stTextInput input {
    font-weight: bold !important; color: #000 !important;
    font-size: 1.0rem !important; text-align: center;
    height: 44px !important; border: 2px solid #555 !important;
    border-radius: 6px !important; padding: 0 !important;
    touch-action: manipulation;
}
input:placeholder-shown { background-color: #FFF9C4 !important; }
.row-label {
    font-size: 1.1rem !important; font-weight: 900 !important;
    color: #111; text-align: center; line-height: 44px;
}
.col-label {
    text-align: center; font-weight: 900 !important;
    color: #d32f2f; font-size: 1.1rem !important; margin-bottom: 4px;
}
.cross-container {
    display: flex; justify-content: center; align-items: center;
    font-size: 40px; color: #444; height: 48px; margin-bottom: 4px;
}
.stButton button {
    font-size: 0.85rem !important; font-weight: bold !important;
    height: 44px !important; border-radius: 6px;
    touch-action: manipulation;
}
.stats-card {
    background: #f8f9fa; padding: 8px 10px;
    border-radius: 8px; border-left: 5px solid #d32f2f; margin-bottom: 8px;
}
/* ── 읽기 전용 셀 ── */
.ro-cell {
    display: flex; align-items: center; justify-content: center;
    height: 44px; border: 2px solid #aaa; border-radius: 6px;
    font-weight: bold; font-size: 0.9rem; color: #111;
    margin-bottom: 4px; user-select: none; box-sizing: border-box;
}
.ro-filled  { background-color: #F48FB1; border-color: #c2185b; }
.ro-empty   { background-color: #FFF9C4; color: #bbb; }
.ro-fixed   { background-color: #e0e0e0; color: #555; }
.ro-aud     { background-color: #fff; }

/* ── 탭 ── */
.stTabs [data-baseweb="tab"] {
    font-size: 1.05rem !important; font-weight: 700 !important;
    padding: 8px 18px !important;
}

/* ── 가로 모드 (landscape) 최적화 ── */
@media (orientation: landscape) and (max-height: 520px) {
    .block-container { padding: 0.1rem 0.2rem 1rem !important; }
    .stTextInput input { height: 34px !important; font-size: 0.78rem !important; }
    .row-label { font-size: 0.82rem !important; line-height: 34px; }
    .col-label { font-size: 0.82rem !important; }
    .stButton button { height: 34px !important; font-size: 0.7rem !important; }
    .ro-cell { height: 34px; font-size: 0.75rem; }
    .cross-container { font-size: 24px; height: 32px; }
    h1, h2, h3, h4 { font-size: 0.95rem !important; margin: 2px 0 !important; }
    .stTabs [data-baseweb="tab"] { font-size: 0.88rem !important; padding: 5px 10px !important; }
}

/* ── 세로 모드 소형 폰 ── */
@media (orientation: portrait) and (max-width: 400px) {
    .stTextInput input { font-size: 0.75rem !important; height: 38px !important; }
    .row-label { font-size: 0.82rem !important; line-height: 38px; }
    .ro-cell { height: 38px; font-size: 0.75rem; }
}

/* ── 핀치 줌 & 스크롤 허용 ── */
html, body { overflow-x: auto !important; touch-action: pan-x pan-y pinch-zoom !important; }
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
    st.session_state.swap_list     = []
    st.session_state.is_admin      = False
    st.session_state.initialized   = True

# ══════════════════════════════════════════════
# 5. 사이드바: 비밀번호 / 관리자 로그인
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
        st.info("📖 현재: **읽기 전용** 모드")
    else:
        st.success("✅ 관리자 모드 활성")
        if st.button("로그아웃", use_container_width=True):
            st.session_state.is_admin = False
            st.rerun()

is_admin = st.session_state.is_admin

# ══════════════════════════════════════════════
# 6. 헬퍼 함수
# ══════════════════════════════════════════════
def execute_swap(id1, id2):
    d1 = st.session_state.stage_data    if id1.startswith("T") else st.session_state.audience_data
    d2 = st.session_state.stage_data    if id2.startswith("T") else st.session_state.audience_data
    d1[id1], d2[id2] = d2[id2], d1[id1]
    st.session_state.swap_list = []
    save_to_json(); st.rerun()

def pink_marker(uid):
    return (
        f'<div id="{uid}" style="display:none"></div>'
        f'<style>'
        f'div#{uid}+div[data-testid="stTextInput"] input,'
        f'div#{uid}+div .stTextInput input'
        f'{{background-color:{PINK}!important;}}'
        f'</style>'
    )

def ro_cell(name: str, kind: str = "aud"):
    """읽기 전용 셀. kind: filled | empty | fixed | aud"""
    display = name if name.strip() else "—"
    st.markdown(f"<div class='ro-cell ro-{kind}'>{display}</div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════
# 7. 탭
# ══════════════════════════════════════════════
tab1, tab2, tab3 = st.tabs(["🎭 무대 배치도", "🪑 객석 배치표", "📊 출석 통계"])

# ─────────────────────────────────────────────
# TAB 1 : 무대 배치도
# ─────────────────────────────────────────────
with tab1:
    title_suffix = "" if is_admin else " &nbsp;🔒 읽기전용"
    st.markdown(f"<h4 style='margin-bottom:6px'>✝️ 무대 배치도{title_suffix}</h4>", unsafe_allow_html=True)

    if is_admin:
        s_swap = st.toggle("🔄 자리 교체 모드", key="s_swap")
    else:
        s_swap = False

    for t in TIER_CONFIG:
        n = t['seats']
        cols = st.columns([1.0] + [2.8]*n, gap="small")
        cols[0].markdown(f"<div class='row-label'>{t['lv']}단</div>", unsafe_allow_html=True)
        mid = n // 2

        for s in range(n):
            sid      = f"T{t['lv']}_S{s}"
            w_key    = f"s_in_{sid}"
            cur      = st.session_state.stage_data.get(sid, "")
            filled   = bool(cur.strip())

            with cols[s+1]:
                # 읽기 전용
                if not is_admin:
                    ro_cell(cur, "filled" if filled else "empty")

                # 관리자 교체 모드
                elif s_swap:
                    if filled:
                        mc = f"spk-{sid}".replace("_","-")
                        st.markdown(
                            f"<style>.{mc} button{{background:{PINK}!important;color:#000!important}}</style>"
                            f"<div class='{mc}'>", unsafe_allow_html=True)
                    clicked = st.button(cur if filled else "—", key=f"sb_{sid}", use_container_width=True)
                    if filled:
                        st.markdown("</div>", unsafe_allow_html=True)
                    if clicked:
                        st.session_state.swap_list.append(sid)
                        if len(st.session_state.swap_list) == 2:
                            execute_swap(st.session_state.swap_list[0], st.session_state.swap_list[1])

                # 관리자 편집 모드
                else:
                    pg = t['left'] if s < mid else t['right']
                    ph = "⭐" if t['solo'] and ((s < mid and s == mid-3) or (s >= mid and s == mid+2)) else pg[:1]
                    if w_key not in st.session_state or st.session_state[w_key] != cur:
                        st.session_state[w_key] = cur
                    if filled:
                        st.markdown(pink_marker(f"pm-T{t['lv']}-S{s}"), unsafe_allow_html=True)
                    st.text_input("", key=w_key, placeholder=ph,
                                  label_visibility="collapsed", on_change=update_master_stage)

    if is_admin and s_swap and st.session_state.swap_list:
        st.info(f"선택됨: **{st.session_state.swap_list[0]}** → 교체할 자리를 선택하세요.")

# ─────────────────────────────────────────────
# TAB 2 : 객석 배치표
# ─────────────────────────────────────────────
with tab2:
    title_suffix = "" if is_admin else " &nbsp;🔒 읽기전용"
    st.markdown(f"<h4 style='margin-bottom:6px'>🪑 객석 배치표{title_suffix}</h4>", unsafe_allow_html=True)

    if is_admin:
        # 자동 정렬 버튼
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

    # 열 헤더
    hc = st.columns([1.0] + [3.0]*6)
    for i, c in enumerate(COLS):
        hc[i+1].markdown(f"<div class='col-label'>{c}</div>", unsafe_allow_html=True)

    for r in ROWS:
        rc = st.columns([1.0] + [3.0]*6)
        rc[0].markdown(f"<div class='row-label'>{r}</div>", unsafe_allow_html=True)

        for ci, c in enumerate(COLS):
            aid      = f"{r}_{c}"
            w_key    = f"a_in_{aid}"
            cur      = st.session_state.audience_data.get(aid, "")

            with rc[ci+1]:
                if r == 'A':
                    ro_cell("CH", "fixed")
                elif aid in FIXED_EMPTY:
                    ro_cell("공석", "fixed")
                elif not is_admin:
                    ro_cell(cur, "aud" if not cur.strip() else "aud")
                elif a_swap:
                    if st.button(cur or "—", key=f"ab_{aid}", use_container_width=True):
                        st.session_state.swap_list.append(aid)
                        if len(st.session_state.swap_list) == 2:
                            execute_swap(st.session_state.swap_list[0], st.session_state.swap_list[1])
                else:
                    if w_key not in st.session_state:
                        st.session_state[w_key] = cur
                    st.text_input("", key=w_key, placeholder=f"{r}{c}",
                                  label_visibility="collapsed", on_change=update_master_audience)

    if is_admin and a_swap and st.session_state.swap_list:
        st.info(f"선택됨: **{st.session_state.swap_list[0]}** → 교체할 자리를 선택하세요.")

# ─────────────────────────────────────────────
# TAB 3 : 출석 통계
# ─────────────────────────────────────────────
with tab3:
    st.markdown("<h4 style='margin-bottom:8px'>📊 파트별 출석 통계</h4>", unsafe_allow_html=True)
    counts = {p: 0 for p in PART_ZONES}; counts["미등록"] = 0
    for name in st.session_state.stage_data.values():
        if name.strip():
            part = member_part_map.get(name.replace(" ",""), "미등록")
            if part in counts: counts[part] += 1
            else: counts["미등록"] += 1
    total = sum(counts.values())

    sc = st.columns(len(counts))
    for i, (p, cnt) in enumerate(counts.items()):
        with sc[i]:
            st.markdown(
                f"<div class='stats-card'>"
                f"<div style='font-size:0.75rem;color:#666'>{p}</div>"
                f"<div style='font-size:1.2rem;font-weight:bold'>{cnt}명</div>"
                f"</div>", unsafe_allow_html=True)
    st.markdown(
        f"<div style='text-align:right;font-size:1.2rem;font-weight:bold;color:#d32f2f'>"
        f"총 출석: {total}명</div>", unsafe_allow_html=True)
