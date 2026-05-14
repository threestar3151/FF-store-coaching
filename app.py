import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, timedelta

# -----------------------------------------------------------------------------
# 1. 페이지 기본 설정 및 디자인 (세련된 스타일 추가)
# -----------------------------------------------------------------------------
st.set_page_config(page_title="GS25 FF 코칭 PRO MAX", page_icon="🏪", layout="wide")

st.markdown("""
<style>
    html, body, [class*="css"] { font-family: 'Pretendard', sans-serif; }
    /* 메트릭 카드 스타일 */
    div[data-testid="metric-container"] {
        background-color: #ffffff; border: 1px solid #f0f2f6;
        padding: 15px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    /* 탭 디자인 */
    button[data-baseweb="tab"] { font-weight: 700; color: #495057; }
</style>
""", unsafe_allow_html=True)

def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False
    if not st.session_state["password_correct"]:
        st.title("🔒 GS25 매출 코칭 대시보드")
        pwd = st.text_input("비밀번호 (GS25)", type="password")
        if st.button("로그인"):
            if pwd == "GS25":
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("❌ 비밀번호가 틀렸습니다.")
        return False
    return True

if not check_password():
    st.stop()

# -----------------------------------------------------------------------------
# 2. 데이터 로드 (항목명: 파트명, 현재코드, 점포유형, 일매출 적용)
# -----------------------------------------------------------------------------
@st.cache_data
def load_advanced_data():
    store_meta = {
        "상무본점": {"파트명": "김광주", "점포유형": "유흥가", "Power": 1.2},
        "첨단산단점": {"파트명": "이전라", "점포유형": "오피스", "Power": 1.3}
    }
    categories = ["도시락", "김밥", "주먹밥", "햄버거/샌드위치", "FF간편식"]
    days_kr = ["월", "화", "수", "목", "금", "토", "일"]
    today = datetime.today()

    daily_data = []
    hourly_data = []

    for store, meta in store_meta.items():
        periods = [("당월", 0), ("전월", 30), ("전년동월", 365)]
        for period_name, days_offset in periods:
            days_to_generate = 14 if period_name == "당월" else 30 
            for i in range(days_to_generate):
                d = today - timedelta(days=i + days_offset)
                for cat in categories:
                    base_inbound = int(np.random.randint(10, 30) * meta["Power"])
                    sales_qty = int(base_inbound * np.random.uniform(0.7, 0.95))
                    # '일매출' 필드로 생성
                    daily_rev = sales_qty * np.random.randint(3000, 5000)
                    
                    daily_data.append({
                        "일자": d.strftime("%Y-%m-%d"),
                        "기간": period_name,
                        "요일": days_kr[d.weekday()],
                        "점포명": store,
                        "점포유형": meta["점포유형"],
                        "중분류": cat,
                        "입고수량": base_inbound,
                        "판매수량": sales_qty,
                        "일매출": daily_rev
                    })
        # 시간대 데이터 생략 (동일 로직)
    return pd.DataFrame(daily_data), pd.DataFrame(), store_meta, categories

df_all_daily, _, store_meta, cat_list = load_advanced_data()

# -----------------------------------------------------------------------------
# 3. 사이드바 및 메인 레이아웃
# -----------------------------------------------------------------------------
st.sidebar.header("🔍 분석 조건")
part_list = list(set([meta["파트명"] for meta in store_meta.values()]))
selected_part = st.sidebar.selectbox("담당 파트명", part_list, index=None, placeholder="선택하세요")

if selected_part:
    store_list = [store for store, meta in store_meta.items() if meta["파트명"] == selected_part]
    selected_store = st.sidebar.selectbox("점포 선택", store_list, index=None, placeholder="점포명 검색")

# -----------------------------------------------------------------------------
# 4. 분석 리포트 화면
# -----------------------------------------------------------------------------
if not selected_part or not selected_store:
    st.info("👈 사이드바에서 조건을 선택해 주세요.")
else:
    df_store_all = df_all_daily[df_all_daily['점포명'] == selected_store]
    
    tab1, tab2, tab3 = st.tabs(["💡 발주/진열 코칭", "🏆 상권 베스트", "📈 요약"])

    with tab1:
        st.subheader("1. 📉 과거 FF 매출 흐름 (단위: 천원)")
        
        # 기간별 '일매출' 합계 계산 및 천원 단위 변환
        def get_rev_k(period):
            val = df_store_all[df_store_all['기간'] == period]['일매출'].sum()
            return val / 1000

        rev_df = pd.DataFrame({
            "구분": ["작년 동월", "전월 전체", "당월 누적"],
            "금액": [get_rev_k("전년동월"), get_rev_k("전월"), get_rev_k("당월")]
        })

        # ✨ 그래프를 세련되게 만들기 위한 레이아웃 조정 (중앙 배치)
        _, col_chart, _ = st.columns([0.15, 0.7, 0.15]) 
        
        with col_chart:
            fig_rev = px.bar(
                rev_df, x="구분", y="금액",
                text=rev_df['금액'].apply(lambda x: f"{x:,.0f}천원"),
                color="구분",
                color_discrete_map={"작년 동월": "#CED4DA", "전월 전체": "#ADB5BD", "당월 누적": "#0078D7"}
            )
            
            # ✨ 세련된 스타일링: 막대 너비 조절 및 디자인 정제
            fig_rev.update_traces(
                width=0.4, # 막대 너비를 슬림하게 (촌스러움 해소)
                textposition='outside',
                textfont_size=13,
                marker_line_width=0
            )
            
            fig_rev.update_layout(
                template='plotly_white',
                showlegend=False,
                margin=dict(l=20, r=20, t=50, b=20),
                plot_bgcolor='rgba(0,0,0,0)',
                yaxis=dict(showgrid=True, gridcolor='#F1F3F5', title="", showticklabels=False),
                xaxis=dict(title="", tickfont_size=14)
            )
            st.plotly_chart(fig_rev, use_container_width=True)

        st.divider()
        st.caption("※ '일매출' 데이터를 기반으로 천원 단위로 환산된 결과입니다.")
