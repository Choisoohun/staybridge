from utils.overpass_query import get_multiple_facility_counts

def base_score_from_count(count: int, weight_per_unit: int = 3, max_score: int = 100) -> int:
    """
    시설 개수(count)에 weight_per_unit(가중치)를 곱한 뒤 max_score 이하로 제한.
    """
    return min(count * weight_per_unit, max_score)

def hobby_to_type(hobby: str) -> str:
    """
    한글 취미 이름을 OSM 태그 키워드로 변환.
    - "산책"은 이제 leisure=park
    - "쇼핑"은 shop=mall
    """
    return {
        "영화": "cinema",
        "전시": "gallery",
        "산책": "park",
        "공예": "craft",
        "쇼핑": "mall"
    }.get(hobby, "")

def calculate_scores(user_inputs: dict, vacant_data) -> list:
    """
    user_inputs: {
      'members': [ {'age':int, 'hobby':List[str], 'importance':int}, ... ],
      'region_keyword': str
    }
    vacant_data: pandas.DataFrame(address, latitude, longitude)

    - 각 공실에 대해 한 번만 Overpass API 호출(묶음 조회)해서 필요한 태그 개수를 가져옴
    - 태그 조회 범위는 반경 2000m
    - 구성원별 점수를 계산해 평균화 후 반환
    """

    members = user_inputs["members"]
    region_keyword = user_inputs["region_keyword"]

    results = []
    ALL_HOBBY_TYPES = [hobby_to_type(h) for h in ["영화", "산책", "전시", "공예", "쇼핑"] if hobby_to_type(h)]

    for _, row in vacant_data.iterrows():
        lat = row["latitude"]
        lon = row["longitude"]
        address = row.get("address", "")

        # (A) 필요한 태그 결정 (반경 2000m)
        need_school = any(m["age"] < 20 for m in members)
        need_hospital = any(m["age"] >= 65 for m in members)

        tags_radius_2000 = ALL_HOBBY_TYPES.copy()
        if need_school:
            tags_radius_2000.append("school")

        tags_radius_1000 = []
        if need_hospital:
            tags_radius_1000.append("hospital")

        # (B) Overpass 묶음 조회 (간단히 개수만 구함)
        counts_2000 = {}
        if tags_radius_2000:
            counts_2000 = get_multiple_facility_counts(
                facility_tags=tags_radius_2000,
                lat=lat,
                lon=lon,
                radius=2000
            )
        counts_1000 = {}
        if tags_radius_1000:
            counts_1000 = get_multiple_facility_counts(
                facility_tags=tags_radius_1000,
                lat=lat,
                lon=lon,
                radius=1000
            )

        # (C) 구성원별 점수 계산
        total_score = 0
        total_weight = 0

        for member in members:
            age = member["age"]
            hobbies = member["hobby"]
            weight = member["importance"]
            member_score = 50  # 기본점수

            # 나이 조건 점수 (학교/병원)
            if age < 20:
                school_count = counts_2000.get("school", 0)
                member_score += base_score_from_count(school_count, weight_per_unit=5)
            elif age >= 65:
                hosp_count = counts_1000.get("hospital", 0)
                member_score += base_score_from_count(hosp_count, weight_per_unit=5)

            # 취미 시설 점수 (반경 2000m)
            for hobby_name in ["영화", "산책", "전시", "공예", "쇼핑"]:
                tag = hobby_to_type(hobby_name)
                if not tag:
                    continue
                count = counts_2000.get(tag, 0)
                if hobby_name in hobbies:
                    member_score += base_score_from_count(count, weight_per_unit=8)
                else:
                    member_score += base_score_from_count(count, weight_per_unit=5)

            total_score += member_score * weight
            total_weight += weight

        avg_score = total_score / total_weight if total_weight else 0

        # (D) 지역 키워드 미포함 시 20% 감점
        if region_keyword and region_keyword not in address:
            avg_score *= 0.8

        results.append({
            "address": address,
            "latitude": lat,
            "longitude": lon,
            "score": round(avg_score, 2)
        })

    return sorted(results, key=lambda x: x["score"], reverse=True)
