from utils.overpass_query import get_facility_count

def base_score_from_count(count):
    return min(count * 10, 100)

def apply_hobby_bonus(hobby, facility_type, base_score):
    hobby_map = {
        "영화": "cinema",
        "산책": "park",
        "전시": "gallery",
        "공예": "craft",
        "쇼핑": "mall"
    }
    return base_score * 1.5 if hobby_map.get(hobby) == facility_type else base_score

def hobby_to_type(hobby):
    return {
        "영화": "amenity=cinema",
        "산책": "leisure=park",
        "전시": "tourism=gallery",
        "공예": "craft=pottery",
        "쇼핑": "shop=mall"
    }.get(hobby, "")

def calculate_scores(user_inputs, vacant_data):
    members = user_inputs["members"]
    region_keyword = user_inputs["region_keyword"]
    subway_required = user_inputs["subway_required"]

    results = []

    for _, row in vacant_data.iterrows():
        lat, lon = row["위도"], row["경도"]
        address = row.get("주소", "")

        # ✅ 필수 지역 조건 필터링: 해당 지역 아니면 추천 대상에서 제외
        if region_keyword and region_keyword not in address:
            continue

        total_score = 0
        total_weight = 0
        member_scores = []  # 구성원별 점수 저장

        for member in members:
            age = member["age"]
            hobbies = member["hobby"]
            weight = member["importance"]

            member_score = 0

            # 나이 기반 점수
            if age < 20:
                count = get_facility_count("amenity=school", lat, lon, radius=3000)
                member_score += base_score_from_count(count)
            elif age >= 65:
                count = get_facility_count("amenity=hospital", lat, lon, radius=1000)
                member_score += base_score_from_count(count)

            # 취미 기반 점수
            for h in hobbies:
                tag = hobby_to_type(h)
                if tag:
                    count = get_facility_count(tag, lat, lon, radius=3000)
                    base = base_score_from_count(count)
                    member_score += apply_hobby_bonus(h, tag.split('=')[1], base)

            # 가중치 반영
            total_score += member_score * weight
            total_weight += weight
            member_scores.append(round(member_score, 2))

        avg_score = total_score / total_weight if total_weight else 0

        # 지하철 조건 간단 감점 (실제 연동은 추후)
        if subway_required:
            avg_score *= 0.9

        results.append({
            "address": address,
            "latitude": lat,
            "longitude": lon,
            "score": round(avg_score, 2),
            "member_scores": member_scores
        })

    return sorted(results, key=lambda x: x["score"], reverse=True)
