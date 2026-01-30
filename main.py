from fastapi import FastAPI, HTTPException, Request
from fastapi_geolocation import GeoIPMIddleware, Geolocation
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List, Optional
from playwright.sync_api import sync_playwright
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

def priceToInt(priceStr: str) -> int:
    priceStr = priceStr.replace("$", "").replace(",", "").strip()
    try:
        return int(priceStr)
    except ValueError:
        return 0

lastQuery: None

@app.post("/car")
def loadCars(userInput: UserInput):
    n = userInput.number_of_cars
    setMin = userInput.minPrice
    setMax = userInput.maxPrice

    filteredCar = []

    if setMin is not None and setMax is not None:
        filteredCar = [
            car for car in cars_data
            if setMin <= priceToInt(car["price"]) <= setMax
        ]

    if n is not None:
        filteredCar = filteredCar[:n]

    return filteredCar

    

@app.get("/")
def read():
    return{"Evertything working"}