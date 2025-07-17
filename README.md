# Telegram Bot

Telegram bot with OpenAI integration, voice processing, and Supabase backend.

## Setup

1. Create virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate     # Windows
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Install ffmpeg:
```bash
# Ubuntu/Debian
sudo apt-get install ffmpeg

# macOS
brew install ffmpeg

# Windows
# Download from https://ffmpeg.org/download.html
```

4. Configure environment:
```bash
cp env.template .env
# Edit .env with your credentials
```

5. Run the bot:
```bash
python -m ona.bot.main
```

## Security Note

All sensitive credentials are encrypted using Fernet encryption. Use the provided FERNET_KEY to encrypt your credentials before adding them to .env file. 