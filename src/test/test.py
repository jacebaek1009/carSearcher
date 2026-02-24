from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

url = "https://www.autotrader.ca/cars/ab/edmonton/?rcp=0&rcs=0&prx=100&prv=Alberta&loc=Edmonton&hprc=True&wcp=True&sts=New-Used&inMarket=basicSearch"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto(url)
    page.wait_for_selector("div.result-item")  # waits until listings actually load
    html = page.content()
    browser.close()

soup = BeautifulSoup(html, "html.parser")
cards = soup.select("div.result-item")
print(len(cards))

for card in cards:
    title = card.select_one("span.title-with-trim")
    price = card.select_one("span.price-amount")
    mileage = card.select_one("span.odometer-proximity")

    print(title.text.strip() if title else "No title")
    print(price.text.strip() if price else "No price")
    print(mileage.text.strip() if mileage else "No mileage")
    print("---")