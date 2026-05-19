import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# -----------------------------------------------------------------------------
# 1. 페이지 설정 및 디자인 (GS25 테마)
# -----------------------------------------------------------------------------
st.set_page_config(page_title="GS25 FF 코칭 PRO MAX", page_icon="🏪", layout="wide")

st.markdown("""
<style>
    html, body, [class*="css"] { font-family: 'Pretendard', sans-serif; }
    div[data-testid="metric-container"] {
        background-color: #ffffff; border: 1px solid #e6e9ef;
        padding: 20px; border-radius: 12px; box-shadow: 0px 4px 15px rgba(0,0,0,0.05);
    }
    .main-header { color: #0078D7; font-weight: 800; font-size: 2rem; margin-bottom: 0px; }
    .sub-header { color: #606060; font-size: 1.1rem; margin-bottom: 20px; }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. 데이터 로드 (사장님의 엑셀 데이터를 그대로 사용!)
# -----------------------------------------------------------------------------
@st.cache_data
def load_data():
    # 사장님이 만드신 CSV 파일 이름을 정확히 읽어옵니다.
    master = pd.read_csv('Store_Master.csv')
    ff_agg = pd.read_csv('FF_Agg.csv')
    hourly = pd.read_csv('Hourly_Wide.csv')
    subcat = pd.read_csv('Subcat_Summary.csv')
    forecast = pd.read_csv('Forecast_Wide.csv')
    area_best = pd.read_csv('Area_Best.csv')
    return master, ff_agg, hourly, subcat, forecast, area_best

try:
    master, ff_agg, hourly, subcat, forecast, area_best = load_data()
except Exception as e:
    st.error("🚨 데이터를 불러오지 못했습니다. 파이썬 파일과 동일한 폴더에 CSV 파일들이 있는지 확인해주세요.")
    st.stop()

# -----------------------------------------------------------------------------
# 3. 사이드바: 파트 및 점포 선택 (이중 드롭다운 완벽 구현)
# -----------------------------------------------------------------------------
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/1/14/GS25_logo.svg/1024px-GS25_logo.svg.png", width=150)
st.sidebar.markdown("---")
st.sidebar.title("🔍 경영주 코칭 세팅")

# 1. 파트명 선택 (검색 지원)
part_list = sorted(master['파트명'].dropna().unique())
selected_part = st.sidebar.selectbox("1. 파트명 (OFC) 선택", part_list, index=0)

# 2. 파트명에 종속된 점포명 리스트 생성 및 선택
store_list = sorted(master[master['파트명'] == selected_part]['점포명'].dropna().unique())
selected_store = st.sidebar.selectbox("2. 점포명 선택", store_list)

# -----------------------------------------------------------------------------
# 4. 메인 화면 UI 구현
# -----------------------------------------------------------------------------
if selected_store:
    # 점포 마스터 정보
    store_info = master[master['점포명'] == selected_store].iloc[0]
    
    st.markdown(f"<div class='main-header'>🏪 {selected_store} 맞춤형 FF 코칭 리포트</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='sub-header'>📍 파트: {store_info['파트명']} | 팀: {store_info['팀']} | 상권유형: {store_info['점포유형']} | 점포코드: {store_info['현재코드']}</div>", unsafe_allow_html=True)
    
    st.divider()

    # --- [섹션 1] 핵심 성과 지표 (KPI) ---
    st.markdown("### 📈 과거 FF 총 매출 흐름 (단위: 천원)")
    
    store_ff = ff_agg[ff_agg['점포명'] == selected_store]
    
    def get_rev(role):
        val = store_ff[store_ff['역할'] == role]['일매출천원']
        return float(val.iloc[0]) if not val.empty else 0
        
    rev_ly = get_rev('전년동월')
    rev_pm = get_rev('전월')
    rev_cm = get_rev('당월')

    col1, col2, col3 = st.columns(3)
    col1.metric("작년 동월 (25년 5월)", f"{rev_ly:,.1f} 천원")
    col2.metric("전월 전체 (26년 4월)", f"{rev_pm:,.1f} 천원", f"{(rev_pm - rev_ly)/rev_ly*100:.1f}%" if rev_ly else "0%")
    col3.metric("당월 누적 (26년 5월)", f"{rev_cm:,.1f} 천원", f"{(rev_cm - rev_pm)/rev_pm*100:.1f}%" if rev_pm else "0%")

    st.markdown("<br>", unsafe_allow_html=True)

    # --- [섹션 2] 매출 추이 & 피크타임 차트 ---
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("1. 📊 과거 매출 추이")
        # 막대 차트 (전년/전월/당월)
        fig_bar = px.bar(store_ff, x='기간', y='일매출천원', text='일매출천원', color='역할',
                         color_discrete_map={'전년동월':'#DEE2E6', '전월':'#ADB5BD', '당월':'#0078D7'})
        fig_bar.update_traces(textposition='outside', width=0.4)
        fig_bar.update_layout(template='plotly_white', showlegend=False, yaxis_title="일매출 (천원)", xaxis_title="", height=350)
        st.plotly_chart(fig_bar, use_container_width=True)

    with col_right:
        st.subheader("2. ⏰ 자점 시간대별 방문 일 객수")
        store_hour = hourly[(hourly['점포명'] == selected_store) & (hourly['보기'] == '전체')]
        
        if not store_hour.empty:
            hours = [f'H{str(i).zfill(2)}' for i in range(24)]
            hour_data = store_hour[hours].iloc[0].values
            
            # 꺾은선 차트 (시간대별 트래픽)
            fig_line = px.line(x=[f"{i}시" for i in range(24)], y=hour_data, markers=True)
            fig_line.update_traces(line_color='#FF9800', fill='tozeroy')
            fig_line.update_layout(template='plotly_white', xaxis_title="결제시간대", yaxis_title="방문 객수", height=350)
            st.plotly_chart(fig_line, use_container_width=True)
        else:
            st.info("시간대 트래픽 데이터가 없습니다.")

    st.divider()

    # --- [섹션 3] 맞춤 발주 가이드 & 상권 베스트 ---
    st.subheader("3. 💡 데이터 기반 요일별 맞춤 발주 (당월 0.7 + 전월 0.3)")
    store_forecast = forecast[forecast['점포명'] == selected_store].drop(columns=['Key', '점포명'])
    st.dataframe(store_forecast, use_container_width=True, hide_index=True)

    st.markdown("<br>", unsafe_allow_html=True)
    
    col_bot1, col_bot2 = st.columns(2)
    
    with col_bot1:
        st.subheader("4. 🏆 상권 베스트 상품 점검")
        store_area = area_best[area_best['점포명'] == selected_store][['중분류', '상권1위상품', '우리점포일평균판매', '취급여부']]
        st.dataframe(store_area, use_container_width=True, hide_index=True)

    with col_bot2:
        st.subheader("5. 🎯 중분류별 누적 판매율")
        store_subcat = subcat[subcat['점포명'] == selected_store]
        store_subcat['판매율(%)'] = (store_subcat['판매율'] * 100).round(1)
        
        fig_sub = px.bar(store_subcat, x='중분류', y='판매율(%)', text='판매율(%)')
        fig_sub.update_traces(marker_color='#4CAF50', width=0.5, textposition='outside')
        fig_sub.update_layout(template='plotly_white', yaxis_title="판매율 (%)", xaxis_title="", height=300)
        st.plotly_chart(fig_sub, use_container_width=True)
