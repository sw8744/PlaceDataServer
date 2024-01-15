from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from key.key import *
from pydantic import BaseModel
import pymysql
from datetime import datetime

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

conn = pymysql.connect(host="app.ishs.co.kr", user="root", password="ishs12345!", db="placedata", charset="utf8")
curs = conn.cursor()


@app.get("/")
async def root():
    return {"message": "Hello World"}


class PlaceRegister(BaseModel):
    name: str
    lat: float
    lng: float
    width: int
    height: int


class PlaceRegisterDTO(BaseModel):
    API_KEY: str
    place_data: list[PlaceRegister]


class PlaceUpdate(BaseModel):
    name: str
    ppl_min: int
    ppl_max: int


class PlaceUpdateDTO(BaseModel):
    API_KEY: str
    place_data: list[PlaceUpdate]


@app.post("/register")
async def register(place: PlaceRegisterDTO):
    if auth(place.API_KEY):
        for p in place.place_data:
            curs.execute(
                f"INSERT INTO place VALUES ('{p.name}', {p.lat}, {p.lng}, {p.width}, {p.height})")
        conn.commit()
        return {"message": "success"}
    else:
        return {"message": "not authorized"}


@app.patch("/register")
async def register(place: PlaceRegisterDTO):
    if auth(place.API_KEY):
        for p in place.place_data:
            curs.execute(
                f"UPDATE place SET latitude={p.lat}, longitude={p.lng}, width={p.width}, height={p.height} WHERE place_name='{p.name}'")
        conn.commit()
        return {"message": "success"}
    else:
        return {"message": "not authorized"}


@app.get("/places")
async def places():
    curs.execute("SELECT * FROM place")
    result = {}
    rows = curs.fetchall()
    for row in rows:
        result[row[0]] = {
            "lat": row[1],
            "lng": row[2],
            "width": row[3],
            "height": row[4]
        }
    return result


@app.post("/update")
async def update(place: PlaceUpdateDTO):
    t = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if auth(place.API_KEY):
        for p in place.place_data:
            curs.execute(
                f"INSERT INTO people VALUES ('{p.name}', '{t}', {p.ppl_min}, {p.ppl_max})")
        conn.commit()
        return {"message": "success"}
    else:
        return {"message": "not authorized"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="localhost", port=8000)
