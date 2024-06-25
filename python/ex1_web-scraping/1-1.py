import requests
from bs4 import BeautifulSoup
import re
import time
import socket
import ssl
import urllib
import pandas as pd

headers = {
  "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
}

top_url = "https://r.gnavi.co.jp/area/jp/rs/?date=20240624"
res = requests.get(top_url, headers=headers)
html = BeautifulSoup(res.content, "html.parser")

# 1ページ目の店の店舗urlを取得
restaurants_a = html.select(".style_restaurant__SeIVn a.style_titleLink__oiHVJ")
restaurants_url_array = [a.get("href") for a in restaurants_a]

# 2ページ目以降の店の店舗urlを取得
i = 2
while len(restaurants_url_array) < 50:
  url = f"https://r.gnavi.co.jp/area/jp/rs/?date=20240624&p={i}"
  time.sleep(3)
  res = requests.get(url, headers=headers)
  html = BeautifulSoup(res.content, "html.parser")
  restaurants_a = html.select(".style_restaurant__SeIVn a.style_titleLink__oiHVJ")
  for a in restaurants_a:
    restaurants_url_array.append(a.get("href"))
    if len(restaurants_url_array) == 50:
      break
  i += 1

restaurants_info = []
for url in restaurants_url_array:
  print(url)
  time.sleep(3)
  res = requests.get(url, headers=headers)
  html = BeautifulSoup(res.content, "html.parser")
  name = html.select_one("p.fn").text
  phone_num = html.select_one("span.number").text
  all_table_a = html.select(".basic-table a")
  email = ""
  for a in all_table_a:
    if "mailto" in a.get("href"):
      email = a.get("href").replace("mailto:", "")
  address = html.select_one("span.region").text
  pref = re.match(r"^.+(都|道|府|県)", address).group()
  city = re.search(r"(?<=都|道|府|県)\D+", address).group()
  street_address = re.search(r"\d+(-|\d)+$", address).group() if re.search(r"\d+(-|\d)+", address) is not None else ""
  building_ele = html.select_one("span.locality")
  building = building_ele.text if building_ele else ""
  restaurant_url = ""
  parsed_url = urllib.parse.urlparse(url)
  hostname = parsed_url.hostname
  port = parsed_url.port if parsed_url.port else 443
  try:
    context = ssl.create_default_context()
    with socket.create_connection((hostname, port)) as sock:
      with context.wrap_socket(sock, server_hostname=hostname) as ssock:
        cert = ssock.getpeercert()
        if cert:
          has_ssl = True
  except ssl.SSLError:
    has_ssl = False
  except Exception as e:
    print(f"Error: {e}")
    has_ssl = False
  restaurants_info.append({"店舗名": name, "電話番号": phone_num, "メールアドレス": email, "都道府県": pref, "市区町村": city, "番地": street_address, "建物名": building, "URL": restaurant_url, "SSL": has_ssl})

df = pd.DataFrame(restaurants_info)
df.to_csv("1-1.csv", index = False)
