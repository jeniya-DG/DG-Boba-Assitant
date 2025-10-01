# 🧋 Deepgram BobaRista – Voice Ordering System

An AI-powered **voice ordering assistant** for boba shops, built with **FastAPI**, **Twilio**, and **Deepgram Agent API**.  
Customers call a phone number, place their order naturally through voice conversation, and receive SMS updates when their drinks are ready for pickup.

---

## ✨ Features

- ☎️ **Voice Ordering** via Twilio phone calls + Deepgram Realtime Agent
- 🧠 **Conversational AI** with natural language understanding
  - Menu navigation and recommendations
  - Cart management with staged confirmation flow
  - Order checkout and status tracking
- 📲 **SMS Notifications** 
  - Order confirmation immediately after checkout
  - Pickup notification when barista marks order ready
- 📺 **Orders TV Dashboard** (`/orders`) - Large display for in-progress orders
- 👨‍🍳 **Barista Console** (`/barista`) - Staff interface to view details and mark orders ready
- 🔄 **Real-time Updates** via Server-Sent Events (SSE)
- 📦 **Containerized** with Podman/Docker, published to [quay.io](https://quay.io/repository/jeniya26/deepgram_bobarista)

## 🚀 Quick Start

### Option 1: Local Development (Podman + ngrok)

```bash
# 1. Copy env file and fill in your API keys
cp sample.env.txt .env

# 2. Start the app locally (builds and runs container)
./podman-start.sh

# 3. Expose to internet with ngrok
ngrok http 8000
```

💡 Copy the ngrok HTTPS URL (e.g., `https://abc123.ngrok-free.app`) into `.env` as `VOICE_HOST`, then configure your Twilio Voice Webhook to:

https://<your-ngrok-url>/voice

### Option 2: Production Deployment (AWS EC2)

See the **[Complete Deployment Tutorial](documentations/04-deployment.md)** for step-by-step instructions on:
- Setting up AWS EC2 with Ubuntu
- Configuring Twilio phone numbers and webhooks
- Installing SSL certificates with Let's Encrypt
- Setting up Nginx reverse proxy
- Running as a systemd service

**Current Production Setup:**
- **Server**: AWS EC2 (Ubuntu 22.04)
- **Domain**: `voice.boba-demo.deepgram.com`
- **SSL**: Let's Encrypt certificate with auto-renewal
- **Reverse Proxy**: Nginx with WebSocket support

## 📂 Project Architecture

app/
├── main.py              # FastAPI entrypoint
├── app_factory.py       # Application factory with startup/shutdown hooks
├── settings.py          # Configuration, prompts, Deepgram agent settings
├── http_routes.py       # HTTP routes: TwiML, dashboards, barista console, SSE
├── ws_bridge.py         # WebSocket bridge: Twilio ↔ Deepgram audio streaming
├── agent_client.py      # Deepgram Agent API client connection
├── agent_functions.py   # AI tool definitions with state management
├── business_logic.py    # Core menu, cart, checkout, order management
├── orders_store.py      # Thread-safe JSON-backed order persistence
├── events.py            # Pub/sub system for real-time dashboard updates
├── audio.py             # Audio resampling (µ-law 8kHz ↔ Linear16 48kHz/24kHz)
├── send_sms.py          # Twilio SMS notifications
└── orders.json          # Order storage (auto-reset on startup)

documentations/          # Complete documentation
├── 01-getting-started.md
├── 02-ec2-setup.md
├── 03-twilio-setup.md
├── 04-deployment.md
├── 05-architecture.md
├── 06-api-reference.md
├── 07-troubleshooting.md
└── 08-development.md

Containerfile            # Podman/Docker build recipe  
podman-start.sh          # Local dev: build and run container  
podman-stop.sh           # Local dev: stop and cleanup  
requirements.txt         # Python dependencies  
sample.env.txt           # Environment variable template  

## 📚 Documentation

| Guide | Description |
|-------|-------------|
| [Getting Started](documentations/01-getting-started.md) | Local development setup with Podman + ngrok |
| [EC2 Setup](documentations/02-ec2-setup.md) | AWS EC2 instance configuration |
| [Twilio Setup](documentations/03-twilio-setup.md) | Complete Twilio phone & webhook configuration |
| [Deployment](documentations/04-deployment.md) | Production deployment guide |
| [Architecture](documentations/05-architecture.md) | System design & component deep dive |
| [API Reference](documentations/06-api-reference.md) | All endpoints & examples |
| [Troubleshooting](documentations/07-troubleshooting.md) | Common issues & solutions |
| [Development](documentations/08-development.md) | Contributing & development workflow |

## 🎯 How It Works

Customer Dials 
        ↓
Twilio receives call → POST /voice webhook
WebSocket connection established
┌─────────────────────────────────────┐
│  Twilio (µ-law 8kHz)                │
│         ↕                           │
│  Your Server (resampling)           │
│  Deepgram Agent (Linear16 48kHz)    │
│    • STT: nova-3                    │
│    • Think: gemini-2.5-flash        │
│    • TTS: aura-2-odysseus-en        │
└─────────────────────────────────────┘
AI calls functions: add_to_cart, checkout_order, etc.
Order saved → SMS sent → Dashboard updated
Barista marks ready → SMS sent

See [Architecture Documentation](documentations/05-architecture.md) for detailed flow diagrams.

## 📝 Environment Variables

Create a `.env` file:

# Server
VOICE_HOST=voice.boba-demo.deepgram.com

# Deepgram
DEEPGRAM_API_KEY=your_key_here

# Agent Models
AGENT_TTS_MODEL=aura-2-odysseus-en
AGENT_STT_MODEL=nova-3
AGENT_THINK_MODEL=gemini-2.5-flash

# Twilio Messaging (SMS)
xxx=ACxxxxxx
xxx=your_token
xxx=+xxxxx

# Twilio Calling (SMS)
TWILIO_ACCOUNT_SID=*****
TWILIO_AUTH_TOKEN=*****

# Your Twilio phone number (the number customers will call)
TWILIO_FROM_E164=*****

# Test destination number (for making test calls)
TWILIO_TO_E164=*****

See `sample.env.txt` for complete template.

## 🧪 Quick Test

# 1. Call the number
Call: +1 (xxx) xxx-xxxx

# 2. Order something
Say: "I want a taro milk tea with boba"

# 3. Check dashboards
Visit: https://voice.boba-demo.deepgram.com/orders
Visit: https://voice.boba-demo.deepgram.com/barista

## 🛠️ Local Development

# Start container

# View logs
podman logs -f boba-voice

# Stop
./podman-stop.sh

See [Getting Started Guide](documentations/01-getting-started.md) for detailed instructions.

## 🚀 Production Deployment

# Quick deploy on EC2
git clone <repo> /opt/bobarista
cd /opt/bobarista
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
# Edit .env with your credentials
sudo systemctl enable bobarista
sudo systemctl start bobarista

See [Deployment Guide](documentations/04-deployment.md) for complete setup including Nginx, SSL, and systemd.

## 📊 API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /` | Landing page |
| `GET /orders` | TV display (large numbers) |
| `GET /barista` | Staff console |
| `POST /voice` | Twilio webhook |
| `WS /twilio` | Audio streaming |
| `GET /orders.json` | Orders data |

See [API Reference](documentations/06-api-reference.md) for complete documentation.

## 🔧 Troubleshooting

**Call ends immediately?**
- Check Twilio webhook URL
- Verify server accessibility

**No SMS received?**
- Check Twilio credentials
- Verify phone number capabilities

See [Troubleshooting Guide](documentations/07-troubleshooting.md) for detailed solutions.

