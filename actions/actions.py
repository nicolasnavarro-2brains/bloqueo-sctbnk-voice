
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, FollowupAction
import requests
import os
from datetime import datetime
import logging
from dotenv import load_dotenv
import re


# Cargar variables de entorno desde .env
load_dotenv()

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ActionSaludoInteligente(Action):
    """Acción inteligente para saludar solo cuando sea necesario"""
    
    def name(self) -> Text:
        return "action_saludo_inteligente"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Verificar si ya se ha saludado en esta conversación
        saludo_ya_dado = tracker.get_slot("saludo_dado")
        
        # Verificar si ya hay mensajes del bot en la conversación (indicando que no es el primer turno)
        bot_events = [e for e in tracker.events if e.get('event') == 'bot']
        if len(bot_events) > 0:  # Ya hay mensajes del bot
            logger.info(f"Ya hay {len(bot_events)} mensajes del bot, no mostrar saludo repetitivo")
            return []
        
        if saludo_ya_dado:
            # Si ya se saludó, no mostrar saludo repetitivo
            logger.info("Saludo ya dado, no mostrar saludo repetitivo")
            return []
        
        # Verificar si el usuario es desconocido (no tiene customer_id en metadata)
        # Para usuarios desconocidos, ser más restrictivo con el saludo
        metadata = tracker.get_slot("metadata") or {}
        customer_id = metadata.get("customer_id")
        
        if not customer_id:
            # Usuario desconocido, solo saludar en el primer turno absoluto
            user_events = [e for e in tracker.events if e.get('event') == 'user']
            if len(user_events) > 1:  # Ya no es el primer turno
                logger.info("Usuario desconocido - Ya no es el primer turno, no mostrar saludo")
                return []
        
        current_hour = datetime.now().hour
        
        if 5 <= current_hour < 12:
            greeting = "¡Buenos días! Soy el asistente de Scotiabank, ¿en qué puedo ayudarte?"
        elif 12 <= current_hour < 19:
            greeting = "¡Buenas tardes! Soy el asistente de Scotiabank, ¿en qué puedo ayudarte?"
        else:
            greeting = "¡Buenas noches! Soy el asistente de Scotiabank, ¿en qué puedo ayudarte?"
        
        dispatcher.utter_message(text=greeting)
        
        # Marcar que ya se ha saludado
        return [SlotSet("saludo_dado", True)]

class ActionSaludoUsuarioDesconocido(Action):
    """Acción para saludar solo a usuarios desconocidos cuando sea necesario"""
    
    def name(self) -> Text:
        return "action_saludo_usuario_desconocido"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Verificar si ya se ha saludado en esta conversación
        saludo_ya_dado = tracker.get_slot("saludo_dado")
        
        # Verificar si ya hay mensajes del bot en la conversación (indicando que no es el primer turno)
        bot_events = [e for e in tracker.events if e.get('event') == 'bot']
        if len(bot_events) > 0:  # Ya hay mensajes del bot
            logger.info(f"Usuario desconocido - Ya hay {len(bot_events)} mensajes del bot, no mostrar saludo repetitivo")
            return []
        
        if saludo_ya_dado:
            # Si ya se saludó, no mostrar saludo repetitivo
            logger.info("Usuario desconocido - Saludo ya dado, no mostrar saludo repetitivo")
            return []
        
        # Solo saludar si es el primer turno y no se ha saludado
        current_hour = datetime.now().hour
        
        if 5 <= current_hour < 12:
            greeting = "¡Buenos días! Soy el asistente de Scotiabank, ¿en qué puedo ayudarte?"
        elif 12 <= current_hour < 19:
            greeting = "¡Buenas tardes! Soy el asistente de Scotiabank, ¿en qué puedo ayudarte?"
        else:
            greeting = "¡Buenas noches! Soy el asistente de Scotiabank, ¿en qué puedo ayudarte?"
        
        dispatcher.utter_message(text=greeting)
        
        # Marcar que ya se ha saludado
        return [SlotSet("saludo_dado", True)]

