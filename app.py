import streamlit as st
import pandas as pd
import plotly.express as px
from utils import load_data, save_data, calculate_metrics, get_exchange_rate, load_folders, save_folders, load_users, register_user, verify_user, approve_user, delete_user
from datetime import datetime
import uuid
import os

# 페이지 설정
st.set_page_config(page_title="영현이의 여행", page_icon="✈️", layout="wide")

# Image Paths
# Local or deployed relative path
PROFILE_IMAGE_PATH = "profile.png"

# CSS 스타일 적용 (Ant Design Mobile Inspired)
st.markdown("""
    <style>
    /* Global Font */
    html, body, [class*="css"] {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        color: #1f1f1f;
    }

    /* Primary Color: Ant Design Blue */
    :root {
        --primary-color: #1677ff;
        --bg-color: #f5f5f5;
        --card-bg: #ffffff;
    }

    /* Override Streamlit Main Container Padding for Mobile */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 5rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        max-width: 800px; /* Maximize mobile view width on desktop */
    }

    /* Metric Cards */
    .metric-card {
        padding: 16px;
        border-radius: 12px;
        background-color: var(--card-bg);
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        text-align: center;
        margin-bottom: 12px;
    }

    /* Buttons (Ant Design Style) */
    .stButton button {
        background-color: var(--primary-color) !important;
        color: white !important;
        border-radius: 8px !important;
        border: none !important;
        padding: 12px 24px !important;
        font-weight: 500 !important;
        font-size: 16px !important;
        width: 100%; /* Full width on mobile */
        box-shadow: 0 2px 0 rgba(5, 145, 255, 0.1);
        transition: all 0.3s;
    }
    .stButton button:hover {
        background-color: #4096ff !important;
        transform: translateY(-1px);
        box-shadow: 0 4px 10px rgba(5, 145, 255, 0.2);
    }
    .stButton button:active {
        background-color: #0958d9 !important;
    }
    
    /* Secondary Button (Outline) - using type="secondary" */
    button[kind="secondary"] {
        background-color: transparent !important;
        color: var(--primary-color) !important;
        border: 1px solid var(--primary-color) !important;
        box-shadow: none !important;
    }
    button[kind="secondary"]:hover {
        background-color: #e6f7ff !important;
    }

    /* Input Fields */
    .stTextInput input, .stNumberInput input, .stSelectbox select, .stDateInput input {
        border-radius: 8px !important;
        border: 1px solid #d9d9d9 !important;
        padding: 10px 12px !important;
    }
    .stTextInput input:focus, .stNumberInput input:focus {
        border-color: var(--primary-color) !important;
        box-shadow: 0 0 0 2px rgba(5, 145, 255, 0.1) !important;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        border-bottom: 1px solid #f0f0f0;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        border-radius: 8px 8px 0 0;
        padding: 0 24px;
        font-weight: 500;
    }
    .stTabs [aria-selected="true"] {
        background-color: white !important;
        color: var(--primary-color) !important;
        border-bottom: 2px solid var(--primary-color) !important;
    }

    /* Hide Default Header/Footer */
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Custom Profile Image Style */
    .profile-img {
        display: block;
        margin-left: auto;
        margin-right: auto;
        width: 120px;
        height: 120px;
        border-radius: 50%;
        object-fit: cover;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        margin-bottom: 20px;
        border: 3px solid white;
    }
    
    /* Mobile-first Headers */
    h1, h2, h3 {
        font-weight: 600 !important;
        letter-spacing: -0.5px;
    }
    
    /* Expander Style */
    .streamlit-expanderHeader {
        background-color: white;
        border-radius: 8px;
        padding: 12px;
        margin-bottom: 8px;
        border: 1px solid #f0f0f0;
    }

    </style>
    """, unsafe_allow_html=True)

# 초기화
if 'folders' not in st.session_state:
    st.session_state.folders = load_folders()

if 'current_trip_id' not in st.session_state:
    st.session_state.current_trip_id = None

if 'df_expenses' not in st.session_state:
    st.session_state.df_expenses = pd.DataFrame()

