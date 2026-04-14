from playwright.sync_api import sync_playwright
import json
import re

TARGET = 5
BASE_URL = "https://www.autotrader.ca/cars/ab/edmonton/?rcp=15&rcs={rcs}&srt=39&prx=100&prv=Alberta&loc=Edmonton&hprc=True&wcp=True&sts=New-Used&inMarket=basicSearch"

with sync_playwright() as p:
    browser = p.firefox.launch(headless=True)
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        viewport={"width": 1280, "height": 800}
    )
    page = context.new_page()
    page.route("**/*", lambda route: route.abort()
        if route.request.resource_type in ["image", "media", "font"]
        else route.continue_())

    results = []
    offset  = 0

    while len(results) < TARGET:
        if offset == 0:
            url = "https://www.autotrader.ca/cars/ab/edmonton/?rcp=0&rcs=0&prx=100&prv=Alberta&loc=Edmonton&hprc=True&wcp=True&sts=New-Used&inMarket=basicSearch"
        else:
            url = BASE_URL.format(rcs=offset)

        page.goto(url, timeout=50000, wait_until="domcontentloaded")
        page.wait_for_selector("a.inner-link[href^='/a/']", timeout=15000)
        cards = page.query_selector_all("a.inner-link[href^='/a/']")
        print(f"Found {len(cards)} cards")

        if not cards:
            break

        for card in cards:
            if len(results) >= TARGET:
                break

            title_el        = card.query_selector(".title-with-trim")
            price_el        = card.query_selector("span.price-amount")
            mileage_el      = card.query_selector("[data-testid='VehicleDetails-mileage_odometer']")
            transmission_el = card.query_selector("[data-testid='VehicleDetails-gearbox']")
            fuel_el         = card.query_selector("[data-testid='VehicleDetails-gas_pump']")
            location_el     = card.query_selector("span.proximity-text.overflow-ellipsis")
            seller_el       = card.query_selector(".seller-name")

            title        = title_el.inner_text().strip()        if title_el        else None
            price        = price_el.inner_text().strip()        if price_el        else None
            mileage      = mileage_el.inner_text().strip()      if mileage_el      else None
            transmission = transmission_el.inner_text().strip() if transmission_el else None
            fuel_type    = fuel_el.inner_text().strip()         if fuel_el         else None
            location     = location_el.inner_text().strip()     if location_el     else None
            seller       = seller_el.inner_text().strip()       if seller_el       else None

            # parse year / make / model from title e.g. "2024 Ford F-150 Lariat"
            year = make = model = None
            if title:
                parts = title.split()
                if parts and parts[0].isdigit():
                    year  = parts[0]
                    make  = parts[1] if len(parts) > 1 else None
                    model = parts[2] if len(parts) > 2 else None

            data = {
                "title":        title,
                "price":        price,
                "mileage":      mileage,
                "transmission": transmission,
                "fuel_type":    fuel_type,
                "location":     location,
                "seller":       seller,
                "year":         year,
                "make":         make,
                "model":        model,
                "href":         f"https://www.autotrader.ca{card.get_attribute('href')}",
                "source":       "AutoTrader",
            }
            results.append(data)

        offset += 15

    browser.close()

# dedupe by href
seen   = set()
unique = []
for r in results:
    if r["href"] in seen:
        continue
    seen.add(r["href"])
    unique.append(r)

for i in unique:
    print(f"{i['title']} | {i['price']} | {i['mileage']} | {i['transmission']} | {i['fuel_type']} | {i['seller']}")

print(json.dumps(unique, indent=2, ensure_ascii=False))