class ActionSaludoContextual(Action):
    """Acción para saludar según la hora del día"""
    
    def name(self) -> Text:
        return "action_saludo_contextual"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Verificar si ya se ha saludado en esta conversación
        saludo_ya_dado = tracker.get_slot("saludo_dado")
        
        # Verificar si ya hay mensajes del bot en la conversación (indicando que no es el primer turno)
        bot_events = [e for e in tracker.events if e.get('event') == 'bot']
        if len(bot_events) > 0:  # Ya hay mensajes del bot
            logger.info(f"Ya hay {len(bot_events)} mensajes del bot, no mostrar saludo repetitivo")
            return []
        
        if saludo_ya_dado:
            # Si ya se saludó, no mostrar saludo repetitivo
            logger.info("Saludo ya dado, no mostrar saludo repetitivo")
            return []
        
        current_hour = datetime.now().hour
        
        if 5 <= current_hour < 12:
            greeting = "¡Buenos días! Soy el asistente de Scotiabank, ¿en qué puedo ayudarte?"
        elif 12 <= current_hour < 19:
            greeting = "¡Buenas tardes! Soy el asistente de Scotiabank, ¿en qué puedo ayudarte?"
        else:
            greeting = "¡Buenas noches! Soy el asistente de Scotiabank, ¿en qué puedo ayudarte?"
        
        dispatcher.utter_message(text=greeting)
        
        # Marcar que ya se ha saludado
        return [SlotSet("saludo_dado", True)]

class ActionSolicitarDigitos(Action):
    """Acción para solicitar los últimos 4 dígitos de la tarjeta"""
    
    def name(self) -> Text:
        return "action_solicitar_digitos"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        message = "Perfecto, te puedo ayudar con eso. Dime, ¿qué tarjeta es la que necesitas bloquear? Puedes darme los últimos 4 dígitos."
        dispatcher.utter_message(text=message)
        return []


class ActionConfirmarBloqueo(Action):
    """Acción para confirmar el bloqueo de la tarjeta"""
    
    def name(self) -> Text:
        return "action_confirmar_bloqueo"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        message = "Entiendo, voy a generar un ticket para el bloqueo de tu tarjeta. ¿Te parece bien proceder?"
        dispatcher.utter_message(text=message)
        return []

