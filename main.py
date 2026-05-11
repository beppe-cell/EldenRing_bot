import os
import json
import telebot
import google.generativeai as genai
from google.generativeai.types import RequestOptions

# =========================
# CONFIG
# =========================

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]

bot = telebot.TeleBot(TELEGRAM_TOKEN)

# Configurazione API forzando la versione stabile v1
genai.configure(api_key=GEMINI_API_KEY)

# CAMBIO MODELLO: Passiamo a 1.5-pro che è più stabile sui permessi
# Usiamo il nome corto che l'SDK risolve internamente
model = genai.GenerativeModel('gemini-1.5-pro')

# =========================
# PROMPT
# =========================

PROMPT = """
Sei un esperto di Elden Ring.
Analizza il volto nella foto e genera SOLO JSON valido.
Regole:
- Nessun testo fuori dal JSON
- Nessun markdown
- Tutti i valori slider devono essere numeri da 0 a 8
Formato:
{
  "genere":"Maschile o Femminile",
  "sezioni":[
    {
      "nome":"STRUTTURA TESTA",
      "parametri":[{"nome":"Dimensione testa","valore":4}]
    }
  ],
  "colori":{"pelle":"","occhi":"","capelli":""},
  "note":""
}
"""

# =========================
# GEMINI
# =========================

def chiedi_gemini(image_bytes):
    # Usiamo RequestOptions per forzare la versione API v1 ed evitare v1beta
    response = model.generate_content(
        contents=[
            PROMPT,
            {
                "mime_type": "image/jpeg",
                "data": image_bytes
            }
        ],
        generation_config={
            "temperature": 0.3,
            "max_output_tokens": 2000
        },
        request_options=RequestOptions(api_version='v1')
    )

    testo = response.text.strip()

    # Pulizia JSON
    if "```" in testo:
        testo = testo.split("```")[1]
        if testo.startswith("json"):
            testo = testo[4:]
    
    return json.loads(testo.strip())

# =========================
# FORMATTAZIONE & TELEGRAM
# =========================

def formatta(dati):
    barre = ["________", "*_______", "**______", "***_____", "****____", "*****___", "******__", "*******_", "********"]
    colori = dati.get("colori", {})
    msg = f"⚔️ ELDEN RING - PARAMETRI ⚔️\n\nGenere: {dati.get('genere', '?')}\n\n🎨 COLORI\nPelle: {colori.get('pelle', '?')}\nOcchi: {colori.get('occhi', '?')}\nCapelli: {colori.get('capelli', '?')}\n\n"
    for sezione in dati.get("sezioni", []):
        msg += f"--- {sezione['nome']} ---\n"
        for p in sezione.get("parametri", []):
            val = max(0, min(8, int(p["valore"])))
            msg += f"{p['nome']}: {val} [{barre[val]}]\n"
        msg += "\n"
    return msg + "0=min | 4=centro | 8=max"

@bot.message_handler(commands=["start"])
def start(message):
    bot.reply_to(message, "⚔️ Invia una foto del volto!")

@bot.message_handler(content_types=["photo"])
def ricevi_foto(message):
    attesa = bot.reply_to(message, "⏳ Analisi con Gemini 1.5 Pro...")
    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        image_bytes = bot.download_file(file_info.file_path)
        dati = chiedi_gemini(image_bytes)
        bot.reply_to(message, formatta(dati))
    except Exception as e:
        bot.reply_to(message, f"❌ Errore:\n{str(e)}")
    finally:
        bot.delete_message(message.chat.id, attesa.message_id)

if __name__ == "__main__":
    bot.infinity_polling()
