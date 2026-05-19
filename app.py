import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# -----------------------------------------------------------------------------
# 1. 페이지 설정 및 디자인 (GS25 테마)
# -----------------------------------------------------------------------------
st.set_page_config(page_title="GS25 FF 코칭 PRO MAX", page_icon="🏪", layout="wide")

st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
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
# 2. 데이터 로드
#    우선순위 1: app.py와 같은 폴더의 'ff_data.xlsx' (GitHub 배포용, 파일명 영문 권장)
#    우선순위 2: 사이드바 파일 업로더 (로컬 테스트 / 클라우드 직접 업로드)
# -----------------------------------------------------------------------------
@st.cache_data
def load_data(file_source):
    master   = pd.read_excel(file_source, sheet_name='Store_Master')
    ff_agg   = pd.read_excel(file_source, sheet_name='FF_Agg')
    hourly   = pd.read_excel(file_source, sheet_name='Hourly_Wide')
    subcat   = pd.read_excel(file_source, sheet_name='Subcat_Summary')
    forecast = pd.read_excel(file_source, sheet_name='Forecast_Wide')
    area_best= pd.read_excel(file_source, sheet_name='Area_Best')
    return master, ff_agg, hourly, subcat, forecast, area_best

# 사이드바 로고 & 업로더
st.sidebar.image(
    "https://upload.wikimedia.org/wikipedia/commons/thumb/1/14/GS25_logo.svg/1024px-GS25_logo.svg.png",
    width=150
)
st.sidebar.markdown("---")
st.sidebar.title("🔍 경영주 코칭 세팅")

# ── 파일 탐색 순서 ──────────────────────────────────────────────
# 1) 영문 파일명 (GitHub 업로드 권장)
# 2) 한글 파일명 (기존 파일 그대로 사용하고 싶을 때)
# 3) 사이드바 업로더
CANDIDATE_FILES = ["ff_data.xlsx", "FF 테스트 2.xlsx"]

file_source = None
for fname in CANDIDATE_FILES:
    if os.path.exists(fname):
        file_source = fname
        break

if file_source is None:
    st.sidebar.caption("📂 엑셀 파일을 직접 업로드하세요")
    uploaded = st.sidebar.file_uploader(
        "ff_data.xlsx 또는 FF 테스트 2.xlsx",
        type=["xlsx"]
    )
    if uploaded:
        file_source = uploaded
    else:
        st.warning(
            "⚠️ 데이터 파일을 찾을 수 없습니다.\n\n"
            "**방법 A (GitHub 배포):** 엑셀 파일명을 `ff_data.xlsx`로 바꿔서 `app.py`와 같은 폴더에 업로드하세요.\n\n"
            "**방법 B (바로 사용):** 왼쪽 사이드바의 파일 업로더로 엑셀 파일을 올려주세요."
        )
        st.stop()

try:
    master, ff_agg, hourly, subcat, forecast, area_best = load_data(file_source)
except Exception as e:
    st.error(
        f"🚨 파일을 읽는 중 오류가 발생했습니다.\n\n"
        f"엑셀 시트 이름이 정확한지 확인하세요: "
        f"Store_Master / FF_Agg / Hourly_Wide / Subcat_Summary / Forecast_Wide / Area_Best\n\n"
        f"상세 에러: {e}"
    )
    st.stop()

# -----------------------------------------------------------------------------
# 3. 사이드바: 파트 및 점포 선택
# -----------------------------------------------------------------------------
st.sidebar.caption("✅ 데이터 로드 완료")

part_list     = sorted(master['파트명'].dropna().unique())
selected_part = st.sidebar.selectbox("1. 파트명 (OFC) 선택", part_list, index=0)

store_list    = sorted(master[master['파트명'] == selected_part]['점포명'].dropna().unique())
selected_store= st.sidebar.selectbox("2. 점포명 선택", store_list)