class ActionGenerarTicket(Action):
    """Acción para generar el ticket en Freshdesk"""
    
    def name(self) -> Text:
        return "action_generar_ticket"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        try:
            case_number = self.crear_ticket_freshdesk(tracker)
            if case_number:
                dispatcher.utter_message(text=f"Excelente, se ha generado el caso número {case_number}. En instantes un ejecutivo realizará el bloqueo de tu tarjeta.")
                return [
                    SlotSet("ticket_number", case_number),
                    SlotSet("ticket_created", True),
                    SlotSet("case_number", case_number),
                    SlotSet("card_blocked", True)
                ]
            # Fallo creando ticket real
            dispatcher.utter_message(text="Lo siento, hubo un problema creando el ticket en soporte. Te transferiré con un ejecutivo humano para ayudarte inmediatamente.")
            return [
                SlotSet("ticket_created", False),
                FollowupAction("action_fallback_to_human")
            ]
        except Exception as e:
            logger.error(f"Error al generar ticket: {e}")
            dispatcher.utter_message(text="Estamos experimentando dificultades técnicas para crear el ticket. Te transferiré con un ejecutivo humano ahora mismo.")
            return [
                SlotSet("ticket_created", False),
                FollowupAction("action_fallback_to_human")
            ]
    
    def crear_ticket_freshdesk(self, tracker: Tracker) -> str:
        """Crea un ticket en Freshdesk con información completa del cliente y tarjeta"""
        API_KEY = os.getenv("FRESHDESK_API_KEY") or os.getenv("API_KEY")
        DOMAIN = os.getenv("FRESHDESK_DOMAIN") or os.getenv("DOMAIN") or "2brains-support"
        
        if not API_KEY:
            logger.error("API_KEY no configurada")
            return None
            
        freshdesk_url = f'https://{DOMAIN}.freshdesk.com/api/v2/tickets'
        headers = {
            'Content-Type': 'application/json'
        }
        
        # Get customer information for ticket (desde slots o metadata del tracker)
        # La metadata viene en el tracker, no como slot
        metadata = {}
        if hasattr(tracker, 'latest_message') and tracker.latest_message:
            metadata = tracker.latest_message.get("metadata", {})
        
        customer_id = tracker.get_slot("customer_id") or metadata.get("customer_id") or "CLIENTE_DEFAULT"
        customer_full_name = tracker.get_slot("customer_full_name") or metadata.get("customer_full_name") or "Cliente Scotiabank"
        customer_phone = tracker.get_slot("customer_phone") or metadata.get("customer_phone") or None
        
        logger.info(f"🔍 Metadata encontrada: {metadata}")
        logger.info(f"👤 Cliente: {customer_id}, {customer_full_name}, {customer_phone}")
        
        # Get card details for ticket
        digitos = tracker.get_slot("digitos") or "****"
        card_name = f"Tarjeta terminada en {digitos}"
        
        logger.info(f"Creating ticket for card ending in {digitos}")
        
        # Función auxiliar para formatear RUT (implementación básica)
        def formatear_rut(rut):
            if not rut:
                return "N/A"
            # Formato básico: XX.XXX.XXX-X
            rut_clean = str(rut).replace(".", "").replace("-", "")
            if len(rut_clean) >= 2:
                return f"{rut_clean[:-1]}-{rut_clean[-1]}"
            return rut
        
        ticket_data = {
            "subject": f"Bloqueo de tarjeta confirmado - RUT {formatear_rut(customer_id)}",
            "description": (
                f"Tarjeta {card_name} bloqueada para {customer_full_name} (RUT {formatear_rut(customer_id)}). "
                f"Teléfono: {customer_phone or 'N/D'}."
            ),
            "status": 2,
            "priority": 1,
            "name": customer_full_name  # Freshdesk requiere name cuando se proporciona phone
        }
        # Freshdesk requiere email o phone. Si tenemos teléfono, úsalo; si no, usa un email genérico.
        if customer_phone:
            ticket_data["phone"] = customer_phone
        else:
            ticket_data["email"] = "cliente@ejemplo.com"
        
        try:
            # Usar autenticación correcta: auth=(API_KEY, 'X')
            logger.info(f"Enviando POST a: {freshdesk_url}")
            logger.info(f"Headers: {headers}")
            logger.info(f"Data del ticket: {ticket_data}")
            
            freshdesk_response = requests.post(
                freshdesk_url, 
                json=ticket_data, 
                headers=headers, 
                auth=(API_KEY, 'X')
            )
            
            logger.info(f"Respuesta de Freshdesk: Status {freshdesk_response.status_code}")
            logger.info(f"Headers de respuesta: {dict(freshdesk_response.headers)}")
            logger.info(f"Contenido de respuesta: {freshdesk_response.text}")
            
            # Check if Freshdesk ticket was created successfully
            if freshdesk_response.status_code in [200, 201]:
                logger.info(f"Freshdesk ticket created successfully. Status: {freshdesk_response.status_code}")
                freshdesk_data = freshdesk_response.json()
                
                # Generate case number using Freshdesk ticket ID
                from datetime import datetime
                import uuid
                case_number = f"BLK-{datetime.now().strftime('%Y%m%d')}-{freshdesk_data.get('id', str(uuid.uuid4()))}"
                
                logger.info(f"Card blocking process completed successfully. Case number: {case_number}")
                return case_number
            else:
                logger.warning(f"Failed to create Freshdesk ticket. Status: {freshdesk_response.status_code} Body: {freshdesk_response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Excepción al crear ticket: {e}")
            return None

class ActionConfirmarTicket(Action):
    """Acción para confirmar que el ticket fue creado"""
    
    def name(self) -> Text:
        return "action_confirmar_ticket"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        ticket_number = tracker.get_slot("ticket_number")
        
        if ticket_number:
            dispatcher.utter_message(text=f"Perfecto, tu ticket {ticket_number} ha sido creado exitosamente. Ahora procederé a despedirme.")
            return [FollowupAction("action_despedida_contextual")]
        else:
            dispatcher.utter_message(text="Lo siento, hubo un problema con el ticket. Te voy a conectar con un ejecutivo.")
            return [FollowupAction("action_fallback_to_human")]

class ActionDespedidaContextual(Action):
    """Acción para despedirse según la hora del día"""
    
    def name(self) -> Text:
        return "action_despedida_contextual"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        current_hour = datetime.now().hour
        
        if 5 <= current_hour < 12:
            goodbye = "Gracias por contactarte con nosotros. ¡Que tengas un excelente día!"
        elif 12 <= current_hour < 19:
            goodbye = "Gracias por contactarte con nosotros. ¡Que tengas una excelente tarde!"
        else:
            goodbye = "Gracias por contactarte con nosotros. ¡Que tengas una excelente noche!"
        
        dispatcher.utter_message(text=goodbye)
        
        from rasa_sdk.events import ConversationPaused
        return [ConversationPaused()]

