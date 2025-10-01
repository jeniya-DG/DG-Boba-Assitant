# 🧋 Deepgram BobaRista – Voice Ordering System

An AI-powered **voice ordering assistant** for boba shops, built with **FastAPI**, **Twilio**, and **Deepgram Agent API**.  
Customers call a phone number, place their order naturally through voice conversation, and receive SMS updates when their drinks are ready for pickup.

---



## ✨ Features

- ☎️ **Voice Ordering** - Natural conversation via Twilio + Deepgram Agent
- 🧠 **Conversational AI** - Menu navigation, cart management, checkout
- 📲 **SMS Notifications** - Order confirmation + pickup ready alerts
- 📺 **Live Dashboards** - Real-time order tracking for staff and displays
- 🔄 **Staged Confirmation** - Prevents accidental orders with two-step verification
- 📦 **Containerized** - Easy deployment with Podman/Docker

---

## 🚀 Quick Start

### Local Development (5 minutes)

```bash
# 1. Clone and configure
git clone <repository-url>
cd deepgram-bobarista
cp sample.env.txt .env
# Edit .env with your API keys

# 2. Start with Podman
./podman-start.sh

# 3. Expose with ngrok
ngrok http 8000
```

📖 **[Full Local Setup Guide →](documentations/LOCAL_DEVELOPMENT.md)**

### Production Deployment

```bash
# Deploy to AWS EC2 with systemd + Nginx + SSL
ssh ubuntu@your-server
git clone <repository-url> /opt/bobarista
cd /opt/bobarista
# ... follow deployment guide
```

📖 **[Complete Deployment Guide →](documentations/DEPLOYMENT.md)**

---

## 📚 Documentation

### Setup Guides
- **[Local Development](documentations/LOCAL_DEVELOPMENT.md)** - Podman + ngrok setup
- **[AWS EC2 Deployment](documentations/DEPLOYMENT.md)** - Production deployment with SSL
- **[Twilio Configuration](documentations/TWILIO_SETUP.md)** - Phone numbers & webhooks

### Technical Reference
- **[System Architecture](documentations/ARCHITECTURE.md)** - How it works under the hood
- **[API Reference](documentations/API_REFERENCE.md)** - Endpoints & usage
- **[Troubleshooting](documentations/TROUBLESHOOTING.md)** - Common issues & solutions

---

## 📂 Project Structure

```
app/
├── main.py              # FastAPI entrypoint
├── app_factory.py       # Application lifecycle management
├── settings.py          # Configuration & AI prompts
├── http_routes.py       # Web routes & dashboards
├── ws_bridge.py         # Twilio ↔ Deepgram audio bridge
├── agent_client.py      # Deepgram Agent API client
├── agent_functions.py   # AI tools (menu, cart, checkout)
├── business_logic.py    # Order management logic
├── orders_store.py      # JSON-based order storage
├── events.py            # Real-time event system (SSE)
├── audio.py             # Audio format conversion
└── send_sms.py          # Twilio SMS notifications

documentations/          # Detailed setup guides
Containerfile           # Podman/Docker image
requirements.txt        # Python dependencies
sample.env.txt          # Environment template
```

---

## 🎯 How It Works (Quick Overview)

```
Customer calls → Twilio receives → WebSocket to your server
    ↓
Audio streaming: Twilio ↔ Your Server ↔ Deepgram Agent
    ↓
AI processes speech and calls functions:
  • add_to_cart (stage drink)
  • confirm_pending_to_cart (add to cart)
  • checkout_order (finalize & get order number)
    ↓
Order saved → SMS sent → Dashboard updates
    ↓
Barista marks ready → Pickup SMS sent
```

📖 **[Detailed Architecture →](documentations/ARCHITECTURE.md)**

---

## ⚙️ Key Technologies

- **[Deepgram Agent API](https://developers.deepgram.com)** - Conversational AI (STT + LLM + TTS)
- **[Twilio](https://twilio.com)** - Phone calls & SMS
- **[FastAPI](https://fastapi.tiangolo.com)** - High-performance web framework
- **[Podman](https://podman.io)** - Container runtime

---

## 🧪 Quick Test

1. **Call**: Dial [+1 (888) 762-8114](tel:+18887628114)
2. **Order**: "I want a taro milk tea with boba"
3. **Confirm**: Say "yes" when asked
4. **Phone**: Provide your phone number
5. **Check**: Receive SMS with order number
6. **Monitor**: Visit https://voice.boba-demo.deepgram.com/orders
7. **Complete**: Barista marks ready → Receive pickup SMS

---

## 🆘 Need Help?

- **Setup Issues?** → [Troubleshooting Guide](documentations/TROUBLESHOOTING.md)
- **API Questions?** → [API Reference](documentations/API_REFERENCE.md)
- **Architecture Questions?** → [System Architecture](documentations/ARCHITECTURE.md)