# -----------------------------------------------------------------------------
# 4. 메인 화면
# -----------------------------------------------------------------------------
if selected_store:
    store_info = master[master['점포명'] == selected_store].iloc[0]

    st.markdown(
        f"<div class='main-header'>🏪 {selected_store} 맞춤형 FF 코칭 리포트</div>",
        unsafe_allow_html=True
    )
    st.markdown(
        f"<div class='sub-header'>"
        f"📍 파트: {store_info['파트명']} | "
        f"팀: {store_info['팀']} | "
        f"상권유형: {store_info['점포유형']} | "
        f"점포코드: {store_info['현재코드']}"
        f"</div>",
        unsafe_allow_html=True
    )

    st.divider()

    # --- [섹션 1] 핵심 KPI ---
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
    col2.metric(
        "전월 전체 (26년 4월)", f"{rev_pm:,.1f} 천원",
        f"{(rev_pm - rev_ly)/rev_ly*100:.1f}%" if rev_ly else "0%"
    )
    col3.metric(
        "당월 누적 (26년 5월)", f"{rev_cm:,.1f} 천원",
        f"{(rev_cm - rev_pm)/rev_pm*100:.1f}%" if rev_pm else "0%"
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # --- [섹션 2] 매출 추이 & 피크타임 ---
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("1. 📊 과거 매출 추이")
        if not store_ff.empty:
            fig_bar = px.bar(
                store_ff, x='기간', y='일매출천원', text='일매출천원', color='역할',
                color_discrete_map={'전년동월': '#DEE2E6', '전월': '#ADB5BD', '당월': '#0078D7'}
            )
            fig_bar.update_traces(textposition='outside', width=0.4)
            fig_bar.update_layout(
                template='plotly_white', showlegend=False,
                yaxis_title="일매출 (천원)", xaxis_title="", height=350
            )
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("해당 점포의 매출 데이터가 없습니다.")

    with col_right:
        st.subheader("2. ⏰ 자점 시간대별 방문 일 객수")
        store_hour = hourly[
            (hourly['점포명'] == selected_store) & (hourly['보기'] == '전체')
        ]

        if not store_hour.empty:
            # 실제 컬럼에서 시간대 컬럼만 자동 추출 (H00~H23 형식)
            hour_cols = [c for c in hourly.columns if str(c).startswith('H') and str(c)[1:].isdigit()]
            if not hour_cols:
                # 숫자형 컬럼(0~23)으로 된 경우도 대응
                hour_cols = [c for c in hourly.columns if str(c).isdigit() and 0 <= int(c) <= 23]

            if hour_cols:
                hour_data = store_hour[hour_cols].iloc[0].values
                x_labels  = [f"{i}시" for i in range(len(hour_cols))]

                fig_line = px.line(x=x_labels, y=hour_data, markers=True)
                fig_line.update_traces(line_color='#FF9800', fill='tozeroy')
                fig_line.update_layout(
                    template='plotly_white',
                    xaxis_title="결제시간대", yaxis_title="방문 객수", height=350
                )
                st.plotly_chart(fig_line, use_container_width=True)
            else:
                st.info("시간대 컬럼(H00~H23)을 찾을 수 없습니다.")
        else:
            st.info("시간대 트래픽 데이터가 없습니다.")

    st.divider()

    # --- [섹션 3] 발주 가이드 & 상권 베스트 ---
    st.subheader("3. 💡 데이터 기반 요일별 맞춤 발주 (당월 0.7 + 전월 0.3)")
    store_forecast = forecast[forecast['점포명'] == selected_store].drop(
        columns=[c for c in ['Key', '점포명'] if c in forecast.columns]
    )
    st.dataframe(store_forecast, use_container_width=True, hide_index=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col_bot1, col_bot2 = st.columns(2)

    with col_bot1:
        st.subheader("4. 🏆 상권 베스트 상품 점검")
        cols_needed = ['중분류', '상권1위상품', '우리점포일평균판매', '취급여부']
        available   = [c for c in cols_needed if c in area_best.columns]
        store_area  = area_best[area_best['점포명'] == selected_store][available]
        st.dataframe(store_area, use_container_width=True, hide_index=True)

    with col_bot2:
        st.subheader("5. 🎯 중분류별 누적 판매율")
        store_subcat = subcat[subcat['점포명'] == selected_store].copy()
        if not store_subcat.empty:
            store_subcat['판매율(%)'] = (store_subcat['판매율'] * 100).round(1)
            fig_sub = px.bar(store_subcat, x='중분류', y='판매율(%)', text='판매율(%)')
            fig_sub.update_traces(marker_color='#4CAF50', width=0.5, textposition='outside')
            fig_sub.update_layout(
                template='plotly_white',
                yaxis_title="판매율 (%)", xaxis_title="", height=300
            )
            st.plotly_chart(fig_sub, use_container_width=True)
        else:
            st.info("중분류 판매율 데이터가 없습니다.")
