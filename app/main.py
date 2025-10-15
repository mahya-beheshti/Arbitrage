from app.exchanges import get_nobitex_price
from fastapi import FastAPI

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/get_nobitex_prices")
async def get_nobitex_prices():
    res = get_nobitex_price()
    return res