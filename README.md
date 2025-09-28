# 🧋 Deepgram BobaRista – Voice Ordering System

An AI-powered **voice ordering assistant** for boba shops, built with **FastAPI**, **Twilio**, and **Deepgram**.
Customers call a phone number, place their order naturally, and receive SMS updates when their drinks are ready.

---

## ✨ Features

* ☎️ **Voice Ordering** via Twilio Calls + Deepgram Realtime Agent
* 🧠 **Conversational AI** with menu, cart, checkout, and order status tools
* 📲 **SMS Notifications** for order confirmation & pickup readiness
* 📺 **Orders TV Dashboard** (`/orders`) shows in-progress drinks
* 🍵 **Barista Console** (`/barista`) lets staff mark drinks “ready” → auto SMS
* 📦 **Containerized with Podman**, published to [quay.io](https://quay.io/repository/jeniya26/deepgram_bobarista)

---

## 📂 Project Architecture

```
app/
├── main.py              # FastAPI entrypoint
├── app_factory.py       # App creation + lifespan
├── settings.py          # Config + prompt + Deepgram agent settings
├── http_routes.py       # HTTP routes (TwiML, orders, barista UI, SSE)
├── ws_bridge.py         # WebSocket bridge: Twilio <-> Deepgram
├── agent_client.py      # Agent connection + settings injection
├── agent_functions.py   # Tool definitions + wrappers
├── business_logic.py    # Menu, cart, checkout, order mgmt
├── orders_store.py      # JSON-backed store (thread-safe)
├── events.py            # Pub/sub for dashboards
├── audio.py             # Resampling utils for Twilio ↔ Deepgram
├── send_sms.py          # Twilio SMS for order received + ready
└── orders.json          # Persistent store (reset each startup)

Containerfile            # Podman/Dockerfile for builds
.dockerignore            # Excludes secrets/junk
.env                     # Local config (not checked in!)
requirements.txt         # Python dependencies
README.md                # Project docs
```

---

## ⚙️ Local Development (Podman + ngrok)

### 1. Prerequisites

* [Podman](https://podman.io/) installed (`brew install podman` on macOS)
* [ngrok](https://ngrok.com/) installed

### 2. Start Podman VM (macOS/Linux)

```bash
podman machine init --cpus 4 --memory 4096 --disk-size 20
podman machine start
```

### 3. Build & run container

```bash
# Build
podman build -t boba-voice:local -f Containerfile .

# Run with your .env
podman run --rm -p 8000:8000 --env-file .env --name boba-voice boba-voice:local
```

### 4. Start ngrok

```bash
ngrok http 8000
```

Copy the HTTPS domain (e.g.
`https://multifibered-example.ngrok-free.dev`) → put it in `.env` as `VOICE_HOST`.

### 5. Set Twilio webhook

In Twilio phone number settings:
**Voice → A CALL COMES IN → Webhook (POST)**

```
https://<VOICE_HOST>/voice
```

---

## 🚀 Deploy to Any Server

### 1. Push image to Quay

```bash
podman login quay.io
podman tag boba-voice:local quay.io/jeniya26/deepgram_bobarista:latest
podman push quay.io/jeniya26/deepgram_bobarista:latest
```

### 2. On the server

```bash
podman run -d --name boba-voice \
  --restart unless-stopped \
  -p 8000:8000 \
  --env-file .env \
  quay.io/jeniya26/deepgram_bobarista:latest
```

### 3. Expose HTTPS/WSS

* For production: put Nginx, Caddy, or Cloudflare Tunnel in front of the container
* Update `.env` → `VOICE_HOST=your.domain.com`

---

## 📝 Sample `.env`

```bash
# --- Deepgram ---
DEEPGRAM_API_KEY=your_deepgram_api_key

# --- Voice Agent Host (used for Twilio webhook & WSS) ---
VOICE_HOST=your-public-domain.ngrok-free.dev
WS_SCHEME=wss

# --- Twilio SMS credentials ---
MSG_TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxx
MSG_TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxx
MSG_TWILIO_FROM_E164=+10000000000

# Optional test recipient
TWILIO_TO_E164=+19999999999

# --- Agent config ---
AGENT_LANGUAGE=en
AGENT_TTS_MODEL=aura-2-odysseus-en
AGENT_STT_MODEL=nova-3
```

---

## 🔧 Useful Commands

### Logs

```bash
podman logs -f boba-voice
```

### Stop

```bash
podman stop boba-voice
```

### Restart

```bash
podman start boba-voice
```

### Containers list

```bash
podman ps -a
```

---

## 📺 Dashboards

* Orders TV: `http://<host>:8000/orders`
* Barista Console: `http://<host>:8000/barista`
* Orders JSON: `http://<host>:8000/orders.json`


