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

HOST = "jrh-ishs.kro.kr"
USER = "root"
PASSWORD = "ishs12345!"
DB = "placedata"


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


def calculate_peopleChangeRate(current, previous) -> float:
    # cases when previous is 0 or current is 0
    if previous == 0 and current == 0:
        return 0.0
    elif previous == 0:
        return 100.0
    elif current == 0:
        return -100.0
    else:
        return (current - previous) / previous * 100.0

@app.post("/register")
async def register(place: PlaceRegisterDTO):
    conn = pymysql.connect(host=HOST, user=USER, password=PASSWORD, db=DB, charset="utf8")
    curs = conn.cursor()
    if auth(place.API_KEY):
        for p in place.place_data:
            curs.execute(
                f"INSERT INTO place VALUES ('{p.name}', {p.lat}, {p.lng}, {p.width}, {p.height})")
        conn.commit()
        conn.close()
        return {"message": "success"}
    else:
        return {"message": "not authorized"}


@app.patch("/register")
async def register(place: PlaceRegisterDTO):
    if auth(place.API_KEY):
        conn = pymysql.connect(host="app.ishs.co.kr", user="root", password="ishs12345!", db="placedata",
                               charset="utf8")
        curs = conn.cursor()
        for p in place.place_data:
            curs.execute(
                f"UPDATE place SET latitude={p.lat}, longitude={p.lng}, width={p.width}, height={p.height} WHERE place_name='{p.name}'")
        conn.commit()
        conn.close()
        return {"message": "success"}
    else:
        return {"message": "not authorized"}


@app.get("/places")
async def places():
    conn = pymysql.connect(host=HOST, user=USER, password=PASSWORD, db=DB, charset="utf8")
    curs = conn.cursor()
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
    conn.close()
    return result

@app.get("/people")
async def people():
    conn = pymysql.connect(host=HOST, user=USER, password=PASSWORD, db=DB, charset="utf8")
    curs = conn.cursor()
    curs.execute("SELECT * FROM people WHERE time IN (SELECT MAX(time) FROM people GROUP BY place_name)")
    result = {}
    rows = curs.fetchall()
    for row in rows:
        result[row[0]] = {
            "time": row[1],
            "ppl_min": row[2],
            "ppl_max": row[3]
        }
    conn.close()
    return result

@app.get("/peopleChangeRate/")
async def peopleChangeRate():
    conn = pymysql.connect(host=HOST, user=USER, password=PASSWORD, db=DB, charset="utf8")
    curs = conn.cursor()
    curs.execute("SELECT place_name from place")
    places = curs.fetchall()
    result = {}
    for place in places:
        curs.execute(f"SELECT ppl_min, ppl_max FROM people WHERE place_name='{place[0]}' ORDER BY time DESC LIMIT 2")
        rows = curs.fetchall()
        if len(rows) == 2:
            print(rows)
            result[place[0]] = {
                "ppl_min_rate": calculate_peopleChangeRate(rows[0][0], rows[1][0]),
                "ppl_max_rate": calculate_peopleChangeRate(rows[0][1], rows[1][1])
            }
        else:
            result[place[0]] = {
                "ppl_min_rate": 0.0,
                "ppl_max_rate": 0.0
            }
    conn.close()
    return result

@app.post("/update")
async def update(place: PlaceUpdateDTO):
    conn = pymysql.connect(host=HOST, user=USER, password=PASSWORD, db=DB, charset="utf8")
    curs = conn.cursor()
    t = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if auth(place.API_KEY):
        for p in place.place_data:
            curs.execute(
                f"INSERT INTO people VALUES ('{p.name}', '{t}', {p.ppl_min}, {p.ppl_max})")
        conn.commit()
        conn.close()
        return {"message": "success"}
    else:
        return {"message": "not authorized"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=5000)
