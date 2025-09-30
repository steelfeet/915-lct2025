import requests

import config


# ГАПОУ НППК, улица Ленина, 11
start_lat = "52.535482"
start_long = "31.937159"

# 100 м. вправо
# 52.535410, 31.938395
# 31.9384 - 31.9372 = 0.0012

# 100 м. вниз
# 52.534510, 31.936830
# 52.5355 - 52.5345 = 0.001

params = {
    'lat': start_lat,
    'long': start_long,
    'start_time': "",
    'end_time': "",
    'radius': 100,
    'sort': 0,
    'count': 1000,
    'access_token': config.vk_token,
    'v': "5.199"
}

r = requests.get('https://api.vk.com/method/photos.search', params=params).json()

count = r['response']['count']
print(f"Всего: {count}")

n = 0
for item in r['response']['items']:
    orig_photo = item["orig_photo"]
    n += 1
print(f"в первом запросе: {n}")