import os
import json
import telebot
import google.generativeai as genai

# CONFIGURAZIONE
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

bot = telebot.TeleBot(TELEGRAM_TOKEN)
genai.configure(api_key=GEMINI_API_KEY)

# Usiamo il nome del modello che ha più probabilità di essere visto dalle vecchie librerie
model = genai.GenerativeModel('gemini-1.5-flash')

PROMPT_CONFIG = """
Sei un esperto di Elden Ring. Analizza il volto e genera SOLO un JSON.
Regole: Solo JSON, no markdown, valori slider da 0 a 8.
{
  "genere": "",
  "sezioni": [{"nome": "STRUTTURA TESTA", "parametri": [{"nome": "Dimensione", "valore": 4}]}],
  "colori": {"pelle": "", "occhi": "", "capelli": ""},
  "note": ""
}
"""

def chiedi_gemini(image_bytes):
    # Sintassi semplificata al massimo per evitare errori di versione
    img = {'mime_type': 'image/jpeg', 'data': image_bytes}
    
    # Chiamata base senza parametri opzionali moderni
    response = model.generate_content([PROMPT_CONFIG, img])
    
    testo = response.text.strip()
    if "```" in testo:
        testo = testo.split("```")[1].replace("json", "").strip()
    return json.loads(testo)

def formatta_messaggio(dati):
    msg = f"⚔️ ELDEN RING ⚔️\n\nGenere: {dati.get('genere')}\n"
    for s in dati.get("sezioni", []):
        msg += f"\n--- {s['nome']} ---\n"
        for p in s.get("parametri", []):
            msg += f"{p['nome']}: {p['valore']}\n"
    return msg

@bot.message_handler(commands=["start"])
def start(message):
    bot.reply_to(message, "⚔️ Bot Online! Mandami una foto.")

@bot.message_handler(content_types=["photo"])
def handle_photo(message):
    attesa = bot.reply_to(message, "⏳ Analisi universale in corso...")
    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        image_bytes = bot.download_file(file_info.file_path)
        
        dati = chiedi_gemini(image_bytes)
        bot.reply_to(message, formatta_messaggio(dati))
    except Exception as e:
        # Se fallisce ancora, stampiamo l'errore per capire se è ancora il 404
        bot.reply_to(message, f"❌ Errore: {str(e)}")
    finally:
        try: bot.delete_message(message.chat.id, attesa.message_id)
        except: pass

if __name__ == "__main__":
    bot.infinity_polling()
