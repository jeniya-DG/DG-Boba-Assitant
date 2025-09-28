# app/agent_functions.py

from typing import Any, Dict
from . import business_logic as bl
from .orders_store import add_order
from .events import publish
from .send_sms import send_received_sms

# --- Session state to capture phone & order across the call ---
session_state: Dict[str, Any] = {
    "phone_number": None,
    "order_number": None,
    "phone_confirmed": False,
    "received_sms_sent": False,
}

# --- Tool definitions ---
FUNCTION_DEFS: list[Dict[str, Any]] = [
    {
        "name": "menu_summary",
        "description": "Give a short human-style menu overview (flavors, toppings, add-ons).",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "add_to_cart",
        "description": "Add a drink to the cart.",
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
        "name": "save_phone_number",
        "description": "Save the customer's phone number for pickup.",
        "parameters": {
            "type": "object",
            "properties": {"phone": {"type": "string"}},
            "required": ["phone"],
        },
    },
    {
        "name": "confirm_phone",
        "description": "Set whether the spoken-back phone number was confirmed by the caller.",
        "parameters": {
            "type": "object",
            "properties": {"confirmed": {"type": "boolean"}},
            "required": ["confirmed"],
        },
    },
    {
        "name": "checkout_order",
        "description": "Place the order and return order number + total. Only allowed after phone_confirmed = true.",
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
]

# --- Wrappers to update session_state, persist, publish, and SMS ---
def _wrap_checkout_order(name: str | None = None, phone: str | None = None):
    # Gate: require explicit confirmation first
    if not session_state.get("phone_confirmed"):
        return {"ok": False, "error": "Phone number not confirmed"}
    result = bl.checkout_order(name=name, phone=phone or session_state.get("phone_number"))
    if isinstance(result, dict) and result.get("ok"):
        # Persist to orders.json
        add_order({
            "order_number": result["order_number"],
            "phone": result.get("phone"),
            "items": result.get("items") or [],
            "total": result.get("total", 0.0),
            "status": result.get("status", "received"),
            "created_at": result.get("created_at"),
        })
        # Notify dashboards (website updates)
        publish({"type": "order_created", "order_number": result["order_number"], "status": "received"})
        # Capture session
        if result.get("phone"):
            session_state["phone_number"] = result["phone"]
        if result.get("order_number"):
            session_state["order_number"] = result["order_number"]
        # Send the "received" SMS exactly once
        try:
            if (
                session_state.get("phone_number")
                and session_state.get("order_number")
                and not session_state.get("received_sms_sent")
            ):
                send_received_sms(
                    order_no=session_state["order_number"],
                    to_phone_no=session_state["phone_number"],
                )
                session_state["received_sms_sent"] = True
        except Exception as e:
            print(f"❌ Error sending 'received' SMS: {e}")
    return result

def _save_phone_number(phone: str):
    normalized = bl.normalize_phone(phone)
    session_state["phone_number"] = normalized
    session_state["phone_confirmed"] = False  # reset until explicitly confirmed
    return {"ok": True, "phone": normalized}

def _confirm_phone(confirmed: bool):
    session_state["phone_confirmed"] = bool(confirmed)
    if not confirmed:
        # If caller said "no", clear the saved phone so the agent will ask again
        session_state["phone_number"] = None
        session_state["order_number"] = None
        session_state["received_sms_sent"] = False
    return {"ok": True, "phone_confirmed": session_state["phone_confirmed"]}

# --- Map tool names to functions ---
FUNCTION_MAP: dict[str, Any] = {
    "menu_summary": bl.menu_summary,
    "add_to_cart": bl.add_to_cart,
    "remove_from_cart": bl.remove_from_cart,
    "set_sweetness_ice": bl.set_sweetness_ice,
    "save_phone_number": _save_phone_number,
    "confirm_phone": _confirm_phone,
    "checkout_order": _wrap_checkout_order,  # gated by confirmation; persists + publishes + SMS
    "order_status": bl.order_status,
    "extract_phone_and_order": bl.extract_phone_and_order,
}
