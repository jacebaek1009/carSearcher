from fastapi import FastAPI, HTTPException, Request
import httpx
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import re


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

cars_data = [
    {
        "id": 1,
        "make": "Toyota",
        "model": "Camry",
        "year": "2018",
        "price": "$20,000",
        "mileage": "30,000 km"
    },
    {
        "id": 2,
        "make": "Honda",
        "model": "Civic",
        "year": "2017",
        "price": "$18,500",
        "mileage": "40,000 km"
    },
    {
        "id": 3,
        "make": "Ford",
        "model": "Focus",
        "year": "2016",
        "price": "$15,000",
        "mileage": "50,000 km"
    },
    {
        "id": 4,
        "make": "Chevrolet",
        "model": "Malibu",
        "year": "2019",
        "price": "$22,000",
        "mileage": "25,000 km"
    },
    {
        "id": 5,
        "make": "Nissan",
        "model": "Altima",
        "year": "2015",
        "price": "$14,000",
        "mileage": "60,000 km"
    },
    {
        "id": 6,
        "make": "Hyundai",
        "model": "Elantra",
        "year": "2018",
        "price": "$19,000",
        "mileage": "35,000 km"
    },
    {
        "id": 7,
        "make": "Volkswagen",
        "model": "Jetta",
        "year": "2017",
        "price": "$17,500",
        "mileage": "45,000 km"
    },
    {
        "id": 8,
        "make": "Subaru",
        "model": "Impreza",
        "year": "2016",
        "price": "$16,000",
        "mileage": "55,000 km"
    }
]

class UserInput(BaseModel):
    number_of_cars: Optional[int] = None
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

@app.post("/car")
def loadCars(userInput: UserInput):
    n = userInput.number_of_cars
    setMin = userInput.minPrice
    setMax = userInput.maxPrice
    minMilage = userInput.minMilage
    maxMilage = userInput.maxMilage

    filteredCar = cars_data

    if setMin is not None and setMax is not None:
        filteredCar = [
            car for car in cars_data
            if setMin <= priceToInt(car["price"]) <= setMax
        ]
    elif setMin is not None:
        filteredCar = [
            car for car in cars_data
            if priceToInt(car["price"]) >= setMin
        ]
    elif setMax is not None:
        filteredCar = [
            car for car in cars_data
            if priceToInt(car["price"]) <= setMax
        ]
    if minMilage is not None and maxMilage is not None:
        filteredCar = [
            car for car in filteredCar
            if mileageToInt(car["mileage"]) <= maxMilage
        ]
    elif minMilage is not None:
        filteredCar = [
            car for car in filteredCar
            if mileageToInt(car["mileage"]) >= minMilage
        ]
    elif maxMilage is not None:
        filteredCar = [
            car for car in filteredCar
            if mileageToInt(car["mileage"]) <= maxMilage
        ]

    if n is not None:
        filteredCar = filteredCar[:n]

    return filteredCar


## Location finder functions

class LocationRequest(BaseModel):
    latitude: float
    longitude: float

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
    lat = location_request.latitude
    lon = location_request.longitude

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://nominatim.openstreetmap.org/reverse",
            params={"lat": lat, "lon": lon, "format": "json"},
            headers={"User-Agent": "KijijiCarSearcher/1.0"}
        )
        geo_data = response.json()
        address = geo_data.get("address", {})
        
        city = address.get("city") or address.get("town")
        region = address.get("state") or address.get("province")
    
    # Return cars (you can add distance filtering here later)
    return {
        "location": f"{city}, {region}" if city else "Unknown",
        "city": city,
        "region": region
    }

