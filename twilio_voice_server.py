#!/usr/bin/env python3
import os
import logging
import re
import uuid
import random
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
ELEVEN_VOICE_ID = os.getenv("ELEVEN_VOICE_ID")
ELEVEN_VOICE_ID2 = os.getenv("ELEVEN_VOICE_ID2")
RASA_URL = os.getenv("RASA_URL", "http://localhost:5005/webhooks/rest/webhook")
BASE_URL = os.getenv("BASE_URL", "https://df4a6fec2ac0.ngrok-free.app")  # ngrok pública (sin espacio al final)

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
        logger.error(f"Error conectando a la base de datos: {e}")
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
                logger.info(f"Cliente encontrado: {customer['nombre_completo']} ({customer['telefono']})")
            return customer
    except Exception as e:
        logger.error(f"Error consultando DB: {e}")
        return None
    finally:
        if conn:
            conn.close()

# -------------------------------
# ElevenLabs TTS
# -------------------------------
def seleccionar_voz_para_sesion(call_sid):
    """
    Selecciona aleatoriamente una voz para la sesión si no existe.
    Mantiene la misma voz durante toda la conversación.
    """
    if call_sid not in voice_assignment_cache:
        # Verificar que ambas voces estén configuradas
        voces_disponibles = []
        if ELEVEN_VOICE_ID:
            voces_disponibles.append((ELEVEN_VOICE_ID, "femenina"))
        if ELEVEN_VOICE_ID2:
            voces_disponibles.append((ELEVEN_VOICE_ID2, "masculina"))
        
        if not voces_disponibles:
            logger.error("No hay voces configuradas")
            return None, None
        
        # Seleccionar aleatoriamente
        voice_id, voice_type = random.choice(voces_disponibles)
        voice_assignment_cache[call_sid] = (voice_id, voice_type)
        logger.info(f"Voz asignada para {call_sid}: {voice_type} ({voice_id[:8]}...)")
    
    return voice_assignment_cache[call_sid]

def texto_a_voz(texto, filename, call_sid, velocidad="1.0"):
    """
    Convierte texto a voz usando ElevenLabs.
    Usa la voz asignada para esta sesión (call_sid).
    """
    # Obtener voz asignada para esta sesión
    voice_info = seleccionar_voz_para_sesion(call_sid)
    if not voice_info:
        logger.error("No se pudo obtener voz para la sesión")
        return None
    
    voice_id, voice_type = voice_info
    
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "xi-api-key": ELEVEN_API_KEY,
        "Accept": "audio/mpeg",
        "Content-Type": "application/json"
    }
    ssml_texto = f"<speak><prosody rate='{velocidad}'>{texto}</prosody></speak>"
    data = {"text": ssml_texto, "model_id": "eleven_multilingual_v2",
            "voice_settings":{"stability":0.5,"similarity_boost":0.95}}
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
        if "audio" not in response.headers.get("Content-Type", ""):
            logger.error("Error ElevenLabs: %s", response.text)
            return None
        
        output_file = os.path.join(AUDIO_FOLDER, f"{filename}.mp3")
        with open(output_file, "wb") as f:
            f.write(response.content)
        
        file_size = os.path.getsize(output_file)
        logger.info(f"Audio generado ({voice_type}): {output_file} ({file_size} bytes)")
        return f"/audio/{filename}.mp3"
    except Exception as e:
        logger.error(f"Error generando audio: {e}")
        return None

def responder_con_tts_twiml(container, texto, call_sid, tag="msg"):
    """
    Genera y reproduce audio usando la voz asignada para esta sesión.
    """
    filename = f"{call_sid}_{tag}_{abs(hash(texto))}"
    mp3_url = texto_a_voz(texto, filename, call_sid)
    if mp3_url:
        full_url = f"{BASE_URL}{mp3_url}"
        logger.info(f"Reproduciendo audio: {full_url}")
        container.play(full_url)
    else:
        logger.error(f"Error generando audio, usando fallback")
        # Fallback a <Say> de Twilio si falla ElevenLabs
        container.say(texto, language="es-MX", voice="Polly.Mia")

# -------------------------------
# Cache 
# -------------------------------
phone_cache = {}  # call_sid -> phone
rut_attempts_cache = {}  # call_sid -> número de intentos
rut_max_attempts = 3
autorizacion_cache = {}
session_metadata_cache = {}  # call_sid -> dict con metadata para Rasa
voice_assignment_cache = {}  # call_sid -> voice_id asignado (para consistencia en la conversación)
# -------------------------------
# Rutas Flask
# -------------------------------
def delegar_a_rasa(session_id, user_message):
    metadata = session_metadata_cache.get(session_id, {})
    # Formato correcto para Rasa REST webhook
    payload = {
        "sender": session_id, 
        "message": user_message,
        "metadata": metadata
    }
    try:
        logger.info(f"Enviando a Rasa: sender={session_id}, message='{user_message}', metadata={metadata}")
        r = requests.post(RASA_URL, json=payload)
        r.raise_for_status()
        return r.json()  # lista de mensajes [{"recipient_id":..., "text":...}, ...]
    except Exception as e:
        logger.error(f"Error al comunicar con Rasa: {e}")
        return []

