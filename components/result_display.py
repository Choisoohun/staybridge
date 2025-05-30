import streamlit as st
import folium
from streamlit_folium import st_folium
from utils.score_calculator import calculate_scores
import pandas as pd
import requests

KAKAO_REST_API_KEY = "d5b327d7ed1a51e4c31331d7f224e005"

def search_places_kakao(query, lat, lon, radius=3000, size=15):
    headers = {"Authorization": f"KakaoAK {KAKAO_REST_API_KEY}"}
    params = {
        "query": query,
        "y": lat,
        "x": lon,
        "radius": radius,
        "size": size,
        "sort": "distance"
    }
    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json()["documents"]
    else:
        print("Kakao API 오류:", response.text)
        return []

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

    st.subheader("📍 공실 위치 및 주변 시설 (Kakao 기반)")
    with st.spinner("주변 시설 정보를 불러오는 중입니다..."):
        m = folium.Map(location=[lat, lon], zoom_start=14)

        folium.Marker(
            location=[lat, lon],
            popup=f"<b>추천 공실</b><br>{address}",
            icon=folium.Icon(color="gray", icon="home", prefix="fa")
        ).add_to(m)

        folium.Circle(
            radius=3000,
            location=[lat, lon],
            color="#555",
            fill=True,
            fill_opacity=0.08
        ).add_to(m)

        kakao_keywords = {
            "병원": "black",
            "학교": "cadetblue",
            "영화관": "red",
            "전시회관": "blue",
            "공방": "purple",
            "공원": "green",
            "쇼핑몰": "orange"
        }

        for keyword, color in kakao_keywords.items():
            places = search_places_kakao(keyword, lat, lon)
            for p in places:
                try:
                    y = float(p["y"])
                    x = float(p["x"])
                    folium.Marker(
                        location=[y, x],
                        popup=f"{keyword} - {p['place_name']}",
                        icon=folium.Icon(color=color, icon="info-sign")
                    ).add_to(m)
                except Exception as e:
                    print("좌표 변환 실패:", e)

        st_folium(m, width=800, height=600)

    st.subheader("📊 구성원별 점수")
    chart_df = pd.DataFrame({
        "구성원": [f"구성원 {i+1}" for i in range(len(member_scores))],
        "점수": member_scores
    })
    st.bar_chart(chart_df.set_index("구성원"))
