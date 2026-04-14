import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from fastapi import FastAPI, HTTPException, Request
import httpx
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import re
from playwright.async_api import async_playwright

from scraper import scrape_kijiji

print("=== MAIN.PY LOADED ===")

app = FastAPI(title="Kijiji Car Searcher API")

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Car(BaseModel):
    id: int
    make: str
    model: str  
    year: str
    price: str
    mileage: str

class CarSearchRequest(BaseModel):
    city: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    number_of_cars: Optional[int] = None
    minPrice: Optional[int] = None
    maxPrice: Optional[int] = None
    minMilage: Optional[int] = None
    maxMilage: Optional[int] = None
    minPrice: Optional[int] = None
    maxPrice: Optional[int] = None
    minMilage: Optional[int] = None
    maxMilage: Optional[int] = None

class CityRequest(BaseModel):
    city: str

def priceToInt(priceStr: str) -> int:
    priceStr = priceStr.replace("$", "").replace(",", "").strip()
    try:
        return int(priceStr)
    except ValueError:
        return 0
    
def mileageToInt(mileageStr: str) -> int:
    mileageStr = mileageStr.replace("km", "").replace(",","").strip()
    try:
        return int(mileageStr)
    except ValueError:
        return 0

lastQuery: None

@app.post("/search-cars")
async def search_cars(req: CarSearchRequest):
    city = None

    async with httpx.AsyncClient() as client:
        if req.city:
            response = await client.get(
                "https://nominatim.openstreetmap.org/search",
                params={"q": req.city, "format": "json", "limit": 1},
                headers={"User-Agent": "CarApp"}
            )
     


## Location finder functions

class LocationRequest(BaseModel):
    latitude: float
    longitude: float
    number_of_cars: Optional[int] = None
    min_price: Optional[int] = None
    max_price: Optional[int] = None
    min_milage: Optional[int] = None
    max_milage: Optional[int] = None

class LocationResponse(BaseModel):
    location: str
    city: Optional[str] = None
    province: Optional[str] = None

@app.post("/cars-by-city")
async def get_cars_by_city(city_request: CityRequest):
    city = city_request.city.strip()

    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": city, "format": "json", "addressdetails": 1, "limit": 1},
            headers={"User-Agent": "KijijiCarSearcher/1.0"}
        )
        results = response.json()

    if not results:
        raise HTTPException(status_code=404, detail=f"City '{city}' not found")

    address = results[0].get("address", {})
    resolved_city = address.get("city") or address.get("town") or address.get("village") or city
    region = address.get("state") or address.get("province")

    return {
        "location": f"{resolved_city}, {region}" if region else resolved_city,
        "city": resolved_city,
        "region": region
    }

@app.post("/cars-near-me")
async def get_cars_near_me(location_request: LocationRequest):
    print(f">>> number_of_cars: {location_request.number_of_cars}, min_price: {location_request.min_price}, max_price: {location_request.max_price}, min_milage: {location_request.min_milage}, max_milage: {location_request.max_milage}")
    lat = location_request.latitude
    lon = location_request.longitude
    num = location_request.number_of_cars or 15
    min_price = location_request.min_price
    max_price = location_request.max_price
    min_milage = location_request.min_milage
    max_milage = location_request.max_milage


    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://nominatim.openstreetmap.org/reverse",
            params={"lat": lat, "lon": lon, "format": "json"},
            headers={"User-Agent": "KijijiCarSearcher/1.0"}
        )
        address = response.json().get("address", {})

    city   = address.get("city") or address.get("town")
    region = address.get("state") or address.get("province")
    if min_price or min_milage or max_price or max_milage:
        buffer = num * 5
    else:
        buffer = num
    cars = await scrape_kijiji(target=buffer, city=city)

    # apply filters
    if min_price is not None:
        cars = [c for c in cars if priceToInt(c.get("price", "0")) >= min_price]
    if max_price is not None:
        cars = [c for c in cars if priceToInt(c.get("price", "0")) <= max_price]
    if min_milage is not None:
        cars = [c for c in cars if mileageToInt(c.get("mileage", "0")) >= min_milage]
    if max_milage is not None:
        cars = [c for c in cars if mileageToInt(c.get("mileage", "0")) <= max_milage]

    return {
        "location": f"{city}, {region}" if city else "Unknown",
        "city":     city,
        "region":   region,
        "cars":     cars[:num] if num is not None else cars,
    }
