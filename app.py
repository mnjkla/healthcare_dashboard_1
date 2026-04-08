import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import analysis
from datetime import datetime
import time
import json

# --- Page Config ---
st.set_page_config(
    page_title="Health & Fitness Tracker Dashboard", 
    layout="wide", 
    page_icon="🏥",
    initial_sidebar_state="expanded"
)

# --- Custom CSS ---
st.markdown("""
<style>
    /* Main background */
    .stApp {
        background: linear-gradient(135deg, #0f0c29 0%, #1a1a3e 50%, #24243e 100%);
    }
    
    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e1e3f 0%, #2d1b69 100%);
    }
    section[data-testid="stSidebar"] .stMarkdown {
        color: #e0e0ff;
    }
    
    /* Metric cards */
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, rgba(102, 51, 153, 0.3), rgba(51, 51, 153, 0.3));
        border: 1px solid rgba(138, 43, 226, 0.3);
        border-radius: 16px;
        padding: 20px 16px;
        backdrop-filter: blur(10px);
        box-shadow: 0 4px 20px rgba(138, 43, 226, 0.15);
        transition: transform 0.2s;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 25px rgba(138, 43, 226, 0.25);
    }
    div[data-testid="stMetric"] label {
        color: #b8b8ff !important;
        font-size: 0.85rem !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        color: #ffffff !important;
        font-size: 1.8rem !important;
        font-weight: 700 !important;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: rgba(30, 30, 63, 0.5);
        border-radius: 12px;
        padding: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        color: #b8b8ff;
        font-weight: 500;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #6633cc, #3366cc) !important;
        color: white !important;
    }
    
    /* Chat */
    .stChatMessage {
        background: rgba(30, 30, 63, 0.6) !important;
        border: 1px solid rgba(138, 43, 226, 0.2) !important;
        border-radius: 12px !important;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background: rgba(102, 51, 153, 0.2);
        border-radius: 8px;
    }
    
    /* Health score circle */
    .health-score {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 120px;
        height: 120px;
        border-radius: 50%;
        font-size: 2rem;
        font-weight: 800;
        color: white;
        margin: 0 auto;
        text-align: center;
    }
    .score-high { background: linear-gradient(135deg, #00b894, #00cec9); }
    .score-mid { background: linear-gradient(135deg, #fdcb6e, #e17055); }
    .score-low { background: linear-gradient(135deg, #e17055, #d63031); }
    
    /* Priority badge */
    .priority-high { color: #ff6b6b; font-weight: 700; }
    .priority-mid { color: #feca57; font-weight: 700; }
    .priority-low { color: #48dbfb; font-weight: 700; }
    
    /* Headers */
    h1, h2, h3 { color: #e0e0ff !important; }
    
    /* Info / Success boxes */
    div[data-testid="stAlert"] {
        border-radius: 12px;
    }
</style>
""", unsafe_allow_html=True)

# --- Plotly theme ---
PLOT_TEMPLATE = "plotly_dark"
COLORS = {
    'primary': '#8b5cf6',
    'secondary': '#06b6d4',
    'accent': '#f59e0b',
    'success': '#10b981',
    'danger': '#ef4444',
    'gradient': ['#8b5cf6', '#06b6d4', '#10b981', '#f59e0b', '#ef4444']
}

# --- Hệ thống Đăng nhập ---
USERS = {
    "admin": {"height": 170, "gender": "Nam", "pref": "Gym", "age": 28, "condition": "Bình thường"},
    "user1": {"height": 160, "gender": "Nữ", "pref": "Yoga", "age": 45, "condition": "Tim mạch"},
    "user2": {"height": 175, "gender": "Nam", "pref": "Chạy bộ", "age": 55, "condition": "Tiểu đường"}
}

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['username'] = None

