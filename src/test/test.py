from playwright.sync_api import sync_playwright
import json
import time

TARGET = 50  # change this to however many cars you want
BASE_URL = "https://www.autotrader.ca/cars/ab/edmonton/?rcp=15&rcs={rcs}&srt=39&prx=100&prv=Alberta&loc=Edmonton&hprc=True&wcp=True&sts=New-Used&inMarket=basicSearch"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        viewport={"width": 1280, "height": 800}
    )
    page = context.new_page()

    results = []
    offset = 0

    while len(results) < TARGET:
        if offset == 0:
            url = "https://www.autotrader.ca/cars/ab/edmonton/?rcp=0&rcs=0&prx=100&prv=Alberta&loc=Edmonton&hprc=True&wcp=True&sts=New-Used&inMarket=basicSearch"
        else:
            url = BASE_URL.format(rcs=offset)

        page.goto(url, timeout=50000)
        page.wait_for_load_state("domcontentloaded")
        time.sleep(8)

        cards = page.query_selector_all("a.inner-link[href^='/a/']")
        print(f"Found {len(cards)} cards")
        input("pause")

        if not cards:
            break

        for card in cards:
            if len(results) >= TARGET:
                break

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

            price = card.evaluate("""el => {
                const container = el.closest('[id^="result-item"], [class*="result-item"]')
                            || el.parentElement.parentElement;
                const span = container ? container.querySelector('span.price-amount') : null;
                return span ? span.innerText.trim() : null;
            }""")

            title_el = card.query_selector(".title-with-trim")
            mileage_el = card.query_selector(".kms, .odometer-proximity, [class*='kms']")

            data = {
                **attr_data,
                "title": title_el.inner_text().strip() if title_el else None,
                "price": price,
                "mileage": mileage_el.inner_text().strip() if mileage_el else attr_data.get("mileage"),
                "href": card.get_attribute("href"),
            }
            results.append(data)

        offset += 15

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