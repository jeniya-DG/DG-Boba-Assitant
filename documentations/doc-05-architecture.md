# System Architecture

Deep dive into how Deepgram BobaRista works under the hood.

---

## High-Level Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                      Customer's Phone                            │
└────────────────────────┬─────────────────────────────────────────┘
                         │
                         │ Dials +1-xxx-xxx-xxxx
                         ↓
┌──────────────────────────────────────────────────────────────────┐
│                         Twilio Cloud                             │
│  • Receives incoming call                                        │
│  • Fetches TwiML instructions from our webhook                   │
│  • Establishes WebSocket for audio streaming                     │
└────────────────────────┬─────────────────────────────────────────┘
                         │
                         │ WebSocket: wss://voice.boba-demo.deepgram.com/twilio
                         ↓
┌──────────────────────────────────────────────────────────────────┐
│                     Our FastAPI Server                           │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │              WebSocket Bridge (ws_bridge.py)               │ │
│  │  • Accepts Twilio WebSocket connection                     │ │
│  │  • Resamples audio formats                                 │ │
│  │  • Routes audio to/from Deepgram                           │ │
│  │  • Handles function calls                                  │ │
│  └─────────────────────┬──────────────────────────────────────┘ │
│                        │                                          │
│  ┌─────────────────────┴──────────────────────────────────────┐ │
│  │              Agent Functions (agent_functions.py)          │ │
│  │  • add_to_cart, checkout_order, save_phone, etc.           │ │
│  └─────────────────────┬──────────────────────────────────────┘ │
│                        │                                          │
│  ┌─────────────────────┴──────────────────────────────────────┐ │
│  │          Business Logic (business_logic.py)                │ │
│  │  • Menu validation                                         │ │
│  │  • Cart management                                         │ │
│  │  • Order creation                                          │ │
│  └─────────────────────┬──────────────────────────────────────┘ │
│                        │                                          │
│  ┌─────────────────────┴──────────────────────────────────────┐ │
│  │            Orders Store (orders_store.py)                  │ │
│  │  • Thread-safe JSON file operations                        │ │
│  │  • Persists all orders                                     │ │
│  └─────────────────────┬──────────────────────────────────────┘ │
│                        │                                          │
│  ┌─────────────────────┴──────────────────────────────────────┐ │
│  │              Event System (events.py)                      │ │
│  │  • Pub/sub for dashboard updates                           │ │
│  │  • Server-Sent Events (SSE)                                │ │
│  └────────────────────────────────────────────────────────────┘ │
└────────────────────────┬─────────────────────────────────────────┘
                         │
                         │ WebSocket: wss://agent.deepgram.com
                         ↓
┌──────────────────────────────────────────────────────────────────┐
│                    Deepgram Agent API                            │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Listen (STT)    │ Think (LLM)     │ Speak (TTS)            │ │
│  │ nova-3          │ gemini-2.5-flash│ aura-2-odysseus-en     │ │
│  └────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
```

---

## Call Flow Sequence

### Step 1: Incoming Call

```
Customer → Dials +1-xxx-xxx-xxxx
         ↓
Twilio   → Receives call
         → POST /voice webhook
         ↓
Server   → Returns TwiML:
           <Response>
             <Say>Connecting you to the Deepgram Boba Rista.</Say>
             <Connect>
               <Stream url="wss://voice.boba-demo.deepgram.com/twilio" />
             </Connect>
           </Response>
```

### Step 2: WebSocket Establishment

```
Twilio → Opens WebSocket to /twilio
       ↓
Server → Accepts WebSocket
       → Connects to Deepgram Agent API
       → Sends agent settings (models, prompt, functions)
       ↓
Deepgram → Sends greeting: "Hey! I am your Deepgram BobaRista..."
```

### Step 3: Audio Streaming Loop

```
Customer speaks
    ↓
Twilio → Sends audio (µ-law 8kHz, base64-encoded)
    ↓
Server → Decodes + Resamples to Linear16 48kHz
    ↓
Deepgram → STT (nova-3) → Text
         → LLM (gemini-2.5-flash) → Response
         → TTS (aura-2-odysseus-en) → Audio (Linear16 24kHz)
    ↓
