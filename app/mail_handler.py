import requests
import time
import re
import json
import random

class GuerrillaMail:
    def __init__(self):
        self.session = requests.Session()
        # Create a new email
        resp = self.session.get("http://api.guerrillamail.com/ajax.php?f=get_email_address").json()
        self.address = resp['email_addr']
        self.sid_token = resp['sid_token']
        # Optionally set a random domain that is less blocked
        domains = ['sharklasers.com', 'spam4.me', 'pokemail.net']
        self.domain = random.choice(domains)
        self.session.get(f"http://api.guerrillamail.com/ajax.php?f=set_email_user&email_user={self.address.split('@')[0]}&domain={self.domain}&sid_token={self.sid_token}")
        self.address = f"{self.address.split('@')[0]}@{self.domain}"
        self.seq = 0

    def message_list(self):
        resp = self.session.get(f"http://api.guerrillamail.com/ajax.php?f=check_email&seq={self.seq}&sid_token={self.sid_token}").json()
        if 'list' in resp and len(resp['list']) > 0:
            return resp['list']
        return []

    def message(self, mail_id):
        resp = self.session.get(f"http://api.guerrillamail.com/ajax.php?f=fetch_email&email_id={mail_id}&sid_token={self.sid_token}").json()
        return resp.get('mail_body', '')

def get_free_email():
    """Membuat email temporer gratis menggunakan GuerrillaMail"""
    test = GuerrillaMail()
    print(f"Email Baru Dibuat: {test.address}")
    return test

def wait_for_otp(email_obj, timeout=120):
    """Menunggu pesan masuk (OTP) dari GuerrillaMail."""
    start_time = time.time()
    print("Menunggu kode OTP masuk...")
    while time.time() - start_time < timeout:
        msgs = email_obj.message_list()
        # Filter welcome emails from guerrilla
        msgs = [m for m in msgs if m.get('mail_from') != 'no-reply@guerrillamail.com']
        
        if msgs:
            msg_id = msgs[0]['mail_id']
            content = email_obj.message(msg_id)
            print(f"Pesan Masuk Terdeteksi.")
            
            # Cari angka 4-6 digit menggunakan Regex
            otp_match = re.search(r'\b\d{4,6}\b', content)
            if otp_match:
                code = otp_match.group()
                print(f"OTP Ditemukan: {code}")
                return code
        time.sleep(5)
    return None
