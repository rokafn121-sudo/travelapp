import streamlit as st
import pandas as pd
import plotly.express as px
import extra_streamlit_components as stx

# --- Streamlit Cloud Hot-Reload Cache Fix ---
import sys
if "utils" in sys.modules:
    import importlib
    importlib.reload(sys.modules["utils"])

from utils import load_data, save_data, calculate_metrics, get_exchange_rate, load_folders, save_folders, load_users, register_user, verify_user, approve_user, delete_user, load_expense_requests, save_expense_requests, load_itineraries, save_itinerary_event, delete_itinerary_event
from datetime import datetime
import time
import uuid
import os
import requests
import re

# 페이지 설정
st.set_page_config(page_title="영늘 트립 트래커 🎀", page_icon="✈️", layout="wide")

# Image Paths
# Local or deployed relative path
PROFILE_IMAGE_PATH = "profile.png"

# 초기화
if 'folders' not in st.session_state:
    st.session_state.folders = load_folders()

if 'current_trip_id' not in st.session_state:
    st.session_state.current_trip_id = None

if 'df_expenses' not in st.session_state:
    st.session_state.df_expenses = pd.DataFrame()

if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = False

# CSS 스타일 적용 (Premium Blue Theme & Pretendard Font)
is_dark = st.session_state.get('dark_mode', False)

if is_dark:
    theme_css = """
    :root {
        --bg-color: #0f172a;
        --sidebar-bg: #1e293b;
        --card-bg: #1e293b;
        --card-border: #334155;
        --text-main: #f8fafc;
        --text-sub: #94a3b8;
        --primary: #3b82f6;
        --primary-hover: #60a5fa;
        --input-bg: #0f172a;
        --danger: #ef4444;
        --success: #10b981;
    }
    """
else:
    theme_css = """
    :root {
        --bg-color: #f8fafc;
        --sidebar-bg: #f1f5f9;
        --card-bg: #ffffff;
        --card-border: #e2e8f0;
        --text-main: #0f172a;
        --text-sub: #64748b;
        --primary: #2563eb;
        --primary-hover: #1d4ed8;
        --input-bg: #ffffff;
        --danger: #ef4444;
        --success: #10b981;
    }
    """

