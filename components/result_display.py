import streamlit as st
import folium
from streamlit_folium import st_folium
from utils.score_calculator import calculate_scores
from utils.overpass_query import get_facility_count
import pandas as pd

# 고정 마커 태그 및 색상
HOBBY_TAG_COLOR_MAP = {
    "영화": {"tag": "amenity=cinema", "color": "red"},
    "전시": {"tag": "tourism=gallery", "color": "blue"},
    "산책": {"tag": "leisure=park", "color": "green"},
    "공예": {"tag": "craft=pottery", "color": "purple"},
    "쇼핑": {"tag": "shop=mall", "color": "orange"}
}
ALL_HOBBIES = list(HOBBY_TAG_COLOR_MAP.keys())

# 추가 시설 태그
SCHOOL_TAG = 'amenity=school'
HOSPITAL_TAG = 'amenity=hospital'

def display_results(user_inputs, vacant_data):
    results = calculate_scores(user_inputs, vacant_data)
    if not results:
        st.warning("조건에 맞는 추천 결과가 없습니다.")
        return

    st.subheader("🏘️ 추천 공실 목록 (상위 5개)")
    df = pd.DataFrame(results)[["address", "score"]].rename(columns={"address": "주소", "score": "점수"})
    st.dataframe(df, use_container_width=True)

    options = [f"{r['address']} (점수: {r['score']})" for r in results]
    selected = st.selectbox("🗺️ 지도로 볼 공실 선택:", options=options)
    selected_result = results[options.index(selected)]

    lat, lon = selected_result["latitude"], selected_result["longitude"]
    address = selected_result["address"]
    member_scores = selected_result["member_scores"]

    # 연령 조건 확인
    has_kid = any(member["age"] < 20 for member in user_inputs["members"])
    has_senior = any(member["age"] >= 65 for member in user_inputs["members"])

    st.subheader("📍 공실 위치 및 주변 시설")
    m = folium.Map(location=[lat, lon], zoom_start=14)

    # 공실 마커
    folium.Marker(
        location=[lat, lon],
        popup=f"<b>추천 공실</b><br>{address}",
        icon=folium.Icon(color="gray", icon="home", prefix="fa")
    ).add_to(m)

    # 반경 원 3km
    folium.Circle(
        radius=3000,
        location=[lat, lon],
        color="#555",
        fill=True,
        fill_opacity=0.08
    ).add_to(m)

    # 모든 취미 시설 마커 (항상 표시)
    for hobby in ALL_HOBBIES:
        tag = HOBBY_TAG_COLOR_MAP[hobby]["tag"]
        color = HOBBY_TAG_COLOR_MAP[hobby]["color"]
        _, facilities = get_facility_count(tag, lat, lon, radius=3000, return_elements=True)
        for f in facilities:
            folium.Marker(
                location=[f["lat"], f["lon"]],
                popup=f"{hobby} 관련 시설",
                icon=folium.Icon(color=color, icon="info-sign")
            ).add_to(m)

    # 초중고 학교 (20세 미만이 있을 경우)
    if has_kid:
        _, schools = get_facility_count(SCHOOL_TAG, lat, lon, radius=3000, return_elements=True)
        for s in schools:
            folium.Marker(
                location=[s["lat"], s["lon"]],
                popup="학교",
                icon=folium.Icon(color="cadetblue", icon="book", prefix="fa")
            ).add_to(m)

    # 병원 (65세 이상이 있을 경우)
    if has_senior:
        _, hospitals = get_facility_count(HOSPITAL_TAG, lat, lon, radius=1000, return_elements=True)
        for h in hospitals:
            folium.Marker(
                location=[h["lat"], h["lon"]],
                popup="병원",
                icon=folium.Icon(color="black", icon="plus-sign", prefix="fa")
            ).add_to(m)

    # 범례 UI
    legend_html = """
    <div style="
        position: fixed;
        top: 50px;
        right: 50px;
        background-color: rgba(255, 255, 255, 0.95);
        padding: 10px 15px;
        border: 1px solid #ccc;
        border-radius: 8px;
        font-size: 14px;
        z-index: 9999;
        box-shadow: 2px 2px 6px rgba(0,0,0,0.15);">
        <b>📌 범례</b><br>
        <i class="fa fa-home fa-1x" style="color:gray"></i> 공실<br>
        <i class="fa fa-map-marker fa-1x" style="color:red"></i> 영화관<br>
        <i class="fa fa-map-marker fa-1x" style="color:blue"></i> 전시회관<br>
        <i class="fa fa-map-marker fa-1x" style="color:green"></i> 공원<br>
        <i class="fa fa-map-marker fa-1x" style="color:purple"></i> 공방<br>
        <i class="fa fa-map-marker fa-1x" style="color:orange"></i> 쇼핑몰<br>
        <i class="fa fa-map-marker fa-1x" style="color:cadetblue"></i> 학교<br>
        <i class="fa fa-map-marker fa-1x" style="color:black"></i> 병원<br>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

    st_folium(m, width=800, height=600)

    # 구성원 점수 시각화
    st.subheader("📊 구성원별 점수")
    chart_df = pd.DataFrame({
        "구성원": [f"구성원 {i+1}" for i in range(len(member_scores))],
        "점수": member_scores
    })
    st.bar_chart(chart_df.set_index("구성원"))
