import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import io

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
    .sub-header  { color: #606060; font-size: 1.1rem; margin-bottom: 20px; }
    .period-box  {
        background: #f0f6ff; border-left: 4px solid #0078D7;
        padding: 10px 16px; border-radius: 6px;
        font-size: 0.88rem; color: #444; margin-bottom: 8px;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. Google Sheets에서 데이터 로드
# -----------------------------------------------------------------------------
@st.cache_data
def load_data():
    FILE_ID    = "1tKeyLY9IApZaKmizNHXunEgUPLj4Db8j"
    EXPORT_URL = f"https://docs.google.com/spreadsheets/d/{FILE_ID}/export?format=xlsx"

    response = requests.get(EXPORT_URL, timeout=30)
    response.raise_for_status()
    fb = io.BytesIO(response.content)

    def read(sheet):
        fb.seek(0)
        return pd.read_excel(fb, sheet_name=sheet)

    master    = read('Store_Master')
    ff_agg    = read('FF_Agg')
    hourly    = read('Hourly_Wide')
    subcat    = read('Subcat_Summary')
    forecast  = read('Forecast_Wide')
    area_best = read('Area_Best')
    sku_top   = read('SKU_Top')
    sku_weak  = read('SKU_Weak')

    return master, ff_agg, hourly, subcat, forecast, area_best, sku_top, sku_weak

with st.spinner("📥 Google Sheets에서 데이터를 불러오는 중..."):
    try:
        master, ff_agg, hourly, subcat, forecast, area_best, sku_top, sku_weak = load_data()
    except Exception as e:
        st.error(
            f"🚨 데이터를 불러오지 못했습니다.\n\n"
            f"Google Sheets 공유 설정이 **'링크가 있는 모든 사용자 → 뷰어'** 인지 확인해주세요.\n\n"
            f"상세 에러: {e}"
        )
        st.stop()

# -----------------------------------------------------------------------------
# 3. 사이드바
# -----------------------------------------------------------------------------
st.sidebar.image(
    "https://upload.wikimedia.org/wikipedia/commons/thumb/1/14/GS25_logo.svg/1024px-GS25_logo.svg.png",
    width=150
)
st.sidebar.markdown("---")
st.sidebar.title("🔍 경영주 코칭 세팅")
st.sidebar.caption("✅ Google Sheets 연동 완료")

part_list      = sorted(master['파트명'].dropna().unique())
selected_part  = st.sidebar.selectbox("1. 파트명 (OFC) 선택", part_list, index=0)

store_list     = sorted(master[master['파트명'] == selected_part]['점포명'].dropna().unique())
selected_store = st.sidebar.selectbox("2. 점포명 선택", store_list)

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

    # 데이터 산정 기간 안내 배너
    st.markdown("""
    <div class='period-box'>
    📅 <b>데이터 산정 기간 및 기준</b> &nbsp;|&nbsp;
    작년 동월: 2025년 5월 전체 &nbsp;|&nbsp;
    전월: 2026년 4월 전체 &nbsp;|&nbsp;
    당월 누적: 2026년 5월 1일 ~ 최신일 &nbsp;|&nbsp;
    시간대 · SKU: 당월 누적 기준
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # ═══════════════════════════════════════════════════════════
    # [섹션 1] 핵심 KPI
    # ═══════════════════════════════════════════════════════════
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

    # ═══════════════════════════════════════════════════════════
    # [섹션 2] 매출 추이 & 시간대별 객수
    # ═══════════════════════════════════════════════════════════
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

        view_option = st.radio(
            "기간 구분",
            options=["전체", "평일", "주말"],
            horizontal=True,
            label_visibility="collapsed"
        )

        store_hour = hourly[
            (hourly['점포명'] == selected_store) & (hourly['보기'] == view_option)
        ]

        if not store_hour.empty:
            hour_cols = [c for c in hourly.columns if str(c).startswith('H') and str(c)[1:].isdigit()]
            if not hour_cols:
                hour_cols = [c for c in hourly.columns if str(c).isdigit() and 0 <= int(str(c)) <= 23]

            if hour_cols:
                hour_data = store_hour[hour_cols].iloc[0].values
                x_labels  = [f"{i}시" for i in range(len(hour_cols))]
                color_map = {"전체": "#FF9800", "평일": "#0078D7", "주말": "#E53935"}

                fig_line = px.line(x=x_labels, y=hour_data, markers=True)
                fig_line.update_traces(
                    line_color=color_map.get(view_option, "#FF9800"),
                    fill='tozeroy'
                )
                fig_line.update_layout(
                    template='plotly_white',
                    xaxis_title="결제시간대", yaxis_title="방문 객수", height=320
                )
                st.plotly_chart(fig_line, use_container_width=True)
            else:
                st.info("시간대 컬럼(H00~H23)을 찾을 수 없습니다.")
        else:
            st.info(f"'{view_option}' 시간대 데이터가 없습니다.")

    st.divider()

    # ═══════════════════════════════════════════════════════════
    # [섹션 3] 발주 가이드 & 상권 베스트 & 판매율
    # ═══════════════════════════════════════════════════════════
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

    st.divider()

    # ═══════════════════════════════════════════════════════════
    # [섹션 4] 판매수량 TOP SKU & 판매율 취약 SKU
    # ═══════════════════════════════════════════════════════════
    col_sku1, col_sku2 = st.columns(2)

    # 공통 컬럼 순서 (시트 실제 컬럼명 기준)
    SKU_COLS = ['순위', '중분류', '상품명', '입고', '판매', '판매율']

    with col_sku1:
        st.subheader("6. 🥇 판매수량 TOP SKU")
        st.caption("📅 SKU 26년 4월~26년 5월, 판매수량 기준 TOP 10")

        store_top = sku_top[sku_top['점포명'] == selected_store].copy()

        if not store_top.empty:
            show_cols = [c for c in SKU_COLS if c in store_top.columns]
            store_top = store_top[show_cols].sort_values('순위').reset_index(drop=True)

            # 판매율 % 변환
            if '판매율' in store_top.columns:
                store_top['판매율'] = (store_top['판매율'] * 100).round(1).astype(str) + '%'

            st.dataframe(
                store_top,
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("해당 점포의 TOP SKU 데이터가 없습니다.")

    with col_sku2:
        st.subheader("7. ⚠️ 판매율 취약 SKU")
        st.caption("📅 SKU 26년 4월~26년 5월, 입고 5개 이상 품목 중 판매율 낮은 순")

        store_weak = sku_weak[sku_weak['점포명'] == selected_store].copy()

        if not store_weak.empty:
            show_cols = [c for c in SKU_COLS if c in store_weak.columns]
            store_weak = store_weak[show_cols].sort_values('순위').reset_index(drop=True)

            # 판매율 % 변환
            if '판매율' in store_weak.columns:
                store_weak['판매율'] = (store_weak['판매율'] * 100).round(1).astype(str) + '%'

            st.dataframe(
                store_weak,
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("해당 점포의 취약 SKU 데이터가 없습니다.")
