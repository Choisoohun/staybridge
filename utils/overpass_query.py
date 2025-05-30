import requests
import streamlit as st

OVERPASS_URL = "https://overpass.kumi.systems/api/interpreter"

@st.cache_data(show_spinner=False)
def get_facility_count(facility_tag, lat, lon, radius=3000, return_elements=False):
    query = f"""
    [out:json][timeout:10];
    node[{facility_tag}](around:{radius},{lat},{lon});
    out;
    """

    try:
        response = requests.get(OVERPASS_URL, params={"data": query}, timeout=15)
        response.raise_for_status()
        data = response.json()
        elements = data.get("elements", [])
        return (len(elements), elements) if return_elements else len(elements)
    except requests.exceptions.Timeout:
        st.warning(f"⚠️ 시설 요청 타임아웃: {facility_tag}")
        return (0, []) if return_elements else 0
    except Exception as e:
        print("Overpass API 오류:", e)
        return (0, []) if return_elements else 0
