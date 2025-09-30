import os, json, urllib
import time
import hashlib
import random
import requests

from urllib.parse import urlparse
from bs4 import BeautifulSoup


def get_url_html(url, use_cache=False, CACHE_DIR = os.path.join("D:\\", "cache")):

    url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()
    hash_path = os.path.join(CACHE_DIR, f"{url_hash}.html")
    cache_not_exist = False

    if use_cache:
        if os.path.isfile(hash_path):
            with open(hash_path, 'r', encoding="utf-8") as f:
                post_html = f.read()
        else:
            cache_not_exist = True

    if not(use_cache) or cache_not_exist:
        is_not_exec = True
        sleep_time = 1
        while is_not_exec:
            try:
                user_agent = random.choice(user_agents)
                host = urllib.parse.urlparse(url).netloc
                referer = f"https://{host}/"
                headers = {
                        "Host": str(host),
                        'User-Agent': str(user_agent),
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                        'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'Referer': str(referer),
                        'Upgrade-Insecure-Requests': '1',
                        'Connection': 'keep-alive'}

                response = requests.get(url, headers=headers)
                #response.encoding='windows-1251'
                is_not_exec = False
            except:
                print(f"{url} -> Ошибка сайта донора, ждем {sleep_time} с.")
                time.sleep(sleep_time)
                sleep_time += 1
        post_html = response.text
    
    if use_cache:
        with open(hash_path, 'w', encoding="utf-8") as f:
            f.write(post_html)

    return post_html



def post_url_html(url, data, use_cache=False, CACHE_DIR = os.path.join("D:\\", "cache")):

    url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()
    hash_path = os.path.join(CACHE_DIR, f"{url_hash}.html")
    cache_not_exist = False

    if use_cache:
        if os.path.isfile(hash_path):
            with open(hash_path, 'r', encoding="utf-8") as f:
                post_html = f.read()
        else:
            cache_not_exist = True

    if not(use_cache) or cache_not_exist:
        is_not_exec = True
        sleep_time = 1
        while is_not_exec:
            try:
                user_agent = random.choice(user_agents)
                host = urllib.parse.urlparse(url).netloc
                referer = f"https://{host}/"
                headers = {
                            'Host': 'goskatalog.ru',
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:136.0) Gecko/20100101 Firefox/136.0',
                            'Accept':'application/json, text/plain, */*',
                            'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
                            'Accept-Encoding': 'gzip, deflate, br, zstd',
                            'Content-Type': 'application/json;charset=utf-8',
                            'X-Requested-With': 'XMLHttpRequest',
                            'X-Ajax-Token': 'b8cb43252ea528218682e9bffa9fabff350576d9642abf12356c438d1c83e4b9',
                            'Content-Length': '111',
                            'Origin': 'https://goskatalog.ru',
                            'Connection': 'keep-alive',
                            'Referer': 'https://goskatalog.ru/portal/',
                            'Cookie': '_ym_uid=1741775318470136652; _ym_d=1741775318; session-cookie=182e36190d1f20564fc09bd504983c47702925673a29178436395f9a45f11e56bbdf57ec6928ae5dfe99d6998e6f8c1b; _ym_isad=2; _ym_visorc=w',
                            'Sec-Fetch-Dest': 'empty',
                            'Sec-Fetch-Mode': 'cors'
                        
                        }

                response = requests.post(url, data, headers=headers)
                #response.encoding='windows-1251'
                is_not_exec = False
            except:
                print(f"{url} -> Ошибка сайта донора, ждем {sleep_time} с.")
                time.sleep(sleep_time)
                sleep_time += 1
        post_html = response.text
    
    if use_cache:
        with open(hash_path, 'w', encoding="utf-8") as f:
            f.write(post_html)

    return post_html



