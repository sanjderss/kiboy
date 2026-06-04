import requests
try:
    r = requests.get("https://www.1secmail.com/api/v1/?action=genRandomMailbox&count=1")
    print(r.status_code)
    print(r.text)
except Exception as e:
    print(e)
