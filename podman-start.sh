#!/bin/bash
set -euo pipefail

# --- Local dev helper for Podman + ngrok ---
# - Ensures Podman VM is running (macOS/Windows)
# - Removes any existing 'boba-voice' container
# - Builds the image from Containerfile
# - Runs the container on port 8000 with your .env

echo "▶️ Ensuring Podman machine is running..."
podman machine start >/dev/null 2>&1 || true

if podman ps -a --format '{{.Names}}' | grep -q '^boba-voice$'; then
  echo "🗑️  Removing old 'boba-voice' container..."
  podman stop boba-voice >/dev/null 2>&1 || true
  podman rm boba-voice   >/dev/null 2>&1 || true
fi

echo "🧱 Building image boba-voice:local ..."
podman build -t boba-voice:local -f Containerfile .

echo "🚀 Starting container on :8000 ..."
podman run -d --name boba-voice \
  --restart unless-stopped \
  -p 8000:8000 \
  --env-file .env \
  boba-voice:local

echo ""
echo "✅ Up! Dashboards:"
echo "   • Orders:  http://localhost:8000/orders"
echo "   • Barista: http://localhost:8000/barista"
echo ""
echo "📞 Expose to Twilio with ngrok:"
echo "   ngrok http 8000"
echo "   (Then set NGROK_HOST in .env and Twilio Voice webhook to https://<NGROK_HOST>/voice)"
echo ""
echo "🔎 Logs (follow):"
echo "   podman logs -f boba-voice"
echo ""
echo "🛑 To stop and remove container manually:"
echo "   podman stop boba-voice && podman rm boba-voice"
echo ""
echo "🛑 Or simply run the helper script:"
echo "   ./podman-stop.sh"
echo ""
echo "🛑 To stop Podman VM entirely:"
echo "   podman machine stop"
