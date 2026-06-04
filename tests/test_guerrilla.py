import requests
import json

def test_guerrillamail():
    r = requests.get("http://api.guerrillamail.com/ajax.php?f=get_email_address")
    print("guerrillamail:", r.status_code, r.text)

test_guerrillamail()
