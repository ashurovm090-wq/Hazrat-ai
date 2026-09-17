import random
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ITEMS = {
    "1": {"id": "1", "name": "P250 | Sand Dune", "price": 10.0},
    "2": {"id": "2", "name": "AK-47 | Redline", "price": 100.0},
    "3": {"id": "3", "name": "AWM | Asiimov", "price": 500.0},
}

HOUSE_EDGE = 0.95

class UpgradeRequest(BaseModel):
    user_item_id: str
    target_item_id: str

# Главная страница загружает index.html
@app.get("/", response_class=HTMLResponse)
async def read_index():
    try:
        with open("index.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "<h1>Файл index.html не найден в репозитории</h1>"

@app.post("/api/upgrade")
async def upgrade(req: UpgradeRequest):
    user_item = ITEMS.get(req.user_item_id)
    target_item = ITEMS.get(req.target_item_id)

    if not user_item or not target_item:
        raise HTTPException(status_code=400, detail="Предмет не найден")

    if user_item["price"] >= target_item["price"]:
        raise HTTPException(status_code=400, detail="Целевой предмет должен быть дороже")

    win_chance = (user_item["price"] / target_item["price"]) * 100 * HOUSE_EDGE
    win_chance = round(min(win_chance, 80.0), 2)

    roll = random.uniform(0, 100)
    is_win = roll <= win_chance

    winning_angle_max = (win_chance / 100) * 360

    if is_win:
        stop_angle = random.uniform(2, max(2, winning_angle_max - 2))
    else:
        stop_angle = random.uniform(winning_angle_max + 2, 358)

    return {
        "success": True,
        "is_win": is_win,
        "win_chance": win_chance,
        "roll": round(roll, 2),
        "stop_angle": round(stop_angle, 2),
        "user_item": user_item,
        "target_item": target_item
    }