st.markdown(f"""
    <style>
    @import url("https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css");
    
    {theme_css}
    
    /* Global Font & Base */
    html, body, [class*="css"], .stApp {{
        font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, sans-serif !important;
        background-color: var(--bg-color) !important;
        color: var(--text-main) !important;
        letter-spacing: -0.02em;
    }}
    
    /* Typography Overrides (Safer) */
    h1, h2, h3, h4, h5, h6, p, label, .streamlit-expanderHeader, div[data-testid="stMarkdownContainer"] > p {{
        color: var(--text-main) !important;
    }}
    
    /* Sidebar */
    [data-testid="stSidebar"], [data-testid="stSidebar"] > div:first-child, section[data-testid="stSidebar"] {{
        background-color: var(--sidebar-bg) !important;
        border-right: 1px solid var(--card-border) !important;
    }}
    
    /* Inputs & Forms - Text Inputs */
    .stTextInput input, .stNumberInput input, .stDateInput input {{
        background-color: var(--input-bg) !important;
        color: var(--text-main) !important;
        border-radius: 12px !important;
        border: 1px solid var(--card-border) !important;
        padding: 10px 14px !important;
        font-weight: 500;
        transition: all 0.2s ease;
    }}
    
    /* Selectbox specific tweaks */
    div[data-baseweb="select"] > div {{
        background-color: var(--input-bg) !important;
        color: var(--text-main) !important;
        border-radius: 12px !important;
        border: 1px solid var(--card-border) !important;
        transition: all 0.2s ease;
    }}
    
    /* Selectbox Inner Text Display Fix */
    div[data-baseweb="select"] span, div[data-baseweb="select"] div {{
        color: var(--text-main) !important;
    }}
    
    /* Selectbox Dropdown Fix */
    [data-baseweb="popover"], [data-baseweb="menu"], ul[role="listbox"] {{
        background-color: var(--card-bg) !important;
    }}
    li[role="option"] {{
        background-color: transparent !important;
        color: var(--text-main) !important;
    }}
    li[role="option"]:hover, li[role="option"][aria-selected="true"] {{
        background-color: var(--primary) !important;
        color: white !important;
    }}
    
    .stTextInput input:focus, .stNumberInput input:focus, .stSelectbox select:focus, div[data-baseweb="select"]:focus-within {{
        border-color: var(--primary) !important;
        box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.15) !important;
    }}
    
    /* Buttons (Premium Style) */
    .stButton>button {{
        background: linear-gradient(135deg, var(--primary) 0%, var(--primary-hover) 100%) !important;
        color: #ffffff !important;
        border-radius: 12px !important;
        border: none !important;
        padding: 14px 24px !important;
        font-weight: 600 !important;
        font-size: 16px !important;
        width: 100%;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }}
    .stButton>button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(37, 99, 235, 0.3) !important;
    }}
    .stButton>button:active {{
        transform: translateY(0);
        box-shadow: 0 2px 8px rgba(37, 99, 235, 0.2) !important;
    }}
    
    /* Secondary Button (Outline) */
    button[kind="secondary"] {{
        background: transparent !important;
        color: var(--primary) !important;
        border: 1.5px solid var(--primary) !important;
        box-shadow: none !important;
    }}
    button[kind="secondary"]:hover {{
        background: var(--sidebar-bg) !important;
        box-shadow: none !important;
        transform: translateY(-1px);
    }}
    
    /* Override Streamlit Main Container Padding for Mobile */
    .block-container {{
        padding-top: 2rem !important;
        padding-bottom: 5rem !important;
        padding-left: 1.25rem !important;
        padding-right: 1.25rem !important;
        max-width: 800px;
    }}
    
    /* Premium Cards */
    .metric-card, .trip-card, .streamlit-expanderHeader, [data-testid="stExpanderDetails"] {{
        background-color: var(--card-bg) !important;
        border: 1px solid var(--card-border) !important;
        border-radius: 16px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.03);
        transition: all 0.3s ease;
    }}
    .streamlit-expanderHeader {{
        padding: 16px;
        margin-bottom: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.02);
        font-weight: 600;
    }}
    [data-testid="stExpanderDetails"] {{
        border-top: none !important;
        border-top-left-radius: 0;
        border-top-right-radius: 0;
    }}
    .metric-card {{
        padding: 20px;
        text-align: center;
        margin-bottom: 16px;
    }}
    .trip-card {{ margin-bottom: 16px; padding: 24px; }}
    
    .metric-card:hover, .trip-card:hover {{
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.06);
        border-color: var(--primary) !important;
    }}
    
    /* History List Items */
    .history-item {{
        background: var(--card-bg) !important;
        padding: 16px;
        border-radius: 16px;
        margin-bottom: 12px;
        border: 1px solid var(--card-border) !important;
        box-shadow: 0 2px 12px rgba(0,0,0,0.02);
        display: flex;
        justify-content: space-between;
        align-items: center;
        transition: all 0.2s ease;
    }}
    .history-item:hover {{
        box-shadow: 0 4px 16px rgba(0,0,0,0.06);
        border-color: var(--primary) !important;
    }}
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 16px;
        border-bottom: 2px solid var(--card-border);
    }}
    .stTabs [data-baseweb="tab"] {{
        height: 54px;
        padding: 0 16px;
        font-weight: 600;
        color: var(--text-sub) !important;
        background-color: transparent !important;
        border-radius: 0 !important;
    }}
    .stTabs [aria-selected="true"] {{
        color: var(--primary) !important;
        border-bottom: 3px solid var(--primary) !important;
    }}
    
    /* Hide Default Footer */
    footer {{visibility: hidden;}}
    
    /* Custom Profile Image Style */
    .profile-img {{
        display: block;
        margin-left: auto;
        margin-right: auto;
        width: 130px;
        height: 130px;
        border-radius: 50%;
        object-fit: cover;
        box-shadow: 0 8px 24px rgba(0,0,0,0.12);
        margin-bottom: 24px;
        border: 4px solid var(--card-bg);
    }}
    
    /* Mobile-first Headers */
    h1, h2, h3 {{
        font-weight: 700 !important;
        letter-spacing: -0.03em;
        word-break: keep-all; 
    }}
    @media (max-width: 768px) {{
        h1 {{ font-size: 1.4rem !important; }}
        h2 {{ font-size: 1.2rem !important; }}
        h3 {{ font-size: 1.1rem !important; }}
    }}
    </style>
""", unsafe_allow_html=True)

# 세션 상태: 사용자 인증
if 'user_session' not in st.session_state:
    st.session_state.user_session = None

# Cookie Manager 초기화
cookie_manager = stx.CookieManager(key="cookie_manager")

if 'explicit_logout' not in st.session_state:
    st.session_state.explicit_logout = False

# Perform pending logout cookie deletions
if st.session_state.get('do_logout', False):
    try:
        cookie_manager.delete("saved_user", key="del_u")
    except Exception:
        pass
    try:
        cookie_manager.delete("saved_role", key="del_r")
    except Exception:
        pass
    st.session_state.do_logout = False

# --- 자동 로그인 체크 로직 ---
if st.session_state.user_session is None:
    if st.session_state.explicit_logout:
        # Reset the flag after one bypass to allow future normal logins
        pass # Wait for user to login manually. 
    else:
        saved_user = cookie_manager.get(cookie="saved_user")
        saved_role = cookie_manager.get(cookie="saved_role")
        if saved_user and saved_role:
            # Check if user is still valid/approved in latest DB
            users = load_users()
            if saved_user in users and users[saved_user]['approved']:
                st.session_state.user_session = {"username": saved_user, "role": saved_role}
                st.rerun()

