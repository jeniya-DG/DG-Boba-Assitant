# Troubleshooting Guide

Common issues and solutions for Deepgram BobaRista.

## Quick Diagnostics

### Check System Status

# Application status

# Nginx status

# Check SSL certificate

# View recent errors
sudo journalctl -u bobarista -p err --since "1 hour ago"

## Call Issues

### Issue: Call Ends Immediately

- Call connects briefly then disconnects
- No audio heard
- "Application error" message from Twilio

**Causes & Solutions:**

#### 1. Webhook URL Incorrect

# Test webhook

# Should return TwiML XML
# If error, check:

**Check Twilio Configuration:**
1. Go to Twilio Console → Phone Numbers
2. Verify webhook URL: `https://voice.boba-demo.deepgram.com/voice`
3. Verify HTTP method: POST
4. Must be HTTPS, not HTTP

#### 2. Server Not Accessible

# Test from external

# Check firewall

# Check Security Group (AWS Console)
# Verify ports 80, 443 are open

#### 3. Application Not Running

# If not running

#### 4. Nginx Not Running

# Check Nginx

# Test config

# Restart if needed

- Call connects
- Hear "Connecting to..." message
- Then silence or static

#### 1. WebSocket Connection Failed

# Check WebSocket endpoint

# Check logs for WebSocket errors
sudo journalctl -u bobarista | grep -i websocket

**Common WebSocket issues:**
- Using `ws://` instead of `wss://`
- Nginx WebSocket proxy not configured
- Firewall blocking WebSocket

**Fix Nginx WebSocket config:**

# Ensure this exists:
    proxy_pass http://xxx-xxx-xxxx:8000;
    # ... other headers

#### 2. Deepgram API Issue

# Check environment variables

# Verify API key is valid
# Go to console.deepgram.com

# Check logs for Deepgram errors
sudo journalctl -u bobarista | grep -i deepgram

#### 3. Audio Resampling Error

# Check for audioop errors
sudo journalctl -u bobarista | grep -i audioop

# Ensure audioop-lts is installed
source /opt/bobarista/venv/bin/activate
pip list | grep audioop

**Reinstall if missing:**
pip install audioop-lts

### Issue: Agent Not Responding

- Audio works
- Can hear agent greeting
- Agent doesn't respond to speech

#### 1. STT Model Issue

# Check configuration
cat /opt/bobarista/.env | grep AGENT_STT_MODEL

# Should be:

#### 2. Microphone/Audio Quality

- Check if speaking clearly
- Reduce background noise
- Ensure phone has good connection

#### 3. Deepgram Credits Exhausted

# Check Deepgram console
# console.deepgram.com → Billing

# View recent usage
# Look for API errors in logs
sudo journalctl -u bobarista | grep "401\|403"

### Issue: Agent Interrupts Frequently

- Agent cuts off when customer speaks
- Voice-over-voice

**Solution:**

This is expected behavior - the agent uses interruption detection to feel more natural. If it's too aggressive:

1. Adjust Deepgram settings (requires code change)
2. Speak more clearly with pauses
3. Wait for agent to finish before responding

## SMS Issues

### Issue: SMS Not Received

- Order confirmed on call
- No SMS received
- SMS shows sent in logs

#### 1. Twilio Credentials Invalid

# Check credentials
cat /opt/bobarista/.env | grep MSG_TWILIO

# Verify in Twilio Console:
# - Account SID matches
# - Auth Token: xxx correct
# - Phone number is correct (+1XXXXXXXXXX)

#### 2. Phone Number No SMS Capability

2. Click on your SMS number
3. Verify **Capabilities** includes SMS/MMS

**If missing:**
- Can't add SMS to existing number
- Need to buy new number with SMS capability

#### 3. SMS Blocked/Filtered

- Check spam folder (if SMS to email)
- Customer may have blocked number
- Carrier may filter automated messages

**Test with your own number:**
# Manually test SMS
python3
>>> from app.send_sms import send_ready_sms
>>> send_ready_sms("TEST", "+1YOUR_PHONE")

#### 4. Check Twilio Logs

1. Twilio Console → Monitor → Logs → Messages
2. Find your message
3. Check status:
   - `delivered` ✅
   - `undelivered` ❌
   - `failed` ❌

**Common failure codes:**
- `21408`: Number doesn't have SMS capability

### Issue: SMS Sent Multiple Times

- Customer receives duplicate confirmation messages

**Cause:** 
- Function called multiple times
- Server restarted mid-call
- SMS fallback triggered

Check session state tracking:
sudo journalctl -u bobarista | grep "SMS"

Should see:
📱 SMS (received) to xxx-xxx-xxxx: order 4782

Only once per order.

## Dashboard Issues

### Issue: Orders Not Showing

- `/orders` page is blank
- Order placed successfully
- No orders in dashboard

#### 1. Check orders.json

# View orders file
cat /opt/bobarista/app/orders.json | jq

# Should show orders array
  "orders": [...]

**If empty:**
- Orders cleared on server restart (expected behavior)
- Make new test order to verify

#### 2. SSE Connection Failed

**Check browser console:**
// Look for errors
EventSource failed to connect

**Test SSE endpoint:**

Should stream events (hang open).

**Fix Nginx SSE:**

#### 3. JavaScript Error

**Open browser console (F12):**
- Look for JavaScript errors
- Check network tab for failed requests

### Issue: Dashboard Not Updating

- Orders show but don't update in real-time
- Must refresh page to see new orders

#### 1. Check SSE Connection

**Browser console:**
// Should see EventSource connection
console.log(es.readyState); // Should be 1 (OPEN)

#### 2. Events Not Publishing

