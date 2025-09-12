#!/usr/bin/env python3
import os
import logging
import re
import uuid
from datetime import datetime
from flask import Flask, request, Response, send_from_directory
from twilio.twiml.voice_response import VoiceResponse, Gather
import requests
import pymysql
from dotenv import load_dotenv

# -------------------------------
# Configuración
# -------------------------------
load_dotenv()

ELEVEN_API_KEY = os.getenv("ELEVEN_API_KEY")
ELEVEN_VOICE_ID = os.getenv("ELEVEN_VOICE_ID", "iNlaSRLu8vd4RtnF3w9i")
RASA_URL = os.getenv("RASA_URL", "http://localhost:5005/webhooks/rest/webhook")
BASE_URL = os.getenv("BASE_URL", "https://1c683bbcb8f9.ngrok-free.app")  # ngrok pública

# Carpeta para audios
AUDIO_FOLDER = os.path.join(os.getcwd(), "audio")
os.makedirs(AUDIO_FOLDER, exist_ok=True)

# Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask app
app = Flask(__name__)

# -------------------------------
# Base de datos
# -------------------------------
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'nico'),
    'password': os.getenv('DB_PASSWORD', 'nico'),
    'database': os.getenv('DB_NAME', 'bank'),
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

def get_database_connection():
    try:
        return pymysql.connect(**DB_CONFIG)
    except Exception as e:
        logger.error(f"❌ Error conectando a la base de datos: {e}")
        return None

def get_customer_by_phone(phone_number: str):
    raw_phone = (phone_number or '').strip()
    digits_only = re.sub(r"\D", "", raw_phone)
    candidates = [raw_phone, digits_only, f"+{digits_only}"]
    seen = set()
    norm_candidates = []
    for c in candidates:
        if c and c not in seen:
            seen.add(c)
            norm_candidates.append(c)
    try:
        conn = get_database_connection()
        if not conn:
            return None
        with conn.cursor() as cursor:
            conditions = " OR ".join(["telefono=%s" for _ in norm_candidates])
            sql = f"SELECT * FROM customers WHERE {conditions} LIMIT 1"
            cursor.execute(sql, tuple(norm_candidates))
            customer = cursor.fetchone()
            if customer:
                logger.info(f"👤 Cliente encontrado: {customer['nombre_completo']} ({customer['telefono']})")
            return customer
    except Exception as e:
        logger.error(f"❌ Error consultando DB: {e}")
        return None
    finally:
        if conn:
            conn.close()

# -------------------------------
# ElevenLabs TTS
# -------------------------------
def texto_a_voz(texto, filename, velocidad="x-fast"):
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVEN_VOICE_ID}"
    headers = {
        "xi-api-key": ELEVEN_API_KEY,
        "Accept": "audio/mpeg",
        "Content-Type": "application/json"
    }
    ssml_texto = f"<speak><prosody rate='{velocidad}'>{texto}</prosody></speak>"
    data = {"text": ssml_texto, "model_id": "eleven_multilingual_v2",
            "voice_settings":{"stability":0.8,"similarity_boost":0.95}}
    response = requests.post(url, headers=headers, json=data)
    if "audio" not in response.headers.get("Content-Type", ""):
        logger.error("❌ Error ElevenLabs: %s", response.text)
        return None
    output_file = os.path.join(AUDIO_FOLDER, f"{filename}.mp3")
    with open(output_file, "wb") as f:
        f.write(response.content)
    logger.info(f"✅ Audio generado: {output_file}")
    return f"/audio/{filename}.mp3"

def responder_con_tts_twiml(container, texto, call_sid, tag="msg"):
    filename = f"{call_sid}_{tag}_{abs(hash(texto))}"
    mp3_url = texto_a_voz(texto, filename)
    if mp3_url:
        container.play(f"{BASE_URL}{mp3_url}")

# -------------------------------
# Cache de llamadas
# -------------------------------
phone_cache = {}  # call_sid -> phone

# -------------------------------
# Rutas Flask
# -------------------------------
@app.route("/audio/<filename>")
def serve_audio(filename):
    return send_from_directory(AUDIO_FOLDER, filename)