class ActionPreguntarConfirmacion(Action):
    """Acción para preguntar si desea confirmar el bloqueo, mencionando los 4 dígitos"""
    
    def name(self) -> Text:
        return "action_preguntar_confirmacion"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Obtener los dígitos de la tarjeta del slot
        digitos = tracker.get_slot("digitos")
        
        if digitos:
            # Decir los dígitos separados para mayor claridad
            digitos_separados = " ".join(digitos)
            mensaje = f"Perfecto, encontré tu tarjeta terminada en {digitos_separados}. ¿Deseas continuar con el bloqueo?"
        else:
            # Fallback si no hay dígitos (no debería pasar)
            mensaje = "Su tarjeta ha sido encontrada. ¿Desea continuar con el bloqueo?"
        
        dispatcher.utter_message(text=mensaje)
        
        return []

class ActionBloqueoCancelado(Action):
    """Acción para cuando el usuario cancela el bloqueo"""
    
    def name(self) -> Text:
        return "action_bloqueo_cancelado"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        dispatcher.utter_message(text="Entendido, no se realizará el bloqueo de tu tarjeta. Gracias por contactarte con nosotros.")
        
        from rasa_sdk.events import ConversationPaused
        return [ConversationPaused()]

class ActionFallbackToHuman(Action):
    """Acción para conectar con un ejecutivo humano"""
    
    def name(self) -> Text:
        return "action_fallback_to_human"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        message = "Lo siento, no pude entenderte bien. Te voy a conectar con un ejecutivo que te ayudará personalmente."
        dispatcher.utter_message(text=message)
        return []

class ActionClarifyDigits(Action):
    """Acción para aclarar la solicitud de dígitos"""
    
    def name(self) -> Text:
        return "action_clarify_digits"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        message = "Necesito que me proporciones los últimos 4 dígitos de la tarjeta que quieres bloquear. Por ejemplo: 1234"
        dispatcher.utter_message(text=message)
        return []

class ActionCardNotFound(Action):
    """Acción para manejar tarjetas no encontradas"""
    
    def name(self) -> Text:
        return "action_card_not_found"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        message = "No encontré una tarjeta con esos últimos 4 dígitos. ¿Podrías verificar y proporcionarme los dígitos correctos?"
        dispatcher.utter_message(text=message)
        return []

class ActionHandleDecline(Action):
    """Acción para manejar cuando el usuario declina"""
    
    def name(self) -> Text:
        return "action_handle_decline"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        message = "Entiendo que no quieres proceder con el bloqueo. ¿Te gustaría que te ayude con algo más o prefieres terminar la llamada?"
        dispatcher.utter_message(text=message)
        return []

class ActionGreetingResponse(Action):
    """Acción para responder a saludos"""
    
    def name(self) -> Text:
        return "action_greeting_response"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        message = "¡Hola! ¿En qué puedo ayudarte hoy?"
        dispatcher.utter_message(text=message)
        return []

class ActionEndGreeting(Action):
    """Acción para terminar conversaciones de solo saludo"""
    
    def name(self) -> Text:
        return "action_end_greeting"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        message = "Me alegra que me hayas saludado. Si necesitas ayuda con algo específico, no dudes en decírmelo."
        dispatcher.utter_message(text=message)
        return []
    
class ActionVerificarRUT(Action):
    def name(self) -> Text:
        return "action_verificar_rut"

    def run(self, dispatcher, tracker, domain):
        rut = re.sub(r"\D", "", tracker.latest_message.get("text", ""))
        intentos = tracker.get_slot("rut_intentos") or 0
        logger.info(f"🔎 Verificando RUT: {rut}")

        if re.fullmatch(r"\d{7,8}[0-9kK]?", rut):
            return [SlotSet("rut_valido", True), SlotSet("rut_intentos", 0)]
        else:
            return [SlotSet("rut_valido", False), SlotSet("rut_intentos", intentos + 1)]