if not st.session_state['logged_in']:
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center; color: #b8b8ff;'>🔒 Đăng nhập Hệ thống</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: gray;'>Health & Fitness Tracker Dashboard</p>", unsafe_allow_html=True)
    
    _, col2, _ = st.columns([1, 2, 1])
    with col2:
        with st.container(border=True):
            username = st.text_input("👤 Tên đăng nhập")
            password = st.text_input("🔑 Mật khẩu", type="password")
            if st.button("Đăng nhập", use_container_width=True):
                if username in USERS and password == "123456":
                    st.session_state['logged_in'] = True
                    st.session_state['username'] = username
                    st.rerun()
                else:
                    st.error("Sai tài khoản! (Hỗ trợ: admin, user1, user2 | Pass: 123456)")
    # Ngừng chạy toàn bộ code phía dưới nếu chưa đăng nhập
    st.stop()

# ==========================================
# KHU VỰC SAU KHI ĐĂNG NHẬP (DASHBOARD)
# ==========================================
username = st.session_state['username']
user_info = USERS.get(username, {"height": 170, "gender": "Nam", "pref": "Gym", "age": 30, "condition": "Bình thường"})

# --- Load Data ---
df = analysis.load_data(f"data_{username}.csv")
anomalies = analysis.detect_anomalies(df, user_info['age'], user_info['condition'])

# --- Sidebar ---
st.sidebar.markdown(f"## 🏥 Xin chào, `{username}`")
st.sidebar.markdown(f"**Độ tuổi:** {user_info['age']} | **Bệnh lý:** *{user_info['condition']}*")
st.sidebar.divider()

st.sidebar.markdown("### ⚙️ Cá nhân hóa AI")
height_cm = st.sidebar.number_input("📏 Chiều cao (cm)", min_value=100, max_value=250, value=user_info["height"], step=1)
gender_list = ["Nam", "Nữ", "Khác"]
gender = st.sidebar.selectbox("⚧ Giới tính", gender_list, index=gender_list.index(user_info["gender"]))
pref_list = ["Gym", "Yoga", "Chạy bộ", "Bơi lội", "Đạp xe", "Thiền"]
pref = st.sidebar.selectbox("🏅 Sở thích tập luyện", pref_list, index=pref_list.index(user_info["pref"]))

risk_score = analysis.calculate_risk_score(df, height_cm, user_info['age'], user_info['condition'])

st.sidebar.divider()
st.sidebar.markdown("### 📅 Khoảng thời gian")
date_range = st.sidebar.date_input(
    "Chọn ngày", 
    [df['date'].min(), df['date'].max()],
    min_value=df['date'].min(),
    max_value=df['date'].max()
)

# Filter data
if len(date_range) == 2:
    start_date, end_date = date_range
    mask = (df['date'].dt.date >= start_date) & (df['date'].dt.date <= end_date)
    filtered_df = df.loc[mask]
else:
    filtered_df = df

st.sidebar.divider()
st.sidebar.markdown("### 📊 Thông tin dữ liệu")
st.sidebar.info(f"📅 {len(filtered_df)} ngày dữ liệu\n\n🗓️ {filtered_df['date'].min().strftime('%d/%m/%Y')} → {filtered_df['date'].max().strftime('%d/%m/%Y')}")

# Risk Score display
risk_color = '#10b981' if risk_score < 3 else '#f59e0b' if risk_score < 6 else '#ef4444'
risk_label = 'Thấp ✅' if risk_score < 3 else 'Trung bình ⚠️' if risk_score < 6 else 'Cao 🚨' if risk_score < 8 else 'Rất cao 🆘'
st.sidebar.markdown(f"""
<div style='background:rgba(0,0,0,0.3);border:1px solid {risk_color};border-radius:12px;padding:12px;text-align:center;margin-top:8px'>
  <div style='color:#b8b8ff;font-size:0.8rem;text-transform:uppercase;letter-spacing:1px'>RISK SCORE</div>
  <div style='color:{risk_color};font-size:2rem;font-weight:800'>{risk_score}/10</div>
  <div style='color:{risk_color};font-size:0.9rem'>{risk_label}</div>
</div>
""", unsafe_allow_html=True)

st.sidebar.divider()
st.sidebar.markdown("### 🔄 Đồng bộ Dữ liệu IoT")

update_mode = st.sidebar.radio(
    "Chế độ kết nối:", 
    ["Cập nhật chủ động (Thủ công)", "Live Auto-Refresh (5 phút)"]
)