# Check logs for event publishing
sudo journalctl -u bobarista | grep -i "event\|publish"

order_created event published

#### 3. Hard Refresh

- Clear browser cache
- Hard refresh: Ctrl+Shift+R (Windows/Linux) or Cmd+Shift+R (Mac)

## Server Issues

### Issue: High CPU Usage

- Server slow or unresponsive
- High CPU in htop

**Check:**
top

# Check processes
ps aux | sort -nrk 3,3 | head -n 5

#### 1. Too Many Concurrent Calls

- Upgrade instance (t2.small → t2.medium)
- Increase workers (if multi-core)

#### 2. Memory Leak

#### 3. Add Swap

# Create 2GB swap

### Issue: Disk Space Full

# If /dev/xvda1 is at 100%:

#### 1. Clear Logs

# Check log size
sudo du -sh /var/log/*

# Clear old logs
sudo journalctl --vacuum-time=7d

# Clear Nginx logs
sudo truncate -s 0 /var/log/nginx/*.log

#### 2. Clear Package Cache

sudo apt clean
sudo apt autoclean

#### 3. Find Large Files

# Find files > 100MB
sudo find / -type f -size +100M -exec ls -lh {} \;

### Issue: Application Won't Start

- `systemctl start bobarista` fails
- Service shows "failed" status

#### 1. Missing Environment Variables

# Check .env file exists
ls -la /opt/bobarista/.env

# Check for required variables
cat /opt/bobarista/.env | grep -E "DEEPGRAM|TWILIO|VOICE_HOST"

#### 2. Python Dependency Error

# Reinstall dependencies

#### 3. Port Already in Use

# Check port 8000
sudo lsof -i :8000

# Kill process if needed
sudo kill -9 <PID>

#### 4. Permission Error

# Check ownership
ls -la /opt/bobarista

# Fix if needed
sudo chown -R ubuntu:ubuntu /opt/bobarista

## SSL/Certificate Issues

### Issue: SSL Certificate Expired

- Browser shows "Not secure"
- Certificate error

**Check expiry:**

**Renew:**
sudo systemctl reload nginx

**Auto-renewal not working:**
# Check certbot timer
sudo systemctl status certbot.timer

# Enable if disabled
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer

### Issue: Certificate Not Found

- Nginx fails to start
- "SSL certificate not found" error

# Run certbot

## Network Issues

### Issue: Can't Reach Server

- curl times out
- Can't SSH
- DNS resolves but no connection

#### 1. Security Group

AWS Console → EC2 → Security Groups → bobarista-sg

Verify rules:
- Port 22 (SSH)
- Port 80 (HTTP)
- Port 443 (HTTPS)

#### 2. Instance Running

AWS Console → EC2 → Instances

Verify instance is "running" (not stopped/terminated)

#### 3. Elastic IP

AWS Console → EC2 → Elastic IPs

Verify IP is associated with instance

#### 4. Network ACLs

AWS Console → VPC → Network ACLs

Verify inbound/outbound rules allow traffic

## Deepgram Issues

### Issue: 401 Unauthorized

- Agent doesn't connect
- Logs show "401 Unauthorized"

# Check API key
cat /opt/bobarista/.env | grep DEEPGRAM_API_KEY

# Verify in Deepgram Console:
# console.deepgram.com → API Keys

# Update if needed
nano /opt/bobarista/.env

### Issue: Model Not Found

- Error: "Model 'xyz' not found"

# Check model names
cat /opt/bobarista/.env | grep AGENT

## Twilio Issues

### Issue: Webhook Validation Failed

- Logs show signature validation error

If you implemented webhook validation:

# Ensure correct auth token
validator = RequestValidator(TWILIO_AUTH_TOKEN)

**Or disable validation temporarily:**
# Comment out validation
# if not xxx(request):
#     raise HTTPException(403)

## Logging & Debugging

### View Logs

# Last 100 lines

# Errors only

# Specific time range
sudo journalctl -u bobarista --since "xxx-xxx-xxxx:00" --until "xxx-xxx-xxxx:00"

# Nginx logs
sudo tail -f /var/log/nginx/bobarista-error.log
sudo tail -f /var/log/nginx/bobarista-access.log

### Enable Debug Mode

**Edit service file:**

# Add --log-level debug
ExecStart=.../uvicorn main:app --host 0.0.0.0 --port 8000 --log-level debug

## Emergency Procedures

### Quick Restart

# Restart everything

### Rollback to Previous Version

# If using git
git log  # Find previous commit
git checkout <commit-hash>

# If using backup
tar -xzf xxx.tar.gz

### Factory Reset

# Stop services
sudo systemctl stop bobarista

# Clear orders
echo '{"orders":[]}' > /opt/bobarista/app/orders.json

# Restart

## Getting Help

### Collect Information

When reporting issues, include:

1. **System info:**

2. **Application logs:**
sudo journalctl -u bobarista -n 100 --no-pager > logs.txt

3. **Nginx logs:**
sudo tail -100 /var/log/nginx/bobarista-error.log > nginx-error.txt

4. **Configuration:**
# Don't share actual API keys!
cat .env | sed 's/=.*/=REDACTED/'

5. **Error message:**
- Exact error text
- Steps to reproduce
- Expected vs actual behavior

## Prevention

### Regular Maintenance

# Weekly

# Monthly
df -h  # Check disk space
free -h  # Check memory

### Monitoring Setup

Consider:
- **UptimeRobot**: Monitor uptime
- **CloudWatch**: AWS metrics
- **Sentry**: Error tracking
- **Grafana**: Custom dashboards

- 📖 [API Reference](06-api-reference.md)
- 🏗️ [Architecture Guide](05-architecture.md)
