import json

with open('static/my_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 제주도 관련 주소 필터링 (address_ko에 '제주' 포함) + 이미지 URL이 '이미지 없음'이 아닌 것만
jeju_with_image = [
    item for item in data
    if '제주' in item['address_ko'] and item['image_url'] != '이미지 없음'
]

# 결과 저장
with open('static/jeju_with_image.json', 'w', encoding='utf-8') as f:
    json.dump(jeju_with_image, f, ensure_ascii=False, indent=4)

print(f"제주도 + 이미지 URL 있는 항목 {len(jeju_with_image)}개 저장 완료.")