import streamlit as st
import pandas as pd
import numpy as np
import io
import json
import os
import requests
import base64

# 1. 페이지 설정 및 디자인 (모바일 대응 강화)
st.set_page_config(page_title="성가대 통합 관리 시스템 v14.70", layout="wide")
st.markdown("""
<style>
/* 모바일 기기 대응을 위한 메타 태그 설정 효과 */
@media (max-width: 768px) {
.stTextInput input { font-size: 1.0rem !important; height: 45px !important; }
.row-label { font-size: 1.2rem !important; line-height: 45px !important; }
.col-label { font-size: 1.0rem !important; }
.cross-container { font-size: 40px !important; height: 45px !important; }
}
.stTextInput { margin-bottom: 8px !important; }
.stTextInput input {
font-weight: bold !important; color: #000 !important; font-size: 1.2rem !important;
text-align: center; height: 50px !important; border: 2px solid #333 !important;
border-radius: 6px !important; padding: 0px !important;
}
input:placeholder-shown { background-color: #FFF9C4 !important; }
.row-label { font-size: 1.8rem !important; font-weight: 900 !important; color: #111; text-align: center; line-height: 50px; }
.col-label { text-align: center; font-weight: 900 !important; color: #d32f2f; font-size: 1.5rem !important; margin-bottom: 5px; }
.cross-container { display: flex; justify-content: center; align-items: center; font-size: 50px; color: #444; height: 55px; margin-bottom: 5px; width: 100%; }
.stButton button { font-size: 1.0rem !important; font-weight: bold !important; height: 50px !important; border-radius: 8px; }
.stats-card { background-color: #f8f9fa; padding: 10px; border-radius: 8px; border-left: 5px solid #d32f2f; margin-bottom: 10px; }
</style>
""", unsafe_allow_html=True)

# 2. 데이터 관리 로직
DATA_FILE = "choir_data.json"

def save_to_github(json_str):
    """GitHub API를 통해 choir_data.json을 직접 커밋하여 영구 저장"""
    try:
        token = st.secrets["GITHUB_TOKEN"]
        repo  = st.secrets["GITHUB_REPO"]
        path  = st.secrets["GITHUB_FILE"]

        url = f"https://api.github.com/repos/{repo}/contents/{path}"
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github+json"
        }

        # 현재 파일의 SHA 가져오기 (업데이트 시 필수)
        res = requests.get(url, headers=headers)
        sha = res.json().get("sha", None)

        # base64 인코딩 후 커밋
        encoded = base64.b64encode(json_str.encode("utf-8")).decode("utf-8")
        payload = {
            "message": "Update choir data",
            "content": encoded,
        }
        if sha:
            payload["sha"] = sha

        result = requests.put(url, headers=headers, json=payload)
        return result.status_code in (200, 201)

    except Exception as e:
        return False

def save_to_json():
    data = {"stage": st.session_state.stage_data, "audience": st.session_state.audience_data}
    json_str = json.dumps(data, ensure_ascii=False, indent=2)

    # GitHub에 저장 시도
    github_ok = save_to_github(json_str)

    # GitHub 저장 실패 시 로컬 파일로 fallback
    if not github_ok:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            f.write(json_str)

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
    # GitHub에서 최신 데이터 로드 시도
    try:
        token = st.secrets["GITHUB_TOKEN"]
        repo  = st.secrets["GITHUB_REPO"]
        path  = st.secrets["GITHUB_FILE"]

        url = f"https://api.github.com/repos/{repo}/contents/{path}"
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github+json"
        }
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            content = base64.b64decode(res.json()["content"]).decode("utf-8")
            data = json.loads(content)
            if isinstance(data, dict) and "stage" in data:
                return data
    except Exception:
        pass

    # GitHub 실패 시 로컬 파일에서 로드
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                content = json.load(f)
            if isinstance(content, dict) and "stage" in content:
                return content
        except:
            return None

    return None

MEMBER_FILE = "choir_list.xlsx"