Server → Resamples to µ-law 8kHz
    ↓
Twilio → Plays audio to customer
```

### Step 4: Function Calls

```
Customer: "I want a taro milk tea with boba"
    ↓
Deepgram → Detects intent
         → Generates function call:
           {
             "type": "FunctionCallRequest",
             "functions": [{
               "name": "add_to_cart",
               "arguments": {
                 "flavor": "taro milk tea",
                 "toppings": ["boba"]
               }
             }]
           }
    ↓
Server → Executes function
       → Returns result:
         {
           "type": "FunctionCallResponse",
           "content": {
             "ok": true,
             "staged": true,
             "pending_item": {...}
           }
         }
    ↓
Deepgram → Continues conversation based on result
```

### Step 5: Order Completion

```
Agent: "Can I get your phone number?"
Customer: "555-123-4567"
    ↓
Server → save_phone_number("+15551234567")
       → checkout_order(phone="+15551234567")
       → Returns { "ok": true, "order_number": "4782", ... }
       → Persists to orders.json
       → Publishes "order_created" event
       → Sends SMS via Twilio
    ↓
Deepgram → "Your order number is 4, 7, 8, 2"
```

### Step 6: Dashboard Updates

```
Event System → Publishes "order_created"
             ↓
SSE Clients ← Receive event
             ↓
/orders     → Updates TV display
/barista    → Refreshes order list
```

---

## Component Deep Dive

### 1. WebSocket Bridge (`ws_bridge.py`)

**Responsibilities:**
- Accept Twilio WebSocket connections
- Manage Deepgram Agent WebSocket
- Bidirectional audio streaming
- Audio format conversion
- Function call routing
- Session state management

**Key Functions:**

```python
async def twilio_agent(ws: WebSocket):
    # Accept Twilio connection
    await ws.accept()
    
    # Connect to Deepgram
    agent = await connect_agent()
    await send_agent_settings(agent)
    
    # Audio resampling states
    twilio_to_agent_state = None
    agent_to_twilio_state = None
    
    # Bidirectional streaming
    # 1. agent_to_twilio_task() - forwards Deepgram → Twilio
    # 2. Main loop - forwards Twilio → Deepgram
    
    # Handle events: start, media, stop
    # Execute function calls
    # Manage cleanup
```

**Audio Flow:**

```
Twilio Input (µ-law 8kHz):
  base64 decode
    ↓
  audioop.ulaw2lin → Linear16 8kHz
    ↓
  audioop.ratecv → Linear16 48kHz
    ↓
  Send to Deepgram

Deepgram Output (Linear16 24kHz):
  audioop.ratecv → Linear16 8kHz
    ↓
  audioop.lin2ulaw → µ-law 8kHz
    ↓
  Split into 160-byte chunks (20ms frames)
    ↓
  base64 encode → Send to Twilio
```

### 2. Agent Functions (`agent_functions.py`)

**Purpose:** Define tools the AI can call during conversation.

**Function Categories:**

**A. Staging Flow** (prevents accidental cart adds)
```python
add_to_cart()             # Stage a drink (not in cart yet)
update_pending_item()     # Modify staged drink
confirm_pending_to_cart() # Actually add to cart
clear_pending_item()      # Discard staged drink
```

**B. Order Management**
```python
checkout_order()   # Finalize order, get 4-digit number
order_status()     # Check order by phone/number
order_is_placed()  # Check if call already has order
save_phone_number() # Save customer's phone
```

**C. Cart Operations**
```python
remove_from_cart()   # Remove drink by index
set_sweetness_ice()  # Adjust preferences
menu_summary()       # Get menu info
```

**Function Definition Example:**

```python
{
    "name": "add_to_cart",
    "description": "Stage a drink spec (flavor/toppings/addons). Does NOT add to cart until confirmed.",
    "parameters": {
        "type": "object",
        "properties": {
            "flavor": {
                "type": "string",
                "description": "taro milk tea | black milk tea"
            },
            "toppings": {
                "type": "array",
                "items": {"type": "string"}
            },
            # ...
        },
        "required": ["flavor"]
    }
}
```

**Session State:**

```python
session_state = {
    "phone_number": "+15551234567",  # Customer's phone
    "order_number": "4782",          # 4-digit order ID
    "phone_confirmed": True,         # Phone explicitly saved
    "received_sms_sent": True,       # SMS sent (prevent duplicates)
    "pending_item": {                # Staged drink
        "flavor": "taro milk tea",
        "toppings": ["boba"],
        "sweetness": "50%",
        "ice": "regular ice",
        "addons": []
    }
}
```

### 3. Business Logic (`business_logic.py`)

**Core Functionality:**

**Menu Definition:**
```python
MENU = {
    "flavors": ["taro milk tea", "black milk tea"],
    "toppings": ["boba", "egg pudding", "crystal agar boba", "vanilla cream"],
    "addons": ["matcha stencil on top"]
}

