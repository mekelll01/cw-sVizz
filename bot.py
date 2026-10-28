import os
import telebot
from telebot import types
import subprocess
import threading

# Konfigurasi - token diambil dari environment variable
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
if not TOKEN:
    raise SystemExit("ERROR: TELEGRAM_BOT_TOKEN belum diset. Set lewat environment variable atau file .env")

bot = telebot.TeleBot(TOKEN)

# Cek apakah opencode tersedia di system
try:
    subprocess.run(['opencode', '--version'], capture_output=True, timeout=5)
    HAS_OPENCODE = True
except Exception:
    HAS_OPENCODE = False
    print(f"[INFO] opencode tidak tersedia di environment ini. Bot akan menggunakan fallback response.")

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, 
        "Halo! Saya asisten pribadi OpenCode Anda.\n\n"
        "Cukup ketik pertanyaan langsung, saya akan membantu!\n\n"
        "Perintah:\n"
        "/status - Cek status bot\n"
        "/help - Tampilkan bantuan")

@bot.message_handler(commands=['status'])
def send_status(message):
    status = "🟢 Bot aktif"
    status += " - Terhubung ke OpenCode" if HAS_OPENCODE else " - Mode fallback (OpenCode tidak tersedia di server)"
    bot.reply_to(message, status)

@bot.message_handler(commands=['ask'])
def handle_ask(message):
    user_text = message.text.replace('/ask', '').strip()
    if not user_text:
        bot.reply_to(message, "Silakan masukkan pertanyaan Anda.")
        return
    process_question(message, user_text)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    process_question(message, message.text)

def generate_fallback_response(user_text):
    """Jawaban sederhana tanpa OpenCode (untuk deploy cloud)"""
    lower = user_text.lower()
    if any(word in lower for word in ['halo', 'hai', 'hi', 'assalam']):
        return "Halo! 👋 Ada yang bisa saya bantu?"
    elif any(word in lower for word in ['thank', 'makasih', 'terima kasih', 'thanks']):
        return "Sama-sama! Ada lagi yang bisa saya bantu? 😊"
    elif any(word in lower for word in ['python', 'python', 'code', 'koding']):
        return "Untuk pertanyaan coding, saya sarankan menggunakan OpenCode Desktop di laptop Anda untuk hasil terbaik. Bot ini akan memprosesnya secara langsung saat dijalankan secara lokal."
    else:
        return f"Pertanyaan: {user_text}\n\nMohon maaf, saat ini bot berjalan di cloud tanpa akses OpenCode penuh.\nUntuk asisten AI yang lebih lengkap, jalankan bot di laptop Anda dengan OpenCode-Desktop."

def process_question(message, user_text):
    # Kirim notifikasi sedang memproses
    processing_msg = bot.reply_to(message, "⏳ Sedang memproses, mohon tunggu...")
    
    try:
        if HAS_OPENCODE:
            # Tambahkan instruksi untuk menjawab dalam Bahasa Indonesia
            prompt = f"Jawab dalam Bahasa Indonesia secara ringkas dan jelas: {user_text}"
            
            process = subprocess.Popen(
                ['opencode', 'run', prompt],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, stderr = process.communicate(timeout=120)  # timeout 2 menit
            
            if process.returncode == 0 and stdout.strip():
                response = stdout.strip()
                bot.delete_message(message.chat.id, processing_msg.message_id)
            else:
                response = generate_fallback_response(user_text)
                bot.delete_message(message.chat.id, processing_msg.message_id)
        else:
            response = generate_fallback_response(user_text)
            bot.delete_message(message.chat.id, processing_msg.message_id)

        # Potong jika terlalu panjang (batas Telegram 4096 karakter)
        if len(response) > 4000:
            response = response[:4000] + "\n\n... (pesan terpotong)"
        
        bot.reply_to(message, response)
        
    except subprocess.TimeoutExpired:
        bot.delete_message(message.chat.id, processing_msg.message_id)
        bot.reply_to(message, "⏱️ Waktu pemrosesan habis. Coba pertanyaan yang lebih singkat.")
    except Exception as e:
        bot.delete_message(message.chat.id, processing_msg.message_id)
        bot.reply_to(message, f"Maaf, terjadi kesalahan: {str(e)}")

if __name__ == '__main__':
    print("Bot Telegram OpenCode sedang berjalan...")
    print(f"Mode: {'OpenCode' if HAS_OPENCODE else 'Fallback'}")
    print("Kirim pesan ke bot Anda di Telegram untuk memulai.")
    bot.polling(none_stop=True)
