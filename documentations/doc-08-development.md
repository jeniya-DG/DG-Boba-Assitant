# Development Guide

Guide for contributing to and extending Deepgram BobaRista.

## Development Setup

### Prerequisites

- Python 3.11+
- Podman or Docker
- Git
- Code editor (VS Code, PyCharm, etc.)
- ngrok (for testing with locally)

### Clone Repository

git clone https://github.com/your-org/deepgram-bobarista.git

### Local Development

#### Option 1: Using Podman (Recommended)

# Start development environment

#### Option 2: Direct Python (No Container)

source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Create .env from template

# Run application
uvicorn main:app --reload --host 0.0.0.0 --port 8000

**Advantages of `--reload`:**
- Auto-reloads on code changes
- Faster development cycle
- No need to restart manually

## Project Structure

deepgram-bobarista/
├── app/
│   ├── __init__.py
│   ├── main.py                  # Entry point
│   ├── app_factory.py           # FastAPI app creation
│   ├── settings.py              # Configuration & prompts
│   ├── http_routes.py           # HTTP endpoints
│   ├── ws_bridge.py             # WebSocket bridge
│   ├── agent_client.py          # Deepgram connection
│   ├── agent_functions.py       # Agent tools/functions
│   ├── business_logic.py        # Core business logic
│   ├── orders_store.py          # Order persistence
│   ├── events.py                # Pub/sub system
│   ├── audio.py                 # Audio resampling
│   ├── send_sms.py              # Twilio SMS
│   └── orders.json              # Order data (generated)
├── documentations/              # Documentation files
├── Containerfile                # Docker/Podman build
├── requirements.txt             # Python dependencies
├── sample.env.txt               # Environment template
├── podman-start.sh             # Helper: start container
├── podman-stop.sh              # Helper: stop container
└── README.md                    # Main documentation

## Code Style & Standards

### Python Style

Follow **PEP 8** with these conventions:

# Good
def add_to_cart(flavor: str, toppings: list[str] | None = None) -> dict:
    """Add item to cart with validation."""
    if toppings is None:
        toppings = []

# Use type hints
def checkout_order(phone: str | None = None) -> dict:
    pass

# Use docstrings
def complex_function():
    """
    Brief description.

    Detailed explanation if needed.

    Args:
        param1: Description

    Returns:
        dict: Result object

### Naming Conventions

# Variables and functions: snake_case
order_number = "1234"
def get_order_status():

# Classes: PascalCase
class OrderManager:

# Constants: UPPER_SNAKE_CASE
MAX_ORDERS = 10
DEFAULT_SWEETNESS = "50%"

# Private functions: leading underscore
def _internal_helper():

### Import Organization

# Standard library
import os
import json
from typing import Any, Dict

# Third-party
from fastapi import FastAPI, WebSocket
import websockets

# Local
from .settings import DEEPGRAM_API_KEY
from .orders_store import add_order

## Adding New Features

### 1. Adding a New Menu Item

**Step 1:** Update menu in `business_logic.py`:

    "flavors": [
        "taro milk tea",
        "black milk tea",
        "matcha milk tea"  # ← New flavor
    "toppings": [
        "boba",
        "egg pudding",
        "crystal agar boba",
        "vanilla cream",
        "lychee jelly"  # ← New topping

**Step 2:** Update pricing if needed:

    "addon": 0.50,

**Step 3:** Add aliases if needed:

TOPPING_ALIASES = {
    "lychee jelly": {"lychee jelly", "lychee", "jelly"},

**Step 4:** Update prompt in `settings.py`:

BOBA_PROMPT = """
...
#Menu
STEP 1: CHOOSE A MILK TEA FLAVOR
Taro Milk Tea, Black Milk Tea, Matcha Milk Tea

STEP 2: CHOOSE YOUR TOPPINGS
Boba, Egg Pudding, Crystal Agar Boba, Vanilla Cream, Lychee Jelly

**Step 5:** Test:

# Call and order new item

### 2. Adding a New Agent Function

**Step 1:** Define function in `agent_functions.py`:

def _get_order_history(phone: str) -> dict:
    """Get customer's order history."""
    phone_norm = bl.normalize_phone(phone)
    # Query orders_store for this phone
    # Return list of past orders

