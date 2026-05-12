import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, timedelta

# -----------------------------------------------------------------------------
# 1. 페이지 기본 설정 및 비밀번호 로직
# -----------------------------------------------------------------------------
st.set_page_config(page_title="GS25 FF 코칭 PRO MAX", page_icon="🏪", layout="wide")

def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False
    if not st.session_state["password_correct"]:
        st.title("🔒 GS25 매출 코칭 대시보드")
        pwd = st.text_input("비밀번호를 입력하세요 (GS25)", type="password")
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
# 2. 고급 가상 데이터 생성 (요일, 시간대, 폐기율 포함)
# -----------------------------------------------------------------------------
@st.cache_data
def load_advanced_data():
    store_meta = {
        "상무본점": {"OFC": "김광주", "Area": "유흥가", "Power": 1.2},
        "충장로중앙점": {"OFC": "김광주", "Area": "상업지", "Power": 1.5},
        "수완지구점": {"OFC": "김광주", "Area": "주택가", "Power": 0.8},
        "첨단산단점": {"OFC": "이전라", "Area": "오피스", "Power": 1.3},
        "금남로4가점": {"OFC": "이전라", "Area": "오피스", "Power": 0.9},
        "광천터미널점": {"OFC": "이전라", "Area": "상업지", "Power": 1.8}
    }
    categories = ["도시락", "주먹밥", "김밥", "샌드위치/햄버거"]
    days_kr = ["월", "화", "수", "목", "금", "토", "일"]
    today = datetime.today()

    daily_data = []
    hourly_data = [] # 시간대별 매출 분석을 위한 별도 데이터셋

    for store, meta in store_meta.items():
        # 1. 일별/카테고리별 데이터 (최근 30일)
        for i in range(30):
            d = today - timedelta(days=i)
            day_str = days_kr[d.weekday()]
            
            for cat in categories:
                # 오피스는 주말(토,일)에 발주/판매 급감, 주택가는 주말 유지 등 상권 로직
                is_weekend = d.weekday() >= 5
                base_inbound = int(np.random.randint(10, 30) * meta["Power"])
                
                if meta["Area"] == "오피스" and is_weekend:
                    base_inbound = int(base_inbound * 0.3)
                    # 오피스 주말에 평일처럼 발주하면 폐기가 늘어나는 로직
                    sales_qty = int(base_inbound * np.random.uniform(0.3, 0.6)) 
                elif meta["Area"] == "주택가" and is_weekend:
                    base_inbound = int(base_inbound * 1.2)
                    sales_qty = int(base_inbound * np.random.uniform(0.8, 1.0))
                else:
                    sales_qty = int(base_inbound * np.random.uniform(0.7, 0.95))
                
                waste_qty = base_inbound - sales_qty
                revenue = sales_qty * np.random.randint(2000, 5000)
                
                daily_data.append({
                    "Date": d.strftime("%Y-%m-%d"),
                    "DayOfWeek": day_str,
                    "Store": store,
                    "Area_Type": meta["Area"],
                    "Category": cat,
                    "Inbound": base_inbound,
                    "Sales_Qty": sales_qty,
                    "Waste_Qty": waste_qty,
                    "Revenue": revenue
                })

        # 2. 시간대별 데이터 (히트맵용 - 패턴화된 가상 데이터)
        for day_idx, day_str in enumerate(days_kr):
            for hour in range(24):
                traffic = np.random.randint(1, 10)
                is_weekend = day_idx >= 5
                
                # 피크타임 설정
                if meta["Area"] == "오피스" and not is_weekend and (11 <= hour <= 13):
                    traffic += np.random.randint(30, 50) # 오피스 평일 점심 피크
                elif meta["Area"] == "오피스" and not is_weekend and (17 <= hour <= 19):
                    traffic += np.random.randint(15, 25) # 퇴근 시간 약간
                elif meta["Area"] == "주택가" and is_weekend and (18 <= hour <= 22):
                    traffic += np.random.randint(30, 60) # 주택가 주말 저녁 야식 피크
                elif meta["Area"] == "유흥가" and (20 <= hour <= 23 or 0 <= hour <= 2):
                    traffic += np.random.randint(40, 70) # 유흥가 심야 피크
                    
                hourly_data.append({
                    "Store": store,
                    "DayOfWeek": day_str,
                    "Hour": hour,
                    "Traffic_Sales": traffic
                })

    return pd.DataFrame(daily_data), pd.DataFrame(hourly_data), store_meta

df_daily, df_hourly, store_meta = load_advanced_data()

# -----------------------------------------------------------------------------
# 3. 사이드바 
# -----------------------------------------------------------------------------
if st.sidebar.button("🔓 로그아웃"):
    st.session_state["password_correct"] = False
    st.rerun()

st.sidebar.header("🔍 분석 조건")
ofc_list = list(set([meta["OFC"] for meta in store_meta.values()]))
selected_ofc = st.sidebar.selectbox("담당 OFC 선택", ["선택하세요"] + ofc_list)

if selected_ofc != "선택하세요":
    store_list = [store for store, meta in store_meta.items() if meta["OFC"] == selected_ofc]
    selected_store = st.sidebar.selectbox("점포 선택", ["선택하세요"] + store_list)

# -----------------------------------------------------------------------------
# 4. 메인 화면 
# -----------------------------------------------------------------------------
st.title("📊 GS25 데이터 기반 경영주 코칭 시스템")

if selected_ofc == "선택하세요" or 'selected_store' not in locals() or selected_store == "선택하세요":
    st.info("👈 사이드바에서 담당 OFC와 점포를 선택하시면 분석이 시작됩니다.")
