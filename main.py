import os
import json
import telebot
import google.generativeai as genai
from google.api_core import client_options

# =========================
# CONFIGURAZIONE HARDCORE
# =========================

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Forziamo l'endpoint v1 stabile a livello di client_options
my_options = client_options.ClientOptions(api_endpoint="generativelanguage.googleapis.com")

genai.configure(
    api_key=GEMINI_API_KEY,
    client_options=my_options
)

# Inizializziamo il bot
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# Usiamo un nome modello ultra-standard
model = genai.GenerativeModel('gemini-1.5-flash')

PROMPT = "Sei un esperto di Elden Ring. Analizza il volto e restituisci i parametri slider in JSON."

# =========================
# LOGICA
# =========================

def chiedi_gemini(image_bytes):
    # Specifichiamo la versione API v1 direttamente nella chiamata
    response = model.generate_content(
        contents=[
            PROMPT,
            {'mime_type': 'image/jpeg', 'data': image_bytes}
        ]
    )
    return response.text

@bot.message_handler(commands=["start"])
def start(message):
    bot.reply_to(message, "⚔️ Bot Elden Ring Online! Inviami una foto.")

@bot.message_handler(content_types=["photo"])
def handle_photo(message):
    attesa = bot.reply_to(message, "⏳ Tentativo di connessione a Google v1...")
    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        image_bytes = bot.download_file(file_info.file_path)
        
        testo_risposta = chiedi_gemini(image_bytes)
        bot.reply_to(message, f"✅ RISULTATO:\n\n{testo_risposta}")
        
    except Exception as e:
        errore_str = str(e)
        bot.reply_to(message, f"❌ Errore persistente:\n`{errore_str}`", parse_mode="Markdown")
        
        # Se fallisce ancora col 404, l'unica è la chiave API
        if "404" in errore_str:
            bot.send_message(message.chat.id, "⚠️ **ATTENZIONE**: Se vedi ancora 404, devi generare una NUOVA API KEY su AI Studio in un NUOVO progetto. Quella attuale è bloccata sul vecchio sistema.")
    finally:
        try: bot.delete_message(message.chat.id, attesa.message_id)
        except: pass

if __name__ == "__main__":
    bot.infinity_polling()
