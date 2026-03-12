from playwright.sync_api import sync_playwright
import json

url = "https://www.autotrader.ca/cars/ab/edmonton/?rcp=0&rcs=0&prx=100&prv=Alberta&loc=Edmonton&hprc=True&wcp=True&sts=New-Used&inMarket=basicSearch"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        viewport={"width": 1280, "height": 800}
    )
    page = context.new_page()
    page.goto(url, timeout=50000)

    # JUST wait for the listing links, no networkidle
    page.wait_for_selector("a.inner-link[href^='/a/']", timeout=50000)

    cards = page.query_selector_all("a.inner-link[href^='/a/']")

    results = []
    for card in cards:
        attr_data = card.evaluate(
            """el => {
                const c = el.closest('[data-make]');
                if (!c) return {};
                return {
                    make: c.getAttribute('data-make'),
                    model: c.getAttribute('data-model'),
                    mileage: c.getAttribute('data-mileage'),
                    fuel_type: c.getAttribute('data-fuel-type'),
                    first_registration: c.getAttribute('data-first-registration'),
                    seller_type: c.getAttribute('data-seller-type'),
                    ownership_models: c.getAttribute('data-ownership-models'),
                    zip_code: c.getAttribute('data-listing-zip-code'),
                    country: c.getAttribute('data-listing-country'),
                };
            }"""
        )

        title_el = card.query_selector(".title-with-trim")
        price_el = card.query_selector("[data-qaid='result-list-price'], .result-price, [data-testid='price']")

        data = {
            **attr_data,
            "title": title_el.inner_text().strip() if title_el else None,
            "price": price_el.inner_text().strip() if price_el else None,
            "href": card.get_attribute("href"),
        }
        results.append(data)

    browser.close()

# dedupe by href
seen = set()
unique = []
for r in results:
    if r["href"] in seen:
        continue
    seen.add(r["href"])
    unique.append(r)

print(len(unique))
print(json.dumps(unique, indent=2, ensure_ascii=False))