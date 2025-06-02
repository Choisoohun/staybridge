import streamlit as st

def user_input_form():
    st.header("👥 사용자 정보 입력")

    member_count = st.number_input(
        "세대 구성원 수",
        min_value=1,
        max_value=5,
        value=1,
        step=1
    )
    members = []
    for i in range(member_count):
        # expander는 항상 열린 상태(expanded=True)
        with st.expander(f"구성원 {i+1} 정보", expanded=True):
            age = st.number_input(
                f"나이 (구성원 {i+1})",
                min_value=0,
                max_value=100,
                value=30,
                key=f"age_{i}"
            )
            hobby = st.multiselect(
                f"취미 선택 (복수 가능, 구성원 {i+1})",
                ["영화", "전시", "산책", "공예", "쇼핑"],
                key=f"hobby_{i}"
            )
            importance = st.slider(
                f"중요도 (가중치, 구성원 {i+1})",
                1, 5, 3,
                key=f"importance_{i}"
            )
            members.append({
                "age": age,
                "hobby": hobby,
                "importance": importance
            })

    region_keyword = st.text_input(
        "지역 필수 조건 (예: 수원시)",
        key="region_keyword"
    )

    # 지하철 접근성 옵션 모두 제거 (요구사항)

    return {
        "members": members,
        "region_keyword": region_keyword
    }
