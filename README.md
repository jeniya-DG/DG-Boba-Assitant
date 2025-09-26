# Voice-Powered Boba Ordering System

A real-time voice ordering system for boba tea shops built with FastAPI, Twilio, and Deepgram. Customers can place orders through natural conversations with an AI-powered assistant.

## Features

* **Voice Ordering**: Natural language ordering via phone calls
* **Multi-Provider AI**: Support for OpenAI, Google Gemini, and other AI providers
* **Real-Time Speech Processing**: Powered by Deepgram for speech-to-text and text-to-speech
* **SMS Integration**: Order confirmations and notifications via Twilio SMS
* **Configurable Menu**: Easy customization through JSON configuration
* **WebSocket Communication**: Real-time audio streaming between Twilio and Deepgram
* **Testing Tools**: Built-in echo server for validating Twilio integration

## Technology Stack

* **Backend**: FastAPI (Python)
* **Voice Services**: Deepgram (Voice Agent)
* **Communication**: Twilio (Voice & SMS)
* **Protocol**: WebSockets for real-time audio streaming

## Prerequisites

* Python 3.8+
* [Twilio Account](https://www.twilio.com/) with phone number
* [Deepgram API Key](https://deepgram.com/)
* [ngrok](https://ngrok.com/) or similar tunneling service for development
* API key from chosen AI provider (OpenAI, Google, etc.)

## Installation and Setup

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/VapiConf.git
cd VapiConf
```

### 2. Set Up a Virtual Environment

```bash
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
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
DEEPGRAM_API_KEY=your_deepgram_api_key_here
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_FROM_E164=+1234567890   # Your Twilio phone number
TWILIO_TO_E164=+0987654321     # Test destination number
NGROK_HOST=your-ngrok-subdomain.ngrok-free.app
```

### 5. Configure the AI Agent

Edit `config.json` to customize your assistant:

* **AI Provider**: Choose between OpenAI, Google, Deepgram, etc.
* **Voice Model**: Select from Deepgram’s voice models
* **Menu Items**: Customize available flavors and toppings
* **Greeting Message**: Set a custom welcome message

## Usage

### Development Server

1. Start the FastAPI server:

   ```bash
   cd app
   uvicorn main:app --reload --port 8000
   ```

2. Start an ngrok tunnel (in another terminal):

   ```bash
   ngrok http 8000
   ```

3. Update environment variables:

   * Copy your ngrok URL and update `NGROK_HOST` in `.env`
   * Configure your Twilio phone number webhook to point to:
     `https://your-ngrok-url.ngrok-free.app/voice`

4. Test the system:

   * Call your Twilio phone number
   * You should hear the greeting and interact with the ordering assistant

### Testing Mode

For basic Twilio integration testing, run the echo server:

```bash
uvicorn echo:app --reload --port 8000
```

This plays a test tone when you call.

## API Endpoints

### Voice Webhook

* **POST** `/voice` – Twilio voice webhook endpoint
* Returns TwiML to connect the caller to a WebSocket stream

### WebSocket

* **WS** `/twilio` – Real-time audio streaming endpoint
* Handles bidirectional audio between Twilio and Deepgram

## Configuration

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

Update the AI prompt in `config.json` to:

* Add or remove flavors
* Modify toppings
* Change pricing
* Adjust business rules

## File Structure

```
├── app/
│   ├── main.py        # Main FastAPI application
│   └── echo.py        # Testing echo server
├── config.json        # AI agent configuration
├── sample.env         # Environment template
├── requirements.txt   # Python dependencies
└── README.md          # Documentation
```

### Environment Variables

* `DEEPGRAM_API_KEY`: Your Deepgram API key
* `TWILIO_ACCOUNT_SID`: Twilio account identifier
* `TWILIO_AUTH_TOKEN`: Twilio authentication token
* `TWILIO_FROM_E164`: Your Twilio phone number (E.164 format)
* `TWILIO_TO_E164`: Test destination number (E.164 format)
* `NGROK_HOST`: Your ngrok hostname (without protocol)

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-feature`)
3. Commit your changes (`git commit -am 'Add new feature'`)
4. Push to the branch (`git push origin feature/new-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License. See the LICENSE file for details.
