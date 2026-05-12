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
# 2. 고급 가상 데이터 생성 (FF간편식 추가)
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
    
    # 카테고리 업데이트 (FF간편식 추가)
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
        for i in range(30):
            d = today - timedelta(days=i)
            day_str = days_kr[d.weekday()]
            
            for cat in categories:
                for prod in products[cat]:
                    base_inbound = int(np.random.randint(5, 20) * meta["Power"])
                    
                    if meta["Area"] == "오피스" and d.weekday() >= 5:
                        base_inbound = int(base_inbound * 0.3)
                        sales_qty = int(base_inbound * np.random.uniform(0.5, 0.9))
                    else:
                        sales_qty = int(base_inbound * np.random.uniform(0.7, 1.0))
                        
                    revenue = sales_qty * np.random.randint(2000, 5000)
                    
                    daily_data.append({
                        "Date": d.strftime("%Y-%m-%d"),
                        "DayOfWeek": day_str,
                        "Store": store,
                        "Area_Type": meta["Area"],
                        "Category": cat,
                        "Product": prod,
                        "Inbound": base_inbound,
                        "Sales_Qty": sales_qty,
                        "Revenue": revenue
                    })

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

df_daily, df_hourly, store_meta, cat_list = load_advanced_data()

# -----------------------------------------------------------------------------
# 3. 사이드바 (모바일 검색 UI 개선)
# -----------------------------------------------------------------------------
if st.sidebar.button("🔓 로그아웃"):
    st.session_state["password_correct"] = False
    st.rerun()

st.sidebar.header("🔍 분석 조건")
ofc_list = list(set([meta["OFC"] for meta in store_meta.values()]))

# index=None과 placeholder를 통해 모바일 터치 시 즉각적인 타이핑 유도
selected_ofc = st.sidebar.selectbox("담당 OFC", ofc_list, index=None, placeholder="터치하여 선택/검색")

if selected_ofc:
    store_list = [store for store, meta in store_meta.items() if meta["OFC"] == selected_ofc]
    selected_store = st.sidebar.selectbox("점포 선택", store_list, index=None, placeholder="점포명 검색/선택")

# -----------------------------------------------------------------------------
# 4. 메인 화면 
# -----------------------------------------------------------------------------
st.title("📊 GS25 데이터 기반 경영주 코칭 시스템")

if not selected_ofc or not selected_store:
    st.info("👈 사이드바에서 담당 OFC와 점포를 먼저 선택해 주세요.")
