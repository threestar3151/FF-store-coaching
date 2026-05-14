import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, timedelta

# -----------------------------------------------------------------------------
# 1. 페이지 설정 및 디자인(CSS) 적용
# -----------------------------------------------------------------------------
st.set_page_config(page_title="GS25 FF 코칭 PRO MAX", page_icon="🏪", layout="wide")

st.markdown("""
<style>
    html, body, [class*="css"] { font-family: 'Pretendard', sans-serif; }
    div[data-testid="metric-container"] {
        background-color: #ffffff; border: 1px solid #e6e9ef;
        padding: 15px; border-radius: 12px; box-shadow: 0px 2px 10px rgba(0,0,0,0.05);
    }
    button[data-baseweb="tab"] { font-weight: 700; font-size: 16px !important; }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. 보안 로직 (비밀번호 힌트 제거)
# -----------------------------------------------------------------------------
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False
    
    if not st.session_state["password_correct"]:
        st.title("🔒 GS25 매출 코칭 시스템")
        # 비밀번호 힌트 없이 깔끔한 입력창 유지
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
# 3. 데이터 로드 로직 (항목명 준수: 파트명, 현재코드, 점포유형, 일매출)
# -----------------------------------------------------------------------------
@st.cache_data
def load_data():
    store_meta = {
        "상무본점": {"파트명": "영업1팀", "점포유형": "유흥가", "현재코드": "25001"},
        "첨단산단점": {"파트명": "영업2팀", "점포유형": "오피스", "현재코드": "25002"},
        "수완지구점": {"파트명": "영업1팀", "점포유형": "주택가", "현재코드": "25003"}
    }
    categories = ["도시락", "김밥", "주먹밥", "햄버거/샌드위치", "FF간편식"]
    products = {
        "도시락": ["혜자로운집밥", "정통커리도시락", "고기진짜많구나"],
        "김밥": ["참치김밥", "불고기김밥", "야채김밥"],
        "주먹밥": ["참치마요삼각", "전주비빔삼각", "소고기볶음고추장"],
        "햄버거/샌드위치": ["에그마요샌드", "불고기버거", "듬뿍햄샌드"],
        "FF간편식": ["위대한떡볶이", "더큰반반닭강정", "떠먹는피자"]
    }
    days_kr = ["월", "화", "수", "목", "금", "토", "일"]
    today = datetime.today()

    daily_records = []
    hourly_records = []

    for store, meta in store_meta.items():
        for period, offset in [("당월", 0), ("전월", 30), ("전년동월", 365)]:
            days = 14 if period == "당월" else 30
            for i in range(days):
                dt = today - timedelta(days=i + offset)
                for cat in categories:
                    for prod in products[cat]:
                        inbound = np.random.randint(10, 40)
                        sales = int(inbound * np.random.uniform(0.7, 0.95))
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
                            "상품명": prod,
                            "입고수량": inbound,
                            "판매수량": sales,
                            "일매출": revenue
                        })
        for day in days_kr:
            for hr in range(24):
                hourly_records.append({
                    "점포명": store, "요일": day, "결제시간대": hr,
                    "판매량": np.random.randint(5, 50)
                })

    return pd.DataFrame(daily_records), pd.DataFrame(hourly_records), store_meta

df_daily_all, df_hourly, store_meta = load_data()

# -----------------------------------------------------------------------------
# 4. 사이드바 검색
# -----------------------------------------------------------------------------
st.sidebar.header("🔍 분석 조건")
part_list = sorted(list(set(df_daily_all['파트명'])))
selected_part = st.sidebar.selectbox("담당 파트명", part_list, index=None, placeholder="파트 선택/검색")

selected_store = None
if selected_part:
    stores_in_part = sorted(list(set(df_daily_all[df_daily_all['파트명'] == selected_part]['점포명'])))
    selected_store = st.sidebar.selectbox("점포 선택", stores_in_part, index=None, placeholder="점포명 선택/검색")

# -----------------------------------------------------------------------------
# 5. 메인 리포트 화면
# -----------------------------------------------------------------------------
st.title("📊 GS25 현장 맞춤형 코칭 리포트")

if not selected_part or not selected_store:
    st.info("👈 왼쪽 사이드바에서 파트와 점포를 선택해 주세요.")
else:
    # 데이터 필터링 (기간별 분리)
    df_s_all = df_daily_all[df_daily_all['점포명'] == selected_store]
    df_s_curr = df_s_all[df_s_all['기간'] == "당월"]
    current_area = store_meta[selected_store]["점포유형"]

    # 상단 분석 기간 출력
    st.markdown("##### 🗓️ 분석 기준 기간")
    p_cols = st.columns(3)
    for i, p in enumerate(["당월", "전월", "전년동월"]):
        temp = df_s_all[df_s_all['기간'] == p]
        if not temp.empty:
            p_cols[i].caption(f"**{p}**: {temp['일자'].min()} ~ {temp['일자'].max()}")
        else:
            p_cols[i].caption(f"**{p}**: 데이터 없음")
    
    st.markdown("---")

    # 탭 구성
    tab1, tab2, tab3 = st.tabs(["💡 발주/진열 코칭", "🏆 상권 베스트", "📈 매출 흐름 요약"])

    # --- TAB 1: 코칭 및 시간대 ---
    with tab1:
        if df_s_all.empty:
            st.error("해당 점포의 과거 실적 데이터가 없습니다.")
        else:
            st.subheader("1. 📉 과거 FF 매출 흐름 (단위: 천원)")
            def get_k_rev(p): return df_s_all[df_s_all['기간'] == p]['일매출'].sum() / 1000
            rev_data = pd.DataFrame({
                "구분": ["작년 동월", "전월 전체", "당월 누적"],
                "금액": [get_k_rev("전년동월"), get_k_rev("전월"), get_k_rev("당월")]
            })
            _, chart_col, _ = st.columns([0.1, 0.8, 0.1])
            with chart_col:
                fig_rev = px.bar(rev_data, x="구분", y="금액", text=rev_data['금액'].apply(lambda x: f"{x:,.0f}k"),
                                color="구분", color_discrete_map={"작년 동월":"#DEE2E6", "전월 전체":"#ADB5BD", "당월 누적":"#0078D7"})
                fig_rev.update_traces(width=0.4, textposition='outside')
                fig_rev.update_layout(template='plotly_white', showlegend=False, yaxis_visible=False, height=350)
                st.plotly_chart(fig_rev, use_container_width=True)

    # --- TAB 2: 상권 베스트 (문제 해결 핵심 부분) ---
    with tab2:
        st.subheader(f"🏆 [{current_area}] 상권 베스트 상품 점검")
        # 상권 전체(동일 유형) 데이터 필터링
        df_area = df_daily_all[(df_daily_all['점포유형'] == current_area) & (df_daily_all['기간'] == "당월")]
        
        if df_area.empty:
            st.warning("상권 유형에 맞는 당월 데이터가 존재하지 않습니다.")
        else:
            best_items = []
            for cat in sorted(list(set(df_area['중분류']))):
                cat_df = df_area[df_area['중분류'] == cat]
                top_item_row = cat_df.groupby('상품명')['판매수량'].sum().reset_index().sort_values(by='판매수량', ascending=False).iloc[0]
                item_name = top_item_row['상품명']
                
                # 우리 점포 취급 현황 확인
                my_item = df_s_curr[df_s_curr['상품명'] == item_name]
                inbound = int(my_item['입고수량'].sum()) if not my_item.empty else 0
                sales = int(my_item['판매수량'].sum()) if not my_item.empty else 0
                
                best_items.append({
                    "분류": cat, "상권 1위 상품": item_name,
                    "우리점포 입고": inbound, "우리점포 판매": sales,
                    "상태": "🟢 취급중" if inbound > 0 else "🔴 미취급"
                })
            
            if best_items:
                st.table(pd.DataFrame(best_items))
            else:
                st.write("분석할 상품 데이터가 없습니다.")

    # --- TAB 3: 매출 요약 ---
    with tab3:
        if df_s_curr.empty:
            st.warning("당월 매출 데이터가 없습니다.")
        else:
            st.subheader("1. 당월 일별 FF 일매출 흐름")
            df_plot = df_s_curr.groupby('일자')['일매출'].sum().reset_index()
            fig_day = px.bar(df_plot, x="일자", y="일매출", text_auto='.2s')
            fig_day.update_traces(marker_color='#0078D7', width=0.6)
            st.plotly_chart(fig_day, use_container_width=True)
