import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import threading
import requests

def install_resources():
    os.system('pip install selenium')

def translate_to_english(text):
    url = "https://translate.googleapis.com/translate_a/single"
    params = {
        "client": "gtx",
        "sl": "zh-TW",
        "tl": "en",
        "dt": "t",
        "q": text
    }
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            result = response.json()
            return result[0][0][0]
        else:
            print("翻譯API請求失敗，將直接用原文搜尋。")
            return text
    except Exception as e:
        print("翻譯過程出現錯誤：", e)
        return text

def get_search_terms():
    term = input("請輸入搜尋詞（中英文皆可）：")
    # 判斷是否包含中文（任一中文字元）
    if any('\u4e00' <= ch <= '\u9fff' for ch in term):
        ndltd_term = term
        wos_term = translate_to_english(term)
        print(f"Web of Science 將自動使用英文搜尋詞：{wos_term}")
    else:
        ndltd_term = term
        wos_term = term
        print(f"偵測到英文，兩站皆用英文搜尋詞：{term}")
    return ndltd_term, wos_term

def ndltd_crawler(search_term):
    chrome_options = Options()
    chrome_options.add_argument("--incognito")

    # 禁用彈窗和通知
    prefs = {
        "profile.default_content_setting_values.notifications": 2,
        "profile.default_content_setting_values.popups": 2
    }
    chrome_options.add_experimental_option("prefs", prefs)

    # 啟用 Chrome 功能
    driver = webdriver.Chrome(options=chrome_options)
    try:
        driver.maximize_window()  # 設定瀏覽器為全螢幕模式
        driver.get("https://ndltd.ncl.edu.tw/cgi-bin/gs32/gsweb.cgi?o=d")
        time.sleep(5)  # 等待網頁載入

        # 找到正確的搜尋欄位並輸入關鍵字
        search_box = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "ysearchinput0"))
        )
        search_box.clear()
        search_box.send_keys(search_term)
        time.sleep(0.5)

        # 點擊正確的查詢按鈕（input[type='image']，id='gs32search'）
        search_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "gs32search"))
        )
        driver.execute_script("arguments[0].click();", search_button)
        time.sleep(5)  # 等待搜尋結果載入

        # 提交表單（有些網站需直接 submit form 才能觸發查詢）
        try:
            form = driver.find_element(By.NAME, "main")
            form.submit()
            time.sleep(5)
        except Exception as e:
            print("表單提交失敗，將嘗試點擊查詢按鈕：", e)
            search_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "input[type='button'][value='查詢']"))
            )
            driver.execute_script("arguments[0].click();", search_button)
            time.sleep(5)

        # 爬取搜尋結果
        try:
            rows = driver.find_elements(By.CSS_SELECTOR, "table#table1 tr")
            found = False
            for row in rows:
                cols = row.find_elements(By.TAG_NAME, "td")
                if len(cols) > 2:
                    print(' | '.join([col.text.strip() for col in cols]))
                    found = True
            if not found:
                print("未找到搜尋結果。")
        except Exception as e:
            print("爬取搜尋結果時出現錯誤：", e)

    except Exception as e:
        print("爬取過程中出現錯誤：", e)
    finally:
        print("瀏覽器保持開啟，請手動關閉。")
        try:
            while True:
                if len(driver.window_handles) == 0:  # 檢查瀏覽器視窗是否已關閉
                    print("瀏覽器已關閉，程式結束。")
                    break
                time.sleep(1)  # 保持程式運行
        except Exception as e:
            print("檢查瀏覽器狀態時出現錯誤：", e)

def web_of_science_crawler(search_term):
    chrome_options = Options()
    chrome_options.add_argument("--incognito")
    prefs = {
        "profile.default_content_setting_values.notifications": 2,
        "profile.default_content_setting_values.popups": 2
    }
    chrome_options.add_experimental_option("prefs", prefs)
    driver = webdriver.Chrome(options=chrome_options)
    try:
        driver.maximize_window()
        driver.get("https://www.webofscience.com/wos/woscc/basic-search")
        time.sleep(5)
        # Web of Science 搜尋框與按鈕
        search_box = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "search-option"))
        )
        search_box.clear()
        search_box.send_keys(search_term)
        time.sleep(0.5)
        # 點擊正確的搜尋按鈕
        search_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit'][data-ta='run-search']"))
        )
        driver.execute_script("arguments[0].click();", search_button)
        time.sleep(5)
        try:
            results = driver.find_elements(By.CSS_SELECTOR, "div.search-results")
            if results:
                for result in results:
                    print(result.text)
            else:
                print("Web of Science 未找到搜尋結果。")
        except Exception as e:
            print("Web of Science 爬取搜尋結果時出現錯誤：", e)
    except Exception as e:
        print("Web of Science 爬取過程中出現錯誤：", e)
    finally:
        print("Web of Science 瀏覽器保持開啟，請手動關閉。")
        try:
            while True:
                if len(driver.window_handles) == 0:
                    print("Web of Science 瀏覽器已關閉，程式結束。")
                    break
                time.sleep(1)
        except Exception as e:
            print("Web of Science 檢查瀏覽器狀態時出現錯誤：", e)

def run_both_crawlers():
    ndltd_term, wos_term = get_search_terms()
    t1 = threading.Thread(target=ndltd_crawler, args=(ndltd_term,))
    t2 = threading.Thread(target=web_of_science_crawler, args=(wos_term,))
    t1.start()
    t2.start()
    t1.join()
    t2.join()

if __name__ == "__main__":
    install_resources()
    run_both_crawlers()