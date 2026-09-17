import random
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

# Разрешаем запросы с фронтенда
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Мок-база предметов (в реальности берется из SQLite)
ITEMS = {
    "1": {"id": "1", "name": "P250 | Sand Dune", "price": 10.0},
    "2": {"id": "2", "name": "AK-47 | Redline", "price": 100.0},
    "3": {"id": "3", "name": "AWM | Asiimov", "price": 500.0},
}

# Платформенный маржа/комиссия (House Edge) 5%
HOUSE_EDGE = 0.95 

class UpgradeRequest(BaseModel):
    user_item_id: str
    target_item_id: str

@app.post("/api/upgrade")
async def upgrade(req: UpgradeRequest):
    user_item = ITEMS.get(req.user_item_id)
    target_item = ITEMS.get(req.target_item_id)

    if not user_item or not target_item:
        raise HTTPException(status_code=400, detail="Предмет не найден")

    if user_item["price"] >= target_item["price"]:
        raise HTTPException(status_code=400, detail="Целевой предмет должен быть дороже")

    # Расчет шанса в процентах (с учетом комиссии сайта)
    # Например: (10 / 100) * 100 * 0.95 = 9.5%
    win_chance = (user_item["price"] / target_item["price"]) * 100 * HOUSE_EDGE
    win_chance = round(min(win_chance, 80.0), 2)  # Ограничиваем макс. шанс до 80%

    # Генерация случайного числа от 0.00 до 100.00
    roll = random.uniform(0, 100)
    is_win = roll <= win_chance

    # Расчет угла остановки стрелки (от 0 до 360 градусов)
    # Зона победы: от 0 до (win_chance / 100 * 360)
    winning_angle_max = (win_chance / 100) * 360

    if is_win:
        # Выпадаем в жёлтую зону
        stop_angle = random.uniform(2, max(2, winning_angle_max - 2))
    else:
        # Выпадаем в серую зону
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
