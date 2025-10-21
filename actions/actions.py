import logging
import os
import re
from datetime import datetime
from typing import Any, Dict, List, Text

import requests
from dotenv import load_dotenv
from rasa_sdk import Action, Tracker
from rasa_sdk.events import FollowupAction, SlotSet, ConversationPaused
from rasa_sdk.executor import CollectingDispatcher

# Cargar variables de entorno desde .env
load_dotenv()

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

class ActionTransferirEjecutivo(Action):
    def name(self) -> str:
        return "action_transferir_a_ejecutivo"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[str, Any]) -> List[Dict[str, Any]]:
        
        dispatcher.utter_message(text="📞 Te estoy transfiriendo con un ejecutivo humano...")
        # Aquí deberías invocar Twilio <Dial> para transferir la llamada
        return [ConversationPaused()]