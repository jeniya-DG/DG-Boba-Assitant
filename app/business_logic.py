# business_logic.py
import re, time, random

# --- Menu (no pricing, no sizes - one standard size only) ---
MENU = {
    "flavors": ["taro milk tea", "black milk tea"],
    "toppings": ["boba", "egg pudding", "crystal agar boba", "vanilla cream"],
    "addons": ["matcha stencil on top"],
}
MAX_DRINKS = 5
MAX_ORDERS_PER_PHONE = 5  # Maximum active drinks total per phone number

# In-memory stores
CART = []
ORDERS = {}
PENDING_ORDERS = {}  # Orders that have number but not yet finalized

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
    "vanilla cream": {"vanilla cream", "cream", "vanilla foam", "vanilla cold foam", "foam"},
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

def menu_summary():
    return {
        "summary": (
            "We have Taro Milk Tea and Black Milk Tea. "
            "Toppings: boba, egg pudding, crystal agar boba, vanilla cream. "
            "Optional add-on: matcha stencil on top (requires vanilla cream foam)."
        ),
        "flavors": MENU["flavors"],
        "toppings": MENU["toppings"],
        "addons": MENU["addons"],
    }

def add_to_cart(flavor: str, toppings=None, sweetness: str | None = None, ice: str | None = None, addons=None):
    """Add a drink to cart (no pricing, no size - standard size only)."""
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

    # Business rule: matcha stencil requires vanilla cream (foam)
    if "matcha stencil on top" in adds_out and "vanilla cream" not in tops_out:
        return {
            "ok": False,
            "error": "Matcha stencil is only available with foam. Please add Vanilla Cream topping.",
            "requires": {"topping": "vanilla cream"},
        }

    item = {
        "flavor": f,
        "toppings": tops_out,
        "sweetness": (sweetness or "50%"),
        "ice": (ice or "regular ice"),
        "addons": adds_out,
    }
    CART.append(item)
    return {
        "ok": True,
        "cart_count": len(CART),
        "item": item,
    }

def remove_from_cart(index: int):
    if not (0 <= index < len(CART)):
        return {"ok": False, "error": "Index out of range.", "cart_count": len(CART)}
    removed = CART.pop(index)
    return {"ok": True, "removed": removed, "cart_count": len(CART)}

def modify_cart_item(index: int, flavor: str | None = None, toppings=None, sweetness: str | None = None, ice: str | None = None, addons=None):
    """Modify an existing item in the cart by index."""
    if not (0 <= index < len(CART)):
        return {"ok": False, "error": "Index out of range.", "cart_count": len(CART)}
    
    item = CART[index]
    
    # Update flavor if provided
    if flavor:
        f = _normalize(flavor)
        if f not in MENU["flavors"]:
            return {"ok": False, "error": f"'{flavor}' is not on the menu."}
        item["flavor"] = f
    
    # Update toppings if provided
    if toppings is not None:
        tops_in = [_normalize(t) for t in _ensure_list(toppings)]
        tops_out = []
        for t in tops_in:
            if not t:
                continue
            m = _match_with_aliases(t, MENU["toppings"], TOPPING_ALIASES)
            if not m:
                return {"ok": False, "error": f"Topping '{t}' not available."}
            tops_out.append(m)
        item["toppings"] = tops_out
    
    # Update addons if provided
    if addons is not None:
        adds_in = [_normalize(a) for a in _ensure_list(addons)]
        adds_out = []
        for a in adds_in:
            if not a:
                continue
            m = _match_with_aliases(a, MENU["addons"], ADDON_ALIASES)
            if not m:
                return {"ok": False, "error": f"Add-on '{a}' not available."}
            adds_out.append(m)
        item["addons"] = adds_out
    
    # Business rule: matcha stencil requires vanilla cream (foam)
    if "matcha stencil on top" in item.get("addons", []) and "vanilla cream" not in item.get("toppings", []):
        return {
            "ok": False,
            "error": "Matcha stencil is only available with foam. Please add Vanilla Cream topping.",
            "requires": {"topping": "vanilla cream"},
        }
    
    # Update sweetness and ice if provided
    if sweetness:
        item["sweetness"] = sweetness
    if ice:
        item["ice"] = ice
    
    return {"ok": True, "item": item, "cart_count": len(CART)}