@st.cache_data
def load_member_part_map(file_mtime=None):
    # file_mtime: 엑셀 파일 수정 시각. 파일이 바뀌면 캐시가 자동으로 새로 읽힘
    file_name = MEMBER_FILE
    if os.path.exists(file_name):
        try:
            df = pd.read_excel(file_name)
            n_col = 'name' if 'name' in df.columns else '이름'
            p_col = 'part' if 'part' in df.columns else '파트'
            return {str(row[n_col]).replace(" ", "").strip(): str(row[p_col]).strip() for _, row in df.iterrows()}
        except: return {}
    return {}

member_part_map = load_member_part_map(os.path.getmtime(MEMBER_FILE) if os.path.exists(MEMBER_FILE) else None)

# 4. 구성 설정
TIER_CONFIG = [
    {"lv": 4, "left": "Tenor", "right": "Bass", "seats": 14, "solo": "TB"},
    {"lv": 3, "left": "Tenor", "right": "Bass", "seats": 13, "solo": None},
    {"lv": 2, "left": "Soprano", "right": "Alto", "seats": 14, "solo": "SA"},
    {"lv": 1, "left": "Soprano", "right": "Alto", "seats": 13, "solo": None},
]
ROWS = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L']
COLS = [30, 29, 28, 27, 26, 25]
# 파트 순서 (객석 앞줄부터). 줄 배정은 정렬할 때 인원수에 맞춰 자동으로 계산됨
PART_ZONES = {"Soprano": [], "Alto": [], "Tenor": [], "Bass": []}
MIN_VISIBLE_ROWS = 6  # 객석표에 최소한 보여줄 줄 수 (A~F)
FIXED_EMPTY_SEATS = ["B_25", "B_26"]

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
st.header("🎭 1. 무대 배치도")
cross_cols = st.columns([1.5, 21.7, 3.1, 21.7])
with cross_cols[2]: st.markdown("<div class='cross-container'>✝️</div>", unsafe_allow_html=True)

s_swap_mode = st.toggle("🔄 무대 자리 교체 모드", key="stage_swap_toggle")

for t in TIER_CONFIG:
    cols = st.columns([1.5] + [3.1] * t['seats'], gap="small")
    cols[0].markdown(f"<div class='row-label' style='font-size:1.2rem;'>{t['lv']}단</div>", unsafe_allow_html=True)
    mid = t['seats'] // 2
    for s in range(t['seats']):
        sid = f"T{t['lv']}_S{s}"; w_key = f"s_in_{sid}"
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
st.header("🪑 2. 객석 배치표")

if st.button("🔄 무대 명단 입장 순서 정렬 (뒷줄 우선)", use_container_width=True):
    p_groups = {p: [] for p in PART_ZONES}; p_groups["미등록"] = []
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
    # 파트별로 필요한 줄 수만큼만 B열부터 빈 줄 없이 이어서 배정
    #  - 각 파트 안에서는 뒷줄부터 채움 (무대 뒷단 → 객석 뒷줄)
    #  - 모든 줄에 최소 1명이 앉도록 인원을 나눔 → 완전히 빈 줄이 생기지 않음
    #  - 명단(엑셀)에 없는 '미등록' 대원은 마지막 파트 다음 줄에 배치
    def row_seats(r):
        return [f"{r}_{c}" for c in COLS if f"{r}_{c}" not in FIXED_EMPTY_SEATS]
    free_rows = ROWS[1:]  # A열은 Chamber/CH 고정
    r_ptr = 0
    groups = [(p, p_groups[p]) for p in PART_ZONES] + [("미등록", p_groups["미등록"])]
    not_seated = []
    for p_name, names in groups:
        if not names: continue
        rows, cap = [], 0
        while cap < len(names) and r_ptr < len(free_rows):
            rows.append(free_rows[r_ptr]); cap += len(row_seats(free_rows[r_ptr])); r_ptr += 1
        rows = rows[::-1]  # 뒷줄부터
        remaining = len(names); idx = 0
        for i, r in enumerate(rows):
            seats = row_seats(r)
            cnt = min(len(seats), remaining - (len(rows) - i - 1))
            for aid in seats[:cnt]:
                st.session_state.audience_data[aid] = names[idx]
                st.session_state[f"a_in_{aid}"] = names[idx]
                idx += 1
            remaining -= cnt
        not_seated += names[idx:]
    st.session_state.sort_warnings = []
    if p_groups["미등록"]:
        st.session_state.sort_warnings.append(
            "엑셀 명단(choir_list.xlsx)에 없는 이름이라 맨 뒤쪽 줄에 따로 배치했습니다: "
            + ", ".join(p_groups["미등록"]) + " — 이름 철자를 확인하거나 엑셀에 추가해 주세요.")
    if not_seated:
        st.session_state.sort_warnings.append(
            "객석 자리가 모자라 넣지 못한 대원: " + ", ".join(not_seated))
    save_to_json(); st.rerun()

