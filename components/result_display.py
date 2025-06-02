import os
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

from utils.score_calculator import calculate_scores
from utils.overpass_query import get_facility_elements

# ─────────────────────────────────────────────────────────────────────────────
# 취미별 태그 키 & 마커 색상 & 팝업 라벨 매핑
HOBBY_TAG_COLOR_LABEL_MAP = {
    "영화": {"tag": "cinema",  "color": "red",    "label": "영화관"},
    "전시": {"tag": "gallery", "color": "blue",   "label": "전시회장"},
    # 산책: park → 팝업 “공원”
    "산책": {"tag": "park",    "color": "green",  "label": "공원"},
    "공예": {"tag": "craft",   "color": "purple", "label": "공방"},
    # 쇼핑: mall → 팝업 “백화점 / 쇼핑몰”
    "쇼핑": {"tag": "mall",    "color": "orange", "label": "백화점 / 쇼핑몰"}
}
ALL_HOBBIES = list(HOBBY_TAG_COLOR_LABEL_MAP.keys())
# ─────────────────────────────────────────────────────────────────────────────

def display_results(user_inputs, vacant_data):
    """
    1) calculate_scores()로 상위 5개 공실 추출 → 표로 표시
    2) “📍 선택된 공실 지도 보기” 버튼을 누르면 지도가 계속 표시됨 (사라지지 않음)
    3) 취미 중 “산책(park) / 쇼핑(mall) / 영화(cinema) / 전시(gallery) / 공예(craft)” 모두 
       node 또는 way/relation의 center를 이용해 **시설당 마커 하나**만 찍도록 처리
    4) 범례(legend) 삭제
    """

    # ─────────────────────────────────────────────────────────────────────────
    # 1) 점수 계산 및 상위 5개 추출
    results = calculate_scores(user_inputs, vacant_data)
    top5 = sorted(results, key=lambda x: x["score"], reverse=True)[:5]

    # ─────────────────────────────────────────────────────────────────────────
    # 2) 추천 공실 목록 표 (주소+점수) - 인덱스를 “1순위, 2순위, …” 로 변경
    st.subheader("🏘️ 추천 공실 목록 (상위 5개)")
    df = pd.DataFrame(top5)[["address", "score"]].rename(
        columns={"address": "주소", "score": "점수"}
    )
    df.index = [f"{i+1}순위" for i in range(len(df))]
    st.dataframe(df, use_container_width=True)

    # ─────────────────────────────────────────────────────────────────────────
    # 3) 드롭다운: “주소 (점수: xx.xx)” 선택
    options = [f"{item['address']} (점수: {item['score']})" for item in top5]
    selected = st.selectbox("➤ 지도로 볼 공실을 선택하세요:", options=options)
    chosen = top5[options.index(selected)]
    lat, lon, address = chosen["latitude"], chosen["longitude"], chosen["address"]

    # 세션 스테이트 초기화 (없으면 False 로 세팅)
    if "show_map" not in st.session_state:
        st.session_state.show_map = False

    # ─────────────────────────────────────────────────────────────────────────
    # 4) “📍 선택된 공실 지도 보기” 버튼을 누르면 show_map=True 로 설정
    if st.button("📍 선택된 공실 지도 보기"):
        st.session_state.show_map = True

    # ─────────────────────────────────────────────────────────────────────────
    # 5) show_map=True 일 때만 지도 그리기
    if st.session_state.show_map:
        # (a) Folium 지도 생성
        st.subheader(f"📍 '{address}' 주변 시설 지도")
        m = folium.Map(location=[lat, lon], zoom_start=13)

        # (b) 추천 공실 마커 (검은색 홈 아이콘)
        folium.Marker(
            location=[lat, lon],
            popup=f"<b>추천 공실</b><br>{address}",
            icon=folium.Icon(color="black", icon="home", prefix="fa"),
        ).add_to(m)

        # (c) 반경 2km 원 (반투명 회색)
        folium.Circle(
            radius=2000,
            location=[lat, lon],
            color="#555555",
            fill=True,
            fill_opacity=0.08,
        ).add_to(m)

        # ─────────────────────────────────────────────────────────────────────
        # (d) 취미별 시설 마커 추가
        for hobby in ALL_HOBBIES:
            mapping = HOBBY_TAG_COLOR_LABEL_MAP[hobby]
            tag = mapping["tag"]
            color = mapping["color"]
            popup_label = mapping["label"]

            # ① get_facility_elements(tag, …) 로 node/way/relation 요소 리스트 획득
            elements = get_facility_elements(tag, lat, lon, radius=2000)

            # ② ‘시설당 한 개의 마커’만 찍기 위해 seen 집합으로 중복 좌표 제거
            seen = set()
            for elem in elements:
                # (1) node 타입: elem["lat"], elem["lon"]
                if elem.get("type") == "node" and "lat" in elem and "lon" in elem:
                    coord = (round(elem["lat"], 6), round(elem["lon"], 6))
                    if coord in seen:
                        continue
                    seen.add(coord)
                    folium.Marker(
                        location=[elem["lat"], elem["lon"]],
                        popup=popup_label,
                        icon=folium.Icon(color=color, icon="info-sign"),
                    ).add_to(m)

                # (2) way / relation 타입: elem["center"]["lat"], elem["center"]["lon"]
                elif elem.get("type") in ("way", "relation") and "center" in elem:
                    c = elem["center"]
                    coord = (round(c["lat"], 6), round(c["lon"], 6))
                    if coord in seen:
                        continue
                    seen.add(coord)
                    folium.Marker(
                        location=[c["lat"], c["lon"]],
                        popup=popup_label,
                        icon=folium.Icon(color=color, icon="info-sign"),
                    ).add_to(m)

            # → 이렇게 하면 “전시회장”, “영화관”, “공방”, “산책(공원)”, “쇼핑(몰)” 모두 
            #    하나의 시설당 하나의 녹색/주황색/빨강/파랑/보라 마커가 찍힙니다.

        # ─────────────────────────────────────────────────────────────────────
        # (e) 학령기/시니어 시설: 학교, 병원 (중복 제거 + node 타입만)
        has_kid = any(m["age"] < 20 for m in user_inputs["members"])
        has_senior = any(m["age"] >= 65 for m in user_inputs["members"])

        if has_kid:
            schools = get_facility_elements("school", lat, lon, radius=2000)
            seen_school = set()
            for s in schools:
                if s.get("type") != "node":
                    continue
                if "lat" not in s or "lon" not in s:
                    continue
                coord = (round(s["lat"], 6), round(s["lon"], 6))
                if coord in seen_school:
                    continue
                seen_school.add(coord)
                folium.Marker(
                    location=[s["lat"], s["lon"]],
                    popup="학교",
                    icon=folium.Icon(color="cadetblue", icon="book", prefix="fa"),
                ).add_to(m)

        if has_senior:
            hospitals = get_facility_elements("hospital", lat, lon, radius=1000)
            seen_hosp = set()
            for h in hospitals:
                if h.get("type") != "node":
                    continue
                if "lat" not in h or "lon" not in h:
                    continue
                coord = (round(h["lat"], 6), round(h["lon"], 6))
                if coord in seen_hosp:
                    continue
                seen_hosp.add(coord)
                folium.Marker(
                    location=[h["lat"], h["lon"]],
                    popup="병원",
                    icon=folium.Icon(color="black", icon="plus-sign", prefix="fa"),
                ).add_to(m)

        # ─────────────────────────────────────────────────────────────────────
        # (f) Folium 지도를 Streamlit에 렌더링
        st_folium(m, width=800, height=600)

    # “지도 보기”를 누르지 않으면 지도 로직은 실행되지 않음
    return top5
