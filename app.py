import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import io

# -----------------------------------------------------------------------------
# 1. 페이지 설정
# -----------------------------------------------------------------------------
st.set_page_config(page_title="GS25 FF 코칭", page_icon="🏪", layout="centered")

st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');

    /* ── 전체 기본 ── */
    html, body, [class*="css"] {
        font-family: 'Pretendard', sans-serif;
    }

    /* ── 모바일 최적화: 최대 너비 고정 & 패딩 축소 ── */
    .block-container {
        max-width: 100% !important;
        padding: 0.8rem 0.8rem 2rem 0.8rem !important;
    }

    /* ── 상단 헤더 카드 ── */
    .header-card {
        background: linear-gradient(135deg, #0078D7 0%, #005fa3 100%);
        border-radius: 16px;
        padding: 16px 18px 12px 18px;
        color: white;
        margin-bottom: 12px;
    }
    .header-card .store-name {
        font-size: 1.25rem;
        font-weight: 800;
        margin-bottom: 4px;
    }
    .header-card .store-meta {
        font-size: 0.78rem;
        opacity: 0.88;
        line-height: 1.6;
    }

    /* ── 기간 배너 ── */
    .period-box {
        background: #f0f6ff;
        border-left: 4px solid #0078D7;
        padding: 8px 12px;
        border-radius: 6px;
        font-size: 0.78rem;
        color: #444;
        margin-bottom: 12px;
        line-height: 1.7;
    }

    /* ── 섹션 타이틀 ── */
    .section-title {
        font-size: 1rem;
        font-weight: 700;
        color: #1a1a1a;
        margin: 18px 0 8px 0;
        padding-left: 8px;
        border-left: 3px solid #0078D7;
    }
    .section-caption {
        font-size: 0.74rem;
        color: #888;
        margin-bottom: 6px;
        padding-left: 2px;
    }

    /* ── KPI 카드 (3개 가로) ── */
    div[data-testid="metric-container"] {
        background: #ffffff;
        border: 1px solid #e8edf3;
        border-radius: 12px;
        padding: 12px 10px !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        text-align: center;
    }
    div[data-testid="metric-container"] label {
        font-size: 0.7rem !important;
        color: #666 !important;
    }
    div[data-testid="metric-container"] [data-testid="stMetricValue"] {
        font-size: 1rem !important;
        font-weight: 700 !important;
    }
    div[data-testid="metric-container"] [data-testid="stMetricDelta"] {
        font-size: 0.75rem !important;
    }

    /* ── 라디오 버튼 (탭처럼) ── */
    div[data-testid="stRadio"] > div {
        gap: 6px !important;
    }
    div[data-testid="stRadio"] label {
        background: #f0f4f8;
        border-radius: 20px;
        padding: 4px 14px !important;
        font-size: 0.82rem !important;
        font-weight: 600;
        cursor: pointer;
        border: 1.5px solid transparent;
        transition: all 0.2s;
    }
    div[data-testid="stRadio"] label:has(input:checked) {
        background: #0078D7;
        color: white;
        border-color: #0078D7;
    }

    /* ── 데이터프레임 모바일 최적화 ── */
    .stDataFrame {
        font-size: 0.78rem !important;
    }
    iframe[title="st.dataframe"] {
        border-radius: 10px;
    }

    /* ── 사이드바 ── */
    [data-testid="stSidebar"] {
        min-width: 260px !important;
        max-width: 280px !important;
    }
    [data-testid="stSidebar"] .block-container {
        padding: 1rem 0.8rem !important;
    }

    /* ── 구분선 ── */
    hr { margin: 12px 0 !important; border-color: #eee; }

    /* ── TOP/WEAK SKU 색상 뱃지 ── */
    .badge-top  { background:#0078D7; color:#fff; padding:2px 8px; border-radius:10px; font-size:0.72rem; }
    .badge-weak { background:#E53935; color:#fff; padding:2px 8px; border-radius:10px; font-size:0.72rem; }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. 데이터 로드
# -----------------------------------------------------------------------------
@st.cache_data
def load_data():
    FILE_ID    = "1tKeyLY9IApZaKmizNHXunEgUPLj4Db8j"
    EXPORT_URL = f"https://docs.google.com/spreadsheets/d/{FILE_ID}/export?format=xlsx"
    response   = requests.get(EXPORT_URL, timeout=30)
    response.raise_for_status()
    fb = io.BytesIO(response.content)

    def read(sheet):
        fb.seek(0)
        return pd.read_excel(fb, sheet_name=sheet)

    return (
        read('Store_Master'),
        read('FF_Agg'),
        read('Hourly_Wide'),
        read('Subcat_Summary'),
        read('Forecast_Wide'),
        read('Area_Best'),
        read('SKU_Top'),
        read('SKU_Weak'),
    )

with st.spinner("📥 데이터 불러오는 중..."):
    try:
        master, ff_agg, hourly, subcat, forecast, area_best, sku_top, sku_weak = load_data()
    except Exception as e:
        st.error(f"🚨 데이터 로드 실패\n\n상세 에러: {e}")
        st.stop()

# -----------------------------------------------------------------------------
# 3. 사이드바: 점포 선택
# -----------------------------------------------------------------------------
st.sidebar.image(
    "https://upload.wikimedia.org/wikipedia/commons/thumb/1/14/GS25_logo.svg/1024px-GS25_logo.svg.png",
    width=130
)
st.sidebar.markdown("---")
st.sidebar.markdown("### 🔍 코칭 점포 선택")

part_list      = sorted(master['파트명'].dropna().unique())
selected_part  = st.sidebar.selectbox("파트명 (OFC)", part_list, index=0)
store_list     = sorted(master[master['파트명'] == selected_part]['점포명'].dropna().unique())
selected_store = st.sidebar.selectbox("점포명", store_list)
st.sidebar.caption("✅ Google Sheets 연동")

# -----------------------------------------------------------------------------
# 4. 메인 화면
# -----------------------------------------------------------------------------
if not selected_store:
    st.info("왼쪽 메뉴에서 점포를 선택해주세요.")
    st.stop()

store_info = master[master['점포명'] == selected_store].iloc[0]

# ── 상단 헤더 카드 ──
st.markdown(f"""
<div class="header-card">
    <div class="store-name">🏪 {selected_store}</div>
    <div class="store-meta">
        📍 파트: {store_info['파트명']} &nbsp;|&nbsp; 팀: {store_info['팀']}<br>
        상권: {store_info['점포유형']} &nbsp;|&nbsp; 코드: {store_info['현재코드']}
    </div>
</div>
""", unsafe_allow_html=True)

# ── 데이터 기간 안내 ──
st.markdown("""
<div class="period-box">
📅 <b>데이터 산정 기준</b><br>
작년 동월: 2025년 5월 전체 &nbsp;|&nbsp; 전월: 2026년 4월 전체<br>
당월 누적: 2026년 5월 1일 ~ 최신일 &nbsp;|&nbsp; SKU·시간대: 당월 기준
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════
# [1] KPI 지표
# ══════════════════════════════════════════
st.markdown("<div class='section-title'>📈 FF 매출 흐름 (천원)</div>", unsafe_allow_html=True)

store_ff = ff_agg[ff_agg['점포명'] == selected_store]

def get_rev(role):
    val = store_ff[store_ff['역할'] == role]['일매출천원']
    return float(val.iloc[0]) if not val.empty else 0

rev_ly, rev_pm, rev_cm = get_rev('전년동월'), get_rev('전월'), get_rev('당월')

c1, c2, c3 = st.columns(3)
c1.metric("작년동월", f"{rev_ly:,.0f}")
c2.metric("전월", f"{rev_pm:,.0f}", f"{(rev_pm-rev_ly)/rev_ly*100:.1f}%" if rev_ly else "0%")
c3.metric("당월누적", f"{rev_cm:,.0f}", f"{(rev_cm-rev_pm)/rev_pm*100:.1f}%" if rev_pm else "0%")

# ══════════════════════════════════════════
# [2] 매출 추이 차트
# ══════════════════════════════════════════
st.markdown("<div class='section-title'>1. 📊 과거 매출 추이</div>", unsafe_allow_html=True)

if not store_ff.empty:
    fig_bar = px.bar(
        store_ff, x='기간', y='일매출천원', text='일매출천원', color='역할',
        color_discrete_map={'전년동월': '#DEE2E6', '전월': '#ADB5BD', '당월': '#0078D7'}
    )
    fig_bar.update_traces(textposition='outside', width=0.4,
                          texttemplate='%{text:,.0f}')
    fig_bar.update_layout(
        template='plotly_white', showlegend=True,
        legend=dict(orientation='h', y=-0.2, x=0.5, xanchor='center', font_size=11),
        yaxis_title="일매출(천원)", xaxis_title="",
        height=280, margin=dict(t=10, b=40, l=10, r=10)
    )
    st.plotly_chart(fig_bar, use_container_width=True)
else:
    st.info("매출 데이터가 없습니다.")

# ══════════════════════════════════════════
# [3] 시간대별 객수 (전체/평일/주말)
# ══════════════════════════════════════════
st.markdown("<div class='section-title'>2. ⏰ 시간대별 방문 일 객수</div>", unsafe_allow_html=True)

view_option = st.radio(
    "기간 구분", ["전체", "평일", "주말"],
    horizontal=True, label_visibility="collapsed"
)

store_hour = hourly[(hourly['점포명'] == selected_store) & (hourly['보기'] == view_option)]

if not store_hour.empty:
    hour_cols = [c for c in hourly.columns if str(c).startswith('H') and str(c)[1:].isdigit()]
    if not hour_cols:
        hour_cols = [c for c in hourly.columns if str(c).isdigit() and 0 <= int(str(c)) <= 23]

    if hour_cols:
        hour_data = store_hour[hour_cols].iloc[0].values
        x_labels  = [f"{i}시" for i in range(len(hour_cols))]
        color_map = {"전체": "#FF9800", "평일": "#0078D7", "주말": "#E53935"}

        fig_line = px.line(x=x_labels, y=hour_data, markers=True)
        fig_line.update_traces(line_color=color_map.get(view_option, "#FF9800"), fill='tozeroy',
                               marker=dict(size=5))
        fig_line.update_layout(
            template='plotly_white',
            xaxis_title="", yaxis_title="객수",
            height=250, margin=dict(t=10, b=10, l=10, r=10),
            xaxis=dict(tickfont=dict(size=10), tickangle=-45)
        )
        st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.info("시간대 컬럼을 찾을 수 없습니다.")
else:
    st.info(f"'{view_option}' 데이터가 없습니다.")

# ══════════════════════════════════════════
# [4] 요일별 맞춤 발주
# ══════════════════════════════════════════
st.markdown("<div class='section-title'>3. 💡 요일별 맞춤 발주</div>", unsafe_allow_html=True)
st.markdown("<div class='section-caption'>당월 0.7 + 전월 0.3 가중 평균</div>", unsafe_allow_html=True)

store_forecast = forecast[forecast['점포명'] == selected_store].drop(
    columns=[c for c in ['Key', '점포명'] if c in forecast.columns]
)
st.dataframe(store_forecast, use_container_width=True, hide_index=True)

# ══════════════════════════════════════════
# [5] 상권 베스트
# ══════════════════════════════════════════
st.markdown("<div class='section-title'>4. 🏆 상권 베스트 상품 점검</div>", unsafe_allow_html=True)

cols_needed = ['중분류', '상권1위상품', '우리점포일평균판매', '취급여부']
available   = [c for c in cols_needed if c in area_best.columns]
store_area  = area_best[area_best['점포명'] == selected_store][available]
st.dataframe(store_area, use_container_width=True, hide_index=True)

# ══════════════════════════════════════════
# [6] 중분류별 판매율 차트
# ══════════════════════════════════════════
st.markdown("<div class='section-title'>5. 🎯 중분류별 누적 판매율</div>", unsafe_allow_html=True)

store_subcat = subcat[subcat['점포명'] == selected_store].copy()
if not store_subcat.empty:
    store_subcat['판매율(%)'] = (store_subcat['판매율'] * 100).round(1)
    fig_sub = px.bar(store_subcat, x='중분류', y='판매율(%)', text='판매율(%)')
    fig_sub.update_traces(marker_color='#4CAF50', width=0.5, textposition='outside')
    fig_sub.update_layout(
        template='plotly_white',
        yaxis_title="판매율(%)", xaxis_title="",
        height=260, margin=dict(t=10, b=10, l=10, r=10),
        xaxis=dict(tickfont=dict(size=10))
    )
    st.plotly_chart(fig_sub, use_container_width=True)
else:
    st.info("판매율 데이터가 없습니다.")

# ══════════════════════════════════════════
# [7] 판매수량 TOP SKU
# ══════════════════════════════════════════
SKU_COLS = ['순위', '중분류', '상품명', '입고', '판매', '판매율']

st.markdown("<div class='section-title'>6. 🥇 판매수량 TOP SKU</div>", unsafe_allow_html=True)
st.markdown("<div class='section-caption'>📅 SKU 26년 4월~26년 5월 | 판매수량 기준 TOP 10</div>", unsafe_allow_html=True)

store_top = sku_top[sku_top['점포명'] == selected_store].copy()
if not store_top.empty:
    show_cols = [c for c in SKU_COLS if c in store_top.columns]
    store_top = store_top[show_cols].sort_values('순위').reset_index(drop=True)
    if '판매율' in store_top.columns:
        store_top['판매율'] = (store_top['판매율'] * 100).round(1).astype(str) + '%'
    st.dataframe(store_top, use_container_width=True, hide_index=True)
else:
    st.info("TOP SKU 데이터가 없습니다.")

# ══════════════════════════════════════════
# [8] 판매율 취약 SKU
# ══════════════════════════════════════════
st.markdown("<div class='section-title'>7. ⚠️ 판매율 취약 SKU</div>", unsafe_allow_html=True)
st.markdown("<div class='section-caption'>📅 SKU 26년 4월~26년 5월 | 입고 5개 이상 품목 중 판매율 낮은 순</div>", unsafe_allow_html=True)

store_weak = sku_weak[sku_weak['점포명'] == selected_store].copy()
if not store_weak.empty:
    show_cols = [c for c in SKU_COLS if c in store_weak.columns]
    store_weak = store_weak[show_cols].sort_values('순위').reset_index(drop=True)
    if '판매율' in store_weak.columns:
        store_weak['판매율'] = (store_weak['판매율'] * 100).round(1).astype(str) + '%'
    st.dataframe(store_weak, use_container_width=True, hide_index=True)
else:
    st.info("취약 SKU 데이터가 없습니다.")
