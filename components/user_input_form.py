import streamlit as st

def get_user_inputs():
    inputs = {}

    # 세대 구성원 수
    num_members = st.number_input("세대 구성원 수", min_value=1, max_value=10, step=1)
    members = []

    for i in range(num_members):
        with st.expander(f"구성원 {i+1} 정보"):
            age = st.number_input(f"나이 (구성원 {i+1})", min_value=0)
            hobby = st.multiselect(
                f"취미 (구성원 {i+1})",
                ["영화", "산책", "전시", "공예", "쇼핑"]
            )
            importance = st.slider(f"중요도 (구성원 {i+1})", 1, 5, 3)
            members.append({"age": age, "hobby": hobby, "importance": importance})

    # 공통 필수 조건 입력
    region_keyword = st.text_input("지역 필수 조건 (예: 수원시)")
    subway_required = st.checkbox("지하철 반경 10분 이내 필요")

    inputs["members"] = members
    inputs["region_keyword"] = region_keyword
    inputs["subway_required"] = subway_required

    return inputs
