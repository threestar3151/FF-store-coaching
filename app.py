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
# 2. 고급 가상 데이터 생성 (전년/전월 데이터 및 일매출 포함)
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

    daily_data = []
    hourly_data = []

    for store, meta in store_meta.items():
        # 당월(Current), 전월(MoM), 전년동월(YoY) 30일치 데이터 생성
        periods = [
            ("당월", 0),
            ("전월", 30),
            ("전년동월", 365)
        ]
        
        for period_name, days_offset in periods:
            for i in range(30):
                d = today - timedelta(days=i + days_offset)
                day_str = days_kr[d.weekday()]
                
                for cat in categories:
                    for prod in products[cat]:
                        base_inbound = int(np.random.randint(5, 20) * meta["Power"])
                        
                        # 전월, 전년동월은 약간의 랜덤 증감치 부여
                        if period_name == "전월": base_inbound = int(base_inbound * 0.95)
                        if period_name == "전년동월": base_inbound = int(base_inbound * 0.85)

                        if meta["Area"] == "오피스" and d.weekday() >= 5:
                            base_inbound = int(base_inbound * 0.3)
                            sales_qty = int(base_inbound * np.random.uniform(0.5, 0.9))
                        else:
                            sales_qty = int(base_inbound * np.random.uniform(0.7, 1.0))
                            
                        revenue = sales_qty * np.random.randint(2000, 5000)
                        
                        daily_data.append({
                            "Date": d.strftime("%Y-%m-%d"),
                            "Period": period_name,
                            "DayOfWeek": day_str,
                            "Store": store,
                            "Area_Type": meta["Area"],
                            "Category": cat,
                            "Product": prod,
                            "Inbound": base_inbound,
                            "Sales_Qty": sales_qty,
                            "Revenue": revenue
                        })

        # 시간대 데이터는 당월 트렌드 파악을 위해 당월만 생성
        for day_idx, day_str in enumerate(days_kr):
            for hour in range(24):
                traffic = np.random.randint(1, 10)
                is_weekend = day_idx >= 5
                
                if meta["Area"] == "오피스" and not is_weekend and (11 <= hour <= 13):
                    traffic += np.random.randint(30, 50)
                elif meta["Area"] == "주택가" and is_weekend and (18 <= hour <= 22):
                    traffic += np.random.randint(30, 60)
                elif meta["Area"] == "유흥가" and (20 <= hour <= 23 or 0 <= hour <= 2):
                    traffic += np.random.randint(40, 70)
                    
                hourly_data.append({
                    "Store": store,
                    "DayOfWeek": day_str,
                    "Hour": hour,
                    "Traffic_Sales": traffic
                })

    return pd.DataFrame(daily_data), pd.DataFrame(hourly_data), store_meta, categories

df_all_daily, df_hourly, store_meta, cat_list = load_advanced_data()
df_daily = df_all_daily[df_all_daily['Period'] == '당월'] # 대부분의 분석은 당월 기준

# -----------------------------------------------------------------------------
# 3. 사이드바 
# -----------------------------------------------------------------------------
if st.sidebar.button("🔓 로그아웃"):
    st.session_state["password_correct"] = False
    st.rerun()

st.sidebar.header("🔍 분석 조건")
ofc_list = list(set([meta["OFC"] for meta in store_meta.values()]))
selected_ofc = st.sidebar.selectbox("담당 OFC", ofc_list, index=None, placeholder="터치하여 선택/검색")

if selected_ofc:
    store_list = [store for store, meta in store_meta.items() if meta["OFC"] == selected_ofc]
    selected_store = st.sidebar.selectbox("점포 선택", store_list, index=None, placeholder="점포명 검색/선택")

# -----------------------------------------------------------------------------
# 4. 메인 화면 
# -----------------------------------------------------------------------------
st.title("📊 GS25 현장 맞춤형 코칭 리포트")

if not selected_ofc or not selected_store:
    st.info("👈 사이드바에서 담당 OFC와 점포를 먼저 선택해 주세요.")