@st.cache_data(ttl=3600)
def get_auto_currency():
    try:
        res = requests.get('http://ip-api.com/json/', timeout=3).json()
        cc = res.get("countryCode", "KR")
        if cc == "US": return 1 # USD
        elif cc in ["FR", "DE", "IT", "ES", "NL", "BE", "AT", "IE", "FI", "PT"]: return 2 # EUR
        elif cc == "JP": return 3 # JPY
        return 0 # KRW
    except:
        return 0

# --- 메인 앱 로직 (로그인 후 실행됨) ---
def main_app():
    user = st.session_state.user_session
    username = user['username']
    role = user['role']

    # --- 사이드바 ---
    try:
        if os.path.exists(PROFILE_IMAGE_PATH):
            st.sidebar.image(PROFILE_IMAGE_PATH, width=150)
        else:
            st.sidebar.warning("프로필 이미지를 찾을 수 없습니다.")
    except Exception as e:
        st.sidebar.error(f"이미지 로드 오류: {e}")

    st.sidebar.write(f"### 👋 반가워요, {username}님!")
    
    if st.sidebar.button("로그아웃 (Logout)", type="secondary"):
        st.session_state.do_logout = True
        st.session_state.user_session = None
        st.session_state.current_trip_id = None
        st.session_state.explicit_logout = True
        st.rerun()

    st.sidebar.markdown("---")
    
    # 북마크/다크 모드 설정
    dark_toggle = st.sidebar.toggle("🌙 다크 모드", value=st.session_state.dark_mode)
    if dark_toggle != st.session_state.dark_mode:
        st.session_state.dark_mode = dark_toggle
        st.rerun()
    
    st.sidebar.markdown("---")
    
    if st.session_state.current_trip_id:
        current_trip = st.session_state.folders.get(st.session_state.current_trip_id)
        if current_trip:
            st.sidebar.info(f"📍 현재 여행:\n**{current_trip['name']}**")
            if st.sidebar.button("⬅️ 여행 목록으로", type="secondary"):
                st.session_state.current_trip_id = None
                st.session_state.df_expenses = pd.DataFrame()
                st.rerun()
        else:
            st.session_state.current_trip_id = None
            st.rerun()
    
    st.sidebar.markdown("---")
    st.sidebar.caption("Designed by 영현 ✨")

    # --- 메인 로직 ---

    if st.session_state.current_trip_id is None:
        # Trip Selection Dashboard
        st.title("나의 여행 목록 ✈️")
        st.caption("소중한 추억이 담긴 여행을 선택해주세요.")

        # Tab navigation for cleaner mobile view
        if role == 'admin':
            tabs = st.tabs(["📂 내 여행", "⚙️ 관리자"])
        else:
            tabs = st.tabs(["📂 내 여행"])

        with tabs[0]: # 내 여행 탭
            trip_options = {v['name']: k for k, v in st.session_state.folders.items()}
            
            if not trip_options:
                st.info("아직 등록된 여행이 없어요. 😢")
            else:
                for name, tid in trip_options.items():
                    trip_info = st.session_state.folders[tid]
                    date_str = ""
                    if "start_date" in trip_info and "end_date" in trip_info:
                        date_str = f"<p style='margin: 0; font-size: 13px; color: var(--text-sub);'>🗓️ {trip_info['start_date']} ~ {trip_info['end_date']}</p>"

                    # Card-like container for each trip
                    with st.container():
                        st.markdown(f"""
                        <div class="trip-card">
                            <h3 style="margin: 0 0 8px 0; color: var(--text-main);">🏝 {name}</h3>
                            {date_str}
                        </div>
                        """, unsafe_allow_html=True)
                        
                        col_pw, col_btn = st.columns([2, 1])
                        with col_pw:
                            pw_input = st.text_input(f"비밀번호", type="password", key=f"pw_{tid}", placeholder="****", label_visibility="collapsed")
                        with col_btn:
                            if st.button("입장", key=f"btn_{tid}"):
                                trip_data = st.session_state.folders[tid]
                                if pw_input == trip_data['password']:
                                    st.session_state.current_trip_id = tid
                                    st.session_state.df_expenses = load_data(tid)
                                    st.toast(f"'{name}' 여행을 시작합니다! 🚀")
                                    st.rerun()
                                else:
                                    st.error("비밀번호 확인 필요")

        if role == 'admin':
            with tabs[1]: # 관리자 탭
                st.subheader("새 여행 만들기")
                with st.form("create_trip_form"):
                    new_trip_name = st.text_input("여행 이름 (예: 다낭 여행)")
                    # Trip duration input
                    new_duration = st.date_input("여행 기간", value=(datetime.now(), datetime.now() + pd.Timedelta(days=3)))
                    new_trip_pw = st.text_input("비밀번호 설정")
                    new_trip_budget = st.number_input("총 예산 (KRW)", min_value=0, value=1000000, step=10000)
                    
                    if st.form_submit_button("여행 생성하기 ✨"):
                        if new_trip_name and new_trip_pw:
                            if isinstance(new_duration, tuple) and len(new_duration) == 2:
                                s_date, e_date = new_duration
                            else:
                                s_date = e_date = new_duration if new_duration else datetime.now()
                            
                            new_id = str(uuid.uuid4())
                            st.session_state.folders[new_id] = {
                                "name": new_trip_name,
                                "password": new_trip_pw,
                                "budget": int(new_trip_budget),
                                "start_date": s_date.strftime("%Y-%m-%d"),
                                "end_date": e_date.strftime("%Y-%m-%d"),
                                "created_at": datetime.now().strftime("%Y-%m-%d")
                            }
                            save_folders(st.session_state.folders)
                            st.success("새로운 여행이 추가되었습니다!")
                            st.rerun()
                        else:
                            st.warning("이름과 비밀번호는 필수입니다.")
                
                st.divider()
                st.subheader("방 (여행) 관리")
                for tid, tdata in list(st.session_state.folders.items()):
                    with st.expander(f"🏝 {tdata['name']} (PW: {tdata.get('password', 'N/A')})"):
                        new_name = st.text_input("이름", value=tdata['name'], key=f"edit_name_{tid}")
                        new_pw = st.text_input("비밀번호", value=tdata.get('password', ''), key=f"edit_pw_{tid}")
                        new_budget = st.number_input("예산", value=int(tdata.get('budget', 0)), key=f"edit_budget_{tid}")
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("수정 저장", key=f"save_{tid}", type="secondary"):
                                st.session_state.folders[tid].update({"name": new_name, "password": new_pw, "budget": new_budget})
                                save_folders(st.session_state.folders)
                                st.success("수정 완료!")
                                st.rerun()
                        with col2:
                            if st.button("🔴 위 여행 삭제하기", key=f"del_{tid}", use_container_width=True):
                                del st.session_state.folders[tid]
                                save_folders(st.session_state.folders)
                                st.success("여행이 삭제되었습니다.")
                                st.rerun()

                st.divider()
                st.subheader("사용자 관리")
                users = load_users()
                pending_users = [u for u, data in users.items() if not data['approved']]
                approved_users = [u for u, data in users.items() if data['approved']]
                
                if pending_users:
                    st.write("**승인 대기 중**")
                    for u in pending_users:
                        c1, c2 = st.columns([3, 1])
                        c1.info(f"👤 {u}")
                        if c2.button("승인", key=f"approve_{u}"):
                            approve_user(u)
                            st.rerun()
                
                if approved_users:
                    st.write("**승인된 활성 사용자**")
                    for u in approved_users:
                        if u == 'admin': continue
                        c1, c2 = st.columns([3, 1])
                        c1.success(f"👤 {u} ({users[u].get('role', 'user')})")
                        if c2.button("탈퇴(삭제)", key=f"delete_{u}"):
                            delete_user(u)
                            st.rerun()

                st.divider()
                st.subheader("지출 변경/삭제 요청 관리")
                requests = load_expense_requests()
                if not requests:
                    st.caption("대기 중인 요청이 없습니다.")
                else:
                    for idx, req in enumerate(requests):
                        req_type_str = "📝 수정" if req['type'] == 'edit' else "🗑️ 삭제"
                        with st.expander(f"{req_type_str} 요청: {req['item_name']} (요청자: {req['request_user']})"):
                            st.write(f"이유: {req.get('reason', '없음')}")
                            if req['type'] == 'edit':
                                st.write("변경 내용:", req['new_data'])
                            
                            colA, colB = st.columns(2)
                            with colA:
                                if st.button("✅ 승인", key=f"req_app_{idx}"):
                                    df = load_data(req['trip_id'])
                                    if req['type'] == 'delete':
                                        df = df[df['ID'] != req['expense_id']]
                                    elif req['type'] == 'edit':
                                        mask = df['ID'] == req['expense_id']
                                        if not df[mask].empty:
                                            for k, v in req['new_data'].items():
                                                df.loc[mask, k] = v
                                    save_data(df, req['trip_id'])
                                    
                                    # Refresh if current trip
                                    if st.session_state.current_trip_id == req['trip_id']:
                                        st.session_state.df_expenses = load_data(req['trip_id'])

                                    requests.pop(idx)
                                    save_expense_requests(requests)
                                    st.success("요청이 승인되어 데이터에 반영되었습니다!")
                                    st.rerun()
                            with colB:
                                if st.button("❌ 반려", key=f"req_rej_{idx}"):
                                    requests.pop(idx)
                                    save_expense_requests(requests)
                                    st.warning("요청이 반려(삭제)되었습니다.")
                                    st.rerun()

    else:
        # Trip Dashboard
        trip_id = st.session_state.current_trip_id
        trip_data = st.session_state.folders[trip_id]
        
        # Header with Exit Button
        col_head, col_exit = st.columns([4, 1])
        with col_head:
            st.title(trip_data['name'])
            if "start_date" in trip_data and "end_date" in trip_data:
                st.caption(f"🗓️ {trip_data['start_date']} ~ {trip_data['end_date']}")
        with col_exit:
            if st.button("⬅️ 뒤로", use_container_width=True, type="secondary"):
                st.session_state.current_trip_id = None
                st.session_state.df_expenses = pd.DataFrame()
                st.rerun()
            
        # Metrics
        budget = trip_data['budget']
        total_spent, remaining = calculate_metrics(st.session_state.df_expenses, budget)
        
        # Mobile Metric Grid
        m1, m2 = st.columns(2)
        with m1:
            st.markdown(f"""
            <div class="metric-card">
                <div style="font-size: 12px; color: var(--text-sub);">지출 (Spent)</div>
                <div style="font-size: 20px; font-weight: bold; color: #ff4d4f;">{total_spent:,.0f}</div>
                <div style="font-size: 10px; color: var(--text-sub);">{total_spent/budget*100:.1f}%</div>
            </div>
            """, unsafe_allow_html=True)
        with m2:
            st.markdown(f"""
            <div class="metric-card">
                <div style="font-size: 12px; color: var(--text-sub);">잔액 (Left)</div>
                <div style="font-size: 20px; font-weight: bold; color: {'#52c41a' if remaining > 0 else '#ff4d4f'};">{remaining:,.0f}</div>
                 <div style="font-size: 10px; color: var(--text-sub);">{remaining/budget*100:.1f}%</div>
            </div>
            """, unsafe_allow_html=True)

        st.progress(min(total_spent / budget if budget > 0 else 0, 1.0))

        # ⚡ 빠른 지출 추가 (Quick Add)
        with st.expander("⚡ 빠른 지출 추가 (Quick Add)", expanded=False):
            with st.form("quick_add_form", clear_on_submit=True):
                q_col1, q_col2 = st.columns(2)
                with q_col1:
                    qa_amount = st.number_input("지불한 결제금액 (KRW 환산)", min_value=0.0, step=1000.0)
                with q_col2:
                    qa_item = st.text_input("간단한 지출 내용")
                
                if st.form_submit_button("🚀 간편 등록") and qa_item and qa_amount > 0:
                    exp_id = str(uuid.uuid4())
                    new_data = pd.DataFrame({
                        "ID": [exp_id],
                        "Date": [pd.to_datetime(datetime.now().strftime("%Y-%m-%d"))],
                        "Category": ["기타 (Others)"],
                        "Item": [qa_item],
                        "Amount": [qa_amount],
                        "Currency": ["KRW"],
                        "Original Amount": [qa_amount],
                        "Exchange Rate": [1.0],
                        "User": [username],
                        "image_path": [None]
                    })
                    st.session_state.df_expenses = pd.concat([st.session_state.df_expenses, new_data], ignore_index=True)
                    save_data(st.session_state.df_expenses, trip_id)
                    st.success("간편 등록이 완료되었습니다!")
                    import time; time.sleep(0.5); st.rerun()

        # Main Actions
        # Category Alerts
        cat_budgets = trip_data.get('category_budgets', {})
        if cat_budgets and not st.session_state.df_expenses.empty:
            cat_totals = st.session_state.df_expenses.groupby('Category')['Amount'].sum()
            for cat, limit in cat_budgets.items():
                if cat in cat_totals and cat_totals[cat] > limit:
                    st.error(f"⚠️ **예산 초과 경고:** '{cat}' 카테고리 지출({cat_totals[cat]:,.0f}원)이 설정된 예산({limit:,.0f}원)을 초과했습니다!")

        tab_add, tab_history, tab_stats, tab_itinerary = st.tabs(["➕ 지출 추가", "📋 내역", "📊 통계", "📅 일정 관리"])

        with tab_add:
            with st.container():
                st.markdown("### 💸 지출 기록하기")
                col_date, col_curr = st.columns(2)
                with col_date:
                    date = st.date_input("날짜", datetime.now(), label_visibility="collapsed")
                with col_curr:
                    currency = st.selectbox("통화", ["KRW", "USD", "EUR", "JPY"], index=get_auto_currency(), label_visibility="collapsed")
                
                # Fetch rate quietly
                current_rate = get_exchange_rate(currency, date)
                
                category = st.selectbox("카테고리", ["식비 (Food)", "교통 (Transport)", "숙박 (Accommodation)", "쇼핑 (Shopping)", "관광 (Activities)", "기타 (Others)"])
                item = st.text_input("무엇을 샀나요?", placeholder="예: 맛있는 라멘")
                
                # Photo upload
                receipt_image = st.file_uploader("영수증 / 지출 사진 첨부 📸", type=["jpg", "jpeg", "png"])

                c1, c2 = st.columns(2)
                with c1:
                    amount_origin = st.number_input(f"금액 ({currency})", min_value=0.0, format="%.2f")
                with c2:
                    manual_rate = st.number_input("환율", value=float(current_rate), format="%.2f")

                if st.button("저장하기 (Save)", use_container_width=True):
                    final_krw = amount_origin * manual_rate
                    exp_id = str(uuid.uuid4())
                    
                    # Save image if exists
                    image_path_saved = None
                    if receipt_image is not None:
                        ext = os.path.splitext(receipt_image.name)[1]
                        if not ext: ext = ".jpg"
                        img_filename = f"{exp_id}{ext}"
                        save_path = os.path.join("data", "uploads", img_filename)
                        # Ensure the directory exists
                        os.makedirs(os.path.dirname(save_path), exist_ok=True)
                        with open(save_path, "wb") as f:
                            f.write(receipt_image.getbuffer())
                        image_path_saved = save_path

                    new_data = pd.DataFrame({
                        "ID": [exp_id],
                        "Date": [pd.to_datetime(date)],
                        "Category": [category],
                        "Item": [item],
                        "Amount": [final_krw],
                        "Currency": [currency],
                        "Original Amount": [amount_origin],
                        "Exchange Rate": [manual_rate],
                        "User": [username],
                        "image_path": [image_path_saved]
                    })
                    st.session_state.df_expenses = pd.concat([st.session_state.df_expenses, new_data], ignore_index=True)
                    save_data(st.session_state.df_expenses, trip_id)
                    st.success("🎉 지출이 정상적으로 저장되었습니다!")
                    # Use a short sleep or directly rerun depending on UX preference
                    import time
                    time.sleep(1.0)
                    st.rerun()

        with tab_history:
            if not st.session_state.df_expenses.empty:
                display_df = st.session_state.df_expenses.copy()
                display_df = display_df.sort_values(by="Date", ascending=False)
                
                for idx, row in display_df.iterrows():
                    emoji = "🍽️"
                    if "교통" in row['Category']: emoji = "🚕"
                    elif "숙박" in row['Category']: emoji = "🏨"
                    elif "쇼핑" in row['Category']: emoji = "🛍️"
                    elif "관광" in row['Category']: emoji = "🎡"
                    
                    icon_has_img = "🖼️ " if ('image_path' in row and pd.notna(row['image_path']) and row['image_path']) else ""
                    st.markdown(f"""
                    <div class="history-item">
                        <div>
                            <div style="font-size: 16px; font-weight: 700; color: var(--text-main);">{emoji} {icon_has_img}{row['Item']}</div>
                            <div style="font-size: 13px; color: var(--text-sub); margin-top: 4px;">{row['Date'].strftime('%m.%d')} · {row['Category']} · 👤 {row.get('User', '알수없음')}</div>
                        </div>
                        <div style="text-align: right;">
                            <div style="font-size: 17px; font-weight: 800; color: var(--text-main);">-{row['Amount']:,.0f} 원</div>
                            <div style="font-size: 12px; color: var(--text-sub); margin-top: 2px;">{row['Original Amount']:,.2f} {row['Currency']}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if icon_has_img:
                        with st.expander(f"📷 {row['Item']} 사진 보기"):
                            img_p = row['image_path']
                            if os.path.exists(img_p):
                                st.image(img_p, use_container_width=True)
                            else:
                                st.warning("이미지 파일을 찾을 수 없습니다.")

                    with st.expander("👉 밀어서 메뉴 보기 (수정/삭제)"):
                        if role == 'admin':
                            c_amt, c_del = st.columns([3, 1])
                            with c_amt:
                                new_item = st.text_input("새 항목명", value=row['Item'], key=f"adm_i_{row['ID']}")
                                new_amt = st.number_input("새 결제금액(원화)", value=float(row['Amount']), key=f"adm_a_{row['ID']}")
                            with c_del:
                                if st.button("🗑️ 즉시 삭제", key=f"adm_del_{row['ID']}", type="primary"):
                                    st.session_state.df_expenses = st.session_state.df_expenses[st.session_state.df_expenses['ID'] != row['ID']]
                                    save_data(st.session_state.df_expenses, trip_id)
                                    st.success("삭제 완료!")
                                    import time; time.sleep(0.5)
                                    st.rerun()
                                    
                            if st.button("✏️ 즉시 수정 저장", key=f"adm_edit_{row['ID']}"):
                                mask = st.session_state.df_expenses['ID'] == row['ID']
                                st.session_state.df_expenses.loc[mask, 'Item'] = new_item
                                st.session_state.df_expenses.loc[mask, 'Amount'] = new_amt
                                save_data(st.session_state.df_expenses, trip_id)
                                st.success("수정 완료!")
                                import time; time.sleep(0.5)
                                st.rerun()
                        else:
                            st.caption("변경 또는 삭제는 관리자 승인이 필요합니다.")
                            with st.form(key=f"req_f_{row['ID']}"):
                                new_item = st.text_input("수정할 항목명", value=row['Item'])
                                new_amt = st.number_input("수정할 금액(원화)", value=float(row['Amount']))
                                reason = st.text_input("요청 사유", placeholder="예: 금액 잘못 입력")
                                if st.form_submit_button("📝 변경 요청 전송"):
                                    reqs = load_expense_requests()
                                    reqs.append({
                                        "type": "edit", "trip_id": trip_id, "expense_id": row['ID'], "item_name": row['Item'],
                                        "request_user": username, "reason": reason, 
                                        "new_data": {"Item": new_item, "Amount": new_amt, "Original Amount": new_amt, "Currency": "KRW", "Exchange Rate": 1.0}
                                    })
                                    save_expense_requests(reqs)
                                    st.success("✅ 변경 요청이 전송되었습니다!")
                            
                            if st.button("🗑️ 내역 삭제 요청", key=f"req_d_{row['ID']}"):
                                reqs = load_expense_requests()
                                reqs.append({
                                    "type": "delete", "trip_id": trip_id, "expense_id": row['ID'], "item_name": row['Item'],
                                    "request_user": username, "reason": "사용자 삭제 요청"
                                })
                                save_expense_requests(reqs)
                                st.success("✅ 삭제 요청이 전송되었습니다!")
            else:
                st.info("아직 지출 내역이 없어요.")

        with tab_stats:
            if not st.session_state.df_expenses.empty:
                fig = px.pie(st.session_state.df_expenses, values='Amount', names='Category', hole=0.6,
                             color_discrete_sequence=['#1E3A8A', '#1D4ED8', '#2563EB', '#3B82F6', '#60A5FA', '#93C5FD'])
                fig.update_layout(showlegend=False, margin=dict(t=0, b=0, l=0, r=0), height=200)
                st.plotly_chart(fig, use_container_width=True)
                
                # Legend manually
                usage = st.session_state.df_expenses.groupby('Category')['Amount'].sum().sort_values(ascending=False)
                for cat, val in usage.items():
                    st.caption(f"{cat}: {val:,.0f} KRW ({val/total_spent*100:.1f}%)")

                # Excel Export Button
                st.divider()
                st.markdown("### 📥 여행 데이터 내보내기")
                try:
                    import io
                    output = io.BytesIO()
                    export_df = st.session_state.df_expenses.drop(columns=['image_path'], errors='ignore')
                    export_df['Date'] = export_df['Date'].dt.strftime('%Y-%m-%d %H:%M')
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        export_df.to_excel(writer, index=False, sheet_name='지출내역')
                    excel_data = output.getvalue()
                    st.download_button(
                        label="엑셀 파일(.xlsx) 다운로드",
                        data=excel_data,
                        file_name=f"여행지출내역_{trip_id}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                except Exception as e:
                    st.warning(f"엑셀 내보내기 실패: {e}")
            else:
                st.text("통계를 보려면 지출을 입력하세요.")

        with tab_itinerary:
            st.markdown("### 📅 여행 일정 관리")
            st.caption("시간대별 일정을 추가하고 확인하세요. 🕒")
            
            # --- 일정 추가 폼 ---
            with st.expander("➕ 새 일정 추가하기", expanded=False):
                with st.form("add_itinerary_form", clear_on_submit=True):
                    col1, col2 = st.columns(2)
                    with col1:
                        try:
                            t_start = datetime.strptime(current_trip['start_date'], "%Y/%m/%d").date()
                            t_end = datetime.strptime(current_trip['end_date'], "%Y/%m/%d").date()
                        except:
                            t_start = datetime.now().date()
                            t_end = datetime.now().date()
                        
                        i_date = st.date_input("날짜", value=t_start, min_value=t_start, max_value=t_end)
                        i_time = st.time_input("시간 (선택)")
                    with col2:
                        i_title = st.text_input("일정 제목 *", placeholder="예: 공항 도착 및 렌트카 픽업")
                        i_loc = st.text_input("장소", placeholder="지명, 주소, 또는 구글맵 링크")
                    
                    i_memo = st.text_area("메모", placeholder="필요한 메모 (예: 탑승권 챙기기, 바우처 확인 등)")
                    
                    if st.form_submit_button("일정 저장하기", use_container_width=True):
                        if not i_title:
                            st.error("일정 제목은 필수입니다!")
                        else:
                            evt_data = {
                                "date": i_date.strftime("%Y-%m-%d"),
                                "time": i_time.strftime("%H:%M") if i_time else "",
                                "title": i_title,
                                "location": i_loc,
                                "memo": i_memo
                            }
                            save_itinerary_event(trip_id, evt_data)
                            st.success("✅ 일정이 성공적으로 추가되었습니다!")
                            time.sleep(0.5)
                            st.rerun()

            # --- 타임라인 뷰 ---
            st.markdown("#### ⏳ 나의 타임라인")
            events = load_itineraries(trip_id)
            
            if not events:
                st.info("아직 등록된 일정이 없습니다. 새 일정을 추가해보세요! 🚀")
            else:
                # Group by date
                from collections import defaultdict
                itinerary_grouped = defaultdict(list)
                for ev in events:
                    itinerary_grouped[ev['date']].append(ev)
                
                for d_key in sorted(itinerary_grouped.keys()):
                    st.markdown(f"**🚩 {d_key}**")
                    day_events = itinerary_grouped[d_key]
                    
                    for ev in day_events:
                        with st.container():
                            col_info, col_del = st.columns([85, 15])
                            with col_info:
                                st.markdown(f"""
                                <div style="background-color: var(--card-bg); padding: 16px; border-radius: 12px; margin-bottom: 8px; border-left: 5px solid var(--primary); box-shadow: 0 4px 6px rgba(0,0,0,0.03);">
                                    <h5 style="margin:0; color:var(--text-main); font-weight: 700;">
                                        <span style="color:var(--primary); margin-right:8px;">{ev.get('time', '⏱️')}</span> {ev['title']}
                                    </h5>
                                    {f'<p style="margin:6px 0 0 0; color:var(--text-sub); font-size:0.9em;">📍 {ev["location"]}</p>' if ev.get('location') else ''}
                                    {f'<p style="margin:4px 0 0 0; color:var(--text-sub); font-size:0.85em;">📝 {ev["memo"]}</p>' if ev.get('memo') else ''}
                                </div>
                                """, unsafe_allow_html=True)
                            with col_del:
                                st.markdown("<br>", unsafe_allow_html=True) # 알맞은 정렬을 위해 띄어쓰기
                                if st.button("삭제", key=f"del_evt_{ev['id']}", use_container_width=True):
                                    delete_itinerary_event(ev['id'])
                                    time.sleep(0.3)
                                    st.rerun()
                            
                            st.write("") # card bottom margin


# --- 로그인 / 회원가입 화면 (Center Layout) ---
if st.session_state.user_session is None:
    
    # Profile Image Display
    col_spacer1, col_center, col_spacer2 = st.columns([1, 2, 1])
    
    with col_center:
        try:
            if os.path.exists(PROFILE_IMAGE_PATH):
                # Using custom HTML for circular image
                import base64
                with open(PROFILE_IMAGE_PATH, "rb") as f:
                    data = base64.b64encode(f.read()).decode("utf-8")
                
                st.markdown(f"""
                    <img src="data:image/png;base64,{data}" class="profile-img">
                    <div style="text-align: center; margin-bottom: 30px;">
                        <h2 style="margin: 0; color: #ff85c0; font-family: 'Jua', sans-serif;">✈️ 영늘 트립 트래커 ✈️</h2>
                        <p style="color: var(--text-sub); font-size: 1.1em;">당신의 완벽한 여행을 위하여 💖</p>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("<h1 style='text-align: center; color: #ff85c0; font-family: Jua, sans-serif;'>✈️ 영늘 트립 트래커 ✈️</h1>", unsafe_allow_html=True)
        except Exception:
            st.markdown("<h1 style='text-align: center; color: #ff85c0; font-family: Jua, sans-serif;'>✈️ 영늘 트립 트래커 ✈️</h1>", unsafe_allow_html=True)

        tab_login, tab_signup = st.tabs(["로그인", "회원가입"])
        
        with tab_login:
            login_id = st.text_input("아이디", key="login_id", placeholder="Username")
            login_pw = st.text_input("비밀번호", type="password", key="login_pw", placeholder="Password")
            remember_me = st.checkbox("로그인 상태 유지", value=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("시작하기 (Login)", use_container_width=True):
                user, msg = verify_user(login_id, login_pw)
                if user:
                    st.session_state.user_session = {"username": login_id, "role": user['role']}
                    st.session_state.explicit_logout = False
                    if remember_me:
                        cookie_manager.set("saved_user", login_id, expires_at=datetime.now() + pd.Timedelta(days=30))
                        cookie_manager.set("saved_role", user['role'], expires_at=datetime.now() + pd.Timedelta(days=30))
                    import time; time.sleep(0.5)
                    st.rerun()
                else:
                    st.error(msg)
                    
        with tab_signup:
            new_id = st.text_input("아이디", key="new_id", placeholder="사용할 아이디")
            new_pw = st.text_input("비밀번호", type="password", key="new_pw", placeholder="비밀번호 설정")
            
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("가입 신청하기", use_container_width=True):
                success, msg = register_user(new_id, new_pw)
                if success:
                    st.success(msg)
                else:
                    st.error(msg)

else:
    main_app()
# trigger clean deploy