else:
    current_area = store_meta[selected_store]["Area"]
    
    # 데이터 필터링
    df_store = df_daily[df_daily['Store'] == selected_store]
    df_store_hour = df_hourly[df_hourly['Store'] == selected_store]
    df_area = df_daily[df_daily['Area_Type'] == current_area]

    # --- 핵심 코칭 메시지 상단 배치 ---
    st.markdown(f"### 📍 **{selected_store}** (상권: {current_area})")
    
    peak_hour_data = df_store_hour.groupby('Hour')['Traffic_Sales'].sum().reset_index()
    best_hour = peak_hour_data.loc[peak_hour_data['Traffic_Sales'].idxmax()]['Hour']
    best_cat = df_store.groupby('Category')['Sales_Qty'].sum().idxmax()
    
    st.success(f"🌟 **오늘의 핵심 코칭 포인트**\n\n"
               f"우리 점포는 현재 **[{best_cat}]** 카테고리의 고객 수요가 가장 높습니다. "
               f"하루 중 매출이 폭발하는 **{best_hour}시 ~ {best_hour+1}시** 이전에 결품이 나지 않도록, "
               f"늦어도 **{best_hour-1}시까지는 주력 FF 상품의 보충 진열을 100% 완료**해 최대 매출을 끌어내세요!")
    
    st.markdown("---")

    # 탭 구성
    tab1, tab2, tab3 = st.tabs(["💡 요일/시간별 코칭", "🏆 중분류 베스트 상품", "📈 기본 현황 요약"])

    # -------------------------------------------------------
    # TAB 1: 요일별 코칭 표 및 가로축 히트맵
    # -------------------------------------------------------
    with tab1:
        st.subheader("1. 📅 요일별 맞춤 발주 가이드")
        st.markdown("> 과거 판매 데이터를 기반으로 산출된 요일별 **목표 판매량** 및 **추천 발주량**입니다.")
        
        # 테이블 생성을 위한 데이터 피벗 가공
        day_order = ["월", "화", "수", "목", "금", "토", "일"]
        pivot_df = pd.DataFrame(index=cat_list, columns=day_order)
        
        for cat in cat_list:
            for day in day_order:
                subset = df_store[(df_store['Category'] == cat) & (df_store['DayOfWeek'] == day)]
                if not subset.empty:
                    avg_sales = subset['Sales_Qty'].mean()
                    rec_order = int(avg_sales * 1.1) # 기회로스 방지를 위해 판매량의 110%를 권장 발주로 설정
                    # 키워드 중심의 간결한 텍스트
                    pivot_df.at[cat, day] = f"판매 {avg_sales:.1f}개\n(발주 {rec_order}개)"
                else:
                    pivot_df.at[cat, day] = "-"
                    
        st.dataframe(pivot_df, use_container_width=True)

        st.divider()

        st.subheader("2. ⏰ 시간대별 집중도 (피크 타임)")
        st.markdown("> 모바일 환경에 맞춰 가로축을 요일로 배치했습니다. 색이 진할수록 고객 방문이 집중됩니다.")

        # 히트맵 x축, y축 변경 (x=요일, y=시간)
        df_store_hour['DayOfWeek'] = pd.Categorical(df_store_hour['DayOfWeek'], categories=day_order, ordered=True)
        fig_heat = px.density_heatmap(
            df_store_hour, 
            x="DayOfWeek", 
            y="Hour", 
            z="Traffic_Sales", 
            histfunc="sum",
            color_continuous_scale="Blues", # 판매/긍정을 상징하는 파란색 계열로 변경
        )
        # 세로축(시간)을 위에서 아래로(0~23) 자연스럽게 배치
        fig_heat.update_yaxes(autorange="reversed", tickmode='linear', tick0=0, dtick=2)
        st.plotly_chart(fig_heat, use_container_width=True)

    # -------------------------------------------------------
    # TAB 2: 중분류별 상권 베스트 상품
    # -------------------------------------------------------
    with tab2:
        st.subheader(f"[{current_area}] 상권 중분류별 1위 상품")
        st.markdown("> 상권 내에서 가장 잘 팔리는 카테고리별 핵심 상품입니다. 우리 점포의 매대에도 있는지 점검해 보세요.")
        
        # 카테고리(중분류)별로 상위 1개 상품 추출
        best_items = []
        for cat in cat_list:
            cat_df = df_area[df_area['Category'] == cat]
            if not cat_df.empty:
                top_item = cat_df.groupby('Product')['Sales_Qty'].sum().reset_index().sort_values(by='Sales_Qty', ascending=False).iloc[0]
                best_items.append({"중분류": cat, "1위 상품명": top_item['Product'], "상권 총 판매량": top_item['Sales_Qty']})
                
        best_item_df = pd.DataFrame(best_items)
        st.dataframe(best_item_df, use_container_width=True, hide_index=True)

    # -------------------------------------------------------
    # TAB 3: 요약 (기존 탭 축소 배치)
    # -------------------------------------------------------
    with tab3:
        tot_rev = df_store['Revenue'].sum()
        st.metric("최근 30일 FF 총 매출액", f"{tot_rev:,.0f}원")
        
        st.markdown("#### 카테고리별 매출 비중")
        fig_pie = px.pie(df_store, values='Revenue', names='Category', hole=0.4)
        st.plotly_chart(fig_pie, use_container_width=True)
