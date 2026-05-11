import os
import json
import telebot
import google.generativeai as genai

# =========================
# CONFIG
# =========================

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]

bot = telebot.TeleBot(TELEGRAM_TOKEN)

genai.configure(api_key=GEMINI_API_KEY)

# MODIFICA QUI: Usiamo il nome del modello standard senza "-latest"
# Questo risolve l'errore 404 che ricevevi
model = genai.GenerativeModel(
    "gemini-1.5-flash"
)

# =========================
# PROMPT
# =========================

PROMPT = """
Sei un esperto di Elden Ring.
Analizza il volto nella foto e genera SOLO JSON valido.

Regole:
- Nessun testo fuori dal JSON
- Nessun markdown
- Nessun ```json
- Tutti i valori slider devono essere numeri da 0 a 8

Formato:
{
  "genere":"Maschile o Femminile",
  "sezioni":[
    {
      "nome":"STRUTTURA TESTA",
      "parametri":[
        {
          "nome":"Dimensione testa",
          "valore":4
        }
      ]
    }
  ],
  "colori":{
    "pelle":"",
    "occhi":"",
    "capelli":""
  },
  "note":""
}
"""

# =========================
# GEMINI
# =========================

def chiedi_gemini(image_bytes):
    # Passiamo l'immagine nel formato corretto per l'SDK
    response = model.generate_content(
        [
            PROMPT,
            {
                "mime_type": "image/jpeg",
                "data": image_bytes
            }
        ],
        generation_config={
            "temperature": 0.3,
            "max_output_tokens": 2000
        }
    )

    testo = response.text.strip()

    # Pulizia forzata del markdown se Gemini lo include per errore
    if testo.startswith("```"):
        testo = testo.split("```")[1]
        if testo.startswith("json"):
            testo = testo[4:]
    
    testo = testo.strip()

    return json.loads(testo)

# =========================
# FORMATTAZIONE
# =========================

def formatta(dati):
    barre = [
        "________",
        "*_______",
        "**______",
        "***_____",
        "****____",
        "*****___",
        "******__",
        "*******_",
        "********"
    ]

    colori = dati.get("colori", {})

    msg = (
        "⚔️ ELDEN RING - PARAMETRI ⚔️\n\n"
        f"Genere: {dati.get('genere', '?')}\n\n"
        "🎨 COLORI\n"
        f"Pelle: {colori.get('pelle', '?')}\n"
        f"Occhi: {colori.get('occhi', '?')}\n"
        f"Capelli: {colori.get('capelli', '?')}\n\n"
    )

    for sezione in dati.get("sezioni", []):
        msg += f"--- {sezione['nome']} ---\n"
        for parametro in sezione.get("parametri", []):
            try:
                valore = int(parametro["valore"])
                valore = max(0, min(8, valore)) # Limita tra 0 e 8
                barra = barre[valore]
                msg += f"{parametro['nome']}: {valore} [{barra}]\n"
            except:
                continue
        msg += "\n"

    if dati.get("note"):
        msg += f"📝 Note: {dati['note']}\n\n"

    msg += "0=min | 4=centro | 8=max"
    return msg

# =========================
# COMANDI
# =========================

@bot.message_handler(commands=["start", "help"])
def start(message):
    testo = (
        "⚔️ Benvenuto nel Bot Elden Ring!\n\n"
        "📸 Inviami una foto chiara del volto.\n\n"
        "Consigli:\n"
        "- Foto frontale\n"
        "- Buona illuminazione\n"
        "- Volto ben visibile\n\n"
        "🎮 Riceverai gli slider per ricreare il personaggio!"
    )
    bot.reply_to(message, testo)

# =========================
# FOTO
# =========================

@bot.message_handler(content_types=["photo"])
def ricevi_foto(message):
    attesa = bot.reply_to(message, "⏳ Analisi del volto in corso...")

    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        image_bytes = bot.download_file(file_info.file_path)

        dati = chiedi_gemini(image_bytes)
        risultato = formatta(dati)

        # Gestione limite caratteri Telegram
        if len(risultato) > 4096:
            for i in range(0, len(risultato), 4096):
                bot.send_message(message.chat.id, risultato[i:i + 4096])
        else:
            bot.reply_to(message, risultato)

        bot.send_message(message.chat.id, "✅ Analisi completata! ⚔️")

    except Exception as e:
        bot.reply_to(message, f"❌ Errore:\n{str(e)}")
    finally:
        try:
            bot.delete_message(message.chat.id, attesa.message_id)
        except:
            pass

# =========================
# TESTO
# =========================

@bot.message_handler(func=lambda m: True)
def testo(message):
    bot.reply_to(message, "📸 Inviami una FOTO del volto!")

# =========================
# START BOT
# =========================

if __name__ == "__main__":
    print("🚀 Bot avviato!")
    bot.infinity_polling()