if st.sidebar.button("🔁 Lấy dữ liệu mới nhất", type="primary", use_container_width=True):
    st.session_state['just_updated'] = True
    st.rerun()

st.sidebar.markdown("**🎮 Điều khiển Thiết bị Giả lập**")
if 'target_w' not in st.session_state:
    st.session_state['target_w'] = float(filtered_df['weight'].iloc[-1] if not filtered_df.empty else 47.0)
    # Khôi phục từ file nếu đã có file
    import os
    conf_file = f"sim_config_{username}.json"
    if os.path.exists(conf_file):
        try:
            with open(conf_file, 'r') as f:
                conf = json.load(f)
                st.session_state['target_w'] = conf.get('target_weight', st.session_state['target_w'])
        except: pass

target_w = st.sidebar.slider("Can thiệp cân nặng (kg)", min_value=30.0, max_value=150.0, value=st.session_state['target_w'], step=0.5)
st.session_state['target_w'] = target_w

# Ghi cấu hình cho simulator
try:
    with open(f'sim_config_{username}.json', 'w') as f:
        json.dump({'target_weight': target_w}, f)
except:
    pass

if update_mode == "Live Auto-Refresh (5 phút)":
    st.sidebar.caption("Đang chờ 5 phút để đồng bộ...")
    time.sleep(300)
    st.session_state['just_updated'] = True
    st.rerun()

# Hiển thị thông báo (toast) khi có dữ liệu mới cập nhật
if st.session_state.get('just_updated', False):
    rec_data = analysis.get_recommendations(df)
    st.toast(f"💡 Dữ liệu IoT đã tải! Lời khuyên: {rec_data['recommendation']}", icon="✅")
    st.session_state['just_updated'] = False

st.sidebar.divider()
if st.sidebar.button("🚪 Đăng xuất", use_container_width=True):
    st.session_state['logged_in'] = False
    st.session_state['username'] = None
    # Xoá cache thanh slider của cấu hình cũ để không bị lây chéo
    if 'target_w' in st.session_state:
        del st.session_state['target_w']
    # Xoá lịch sử chat của user cũ
    if 'messages' in st.session_state:
        del st.session_state['messages']
    st.rerun()

# --- Header ---
st.markdown("# 🏥 Health & Fitness Tracker Dashboard")
st.markdown("*Hệ thống Theo dõi và Phân tích Chỉ số Sức khỏe Đa Người dùng*")

if anomalies:
    for anomaly in anomalies:
        st.error(f"🚨 **CẢNH BÁO Y TẾ:** {anomaly}")

# --- KPI Cards ---
stats = analysis.get_summary_stats(filtered_df)
latest = filtered_df.iloc[-1]
bmi, bmi_cat = analysis.calculate_bmi(latest['weight'], height_cm)
health_score, score_details = analysis.calculate_health_score(filtered_df, height_cm)

# Calculate deltas (vs last week avg)
if len(filtered_df) > 7:
    prev_week = filtered_df.iloc[-14:-7] if len(filtered_df) >= 14 else filtered_df.iloc[:7]
    this_week = filtered_df.iloc[-7:]
    delta_steps = int(this_week['steps'].mean() - prev_week['steps'].mean())
    delta_hr = round(this_week['heart_rate'].mean() - prev_week['heart_rate'].mean(), 1)
    delta_sleep = round(this_week['sleep_hours'].mean() - prev_week['sleep_hours'].mean(), 1)
else:
    delta_steps = delta_hr = delta_sleep = None

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.metric("🏆 Điểm Sức khỏe", f"{health_score}/100")
with col2:
    st.metric("🚶 Bước chân TB", f"{int(stats['avg_steps']):,}", 
              delta=f"{delta_steps:+,}" if delta_steps else None)
with col3:
    st.metric("❤️ Nhịp tim TB", f"{stats['avg_heart_rate']} bpm",
              delta=f"{delta_hr:+} bpm" if delta_hr else None, delta_color="inverse")
with col4:
    st.metric("🛏️ Giấc ngủ TB", f"{stats['avg_sleep']}h",
              delta=f"{delta_sleep:+}h" if delta_sleep else None)
