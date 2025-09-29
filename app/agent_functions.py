# agent_functions.py
from typing import Any, Dict, Optional
from . import business_logic as bl
from .orders_store import add_order
from .events import publish

# --- Session state for the call ---
session_state: Dict[str, Any] = {
    "phone_number": None,
    "order_number": None,   # set after checkout
    # staged-but-not-confirmed drink
    "pending_item": None,   # {"flavor":..., "toppings":[...], "sweetness":..., "ice":..., "addons":[...]}
}

# ---------- Helpers ----------
def _coerce_list(x):
    if x is None:
        return []
    if isinstance(x, (list, tuple)):
        return [i for i in x if i is not None]
    return [x]

def _merge_item(base: dict, update: dict) -> dict:
    out = dict(base or {})
    for k, v in (update or {}).items():
        if v is None:
            continue
        if k in ("toppings", "addons"):
            out[k] = _coerce_list(v)
        else:
            out[k] = v
    return out

def _pending_summary(it: Optional[dict]) -> str:
    if not it:
        return "no pending item"
    flavor = it.get("flavor") or "unknown flavor"
    tops = ", ".join(_coerce_list(it.get("toppings"))) or "no toppings"
    adds = ", ".join(_coerce_list(it.get("addons"))) or "no add-ons"
    sweet = it.get("sweetness") or "50%"
    ice = it.get("ice") or "regular ice"
    return f"{flavor} | {tops} | {adds} | {sweet}, {ice}"

# ---------- Tool wrappers ----------
def _stage_item(flavor: str, toppings=None, sweetness: str | None = None, ice: str | None = None, addons=None):
    """Stage a drink (NOT added to cart yet)."""
    staged = {
        "flavor": flavor,
        "toppings": _coerce_list(toppings),
        "sweetness": sweetness,
        "ice": ice,
        "addons": _coerce_list(addons),
    }
    session_state["pending_item"] = staged
    return {"ok": True, "staged": True, "pending_item": staged, "summary": _pending_summary(staged)}

def _update_pending_item(flavor: str | None = None, toppings=None, sweetness: str | None = None, ice: str | None = None, addons=None):
    """Modify the staged drink before confirmation."""
    current = session_state.get("pending_item") or {}
    patch = {}
    if flavor is not None: patch["flavor"] = flavor
    if sweetness is not None: patch["sweetness"] = sweetness
    if ice is not None: patch["ice"] = ice
    if toppings is not None: patch["toppings"] = _coerce_list(toppings)
    if addons is not None: patch["addons"] = _coerce_list(addons)
    updated = _merge_item(current, patch)
    session_state["pending_item"] = updated
    return {"ok": True, "staged": True, "pending_item": updated, "summary": _pending_summary(updated)}

def _clear_pending_item():
    session_state["pending_item"] = None
    return {"ok": True, "cleared": True}

def _confirm_pending_to_cart():
    """Confirm the staged drink -> actually adds to cart via business logic."""
    staged = session_state.get("pending_item")
    if not staged or not staged.get("flavor"):
        return {"ok": False, "error": "No pending drink to confirm."}
    res = bl.add_to_cart(
        flavor=staged.get("flavor"),
        toppings=staged.get("toppings"),
        sweetness=staged.get("sweetness"),
        ice=staged.get("ice"),
        addons=staged.get("addons"),
    )
    if isinstance(res, dict) and res.get("ok"):
        session_state["pending_item"] = None
    return res

def _wrap_checkout_order(name: str | None = None, phone: str | None = None):
    """Auto-commit any staged item, then checkout. Persist and publish events."""
    if session_state.get("pending_item"):
        _ = _confirm_pending_to_cart()

    result = bl.checkout_order(name=name, phone=phone)
    if isinstance(result, dict) and result.get("ok"):
        # Persist orders.json
        add_order({
            "order_number": result["order_number"],
            "phone": result.get("phone"),
            "items": result.get("items") or [],
            "total": result.get("total", 0.0),
            "status": result.get("status", "received"),
            "created_at": result.get("created_at"),
        })
        # Publish to dashboards
        publish({"type": "order_created", "order_number": result["order_number"], "status": "received"})
        # Cache session markers
        if result.get("phone"):
            session_state["phone_number"] = result["phone"]
        if result.get("order_number"):
            session_state["order_number"] = result["order_number"]
    return result

