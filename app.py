import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, timedelta

# -----------------------------------------------------------------------------
# 1. 페이지 기본 설정 및 디자인
# -----------------------------------------------------------------------------
st.set_page_config(page_title="GS25 FF 코칭 PRO MAX", page_icon="🏪", layout="wide")

st.markdown("""
<style>
    html, body, [class*="css"] { font-family: 'Pretendard', 'Apple SD Gothic Neo', sans-serif; }
    div[data-testid="metric-container"] {
        background-color: #ffffff; border: 1px solid #e6e9ef;
        padding: 20px; border-radius: 15px; box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.05);
        transition: transform 0.2s;
    }
    div[data-testid="metric-container"]:hover { transform: translateY(-2px); }
    button[data-baseweb="tab"] { font-weight: 600; font-size: 16px !important; }
    thead tr th { background-color: #f1f3f5 !important; color: #212529 !important; font-weight: bold !important; }
</style>
""", unsafe_allow_html=True)

def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False
    if not st.session_state["password_correct"]:
        st.title("🔒 GS25 매출 코칭 대시보드")
        pwd = st.text_input(type="password")
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
# 2. 가상 데이터 생성 
# -----------------------------------------------------------------------------
@st.cache_data
def load_advanced_data():
    store_meta = {
        "상무본점": {"파트명": "김광주", "점포유형": "유흥가", "Power": 1.2},
        "충장로중앙점": {"파트명": "김광주", "점포유형": "상업지", "Power": 1.5},
        "수완지구점": {"파트명": "김광주", "점포유형": "주택가", "Power": 0.8},
        "첨단산단점": {"파트명": "이전라", "점포유형": "오피스", "Power": 1.3},
        "금남로4가점": {"파트명": "이전라", "점포유형": "오피스", "Power": 0.9},
        "광천터미널점": {"파트명": "이전라", "점포유형": "상업지", "Power": 1.8}
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
        periods = [("당월", 0), ("전월", 30), ("전년동월", 365)]
        for period_name, days_offset in periods:
            days_to_generate = 14 if period_name == "당월" else 30 
            
            for i in range(days_to_generate):
                d = today - timedelta(days=i + days_offset)
                day_str = days_kr[d.weekday()]
                
                for cat in categories:
                    for prod in products[cat]:
                        base_inbound = int(np.random.randint(5, 20) * meta["Power"])
                        if period_name == "전월": base_inbound = int(base_inbound * 0.95)
                        if period_name == "전년동월": base_inbound = int(base_inbound * 0.85)

                        if meta["점포유형"] == "오피스" and d.weekday() >= 5:
                            base_inbound = int(base_inbound * 0.3)
                            sales_qty = int(base_inbound * np.random.uniform(0.5, 0.9))
                        else:
                            sales_qty = int(base_inbound * np.random.uniform(0.7, 1.0))
                            
                        daily_rev = sales_qty * np.random.randint(2000, 5000)
                        
                        daily_data.append({
                            "일자": d.strftime("%Y-%m-%d"),
                            "기간": period_name,
                            "요일": day_str,
                            "점포명": store,
                            "점포유형": meta["점포유형"],
                            "중분류": cat,
                            "상품명": prod,
                            "입고수량": base_inbound,
                            "판매수량": sales_qty,
                            "일매출": daily_rev
                        })

        for day_idx, day_str in enumerate(days_kr):
            for hour in range(24):
                traffic = np.random.randint(1, 10)
                is_weekend = day_idx >= 5
                if meta["점포유형"] == "오피스" and not is_weekend and (11 <= hour <= 13):
                    traffic += np.random.randint(30, 50)
                elif meta["점포유형"] == "주택가" and is_weekend and (18 <= hour <= 22):
                    traffic += np.random.randint(30, 60)
                elif meta["점포유형"] == "유흥가" and (20 <= hour <= 23 or 0 <= hour <= 2):
                    traffic += np.random.randint(40, 70)
                    
                hourly_data.append({
                    "점포명": store,
                    "요일": day_str,
                    "결제시간대": hour,
                    "판매량": traffic
                })

    return pd.DataFrame(daily_data), pd.DataFrame(hourly_data), store_meta, categories

df_all_daily, df_hourly, store_meta, cat_list = load_advanced_data()
df_daily = df_all_daily[df_all_daily['기간'] == '당월'] 

# -----------------------------------------------------------------------------
# 3. 사이드바
# -----------------------------------------------------------------------------
if st.sidebar.button("🔓 로그아웃"):
    st.session_state["password_correct"] = False
    st.rerun()

st.sidebar.header("🔍 분석 조건")
part_list = list(set([meta["파트명"] for meta in store_meta.values()]))
selected_part = st.sidebar.selectbox("담당 파트명", part_list, index=None, placeholder="터치하여 선택/검색")

if selected_part:
    store_list = [store for store, meta in store_meta.items() if meta["파트명"] == selected_part]
    selected_store = st.sidebar.selectbox("점포 선택", store_list, index=None, placeholder="점포명 검색/선택")

# -----------------------------------------------------------------------------
# 4. 메인 화면 
# -----------------------------------------------------------------------------
st.title("📊 GS25 현장 맞춤형 코칭 리포트")

if not df_all_daily.empty:
    st.markdown("##### 🗓️ 데이터 분석 기준 기간")
    col_p1, col_p2, col_p3 = st.columns(3)
    
    def get_period_str(df, period_name):
        temp = df[df['기간'] == period_name]
        if not temp.empty:
            return f"{temp['일자'].min()} ~ {temp['일자'].max()}"
        return "데이터 없음"

    col_p1.info(f"**🟦 당월 누적 (1일~D-1):**\n\n{get_period_str(df_all_daily, '당월')}")
    col_p2.info(f"**⬜ 전월 전체:**\n\n{get_period_str(df_all_daily, '전월')}")
    col_p3.info(f"**⬜ 전년 동월 전체:**\n\n{get_period_str(df_all_daily, '전년동월')}")

st.markdown("---")

if not selected_part or not selected_store:
    st.warning("👈 사이드바에서 담당 파트명과 점포를 먼저 선택해 주세요.")
else:
    current_area = store_meta[selected_store]["점포유형"]
    
    df_store_all = df_all_daily[df_all_daily['점포명'] == selected_store]
    df_store = df_daily[df_daily['점포명'] == selected_store] 
    df_store_hour = df_hourly[df_hourly['점포명'] == selected_store]
    df_area = df_daily[df_daily['점포유형'] == current_area]

    st.markdown(f"### 📍 **{selected_store}** (유형: {current_area})")
    
    peak_hour_data = df_store_hour.groupby('결제시간대')['판매량'].sum().reset_index()
    best_hour = peak_hour_data.loc[peak_hour_data['판매량'].idxmax()]['결제시간대']
    best_cat = df_store.groupby('중분류')['판매수량'].sum().idxmax()
    
    st.success(f"🌟 **오늘의 핵심 액션 플랜**\n\n"
               f"우리 점포 매출의 일등 공신은 **[{best_cat}]** 카테고리입니다! "
               f"가장 손님이 붐비는 시간대인 **{best_hour}시 ~ {best_hour+1}시** 이전에 결품이 나지 않도록, "
               f"**{best_hour-1}시까지는 주력 상품의 보충 진열을 100% 완료**해 주세요.")
    
    st.markdown("---")

    tab1, tab2, tab3 = st.tabs(["💡 발주/진열 코칭", "🏆 유사유형 베스트 점검", "📈 매출 및 판매율 요약"])

    # -------------------------------------------------------
    # TAB 1: 발주 코칭 
    # -------------------------------------------------------
    with tab1:
        # ✨ [업데이트] 막대그래프 및 천원 단위 표기 로직
        st.subheader("1. 📉 과거 FF 매출 흐름 (단위: 천원)")
        
        # 합계 계산
        curr_rev = df_store_all[df_store_all['기간'] == '당월']['일매출'].sum()
        mom_rev = df_store_all[df_store_all['기간'] == '전월']['일매출'].sum()
        yoy_rev = df_store_all[df_store_all['기간'] == '전년동월']['일매출'].sum()
        
        # 단위 변환 (천원)
        curr_rev_k = curr_rev / 1000
        mom_rev_k = mom_rev / 1000
        yoy_rev_k = yoy_rev / 1000
        
        # 막대그래프용 데이터프레임 생성 (시간 순서대로 배열)
        rev_df = pd.DataFrame({
            "기간": ["작년 동월 전체", "전월 전체", "당월 누적"],
            "매출액(천원)": [yoy_rev_k, mom_rev_k, curr_rev_k]
        })
        
        # Plotly 막대그래프 생성
        fig_rev_bar = px.bar(
            rev_df, 
            x="기간", 
            y="매출액(천원)",
            text=rev_df['매출액(천원)'].apply(lambda x: f"{x:,.0f}천원"), # 막대 위에 숫자+천원 표시
            color="기간", 
            color_discrete_sequence=['#B0BEC5', '#90A4AE', '#0078D7'] # 당월만 파란색으로 강조
        )
        
        # 그래프 디자인 세팅
        fig_rev_bar.update_traces(textposition='outside', textfont_size=14, marker_line_width=0)
        fig_rev_bar.update_layout(
            template='plotly_white', 
            showlegend=False, 
            margin=dict(l=0, r=0, t=30, b=0), 
            plot_bgcolor='rgba(0,0,0,0)',
            yaxis=dict(showticklabels=False, title=""), # y축 숫자 숨김 (텍스트가 있으므로)
            xaxis=dict(title="")
        )
        
        st.plotly_chart(fig_rev_bar, use_container_width=True)

        st.divider()

        st.subheader("2. 📅 데이터 기반 요일별 맞춤 발주")
        st.markdown("> **[당월 누적 60% + 전월 30% + 전년동월 10%]** 비중으로 계산된 정밀한 예상치입니다.")
        
        day_order = ["월", "화", "수", "목", "금", "토", "일"]
        pivot_df = pd.DataFrame(index=cat_list, columns=day_order)
        
        for cat in cat_list:
            for day in day_order:
                curr_sales = df_store_all[(df_store_all['중분류'] == cat) & (df_store_all['요일'] == day) & (df_store_all['기간'] == '당월')]['판매수량'].mean()
                mom_sales = df_store_all[(df_store_all['중분류'] == cat) & (df_store_all['요일'] == day) & (df_store_all['기간'] == '전월')]['판매수량'].mean()
                yoy_sales = df_store_all[(df_store_all['중분류'] == cat) & (df_store_all['요일'] == day) & (df_store_all['기간'] == '전년동월')]['판매수량'].mean()
                
                curr_sales = curr_sales if pd.notna(curr_sales) else 0
                mom_sales = mom_sales if pd.notna(mom_sales) else curr_sales
                yoy_sales = yoy_sales if pd.notna(yoy_sales) else curr_sales
                
                if curr_sales > 0:
                    exp_sales = (curr_sales * 0.6) + (mom_sales * 0.3) + (yoy_sales * 0.1)
                    rec_order = int(exp_sales * 1.15) 
                    pivot_df.at[cat, day] = f"예상 {int(exp_sales)} / 권장 {rec_order}"
                else:
                    pivot_df.at[cat, day] = "-"
                    
        st.dataframe(pivot_df, use_container_width=True)

        st.divider()

        st.subheader("3. ⏰ 시간대별 집중도 추이 (피크 타임)")
        
        peak_texts = []
        for day in day_order:
            day_data = df_store_hour[df_store_hour['요일'] == day]
            if not day_data.empty:
                peak_hr = day_data.loc[day_data['판매량'].idxmax()]['결제시간대']
                peak_texts.append(f"**{day}**: {peak_hr}시")
        
        st.info("📌 **전체 요일별 최고점 시간대 요약:** " + " | ".join(peak_texts))
        
        selected_day_chart = st.radio("그래프 조회 조건 선택", ["전체"] + day_order, horizontal=True)
        
        df_line = df_store_hour.groupby(['요일', '결제시간대'])['판매량'].mean().reset_index()
        df_line['요일'] = pd.Categorical(df_line['요일'], categories=day_order, ordered=True)
        
        if selected_day_chart != "전체":
            df_line = df_line[df_line['요일'] == selected_day_chart]
            
        df_line = df_line.sort_values(['요일', '결제시간대'])

        if selected_day_chart == "전체":
            fig_line = px.line(
                df_line, x="결제시간대", y="판매량", color="요일", 
                markers=True, labels={"판매량": "평균 판매건수"}
            )
        else:
            fig_line = px.line(
                df_line, x="결제시간대", y="판매량", 
                markers=True, labels={"판매량": "평균 판매건수"}
            )
            fig_line.update_traces(fill='tozeroy', line_color='#0078D7', fillcolor='rgba(0, 120, 215, 0.2)')

        fig_line.update_xaxes(tickmode='linear', tick0=0, dtick=2) 
        fig_line.update_layout(template='plotly_white', margin=dict(l=0, r=0, t=20, b=0), plot_bgcolor='rgba(0,0,0,0)', legend_title_text='')
        st.plotly_chart(fig_line, use_container_width=True)

    # -------------------------------------------------------
    # TAB 2: 베스트 상품
    # -------------------------------------------------------
    with tab2:
        st.subheader(f"[{current_area}] 유형 베스트 상품 크로스체크")
        best_items = []
        for cat in cat_list:
            cat_df = df_area[df_area['중분류'] == cat]
            if not cat_df.empty:
                top_item = cat_df.groupby('상품명')['판매수량'].sum().reset_index().sort_values(by='판매수량', ascending=False).iloc[0]
                item_name = top_item['상품명']
                area_sales = top_item['판매수량']
                
                my_item_df = df_store[df_store['상품명'] == item_name]
                if not my_item_df.empty:
                    my_inbound = int(my_item_df['입고수량'].sum())
                    my_sales = int(my_item_df['판매수량'].sum())
                else:
                    my_inbound = 0
                    my_sales = 0
                    
                best_items.append({
                    "중분류": cat, "상품명": item_name, "동일유형 누적판매": area_sales,
                    "우리점포 누적입고": my_inbound, "우리점포 누적판매": my_sales,
                    "상태": "🟢취급중" if my_inbound > 0 else "🔴미취급"
                })
                
        best_item_df = pd.DataFrame(best_items)
        st.dataframe(best_item_df, use_container_width=True, hide_index=True)

    # -------------------------------------------------------
    # TAB 3: 요약 
    # -------------------------------------------------------
    with tab3:
        st.subheader("1. 당월 누적 FF 일매출 추이")
        daily_trend = df_store.groupby('일자')['일매출'].sum().reset_index().sort_values(by='일자')
        avg_daily = daily_trend['일매출'].mean()
        st.metric("당월 일평균 FF 일매출", f"{avg_daily:,.0f}원")
        
        fig_bar = px.bar(
            daily_trend, x="일자", y="일매출", 
            text_auto='.2s'
        )
        fig_bar.update_traces(textposition='outside', marker_color='#0078D7', marker_line_width=0, opacity=0.8)
        fig_bar.update_layout(template='plotly_white', margin=dict(l=0, r=0, t=30, b=0), plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_bar, use_container_width=True)

        st.divider()

        st.subheader("2. 당월 누적 중분류별 판매율 (소진율)")
        cat_rate_df = df_store.groupby('중분류')[['입고수량', '판매수량']].sum().reset_index()
        cat_rate_df['판매율'] = np.where(cat_rate_df['입고수량'] > 0, (cat_rate_df['판매수량'] / cat_rate_df['입고수량']) * 100, 0)
        
        fig_rate = px.bar(
            cat_rate_df.sort_values('판매율', ascending=False), 
            x="중분류", y="판매율", 
            text=cat_rate_df['판매율'].apply(lambda x: f"{x:.1f}%")
        )
        fig_rate.update_traces(textposition='outside', marker_color='#4CAF50', textfont_color='black')
        fig_rate.update_layout(template='plotly_white', showlegend=False, margin=dict(l=0, r=0, t=30, b=0), plot_bgcolor='rgba(0,0,0,0)', yaxis_title="판매율(%)", xaxis_title="")
        st.plotly_chart(fig_rate, use_container_width=True)