@app.route("/webhook/twilio/voice", methods=["POST"])
def incoming_call():
    call_sid = request.form.get("CallSid")
    from_number = request.form.get("From")
    phone_cache[call_sid] = from_number
    logger.info(f"📞 Llamada entrante {call_sid} de {from_number}")

    customer = get_customer_by_phone(from_number)
    response = VoiceResponse()

    if not customer:
        responder_con_tts_twiml(response,
            "Lo siento, tu número no está registrado. La llamada será finalizada.",
            call_sid, "unknown")
        response.hangup()
        return Response(str(response), mimetype="text/xml")

    # Saludo y pedir RUT
    saludo = f"¡Hola {customer['nombre']}! Soy el asistente de Scotiabank. Por favor, ingresa tu RUT sin puntos ni guion."
    responder_con_tts_twiml(response, saludo, call_sid, "greeting")

    gather = Gather(input="dtmf", num_digits=8, timeout=10,
                    action=f"/webhook/twilio/collect_rut?call_sid={call_sid}")
    #responder_con_tts_twiml(gather, "Ingrese su RUT.", call_sid, "ask_rut")
    response.append(gather)

    return Response(str(response), mimetype="text/xml")

@app.route("/webhook/twilio/collect_rut", methods=["POST"])
def collect_rut():
    call_sid = request.args.get("call_sid")
    rut = request.form.get("Digits", "")
    phone = phone_cache.get(call_sid)
    customer = get_customer_by_phone(phone)
    logger.info(f"🆔 RUT recibido: {rut} de {phone}")

    response = VoiceResponse()
    if not re.fullmatch(r"\d{7,8}", rut):
        responder_con_tts_twiml(response, "RUT inválido. La llamada será finalizada.", call_sid, "invalid_rut")
        response.hangup()
        return Response(str(response), mimetype="text/xml")

    payload = {"sender": call_sid, "message": f"RUT:{rut}"}
    requests.post(RASA_URL, json=payload)

    responder_con_tts_twiml(response, "RUT recibido. Presione 2 para bloqueo de tarjeta.", call_sid, "menu")
    gather = Gather(input="dtmf", num_digits=1, timeout=10,
                    action=f"/webhook/twilio/menu?call_sid={call_sid}")
    response.append(gather)
    return Response(str(response), mimetype="text/xml")

@app.route("/webhook/twilio/menu", methods=["POST"])
def menu():
    call_sid = request.args.get("call_sid")
    option = request.form.get("Digits")
    response = VoiceResponse()
    logger.info(f"📋 Menú seleccionado: {option}")

    if option == "2":
        gather = Gather(input="dtmf", num_digits=4, timeout=10,
                        action=f"/webhook/twilio/card?call_sid={call_sid}")
        responder_con_tts_twiml(gather, "Ha seleccionado bloqueo de tarjeta. Ingrese los últimos 4 dígitos de su tarjeta.", call_sid, "ask_card")
        response.append(gather)
    else:
        responder_con_tts_twiml(response, "Opción no válida. Gracias por llamar a Scotiabank.", call_sid, "invalid")
        response.hangup()

    return Response(str(response), mimetype="text/xml")

@app.route("/webhook/twilio/card", methods=["POST"])
def card():
    call_sid = request.args.get("call_sid")
    digits = request.form.get("Digits")
    logger.info(f"💳 Tarjeta ingresada: {digits}")

    payload = {"sender": call_sid, "message": f"TARJETA:{digits}"}
    requests.post(RASA_URL, json=payload)

    response = VoiceResponse()
    gather = Gather(input="dtmf", num_digits=1, timeout=10,
                    action=f"/webhook/twilio/confirm_block?call_sid={call_sid}&card={digits}")
    responder_con_tts_twiml(gather, f"Está a punto de bloquear su tarjeta terminada en {digits}. Presione 1 para confirmar o 2 para cancelar.", call_sid, "confirm")
    response.append(gather)
    return Response(str(response), mimetype="text/xml")

@app.route("/webhook/twilio/confirm_block", methods=["POST"])
def confirm_block():
    call_sid = request.args.get("call_sid")
    card = request.args.get("card")
    option = request.form.get("Digits")

    response = VoiceResponse()
    if option == "1":
        payload = {"sender": call_sid, "message": f"BLOQUEAR:{card}"}
        requests.post(RASA_URL, json=payload)
        responder_con_tts_twiml(response, f"Su tarjeta terminada en {card} ha sido bloqueada exitosamente. Gracias por preferir Scotiabank.", call_sid, "blocked")
    else:
        responder_con_tts_twiml(response, "Operación cancelada. Gracias por comunicarse con Scotiabank.", call_sid, "cancel")

    response.hangup()
    return Response(str(response), mimetype="text/xml")

# -------------------------------
# Main
# -------------------------------
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True, threaded=True)