PRICES = {
    "drink": 5.50,
    "topping": 0.75,
    "addon": 0.50
}
```

**Business Rules:**
- Max 10 drinks per order
- Matcha stencil requires vanilla cream topping
- Phone number normalization (E.164 format)
- Alias matching (e.g., "cream" → "vanilla cream")

**Cart Management:**
```python
CART = []  # In-memory cart for current session

def add_to_cart(flavor, toppings, ...):
    # Validate flavor against menu
    # Normalize topping names (handle aliases)
    # Check business rules
    # Calculate price
    # Append to cart
    return {"ok": True, "cart_count": len(CART)}
```

**Order Creation:**
```python
def checkout_order(name, phone):
    # Generate 4-digit order number (random)
    # Calculate total price
    # Create order object
    # Store in ORDERS dict
    # Clear cart
    # Return order details
```

### 4. Orders Store (`orders_store.py`)

**Thread-Safe JSON Persistence:**

```python
import threading

_lock = threading.Lock()

def add_order(order: dict):
    with _lock:
        data = _read()
        data["orders"].append(order)
        _write(data)
```

**Key Functions:**
- `init_store()` - Create fresh orders.json on startup
- `clear_store()` - Wipe orders on shutdown
- `add_order()` - Append new order
- `list_recent_orders()` - Get recent orders (newest first)
- `list_in_progress_orders()` - Get active orders only
- `get_order()` - Get full order by order number
- `set_order_status()` - Update order status
- `latest_order_for_phone()` - Get customer's latest order

**Order Structure:**
```json
{
    "order_number": "4782",
    "phone": "+15551234567",
    "items": [
        {
            "flavor": "taro milk tea",
            "toppings": ["boba"],
            "sweetness": "50%",
            "ice": "regular ice",
            "addons": [],
            "price": 6.25
        }
    ],
    "total": 6.25,
    "status": "received",  // or "ready"
    "created_at": 1704067200
}
```

### 5. Event System (`events.py`)

**Simple Pub/Sub Implementation:**

```python
_subscribers: List[asyncio.Queue] = []

def publish(event: Any):
    # Send event to all subscribers
    for q in _subscribers:
        q.put_nowait(event)

async def subscribe() -> asyncio.Queue:
    # Create queue and add to subscribers
    q = asyncio.Queue(maxsize=100)
    _subscribers.append(q)
    return q
```

**Event Types:**
```python
{"type": "order_created", "order_number": "4782", "status": "received"}
{"type": "order_status_changed", "order_number": "4782", "status": "ready"}
```

**Usage in HTTP Routes:**

```python
@app.get("/orders/events")
async def orders_events():
    q = await subscribe()
    async def event_gen():
        while True:
            msg = await q.get()
            yield f"data: {json.dumps(msg)}\n\n"
    return StreamingResponse(event_gen(), media_type="text/event-stream")
```

### 6. Audio Processing (`audio.py`)

**Resampling Utilities:**

```python
def ulaw8k_to_lin16_48k(ulaw_bytes: bytes, state):
    # 1. µ-law → Linear16 (8kHz)
    lin8k = audioop.ulaw2lin(ulaw_bytes, SAMPLE_WIDTH)
    
    # 2. 8kHz → 48kHz
    lin48k, new_state = audioop.ratecv(
        lin8k, SAMPLE_WIDTH, CHANNELS, 8000, 48000, state
    )
    
    return lin48k, new_state

