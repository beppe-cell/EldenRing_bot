import os
import json
import telebot
import google.generativeai as genai

# Carica variabili d'ambiente
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

bot = telebot.TeleBot(TELEGRAM_TOKEN)
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

@bot.message_handler(commands=["start"])
def start(message):
    bot.reply_to(message, "⚔️ Bot Online! Inviami una foto.")

@bot.message_handler(content_types=["photo"])
def ricevi_foto(message):
    bot.reply_to(message, "⏳ Ricevuta! Analizzo...")
    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        image_bytes = bot.download_file(file_info.file_path)
        
        # Chiamata semplificata
        response = model.generate_content([
            "Analizza il volto e restituisci i parametri Elden Ring in formato JSON.",
            {"mime_type": "image/jpeg", "data": image_bytes}
        ])
        
        bot.reply_to(message, f"✅ Risposta:\n{response.text[:1000]}")
    except Exception as e:
        bot.reply_to(message, f"❌ Errore: {str(e)}")

if __name__ == "__main__":
    print("🚀 Avvio polling...")
    bot.infinity_polling()
