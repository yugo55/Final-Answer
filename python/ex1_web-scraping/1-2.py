from selenium import webdriver
from selenium.webdriver.chrome import service
from selenium.webdriver.common.by import By
from  selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import re
import time
import socket
import ssl
import urllib

CHROMEDRIVER = "./chromedriver.exe"
chrome_service = service.Service(executable_path=CHROMEDRIVER)
driver = webdriver.Chrome(service=chrome_service)
driver.get("https://r.gnavi.co.jp/area/jp/rs/?date=20240626")

def get_email():
  all_table_a = driver.find_elements(by=By.CSS_SELECTOR, value=".basic-table a")
  email = ""
  for a in all_table_a:
    if "mailto" in a.get_attribute("href"):
      email = a.get_attribute("href").replace("mailto:", "")
  return email

def get_restaurant_url():
  all_restaurant_url = driver.find_elements(by=By.CSS_SELECTOR, value="div#sv ul#sv-site a")
  restaurant_url = ""
  for url in all_restaurant_url:
    if url.text == "オフィシャルページ":
      restaurant_url = url.get_attribute("href")
      break
  return restaurant_url

def ssl_exists():
  parsed_url = urllib.parse.urlparse(indiv_page_url)
  hostname = parsed_url.hostname
  port = parsed_url.port if parsed_url.port else 443
  try:
    context = ssl.create_default_context()
    with socket.create_connection((hostname, port)) as sock:
      with context.wrap_socket(sock, server_hostname=hostname) as ssock:
        cert = ssock.getpeercert()
        if cert:
          return True
  except ssl.SSLError:
    return False
  except Exception as e:
    print(f"Error: {e}")
    return False

restaurants_info = []
while True:
  # 店舗ページのurlを取得
  restaurants_a = driver.find_elements(by=By.CSS_SELECTOR, value=".style_titleLink__oiHVJ")
  restaurants_url_array = [a.get_attribute("href") for a in restaurants_a]
  for indiv_page_url in restaurants_url_array:
    print(indiv_page_url)
    time.sleep(3)
    driver.get(indiv_page_url)

    WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.CSS_SELECTOR, "#info-name")))

    # 店舗名
    name = driver.find_element(by=By.ID, value="info-name").text

    # メールアドレス
    email = get_email()

    # 電話番号
    phone_num = driver.find_element(by=By.CSS_SELECTOR, value="span.number").text

    # 住所
    address = driver.find_element(by=By.CSS_SELECTOR, value="span.region").text
    # 都道府県
    start_with_kyoto = address.startswith("京都")
    pref_regexp = r"^.+?(道|府|県)" if start_with_kyoto else r"^.+?(都|道|府|県)"
    pref = re.match(pref_regexp, address).group()
    # 市区町村
    city_regexp = r"(?<=道|府|県)\D+" if start_with_kyoto else r"(?<=都|道|府|県)\D+"
    city = re.search(city_regexp, address).group()
    # 番地
    street_address = re.search(r"\d+(-|\d)+", address).group() if re.search(r"\d+(-|\d)+", address) is not None else ""

    # 建物名
    try:
      building = driver.find_element(by=By.CSS_SELECTOR, value="span.locality").text
    except:
      building = ""

    # URL
    restaurant_url = get_restaurant_url()
    
    # SSL
    has_ssl = ssl_exists()

    restaurants_info.append({
      "店舗名": name,
      "電話番号": phone_num,
      "メールアドレス": email,
      "都道府県": pref,
      "市区町村": city,
      "番地": street_address,
      "建物名": building,
      "URL": restaurant_url,
      "SSL": has_ssl
    })

    if is_50_info := len(restaurants_info) == 50:
      break

    driver.back()
  
  if is_50_info:
    break
    
  next_btn = driver.find_element(by=By.CSS_SELECTOR, value="ul.style_pages__Y9bbR li:nth-last-child(2) a")
  next_btn.click()

df = pd.DataFrame(restaurants_info)
df.to_csv("1-2.csv", index = False)

driver.quit()