class ActionVerificarTarjeta(Action):
    def name(self) -> Text:
        return "action_verificar_tarjeta"
    
    def convertir_palabras_a_numeros(self, texto):
        """Convierte palabras numéricas en español a dígitos"""
        palabras_a_digitos = {
            "cero": "0", "uno": "1", "dos": "2", "tres": "3", "cuatro": "4",
            "cinco": "5", "seis": "6", "siete": "7", "ocho": "8", "nueve": "9",
            "0": "0", "1": "1", "2": "2", "3": "3", "4": "4",
            "5": "5", "6": "6", "7": "7", "8": "8", "9": "9"
        }
        
        # Separar por espacios y convertir cada palabra
        palabras = texto.lower().split()
        digitos = []
        for palabra in palabras:
            palabra_limpia = palabra.strip()
            if palabra_limpia in palabras_a_digitos:
                digitos.append(palabras_a_digitos[palabra_limpia])
        
        return "".join(digitos) if len(digitos) == 4 else None

    def run(self, dispatcher, tracker, domain):
        # Obtener los dígitos del slot o del mensaje
        digits = tracker.get_slot("digitos")
        if not digits:
            # Intentar extraer del mensaje si no está en el slot
            message_text = tracker.latest_message.get("text", "")
            logger.info(f"Mensaje recibido para verificación: '{message_text}'")
            
            # Primero intentar buscar 4 dígitos seguidos
            message_text_no_spaces = message_text.replace(" ", "").replace("-", "")
            digit_match = re.search(r'(\d{4})', message_text_no_spaces)
            if digit_match:
                digits = digit_match.group(1)
            else:
                # Intentar convertir palabras a números (por si se dictó por voz)
                digits = self.convertir_palabras_a_numeros(message_text)
        
        # Obtener intentos actuales
        intentos = int(tracker.get_slot("tarjeta_intentos") or 0)
        
        logger.info(f"Verificando tarjeta con dígitos: {digits} (intento {intentos + 1})")

        if not digits or len(digits) != 4 or not digits.isdigit():
            # No mostrar mensaje, el flow lo manejará
            return [SlotSet("tarjeta_valida", False)]

        # Lista de tarjetas válidas para testing
        tarjetas_validas = ["1234", "5678", "9999", "0000"]
        
        if digits in tarjetas_validas:
            logger.info(f"✅ Tarjeta válida encontrada: {digits}")
            return [
                SlotSet("selected_card", digits),
                SlotSet("tarjeta_valida", True),
                SlotSet("tarjeta_encontrada", True),
                SlotSet("tarjeta_intentos", 0)  # Resetear intentos
            ]
        else:
            intentos += 1
            logger.info(f"❌ Tarjeta inválida: {digits} (intento {intentos})")
            
            if intentos >= 2:
                dispatcher.utter_message("No se pudo validar su tarjeta después de 2 intentos. Te voy a conectar con un ejecutivo que te ayudará personalmente.")
                return [
                    SlotSet("tarjeta_valida", False),
                    SlotSet("tarjeta_encontrada", False),
                    SlotSet("tarjeta_intentos", intentos),
                    FollowupAction("action_transferir_a_ejecutivo")
                ]
            else:
                # NO limpiar slot aquí, el flow lo manejará
                return [
                    SlotSet("tarjeta_valida", False),
                    SlotSet("tarjeta_encontrada", False),
                    SlotSet("tarjeta_intentos", intentos)
                ]

class ActionProcesarConfirmacion(Action):
    """Procesa la confirmación del usuario para bloquear la tarjeta"""
    
    def name(self) -> Text:
        return "action_procesar_confirmacion"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Obtener el último intent del usuario
        last_intent = tracker.latest_message.get("intent", {}).get("name", "")
        
        logger.info(f"💬 Intent recibido: {last_intent}")
        
        if last_intent == "confirmar_bloqueo":
            # Usuario confirmó el bloqueo
            return [SlotSet("confirmar_bloqueo", True)]
        elif last_intent == "negar_bloqueo":
            # Usuario canceló el bloqueo
            return [SlotSet("confirmar_bloqueo", False)]
        else:
            # No se reconoció la respuesta, pedir clarificación
            dispatcher.utter_message("No entendí tu respuesta. Por favor, confirma con 'sí' o 'no'. ¿Deseas continuar con el bloqueo?")
            return [SlotSet("confirmar_bloqueo", None)]

