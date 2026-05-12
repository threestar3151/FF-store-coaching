import streamlit as st
import pandas as pd
import numpy as np

# 페이지 기본 설정
st.set_page_config(page_title="FF 발주/판매 최적화 대시보드", layout="wide")

# 1. 엑셀 데이터 불러오기 (캐싱하여 속도 최적화)
@st.cache_data
def load_data():
    # 엑셀 파일 경로 (실제 파일명에 맞게 수정)
    file_path = 'FF_Data.xlsx'
    
    df_order = pd.read_excel(file_path, sheet_name='발주_판매_데이터')
    df_time = pd.read_excel(file_path, sheet_name='시간대별_데이터')
    df_best = pd.read_excel(file_path, sheet_name='상품별_데이터')
    df_ofc = pd.read_excel(file_path, sheet_name='OFC_점포_데이터')
    
    return df_order, df_time, df_best, df_ofc

df_order, df_time, df_best, df_ofc = load_data()

st.title("📊 요일별 프레시푸드(FF) 판매 최적화 대시보드")
st.write("프레시푸드(FF)는 무조건 많이 발주하는 것보다 **버리는 것을 줄이는 것**이 이익률의 핵심입니다.")
st.markdown("---")

# 2. 모바일 UI 개선: OFC 및 점포 선택 (타이핑 검색 지원)
st.subheader("🔍 담당 점포 선택")
ofc_list = df_ofc['OFC명'].unique()
# Streamlit의 selectbox는 모바일에서도 터치 및 타이핑 검색이 완벽하게 지원됩니다.
selected_ofc = st.selectbox("담당 OFC를 검색하거나 선택하세요", options=ofc_list)

store_list = df_ofc[df_ofc['OFC명'] == selected_ofc]['점포명'].tolist()
selected_store = st.selectbox("점포를 선택하세요", options=store_list)

st.markdown("---")

# 3. 요일별 FF 판매 최적화 가이드 (실판매량 기준)
st.subheader("1. 요일별 FF 판매 최적화 가이드 (최근 데이터 기준)")
# 발주수량 - 판매수량 = 잉여 수량(권장 하향 수량) 계산 로직
guide_df = df_order.groupby(['중분류', '요일'])[['발주수량', '판매수량']].mean().reset_index()
guide_df['권장조정'] = np.where(
    guide_df['발주수량'] > guide_df['판매수량'], 
    "실판매 대비 " + (guide_df['발주수량'] - guide_df['판매수량']).round(1).astype(str) + "개 하향", 
    "-"
)
# 피벗 테이블로 변환하여 가로 형태로 출력 (월~토)
sorter = ['월요일', '화요일', '수요일', '목요일', '금요일', '토요일']
guide_pivot = guide_df.pivot(index='중분류', columns='요일', values='권장조정').reindex(columns=sorter, fill_value='-')
st.dataframe(guide_pivot, use_container_width=True)

st.markdown("---")

# 4. 요일별/시간대별 매출 집중도
st.subheader("2. 요일별/시간대별 매출 집중도 (가로형)")
time_df = df_time.groupby(['시간대', '요일'])['판매금액'].sum().reset_index()
# 가장 매출이 높은 요일/시간대를 '피크'로 표시하는 간단한 로직 추가 가능
time_pivot = time_df.pivot(index='시간대', columns='요일', values='판매금액').reindex(columns=sorter).fillna(0)

# 금액을 보기 좋게 포맷팅
def format_currency(val):
    if val > 0:
        return f"{int(val):,}원"
    return "-"

st.dataframe(time_pivot.applymap(format_currency), use_container_width=True)

st.markdown("---")

# 5. FF 중분류별 베스트 상품
st.subheader("3. 중분류별 베스트 상품 (타겟팅 라인업)")
categories = df_best['중분류'].unique()

cols = st.columns(len(categories))
for idx, cat in enumerate(categories):
    with cols[idx]:
        st.markdown(f"**{cat}**")
        cat_best = df_best[df_best['중분류'] == cat].sort_values(by='판매수량', ascending=False).head(3)
        for i, row in cat_best.iterrows():
            st.write(f"• {row['상품명']} ({row['판매수량']}개)")