def set_sweetness_ice(index: int | None = None, sweetness: str | None = None, ice: str | None = None):
    if not CART:
        return {"ok": False, "error": "Cart is empty."}
    i = index if index is not None else len(CART) - 1
    if not (0 <= i < len(CART)):
        return {"ok": False, "error": "Index out of range."}
    if sweetness: CART[i]["sweetness"] = sweetness
    if ice: CART[i]["ice"] = ice
    return {"ok": True, "item": CART[i]}

def get_cart():
    """Return current cart contents (no pricing)."""
    return {
        "ok": True,
        "items": CART.copy(),
        "count": len(CART),
    }

# --- Phone / orders ---
PHONE_RE = re.compile(r'\+?\d[\d\-\s]{7,}\d')
def normalize_phone(p: str | None) -> str | None:
    if not p: return None
    digits = re.sub(r"\D", "", p)
    if len(digits) == 10:  # US
        return "+1" + digits
    if digits.startswith("1") and len(digits) == 11:
        return "+" + digits
    if p.startswith("+"):
        return p
    return "+" + digits if digits else None

def random_order_no() -> str:
    n = random.randint(0, 9999)
    return f"{n:04d}"

def checkout_order(phone: str | None = None):
    """
    Generate order number and create pending order (no pricing, no names, no sizes).
    Does NOT finalize - order stays in PENDING_ORDERS until finalize_order() is called.
    Checks 5-active-drink limit here (early validation).
    """
    if not CART:
        return {"ok": False, "error": "Cart is empty."}
    
    phone_norm = normalize_phone(phone) if phone else None
    
    # Check 5-drink limit per phone number (early validation)
    if phone_norm:
        from .orders_store import count_active_drinks_for_phone
        active_drinks = count_active_drinks_for_phone(phone_norm)
        current_cart_size = len(CART)
        total_drinks = active_drinks + current_cart_size
        
        if total_drinks > MAX_ORDERS_PER_PHONE:
            return {
                "ok": False, 
                "error": f"You currently have {active_drinks} active drink(s). Adding {current_cart_size} more would exceed the limit of {MAX_ORDERS_PER_PHONE} active drinks per phone number. Please wait for your current orders to be ready.",
                "limit_reached": True,
                "active_drinks": active_drinks,
                "cart_drinks": current_cart_size,
                "max_allowed": MAX_ORDERS_PER_PHONE
            }
    
    order_no = random_order_no()
    
    # Create pending order (not finalized yet, no pricing, no name, no size)
    order = {
        "order_number": order_no,
        "items": CART.copy(),
        "phone": phone_norm,
        "status": "received",
        "created_at": int(time.time()),
        "committed": False,
    }
    
    PENDING_ORDERS[order_no] = order
    # Note: Do NOT clear CART yet - customer can still modify
    
    return {"ok": True, **order}

def finalize_order(order_number: str):
    """
    Finalize a pending order - move from PENDING_ORDERS to ORDERS and clear CART.
    Returns the finalized order data ready for persistence.
    """
    if order_number not in PENDING_ORDERS:
        return {"ok": False, "error": "Pending order not found."}
    
    order = PENDING_ORDERS.pop(order_number)
    
    # Update with current cart contents (in case customer modified after checkout)
    if CART:
        order["items"] = CART.copy()
    
    order["committed"] = True
    ORDERS[order_number] = order
    CART.clear()
    
    return {"ok": True, **order}

def discard_pending_order(order_number: str):
    """Discard a pending order without finalizing."""
    if order_number in PENDING_ORDERS:
        PENDING_ORDERS.pop(order_number)
        CART.clear()
        return {"ok": True, "discarded": True}
    return {"ok": False, "error": "Pending order not found."}

def order_status(phone: str | None = None, order_number: str | None = None):
    if order_number and order_number in ORDERS:
        o = ORDERS[order_number]
        return {"found": True, "order_number": order_number, "status": o["status"]}
    phone_norm = normalize_phone(phone) if phone else None
    if phone_norm:
        matches = [(k, v) for k, v in ORDERS.items() if v.get("phone") == phone_norm]
        if matches:
            k, v = sorted(matches, key=lambda kv: kv[1]["created_at"], reverse=True)[0]
            return {"found": True, "order_number": k, "status": v["status"]}
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