def verificar_rut_en_bd(rut: str):
    """
    Verifica si el RUT existe en la base de datos.
    Retorna el registro del cliente si existe, None si no.
    """
    try:
        conn = get_database_connection()
        if not conn:
            return None
        with conn.cursor() as cursor:
            sql = "SELECT * FROM customers WHERE rut = %s LIMIT 1"
            cursor.execute(sql, (rut,))
            cliente = cursor.fetchone()
            if cliente:
                logger.info(f"Cliente encontrado en BD con RUT {rut}")
            else:
                logger.warning(f"RUT {rut} no encontrado en BD")
            return cliente
    except Exception as e:
        logger.error(f"Error al verificar RUT en BD: {e}")
        return None
    finally:
        if conn:
            conn.close()

@app.route("/audio/<filename>")
def serve_audio(filename):
    """Sirve archivos de audio generados para Twilio"""
    logger.info(f"Solicitud de audio: /audio/{filename}")
    audio_path = os.path.join(AUDIO_FOLDER, filename)
    
    if not os.path.exists(audio_path):
        logger.error(f"Archivo no encontrado: {audio_path}")
        return "Audio file not found", 404
    
    file_size = os.path.getsize(audio_path)
    logger.info(f"Sirviendo audio: {audio_path} ({file_size} bytes)")
    return send_from_directory(AUDIO_FOLDER, filename, mimetype="audio/mpeg")

@app.route("/webhook/twilio/voice", methods=["POST"])
def incoming_call():
    call_sid = request.form.get("CallSid")
    from_number = request.form.get("From")
    phone_cache[call_sid] = from_number
    logger.info(f"Llamada entrante {call_sid} de {from_number}")

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

    # Inicializar metadata de sesión para Rasa (se complementará tras validar RUT)
    session_metadata_cache[call_sid] = {
        "customer_phone": customer.get("telefono"),
        "customer_first_name": customer.get("nombre"),
        "customer_full_name": customer.get("nombre_completo"),
        # customer_id lo fijamos tras validar RUT para asegurar consistencia
    }

    gather = Gather(input="dtmf", num_digits=8, timeout=10,
                    action=f"/webhook/twilio/collect_rut?call_sid={call_sid}")
    response.append(gather)

    return Response(str(response), mimetype="text/xml")

@app.route("/webhook/twilio/collect_rut", methods=["POST"])
def collect_rut():
    call_sid = request.args.get("call_sid")
    rut = request.form.get("Digits", "")
    phone = phone_cache.get(call_sid)
    customer = get_customer_by_phone(phone)
    response = VoiceResponse()

    # Inicializar contador de intentos
    if call_sid not in rut_attempts_cache:
        rut_attempts_cache[call_sid] = 0

    # Validar RUT en DB
    if not re.fullmatch(r"\d{7,8}", rut) or (customer and str(customer.get("rut")) != rut):
        rut_attempts_cache[call_sid] += 1
        if rut_attempts_cache[call_sid] >= rut_max_attempts:
            responder_con_tts_twiml(response,
                "Número máximo de intentos alcanzado. La llamada será finalizada.",
                call_sid, "rut_failed")
            response.hangup()
            return Response(str(response), mimetype="text/xml")
        else:
            responder_con_tts_twiml(response,
                f"RUT inválido. Intento {rut_attempts_cache[call_sid]} de {rut_max_attempts}. Por favor, ingréselo nuevamente.",
                call_sid, "rut_retry")
            gather = Gather(input="dtmf", num_digits=8, timeout=10,
                            action=f"/webhook/twilio/collect_rut?call_sid={call_sid}")
            response.append(gather)
            return Response(str(response), mimetype="text/xml")

    # ✅ RUT válido
    responder_con_tts_twiml(response,
        "Estamos enviando una notificación a su app Scotiabank para confirmar su identidad. Por favor, autorice desde su dispositivo móvil.",
        call_sid, "push_auth")

    # Aquí se simula autorización push (reemplazar con IVR real)
    autorizado = True
    autorizacion_cache[call_sid] = autorizado

    if not autorizado:
        responder_con_tts_twiml(response,
            "No pudimos completar la autenticación. Será transferido a un ejecutivo.",
            call_sid, "auth_failed")
        response.hangup()
        return Response(str(response), mimetype="text/xml")

    # ✅ Autenticación exitosa
    responder_con_tts_twiml(response, "Autenticación exitosa. Ahora puede decir su solicitud.", call_sid, "auth_success")

    # Completar metadata de sesión para Rasa con el RUT validado
    if customer:
        session_metadata_cache[call_sid]["customer_id"] = customer.get("rut")
        session_metadata_cache[call_sid]["customer_phone"] = customer.get("telefono")
        session_metadata_cache[call_sid]["customer_full_name"] = customer.get("nombre_completo")
        logger.info(f"Metadata de sesión actualizada para Rasa: {session_metadata_cache[call_sid]}")

    # --- Inicio de sesión Rasa ---
    # Notificar a Rasa que la llamada está autenticada (incluye metadata)
    delegar_a_rasa(call_sid, "call_authenticated")

    # Solicitar al usuario que hable y capturar voz
    gather = Gather(
        input="speech",
        action=f"/webhook/twilio/rasa_conversation?call_sid={call_sid}",
        speech_timeout="auto",
        language="es-CL"
    )
    gather.say("")
    response.append(gather)

    return Response(str(response), mimetype="text/xml")

