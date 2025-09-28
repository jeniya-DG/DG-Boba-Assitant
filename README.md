# 🧋 Deepgram BobaRista – Voice Ordering System

An AI-powered **voice ordering assistant** for boba shops, built with **FastAPI**, **Twilio**, and **Deepgram**.
Customers call a phone number, place their order naturally, and receive SMS updates when their drinks are ready.

---

## ⚡ Quick Start (Local with Podman + ngrok)

```bash
# 1. Copy env file and fill in secrets
cp sample.env.txt .env

# 2. Start the app locally (build + run container)
./podman-start.sh

# 3. Expose to Twilio with ngrok
ngrok http 8000
```

👉 Copy the ngrok HTTPS URL into `.env` as `VOICE_HOST`, then set your Twilio **Voice Webhook** to:

```
https://<VOICE_HOST>/voice
```

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
├── app_factory.py       # Application factory with startup/shutdown hooks
├── settings.py          # Centralized configuration, prompts, Deepgram agent setup
├── http_routes.py       # HTTP routes: TwiML, orders dashboard, barista console, SSE events
├── ws_bridge.py         # WebSocket bridge: Twilio <-> Deepgram audio + events
├── agent_client.py      # Deepgram Agent client + settings injection
├── agent_functions.py   # Function (tool) definitions with wrappers for state + persistence
├── business_logic.py    # Core menu, cart handling, checkout, and order management
├── orders_store.py      # Thread-safe JSON-backed order store
├── events.py            # Lightweight pub/sub for live dashboards
├── audio.py             # Audio resampling utilities (Twilio ↔ Deepgram formats)
├── send_sms.py          # Twilio SMS: order received & order ready notifications
└── orders.json          # Persistent order log (auto-reset at startup)

Containerfile            # Podman/Docker build recipe  
.dockerignore            # Excludes secrets and build artifacts  
.env                     # Local runtime config (not committed; see sample.env.txt)  
requirements.txt         # Python dependencies  
README.md                # Documentation and usage guide  
podman-start.sh          # Start/rebuild/run container for local dev  
podman-stop.sh           # Stop/remove container (and optionally stop VM)  
```

---

## ⚙️ Local Development (Podman + ngrok)

### 1. Prerequisites

* [Podman](https://podman.io/) installed (`brew install podman` on macOS)
* [ngrok](https://ngrok.com/) installed
* Copy sample env → `.env` and fill in your values:

  ```bash
  cp sample.env.txt .env
  ```

---

### 2. Run with helper scripts

**Start / rebuild / run:**

```bash
./podman-start.sh
```

This will:

* Ensure the Podman VM is running
* Remove any old `boba-voice` container
* Build the image
* Run the container on `http://localhost:8000`

**Logs (follow):**

```bash
podman logs -f boba-voice
```

**Expose to Twilio via ngrok:**

```bash
ngrok http 8000
```

Copy the HTTPS URL into your `.env` as `VOICE_HOST`, then set your Twilio Voice webhook to:

```
https://<VOICE_HOST>/voice
```

**Stop / clean up:**

```bash
./podman-stop.sh
```

(Stops and removes the container, and optionally stops the Podman VM.)

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
DEEPGRAM_API_KEY=**********

# --- Twilio Voice (calls) ---
TWILIO_ACCOUNT_SID=**********
TWILIO_AUTH_TOKEN=**********
TWILIO_FROM_E164=+15551234567
TWILIO_TO_E164=+15557654321

# --- Agent config ---
AGENT_LANGUAGE=en
AGENT_TTS_MODEL=aura-2-odysseus-en
AGENT_STT_MODEL=nova-3

# --- Twilio SMS (messaging) ---
MSG_TWILIO_ACCOUNT_SID=**********
MSG_TWILIO_AUTH_TOKEN=**********
MSG_TWILIO_FROM_E164=+15559876543

# --- Hostname for Twilio <Stream> ---
VOICE_HOST=multifibered-glossarially-martine.ngrok-free.dev
WS_SCHEME=wss
```

---

## 🔧 Useful Commands

```bash
# Logs (follow)
podman logs -f boba-voice

# Stop
podman stop boba-voice

# Restart
podman start boba-voice

# List containers
podman ps -a
```

---

## 📺 Dashboards

* Orders TV → `http://<host>:8000/orders`
* Barista Console → `http://<host>:8000/barista`
* Orders JSON → `http://<host>:8000/orders.json`