class ActionBloquearTarjeta(Action):
    def name(self) -> Text:
        return "action_bloquear_tarjeta"

    def run(self, dispatcher, tracker, domain):
        card = tracker.get_slot("selected_card")
        logger.info(f"🚫 Bloqueando tarjeta {card}")
        # Aquí llamas a tu función real de DB
        dispatcher.utter_message(f"✅ Tarjeta {card} bloqueada en sistema.")
        return []
    
class ActionConfirmarIdentidad(Action):
    def name(self) -> Text:
        return "action_confirmar_identidad"

    def run(self, dispatcher, tracker, domain):
        # Mensaje IVR
        mensaje = ("Estamos enviando una notificación a su app Scotiabank para confirmar su identidad. "
                   "Por favor, autorice desde su dispositivo móvil.")
        dispatcher.utter_message(text=mensaje)

        # Simulación de push notification a la app (ejemplo REST)
        try:
            response = requests.post(
                os.getenv("APP_PUSH_ENDPOINT"),
                json={
                    "customer_id": tracker.get_slot("customer_id"),
                    "titulo": "Confirmación de identidad",
                    "mensaje": "Autoriza el bloqueo de tu tarjeta",
                    "acciones": ["Autorizar", "Rechazar"]
                }
            )
            if response.status_code == 200:
                logger.info("📲 Push enviada correctamente")
            else:
                logger.warning(f"⚠️ Error push: {response.status_code} {response.text}")
        except Exception as e:
            logger.error(f"❌ No se pudo enviar push: {e}")

        return []
# actions/actions.py
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from typing import Any, Dict, List
import random
import logging

logger = logging.getLogger(__name__)

# Acción: enviar push notification
class ActionEnviarPush(Action):
    def name(self) -> str:
        return "action_enviar_push"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[str, Any]) -> List[Dict[str, Any]]:
        
        # Simulación del push
        logger.info("📲 Enviando push a la app Scotiabank...")
        dispatcher.utter_message(text="📲 Hemos enviado una notificación a su app Scotiabank. Por favor autorice.")
        
        # Aquí iría integración con API real de push
        return []

# Acción: bloquear tarjeta
class ActionBloquearTarjeta(Action):
    def name(self) -> str:
        return "action_bloquear_tarjeta"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[str, Any]) -> List[Dict[str, Any]]:
        
        tarjeta = tracker.get_slot("selected_card")
        if tarjeta:
            dispatcher.utter_message(text=f"✅ La tarjeta terminada en {tarjeta} ha sido bloqueada exitosamente.")
        else:
            dispatcher.utter_message(text="⚠️ No encontré la tarjeta para bloquear.")
        
        return []

# Acción: transferir a ejecutivo
class ActionTransferirEjecutivo(Action):
    def name(self) -> str:
        return "action_transferir_a_ejecutivo"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[str, Any]) -> List[Dict[str, Any]]:
        
        dispatcher.utter_message(text="📞 Te estoy transfiriendo con un ejecutivo humano...")
        # Aquí deberías invocar Twilio <Dial> para transferir la llamada
        from rasa_sdk.events import ConversationPaused
        return [ConversationPaused()]

class ActionSaludoInicial(Action):
    """Acción para saludo inicial en llamada"""
    
    def name(self) -> Text:
        return "action_saludo_inicial"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        dispatcher.utter_message(text="¡Buenos días! Soy el asistente de Scotiabank. Para brindarte el mejor servicio, necesito verificar tu identidad.")
        return []

class ActionBuscarClientePorTelefono(Action):
    """Acción para buscar cliente por número de teléfono"""
    
    def name(self) -> Text:
        return "action_buscar_cliente_por_telefono"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Obtener metadata del tracker (enviada desde Twilio)
        metadata = {}
        if hasattr(tracker, 'latest_message') and tracker.latest_message:
            metadata = tracker.latest_message.get("metadata", {})
        
        customer_phone = metadata.get("customer_phone")
        customer_full_name = metadata.get("customer_full_name")
        customer_id = metadata.get("customer_id")
        
        if customer_phone and customer_full_name:
            logger.info(f"Cliente encontrado: {customer_full_name} ({customer_phone})")
            dispatcher.utter_message(text=f"Hola {customer_full_name.split()[0]}, veo que llamas desde {customer_phone}.")
            return [
                SlotSet("cliente_encontrado", True),
                SlotSet("customer_phone", customer_phone),
                SlotSet("customer_full_name", customer_full_name),
                SlotSet("customer_id", customer_id)
            ]
        else:
            logger.warning("Cliente no encontrado en metadata")
            dispatcher.utter_message(text="No pude identificar tu número de teléfono en nuestro sistema.")
            return [SlotSet("cliente_encontrado", False)]