with col5:
    st.metric("⚖️ BMI", f"{bmi}", f"({bmi_cat})", delta_color="off")

st.markdown("")

# Risk score banner
if risk_score >= 8:
    st.error(f"🆘 **RỦI RO RẤT CAO ({risk_score}/10):** Hệ thống khuyến nghị gặp bác sĩ sớm!")
elif risk_score >= 6:
    st.warning(f"🚨 **Rủi ro sức khỏe CAO ({risk_score}/10)** — Cần theo dõi sát các chỉ số!")

# === TABS ===
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Tổng quan", 
    "📈 Phân tích chi tiết", 
    "💪 Cải thiện thể lực",
    "🏃 Gợi ý tập luyện",
    "🤖 Trợ lý Sức khỏe"
])

# ==========================================
# TAB 1: TỔNG QUAN
# ==========================================
with tab1:
    row1_col1, row1_col2 = st.columns(2)
    
    with row1_col1:
        st.subheader("❤️ Nhịp tim theo ngày")
        fig_hr = px.line(filtered_df, x='date', y='heart_rate', markers=True,
                         template=PLOT_TEMPLATE)
        fig_hr.update_traces(line_color=COLORS['danger'], marker_color=COLORS['danger'],
                            fill='tozeroy', fillcolor='rgba(239, 68, 68, 0.1)')
        fig_hr.update_layout(
            xaxis_title="Ngày", yaxis_title="Nhịp tim (bpm)",
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
            font_color='#b8b8ff', height=350,
            margin=dict(l=20, r=20, t=30, b=20)
        )
        fig_hr.update_xaxes(tickformat="%d/%m", nticks=10)
        # Add safe zone
        fig_hr.add_hrect(y0=60, y1=80, fillcolor="rgba(16,185,129,0.1)", 
                        line_width=0, annotation_text="Vùng an toàn", annotation_position="top right")
        st.plotly_chart(fig_hr, use_container_width=True)

    with row1_col2:
        st.subheader("🚶 Bước chân hàng ngày")
        # Color bars by activity level
        df_activity, _ = analysis.analyze_activity_density(filtered_df)
        color_map = {'Thấp': COLORS['danger'], 'Trung bình': COLORS['accent'], 'Cao': COLORS['success']}
        fig_steps = px.bar(df_activity, x='date', y='steps', color='activity_level',
                          color_discrete_map=color_map, template=PLOT_TEMPLATE)
        fig_steps.update_layout(
            xaxis_title="Ngày", yaxis_title="Số bước chân",
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
            font_color='#b8b8ff', height=350, legend_title="Mức hoạt động",
            margin=dict(l=20, r=20, t=30, b=20)
        )
        fig_steps.update_xaxes(tickformat="%d/%m", nticks=10)
        # Add 10k target line
        fig_steps.add_hline(y=10000, line_dash="dash", line_color=COLORS['secondary'],
                           annotation_text="Mục tiêu 10,000", annotation_position="top right")
        st.plotly_chart(fig_steps, use_container_width=True)

    st.divider()
    row2_col1, row2_col2 = st.columns(2)

    with row2_col1:
        st.subheader("⚖️ Calories vs Cân nặng")
        fig_cal = go.Figure()
        fig_cal.add_trace(go.Scatter(
            x=filtered_df['date'], y=filtered_df['calories'],
            name='Calories', yaxis='y1', fill='tozeroy',
            line=dict(color=COLORS['accent']), fillcolor='rgba(245,158,11,0.1)'
        ))
        fig_cal.add_trace(go.Scatter(
            x=filtered_df['date'], y=filtered_df['weight'],
            name='Cân nặng (kg)', yaxis='y2',
            line=dict(color=COLORS['secondary'], width=3)
        ))
        fig_cal.update_layout(
            yaxis=dict(title=dict(text="Calories (kcal)", font=dict(color=COLORS['accent']))),
            yaxis2=dict(title=dict(text="Cân nặng (kg)", font=dict(color=COLORS['secondary'])), overlaying='y', side='right'),
            template=PLOT_TEMPLATE,
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
            font_color='#b8b8ff', height=350, legend=dict(orientation="h", y=1.12),
            margin=dict(l=20, r=20, t=30, b=20)
        )
        fig_cal.update_xaxes(tickformat="%d/%m", nticks=10)
        st.plotly_chart(fig_cal, use_container_width=True)

    with row2_col2:
        st.subheader("🛏️ Giấc ngủ")
        fig_sleep = px.area(filtered_df, x='date', y='sleep_hours', template=PLOT_TEMPLATE)
        fig_sleep.update_traces(line_color=COLORS['primary'], fillcolor='rgba(139,92,246,0.2)')
        fig_sleep.update_layout(
            xaxis_title="Ngày", yaxis_title="Số giờ ngủ",
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
            font_color='#b8b8ff', height=350,
            margin=dict(l=20, r=20, t=30, b=20)
        )
        fig_sleep.update_xaxes(tickformat="%d/%m", nticks=10)
        fig_sleep.add_hrect(y0=7, y1=9, fillcolor="rgba(16,185,129,0.1)", 
                           line_width=0, annotation_text="Lý tưởng (7-9h)")
        st.plotly_chart(fig_sleep, use_container_width=True)

