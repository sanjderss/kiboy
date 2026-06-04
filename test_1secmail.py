import requests
import time

def get_1secmail():
    r = requests.get("https://www.1secmail.com/api/v1/?action=genRandomMailbox&count=1")
    return r.json()[0]

print("1secmail:", get_1secmail())
