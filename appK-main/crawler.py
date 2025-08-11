# crawler.py (카카오맵용: 무한 루프 방지 기능 추가된 최종 완성 버전)

import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import requests

# --- 설정 부분 ---
SEARCH_KEYWORDS = ["제주도 찜질방","제주 찜질방"]

# --- 셀레니움 드라이버 설정 ---
def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--log-level=3")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920x1080")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

# --- 메인 크롤링 함수 (무한 루프 방지 로직 추가) ---
def crawl_kakao_maps():
    driver = setup_driver()
    all_saunas = []
    
    driver.get("https://map.kakao.com/")
    time.sleep(2)
    
    for keyword in SEARCH_KEYWORDS:
        print(f"\n'{keyword}' 키워드로 검색을 시작합니다...")
        
        try:
            search_input = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "input.query")))
            search_input.clear()
            search_input.send_keys(keyword)
            search_input.send_keys(Keys.ENTER)
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "info.search.place.list")))
        except Exception as e:
            print(f"검색창을 찾거나 검색을 실행하는 데 실패했습니다: {e}")
            continue

        try:
            more_button = driver.find_element(By.ID, "info.search.place.more")
            driver.execute_script("arguments[0].click();", more_button)
            print("'더보기' 버튼 클릭.")
            time.sleep(2)
        except Exception:
            print("'더보기' 버튼이 없습니다.")

        page_num = 1
        last_page_content_id = None # 이전 페이지의 첫번째 내용을 저장할 변수

        while True:
            html = driver.page_source
            soup = BeautifulSoup(html, "html.parser")
            sauna_items = soup.select("ul.placelist > li.PlaceItem")

            if not sauna_items:
                print("결과 목록을 찾을 수 없습니다.")
                break

            # ▼▼▼▼▼ 무한 루프 방지 로직 ▼▼▼▼▼
            first_item_name = sauna_items[0].select_one('a.link_name').get_text(strip=True) if sauna_items[0].select_one('a.link_name') else ''
            current_page_content_id = first_item_name # 현재 페이지의 첫번째 장소 이름으로 ID 생성

            if current_page_content_id == last_page_content_id:
                print("페이지 내용이 이전과 동일하여 무한 루프 방지를 위해 종료합니다.")
                break
            
            last_page_content_id = current_page_content_id
            # ▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲

            print(f"--- {page_num} 페이지: {len(sauna_items)}개 정보 수집 ---")
            for item in sauna_items:
                name = item.select_one('a.link_name').get_text(strip=True) if item.select_one('a.link_name') else ''
                address = item.select_one('p[data-id="address"]').get_text(strip=True) if item.select_one('p[data-id="address"]') else ''
                
                if name and address and not any(s['name_ko'] == name and s['address_ko'] == address for s in all_saunas):
                    all_saunas.append({
                        "name_ko": name,
                        "address_ko": address,
                        "image_url": "이미지 없음",
                        "region": keyword
                    })

            try:
                next_button_xpath = "//a[@class='ACTIVE']/following-sibling::*[1]"
                next_button = driver.find_element(By.XPATH, next_button_xpath)

                if next_button.tag_name == 'button' and 'disabled' in next_button.get_attribute('class'):
                    print("마지막 페이지입니다. 다음 키워드로 넘어갑니다.")
                    break
                
                driver.execute_script("arguments[0].click();", next_button)
                page_num += 1
                time.sleep(2)

            except Exception:
                print("더 이상 이동할 페이지를 찾지 못했습니다. 다음 키워드로 넘어갑니다.")
                break

    driver.quit()
    return all_saunas


# --- 번역 및 파일 저장 함수 ---
def translate_and_save(sauna_list):
    if not sauna_list:
        print("번역할 데이터가 없습니다.")
        return

    print("\n크롤링 완료. 번역을 시작합니다...")
    translated_list = []
    processed = set()

    def libretranslate(text, source, target):
        url = "https://libretranslate.de/translate"
        payload = {
            "q": text,
            "source": source,
            "target": target,
            "format": "text"
        }
        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            data = response.json()
            if "translatedText" in data:
                return data["translatedText"]
            else:
                print(f"LibreTranslate 응답 오류: {data}")
                return None
        except Exception as e:
            print(f"LibreTranslate 오류: {e}")
            return None

    for sauna in sauna_list:
        if (sauna['name_ko'], sauna['address_ko']) in processed:
            continue
        name_en = libretranslate(sauna['name_ko'], 'ko', 'en')
        address_en = libretranslate(sauna['address_ko'], 'ko', 'en')
        name_ja = libretranslate(sauna['name_ko'], 'ko', 'ja')
        address_ja = libretranslate(sauna['address_ko'], 'ko', 'ja')
        if None in [name_en, address_en, name_ja, address_ja]:
            print(f"'{sauna['name_ko']}' 번역 실패: 일부 언어에서 번역을 건너뜁니다.")
            continue
        translated_list.append({
            "name_ko": sauna['name_ko'],
            "name_en": name_en,
            "name_ja": name_ja,
            "address_ko": sauna['address_ko'],
            "address_en": address_en,
            "address_ja": address_ja,
            "image_url": sauna['image_url']
        })
        processed.add((sauna['name_ko'], sauna['address_ko']))
        print(f"'{sauna['name_ko']}' 번역 완료.")
        time.sleep(0.5)

    with open('saunas_data.json', 'w', encoding='utf-8') as f:
        json.dump(translated_list, f, ensure_ascii=False, indent=4)

    print(f"\n모든 작업 완료! 총 {len(translated_list)}개의 데이터가 saunas_data.json 파일에 저장되었습니다.")


# --- 스크립트 실행 ---
if __name__ == "__main__":
    crawled_data = crawl_kakao_maps()
    translate_and_save(crawled_data)