else:
    current_area = store_meta[selected_store]["Area"]
    st.markdown(f"### 📍 **{selected_store}** (상권: {current_area} / 담당: {selected_ofc})")
    
    # 점포별 데이터 필터링
    df_store = df_daily[df_daily['Store'] == selected_store]
    df_store_hour = df_hourly[df_hourly['Store'] == selected_store]

    # 탭 구성 (4번 탭 추가)
    tab1, tab2, tab3, tab4 = st.tabs(["📈 기간별 요약", "🏘️ 유사 상권 비교", "🏆 카테고리 분석", "💡 발주 및 진열 코칭"])

    # --- TAB 1, 2, 3은 기존 로직과 유사하게 요약 처리 (지면상 간단히 배치) ---
    with tab1:
        st.subheader("매출 및 폐기 요약 (최근 30일)")
        tot_rev = df_store['Revenue'].sum()
        tot_waste = df_store['Waste_Qty'].sum()
        st.metric("총 FF 매출액", f"{tot_rev:,.0f}원")
        st.metric("총 폐기 수량", f"{tot_waste:,.0f}개")
        st.info("상세 분석은 오른쪽 탭들을 클릭하여 확인하세요.")

    with tab2:
        st.subheader(f"[{current_area}] 상권 점포들과의 정밀 비교")
        df_area = df_daily[df_daily['Area_Type'] == current_area]
        fig_comp = px.box(df_area, x="Store", y="Revenue", title="상권 내 점포별 매출 분포 비교", color="Store")
        st.plotly_chart(fig_comp, use_container_width=True)

    with tab3:
        st.subheader("카테고리별 매출 비중")
        fig_pie = px.pie(df_store, values='Revenue', names='Category', hole=0.4)
        st.plotly_chart(fig_pie, use_container_width=True)

    # -------------------------------------------------------
    # TAB 4: 요일별 폐기 분석 및 시간대별 피크타임 (핵심 추가 기능)
    # -------------------------------------------------------
    with tab4:
        st.subheader("1. 📉 요일별 폐기 로스(Loss) 분석 및 발주 가이드")
        st.markdown("> 프레시푸드(FF)는 무조건 많이 발주하는 것보다 **버리는 것을 줄이는 것이 이익률의 핵심**입니다.")
        
        # 요일/카테고리별 평균 폐기량 계산
        day_order = ["월", "화", "수", "목", "금", "토", "일"]
        df_waste = df_store.groupby(['DayOfWeek', 'Category'])['Waste_Qty'].mean().reset_index()
        df_waste['DayOfWeek'] = pd.Categorical(df_waste['DayOfWeek'], categories=day_order, ordered=True)
        df_waste = df_waste.sort_values(['DayOfWeek', 'Category'])

        # 폐기 코칭 로직 (평균 폐기가 3개 이상인 요일/카테고리 색출)
        coaching_msgs = []
        for index, row in df_waste.iterrows():
            if row['Waste_Qty'] >= 3:
                reduce_qty = int(row['Waste_Qty'] * 0.8) # 폐기량의 80% 정도 감축 권장
                coaching_msgs.append(f"⚠️ **{row['DayOfWeek']}요일**에는 평균적으로 **[{row['Category']}]** 카테고리에서 **{row['Waste_Qty']:.1f}개**의 폐기가 발생하고 있습니다. ➡️ **발주를 {reduce_qty}개 정도 줄여보시는 것을 권장**합니다.")

        # 코칭 메시지 출력
        if coaching_msgs:
            for msg in coaching_msgs:
                st.warning(msg)
        else:
            st.success("🌟 현재 모든 요일과 카테고리에서 폐기 관리가 매우 우수하게 이루어지고 있습니다!")

        # 요일별 폐기 추이 차트
        fig_waste_day = px.bar(df_waste, x="DayOfWeek", y="Waste_Qty", color="Category", 
                               title="요일별/카테고리별 평균 폐기 수량", barmode='group')
        st.plotly_chart(fig_waste_day, use_container_width=True)

        st.divider()

        st.subheader("2. ⏰ 시간대별/요일별 매출 피크타임 분석 (진열 가이드)")
        st.markdown(f"> 우리 점포({current_area} 상권)의 시간대별 고객 방문 패턴입니다. **피크 타임 1~2시간 전에 FF 매대 진열을 100% 완료**해야 합니다.")

        # 시간대별 히트맵 (Heatmap)
        df_store_hour['DayOfWeek'] = pd.Categorical(df_store_hour['DayOfWeek'], categories=day_order, ordered=True)
        fig_heat = px.density_heatmap(
            df_store_hour, 
            x="Hour", 
            y="DayOfWeek", 
            z="Traffic_Sales", 
            histfunc="sum",
            color_continuous_scale="Reds",
            title="🔥 우리 점포 시간대별 매출 집중도 (붉을수록 높음)",
            labels={"Hour": "시간대 (0~23시)", "DayOfWeek": "요일", "Traffic_Sales": "매출 볼륨"}
        )
        # x축을 1시간 단위로 모두 표시
        fig_heat.update_layout(xaxis=dict(tickmode='linear', tick0=0, dtick=1))
        st.plotly_chart(fig_heat, use_container_width=True)
        
        # 피크타임 텍스트 코칭 추출 로직
        peak_hour_data = df_store_hour.groupby('Hour')['Traffic_Sales'].sum().reset_index()
        best_hour = peak_hour_data.loc[peak_hour_data['Traffic_Sales'].idxmax()]['Hour']
        st.success(f"🎯 **진열 코칭:** 우리 점포의 하루 중 매출이 가장 폭발하는 시간대는 **{best_hour}시 ~ {best_hour+1}시** 사이입니다! "
                   f"늦어도 **{best_hour-1}시까지는 도시락과 김밥 등 주력 FF 상품의 보충 진열과 검수를 완벽히 끝내어 기회 로스를 잡으세요.**")
