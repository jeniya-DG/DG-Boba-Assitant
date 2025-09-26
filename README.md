# Voice-Powered Boba Ordering System

A real-time voice ordering system for boba tea shops built with FastAPI, Twilio, and Deepgram. Customers can call in and place orders through natural conversation with an AI-powered assistant.

## 🎯 Features

- **Voice Ordering**: Natural language voice ordering via phone calls
- **Multi-Provider AI**: Support for OpenAI, Google Gemini, and other AI providers
- **Real-time Speech Processing**: Powered by Deepgram for speech-to-text and text-to-speech
- **SMS Integration**: Order confirmations and notifications via Twilio SMS
- **Configurable Menu**: Easy menu customization through JSON configuration
- **WebSocket Communication**: Real-time audio streaming between Twilio and Deepgram
- **Testing Tools**: Built-in echo server for testing Twilio integration

## 🛠 Tech Stack

- **Backend**: FastAPI (Python)
- **Voice Services**: Deepgram (STT/TTS)
- **Communication**: Twilio (Voice & SMS)
- **AI Providers**: OpenAI, Google Gemini, Deepgram
- **Protocol**: WebSockets for real-time audio streaming

## 📋 Prerequisites

- Python 3.8+
- [Twilio Account](https://www.twilio.com/) with phone number
- [Deepgram API Key](https://deepgram.com/)
- [ngrok](https://ngrok.com/) or similar tunneling service for development
- AI Provider API Key (OpenAI, Google, etc.)

## 🚀 Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/VapiConf.git
cd VapiConf
```

### 2. Set up Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Environment Configuration
Copy the sample environment file and configure your credentials:
```bash
cp sample.env .env
```

Edit `.env` with your actual API keys and configuration:
```env
# Required API Keys
DEEPGRAM_API_KEY=your_deepgram_api_key_here
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_FROM_E164=+1234567890  # Your Twilio phone number
TWILIO_TO_E164=+0987654321    # Test destination number

# Development
NGROK_HOST=your-ngrok-subdomain.ngrok-free.app
```

### 5. Configure Your AI Agent
Edit `config.json` to customize your boba ordering assistant:
- **AI Provider**: Choose between OpenAI, Google, Deepgram, etc.
- **Voice Model**: Select from Deepgram's voice models
- **Menu Items**: Customize available flavors and toppings
- **Greeting Message**: Set custom welcome message

## 🎮 Usage

### Development Server
1. **Start the FastAPI server**:
```bash
cd app
uvicorn main:app --reload --port 8000
```

2. **Set up ngrok tunnel** (in another terminal):
```bash
ngrok http 8000
```

3. **Update environment variables**:
   - Copy your ngrok URL and update `NGROK_HOST` in `.env`
   - Configure your Twilio phone number webhook to: `https://your-ngrok-url.ngrok-free.app/voice`

4. **Test the system**:
   - Call your Twilio phone number
   - You should hear the greeting and be connected to the boba ordering assistant

### Testing Mode
For basic Twilio integration testing, use the echo server:
```bash
uvicorn echo:app --reload --port 8000
```
This will play a test tone when you call.

## 📡 API Endpoints

### Voice Webhook
- **POST** `/voice` - Twilio voice webhook endpoint
- Returns TwiML to connect caller to WebSocket stream

### WebSocket
- **WS** `/twilio` - Real-time audio streaming endpoint
- Handles bidirectional audio between Twilio and Deepgram

## ⚙️ Configuration

### Agent Settings (`config.json`)
```json
{
  "agent": {
    "language": "en",
    "listen": {
      "provider": {"type": "deepgram", "model": "nova-3"}
    },
    "think": {
      "provider": {"type": "open_ai", "model": "gpt-4o-mini"},
      "prompt": "You are a virtual boba ordering assistant..."
    },
    "speak": {
      "provider": {"type": "deepgram", "model": "aura-2-helena-en"}
    },
    "greeting": "Welcome to our boba shop! What would you like to order?"
  }
}
```

### Menu Customization
The AI prompt in `config.json` includes the full menu. Edit the prompt to:
- Add/remove flavors
- Modify toppings
- Change pricing
- Update business rules

## 🧪 Development & Testing

### File Structure
```
VapiConf/
├── app/
│   ├── main.py          # Main FastAPI application
│   └── echo.py          # Testing echo server
├── config.json          # AI agent configuration
├── sample.env           # Environment template
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

### Environment Variables
- `DEEPGRAM_API_KEY`: Your Deepgram API key
- `TWILIO_ACCOUNT_SID`: Twilio account identifier
- `TWILIO_AUTH_TOKEN`: Twilio authentication token
- `TWILIO_FROM_E164`: Your Twilio phone number (E.164 format)
- `TWILIO_TO_E164`: Test destination number (E.164 format)
- `NGROK_HOST`: Your ngrok hostname (without protocol)

### Debugging
- Enable debug logging in the FastAPI app
- Monitor WebSocket connections in browser dev tools
- Use Twilio's console for webhook debugging
- Check ngrok's web interface at `http://localhost:4040`

## 🚀 Deployment

### Production Deployment
1. Use a production WSGI server like Gunicorn or uWSGI
2. Set up proper SSL certificates
3. Configure webhooks with your production domain
4. Use environment variables for all sensitive data
5. Set up monitoring and logging

### Recommended Stack
- **Hosting**: Railway, Render, or AWS
- **Reverse Proxy**: Nginx
- **Process Manager**: PM2 or systemd
- **SSL**: Let's Encrypt or Cloudflare

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-feature`)
3. Commit your changes (`git commit -am 'Add new feature'`)
4. Push to the branch (`git push origin feature/new-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

- **Issues**: Report bugs or request features via GitHub Issues
- **Documentation**: Check the Deepgram and Twilio documentation for API details
- **Community**: Join the discussions in GitHub Discussions

## 🙏 Acknowledgments

- [Deepgram](https://deepgram.com/) for speech recognition and synthesis
- [Twilio](https://twilio.com/) for telecommunications infrastructure
- [FastAPI](https://fastapi.tiangolo.com/) for the web framework

---

Made with ❤️ for boba lovers everywhere! 🧋