def lin16_24k_to_ulaw8k(lin24k_bytes: bytes, state):
    # 1. 24kHz → 8kHz
    lin8k, new_state = audioop.ratecv(
        lin24k_bytes, SAMPLE_WIDTH, CHANNELS, 24000, 8000, state
    )
    
    # 2. Linear16 → µ-law
    ulaw8k = audioop.lin2ulaw(lin8k, SAMPLE_WIDTH)
    
    return ulaw8k, new_state
```

**Why These Formats?**

- **Twilio**: µ-law 8kHz (telephony standard, compact)
- **Deepgram Input**: Linear16 48kHz (high quality for STT)
- **Deepgram Output**: Linear16 24kHz (high quality TTS)

**Frame Chunking:**

```python
TWILIO_FRAME_BYTES = 160  # 20ms at 8kHz µ-law

def chunk_bytes(b: bytes, size: int):
    for i in range(0, len(b), size):
        yield b[i:i+size]
```

### 7. SMS Notifications (`send_sms.py`)

**Two Message Types:**

**A. Order Received** (after checkout):
```python
def send_received_sms(order_no: str, to_phone_no: str):
    client.messages.create(
        from_=MSG_FROM_PHONE,
        to=to_phone_no,
        body=f"Thanks for your order! Your order number is {order_no}. "
             f"We'll text you when it's ready for pickup."
    )
```

**B. Order Ready** (barista marks done):
```python
def send_ready_sms(order_no: str, to_phone_no: str):
    client.messages.create(
        from_=MSG_FROM_PHONE,
        to=to_phone_no,
        body=f"Your boba order #{order_no} is now ready for pickup! 🧋"
    )
```

---

## Order Lifecycle

### Complete Flow

```
1. CALL INITIATED
   Customer → Dials +1-888-762-8114
   
2. GREETING
   Deepgram → "Hey! I am your Deepgram BobaRista..."
   
3. ITEM STAGING
   Customer → "I want a taro milk tea with boba"
   Agent → add_to_cart(flavor="taro milk tea", toppings=["boba"])
   Result → {"ok": true, "staged": true, "pending_item": {...}}
   
4. CONFIRMATION
   Agent → "One taro milk tea with boba. Is that correct?"
   Customer → "Yes"
   Agent → confirm_pending_to_cart()
   Result → {"ok": true, "cart_count": 1}
   
5. ADDITIONAL ITEMS
   Agent → "Would you like anything else?"
   Customer → "No, that's all"
   
6. PHONE NUMBER
   Agent → "Can I get your phone number?"
   Customer → "xxx-xxx-xxxx"
   Agent → save_phone_number("+1xxxxxxxxxx")
   session_state["phone_confirmed"] = True
   
7. CHECKOUT
   Agent → checkout_order(phone="+xxxxxxxxxx")
   Server → Generates order #4782
          → Persists to orders.json
          → Publishes "order_created" event
          → Sends SMS: "Your order #4782 is confirmed"
   session_state["order_number"] = "4782"
   session_state["received_sms_sent"] = True
   
8. CONFIRMATION
   Agent → "Your order number is 4, 7, 8, 2"
   
9. DASHBOARD UPDATES
   Event → SSE clients receive "order_created"
   /orders → Shows order #4782 in "preparing" state
   /barista → Shows order details
   
10. PREPARATION
    Barista → Views order in /barista console
            → Sees: Taro Milk Tea, Boba
            → Prepares drink
            
11. READY NOTIFICATION
    Barista → Clicks "Done" button
    Server → set_order_status("4782", "ready")
           → Publishes "order_status_changed" event
           → Sends SMS: "Your order #4782 is ready!"
           
12. PICKUP
    Customer → Receives SMS
             → Picks up drink
```

---

## Staged Confirmation Pattern

**Problem:** Agent might misunderstand and add unwanted items to cart.

**Solution:** Two-step confirmation process.

### Traditional Flow (Problem)

```
Customer: "I want a taro milk tea"
Agent: add_to_cart("taro milk tea")  ← Added immediately!
Agent: "What toppings would you like?"
Customer: "Actually, I changed my mind..."  ← Too late!
```

### Staged Flow (Solution)

```
Customer: "I want a taro milk tea"
Agent: add_to_cart("taro milk tea")  ← STAGED only
pending_item = {"flavor": "taro milk tea", ...}

