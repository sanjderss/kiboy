import pytest
from playwright.sync_api import Page, expect

def test_hippo_navigation(page: Page):
    # Ini adalah skrip dasar agar UI Mode punya sesuatu untuk ditampilkan
    page.goto("https://www.hippocloudphone.com/index.html#/pages/login/register")
    page.wait_for_timeout(5000)
    print("Navigated to Hippo")
