# app/business_logic.py
import re, time, random

# --- Menu & simple pricing ---
MENU = {
    "flavors": ["taro milk tea", "black milk tea"],
    "toppings": ["boba", "egg pudding", "crystal agar boba", "vanilla cream"],
    "addons": ["matcha stencil"],
}
PRICES = {
    "drink": 5.50,
    "topping": 0.75,
    "addon": 0.50,
}
MAX_DRINKS = 10

# In-memory stores
CART = []
ORDERS = {}

# ---- Helpers ----
def _normalize(s: str | None) -> str:
    return (s or "").strip().lower()

def _ensure_list(x):
    """Coerce None/str/singleton into a list of strings."""
    if x is None:
        return []
    if isinstance(x, (list, tuple)):
        return [str(i) for i in x if i is not None]
    return [str(x)]

# Alias maps to tolerate natural phrasing
ADDON_ALIASES = {
    "matcha stencil on top": {
        "matcha stencil", "matcha stencil on top", "matcha",
        "matcha art", "matcha design", "stencil", "matcha stencil top"
    }
}
TOPPING_ALIASES = {
    "boba": {"boba", "tapioca", "tapioca pearls"},
    "egg pudding": {"egg pudding", "pudding"},
    "crystal agar boba": {"crystal agar", "agar", "crystal agar boba"},
    "vanilla cream": {"vanilla cream", "cream", "vanilla foam", "vanilla cold foam"},
}

def _match_with_aliases(value_norm: str, canonical_list: list[str], aliases: dict[str, set[str]]):
    if value_norm in canonical_list:
        return value_norm
    for canonical, alias_set in aliases.items():
        if value_norm == canonical or value_norm in alias_set:
            return canonical
        for a in alias_set:
            if value_norm and (value_norm in a or a in value_norm):
                return canonical
    for c in canonical_list:
        if value_norm and (value_norm in c or c in value_norm):
            return c
    return None

def _price_item(item):
    toppings = item.get("toppings", []) or []
    addons = item.get("addons", []) or []
    total = PRICES["drink"] + len(toppings) * PRICES["topping"] + len(addons) * PRICES["addon"]
    return round(total, 2)

def menu_summary():
    return {
        "summary": (
            "We have Taro Milk Tea and Black Milk Tea. "
            "Toppings: boba, egg pudding, crystal agar boba, vanilla cream. "
            "Optional add-on: matcha stencil on top."
        ),
        "flavors": MENU["flavors"],
        "toppings": MENU["toppings"],
        "addons": MENU["addons"],
    }

def add_to_cart(flavor: str, toppings=None, sweetness: str | None = None, ice: str | None = None, addons=None):
    if len(CART) >= MAX_DRINKS:
        return {"ok": False, "error": f"Max {MAX_DRINKS} drinks per order."}

    f = _normalize(flavor)
    if f not in MENU["flavors"]:
        return {"ok": False, "error": f"'{flavor}' is not on the menu."}

    tops_in = [_normalize(t) for t in _ensure_list(toppings)]
    adds_in = [_normalize(a) for a in _ensure_list(addons)]

    tops_out = []
    for t in tops_in:
        if not t:
            continue
        m = _match_with_aliases(t, MENU["toppings"], TOPPING_ALIASES)
        if not m:
            return {"ok": False, "error": f"Topping '{t}' not available."}
        tops_out.append(m)

    adds_out = []
    for a in adds_in:
        if not a:
            continue
        m = _match_with_aliases(a, MENU["addons"], ADDON_ALIASES)
        if not m:
            return {"ok": False, "error": f"Add-on '{a}' not available."}
        adds_out.append(m)

    item = {
        "flavor": f,
        "toppings": tops_out,
        "sweetness": sweetness or "50%",
        "ice": ice or "regular ice",
        "addons": adds_out,
    }
    item["price"] = _price_item(item)
    CART.append(item)
    return {
        "ok": True,
        "cart_count": len(CART),
        "item": item,
        "cart_total": round(sum(_price_item(i) for i in CART), 2)
    }

def remove_from_cart(index: int):
    if not (0 <= index < len(CART)):
        return {"ok": False, "error": "Index out of range.", "cart_count": len(CART)}
    removed = CART.pop(index)
    return {"ok": True, "removed": removed, "cart_count": len(CART)}

def set_sweetness_ice(index: int | None = None, sweetness: str | None = None, ice: str | None = None):
    if not CART:
        return {"ok": False, "error": "Cart is empty."}
    i = index if index is not None else len(CART) - 1
    if not (0 <= i < len(CART)):
        return {"ok": False, "error": "Index out of range."}
    if sweetness: CART[i]["sweetness"] = sweetness
    if ice: CART[i]["ice"] = ice
    return {"ok": True, "item": CART[i]}

# --- Phone / orders ---
PHONE_RE = re.compile(r'\+?\d[\d\-\s]{7,}\d')

def normalize_phone(p: str | None) -> str | None:
    """Return E.164-like number if possible, otherwise None."""
    if not p:
        return None
    raw = p.strip()
    # Preserve plus if present; otherwise extract digits and add +1 for US 10-digit.
    if raw.startswith("+"):
        digits = re.sub(r"[^0-9+]", "", raw)
        return digits if len(digits) >= 8 else None
    digits = re.sub(r"\D", "", raw)
    if len(digits) == 10:         # US local
        return "+1" + digits
    if len(digits) == 11 and digits.startswith("1"):
        return "+" + digits
    return ("+" + digits) if digits else None

def random_order_no() -> str:
    n = random.randint(0, 9999)
    return f"{n:04d}"

def checkout_order(name: str | None = None, phone: str | None = None):
    if not CART:
        return {"ok": False, "error": "Cart is empty."}
    phone_norm = normalize_phone(phone) if phone else None
    order_no = random_order_no()
    total = round(sum(_price_item(i) for i in CART), 2)
    order = {
        "order_number": order_no,
        "items": CART.copy(),
        "name": name,
        "phone": phone_norm,
        "total": total,
        "status": "received",
        "created_at": int(time.time()),
    }
    ORDERS[order_no] = order
    CART.clear()
    return {"ok": True, **order}

def order_status(phone: str | None = None, order_number: str | None = None):
    if order_number and order_number in ORDERS:
        o = ORDERS[order_number]
        return {"found": True, "order_number": order_number, "status": o["status"], "total": o["total"]}
    phone_norm = normalize_phone(phone) if phone else None
    if phone_norm:
        matches = [(k, v) for k, v in ORDERS.items() if v.get("phone") == phone_norm]
        if matches:
            k, v = sorted(matches, key=lambda kv: kv[1]["created_at"], reverse=True)[0]
            return {"found": True, "order_number": k, "status": v["status"], "total": v["total"]}
    return {"found": False}

def extract_phone_and_order(text: str | None):
    phone = None
    order = None
    if text:
        m = PHONE_RE.search(text)
        if m:
            phone = normalize_phone(m.group(0))
        m2 = re.search(r'\b(\d{4})\b', text)
        if m2:
            order = m2.group(1)
    return {"phone": phone, "order_number": order}
