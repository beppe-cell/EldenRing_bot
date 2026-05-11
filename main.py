import os
import json
import telebot
import google.generativeai as genai

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]

bot = telebot.TeleBot(TELEGRAM_TOKEN)

genai.configure(api_key=GEMINI_API_KEY)

# MODELLO STABILE
model = genai.GenerativeModel("gemini-1.5-flash")

PROMPT = """
Sei un esperto di Elden Ring.
Analizza il viso nella foto e restituisci SOLO JSON valido.

Formato:
{
  "genere":"Maschile o Femminile",
  "sezioni":[
    {
      "nome":"OCCHI",
      "parametri":[
        {
          "nome":"Dimensione occhi",
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

    # pulizia eventuali markdown
    testo = testo.replace("```json", "").replace("```", "").strip()

    return json.loads(testo)


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

    c = dati.get("colori", {})

    msg = (
        f"⚔️ ELDEN RING - PARAMETRI ⚔️\n"
        f"Genere: {dati.get('genere','?')}\n\n"
        f"COLORI\n"
        f"  Pelle: {c.get('pelle','?')}\n"
        f"  Occhi: {c.get('occhi','?')}\n"
        f"  Capelli: {c.get('capelli','?')}\n\n"
    )

    for s in dati.get("sezioni", []):
        msg += f"--- {s['nome']} ---\n"

        for p in s.get("parametri", []):

            v = int(p["valore"])

            barra = barre[v] if 0 <= v <= 8 else "?"

            msg += f"  {p['nome']}: {v} [{barra}]\n"

        msg += "\n"

    if dati.get("note"):
        msg += f"Note: {dati['note']}\n"

    msg += "\nValore 4 = centro | 0 = min | 8 = max"

    return msg


@bot.message_handler(commands=["start", "help"])
def start(m):

    bot.reply_to(
        m,
        "⚔️ Benvenuto nel Bot Elden Ring!\n\n"
        "Inviami una foto chiara del viso.\n\n"
        "Consigli:\n"
        "- Foto frontale\n"
        "- Buona luce\n"
        "- Niente filtri\n\n"
        "Invia la foto! 🎮"
    )


@bot.message_handler(content_types=["photo"])
def foto(m):

    att = bot.reply_to(m, "⏳ Analisi in corso...")

    try:

        file_info = bot.get_file(m.photo[-1].file_id)

        image_bytes = bot.download_file(file_info.file_path)

        dati = chiedi_gemini(image_bytes)

        risultato = formatta(dati)

        for i in range(0, len(risultato), 4096):
            bot.reply_to(m, risultato[i:i+4096])

        bot.reply_to(m, "✅ Fatto! ⚔️")

    except Exception as e:

        bot.reply_to(
            m,
            f"❌ Errore:\n{str(e)}"
        )

    finally:

        try:
            bot.delete_message(m.chat.id, att.message_id)
        except:
            pass


@bot.message_handler(func=lambda m: True)
def testo(m):

    bot.reply_to(m, "📸 Inviami una FOTO!")


print("🚀 Bot avviato!")

bot.infinity_polling()
