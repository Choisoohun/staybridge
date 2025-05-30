import streamlit as st
import pandas as pd
from components.user_input_form import get_user_inputs
from components.result_display import display_results

# 페이지 설정
st.set_page_config(page_title="StayBridge 주거 추천", layout="wide")
st.title("🏡 StayBridge: 공실 기반 맞춤형 주거지 추천")

# ✅ 세션 상태 초기화 (처음 실행 시)
if "show_result" not in st.session_state:
    st.session_state["show_result"] = False

# 데이터 로딩
@st.cache_data
def load_data():
    return pd.read_csv("data/vacant_locations.csv")

vacant_data = load_data()

# 사용자 입력
st.header("👥 사용자 정보 입력")
user_inputs = get_user_inputs()

# 버튼 클릭 → 세션 상태 변경
if st.button("🏘️ 추천 받기"):
    st.session_state["show_result"] = True

# 세션 상태에 따라 결과 표시
if st.session_state["show_result"]:
    st.header("📍 추천 결과")
    display_results(user_inputs, vacant_data)