# ==========================================
# TAB 2: PHÂN TÍCH CHI TIẾT
# ==========================================
with tab2:
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.subheader("📉 BMI theo thời gian")
        bmi_df = analysis.calculate_bmi_series(filtered_df, height_cm)
        fig_bmi = px.line(bmi_df, x='date', y='bmi', markers=True, template=PLOT_TEMPLATE)
        fig_bmi.update_traces(line_color=COLORS['primary'], marker_color=COLORS['primary'])
        fig_bmi.add_hrect(y0=18.5, y1=25, fillcolor="rgba(16,185,129,0.15)", line_width=0,
                         annotation_text="BMI bình thường (18.5-25)", annotation_position="top left")
        fig_bmi.update_layout(
            xaxis_title="Ngày", yaxis_title="BMI",
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
            font_color='#b8b8ff', height=350,
            margin=dict(l=20, r=20, t=30, b=20)
        )
        fig_bmi.update_xaxes(tickformat="%d/%m", nticks=10)
        st.plotly_chart(fig_bmi, use_container_width=True)
    
    with col_b:
        st.subheader("📊 Mật độ hoạt động")
        _, density = analysis.analyze_activity_density(filtered_df)
        fig_density = px.pie(
            names=list(density.keys()), values=list(density.values()),
            color=list(density.keys()),
            color_discrete_map={'Thấp': COLORS['danger'], 'Trung bình': COLORS['accent'], 'Cao': COLORS['success']},
            template=PLOT_TEMPLATE, hole=0.5
        )
        fig_density.update_layout(
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
            font_color='#b8b8ff', height=350,
            margin=dict(l=20, r=20, t=30, b=20)
        )
        fig_density.update_traces(textinfo='label+percent', textfont_size=13)
        st.plotly_chart(fig_density, use_container_width=True)
    
    st.divider()
    
    # Correlation heatmap
    st.subheader("🔗 Ma trận tương quan giữa các chỉ số")
    corr_cols = ['steps', 'heart_rate', 'calories', 'sleep_hours', 'weight']
    labels_vn = ['Bước chân', 'Nhịp tim', 'Calories', 'Giấc ngủ', 'Cân nặng']
    corr_matrix = filtered_df[corr_cols].corr()
    
    fig_corr = px.imshow(
        corr_matrix.values, 
        x=labels_vn, y=labels_vn,
        color_continuous_scale='RdBu_r', zmin=-1, zmax=1,
        template=PLOT_TEMPLATE, text_auto='.2f'
    )
    fig_corr.update_layout(
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        font_color='#b8b8ff', height=400,
        margin=dict(l=20, r=20, t=30, b=20)
    )
    st.plotly_chart(fig_corr, use_container_width=True)
    
    # Health Score breakdown
    st.subheader("🏆 Chi tiết Điểm sức khỏe")
    score_col1, score_col2 = st.columns([1, 2])
    with score_col1:
        if health_score >= 75:
            score_class = "score-high"
            score_label = "Tốt! 💪"
        elif health_score >= 50:
            score_class = "score-mid"
            score_label = "Khá 👌"
        else:
            score_class = "score-low"
            score_label = "Cần cải thiện ⚠️"
        
        st.markdown(f'<div class="health-score {score_class}">{health_score}</div>', unsafe_allow_html=True)
        st.markdown(f"<p style='text-align:center; color:#b8b8ff; font-size:1.1rem; margin-top:8px'>{score_label}</p>", unsafe_allow_html=True)
    
    with score_col2:
        for name, got, max_s in score_details:
            pct = got / max_s
            color = COLORS['success'] if pct >= 0.75 else COLORS['accent'] if pct >= 0.5 else COLORS['danger']
            st.markdown(f"**{name}**: {got}/{max_s}")
            st.progress(pct)