**Step 2:** Add function definition:

FUNCTION_DEFS.append({
    "name": "get_order_history",
    "description": "Retrieve customer's previous orders",
            "phone": {
                "description": "Customer's phone number"
        "required": ["phone"]
})

**Step 3:** Map function:

FUNCTION_MAP["get_order_history"] = _get_order_history

**Step 4:** Update prompt to mention the function:

#Tool Usage
- Use `get_order_history` to show returning customers their past orders

### 3. Adding a New HTTP Endpoint

**Step 1:** Add route in `http_routes.py`:

@http_router.get("/api/stats")
def get_stats():
    """Get order statistics."""
    data = list_recent_orders(limit=1000)

    total_orders = len(data)
    total_revenue = sum(o.get("total", 0) for o in data)

    return {
        "total_orders": total_orders,
        "total_revenue": total_revenue,
        # ... more stats

**Step 2:** Test:

curl https://voice.boba-demo.deepgram.com/api/stats

### 4. Adding a New Dashboard

**Step 1:** Create HTML in `http_routes.py`:

KITCHEN_DISPLAY = """<!doctype html>
<html>
<head>
  <title>Kitchen Display</title>
  <style>
    /* Your styles */
  </style>
</head>
<body>
  <h1>Kitchen Display</h1>
  <div id="orders"></div>

  <script>
    // Fetch and display orders
    // Use SSE for real-time updates
  </script>
</body>
</html>"""

@http_router.get("/kitchen")
def kitchen_display():
    return HTMLResponse(KITCHEN_DISPLAY)

**Step 2:** Link from landing page.

### Manual Testing

# 1. Start application

# 2. Start ngrok

# 3. Update Twilio webhook to ngrok URL

# 4. Call and test

### Unit Testing

Create `tests/` directory:

# tests/test_business_logic.py
import pytest
from app import business_logic as bl

def test_add_to_cart():
    bl.CART.clear()

    result = bl.add_to_cart(
        flavor="taro milk tea",
        toppings=["boba"]

    assert result["ok"] == True
    assert len(bl.CART) == 1
    assert bl.CART[0]["flavor"] == "taro milk tea"

    assert bl.normalize_phone("xxx-xxx-xxxx") == "xxx-xxx-xxxx"
    assert bl.normalize_phone("(xxx-xxx-xxxx") == "xxx-xxx-xxxx"

**Run tests:**

# Install pytest
pip install pytest

# Run tests
pytest tests/

## Debugging

### Local Debugging

**VS Code:** Create `.vscode/launch.json`:

  "version": "0.2.0",
  "configurations": [
      "name": "Python: FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "main:app",
        "--reload",
        "--host",
        "0.0.0.0",
        "--port",
        "8000"
      "jinja": true,
      "justMyCode": false,
      "env": {
        "DEEPGRAM_API_KEY": "your-key-here"

### Add Debug Logging

import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def some_function():
    logger.debug("Debug message")
    logger.info("Info message")
    logger.error("Error message")

### Inspect WebSocket Messages

# In ws_bridge.py
async for raw in ws.iter_text():
    print(f"[TWILIO→SERVER] {raw[:100]}...")  # Print first 100 chars

async for message in agent:
    if isinstance(message, bytes):
        print(f"[AGENT→SERVER] Audio: {len(message)} bytes")
    else:
        print(f"[AGENT→SERVER] {message[:100]}...")

## Performance Optimization

### Profiling

import cProfile
import pstats

def profile_function():
    pr = cProfile.Profile()
    pr.enable()

    # Your code here

    pr.disable()
    stats = pstats.Stats(pr)
    stats.sort_stats('cumulative')
    stats.print_stats(10)

### Async Best Practices

# Good - non-blocking
async def handle_request():
    result = await xxx()

# Bad - blocking
def handle_request():
    result = some_sync_operation()  # Blocks event loop

### Memory Management

# Clear large objects when done
def process_audio(audio_data: bytes):
    # Process audio

    # Clear reference
    audio_data = None

# Use generators for large data
def get_orders():
    for order in orders_list:
        yield order

## Database Migration

To scale beyond JSON file storage:

### PostgreSQL Setup

# Install
sudo apt install postgresql

# Create database
sudo -u postgres psql
CREATE DATABASE bobarista;
CREATE USER bobarista_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE bobarista TO bobarista_user;

### SQLAlchemy Models

# app/models.py
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True)
    order_number = Column(String(4), unique=True, index=True)
    phone = Column(String(20), index=True)
    items = Column(JSON)
    total = Column(Float)
    status = Column(String(20), index=True)
    created_at = Column(DateTime)

### Migration Script

# scripts/migrate_to_postgres.py
from app.models import Order
from app.database import SessionLocal

with open("app/orders.json") as f:
    data = json.load(f)

db = SessionLocal()

for order_dict in data["orders"]:
    order = Order(**order_dict)
    db.add(order)

db.commit()

## Deployment

### CI/CD Pipeline

**GitHub Actions** example (`.github/workflows/deploy.yml`):

```yaml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v2

      - name: Build image
        run: podman build -t bobarista .

      - name: Push to registry
        run: |
          podman login quay.io -u ${{ secrets.QUAY_USERNAME }} -p ${{ secrets.QUAY_PASSWORD }}
          podman push bobarista quay.io/your-org/bobarista:latest

      - name: Deploy to server
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.SERVER_HOST }}
          username: ubuntu
          key: ${{ secrets.SSH_KEY }}
          script: |
            podman pull quay.io/your-org/bobarista:latest
            podman stop boba-voice || true
            podman rm boba-voice || true
            podman run -d --name boba-voice \
              quay.io/your-org/bobarista:latest

## Contributing

### Git Workflow

# Create feature branch
git checkout -b feature/new-menu-item

# Make changes

# Commit
git add .
git commit -m "Add matcha milk tea flavor"

# Push
git push origin feature/new-menu-item

# Create Pull Request on GitHub

### Commit Message Format

<type>: <subject>

<footer>

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting
- `refactor`: Code restructuring
- `test`: Adding tests
- `chore`: Maintenance

**Examples:**

feat: Add matcha milk tea flavor

- Added matcha to menu
- Updated prompt with new flavor
- Added tests for matcha ordering

Closes #123

fix: Prevent duplicate SMS notifications

Check session_state before sending SMS to avoid
sending multiple confirmations to the same customer.

Fixes #456

## Code Review Checklist

Before submitting PR:

- [ ] Code follows style guidelines
- [ ] Added tests for new features
- [ ] All tests pass
- [ ] Updated documentation
- [ ] No hardcoded credentials
- [ ] Logging added for debugging
- [ ] Error handling implemented
- [ ] Backward compatible (if possible)
- [ ] Performance considered
- [ ] Security reviewed

## Common Development Tasks

### Update Dependencies

# Check outdated packages
pip list --outdated

# Update specific package
pip install --upgrade package-name

# Update requirements.txt
pip freeze > requirements.txt

### Change Agent Behavior

Edit `settings.py`:

# Your updated prompt here

### Add New Topping

1. Update `MENU` in `business_logic.py`
2. Add aliases if needed
3. Update prompt in `settings.py`
4. Test ordering

### Change Pricing

Update `PRICES` in `business_logic.py`:

    "drink": 6.00,  # ← Changed from 5.50
    "topping": 0.85,  # ← Changed from 0.75

## Resources

### Documentation
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [Deepgram API](https://developers.deepgram.com/)
- [Twilio Docs](https://www.twilio.com/docs)
- [WebSockets](https://websockets.readthedocs.io/)

### Tools
- [Postman](https://www.postman.com/) - API testing
- [wscat](https://github.com/websockets/wscat) - WebSocket testing
- [jq](https://stedolan.github.io/jq/) - JSON processing

### Community
- GitHub Issues: Report bugs
- GitHub Discussions: Ask questions
- Discord/Slack: Real-time chat (if available)

- 📖 [Architecture Guide](05-architecture.md)
- 📊 [API Reference](06-api-reference.md)
- 🔧 [Troubleshooting](07-troubleshooting.md)

## Questions?

If you need help:
1. Check existing documentation
2. Search GitHub issues
3. Create new issue with:
   - Clear description
   - Logs and error messages

Happy coding! 🚀
