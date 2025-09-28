# app/ws_bridge.py

import os, json, base64, asyncio
from fastapi import FastAPI, WebSocket
from starlette.websockets import WebSocketDisconnect

from .agent_client import connect_agent, send_agent_settings
from .agent_functions import FUNCTION_MAP, session_state
from .business_logic import checkout_order
from .send_sms import send_received_sms
from .audio import (
    ulaw8k_to_lin16_48k,
    lin16_24k_to_ulaw8k,
    chunk_bytes,
    TWILIO_FRAME_BYTES,
)
from .orders_store import add_order
from .events import publish

def register_ws_routes(app: FastAPI):

    @app.websocket("/twilio")
    async def twilio_agent(ws: WebSocket):
        await ws.accept()
        print("✅ Twilio WebSocket connected")

        agent = await connect_agent()
        await send_agent_settings(agent)

        stream_sid = None

        # resampler states
        twilio_to_agent_state = None
        agent_to_twilio_state = None

        async def maybe_send_sms_fallback():
            """
            Fallback on stop/disconnect:
            - Only finalize/send if phone was explicitly confirmed AND not already sent.
            """
            if session_state.get("received_sms_sent"):
                return
            if not session_state.get("phone_confirmed"):
                print("ℹ️ Skipping finalize: phone not confirmed.")
                return

            phone = session_state.get("phone_number")
            order = session_state.get("order_number")
            print(f"📱 Final phone: {phone}")
            print(f"🧾 Final order: {order}")

            # finalize on hangup if needed (only if confirmed)
            if phone and not order:
                try:
                    res = checkout_order(name=None, phone=phone)
                    if isinstance(res, dict) and res.get("ok"):
                        order = res.get("order_number")
                        session_state["order_number"] = order
                        add_order({
                            "order_number": res["order_number"],
                            "phone": res.get("phone"),
                            "items": res.get("items") or [],
                            "total": res.get("total", 0.0),
                            "status": res.get("status", "received"),
                            "created_at": res.get("created_at"),
                        })
                        publish({"type": "order_created", "order_number": res["order_number"], "status": "received"})
                        print(f"✅ Server-side checkout finalized. Order: {order}")
                    else:
                        print("ℹ️ No items to finalize; skipping SMS.")
                        return
                except Exception as e:
                    print(f"❌ Server-side checkout failed: {e}")
                    return

            if phone and order and not session_state.get("received_sms_sent"):
                try:
                    send_received_sms(order_no=order, to_phone_no=phone)
                    session_state["received_sms_sent"] = True
                except Exception as e:
                    print(f"❌ Error sending confirmation SMS (fallback): {e}")

        async def agent_to_twilio_task():
            nonlocal agent_to_twilio_state
            async for message in agent:
                # Agent audio: linear16@24k → Twilio μ-law/8k
                if isinstance(message, (bytes, bytearray)):
                    if not stream_sid: continue
                    ulaw8k, agent_to_twilio_state = lin16_24k_to_ulaw8k(message, agent_to_twilio_state)
                    for frame in chunk_bytes(ulaw8k, TWILIO_FRAME_BYTES):
                        if not frame: continue
                        await ws.send_text(json.dumps({
                            "event": "media",
                            "streamSid": stream_sid,
                            "media": {"payload": base64.b64encode(frame).decode("ascii")}
                        }))
                    continue

                # Text events (incl. function calls)
                try:
                    evt = json.loads(message)
                except Exception:
                    continue

                etype = evt.get("type")

                if etype == "UserStartedSpeaking" and stream_sid:
                    await ws.send_text(json.dumps({"event": "clear", "streamSid": stream_sid}))
                    continue

                if etype == "FunctionCallRequest":
                    for fc in evt.get("functions", []):
                        if fc.get("client_side") is False:
                            continue
                        fn_id   = fc.get("id")
                        fn_name = fc.get("name")
                        raw_args = fc.get("arguments") or "{}"
                        try:
                            args = json.loads(raw_args) if isinstance(raw_args, str) else (raw_args or {})
                        except Exception:
                            args = {}
                        print(f"🛠️  FunctionCallRequest → {fn_name}({args})")
                        try:
                            if fn_name in FUNCTION_MAP:
                                result = FUNCTION_MAP[fn_name](**args)
                                resp = {"type":"FunctionCallResponse","id":fn_id,"name":fn_name,
                                        "content": json.dumps(result) if not isinstance(result,str) else result}
                            else:
                                resp = {"type":"FunctionCallResponse","id":fn_id,"name":fn_name or "unknown",
                                        "content": json.dumps({"ok":False,"error":f"Unknown function '{fn_name}'"})}
                            await agent.send(json.dumps(resp))
                            print(f"✅ FunctionCallResponse ← {fn_name}: {resp['content']}")
                        except Exception as e:
                            err = {"type":"FunctionCallResponse","id":fn_id,"name":fn_name or "unknown",
                                   "content": json.dumps({"ok":False,"error":str(e)})}
                            await agent.send(json.dumps(err))
                            print(f"❌ Function handler error: {e}")
                    continue

                print("[agent]", evt)

        forward_task = asyncio.create_task(agent_to_twilio_task())

        try:
            async for raw in ws.iter_text():
                try:
                    evt = json.loads(raw)
                except Exception:
                    continue

                etype = evt.get("event")
                if etype != "media":
                    print(f"[twilio evt] {etype}")

                if etype == "start":
                    stream_sid = evt["start"]["streamSid"]
                    session_state["phone_number"] = None
                    session_state["order_number"] = None
                    session_state["phone_confirmed"] = False
                    session_state["received_sms_sent"] = False
                    twilio_to_agent_state = None
                    agent_to_twilio_state = None
                    print(f"▶️ Stream started: {stream_sid}")

                elif etype == "media":
                    ulaw8k = base64.b64decode(evt["media"]["payload"])
                    lin48k, twilio_to_agent_state = ulaw8k_to_lin16_48k(ulaw8k, twilio_to_agent_state)
                    if lin48k:
                        await agent.send(lin48k)

                elif etype == "stop":
                    print("⏹️ Stream stopped")
                    await maybe_send_sms_fallback()
                    break

                else:
                    print("[twilio raw]", evt)

        except WebSocketDisconnect:
            print("⚠️ Twilio WebSocketDisconnect")
            await maybe_send_sms_fallback()
        finally:
            try: await agent.close()
            except Exception: pass
            forward_task.cancel()
            try: await ws.close()
            except Exception: pass
            await maybe_send_sms_fallback()
            print("🔌 Twilio WebSocket closed")