# 세션 상태: 사용자 인증
if 'user_session' not in st.session_state:
    st.session_state.user_session = None

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
        st.session_state.user_session = None
        st.session_state.current_trip_id = None
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
    st.sidebar.caption("Designed with ❤️ by Antigravity AI")

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
                    # Card-like container for each trip
                    with st.container():
                        st.markdown(f"""
                        <div style="background: white; padding: 16px; border-radius: 12px; margin-bottom: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); border: 1px solid #f0f0f0;">
                            <h3 style="margin: 0 0 10px 0;">🏝 {name}</h3>
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
                    new_trip_pw = st.text_input("비밀번호 설정")
                    new_trip_budget = st.number_input("총 예산 (KRW)", min_value=0, value=1000000, step=10000)
                    
                    if st.form_submit_button("여행 생성하기 ✨"):
                        if new_trip_name and new_trip_pw:
                            new_id = str(uuid.uuid4())
                            st.session_state.folders[new_id] = {
                                "name": new_trip_name,
                                "password": new_trip_pw,
                                "budget": int(new_trip_budget),
                                "created_at": datetime.now().strftime("%Y-%m-%d")
                            }
                            save_folders(st.session_state.folders)
                            st.success("새로운 여행이 추가되었습니다!")
                            st.rerun()
                        else:
                            st.warning("이름과 비밀번호는 필수입니다.")
                
                st.divider()
                st.subheader("사용자 승인")
                users = load_users()
                pending_users = [u for u, data in users.items() if not data['approved']]
                
                if pending_users:
                    for u in pending_users:
                        c1, c2 = st.columns([3, 1])
                        c1.info(f"👤 {u}")
                        if c2.button("승인", key=f"approve_{u}"):
                            approve_user(u)
                            st.rerun()
                else:
                    st.caption("대기 중인 사용자가 없습니다.")

    else:
        # Trip Dashboard
        trip_id = st.session_state.current_trip_id
        trip_data = st.session_state.folders[trip_id]
        
        # Header with Exit Button
        col_head, col_exit = st.columns([4, 1])
        with col_head:
            st.title(trip_data['name'])
        with col_exit:
           pass # Exit logic moved to sidebar/top for cleaner look
            
        # Metrics
        budget = trip_data['budget']
        total_spent, remaining = calculate_metrics(st.session_state.df_expenses, budget)
        
        # Mobile Metric Grid
        m1, m2 = st.columns(2)
        with m1:
            st.markdown(f"""
            <div class="metric-card">
                <div style="font-size: 12px; color: #888;">지출 (Spent)</div>
                <div style="font-size: 20px; font-weight: bold; color: #ff4d4f;">{total_spent:,.0f}</div>
                <div style="font-size: 10px; color: #888;">{total_spent/budget*100:.1f}%</div>
            </div>
            """, unsafe_allow_html=True)
        with m2:
            st.markdown(f"""
            <div class="metric-card">
                <div style="font-size: 12px; color: #888;">잔액 (Left)</div>
                <div style="font-size: 20px; font-weight: bold; color: {'#52c41a' if remaining > 0 else '#ff4d4f'};">{remaining:,.0f}</div>
                 <div style="font-size: 10px; color: #888;">{remaining/budget*100:.1f}%</div>
            </div>
            """, unsafe_allow_html=True)

        st.progress(min(total_spent / budget if budget > 0 else 0, 1.0))

        # Main Actions
        tab_add, tab_history, tab_stats = st.tabs(["➕ 지출 추가", "📋 내역", "📊 통계"])

        with tab_add:
            with st.container():
                st.markdown("### 💸 지출 기록하기")
                col_date, col_curr = st.columns(2)
                with col_date:
                    date = st.date_input("날짜", datetime.now(), label_visibility="collapsed")
                with col_curr:
                    currency = st.selectbox("통화", ["KRW", "USD", "EUR", "JPY"], label_visibility="collapsed")
                
                # Fetch rate quietly
                current_rate = get_exchange_rate(currency, date)
                
                category = st.selectbox("카테고리", ["식비 (Food)", "교통 (Transport)", "숙박 (Accommodation)", "쇼핑 (Shopping)", "관광 (Activities)", "기타 (Others)"])
                item = st.text_input("무엇을 샀나요?", placeholder="예: 맛있는 라멘")
                
                c1, c2 = st.columns(2)
                with c1:
                    amount_origin = st.number_input(f"금액 ({currency})", min_value=0.0, format="%.2f")
                with c2:
                    manual_rate = st.number_input("환율", value=float(current_rate), format="%.2f")
                
                if st.button("저장하기 (Save)", use_container_width=True):
                    final_krw = amount_origin * manual_rate
                    new_data = pd.DataFrame({
                        "Date": [pd.to_datetime(date)],
                        "Category": [category],
                        "Item": [item],
                        "Amount": [final_krw],
                        "Currency": [currency],
                        "Original Amount": [amount_origin],
                        "Exchange Rate": [manual_rate]
                    })
                    st.session_state.df_expenses = pd.concat([st.session_state.df_expenses, new_data], ignore_index=True)
                    save_data(st.session_state.df_expenses, trip_id)
                    st.toast(f"✅ {item} 저장 완료!")
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
                    
                    st.markdown(f"""
                    <div style="background: white; padding: 12px; border-radius: 12px; margin-bottom: 8px; border: 1px solid #f0f0f0; display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <div style="font-size: 16px; font-weight: 600;">{emoji} {row['Item']}</div>
                            <div style="font-size: 12px; color: #888;">{row['Date'].strftime('%m.%d')} · {row['Category']}</div>
                        </div>
                        <div style="text-align: right;">
                            <div style="font-size: 16px; font-weight: bold; color: #1f1f1f;">-{row['Amount']:,.0f}</div>
                            <div style="font-size: 11px; color: #aaa;">{row['Original Amount']:,.2f} {row['Currency']}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("아직 지출 내역이 없어요.")

        with tab_stats:
            if not st.session_state.df_expenses.empty:
                fig = px.pie(st.session_state.df_expenses, values='Amount', names='Category', hole=0.6,
                             color_discrete_sequence=px.colors.qualitative.Pastel)
                fig.update_layout(showlegend=False, margin=dict(t=0, b=0, l=0, r=0), height=200)
                st.plotly_chart(fig, use_container_width=True)
                
                # Legend manually
                usage = st.session_state.df_expenses.groupby('Category')['Amount'].sum().sort_values(ascending=False)
                for cat, val in usage.items():
                    st.caption(f"{cat}: {val:,.0f} KRW ({val/total_spent*100:.1f}%)")
            else:
                st.text("통계를 보려면 지출을 입력하세요.")


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
                        <h2 style="margin: 0;">여행 경비 트래커</h2>
                        <p style="color: #888;">당신의 완벽한 여행을 위하여</p>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.title("여행 경비 트래커")
        except Exception:
            st.title("여행 경비 트래커")

        tab_login, tab_signup = st.tabs(["로그인", "회원가입"])
        
        with tab_login:
            login_id = st.text_input("아이디", key="login_id", placeholder="Username")
            login_pw = st.text_input("비밀번호", type="password", key="login_pw", placeholder="Password")
            
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("시작하기 (Login)", use_container_width=True):
                user, msg = verify_user(login_id, login_pw)
                if user:
                    st.session_state.user_session = {"username": login_id, "role": user['role']}
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
