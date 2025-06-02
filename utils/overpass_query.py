# utils/overpass_query.py

import requests
import streamlit as st

OVERPASS_URL = "https://overpass.kumi.systems/api/interpreter"

# ─────────────────────────────────────────────────────────────────────────────
# 태그 매핑: facility_tag → (OSM key, OSM value)
# – 산책(공원) → leisure=park
# – 쇼핑(몰) → shop=mall
# – 영화관 → amenity=cinema
# – 전시회장 → tourism=gallery
# – 공방 → craft=workshop
TAG_MAPPING = {
    "cinema":  ("amenity", "cinema"),
    "gallery": ("tourism", "gallery"),
    "craft":   ("craft", "workshop"),
    "park":    ("leisure", "park"),
    "mall":    ("shop", "mall"),
    "hospital":("amenity", "hospital"),
    "school":  ("amenity", "school")
}
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_data(show_spinner=False)
def get_facility_elements(facility_tag: str, lat: float, lon: float, radius: int = 2000) -> list:
    """
    facility_tag에 해당하는 요소들을 Overpass API로 조회하여 'elements' 리스트를 반환.
    - facility_tag in {"park", "mall", "cinema", "gallery", "craft"}일 경우, 
      'out center;'를 사용하여 way/relation의 중심 좌표를 포함시킴.
    - 반환값: Overpass JSON의 'elements' 리스트
    """
    mapping = TAG_MAPPING.get(facility_tag)
    if not mapping:
        return []

    key, value = mapping

    # park, mall, cinema, gallery, craft → out center 를 사용하여 center 정보 얻기
    if facility_tag in ("park", "mall", "cinema", "gallery", "craft"):
        query = f"""
        [out:json][timeout:60];
        (
          node["{key}"="{value}"](around:{radius},{lat},{lon});
          way["{key}"="{value}"](around:{radius},{lat},{lon});
          relation["{key}"="{value}"](around:{radius},{lat},{lon});
        );
        out center;
        """
    else:
        # hospital, school 등 → 기존 방식
        query = f"""
        [out:json][timeout:60];
        (
          node["{key}"="{value}"](around:{radius},{lat},{lon});
          way["{key}"="{value}"](around:{radius},{lat},{lon});
          relation["{key}"="{value}"](around:{radius},{lat},{lon});
        );
        out body;
        >;
        out skel qt;
        """

    try:
        response = requests.get(OVERPASS_URL, params={"data": query}, timeout=60)
        response.raise_for_status()
        data = response.json()
        return data.get("elements", [])
    except requests.exceptions.Timeout:
        st.warning(f"⚠️ Overpass 요청 시간 초과: {facility_tag}")
        return []
    except Exception as e:
        print(f"Overpass API 오류 ({facility_tag}):", e)
        return []


@st.cache_data(show_spinner=False)
def get_facility_count(facility_tag: str, lat: float, lon: float, radius: int = 2000) -> int:
    """
    facility_tag 요소의 개수를 반환 (count 용도로만 사용).
    """
    elements = get_facility_elements(facility_tag, lat, lon, radius)
    return len(elements)


@st.cache_data(show_spinner=False)
def get_multiple_facility_counts(facility_tags: list, lat: float, lon: float, radius: int = 2000) -> dict:
    """
    여러 facility_tag를 각각 get_facility_count로 조회하여 개수만 모아서 dict로 반환.
    - 반환형: { 'cinema': int, 'gallery': int, 'park': int, ... }
    """
    counts = {}
    for tag in facility_tags:
        counts[tag] = get_facility_count(tag, lat, lon, radius)
    return counts