# ==========================================
# TAB 3: CẢI THIỆN THỂ LỰC
# ==========================================
with tab3:
    st.subheader("💪 Đánh giá cải thiện thể lực (Tuần 1 vs Tuần 4)")
    
    fitness = analysis.get_fitness_improvement(filtered_df, height_cm)
    trends = analysis.analyze_trends(filtered_df)
    
    # Overall score
    if fitness['score_pct'] >= 75:
        st.success(f"🎉 Điểm cải thiện tổng thể: **{fitness['score_pct']}%** – Tiến bộ tuyệt vời!")
    elif fitness['score_pct'] >= 50:
        st.info(f"👍 Điểm cải thiện tổng thể: **{fitness['score_pct']}%** – Khá ổn, tiếp tục cố gắng!")
    else:
        st.warning(f"⚠️ Điểm cải thiện tổng thể: **{fitness['score_pct']}%** – Cần nỗ lực hơn!")
    
    st.markdown("")
    
    # Detailed improvements table
    for icon, name, change, status in fitness['improvements']:
        with st.container():
            c1, c2, c3 = st.columns([1, 3, 2])
            with c1:
                st.markdown(f"### {icon}")
            with c2:
                st.markdown(f"**{name}**")
                st.caption(change)
            with c3:
                if "Tốt" in status or "khỏe" in status:
                    st.success(status)
                elif "Cần" in status:
                    st.warning(status)
                else:
                    st.info(status)
    
    st.divider()
    
    # Radar chart comparing week 1 vs week 4
    st.subheader("📊 So sánh Tuần 1 vs Tuần 4")
    
    categories = [t['label'] for t in trends.values()]
    w1_values = [t['w1_avg'] for t in trends.values()]
    w4_values = [t['w4_avg'] for t in trends.values()]
    
    # Normalize for radar (0-1 scale)
    max_vals = [max(a, b) for a, b in zip(w1_values, w4_values)]
    w1_norm = [v / m if m > 0 else 0 for v, m in zip(w1_values, max_vals)]
    w4_norm = [v / m if m > 0 else 0 for v, m in zip(w4_values, max_vals)]
    
    fig_radar = go.Figure()
    fig_radar.add_trace(go.Scatterpolar(
        r=w1_norm + [w1_norm[0]], theta=categories + [categories[0]],
        fill='toself', name='Tuần 1', fillcolor='rgba(239,68,68,0.2)',
        line_color=COLORS['danger']
    ))
    fig_radar.add_trace(go.Scatterpolar(
        r=w4_norm + [w4_norm[0]], theta=categories + [categories[0]],
        fill='toself', name='Tuần 4', fillcolor='rgba(16,185,129,0.2)',
        line_color=COLORS['success']
    ))
    fig_radar.update_layout(
        polar=dict(bgcolor='rgba(0,0,0,0)', radialaxis=dict(visible=True, range=[0, 1.1])),
        template=PLOT_TEMPLATE,
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        font_color='#b8b8ff', height=400, showlegend=True,
        margin=dict(l=60, r=60, t=30, b=30)
    )
    st.plotly_chart(fig_radar, use_container_width=True)
    
    # Change details
    with st.expander("📋 Chi tiết thay đổi theo từng chỉ số"):
        for metric, data in trends.items():
            symbol = "📈" if data['change_pct'] > 0 else "📉"
            direction = "tăng" if data['change_pct'] > 0 else "giảm"
            st.markdown(f"{symbol} **{data['label']}**: {data['w1_avg']} → {data['w4_avg']} ({direction} {abs(data['change_pct'])}%)")

