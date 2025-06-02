import streamlit as st
import os
import pandas as pd

# ─────────────────────────────────────────────────────────────────────────────
# 1) 페이지 설정: 반드시 가장 먼저
st.set_page_config(page_title="StayBridge", layout="wide")
# ─────────────────────────────────────────────────────────────────────────────


from components.user_input_form import user_input_form
from components.result_display import display_results

@st.cache_data
def load_data():
    """
    data/vacant_locations.csv를 읽어서
    - 컬럼명: '주소'→'address', '위도'→'latitude', '경도'→'longitude'
    - 세 개 컬럼만 반환
    """
    base_dir = os.path.dirname(__file__)
    csv_path = os.path.join(base_dir, "data", "vacant_locations.csv")
    df = pd.read_csv(csv_path)
    df = df.rename(columns={"주소": "address", "위도": "latitude", "경도": "longitude"})
    return df[["address", "latitude", "longitude"]]

def main():
    st.title("🏡 StayBridge: 공실 기반 맞춤형 주거지 추천")

    # 1) 사용자 정보 입력 폼
    user_inputs = user_input_form()

    # 2) “공실 추천” 버튼을 누르면 load_data() 호출 → 세션에 저장
    if st.button("📊 공실 추천"):
        vacant_data = load_data()
        st.session_state.user_inputs = user_inputs
        st.session_state.vacant_data = vacant_data

    # 3) 세션에 user_inputs, vacant_data가 있으면 display_results 호출
    if "user_inputs" in st.session_state and "vacant_data" in st.session_state:
        display_results(
            st.session_state.user_inputs,
            st.session_state.vacant_data
        )

if __name__ == "__main__":
    main()
