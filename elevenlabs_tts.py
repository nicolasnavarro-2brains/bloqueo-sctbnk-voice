import os
import requests
import logging

from dotenv import load_dotenv
load_dotenv()

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Variables de entorno
ELEVEN_API_KEY = os.getenv("ELEVEN_API_KEY")
ELEVEN_VOICE_ID = os.getenv("ELEVEN_VOICE_ID", "iNlaSRLu8vd4RtnF3w9i")
AUDIO_FOLDER = os.path.join(os.getcwd(), "audio")

os.makedirs(AUDIO_FOLDER, exist_ok=True)

def texto_a_voz(texto, call_sid, velocidad="x-fast"):
    """
    Convierte un texto a voz usando ElevenLabs y guarda el archivo MP3
    :param texto: Texto a convertir
    :param call_sid: Identificador único de la llamada para nombrar el archivo
    :param velocidad: Velocidad del habla (fast, medium, slow)
    :return: Ruta del archivo MP3 generado
    """
    if not ELEVEN_API_KEY:
        raise RuntimeError("ELEVEN_API_KEY no configurada en environment")

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVEN_VOICE_ID}"
    headers = {
        "xi-api-key": ELEVEN_API_KEY,
        "Accept": "audio/mpeg",
        "Content-Type": "application/json"
    }

    ssml_texto = f"<speak><prosody rate='{velocidad}'>{texto}</prosody></speak>"

    data = {
        "text": ssml_texto,
        "model_id": "eleven_multilingual_v2",  # modelo que soporta SSML
        "voice_settings": {
            "stability": 0.8,
            "similarity_boost": 0.95
        }
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error("❌ Error al llamar ElevenLabs API: %s", e)
        return None

    if "audio" not in response.headers.get("Content-Type", ""):
        logger.error("❌ Respuesta de ElevenLabs no contiene audio: %s", response.text)
        return None

    output_file = os.path.join(AUDIO_FOLDER, f"{call_sid}.mp3")
    try:
        with open(output_file, "wb") as f:
            f.write(response.content)
        logger.info("✅ Archivo de audio generado: %s", output_file)
        return output_file
    except Exception as e:
        logger.error("❌ Error guardando archivo MP3: %s", e)
        return None