# ==========================================
# TAB 4: GỢI Ý TẬP LUYỆN
# ==========================================
with tab4:
    st.subheader("🏃 Gợi ý chế độ tập luyện cá nhân hóa")
    st.caption("Dựa trên hệ thống phân tích kết hợp Môn thể thao yêu thích của bạn")
    st.markdown("")
    
    recs = analysis.get_exercise_recommendations(filtered_df, height_cm, gender, pref, user_info['age'], user_info['condition'], anomalies)
    
    for rec in recs:
        priority_class = {
            'Cao': 'priority-high',
            'Trung bình': 'priority-mid',
            'Thấp': 'priority-low'
        }.get(rec['priority'], 'priority-mid')
        
        with st.container():
            st.markdown(f"""
            ### {rec['icon']} {rec['title']}
            <span class="{priority_class}">Ưu tiên: {rec['priority']}</span>
            
            {rec['detail']}
            """, unsafe_allow_html=True)
            st.markdown("")
    
    st.divider()
    
    # Quick recommendations
    rec_data = analysis.get_recommendations(filtered_df)
    st.info(f"📌 **Nhận xét hôm nay:** {rec_data['insight']}")
    st.success(f"💡 **Lời khuyên:** {rec_data['recommendation']}")

# ==========================================
# TAB 5: CHATBOX TRỢ LÝ SỨC KHỎE
# ==========================================
with tab5:
    st.subheader("🤖 Trợ lý Quyết định Sức khỏe")
    st.caption(f"Phân tích dữ liệu thực từ Fitbit (35 người dùng) + Cardiovascular 70,000 bệnh nhân | Risk Score hôm nay: **{risk_score}/10**")

    # ── Quick Action Buttons ──────────────────────────────────────────────────
    st.markdown("**⚡ Câu hỏi nhanh:**")
    qa_col1, qa_col2, qa_col3, qa_col4 = st.columns(4)
    quick_prompt = None
    with qa_col1:
        if st.button("🏃 Có nên tập hôm nay?", use_container_width=True):
            quick_prompt = "hom nay co nen tap khong"
    with qa_col2:
        if st.button("🍽️ Hôm nay ăn gì?", use_container_width=True):
            quick_prompt = "hom nay an gi"
    with qa_col3:
        if st.button("🚨 Tôi đang nguy hiểm không?", use_container_width=True):
            quick_prompt = "toi co dang nguy hiem khong"
    with qa_col4:
        if st.button("📊 Tổng quan sức khỏe", use_container_width=True):
            quick_prompt = "tổng quan sức khỏe"

    st.markdown("")

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": analysis.chatbot_response("xin chào", filtered_df, height_cm, gender, pref, user_info['age'], user_info['condition'], anomalies)}
        ]

    # Handle quick action button press
    if quick_prompt:
        st.session_state.messages.append({"role": "user", "content": quick_prompt})
        resp_qa = analysis.chatbot_response(quick_prompt, filtered_df, height_cm, gender, pref, user_info['age'], user_info['condition'], anomalies)
        st.session_state.messages.append({"role": "assistant", "content": resp_qa})
        st.rerun()

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"], avatar="🤖" if message["role"] == "assistant" else "👤"):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Hỏi trực tiếp: 'Hôm nay có nên tập không?', 'Tôi đang nguy hiểm không?', 'Hôm nay ăn gì?'..."):
        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        response = analysis.chatbot_response(prompt, filtered_df, height_cm, gender, pref, user_info['age'], user_info['condition'], anomalies)
        with st.chat_message("assistant", avatar="🤖"):
            st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})

# --- Footer ---
st.divider()
st.caption("🏥 Health & Fitness Tracker Dashboard | Công nghệ: Streamlit + Pandas + Plotly | Dữ liệu: IoT / Mobile Sensor")