for msg in st.session_state.get("sort_warnings", []):
    st.warning("⚠️ " + msg)

a_swap_mode = st.toggle("🔄 객석 자리 교체 모드", key="audience_swap_toggle")

used_rows = [r for r in ROWS if any(
    st.session_state.audience_data.get(f"{r}_{c}", "").strip() not in ("", "공석") for c in COLS)]
last_idx = max([ROWS.index(r) for r in used_rows] + [MIN_VISIBLE_ROWS - 1])
VISIBLE_ROWS = ROWS[:last_idx + 1]

h_cols = st.columns([1.5] + [3.6]*6)
for i, c_num in enumerate(COLS): h_cols[i+1].markdown(f"<div class='col-label'>{c_num}</div>", unsafe_allow_html=True)

for r_label in VISIBLE_ROWS:
    r_cols = st.columns([1.5] + [3.6]*6)
    r_cols[0].markdown(f"<div class='row-label' style='font-size:1.2rem;'>{r_label}</div>", unsafe_allow_html=True)
    for c_idx, c_label in enumerate(COLS):
        aid = f"{r_label}_{c_label}"; w_key = f"a_in_{aid}"
        current_name = st.session_state.audience_data.get(aid, "")
        with r_cols[c_idx+1]:
            if r_label == 'A': st.text_input("", value="CH", key=f"a_fix_{aid}", disabled=True, label_visibility="collapsed")
            elif aid in FIXED_EMPTY_SEATS: st.text_input("", value="공석", key=f"a_empty_{aid}", disabled=True, label_visibility="collapsed")
            elif a_swap_mode:
                if st.button(current_name or "—", key=f"a_btn_{aid}", use_container_width=True):
                    st.session_state.swap_list.append(aid)
                    if len(st.session_state.swap_list) == 2: execute_swap(st.session_state.swap_list[0], st.session_state.swap_list[1])
            else:
                if w_key not in st.session_state: st.session_state[w_key] = current_name
                st.text_input("", key=w_key, placeholder=f"{r_label}{c_label}", label_visibility="collapsed", on_change=update_master_audience)

st.divider()

# --- [3. 출석 인원 통계] ---
st.header("📊 3. 파트별 출석 통계")
current_counts = {p: 0 for p in PART_ZONES}; current_counts["미등록"] = 0
for name in st.session_state.stage_data.values():
    if name.strip():
        part = member_part_map.get(name.replace(" ", ""), "미등록")
        if part in current_counts: current_counts[part] += 1
        else: current_counts["미등록"] += 1
total_count = sum(current_counts.values())
stats_cols = st.columns(len(current_counts))
for idx, (p_name, count) in enumerate(current_counts.items()):
    with stats_cols[idx]:
        st.markdown(f"<div class='stats-card'><div style='font-size:0.8rem; color:#666;'>{p_name}</div><div style='font-size:1.3rem; font-weight:bold; color:#111;'>{count}명</div></div>", unsafe_allow_html=True)
st.markdown(f"<div style='text-align:right; font-size:1.3rem; font-weight:bold; color:#d32f2f;'>총 출석 인원: {total_count}명</div>", unsafe_allow_html=True)
