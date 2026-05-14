import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, timedelta

# -----------------------------------------------------------------------------
# 1. 페이지 설정 및 세련된 디자인(CSS) 적용
# -----------------------------------------------------------------------------
st.set_page_config(page_title="GS25 FF 코칭 PRO MAX", page_icon="🏪", layout="wide")

st.markdown("""
<style>
    html, body, [class*="css"] { font-family: 'Pretendard', sans-serif; }
    /* 카드형 지표 스타일 */
    div[data-testid="metric-container"] {
        background-color: #ffffff; border: 1px solid #e6e9ef;
        padding: 15px; border-radius: 12px; box-shadow: 0px 2px 10px rgba(0,0,0,0.05);
    }
    /* 탭 디자인 강화 */
    button[data-baseweb="tab"] { font-weight: 700; font-size: 16px !important; }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. 보안 로직 (비밀번호 힌트 삭제)
# -----------------------------------------------------------------------------
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False
    
    if not st.session_state["password_correct"]:
        st.title("🔒 GS25 매출 코칭 시스템")
        # 요청사항 반영: 입력창에 비밀번호 힌트 문구 삭제
        pwd = st.text_input("비밀번호를 입력하세요", type="password")
        
        if st.button("로그인"):
            if pwd == "GS25":
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("❌ 비밀번호가 일치하지 않습니다.")
        return False
    return True

if not check_password():
    st.stop()

# -----------------------------------------------------------------------------
# 3. 데이터 로드 로직 (항목명: 파트명, 현재코드, 점포유형, 일매출 적용)
# -----------------------------------------------------------------------------
@st.cache_data
def load_data():
    # 마스터 정보
    store_meta = {
        "상무본점": {"파트명": "영업1팀", "점포유형": "유흥가", "현재코드": "25001"},
        "첨단산단점": {"파트명": "영업2팀", "점포유형": "오피스", "현재코드": "25002"},
        "수완지구점": {"파트명": "영업1팀", "점포유형": "주택가", "현재코드": "25003"}
    }
    categories = ["도시락", "김밥", "주먹밥", "햄버거/샌드위치", "FF간편식"]
    days_kr = ["월", "화", "수", "목", "금", "토", "일"]
    today = datetime.today()

    daily_records = []
    hourly_records = []

    for store, meta in store_meta.items():
        # 기간 설정: 당월(1~14일 누적 가정), 전월(30일), 전년동월(30일)
        for period, offset in [("당월", 0), ("전월", 30), ("전년동월", 365)]:
            days = 14 if period == "당월" else 30
            for i in range(days):
                dt = today - timedelta(days=i + offset)
                for cat in categories:
                    inbound = np.random.randint(10, 40)
                    sales = int(inbound * np.random.uniform(0.7, 0.95))
                    # '일매출' 필드 사용
                    revenue = sales * np.random.randint(3000, 5500)
                    
                    daily_records.append({
                        "일자": dt.strftime("%Y-%m-%d"),
                        "기간": period,
                        "요일": days_kr[dt.weekday()],
                        "점포명": store,
                        "현재코드": meta["현재코드"],
                        "점포유형": meta["점포유형"],
                        "파트명": meta["파트명"],
                        "중분류": cat,
                        "입고수량": inbound,
                        "판매수량": sales,
                        "일매출": revenue
                    })
        
        # 시간대별 데이터
        for day in days_kr:
            for hr in range(24):
                hourly_records.append({
                    "점포명": store, "요일": day, "결제시간대": hr,
                    "판매량": np.random.randint(5, 50)
                })

    return pd.DataFrame(daily_records), pd.DataFrame(hourly_records), store_meta

df_daily, df_hourly, store_meta = load_data()

# -----------------------------------------------------------------------------
# 4. 사이드바 검색 (모바일 최적화)
# -----------------------------------------------------------------------------
st.sidebar.header("🔍 분석 조건")
part_list = sorted(list(set(df_daily['파트명'])))
selected_part = st.sidebar.selectbox("담당 파트명", part_list, index=None, placeholder="파트 선택/검색")

if selected_part:
    stores_in_part = sorted(list(set(df_daily[df_daily['파트명'] == selected_part]['점포명'])))
    selected_store = st.sidebar.selectbox("점포 선택", stores_in_part, index=None, placeholder="점포명 선택/검색")

# -----------------------------------------------------------------------------
# 5. 메인 리포트 화면
# -----------------------------------------------------------------------------
if not selected_part or not selected_store:
    st.info("👈 왼쪽 사이드바에서 파트와 점포를 선택해 주세요.")
else:
    # 데이터 필터링
    df_s = df_daily[df_daily['점포명'] == selected_store]
    df_h = df_hourly[df_hourly['점포명'] == selected_store]
    curr_area = store_meta[selected_store]["점포유형"]

    # 기간 표시
    st.markdown("##### 🗓️ 분석 기준 기간")
    p_cols = st.columns(3)
    for i, p in enumerate(["당월", "전월", "전년동월"]):
        temp = df_s[df_s['기간'] == p]
        p_cols[i].caption(f"**{p}**: {temp['일자'].min()} ~ {temp['일자'].max()}")
    
    st.markdown("---")

    tab1, tab2, tab3 = st.tabs(["💡 발주/진열 코칭", "🏆 상권 베스트", "📈 매출 흐름 요약"])

    # --- TAB 1: 코칭 및 시간대 분석 ---
    with tab1:
        st.subheader("1. 📉 과거 FF 매출 흐름 (단위: 천원)")
        
        # 매출 합계 및 천원 단위 환산
        def get_k_rev(p): return df_s[df_s['기간'] == p]['일매출'].sum() / 1000
        
        rev_data = pd.DataFrame({
            "구분": ["작년 동월", "전월 전체", "당월 누적"],
            "금액": [get_k_rev("전년동월"), get_k_rev("전월"), get_k_rev("당월")]
        })

        # 세련된 레이아웃: 막대 너비 조절 및 중앙 배치
        _, chart_col, _ = st.columns([0.1, 0.8, 0.1])
        with chart_col:
            fig_rev = px.bar(rev_data, x="구분", y="금액", text=rev_data['금액'].apply(lambda x: f"{x:,.0f}k"),
                             color="구분", color_discrete_map={"작년 동월":"#DEE2E6", "전월 전체":"#ADB5BD", "당월 누적":"#0078D7"})
            fig_rev.update_traces(width=0.4, textposition='outside')
            fig_rev.update_layout(template='plotly_white', showlegend=False, yaxis_visible=False, height=350, margin=dict(t=50))
            st.plotly_chart(fig_rev, use_container_width=True)

        st.divider()
        
        st.subheader("2. 📅 요일별 예상 판매량 및 권장 발주")
        # 가중치 적용 로직
        day_order = ["월", "화", "수", "목", "금", "토", "일"]
        cats = ["도시락", "김밥", "주먹밥", "햄버거/샌드위치", "FF간편식"]
        forecast_table = pd.DataFrame(index=cats, columns=day_order)

        for c in cats:
            for d in day_order:
                # 기간별 평균 판매량
                v_curr = df_s[(df_s['중분류']==c) & (df_s['요일']==d) & (df_s['기간']=="당월")]['판매수량'].mean()
                v_prev = df_s[(df_s['중분류']==c) & (df_s['요일']==d) & (df_s['기간']=="전월")]['판매수량'].mean()
                v_yoy = df_s[(df_s['중분류']==c) & (df_s['요일']==d) & (df_s['기간']=="전년동월")]['판매수량'].mean()
                
                # 가중치 합산 (당월 0.6, 전월 0.3, 전년 0.1)
                final_v = (v_curr*0.6 if not np.isnan(v_curr) else 0) + \
                          (v_prev*0.3 if not np.isnan(v_prev) else 0) + \
                          (v_yoy*0.1 if not np.isnan(v_yoy) else 0)
                
                if final_v > 0:
                    forecast_table.at[c, d] = f"예상 {int(final_v)} / 권장 {int(final_v*1.15)}"
                else: forecast_table.at[c, d] = "-"
        
        st.dataframe(forecast_table, use_container_width=True)

        st.divider()
        st.subheader("3. ⏰ 요일별 피크타임 추이")
        selected_day = st.radio("상세 요일 선택", ["전체"] + day_order, horizontal=True)
        
        plot_df = df_h.copy()
        if selected_day != "전체": plot_df = plot_df[plot_df['요일'] == selected_day]
        
        fig_h = px.line(plot_df, x="결제시간대", y="판매량", color="요일", markers=True)
        if selected_day != "전체": fig_h.update_traces(fill='tozeroy', line_color='#0078D7')
        fig_h.update_layout(template='plotly_white', xaxis=dict(dtick=2))
        st.plotly_chart(fig_h, use_container_width=True)

    # --- TAB 3: 매출 흐름 요약 (일매출 및 판매율) ---
    with tab3:
        st.subheader("1. 당월 일별 FF 일매출 흐름")
        df_curr = df_s[df_s['기간'] == "당월"].groupby('일자')['일매출'].sum().reset_index()
        fig_day = px.bar(df_curr, x="일자", y="일매출", text_auto='.2s')
        fig_day.update_traces(marker_color='#0078D7', width=0.6)
        st.plotly_chart(fig_day, use_container_width=True)

        st.divider()
        st.subheader("2. 중분류별 판매율 (소진율)")
        st.caption("판매율(%) = (판매수량 / 입고수량) × 100")
        
        rate_df = df_s[df_s['기간'] == "당월"].groupby('중분류')[['입고수량', '판매수량']].sum().reset_index()
        rate_df['판매율'] = (rate_df['판매수량'] / rate_df['입고수량'] * 100).round(1)
        
        fig_rate = px.bar(rate_df, x="중분류", y="판매율", text=rate_df['판매율'].apply(lambda x: f"{x}%"))
        fig_rate.update_traces(marker_color='#4CAF50', width=0.4)
        fig_rate.update_layout(template='plotly_white', yaxis_title="판매율 (%)")
        st.plotly_chart(fig_rate, use_container_width=True)
