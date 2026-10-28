import os
import telebot
import subprocess
import json
from io import BytesIO
import pytesseract
from PIL import Image

# Konfigurasi
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
if not TOKEN:
    raise SystemExit("ERROR: TELEGRAM_BOT_TOKEN belum diset")

bot = telebot.TeleBot(TOKEN, threaded=True)

# Simpan session ID per user untuk multi-turn conversation
user_sessions = {}

# Cek opencode
try:
    subprocess.run(['opencode', '--version'], capture_output=True, timeout=5)
    HAS_OPENCODE = True
except Exception:
    HAS_OPENCODE = False

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    user_id = message.chat.id
    if user_id in user_sessions:
        del user_sessions[user_id]
    
    bot.reply_to(message, 
        "Halo! Saya asisten pribadi OpenCode Anda.\n\n"
        "✅ Chat bolak-balik dengan memory\n"
        "📷 Kirim foto untuk OCR & analisis\n\n"
        "/reset - Mulai percakapan baru\n"
        "/status - Cek status bot")

@bot.message_handler(commands=['status'])
def send_status(message):
    user_id = message.chat.id
    has_session = user_id in user_sessions
    status = "🟢 Bot aktif"
    status += " - Terhubung ke OpenCode" if HAS_OPENCODE else " - Mode fallback"
    if has_session:
        status += f"\n💬 Session aktif: {user_sessions[user_id][:20]}..."
    bot.reply_to(message, status)

@bot.message_handler(commands=['reset'])
def reset_chat(message):
    user_id = message.chat.id
    if user_id in user_sessions:
        del user_sessions[user_id]
    bot.reply_to(message, "🔄 Percakapan di-reset. Mulai chat baru sekarang!")

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    try:
        photo = message.photo[-1]
        file_info = bot.get_file(photo.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        img = Image.open(BytesIO(downloaded_file))
        extracted_text = pytesseract.image_to_string(img, lang='ind+eng').strip()
        
        if not extracted_text:
            extracted_text = "(Tidak ada teks terdeteksi)"
        
        caption = message.caption or "Jelaskan teks ini:"
        prompt = f"{caption}\n\n{extracted_text}"
        
        process_question(message, prompt)
        
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    process_question(message, message.text)

def process_question(message, user_text):
    user_id = message.chat.id
    
    try:
        if HAS_OPENCODE:
            prompt = f"Jawab dalam Bahasa Indonesia ringkas: {user_text}"
            
            # Bangun command
            cmd = ['opencode', 'run', '--format', 'json']
            
            # Jika user sudah punya session, continue
            if user_id in user_sessions:
                cmd.extend(['--session', user_sessions[user_id], '--continue'])
            
            cmd.append(prompt)
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, stderr = process.communicate(timeout=120)
            
            if process.returncode == 0 and stdout.strip():
                # Parse JSON lines untuk ekstrak text dan session ID
                response_text = ""
                session_id = None
                
                for line in stdout.strip().split('\n'):
                    try:
                        data = json.loads(line)
                        
                        # Simpan session ID dari response pertama
                        if session_id is None and 'sessionID' in data:
                            session_id = data['sessionID']
                        
                        # Ambil text response
                        if data.get('type') == 'text' and 'part' in data:
                            text = data['part'].get('text', '')
                            if text:
                                response_text += text
                    except json.JSONDecodeError:
                        continue
                
                # Simpan session ID untuk percakapan berikutnya
                if session_id:
                    user_sessions[user_id] = session_id
                
                response = response_text.strip() if response_text else "❌ OpenCode tidak memberikan respons."
            else:
                response = "❌ OpenCode error. Coba lagi."
        else:
            response = "❌ OpenCode tidak tersedia."
        
        # Potong jika terlalu panjang
        if len(response) > 4000:
            response = response[:4000] + "\n\n... (terpotong)"
        
        bot.reply_to(message, response)
        
    except subprocess.TimeoutExpired:
        bot.reply_to(message, "⏱️ Timeout. Coba pertanyaan lebih singkat.")
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

if __name__ == '__main__':
    print("🚀 Bot berjalan dengan multi-turn conversation support!")
    print("📝 Setiap user memiliki session chat terpisah dengan memory")
    bot.polling(none_stop=True, timeout=60)
