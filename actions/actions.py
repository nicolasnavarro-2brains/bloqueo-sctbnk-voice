from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, FollowupAction
import logging
from datetime import datetime
import requests
import os
import uuid
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ----------------- SALUDOS -----------------
class ActionSaludoInteligente(Action):
    def name(self) -> Text:
        return "action_saludo_inteligente"
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        if not tracker.get_slot("saludo_dado"):
            dispatcher.utter_message(response="utter_greeting")
            return [SlotSet("saludo_dado", True)]
        return []

class ActionSaludoUsuarioDesconocido(Action):
    def name(self) -> Text:
        return "action_saludo_usuario_desconocido"
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        if not tracker.get_slot("saludo_dado"):
            dispatcher.utter_message(response="utter_greeting")
            return [SlotSet("saludo_dado", True)]
        return []

class ActionSaludoContextual(Action):
    def name(self) -> Text:
        return "action_saludo_contextual"
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        if not tracker.get_slot("saludo_dado"):
            dispatcher.utter_message(response="utter_greeting")
            return [SlotSet("saludo_dado", True)]
        return []

# ----------------- RUT -----------------
class ActionVerificarRUT(Action):
    def name(self) -> Text:
        return "action_verificar_rut"
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        rut = tracker.latest_message.get("text").replace(".", "").replace("-", "").strip()
        intentos = int(tracker.get_slot("rut_intentos") or 0)
        if rut.isdigit() and len(rut) >= 8:
            return [SlotSet("rut_valido", True), SlotSet("rut_intentos", 0)]
        else:
            intentos += 1
            dispatcher.utter_message(response="utter_rut_invalido")
            if intentos >= 3:
                dispatcher.utter_message(response="utter_despedida")
            else:
                dispatcher.utter_message(response="utter_pedir_rut")
            return [SlotSet("rut_valido", False), SlotSet("rut_intentos", intentos)]

# ----------------- TARJETA -----------------
class ActionSolicitarDigitos(Action):
    def name(self) -> Text:
        return "action_solicitar_digitos"
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        dispatcher.utter_message(response="utter_collect_digitos")
        return []

class ActionVerificarTarjeta(Action):
    def name(self) -> Text:
        return "action_verificar_tarjeta"
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        digitos = tracker.get_slot("digitos")
        tarjetas_validas = ["1234", "5678"]
        if digitos in tarjetas_validas:
            return [SlotSet("selected_card", digitos)]
        else:
            dispatcher.utter_message(response="utter_card_not_found")
            return [SlotSet("selected_card", None)]

class ActionBloquearTarjeta(Action):
    def name(self) -> Text:
        return "action_bloquear_tarjeta"
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        dispatcher.utter_message(response="utter_bloqueo_exitoso")
        return []

class ActionConfirmarBloqueo(Action):
    def name(self) -> Text:
        return "action_confirmar_bloqueo"
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        dispatcher.utter_message(response="utter_collect_confirmar_bloqueo")
        return []

# ----------------- TICKET -----------------
class ActionGenerarTicket(Action):
    def name(self) -> Text:
        return "action_generar_ticket"
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        case_number = f"BLK-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8]}"
        dispatcher.utter_message(response="utter_ticket_created", text=f"Excelente, se ha generado el ticket número {case_number}.")
        return [
            SlotSet("ticket_number", case_number),
            SlotSet("ticket_created", True),
            SlotSet("card_blocked", True)
        ]

class ActionConfirmarTicket(Action):
    def name(self) -> Text:
        return "action_confirmar_ticket"
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        ticket_number = tracker.get_slot("ticket_number")
        if ticket_number:
            dispatcher.utter_message(response="utter_ticket_created", text=f"Perfecto, tu ticket {ticket_number} ha sido creado exitosamente.")
        else:
            dispatcher.utter_message(response="utter_fallback")
        return []

# ----------------- IDENTIDAD -----------------
class ActionConfirmarIdentidad(Action):
    def name(self) -> Text:
        return "action_confirmar_identidad"
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        dispatcher.utter_message(response="utter_confirmar_identidad")
        # Aquí se puede simular push a app
        return []

# ----------------- DESPEDIDA -----------------
class ActionDespedidaContextual(Action):
    def name(self) -> Text:
        return "action_despedida_contextual"
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        dispatcher.utter_message(response="utter_despedida")
        return [FollowupAction("action_listen")]

# ----------------- Fallback -----------------
class ActionFallbackToHuman(Action):
    def name(self) -> Text:
        return "action_fallback_to_human"
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        dispatcher.utter_message(response="utter_fallback")
        return []

# ----------------- OTROS -----------------
class ActionHandleDecline(Action):
    def name(self) -> Text:
        return "action_handle_decline"
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        dispatcher.utter_message(response="utter_transfer_cancelled")
        return []

class ActionClarifyDigits(Action):
    def name(self) -> Text:
        return "action_clarify_digits"
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        dispatcher.utter_message(response="utter_ask_digitos")
        return []

class ActionEndGreeting(Action):
    def name(self) -> Text:
        return "action_end_greeting"
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        dispatcher.utter_message(response="utter_greeting")
        return []