def _save_phone_number(phone: str):
    normalized = bl.normalize_phone(phone)
    session_state["phone_number"] = normalized
    return {"ok": True, "phone": normalized}

def _order_is_placed():
    """Let the agent know if an order has already been placed in this call session."""
    placed = bool(session_state.get("order_number"))
    return {"placed": placed, "order_number": session_state.get("order_number")}

# ---------- Tool definitions ----------
FUNCTION_DEFS: list[Dict[str, Any]] = [
    {
        "name": "menu_summary",
        "description": "Give a short human-style menu overview (flavors, toppings, add-ons).",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },

    # Staging flow (no cart writes until confirmed)
    {
        "name": "add_to_cart",
        "description": "Stage a drink spec (flavor/toppings/addons). Does NOT add to cart until confirmed.",
        "parameters": {
            "type": "object",
            "properties": {
                "flavor": {"type": "string", "description": "taro milk tea | black milk tea"},
                "toppings": {"type": "array", "items": {"type": "string"}},
                "sweetness": {"type": "string", "description": "0% | 25% | 50% | 75% | 100%"},
                "ice": {"type": "string", "description": "no ice | less ice | regular ice | extra ice"},
                "addons": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["flavor"],
        },
    },
    {
        "name": "update_pending_item",
        "description": "Modify the staged (pending) drink before confirmation.",
        "parameters": {
            "type": "object",
            "properties": {
                "flavor": {"type": "string"},
                "toppings": {"type": "array", "items": {"type": "string"}},
                "sweetness": {"type": "string"},
                "ice": {"type": "string"},
                "addons": {"type": "array", "items": {"type": "string"}},
            },
            "required": [],
        },
    },
    {
        "name": "confirm_pending_to_cart",
        "description": "Confirm the staged drink and actually add it to the cart.",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "clear_pending_item",
        "description": "Discard the staged drink (if caller cancels or restarts).",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },

    # Call/session helpers
    {
        "name": "order_is_placed",
        "description": "Return whether an order has already been placed in this call session.",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },

    # Existing helpers
    {
        "name": "remove_from_cart",
        "description": "Remove a drink by index (0-based).",
        "parameters": {
            "type": "object",
            "properties": {"index": {"type": "integer", "minimum": 0}},
            "required": ["index"],
        },
    },
    {
        "name": "set_sweetness_ice",
        "description": "Update sweetness and/or ice for last item or by index.",
        "parameters": {
            "type": "object",
            "properties": {
                "index": {"type": "integer", "minimum": 0},
                "sweetness": {"type": "string"},
                "ice": {"type": "string"},
            },
            "required": [],
        },
    },
    {
        "name": "checkout_order",
        "description": "Place the order and return order number + total. If a drink is staged, it will be added first.",
        "parameters": {
            "type": "object",
            "properties": {"name": {"type": "string"}, "phone": {"type": "string"}},
            "required": [],
        },
    },
    {
        "name": "order_status",
        "description": "Look up order status by phone or order number.",
        "parameters": {
            "type": "object",
            "properties": {"phone": {"type": "string"}, "order_number": {"type": "string"}},
            "required": [],
        },
    },
    {
        "name": "extract_phone_and_order",
        "description": "Extract phone and 4-digit order number from free text.",
        "parameters": {
            "type": "object",
            "properties": {"text": {"type": "string"}},
            "required": ["text"],
        },
    },
    {
        "name": "save_phone_number",
        "description": "Save the customer's phone number for pickup.",
        "parameters": {
            "type": "object",
            "properties": {"phone": {"type": "string"}},
            "required": ["phone"],
        },
    },
]

# --- Map tool names to functions ---
FUNCTION_MAP: dict[str, Any] = {
    "menu_summary": bl.menu_summary,

    # Staging flow
    "add_to_cart": _stage_item,
    "update_pending_item": _update_pending_item,
    "confirm_pending_to_cart": _confirm_pending_to_cart,
    "clear_pending_item": _clear_pending_item,

    # Session
    "order_is_placed": _order_is_placed,

    # Existing
    "remove_from_cart": bl.remove_from_cart,
    "set_sweetness_ice": bl.set_sweetness_ice,
    "checkout_order": _wrap_checkout_order,
    "order_status": bl.order_status,
    "extract_phone_and_order": bl.extract_phone_and_order,
    "save_phone_number": _save_phone_number,
}
