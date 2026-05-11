import os, json, base64, requests, telebot

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
bot = telebot.TeleBot(TELEGRAM_TOKEN)

PROMPT = """Sei un esperto di Elden Ring. Analizza il viso nella foto e restituisci i valori degli slider per replicare questa persona nell'editor del personaggio di Elden Ring. Rispondi SOLO con questo JSON, senza testo aggiuntivo, senza backtick: {"genere":"Maschile o Femminile","sezioni":[{"nome":"STRUTTURA TESTA","parametri":[{"nome":"Dimensione testa","valore":4},{"nome":"Altezza testa","valore":4},{"nome":"Larghezza testa","valore":4},{"nome":"Profondita testa","valore":4}]},{"nome":"OCCHI","parametri":[{"nome":"Posizione verticale occhi","valore":4},{"nome":"Distanza tra gli occhi","valore":4},{"nome":"Inclinazione occhi","valore":4},{"nome":"Dimensione occhi","valore":4},{"nome":"Profondita occhi","valore":4},{"nome":"Angolo occhi interno","valore":4},{"nome":"Angolo occhi esterno","valore":4}]},{"nome":"NASO","parametri":[{"nome":"Posizione verticale naso","valore":4},{"nome":"Dimensione naso","valore":4},{"nome":"Lunghezza naso","valore":4},{"nome":"Altezza punta naso","valore":4},{"nome":"Dimensione punta naso","valore":4},{"nome":"Larghezza narici","valore":4},{"nome":"Inclinazione narici","valore":4}]},{"nome":"BOCCA E LABBRA","parametri":[{"nome":"Posizione verticale bocca","valore":4},{"nome":"Larghezza bocca","valore":4},{"nome":"Spessore labbro superiore","valore":4},{"nome":"Spessore labbro inferiore","valore":4},{"nome":"Profondita labbra","valore":4},{"nome":"Inclinazione bocca","valore":4}]},{"nome":"GUANCE E MENTO","parametri":[{"nome":"Altezza zigomi","valore":4},{"nome":"Sporgenza zigomi","valore":4},{"nome":"Larghezza guance","valore":4},{"nome":"Altezza mento","valore":4},{"nome":"Larghezza mento","valore":4},{"nome":"Profondita mento","valore":4},{"nome":"Forma mascella","valore":4},{"nome":"Larghezza mascella","valore":4}]},{"nome":"FRONTE E ORECCHIE","parametri":[{"nome":"Altezza fronte","valore":4},{"nome":"Profondita fronte","valore":4},{"nome":"Dimensione orecchie","valore":4},{"nome":"Angolo orecchie","valore":4}]},{"nome":"INCARNATO","parametri":[{"nome":"Tono pelle","valore":4},{"nome":"Luminosita pelle","valore":4},{"nome":"Saturazione pelle","valore":4}]},{"nome":"SOPRACCIGLIA","parametri":[{"nome":"Spessore sopracciglia","valore":4},{"nome":"Forma sopracciglia","valore":4},{"nome":"Inclinazione sopracciglia","valore":4},{"nome":"Posizione verticale sopracciglia","valore":4}]}],"colori":{"pelle":"","occhi":"","capelli":""},"note":""}"""

def chiedi_gemini(image_bytes):
    b64 = base64.b64encode(image_bytes).decode("utf-8")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
    r = requests.post(url, json={"contents":[{"parts":[{"inlineData":{"mimeType":"image/jpeg","data":b64}},{"text":PROMPT}]}],"generationConfig":{"temperature":0.3,"maxOutputTokens":2000}}, timeout=60)
    r.raise_for_status()
    testo = r.json()["candidates"][0]["content"]["parts"][0]["text"]
    return json.loads(testo.replace("```json","").replace("```","").strip())

def formatta(dati):
    barre=["________","*_______","**______","***_____","****____","*****___","******__","*******_","********"]
    c=dati.get("colori",{})
    msg=f"⚔️ ELDEN RING - PARAMETRI ⚔️\nGenere: {dati.get('genere','?')}\n\nCOLORI\n  Pelle: {c.get('pelle','?')}\n  Occhi: {c.get('occhi','?')}\n  Capelli: {c.get('capelli','?')}\n\n"
    for s in dati.get("sezioni",[]):
        msg+=f"--- {s['nome']} ---\n"
        for p in s.get("parametri",[]):
            v=p["valore"]; msg+=f"  {p['nome']}: {v} [{barre[v] if 0<=v<=8 else '?'}]\n"
        msg+="\n"
    if dati.get("note"): msg+=f"Note: {dati['note']}\n"
    return msg+"Valore 4=centro | 0=min | 8=max"

@bot.message_handler(commands=["start","help"])
def start(m):
    bot.reply_to(m,"⚔️ Benvenuto nel Bot Elden Ring!\n\nInviami una foto chiara del viso e ti darò tutti i valori degli slider per replicarla nel gioco.\n\nConsigli:\n- Foto frontale\n- Buona luce\n- Niente filtri\n\nInvia la foto! 🎮")

@bot.message_handler(content_types=["photo"])
def foto(m):
    att=bot.reply_to(m,"⏳ Analisi in corso (~20 sec)...")
    try:
        fi=bot.get_file(m.photo[-1].file_id); fb=bot.download_file(fi.file_path)
        ris=formatta(chiedi_gemini(fb))
        for i in range(0,len(ris),4096): bot.reply_to(m,ris[i:i+4096])
        bot.reply_to(m,"✅ Fatto! Buona fortuna! ⚔️")
    except Exception as e:
        bot.reply_to(m,f"❌ Errore: {e}\nRiprova!")
    finally:
        try: bot.delete_message(m.chat.id,att.message_id)
        except: pass

@bot.message_handler(func=lambda m:True)
def testo(m): bot.reply_to(m,"📸 Inviami una FOTO, non testo!")

print("🚀 Bot avviato!")
bot.infinity_polling()
