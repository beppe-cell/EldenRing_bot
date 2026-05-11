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

# Usiamo gemini-1.5-flash ma senza 'models/' davanti se non funziona
# Molti SDK vecchi preferiscono solo il nome
model = genai.GenerativeModel('gemini-1.5-flash')

def chiedi_gemini(image_bytes):
    # Metodo ultra-compatibile
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
        }
    )

    testo = response.text.strip()
    # Pulizia manuale veloce
    if "```" in testo:
        testo = testo.split("```")[1].replace("json", "")
    
    return json.loads(testo.strip())
