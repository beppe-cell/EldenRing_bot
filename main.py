import os
import json
import telebot
import google.generativeai as genai
from google.generativeai import caching
import datetime

# =========================
# FORZATURA API STABILE
# =========================
# Questa variabile d'ambiente dice all'SDK di ignorare v1beta
os.environ["GOOGLE_API_USE_G2_FALLBACK"] = "True"

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

bot = telebot.TeleBot(TELEGRAM_TOKEN)

# Configurazione con forzatura esplicita
genai.configure(api_key=GEMINI_API_KEY)

# Usiamo gemini-1.5-flash-8b se il flash normale dà 404 (è un trucco comune)
# Ma proviamo prima con quello standard
model = genai.GenerativeModel('gemini-1.5-flash')

PROMPT = "Sei un esperto di Elden Ring. Analizza il volto e restituisci i parametri slider in formato JSON (genere, sezioni, colori, note). Solo JSON, no markdown."

def chiedi_gemini(image_bytes):
    # Passiamo i dati in modo ultra-strutturato
    response = model.generate_content(
        contents=[
            PROMPT,
            {'mime_type': 'image/jpeg', 'data': image_bytes}
        ]
    )
    
    testo = response.text.strip()
    if "```" in testo:
        testo = testo.split("```")[1].replace("json", "").strip()
    return json.loads(testo)

@bot.message_handler(commands=["start"])
def start(message):
    bot.reply_to(message, "⚔️ Bot Online! Mandami una foto del volto per Elden Ring.")

@bot.message_handler(content_types=["photo"])
def handle_photo(message):
    attesa = bot.reply_to(message, "⏳ Analisi in corso...")
    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        image_bytes = bot.download_file(file_info.file_path)
        
        dati = chiedi_gemini(image_bytes)
        
        # Formattazione semplice per testare se risponde
        risposta = f"⚔️ RISULTATO ⚔️\n\nGenere: {dati.get('genere')}\n"
        for s in dati.get('sezioni', []):
            risposta += f"\n-- {s['nome']} --\n"
            for p in s.get('parametri', []):
                risposta += f"{p['nome']}: {p['valore']}\n"
        
        bot.reply_to(message, risposta)
        
    except Exception as e:
        # Se ricevi ancora 404, proveremo a cambiare modello qui sotto
        error_msg = str(e)
        if "404" in error_msg:
            bot.reply_to(message, "❌ Il server Google rifiuta ancora il modello Flash. Sto provando un modello alternativo...")
            try:
                # Prova di emergenza con Gemini 1.0 Pro o Flash-8b
                alt_model = genai.GenerativeModel('gemini-1.5-flash-8b')
                res = alt_model.generate_content([PROMPT, {'mime_type': 'image/jpeg', 'data': image_bytes}])
                bot.reply_to(message, f"✅ (Emergenza) Risultato:\n{res.text[:500]}")
            except Exception as e2:
                bot.reply_to(message, f"❌ Fallimento totale: {str(e2)}")
        else:
            bot.reply_to(message, f"❌ Errore: {error_msg}")
    finally:
        try: bot.delete_message(message.chat.id, attesa.message_id)
        except: pass

if __name__ == "__main__":
    bot.infinity_polling()
