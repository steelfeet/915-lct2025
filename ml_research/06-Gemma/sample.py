import requests, json

import secret


prompt = {
"modelUri": f"gpt://{secret.service_acc}/yandexgpt-lite",
"completionOptions": {
    "stream": False,
    "temperature": 0.6,
    "maxTokens": "2000"
},
"messages": [
    {
        "role": "system",
        "text": "Ты специалист по настройке сайтов"
    },
    {
        "role": "user",
        "text": "Как настроить редирект на сайте"
    },
    {
        "role": "assistant",
        "text": """
    использовать .htaccess
        """
    },
    {
        "role": "user",
        "text": """ 
Как отсутствующий  адрес https://domain.ru/dZkduvbBat.html перенаправить на https://domain.ru/show.php?q=dZkduvbBat.html понятно:

RewriteCond %{REQUEST_FILENAME} !-f
RewriteRule ^(.*)$ /kladez/bioclip/show.php?q=$1  [L,R=301]

А вот как сделать так, чтобы предыдущий адрес остался в адресной строке?        
        
"""
    }]
}


url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Api-Key {secret.api_key}"
}



response = requests.post(url, headers=headers, json=prompt)
result_dict = json.loads(response.text)
try:
    referat = result_dict["result"]["alternatives"][0]["message"]["text"]
except:
    referat = "Error"    
    print(result_dict)

print(referat) 