def get_url_content(url):
    is_not_exec = True
    sleep_time = 1
    while is_not_exec:
        try:
            user_agent = random.choice(user_agents)
            referer = user_agent
            host = urllib.parse.urlparse(url).netloc
            headers = {
                    "Host": str(host),
                    'User-Agent': str(user_agent),
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Referer': str(referer),
                    'Upgrade-Insecure-Requests': '1',
                    'Connection': 'keep-alive'}

            response = requests.get(url, headers=headers)
            #response.encoding='windows-1251'
            is_not_exec = False
        except:
            # print(f"\nОшибка сайта донора контента, ждем {sleep_time} с.")
            time.sleep(sleep_time)
            sleep_time += 1
    post_content = response.content
        

    return post_content








photohost_domains = ["imgfoto.host", "postimg.cc", "vfl.ru", "ibb.co"]
# получение ссылки на изображение по ссылке на фотохостинг
def src_from_photohost(internal_url):
    domain = urlparse(internal_url).netloc
    domain = domain.replace("www.", "")

    # прямая ссылка на изображение
    if domain == "reviewdetector.ru":
        image_src = internal_url

    else:
        internal_html = get_url_html(internal_url)
        with open("internal.html", 'w', encoding='utf-8') as f:
            f.write(internal_html)


        if domain == "imgfoto.host":
            # <meta property="og:image" content="https://a.imgfoto.host/2025/03/24/1000115436.jpeg">
            internal_soup = BeautifulSoup(internal_html, "lxml")
            meta_soup = internal_soup.find("meta", {'property': 'og:image'})
            if meta_soup != None:
                image_src = meta_soup["content"]


        elif domain == "postimg.cc":
            internal_soup = BeautifulSoup(internal_html, "lxml")
            meta_soup = internal_soup.find("img", {'id': 'main-image'} )
            if meta_soup != None:
                image_src = meta_soup["src"]


        elif domain == "vfl.ru":
            internal_soup = BeautifulSoup(internal_html, "lxml")
            meta_soup = internal_soup.find("img", {'class': 'img-fluid'} )
            if meta_soup != None:
                image_src = meta_soup["src"]
                image_src = "https:" + image_src
            
        elif domain == "ibb.co":
            internal_soup = BeautifulSoup(internal_html, "lxml")
            meta_soup = internal_soup.find("meta", {'property': 'og:image'})
            if meta_soup != None:
                image_src = meta_soup["content"]
            

        else:
            image_src = None
            print(f"New photohost!! {domain}")
            input(internal_url)


    return image_src



















user_agents = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:45.0) Gecko/20100101 Firefox/45.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:86.0) Gecko/20100101 Firefox/86.0",
    "Mozilla/5.0 (Windows NT 5.1; rv:23.0) Gecko/20100101 Firefox/23.0",
    "Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/29.0.1547.62 Safari/537.36",
    "Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; WOW64; Trident/6.0)",
    "Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/6.0)",
    "Mozilla/5.0 (Windows NT 6.1; rv:23.0) Gecko/20100101 Firefox/23.0",
    "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/29.0.1547.62 Safari/537.36",
    "Opera/9.80 (Windows NT 5.1) Presto/2.12.388 Version/12.16",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/29.0.1547.62 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.22 (KHTML, like Gecko) Chrome/25.0.1364.172 YaBrowser/1.7.1364.21027 Safari/537.22",
    "Opera/9.80 (Windows NT 6.1; WOW64) Presto/2.12.388 Version/12.16",
    "Mozilla/5.0 (iPad; CPU OS 6_1_3 like Mac OS X) AppleWebKit/536.26 (KHTML, like Gecko) Version/6.0 Mobile/10B329 Safari/8536.25",
    "Opera/9.80 (Windows NT 6.1; WOW64) Presto/2.12.388 Version/12.15",
    "Mozilla / 5.0 (Macintosh; Intel Mac OS X 10.14; rv: 75.0) Gecko / 20100101 Firefox / 75.0",
    "Mozilla / 5.0 (Windows NT 6.1; Win64; x64; rv: 74.0) Gecko / 20100101 Firefox / 74.0",
    "Mozilla / 5.0 (Macintosh; Intel Mac OS X 10_15_3) AppleWebKit / 537.36 (KHTML, как Gecko) Chrome / 80.0.3987.163 Safari / 537.36",
    "Dalvik/2.1.0 (Linux; U; Android 10; Mi 9T MIUI/V12.0.5.0.QFJMIXM)"
]
