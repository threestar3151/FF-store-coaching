import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, timedelta

# -----------------------------------------------------------------------------
# 1. 페이지 기본 설정
# -----------------------------------------------------------------------------
st.set_page_config(page_title="GS25 FF 매출 코칭 PRO", page_icon="🏪", layout="wide")

# -----------------------------------------------------------------------------
# 2. 비밀번호 잠금 로직 (신규 추가)
# -----------------------------------------------------------------------------
def check_password():
    # 사용자의 로그인 상태를 저장하는 변수 초기화
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    # 로그인이 안 되어 있다면 로그인 화면을 보여줌
    if not st.session_state["password_correct"]:
        st.title("🔒 GS25 매출 코칭 대시보드")
        st.info("안전한 접근을 위해 비밀번호를 입력해 주세요.")
        
        # type="password"를 통해 입력값을 마스킹 처리 (****)
        pwd = st.text_input("비밀번호", type="password")
        
        if st.button("로그인"):
            if pwd == "GS25":
                st.session_state["password_correct"] = True
                st.rerun() # 비밀번호가 맞으면 화면을 새로고침하여 메인 화면으로 넘어감
            else:
                st.error("❌ 비밀번호가 틀렸습니다. 다시 확인해 주세요.")
        return False # 로그인이 안 된 상태 반환
    
    return True # 로그인 성공 상태 반환

# 비밀번호 확인 로직을 통과하지 못하면 여기서 코드가 멈추고 아래 내용은 보이지 않음!
if not check_password():
    st.stop()

# -----------------------------------------------------------------------------
# 3. 가상 데이터 생성 (상권 유형 포함 - 비밀번호 통과 시에만 실행됨)
# -----------------------------------------------------------------------------
@st.cache_data
def load_mock_data():
    store_meta = {
        "상무본점": {"OFC": "김광주", "Area": "유흥가"},
        "충장로중앙점": {"OFC": "김광주", "Area": "상업지"},
        "수완지구점": {"OFC": "김광주", "Area": "주택가"},
        "첨단산단점": {"OFC": "이전라", "Area": "오피스"},
        "금남로4가점": {"OFC": "이전라", "Area": "오피스"},
        "광천터미널점": {"OFC": "이전라", "Area": "상업지"} 
    }
    
    dates = [datetime.today() - timedelta(days=x) for x in range(30)]
    categories = ["도시락", "주먹밥", "김밥", "샌드위치/햄버거"]
    
    data = []
    for store, meta in store_meta.items():
        for d in dates:
            for cat in categories:
                base_inbound = np.random.randint(10, 50)
                if meta["Area"] == "오피스" and cat == "도시락": base_inbound += 20
                if meta["Area"] == "주택가" and cat == "주먹밥": base_inbound += 15
                
                sales_qty = int(base_inbound * np.random.uniform(0.6, 0.98))
                revenue = sales_qty * np.random.randint(2000, 5000)
                
                data.append({
                    "Date": d.strftime("%Y-%m-%d"),
                    "OFC": meta["OFC"],
                    "Store": store,
                    "Area_Type": meta["Area"],
                    "Category": cat,
                    "Inbound": base_inbound,
                    "Sales_Qty": sales_qty,
                    "Revenue": revenue
                })
    return pd.DataFrame(data), store_meta

df_sales, store_meta = load_mock_data()

# -----------------------------------------------------------------------------
# 4. 사이드바 UI (로그아웃 버튼 및 검색 조건)
# -----------------------------------------------------------------------------
# 로그아웃 버튼 (선택 사항)
if st.sidebar.button("🔓 로그아웃"):
    st.session_state["password_correct"] = False
    st.rerun()
st.sidebar.markdown("---")

st.sidebar.header("🔍 검색 및 분석 조건")

ofc_list = list(set([meta["OFC"] for meta in store_meta.values()]))
selected_ofc = st.sidebar.selectbox("담당 OFC 선택", ["선택하세요"] + ofc_list)

if selected_ofc != "선택하세요":
    store_list = [store for store, meta in store_meta.items() if meta["OFC"] == selected_ofc]
    selected_store = st.sidebar.selectbox(
        "점포 선택 (직접 타이핑하여 검색 가능)", 
        ["선택하세요"] + store_list,
        help="상자 안을 클릭하고 점포명을 입력하면 빠르게 찾을 수 있습니다."
    )

# -----------------------------------------------------------------------------
# 5. 메인 화면 UI 및 분석 로직
# -----------------------------------------------------------------------------
st.title("🏪 GS25 FF 데이터 기반 코칭 리포트")

if selected_ofc == "선택하세요" or 'selected_store' not in locals() or selected_store == "선택하세요":
    st.info("👈 사이드바에서 분석할 OFC와 점포를 선택해 주세요.")
else:
    current_area = store_meta[selected_store]["Area"]
    st.subheader(f"📍 {selected_store} (상권: {current_area} / 담당: {selected_ofc})")
    
    df_store = df_sales[df_sales['Store'] == selected_store]
    df_same_area = df_sales[(df_sales['Area_Type'] == current_area) & (df_sales['Store'] != selected_store)]
    
    st.markdown("### 💡 유사 상권 비교 및 발주 코칭")
    
    if not df_same_area.empty:
        store_cat_sales = df_store.groupby('Category')['Sales_Qty'].mean().reset_index()
        area_cat_sales = df_same_area.groupby('Category')['Sales_Qty'].mean().reset_index()
        
        merged_compare = pd.merge(store_cat_sales, area_cat_sales, on='Category', suffixes=('_Store', '_Area'))
        merged_compare['Difference'] = merged_compare['Sales_Qty_Store'] - merged_compare['Sales_Qty_Area']
        
        for index, row in merged_compare.iterrows():
            if row['Difference'] < -5: 
                st.warning(
                    f"⚠️ **{row['Category']}** 상품의 평균 판매량이 유사 상권({current_area}) 점포들보다 부족합니다. "
                    f"(우리 점포: {row['Sales_Qty_Store']:.1f}개 / 상권 평균: {row['Sales_Qty_Area']:.1f}개). "
                    f"**관련 베스트 상품의 발주 수량을 늘려 기회 로스를 방지해 보세요!**"
                )
            elif row['Difference'] > 5:
                st.success(
                    f"🌟 **{row['Category']}** 카테고리는 유사 상권 대비 매우 우수합니다! "
                    f"(우리 점포: {row['Sales_Qty_Store']:.1f}개 / 상권 평균: {row['Sales_Qty_Area']:.1f}개). "
                    f"**현재의 발주 패턴을 유지하거나 골드존 진열을 강화하세요.**"
                )
    else:
        st.info("비교할 유사 상권 점포 데이터가 아직 충분하지 않습니다.")

    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"#### 📊 {selected_store} 매출 비중")
        fig_pie = px.pie(df_store, values='Revenue', names='Category', hole=0.4)
        st.plotly_chart(fig_pie, use_container_width=True)
        
    with col2:
        if not df_same_area.empty:
            st.markdown(f"#### 📊 {current_area} 상권 평균 매출 비중")
            fig_pie_area = px.pie(df_same_area, values='Revenue', names='Category', hole=0.4)
            st.plotly_chart(fig_pie_area, use_container_width=True)

    with st.expander("📝 상세 판매 데이터 확인"):
        st.dataframe(df_store.sort_values(by="Date", ascending=False).reset_index(drop=True), use_container_width=True)
