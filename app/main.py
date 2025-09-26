import os, json, base64, asyncio
from fastapi import FastAPI, WebSocket
from fastapi.responses import Response
from dotenv import load_dotenv
import websockets
from websockets.legacy.client import WebSocketClientProtocol

load_dotenv()

app = FastAPI(title="Twilio ⇄ Deepgram Voice Agent")

# ---- Config
NGROK_HOST = os.getenv("NGROK_HOST", "multifibered-glossarially-martine.ngrok-free.dev")
DG_API_KEY = os.environ["DEEPGRAM_API_KEY"]

# ---- Load configuration from config.json
def load_config() -> dict:
    """Load configuration from config.json file"""
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
            print("✅ Loaded configuration from config.json")
            return config
    except FileNotFoundError:
        print("⚠️ Warning: config.json not found, using default settings")
        return {}
    except Exception as e:
        print(f"⚠️ Warning: Error reading config.json: {e}")
        return {}

# ---- TwiML webhook (HTTP)
@app.post("/voice")
def voice_twiml():
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Say>Connecting you to the Deepgram Boba Rista.</Say>
  <Connect>
    <Stream url="wss://{NGROK_HOST}/twilio" />
  </Connect>
</Response>"""
    return Response(content=twiml, media_type="text/xml")

# ---- Deepgram Agent helpers
async def connect_agent() -> WebSocketClientProtocol:
    return await websockets.connect(
        "wss://agent.deepgram.com/v1/agent/converse",
        subprotocols=["token", DG_API_KEY],
        max_size=2**24,
    )

async def send_agent_settings(ws: WebSocketClientProtocol):
    # Load configuration from config.json
    config = load_config()
    
    # Use config.json settings as base, but override audio settings for Twilio compatibility
    if config:
        settings = config.copy()
        # Override audio settings for Twilio (requires mulaw 8000)
        settings["audio"] = {
            "input":  {"encoding": "mulaw", "sample_rate": 8000},
            "output": {"encoding": "mulaw", "sample_rate": 8000, "container": "none"},
        }
        print("✅ Using settings from config.json (with Twilio audio overrides)")
    else:
        # Fallback settings if config.json is not available
        settings = {
            "type": "Settings",
            "audio": {
                "input":  {"encoding": "mulaw", "sample_rate": 8000},
                "output": {"encoding": "mulaw", "sample_rate": 8000, "container": "none"},
            },
            "agent": {
                "language": "en",
                "listen": {
                    "provider": {"type": "deepgram", "model": "nova-3"}
                },
                "think": {
                    "provider": {"type": "open_ai", "model": "gpt-4o-mini", "temperature": 0.5},
                    "prompt": "You are a virtual boba ordering assistant. Help customers order from the menu.",
                },
                "speak": {
                    "provider": {"type": "deepgram", "model": "aura-2-helena-en"}
                },
                "greeting": "Hey! Welcome to Deepgram boba hotline. What would you like to order?"
            },
        }
        print("⚠️ Using fallback settings")
    
    await ws.send(json.dumps(settings))

# ---- Twilio Media Streams <-> Agent bridge (WebSocket)
@app.websocket("/twilio")
async def twilio_agent(ws: WebSocket):
    await ws.accept()
    print("✅ Twilio WebSocket connected")

    agent = await connect_agent()
    await send_agent_settings(agent)

    stream_sid = None

    async def agent_to_twilio():
        async for message in agent:
            if isinstance(message, (bytes, bytearray)):
                # Agent TTS audio (mu-law 8k) -> Twilio media frame
                if not stream_sid:
                    continue
                await ws.send_text(json.dumps({
                    "event": "media",
                    "streamSid": stream_sid,
                    "media": {"payload": base64.b64encode(message).decode("ascii")}
                }))
            else:
                # Optional: log agent control messages
                try:
                    print("[agent]", json.loads(message))
                except Exception:
                    pass

    forward_task = asyncio.create_task(agent_to_twilio())

    try:
        async for raw in ws.iter_text():
            evt = json.loads(raw)
            etype = evt.get("event")

            if etype == "start":
                stream_sid = evt["start"]["streamSid"]
                print(f"▶️ Stream started: {stream_sid}")
            elif etype == "media":
                # Twilio caller audio (base64 mu-law) -> raw bytes -> send to agent
                payload = base64.b64decode(evt["media"]["payload"])
                await agent.send(payload)
            elif etype == "stop":
                print("⏹️ Stream stopped")
                break
    finally:
        await agent.close()
        forward_task.cancel()
        await ws.close()
        print("🔌 Twilio WebSocket closed")