class ActionSolicitarRut(Action):
    """Acción para solicitar RUT al cliente"""
    
    def name(self) -> Text:
        return "action_solicitar_rut"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        dispatcher.utter_message(text="Para continuar, necesito que me proporciones tu RUT sin puntos ni guión. Por ejemplo: 123456789.")
        return []

class ActionValidarRut(Action):
    """Acción para validar RUT del cliente contra la base de datos"""
    
    def name(self) -> Text:
        return "action_validar_rut"
    
    def validar_rut_en_db(self, rut: str, customer_id: str) -> bool:
        """Valida RUT comparándolo con la base de datos"""
        if not rut or not customer_id:
            return False
        
        # Limpiar RUT
        rut_clean = rut.replace(".", "").replace("-", "").upper()
        
        # Comparar con el customer_id de la base de datos
        # En este caso, el customer_id ya viene de la metadata de Twilio
        # que fue obtenido de la base de datos al buscar por teléfono
        logger.info(f"Validando RUT {rut_clean} contra customer_id {customer_id}")
        
        # Simulación: en producción aquí se haría la consulta real a la base de datos
        # Por ahora, asumimos que si el RUT coincide con el customer_id, es válido
        return rut_clean == customer_id
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        rut = tracker.get_slot("rut")
        customer_id = tracker.get_slot("customer_id")
        
        if not rut:
            dispatcher.utter_message(text="No pude obtener tu RUT. ¿Podrías repetirlo?")
            return [SlotSet("rut_valido", False)]
        
        if not customer_id:
            dispatcher.utter_message(text="No pude obtener tu información de cliente. Te voy a conectar con un ejecutivo.")
            return [SlotSet("rut_valido", False), FollowupAction("action_transferir_a_ejecutivo")]
        
        if self.validar_rut_en_db(rut, customer_id):
            dispatcher.utter_message(text="RUT válido. Estamos enviando una notificación a tu app Scotiabank para confirmar tu identidad.")
            return [SlotSet("rut_valido", True)]
        else:
            dispatcher.utter_message(text="El RUT ingresado no coincide con nuestros registros. Por favor, verifica e inténtalo nuevamente.")
            return [SlotSet("rut_valido", False)]

class ActionEnviarPushNotificacion(Action):
    """Acción para enviar push notification"""
    
    def name(self) -> Text:
        return "action_enviar_push_notificacion"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Aquí se integraría con el sistema de push notifications
        logger.info("Enviando push notification para autenticación")
        dispatcher.utter_message(text="Por favor, revisa tu app Scotiabank y confirma tu identidad.")
        return []

class ActionMenuPrincipal(Action):
    """Acción para mostrar menú principal"""
    
    def name(self) -> Text:
        return "action_menu_principal"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        dispatcher.utter_message(text="¿En qué puedo ayudarte hoy? Puedes decir: 'bloquear tarjeta', 'consultar saldo' o 'otros servicios'.")
        return []

class ActionClienteNoEncontrado(Action):
    """Acción para manejar cliente no encontrado"""
    
    def name(self) -> Text:
        return "action_cliente_no_encontrado"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        dispatcher.utter_message(text="No pude encontrar tu información en nuestro sistema. Te voy a conectar con un ejecutivo que te ayudará.")
        return []

class ActionRutInvalido(Action):
    """Acción para manejar RUT inválido"""
    
    def name(self) -> Text:
        return "action_rut_invalido"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        dispatcher.utter_message(text="El RUT que ingresaste no coincide con nuestros registros. Por favor, verifica el número en tu cédula de identidad.")
        return []


class ActionTarjetaNoEncontrada(Action):
    """Acción para manejar tarjeta no encontrada"""
    
    def name(self) -> Text:
        return "action_tarjeta_no_encontrada"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        digitos = tracker.get_slot("digitos") or "****"
        dispatcher.utter_message(text=f"No encontré una tarjeta con los últimos 4 dígitos {digitos}. Por favor, verifica el número en tu tarjeta física y proporciona los dígitos correctos.")
        return []