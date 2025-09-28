# app/http_routes.py

import json as _json
import asyncio
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import Response, JSONResponse, HTMLResponse, StreamingResponse

from .settings import VOICE_HOST, WS_SCHEME
from .orders_store import (
    list_recent_orders,
    list_in_progress_orders,
    get_order_phone,
    set_order_status,
    add_order,
)
from .events import subscribe, unsubscribe, publish
from .business_logic import add_to_cart, checkout_order
from .send_sms import send_ready_sms  

http_router = APIRouter()

@http_router.post("/voice")
def voice_twiml(request: Request):
    # Prefer VOICE_HOST from .env; otherwise use the host that Twilio hit for /voice.
    host = VOICE_HOST or request.headers.get("host")
    if not host:
        # Worst case fallback: try request.url.hostname (shouldn’t happen with Twilio)
        host = request.url.hostname or "localhost:8000"

    # Build WSS stream URL for Twilio -> your server
    stream_url = f"{WS_SCHEME}://{host}/twilio"

    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Say>Connecting you to the Deepgram BobaRista.</Say>
  <Connect>
    <Stream url="{stream_url}" />
  </Connect>
</Response>"""
    return Response(content=twiml, media_type="text/xml")

@http_router.get("/orders.json")
def orders_json(limit: int = 50):
    return JSONResponse(list_recent_orders(limit=limit))

@http_router.get("/orders/in_progress.json")
def orders_in_progress_json(limit: int = 100):
    return JSONResponse(list_in_progress_orders(limit=limit))

# --- TV screen (big numbers) ---
ORDERS_TV_HTML = """<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>Boba Orders - Now Serving</title>
  <style>
    :root { color-scheme: light dark; }
    body { margin: 0; font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial; background: #111; color:#fff; }
    header { padding: 16px 24px; background: #222; border-bottom: 1px solid #333; }
    h1 { margin: 0; font-size: 24px; }
    .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 16px; padding: 24px; }
    .card { background: #1b1b1b; border: 1px solid #333; border-radius: 16px; padding: 24px; text-align: center; box-shadow: 0 1px 8px rgba(0,0,0,0.25); }
    .ord { font-size: 56px; letter-spacing: 2px; font-weight: 800; }
    .muted { color:#aaa; font-size:12px; margin-top: 6px; }
    .empty { padding: 80px; text-align:center; color:#777; }
  </style>
</head>
<body>
  <header><h1>🧋 Now Preparing</h1></header>
  <main>
    <div id="grid" class="grid"></div>
    <div id="empty" class="empty" style="display:none;">No active orders yet.</div>
  </main>
  <script>
    const grid = document.getElementById('grid');
    const empty = document.getElementById('empty');

    function renderList(list){
      grid.innerHTML = '';
      if(!list || list.length === 0){ empty.style.display = 'block'; return; }
      empty.style.display = 'none';
      for(const o of list){
        const card = document.createElement('div');
        card.className = 'card';
        card.innerHTML = '<div class="ord">' + (o.order_number || '----') + '</div>' +
                         '<div class="muted">' + (o.status || '') + '</div>';
        grid.appendChild(card);
      }
    }

    async function loadInitial() {
      const res = await fetch('/orders/in_progress.json');
      renderList(await res.json());
    }

    function startSSE() {
      const es = new EventSource('/orders/events');
      es.onmessage = (ev) => {
        try {
          const msg = JSON.parse(ev.data);
          if (msg.type === 'order_created' || msg.type === 'order_status_changed') {
            loadInitial();
          }
        } catch(e) { console.warn('bad event', e); }
      };
    }

    loadInitial().then(startSSE);
    setInterval(loadInitial, 15000);
  </script>
</body>
</html>"""

@http_router.get("/orders")
def orders_tv():
    return HTMLResponse(ORDERS_TV_HTML)

# --- Barista console (mark done -> SMS ready) ---
BARISTA_HTML = """<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>Barista Console</title>
  <style>
    :root{ color-scheme: light dark; }
    body { font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial; margin:24px; }
    h1 { margin: 0 0 12px; }
    table { width: 100%; border-collapse: collapse; }
    th, td { border-bottom: 1px solid #ddd; padding: 10px; text-align: left; }
    tr:hover { background: rgba(0,0,0,0.04); }
    button { padding: 6px 12px; border-radius: 8px; border: 1px solid #999; cursor: pointer; }
    .muted { color:#777; font-size: 12px; }
  </style>
</head>
<body>
  <h1>🧋 Barista Console</h1>
  <p class="muted">Mark orders as done to text the customer that it’s ready for pickup.</p>

  <table id="tbl">
    <thead><tr><th>Order #</th><th>Phone</th><th>Status</th><th>Action</th></tr></thead>
    <tbody></tbody>
  </table>

  <script>
    const tbody = document.querySelector('#tbl tbody');

    async function load() {
      const res = await fetch('/orders/in_progress.json');
      const list = await res.json();
      tbody.innerHTML = '';
      for (const o of list) {
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td><strong>${o.order_number}</strong></td>
          <td data-phone>-</td>
          <td>${o.status || ''}</td>
          <td><button data-done="${o.order_number}">Done</button></td>
        `;
        tbody.appendChild(tr);

        fetch('/api/orders/phone/' + o.order_number).then(r => r.json()).then(d => {
          tr.querySelector('[data-phone]').textContent = d.phone || '—';
        });
      }
    }

    tbody.addEventListener('click', async (e) => {
      const btn = e.target.closest('button[data-done]');
      if (!btn) return;
      const order = btn.getAttribute('data-done');
      btn.disabled = true; btn.textContent = 'Sending...';
      try {
        const res = await fetch('/api/orders/' + order + '/done', { method: 'POST' });
        if (!res.ok) throw new Error('Failed');
        btn.textContent = 'Sent ✅';
        setTimeout(load, 600);
      } catch (e) {
        btn.textContent = 'Error';
      }
    });

    function startSSE() {
      const es = new EventSource('/orders/events');
      es.onmessage = (ev) => {
        try {
          const msg = JSON.parse(ev.data);
          if (msg.type === 'order_created' || msg.type === 'order_status_changed') {
            load();
          }
        } catch(e) { /* ignore */ }
      };
    }

    load(); startSSE();
    setInterval(load, 15000);
  </script>
</body>
</html>"""

@http_router.get("/barista")
def barista():
    return HTMLResponse(BARISTA_HTML)

@http_router.get("/orders/events")
async def orders_events():
    q = await subscribe()
    async def event_gen():
        try:
            while True:
                msg = await q.get()
                yield f"data: {_json.dumps(msg)}\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            unsubscribe(q)
    return StreamingResponse(event_gen(), media_type="text/event-stream")

@http_router.get("/api/orders/phone/{order_no}")
def api_get_phone(order_no: str):
    phone = get_order_phone(order_no)
    return {"order_number": order_no, "phone": phone}

@http_router.post("/api/orders/{order_no}/done")
def api_mark_done(order_no: str):
    ok = set_order_status(order_no, "ready")
    if not ok:
        raise HTTPException(404, "Order not found")
    publish({"type": "order_status_changed", "order_number": order_no, "status": "ready"})
    phone = get_order_phone(order_no)
    if phone:
        try:
            from .send_sms import send_ready_sms
            send_ready_sms(order_no, phone)
        except Exception as e:
            print(f"❌ SMS send failed for {order_no}: {e}")
    return {"ok": True}

# --- DEV seed (optional)
@http_router.post("/api/seed")
def api_seed(n: int = Query(2, ge=1, le=10)):
    created = []
    for _ in range(n):
        add_to_cart(flavor="taro milk tea", toppings=["boba"], addons=["matcha stencil on top"])
        res = checkout_order(name=None, phone="+16145550123")
        if res.get("ok"):
            add_order({
                "order_number": res["order_number"],
                "phone": res.get("phone"),
                "items": res.get("items") or [],
                "total": res.get("total", 0.0),
                "status": res.get("status", "received"),
                "created_at": res.get("created_at"),
            })
            publish({"type": "order_created", "order_number": res["order_number"], "status": "received"})
            created.append(res["order_number"])
    return {"ok": True, "orders": created}
