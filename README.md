# OpenCode Telegram Bot

Bot asisten pribadi yang terhubung dengan OpenCode-Desktop melalui Telegram.

## Fitur

- 💬 Chat langsung tanpa prefix `/ask`
- 🇮🇩 Respons dalam Bahasa Indonesia
- ⏳ Notifikasi sedang memproses
- 📝 Asisten AI pribadi
- ⚡ Integrasi OpenCode

## Instalasi Lokal

```bash
# Clone repository
git clone https://github.com/mekelll01/opencode-telegram-bot.git
cd opencode-telegram-bot

# Setup virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Setup environment variable
cp .env.example .env
# Edit .env dan masukkan TELEGRAM_BOT_TOKEN Anda
```

## Jalankan Bot

```bash
python3 bot.py
```

## Deploy ke Railway

1. Push repository ke GitHub
2. Buat akun Railway di https://railway.app
3. Connect GitHub repository
4. Set environment variable `TELEGRAM_BOT_TOKEN` di Railway dashboard
5. Deploy! ✅

## Environment Variables

- `TELEGRAM_BOT_TOKEN` - Token dari @BotFather di Telegram

## Teknologi

- Python 3.14+
- pyTelegramBotAPI
- OpenCode CLI

## Lisensi

MIT
