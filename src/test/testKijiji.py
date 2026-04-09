import asyncio
from playwright.async_api import async_playwright

KIJIJI_URL = "https://www.kijiji.ca/b-cars-trucks/{city_slug}/page-{page}/c174{location_id}"
 
CITY_LOCATION_IDS = {
    "edmonton":  "l1700203",
    "calgary":   "l1700199",
    "vancouver": "l1700287",
    "toronto":   "l1700273",
    "ottawa":    "l1700185",
}
 
 
async def scrape_kijiji(target: int, city: str, **_) -> list:
    city_slug   = city.lower().replace(" ", "-")
    location_id = CITY_LOCATION_IDS.get(city.lower(), "l1700203")
    results     = []
    page_num    = 1
 
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 800},
        )
        page = await context.new_page()
 
        while len(results) < target:
            url = KIJIJI_URL.format(
                city_slug=city_slug,
                page=page_num,
                location_id=location_id,
            )
 
            await page.goto(url, timeout=60_000)
 
            # wait until cards are actually in the DOM
            try:
                await page.wait_for_selector("[data-testid='listing-card']", timeout=15_000)
            except Exception:
                # page didn't load any cards — stop paginating
                break
 
            cards = await page.query_selector_all("[data-testid='listing-card']")
            if not cards:
                break
 
            for card in cards:
                if len(results) >= target:
                    break
 
                title_el = await card.query_selector("[data-testid='listing-title']")
                price_el = await card.query_selector("[data-testid='autos-listing-price']")
                link_el  = await card.query_selector("[data-testid='listing-link']")
 
                # pills row: mileage • transmission • fuel  (all same tag)
                # primary selector uses data-testid; fallback filters <p> tags for "km"
                pill_els = await card.query_selector_all("p.eEvVV")
                if not pill_els:
                    # fallback: any <p> whose text contains "km"
                    all_p = await card.query_selector_all("p")
                    pill_els = [
                        p for p in all_p
                        if "km" in (await p.inner_text()).lower()
                    ]
 
                title = (await title_el.inner_text()).strip() if title_el else None
                price = (await price_el.inner_text()).strip() if price_el else None
                href  = await link_el.get_attribute("href")   if link_el  else None
 
                pills        = [(await p.inner_text()).strip() for p in pill_els]
                mileage      = pills[0] if len(pills) > 0 else None
                transmission = pills[1] if len(pills) > 1 else None
                fuel_type    = pills[2] if len(pills) > 2 else None
 
                # parse year / make / model from title e.g. "2019 Toyota Camry LE"
                make = model = year = None
                if title:
                    parts = title.split()
                    if parts and parts[0].isdigit():
                        year  = parts[0]
                        make  = parts[1] if len(parts) > 1 else None
                        model = parts[2] if len(parts) > 2 else None
 
                results.append({
                    "title":              title,
                    "price":              price,
                    "mileage":            mileage,
                    "transmission":       transmission,
                    "fuel_type":          fuel_type,
                    "make":               make,
                    "model":              model,
                    "first_registration": year,
                    "seller_type":        None,
                    "href":               href,
                    "source":             "Kijiji",
                })
 
            page_num += 1
 
        await browser.close()
 
    return _dedupe(results)
 
 
# ── Shared ─────────────────────────────────────────────────────────────────────
 
def _dedupe(results: list) -> list:
    seen, unique = set(), []
    for r in results:
        key = r.get("href")
        if key in seen:
            continue
        seen.add(key)
        unique.append(r)
    return unique
 
 
# ── Test ───────────────────────────────────────────────────────────────────────
 
if __name__ == "__main__":
    async def main():
        print("Scraping 5 cars from Edmonton Kijiji...")
        results = await scrape_kijiji(target=15, city="Edmonton")
        print(f"\nGot {len(results)} results:\n")
        for car in results:
            print(f"  Title:        {car['title']}")
            print(f"  Price:        {car['price']}")
            print(f"  Mileage:      {car['mileage']}")
            print(f"  Transmission: {car['transmission']}")
            print(f"  Fuel:         {car['fuel_type']}")
            print(f"  Year:         {car['first_registration']}")
            print(f"  Make:         {car['make']}")
            print(f"  Model:        {car['model']}")
            print(f"  Link:         {car['href']}")
            print()
 
    asyncio.run(main())