@app.route("/webhook/twilio/rasa_conversation", methods=["POST"])
def rasa_conversation():
    call_sid = request.args.get("call_sid")
    speech_text = request.form.get("SpeechResult", "").strip()
    dtmf_digits = request.form.get("Digits", "").strip()
    response = VoiceResponse()
    
    # Priorizar voz, pero aceptar DTMF también
    user_input = speech_text if speech_text else dtmf_digits

    logger.info(f"[INPUT] Usuario {'dijo' if speech_text else 'teclado'}: {user_input}")

    if not user_input:
        # Reintentar si no entendió
        gather = Gather(
            input="speech dtmf",
            action=f"/webhook/twilio/rasa_conversation?call_sid={call_sid}",
            speech_timeout="auto",
            language="es-CL",
            num_digits=4,
            timeout=10
        )
        gather.say("No entendí lo que dijo. Por favor, repita.")
        response.append(gather)
        return Response(str(response), mimetype="text/xml")

    # Enviar texto a Rasa
    rasa_respuestas = delegar_a_rasa(call_sid, user_input)

    if rasa_respuestas:
        for idx, msg in enumerate(rasa_respuestas):
            texto = msg.get("text")
            if texto:
                responder_con_tts_twiml(response, texto, call_sid, f"rasa_{idx}")
                # Continuar escuchando si quieres diálogo abierto
        gather = Gather(
            input="speech dtmf",
            action=f"/webhook/twilio/rasa_conversation?call_sid={call_sid}",
            speech_timeout="auto",
            language="es-CL",
            num_digits=4,
            timeout=10
        )
        #gather.say("")
        response.append(gather)
    else:
        responder_con_tts_twiml(response,
            "No recibí respuesta del asistente. Será transferido a un ejecutivo.",
            call_sid, "no_rasa")
        response.hangup()

    return Response(str(response), mimetype="text/xml")

# -------------------------------
# Main
# -------------------------------
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    
    # Mostrar configuración de voces
    print("\n" + "="*60)
    print("Servidor Twilio Voice iniciando...")
    print("="*60)
    print(f"Puerto: {port}")
    print(f"BASE_URL: {BASE_URL}")
    print(f"Base de datos: {DB_CONFIG['host']}:{DB_CONFIG.get('port', 3306)}")
    print(f"Rasa URL: {RASA_URL}")
    print("")
    print("Configuración de voces ElevenLabs:")
    
    voces_count = 0
    if ELEVEN_VOICE_ID:
        print(f"   [OK] Voz 1 (femenina): {ELEVEN_VOICE_ID[:12]}...")
        voces_count += 1
    else:
        print(f"   [ERROR] Voz 1 (femenina): NO CONFIGURADA")
    
    if ELEVEN_VOICE_ID2:
        print(f"   [OK] Voz 2 (masculina): {ELEVEN_VOICE_ID2[:12]}...")
        voces_count += 1
    else:
        print(f"   [ERROR] Voz 2 (masculina): NO CONFIGURADA")
    
    if voces_count == 2:
        print(f"\n   [INFO] Sistema con {voces_count} voces: selección aleatoria activa")
        print(f"          Cada llamada será atendida por una voz diferente (femenina o masculina)")
    elif voces_count == 1:
        print(f"\n   [WARN] Solo 1 voz configurada: todas las llamadas usarán la misma voz")
    else:
        print(f"\n   [ERROR] ERROR: No hay voces configuradas")
        print(f"           Configura ELEVEN_VOICE_ID y/o ELEVEN_VOICE_ID2 en .env")
    
    print("="*60)
    print("")
    
    app.run(host="0.0.0.0", port=port, debug=True, threaded=True)