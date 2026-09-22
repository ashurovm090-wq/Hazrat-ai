import sqlite3
import random
from fastapi import FastAPI, HTTPException, Header, Cookie
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

app = FastAPI(title="Torch Drop")

DB_NAME = "database.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Таблица пользователей
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            balance REAL DEFAULT 500.0
        )
    """)
    
    # Таблица скинов в инвентаре пользователя
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_items (
            id TEXT PRIMARY KEY,
            username TEXT,
            name TEXT,
            price REAL,
            img TEXT,
            FOREIGN KEY (username) REFERENCES users (username)
        )
    """)
    
    conn.commit()
    conn.close()

init_db()

# Доступные для выбора и апгрейда предметы
SHOP_ITEMS = [
    {"id": "s1", "name": "P250 | Sand Dune", "price": 10.0, "img": "🔫"},
    {"id": "s2", "name": "Glock-18 | Oxide", "price": 15.0, "img": "🔫"},
    {"id": "s3", "name": "AK-47 | Uncharted", "price": 25.0, "img": "🔫"},
    {"id": "s4", "name": "M4A1-S | Briefing", "price": 40.0, "img": "🔫"},
    {"id": "s5", "name": "AWP | Atheris", "price": 60.0, "img": "🎯"},
]

TARGET_ITEMS = [
    {"id": "t1", "name": "AK-47 | Redline", "price": 100.0, "img": "🔥"},
    {"id": "t2", "name": "M4A4 | Neo-Noir", "price": 250.0, "img": "🦄"},
    {"id": "t3", "name": "AWP | Asiimov", "price": 500.0, "img": "⚡"},
    {"id": "t4", "name": "Knife | Doppler", "price": 1200.0, "img": "🔪"},
]

HOUSE_EDGE = 0.95  # 95% RTP (Комиссия сервиса 5%)

class AuthData(BaseModel):
    username: str

class UpgradeRequest(BaseModel):
    selected_item_id: str
    target_item_id: str

class SellRequest(BaseModel):
    item_id: str

def get_user_inventory(username: str):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, price, img FROM user_items WHERE username = ?", (username,))
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r[0], "name": r[1], "price": r[2], "img": r[3]} for r in rows]

@app.get("/", response_class=HTMLResponse)
async def read_index():
    try:
        with open("index.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "<h1>Файл index.html не найден</h1>"

@app.post("/api/login")
async def login(data: AuthData):
    username = data.username.strip()
    if not username or len(username) < 3:
        raise HTTPException(status_code=400, detail="Имя пользователя слишком короткое (мин. 3 символа)")

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()

    if not user:
        cursor.execute("INSERT INTO users (username, balance) VALUES (?, ?)", (username, 500.0))
        # Стартовые предметы при первой регистрации
        cursor.execute("INSERT INTO user_items VALUES (?, ?, ?, ?, ?)", (f"u_{random.randint(10000,99999)}", username, "P250 | Sand Dune", 10.0, "🔫"))
        cursor.execute("INSERT INTO user_items VALUES (?, ?, ?, ?, ?)", (f"u_{random.randint(10000,99999)}", username, "AK-47 | Uncharted", 25.0, "🔫"))
        conn.commit()

    conn.close()

    response = JSONResponse(content={"status": "ok", "username": username})
    response.set_cookie(key="torch_user", value=username, max_age=30*86400)
    return response

@app.get("/api/init")
async def get_init(torch_user: str = Cookie(default="")):
    if not torch_user:
        raise HTTPException(status_code=401, detail="Необходима авторизация")

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE username = ?", (torch_user,))
    res = cursor.fetchone()
    conn.close()

    if not res:
        raise HTTPException(status_code=401, detail="Пользователь не найден")

    return {
        "username": torch_user,
        "balance": res[0],
        "user_inventory": get_user_inventory(torch_user),
        "target_items": TARGET_ITEMS,
        "shop_items": SHOP_ITEMS
    }

@app.post("/api/upgrade")
async def process_upgrade(data: UpgradeRequest, torch_user: str = Cookie(default="")):
    if not torch_user:
        raise HTTPException(status_code=401, detail="Авторизуйтесь!")

    inventory = get_user_inventory(torch_user)
    my_item = next((i for i in inventory if i["id"] == data.selected_item_id), None)
    target_item = next((i for i in TARGET_ITEMS if i["id"] == data.target_item_id), None)

    if not my_item or not target_item:
        raise HTTPException(status_code=400, detail="Выбран неверный предмет")

    if target_item["price"] <= my_item["price"]:
        raise HTTPException(status_code=400, detail="Цена целевого предмета должна быть выше")

    # Расчет вероятности успеха
    win_chance = (my_item["price"] / target_item["price"]) * HOUSE_EDGE
    roll = random.random()
    is_win = roll < win_chance

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Списываем исходный предмет
    cursor.execute("DELETE FROM user_items WHERE id = ? AND username = ?", (my_item["id"], torch_user))

    new_item = None
    if is_win:
        new_item_id = f"u_{random.randint(10000,99999)}"
        cursor.execute("INSERT INTO user_items VALUES (?, ?, ?, ?, ?)", 
                       (new_item_id, torch_user, target_item["name"], target_item["price"], target_item["img"]))
        new_item = {"id": new_item_id, "name": target_item["name"], "price": target_item["price"], "img": target_item["img"]}

    conn.commit()
    conn.close()

    return {
        "win": is_win,
        "chance_percent": round(win_chance * 100, 2),
        "new_item": new_item,
        "updated_inventory": get_user_inventory(torch_user)
    }

@app.post("/api/sell")
async def sell_item(data: SellRequest, torch_user: str = Cookie(default="")):
    if not torch_user:
        raise HTTPException(status_code=401, detail="Авторизуйтесь!")

    inventory = get_user_inventory(torch_user)
    item = next((i for i in inventory if i["id"] == data.item_id), None)

    if not item:
        raise HTTPException(status_code=400, detail="Предмет не найден")

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM user_items WHERE id = ? AND username = ?", (data.item_id, torch_user))
    cursor.execute("UPDATE users SET balance = balance + ? WHERE username = ?", (item["price"], torch_user))
    cursor.execute("SELECT balance FROM users WHERE username = ?", (torch_user,))
    new_balance = cursor.fetchone()[0]
    conn.commit()
    conn.close()

    return {
        "status": "ok",
        "new_balance": new_balance,
        "updated_inventory": get_user_inventory(torch_user)
    }
