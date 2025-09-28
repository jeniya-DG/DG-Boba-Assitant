# app/orders_store.py

import os, json, threading
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ORDERS_PATH = os.path.join(BASE_DIR, "orders.json")
_lock = threading.Lock()

def init_store():
    """Create a fresh orders.json with empty list every time server starts."""
    with _lock:
        data = {"orders": []}
        with open(ORDERS_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    return ORDERS_PATH

def clear_store():
    """Wipe all orders (used on graceful shutdown)."""
    with _lock:
        with open(ORDERS_PATH, "w", encoding="utf-8") as f:
            json.dump({"orders": []}, f, ensure_ascii=False, indent=2)
    print("🧹 Cleared orders.json on shutdown")

def _read():
    with _lock:
        if not os.path.exists(ORDERS_PATH):
            init_store()
        with open(ORDERS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)

def _write(data):
    with _lock:
        with open(ORDERS_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

def add_order(order: dict):
    """Append a new order. Must include: order_number, phone, items, total, status, created_at."""
    data = _read()
    data["orders"].append(order)
    _write(data)

def list_recent_orders(limit: int = 50):
    data = _read()
    items = list(reversed(data["orders"]))  # newest first
    return items[:limit]

def list_in_progress_orders(limit: int = 100):
    data = _read()
    items = [o for o in reversed(data["orders"]) if o.get("status") != "ready"]
    return [{"order_number": o["order_number"], "status": o.get("status", "received")} for o in items[:limit]]

def get_order_phone(order_number: str) -> str | None:
    data = _read()
    for o in data["orders"]:
        if o.get("order_number") == order_number:
            return o.get("phone")
    return None

def set_order_status(order_number: str, status: str) -> bool:
    data = _read()
    for o in data["orders"]:
        if o.get("order_number") == order_number:
            o["status"] = status
            _write(data)
            return True
    return False

def get_order(order_number: str) -> dict | None:
    """Return full order dict by order_number."""
    data = _read()
    for o in data["orders"]:
        if o.get("order_number") == order_number:
            return o
    return None

def latest_order_for_phone(phone_e164: str) -> dict | None:
    """Return the most recent order for a phone (by created_at)."""
    data = _read()
    matches = [o for o in data["orders"] if o.get("phone") == phone_e164]
    if not matches:
        return None
    return sorted(matches, key=lambda o: o.get("created_at") or 0, reverse=True)[0]

def now_iso():
    return datetime.utcnow().isoformat()
