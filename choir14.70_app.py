import streamlit as st
import pandas as pd
import numpy as np
import io
import json
import os

# 1. 페이지 설정 및 디자인
st.set_page_config(page_title="성가대 통합 관리 시스템 v14.60", layout="wide")

st.markdown("""
    <style>
    .stTextInput { margin-bottom: 12px !important; }
    .stTextInput input { 
        font-weight: bold !important; color: #000 !important; font-size: 1.3rem !important; 
        text-align: center; height: 55px !important; border: 2.5px solid #333 !important; 
        border-radius: 8px !important; padding: 0px 2px !important; box-sizing: border-box !important;
    }
    input:placeholder-shown { background-color: #FFF9C4 !important; }
    .row-label { font-size: 2.2rem !important; font-weight: 900 !important; color: #111; text-align: center; line-height: 55px; }
    .col-label { text-align: center; font-weight: 900 !important; color: #d32f2f; font-size: 2.0rem !important; margin-bottom: 10px; }
    .cross-container { display: flex; justify-content: center; align-items: center; font-size: 55px; color: #444; height: 60px; margin-bottom: 5px; width: 100%; }
    .stButton button { font-size: 1.1rem !important; font-weight: bold !important; height: 55px !important; border-radius: 8px; }
    .stats-card { background-color: #f8f9fa; padding: 15px; border-radius: 10px; border-left: 5px solid #d32f2f; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# 2. 데이터 관리 로직
DATA_FILE = "choir_data.json"

def save_to_json():
    data = {"stage": st.session_state.stage_data, "audience": st.session_state.audience_data}
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)

def update_master_stage():
    for k in st.session_state.stage_keys:
        val = st.session_state.get(f"s_in_{k}")
        if val is not None: st.session_state.stage_data[k] = val
    save_to_json()

def update_master_audience():
    for k in st.session_state.audience_keys:
        val = st.session_state.get(f"a_in_{k}")
        if val is not None: st.session_state.audience_data[k] = val
    save_to_json()

def load_all_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                content = json.load(f)
                if isinstance(content, dict) and "stage" in content: return content
        except: return None
    return None

# 3. 명단 로드 (엑셀 파트 기준)
@st.cache_data
def load_member_part_map():
    file_name = "choir_list.xlsx"
    if os.path.exists(file_name):
        try:
            df = pd.read_excel(file_name)
            n_col = 'name' if 'name' in df.columns else '이름'
            p_col = 'part' if 'part' in df.columns else '파트'
            return {str(row[n_col]).replace(" ", "").strip(): str(row[p_col]).strip() for _, row in df.iterrows()}
        except: return {}
    return {}

member_part_map = load_member_part_map()

# 4. 구성 설정
TIER_CONFIG = [
    {"lv": 4, "left": "Tenor", "right": "Bass", "seats": 14, "solo": "TB"},
    {"lv": 3, "left": "Tenor", "right": "Bass", "seats": 13, "solo": None},
    {"lv": 2, "left": "Soprano", "right": "Alto", "seats": 14, "solo": "SA"},
    {"lv": 1, "left": "Soprano", "right": "Alto", "seats": 13, "solo": None},
]
ROWS = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K']
COLS = [30, 29, 28, 27, 26, 25]
PART_ZONES = {
    "Soprano": ['D', 'C', 'B'], 
    "Alto": ['F', 'E'], 
    "Tenor": ['H', 'G'], 
    "Bass": ['J', 'I']
}
FIXED_EMPTY_SEATS = ["B_25", "B_26"]

# 세션 초기화
if 'initialized' not in st.session_state:
    st.session_state.stage_keys = [f"T{t['lv']}_S{s}" for t in TIER_CONFIG for s in range(t['seats'])]
    st.session_state.audience_keys = [f"{r}_{c}" for r in ROWS for c in COLS]
    saved = load_all_data()
    st.session_state.stage_data = saved["stage"] if saved else {k: "" for k in st.session_state.stage_keys}
    st.session_state.audience_data = saved["audience"] if saved else {k: "" for k in st.session_state.audience_keys}
    st.session_state.swap_list = []
    st.session_state.initialized = True

def execute_swap(id1, id2):
    d1 = st.session_state.stage_data if "T" in id1 else st.session_state.audience_data
    d2 = st.session_state.stage_data if "T" in id2 else st.session_state.audience_data
    d1[id1], d2[id2] = d2[id2], d1[id1]
    st.session_state.swap_list = []
    save_to_json(); st.rerun()

# --- [1. 무대 배치도] ---
st.header("🎭 1. 무대 배치도 (Stage Layout)")

# 십자가 중앙 배치 로직 (14석 기준 중앙인 7~8번 사이 배치)
cross_cols = st.columns([1.5, 21.7, 3.1, 21.7])
with cross_cols[2]: st.markdown("<div class='cross-container'>✝️</div>", unsafe_allow_html=True)

s_swap_mode = st.toggle("🔄 무대 자리 교체 모드 ON/OFF", key="stage_swap_toggle")

for t in TIER_CONFIG:
    cols = st.columns([1.5] + [3.1] * t['seats'], gap="small")
    cols[0].markdown(f"<div class='row-label' style='font-size:1.5rem;'>{t['lv']}단</div>", unsafe_allow_html=True)
    mid = t['seats'] // 2
    for s in range(t['seats']):
        sid = f"T{t['lv']}_S{s}"
        w_key = f"s_in_{sid}"
        current_name = st.session_state.stage_data.get(sid, "")
        with cols[s+1]:
            if s_swap_mode:
                if st.button(current_name or "—", key=f"s_btn_{sid}", use_container_width=True):
                    st.session_state.swap_list.append(sid)
                    if len(st.session_state.swap_list) == 2: execute_swap(st.session_state.swap_list[0], st.session_state.swap_list[1])
            else:
                p_guide = t['left'] if s < mid else t['right']
                placeholder = "⭐" if t['solo'] and ((s < mid and s == mid-3) or (s >= mid and s == mid+2)) else p_guide[:1]
                if w_key not in st.session_state or st.session_state[w_key] != current_name:
                    st.session_state[w_key] = current_name
                st.text_input("", key=w_key, placeholder=placeholder, label_visibility="collapsed", on_change=update_master_stage)

st.divider()

# --- [2. 객석 배치표] ---
st.header("🪑 2. 객석 배치표 (Audience Layout)")

if st.button("🔄 무대 명단 입장 순서 정렬 (뒷줄 우선 + 30열 우선)", use_container_width=True):
    p_groups = {p: [] for p in PART_ZONES}
    p_groups["미등록"] = []
    
    for t in TIER_CONFIG:
        for s in range(t['seats']-1, -1, -1):
            sid = f"T{t['lv']}_S{s}"
            name = st.session_state.get(f"s_in_{sid}", st.session_state.stage_data.get(sid, "")).strip()
            if name:
                part = member_part_map.get(name.replace(" ", ""), "미등록")
                if part in p_groups: p_groups[part].append(name)
                else: p_groups["미등록"].append(name)
    
    for k in st.session_state.audience_keys:
        if not k.startswith("A_"):
            val = "공석" if k in FIXED_EMPTY_SEATS else ""
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
                if aid in FIXED_EMPTY_SEATS: continue
                if n_ptr < len(names):
                    st.session_state.audience_data[aid] = names[n_ptr]
                    st.session_state[f"a_in_{aid}"] = names[n_ptr]
                    n_ptr += 1
                else: break
    save_to_json(); st.rerun()

a_swap_mode = st.toggle("🔄 객석 자리 교체 모드 ON/OFF", key="audience_swap_toggle")
h_cols = st.columns([1.5] + [3.6]*6)
h_cols[0].write("")
for i, c_num in enumerate(COLS): h_cols[i+1].markdown(f"<div class='col-label'>{c_num}</div>", unsafe_allow_html=True)

for r_label in ROWS:
    r_cols = st.columns([1.5] + [3.6]*6)
    r_cols[0].markdown(f"<div class='row-label'>{r_label}</div>", unsafe_allow_html=True)
    for c_idx, c_label in enumerate(COLS):
        aid = f"{r_label}_{c_label}"
        w_key = f"a_in_{aid}"
        current_name = st.session_state.audience_data.get(aid, "")
        with r_cols[c_idx+1]:
            if r_label == 'A':
                st.text_input("", value="Chamber", key=f"a_fix_{aid}", disabled=True, label_visibility="collapsed")
            elif aid in FIXED_EMPTY_SEATS:
                st.text_input("", value="공석", key=f"a_empty_{aid}", disabled=True, label_visibility="collapsed")
            elif a_swap_mode:
                if st.button(current_name or "—", key=f"a_btn_{aid}", use_container_width=True):
                    st.session_state.swap_list.append(aid)
                    if len(st.session_state.swap_list) == 2: execute_swap(st.session_state.swap_list[0], st.session_state.swap_list[1])
            else:
                if w_key not in st.session_state: st.session_state[w_key] = current_name
                st.text_input("", key=w_key, placeholder=f"{r_label}{c_label}", label_visibility="collapsed", on_change=update_master_audience)

st.divider()

# --- [3. 출석 인원 통계] ---
st.header("📊 3. 파트별 출석 통계 (Attendance Stats)")

# 현재 무대에 있는 인원 집계
current_counts = {p: 0 for p in PART_ZONES}
current_counts["미등록"] = 0

for name in st.session_state.stage_data.values():
    if name.strip():
        part = member_part_map.get(name.replace(" ", ""), "미등록")
        if part in current_counts: current_counts[part] += 1
        else: current_counts["미등록"] += 1

total_count = sum(current_counts.values())

stats_cols = st.columns(len(current_counts))
for idx, (p_name, count) in enumerate(current_counts.items()):
    with stats_cols[idx]:
        st.markdown(f"""
            <div class='stats-card'>
                <div style='font-size:0.9rem; color:#666;'>{p_name}</div>
                <div style='font-size:1.8rem; font-weight:bold; color:#111;'>{count}명</div>
            </div>
        """, unsafe_allow_html=True)

st.markdown(f"""
    <div style='text-align:right; font-size:1.5rem; font-weight:bold; color:#d32f2f; margin-top:10px;'>
        총 출석 인원: {total_count}명
    </div>
""", unsafe_allow_html=True)
