import json
import requests
import time
import os

# ⚠️ 여기에 발급받은 API 키와 검색 엔진 ID를 입력하세요.
API_KEY = "AIzaSyC4cM9vOtqRH8mKDe-OcibzXg69w6lk5nc"  # 실제 API 키로 변경해야 합니다.
CX_ID = "d5401b01f32d34389"      # 실제 검색 엔진 ID로 변경해야 합니다.

def search_image_url(query):
    """Google Custom Search API를 사용하여 이미지 URL을 검색합니다."""
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "q": query,
        "key": API_KEY,
        "cx": CX_ID,
        "searchType": "image",
        "num": 1  # 첫 번째 검색 결과만 가져옵니다.
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # HTTP 오류가 발생하면 예외 발생
        search_results = response.json()
        if 'items' in search_results and search_results['items']:
            return search_results['items'][0]['link']
    except requests.exceptions.RequestException as e:
        print(f"API 호출 중 오류 발생: {e}")
    return None

def process_json_file(input_path, output_path):
    """JSON 파일의 각 항목에 이미지 URL을 추가하고 저장합니다."""
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        updated_data = []

        for item in data:
            search_query = item.get('name_ko')
            
            if search_query:
                # [수정됨] 검색어를 "[찜질방 이름] 사우나"로 조합합니다.
                full_query = f"{search_query} 사우나"
                image_url = search_image_url(full_query)
                
                if image_url:
                    item['image_url'] = image_url
                    print(f"✔️ '{full_query}' 이미지 URL 추가 완료.")
                else:
                    print(f"⚠️ '{full_query}' 이미지 URL을 찾을 수 없습니다.")
                
                time.sleep(1) # API 호출 제한을 피하기 위해 1초 간격 두기
            else:
                print(f"- 검색어('name_ko')가 없어 건너뜁니다.")
            
            updated_data.append(item)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(updated_data, f, ensure_ascii=False, indent=4)
        print(f"\n✅ 수정된 데이터가 '{output_path}'에 저장되었습니다.")

    except FileNotFoundError:
        print(f"❌ 파일을 찾을 수 없습니다: {input_path}")
    except json.JSONDecodeError:
        print(f"❌ JSON 파일 형식이 올바르지 않습니다: {input_path}")



# 🚀 스크립트 실행
if __name__ == "__main__":
    # 어떤 위치에서 실행해도 파일을 정확히 찾도록 절대 경로를 사용합니다.
    basedir = os.path.abspath(os.path.dirname(__file__))
    input_file = os.path.join(basedir, 'static', 'my_data.json')
    output_file = os.path.join(basedir, 'static', 'updated_my_data.json')
    
    process_json_file(input_file, output_file)
