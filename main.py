import os
import json
import telebot
import google.generativeai as genai
from google.generativeai.types import RequestOptions

# =========================
# CONFIGURAZIONE AMBIENTE
# =========================

# Recupero variabili da Railway
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Inizializzazione Bot
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# Configurazione Google AI
genai.configure(api_key=GEMINI_API_KEY)

# Creazione modello (usiamo 1.5-flash)
model = genai.GenerativeModel('gemini-1.5-flash')

# =========================
# PROMPT DI ELDEN RING
# =========================

PROMPT_CONFIG = """
Sei un esperto di Elden Ring. Analizza il volto nella foto e genera SOLO un JSON valido.
Regole:
- Nessun testo fuori dal JSON.
- Nessun markdown (niente ```json).
- Tutti i valori slider devono essere numeri interi da 0 a 8.

Formato richiesto:
{
  "genere": "Maschile o Femminile",
  "sezioni": [
    {
      "nome": "STRUTTURA TESTA",
      "parametri": [{"nome": "Dimensione testa", "valore": 4}]
    }
  ],
  "colori": {"pelle": "", "occhi": "", "capelli": ""},
  "note": ""
}
"""

# =========================
# LOGICA DI ANALISI
# =========================

def chiedi_gemini(image_bytes):
    # La chiave qui è RequestOptions(api_version='v1') per saltare la v1beta
    response = model.generate_content(
        contents=[
            PROMPT_CONFIG,
            {"mime_type": "image/jpeg", "data": image_bytes}
        ],
        generation_config={
            "temperature": 0.3,
            "max_output_tokens": 2000
        },
        request_options=RequestOptions(api_version='v1')
    )

    testo = response.text.strip()

    # Pulizia manuale se il modello ignora le istruzioni e mette markdown
    if "```" in testo:
        testo = testo.split("```")[1]
        if testo.startswith("json"):
            testo = testo[4:]
    
    return json.loads(testo.strip())

def formatta_messaggio(dati):
    barre = ["________", "*_______", "**______", "***_____", "****____", "*****___", "******__", "*******_", "********"]
    
    colori = dati.get("colori", {})
    msg = (
        "⚔️ **ELDEN RING - PARAMETRI** ⚔️\n\n"
        f"👤 Genere: {dati.get('genere', '?')}\n\n"
        "🎨 **COLORI**\n"
        f"• Pelle: {colori.get('pelle', '?')}\n"
        f"• Occhi: {colori.get('occhi', '?')}\n"
        f"• Capelli: {colori.get('capelli', '?')}\n\n"
    )

    for sezione in dati.get("sezioni", []):
        msg += f"--- {sezione['nome']} ---\n"
        for p in sezione.get("parametri", []):
            try:
                val = max(0, min(8, int(p["valore"])))
                msg += f"{p['nome']}: {val} [{barre[val]}]\n"
            except: continue
        msg += "\n"

    if dati.get("note"):
        msg += f"📝 *Note: {dati['note']}*\n\n"
    
    msg += "0=min | 4=centro | 8=max"
    return msg

# =========================
# GESTIONE TELEGRAM
# =========================

@bot.message_handler(commands=["start", "help"])
def send_welcome(message):
    bot.reply_to(message, "⚔️ **Elden Ring Look Bot** ⚔️\n\nInviami una foto del volto e ti darò gli slider per ricrearlo nel gioco!")

@bot.message_handler(content_types=["photo"])
def handle_photo(message):
    attesa = bot.reply_to(message, "⏳ Analisi del volto in corso (API v1)...")
    
    try:
        # Scarica la foto
        file_info = bot.get_file(message.photo[-1].file_id)
        image_bytes = bot.download_file(file_info.file_path)

        # Analisi Gemini
        dati_json = chiedi_gemini(image_bytes)
        
        # Formattazione e invio
        risposta_finale = formatta_messaggio(dati_json)
        bot.reply_to(message, risposta_finale, parse_mode="Markdown")

    except Exception as e:
        bot.reply_to(message, f"❌ Errore durante l'analisi:\n`{str(e)}`", parse_mode="Markdown")
    
    finally:
        try:
            bot.delete_message(message.chat.id, attesa.message_id)
        except: pass

# =========================
# AVVIO
# =========================

if __name__ == "__main__":
    print("🚀 Bot avviato con API v1!")
    bot.infinity_polling()
