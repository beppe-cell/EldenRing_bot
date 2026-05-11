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

# MODELLO CORRETTO
model = genai.GenerativeModel(
    "models/gemini-1.5-flash-latest"
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

    # pulizia markdown eventuale
    testo = (
        testo
        .replace("```json", "")
        .replace("```", "")
        .strip()
    )

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

            valore = int(parametro["valore"])

            if valore < 0:
                valore = 0

            if valore > 8:
                valore = 8

            barra = barre[valore]

            msg += (
                f"{parametro['nome']}: "
                f"{valore} [{barra}]\n"
            )

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
        "- No filtri\n"
        "- Volto ben visibile\n\n"
        "🎮 Riceverai gli slider per ricreare il personaggio!"
    )

    bot.reply_to(message, testo)

# =========================
# FOTO
# =========================

@bot.message_handler(content_types=["photo"])
def ricevi_foto(message):

    attesa = bot.reply_to(
        message,
        "⏳ Analisi del volto in corso..."
    )

    try:

        # prende foto migliore
        file_info = bot.get_file(
            message.photo[-1].file_id
        )

        image_bytes = bot.download_file(
            file_info.file_path
        )

        dati = chiedi_gemini(image_bytes)

        risultato = formatta(dati)

        # telegram limite 4096 caratteri
        for i in range(0, len(risultato), 4096):

            bot.reply_to(
                message,
                risultato[i:i + 4096]
            )

        bot.reply_to(
            message,
            "✅ Analisi completata! ⚔️"
        )

    except Exception as e:

        bot.reply_to(
            message,
            f"❌ Errore:\n{str(e)}"
        )

    finally:

        try:
            bot.delete_message(
                message.chat.id,
                attesa.message_id
            )
        except:
            pass

# =========================
# TESTO
# =========================

@bot.message_handler(func=lambda m: True)
def testo(message):

    bot.reply_to(
        message,
        "📸 Inviami una FOTO del volto!"
    )

# =========================
# START BOT
# =========================

print("🚀 Bot avviato!")

bot.infinity_polling()
