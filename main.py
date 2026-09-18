import random
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

app = FastAPI(title="Torch Drop")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Базовый баланс
USER_BALANCE = 500.0

# Магазин дешевых скинов для старта
SHOP_ITEMS = [
    {"id": "s1", "name": "P250 | Sand Dune", "price": 10.0, "img": "🔫"},
    {"id": "s2", "name": "Glock-18 | Oxide", "price": 15.0, "img": "🔫"},
    {"id": "s3", "name": "AK-47 | Uncharted", "price": 25.0, "img": "🔫"},
    {"id": "s4", "name": "M4A1-S | Briefing", "price": 40.0, "img": "🔫"},
    {"id": "s5", "name": "AWP | Atheris", "price": 60.0, "img": "🎯"},
]

# Инвентарь игрока
USER_INVENTORY = [
    {"id": "u1", "name": "P250 | Sand Dune", "price": 10.0, "img": "🔫"},
    {"id": "u2", "name": "AK-47 | Uncharted", "price": 25.0, "img": "🔫"},
]

# Доступные цели для апгрейда
TARGET_ITEMS = [
    {"id": "t1", "name": "AK-47 | Redline", "price": 100.0, "img": "🔥"},
    {"id": "t2", "name": "M4A4 | Neo-Noir", "price": 250.0, "img": "🦄"},
    {"id": "t3", "name": "AWP | Asiimov", "price": 500.0, "img": "⚡"},
    {"id": "t4", "name": "Knife | Doppler", "price": 1200.0, "img": "🔪"},
]

HOUSE_EDGE = 0.95

class UpgradeRequest(BaseModel):
    user_item_id: str
    target_item_id: str

class DepositRequest(BaseModel):
    amount: float

class BuyRequest(BaseModel):
    shop_item_id: str

@app.get("/", response_class=HTMLResponse)
async def read_index():
    try:
        with open("index.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "<h1>Файл index.html не найден</h1>"

@app.get("/api/init")
async def get_init():
    return {
        "balance": USER_BALANCE,
        "user_inventory": USER_INVENTORY,
        "target_items": TARGET_ITEMS,
        "shop_items": SHOP_ITEMS
    }

@app.post("/api/deposit")
async def deposit(req: DepositRequest):
    global USER_BALANCE
    if req.amount <= 0:
        raise HTTPException(status_code=400, detail="Некорректная сумма")
    USER_BALANCE += req.amount
    return {"success": True, "new_balance": USER_BALANCE}

@app.post("/api/buy")
async def buy(req: BuyRequest):
    global USER_BALANCE
    item = next((i for i in SHOP_ITEMS if i["id"] == req.shop_item_id), None)
    if not item:
        raise HTTPException(status_code=400, detail="Товар не найден")
    if USER_BALANCE < item["price"]:
        raise HTTPException(status_code=400, detail="Недостаточно баланса")

    USER_BALANCE -= item["price"]
    new_user_item = {"id": f"u_{random.randint(1000,9999)}", "name": item["name"], "price": item["price"], "img": item["img"]}
    USER_INVENTORY.append(new_user_item)

    return {"success": True, "new_balance": USER_BALANCE, "user_inventory": USER_INVENTORY}

@app.post("/api/upgrade")
async def upgrade(req: UpgradeRequest):
    global USER_BALANCE
    user_item = next((i for i in USER_INVENTORY if i["id"] == req.user_item_id), None)
    target_item = next((i for i in TARGET_ITEMS if i["id"] == req.target_item_id), None)

    if not user_item or not target_item:
        raise HTTPException(status_code=400, detail="Предмет не найден")

    win_chance = (user_item["price"] / target_item["price"]) * 100 * HOUSE_EDGE
    win_chance = round(min(win_chance, 80.0), 2)

    roll = random.uniform(0, 100)
    is_win = roll <= win_chance

    USER_INVENTORY.remove(user_item)

    if is_win:
        USER_INVENTORY.append({"id": f"u_{random.randint(1000,9999)}", "name": target_item["name"], "price": target_item["price"], "img": target_item["img"]})

    winning_angle_max = (win_chance / 100) * 360
    if is_win:
        stop_angle = random.uniform(2, max(2, winning_angle_max - 2))
    else:
        stop_angle = random.uniform(winning_angle_max + 2, 358)

    return {
        "success": True,
        "is_win": is_win,
        "win_chance": win_chance,
        "stop_angle": round(stop_angle, 2),
        "user_inventory": USER_INVENTORY
    }