Agent: "One taro milk tea. Is that correct?"
Customer: "Yes"
Agent: confirm_pending_to_cart()  ← NOW added to cart

# OR if customer changes mind:
Customer: "Actually, make it black milk tea"
Agent: update_pending_item(flavor="black milk tea")
pending_item = {"flavor": "black milk tea", ...}
Agent: "Changed to black milk tea. Is that correct?"
```

**Implementation:**

```python
# Stage drink (not in cart yet)
def _stage_item(flavor, toppings, ...):
    staged = {"flavor": flavor, "toppings": toppings, ...}
    session_state["pending_item"] = staged
    return {"ok": True, "staged": True}

# Modify staged drink
def _update_pending_item(flavor=None, toppings=None, ...):
    current = session_state.get("pending_item") or {}
    # Merge changes
    updated = {**current, "flavor": flavor or current.get("flavor"), ...}
    session_state["pending_item"] = updated
    return {"ok": True, "staged": True}

# Confirm and add to cart
def _confirm_pending_to_cart():
    staged = session_state.get("pending_item")
    if not staged:
        return {"ok": False, "error": "No pending drink"}
    
    # Now actually add to cart
    result = bl.add_to_cart(**staged)
    
    if result.get("ok"):
        session_state["pending_item"] = None  # Clear staged item
    
    return result
```

---

## Dashboards

### Orders TV (`/orders`)

**Purpose:** Large display for shop screens.

**Features:**
- Shows only in-progress orders (status ≠ "ready")
- Large order numbers (56px font)
- Auto-refreshes via SSE
- Minimal UI (just numbers and status)

**Implementation:**
```javascript
const es = new EventSource('/orders/events');
es.onmessage = (ev) => {
    const msg = JSON.parse(ev.data);
    if (msg.type === 'order_created' || msg.type === 'order_status_changed') {
        loadOrders();
    }
};
```

### Barista Console (`/barista`)

**Purpose:** Staff interface for order management.

**Features:**
- Full order details (flavor, toppings, add-ons)
- Customer phone number
- "Done" button → marks ready + sends SMS
- Real-time updates via SSE

**Order Details:**
- Fetches via `/api/orders/{order_no}`
- Shows flavor + toppings with formatting
- Phone displayed (for exceptions/questions)

**Mark Ready Flow:**
```javascript
button.addEventListener('click', async () => {
    const res = await fetch(`/api/orders/${order_no}/done`, {method: 'POST'});
    // Server: sets status="ready" + sends SMS
    // Dashboard refreshes via SSE
});
```

---

## Performance Considerations

### Concurrency

**Single Worker** (default):
- Handles ~10-20 concurrent calls
- Sufficient for small/medium shops

**Multiple Workers** (if needed):
```ini
ExecStart=.../uvicorn main:app --workers 2
```

### Memory Usage

**Per Call:**
- WebSocket connections: ~2-5MB
- Audio buffers: ~1-2MB
- Session state: <1MB

**Total:**
- Base app: ~50-100MB
- Per active call: ~5-10MB

### Audio Latency

**Sources of latency:**
1. Network (Twilio → Server): 20-50ms
2. Resampling: <5ms
3. Network (Server → Deepgram): 20-50ms
4. Deepgram processing: 100-300ms
5. Return path: 40-100ms

**Total:** ~200-500ms (acceptable for voice)

---

## Security

### Authentication

**Deepgram:**
- API key in Authorization header
- Sent via WebSocket subprotocol

**Twilio:**
- Can validate requests via X-Twilio-Signature
- Optional but recommended

### Data Protection

**Environment Variables:**
```bash
chmod 600 .env  # Restrict permissions
```

**Orders Data:**
- Phone numbers stored in E.164 format
- No PII beyond phone + name (if provided)
- orders.json cleared on server restart

### SSL/TLS

**Required for:**
- Twilio webhooks (HTTPS only)
- WebSocket connections (WSS)
- Dashboard access

---