else:
    current_area = store_meta[selected_store]["Area"]
    
    # 선택 점포 데이터 필터링
    df_store = df_daily[df_daily['Store'] == selected_store]
    df_store_hour = df_hourly[df_hourly['Store'] == selected_store]
    df_area = df_daily[df_daily['Area_Type'] == current_area]

    st.markdown(f"### 📍 **{selected_store}** (상권: {current_area})")
    
    # 핵심 코칭 포인트 추출
    peak_hour_data = df_store_hour.groupby('Hour')['Traffic_Sales'].sum().reset_index()
    best_hour = peak_hour_data.loc[peak_hour_data['Traffic_Sales'].idxmax()]['Hour']
    best_cat = df_store.groupby('Category')['Sales_Qty'].sum().idxmax()
    
    st.success(f"🌟 **오늘의 핵심 액션 플랜**\n\n"
               f"우리 점포 매출의 일등 공신은 **[{best_cat}]** 카테고리입니다! "
               f"가장 손님이 붐비는 시간대인 **{best_hour}시 ~ {best_hour+1}시** 이전에 결품이 나지 않도록, "
               f"**{best_hour-1}시까지는 주력 상품의 보충 진열을 100% 완료**해 주세요.")
    
    st.markdown("---")

    # 탭 구성
    tab1, tab2, tab3 = st.tabs(["💡 발주/진열 코칭", "🏆 상권 베스트 점검", "📈 매출 흐름 요약"])

    # -------------------------------------------------------
    # TAB 1: 요일별 발주 표 및 피크타임 (전년/전월 비교 포함)
    # -------------------------------------------------------
    with tab1:
        st.subheader("1. 📉 과거 FF 매출 흐름 (최근 30일)")
        # 전년/전월 데이터 필터링 및 합산
        df_store_all = df_all_daily[df_all_daily['Store'] == selected_store]
        curr_rev = df_store_all[df_store_all['Period'] == '당월']['Revenue'].sum()
        mom_rev = df_store_all[df_store_all['Period'] == '전월']['Revenue'].sum()
        yoy_rev = df_store_all[df_store_all['Period'] == '전년동월']['Revenue'].sum()
        
        col1, col2, col3 = st.columns(3)
        col1.metric("최근 30일 매출액", f"{curr_rev:,.0f}원")
        col2.metric("전월 동기 대비", f"{mom_rev:,.0f}원", f"{(curr_rev - mom_rev) / mom_rev * 100:.1f}%" if mom_rev else "0%")
        col3.metric("작년 동월 대비", f"{yoy_rev:,.0f}원", f"{(curr_rev - yoy_rev) / yoy_rev * 100:.1f}%" if yoy_rev else "0%")

        st.divider()

        st.subheader("2. 📅 직관적 요일별 맞춤 발주")
        st.markdown("> 최근 한 달 데이터를 분석한 목표치입니다. **(판=평균 판매량 / 발=권장 발주량)**")
        
        # 모바일 가독성을 극대화한 테이블 (소수점 제거 및 글자수 압축)
        day_order = ["월", "화", "수", "목", "금", "토", "일"]
        pivot_df = pd.DataFrame(index=cat_list, columns=day_order)
        
        for cat in cat_list:
            for day in day_order:
                subset = df_store[(df_store['Category'] == cat) & (df_store['DayOfWeek'] == day)]
                if not subset.empty:
                    avg_sales = int(subset['Sales_Qty'].mean())
                    rec_order = int(avg_sales * 1.15) # 발주량은 평균 판매의 115%로 세팅 (안전 재고)
                    pivot_df.at[cat, day] = f"판 {avg_sales} / 발 {rec_order}"
                else:
                    pivot_df.at[cat, day] = "-"
                    
        st.dataframe(pivot_df, use_container_width=True)

        st.divider()

        st.subheader("3. ⏰ 요일별 진열 마지노선 (피크 타임)")
        
        # 요일별 피크타임 키워드 추출
        peak_texts = []
        for day in day_order:
            day_data = df_store_hour[df_store_hour['DayOfWeek'] == day]
            if not day_data.empty:
                peak_hr = day_data.loc[day_data['Traffic_Sales'].idxmax()]['Hour']
                peak_texts.append(f"**{day}요일**: {peak_hr}시")
        
        st.info("📌 **요일별 매출 집중 시간대:** " + " | ".join(peak_texts))
        
        # 히트맵 (가로축: 요일, 세로축: 시간)
        df_store_hour['DayOfWeek'] = pd.Categorical(df_store_hour['DayOfWeek'], categories=day_order, ordered=True)
        fig_heat = px.density_heatmap(
            df_store_hour, x="DayOfWeek", y="Hour", z="Traffic_Sales", 
            histfunc="sum", color_continuous_scale="Blues", labels={"Traffic_Sales":"매출"}
        )
        fig_heat.update_yaxes(autorange="reversed", tickmode='linear', tick0=0, dtick=2)
        fig_heat.update_layout(margin=dict(l=0, r=0, t=30, b=0)) # 모바일 여백 최소화
        st.plotly_chart(fig_heat, use_container_width=True)

    # -------------------------------------------------------
    # TAB 2: 베스트 상품 우리 점포 취급 현황
    # -------------------------------------------------------
    with tab2:
        st.subheader(f"[{current_area}] 상권 베스트 상품 크로스체크")
        st.markdown("> 유사 상권에서 가장 잘 팔리는 상품이 우리 점포에도 들어오고 있는지 확인하세요.")
        
        best_items = []
        for cat in cat_list:
            cat_df = df_area[df_area['Category'] == cat]
            if not cat_df.empty:
                top_item = cat_df.groupby('Product')['Sales_Qty'].sum().reset_index().sort_values(by='Sales_Qty', ascending=False).iloc[0]
                item_name = top_item['Product']
                area_sales = top_item['Sales_Qty']
                
                # 우리 점포의 해당 상품 입고/판매 합계 구하기
                my_item_df = df_store[df_store['Product'] == item_name]
                if not my_item_df.empty:
                    my_inbound = int(my_item_df['Inbound'].sum())
                    my_sales = int(my_item_df['Sales_Qty'].sum())
                else:
                    my_inbound = 0
                    my_sales = 0
                    
                best_items.append({
                    "분류": cat, 
                    "상품명": item_name, 
                    "상권 판매": area_sales,
                    "우리점포 입고": my_inbound,
                    "우리점포 판매": my_sales,
                    "상태": "🟢취급중" if my_inbound > 0 else "🔴미취급"
                })
                
        best_item_df = pd.DataFrame(best_items)
        st.dataframe(best_item_df, use_container_width=True, hide_index=True)
        st.warning("☝️ **'🔴미취급'** 상태인 상품이 있다면 다음 발주 시 꼭 추가해 상권의 수요를 흡수해 보세요!")

    # -------------------------------------------------------
    # TAB 3: 일매출 흐름 요약
    # -------------------------------------------------------
    with tab3:
        st.subheader("최근 30일 FF 일매출 추이")
        
        # 날짜별 매출 합계 계산
        daily_trend = df_store.groupby('Date')['Revenue'].sum().reset_index()
        daily_trend = daily_trend.sort_values(by='Date')
        
        avg_daily = daily_trend['Revenue'].mean()
        st.metric("일평균 FF 매출", f"{avg_daily:,.0f}원")
        
        # 일매출 Bar Chart
        fig_bar = px.bar(
            daily_trend, x="Date", y="Revenue", 
            text_auto='.2s', # 막대 위에 단위 줄여서 금액 표시
            labels={"Revenue": "매출액 (원)", "Date": "날짜"}
        )
        fig_bar.update_traces(textposition='outside')
        fig_bar.update_layout(margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig_bar, use_container_width=True)
