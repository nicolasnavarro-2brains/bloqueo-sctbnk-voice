# 🏗️ Arquitectura Técnica - Bot de Voz Scotiabank

**Documentación técnica completa del sistema**

---

## 📊 Visión General del Sistema

El bot de voz es un sistema de **4 microservicios** que trabajan juntos:

```
┌─────────────────────────────────────────────────────────┐
│  CLIENTE                                                │
│  Llama al número Twilio                                 │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│  TWILIO VOICE API (Cloud)                               │
│  • Recibe llamada                                       │
│  • Speech-to-Text (STT)                                 │
│  • Text-to-Speech (TTS básico)                          │
│  • Envía webhooks a tu servidor                         │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│  TWILIO VOICE SERVER (Flask)                            │
│  Puerto: 5000                                           │
│  • Orquestador principal                                │
│  • Identificación de clientes                           │
│  • Autenticación multi-factor                           │
│  • Generación de audio (ElevenLabs)                     │
│  • Gestión de sesiones y caché                          │
└──────┬──────────────┬─────────────────┬────────────────┘
       │              │                 │
       ▼              ▼                 ▼
  ┌─────────┐   ┌──────────┐    ┌────────────┐
  │  RASA   │   │ MariaDB  │    │ Freshdesk  │
  │  PRO    │   │  (MySQL) │    │    API     │
  │  5005   │   │   3306   │    │   Cloud    │
  │         │   │          │    │            │
  │ ┌─────┐ │   │ Clientes │    │  Tickets   │
  │ │Flows│ │   │  RUTs    │    │            │
  │ │ NLU │ │   │ Teléfonos│    │            │
  │ └──┬──┘ │   └──────────┘    └────────────┘
  └─────┼───┘
        │
        ▼
  ┌─────────────┐
  │   ACTIONS   │
  │   SERVER    │
  │    5055     │
  │             │
  │  • Lógica   │
  │  • Tickets  │
  │  • Validac. │
  └─────────────┘
```

---

## 🔧 COMPONENTE 1: Twilio Voice Server

**Archivo:** `twilio_voice_server.py`  
**Puerto:** 5000  
**Framework:** Flask  
**Responsabilidad:** Orquestador principal del sistema

### **Funciones Principales (13 endpoints/funciones):**

#### **1. Gestión de Conexiones**
```python
get_database_connection()
```
- Conecta a MySQL/MariaDB
- Pool de conexiones reutilizables
- Manejo de errores de conexión

#### **2. Identificación de Clientes**
```python
get_customer_by_phone(phone_number)
```
- Busca cliente por número telefónico
- Normaliza formatos: +56..., 56..., 9...
- Retorna: id, rut, nombre, nombre_completo, telefono
- **Decisión:** Si no existe → Rechaza llamada

#### **3. Selección de Voz**
```python
seleccionar_voz_para_sesion(call_sid)
```
- Asigna **aleatoriamente** voz femenina o masculina
- **Mantiene consistencia** durante toda la llamada
- Cache por `call_sid`
- Voces: ELEVEN_VOICE_ID (fem), ELEVEN_VOICE_ID2 (masc)

#### **4. Generación de Audio (ElevenLabs TTS)**
```python
texto_a_voz(texto, filename, call_sid, velocidad="1.0")
```
- Convierte texto a audio profesional
- API: ElevenLabs (voces neuronales)
- **Almacenamiento:** RAM (audio_cache) - NO disco
- Parámetros personalizables: velocidad, estabilidad, claridad

#### **5. Respuestas TwiML**
```python
responder_con_tts_twiml(container, texto, call_sid, tag="msg")
```
- Genera respuestas en formato TwiML de Twilio
- Integra audio de ElevenLabs
- Fallback a Polly.Mia (TTS de Twilio) si ElevenLabs falla
- Logging completo de URLs

#### **6. Integración con Rasa**
```python
delegar_a_rasa(session_id, user_message)
```
- Envía mensaje del usuario a Rasa
- Endpoint: `/webhooks/rest/webhook`
- Recibe: Lista de respuestas del bot
- Manejo de errores y timeout

#### **7. Validación de RUT**
```python
verificar_rut_en_bd(rut)
```
- Consulta RUT en base de datos
- Valida contra tabla `customers`
- Retorna: `True/False` + datos del cliente

#### **8. Limpieza de Recursos**
```python
limpiar_cache_de_llamada(call_sid)
```
- Limpia **todos** los caches al finalizar llamada
- Libera audio de memoria (RAM)
- Elimina: phone_cache, rut_attempts_cache, voice_assignment_cache, audio_cache
- **Trigger:** Callback de Twilio cuando llamada termina

---

### **Endpoints HTTP (5):**

#### **1. `/audio/<filename>` [GET]**
```python
serve_audio(filename)
```
- Sirve archivos de audio desde **memoria RAM**
- Content-Type: audio/mpeg
- Logging de cada request

#### **2. `/webhook/twilio/voice` [POST]**
```python
incoming_call()
```
**Flujo completo:**
1. Recibe llamada de Twilio
2. Extrae `call_sid` y `From` (teléfono)
3. Busca cliente en BD: `get_customer_by_phone()`
4. **Si existe:**
   - Saludo personalizado: "Hola {nombre}"
   - Asigna voz (fem/masc) para sesión
   - Solicita RUT por DTMF
   - Action: `/webhook/twilio/collect_rut`
5. **Si NO existe:**
   - Mensaje: "Lo siento, tu número no está registrado"
   - Cuelga llamada

**Entrada DTMF:** 
- `num_digits=8` (RUT sin dígito verificador)
- `timeout=10` segundos
- `finish_on_key=#`

#### **3. `/webhook/twilio/collect_rut` [POST]**
```python
collect_rut()
```
**Autenticación multi-capa:**
1. Recibe dígitos del RUT (DTMF)
2. Valida contra BD: `verificar_rut_en_bd()`
3. **Si RUT correcto:**
   - Marca sesión como autenticada
   - Mensaje: "Perfecto. Ahora puede decir su solicitud"
   - Action: `/webhook/twilio/rasa_conversation`
4. **Si RUT incorrecto:**
   - Incrementa contador de intentos (máx 3)
   - Reintentar o transferir a ejecutivo
5. **Metadata a Rasa:**
   - Envía RUT, nombre, call_sid para contexto

**Optimización:** 
- Velocidad 1.3x para respuesta más ágil
- No genera audio innecesario de "push notification"

#### **4. `/webhook/twilio/rasa_conversation` [POST]**
```python
rasa_conversation()
```
**Motor conversacional:**
1. **Entrada flexible:**
   - `SpeechResult`: Voz (transcripción Twilio)
   - `Digits`: Teclado numérico (DTMF)
   - Prioridad: Voz > DTMF
2. Delega a Rasa: `delegar_a_rasa(call_sid, user_input)`
3. **Procesa respuestas de Rasa:**
   - Genera audio para cada mensaje
   - Mantiene contexto de sesión
   - Gather para siguiente input
4. **Configuración Gather:**
   - `input="speech dtmf"` (ambos métodos)
   - `num_digits=4` (para tarjeta)
   - `speech_timeout="auto"`
   - `language="es-CL"`
5. **Manejo de errores:**
   - Si Rasa no responde → Fallback
   - Si no hay input → Repite pregunta

#### **5. `/webhook/twilio/status` [POST]**
```python
call_status()
```
**Callback de limpieza:**
- Recibe: `CallStatus` de Twilio
- Estados: `completed`, `busy`, `no-answer`, `failed`, `canceled`
- **Acción:** Llama a `limpiar_cache_de_llamada()`
- **Resultado:** Libera RAM y recursos

---

### **Caches y Gestión de Estado:**

```python
# Diccionarios en memoria (por call_sid)
phone_cache = {}           # Teléfono del cliente
autorizacion_cache = {}    # ¿Está autenticado?
rut_attempts_cache = {}    # Intentos de RUT (máx 3)
session_metadata_cache = {} # Metadata enviada a Rasa
voice_assignment_cache = {} # Voz asignada (fem/masc)
audio_cache = {}           # Audio en RAM (filename -> bytes)
```

**Limpieza:** Todos se limpian automáticamente al terminar llamada

---

### **Configuración (Variables de Entorno):**

```bash
# ElevenLabs TTS
ELEVEN_API_KEY=sk-...
ELEVEN_VOICE_ID=<voice_id_femenina>
ELEVEN_VOICE_ID2=<voice_id_masculina>

# Rasa
RASA_URL=http://localhost:5005/webhooks/rest/webhook

# Base de datos
DB_HOST=localhost
DB_PORT=3306
DB_USER=nico
DB_PASSWORD=nico
DB_NAME=bank

# Servidor
BASE_URL=https://tu-url.run.app  # URL pública
PORT=5000
```

---

## 🤖 COMPONENTE 2: Rasa Pro Server

**Puerto:** 5005  
**Versión:** Rasa Pro 3.13.5  
**Responsabilidad:** Motor conversacional e IA

### **Capacidades:**

1. **NLU (Natural Language Understanding)**
   - Intents: solicitar_bloqueo, confirmar, rechazar, etc
   - Entities: digitos_tarjeta, confirmacion
   - Idioma: Español (es)

2. **Dialogue Management (CALM)**
   - Flows conversacionales
   - Gestión de contexto
   - Multi-turn conversations

3. **Custom Actions**
   - Endpoint: `http://actions:5055/webhook`
   - Ejecuta lógica de negocio

### **Endpoints Principales:**

- `/webhooks/rest/webhook` - Recibe mensajes
- `/` - Health check
- `/model` - Información del modelo

---

## ⚙️ COMPONENTE 3: Rasa Actions Server

**Archivo:** `actions/actions.py`  
**Puerto:** 5055  
**Framework:** Rasa SDK  
**Responsabilidad:** Lógica de negocio y integraciones

### **7 Acciones Personalizadas:**

#### **1. ActionGenerarTicket**
```python
action_generar_ticket
```
**Propósito:** Crea ticket en Freshdesk al confirmar bloqueo

**Flujo:**
1. Extrae slots: nombre, rut, telefono, digitos, metadata
2. Crea ticket en Freshdesk API:
   - Subject: "Bloqueo de tarjeta - {nombre}"
   - Description: HTML con datos completos
   - Priority: 1 (Alta)
   - Status: 2 (Abierto)
   - Source: 7 (Teléfono)
3. **Si éxito:**
   - Retorna: ticket_id
   - Mensaje: "Caso número {ticket_id}"
   - Marca: card_blocked=True
4. **Si falla:**
   - Transfiere a ejecutivo humano

**Integraciones:**
- Freshdesk REST API
- Autenticación: API Key

#### **2. ActionDespedidaContextual**
```python
action_despedida_contextual
```
**Propósito:** Despedida personalizada según resultado

**Lógica:**
- Si `card_blocked=True`:
  - "Tu tarjeta ha sido bloqueada exitosamente"
- Si `ticket_created=True`:
  - "Caso {ticket_number} creado"
- Mensaje: "Gracias por llamar. Que tengas un excelente día"

#### **3. ActionPreguntarConfirmacion**
```python
action_preguntar_confirmacion
```
**Propósito:** Confirma bloqueo anunciando últimos 4 dígitos

**Lógica:**
1. Obtiene slot: `digitos` (últimos 4 de tarjeta)
2. **Formatea dígitos separados:**
   - Input: "1234"
   - Output: "1 2 3 4"  (para claridad auditiva)
3. Mensaje: "Perfecto, encontré tu tarjeta terminada en {1 2 3 4}. ¿Deseas continuar con el bloqueo?"

**Mejora UX:** Dígitos separados se escuchan más claro

#### **4. ActionBloqueoCancelado**
```python
action_bloqueo_cancelado
```
**Propósito:** Maneja cancelación voluntaria

**Flujo:**
1. Marca: `card_blocked=False`
2. Mensaje: "Entendido, no bloquearé tu tarjeta"
3. Ofrece: Ayuda adicional o finalizar

#### **5. ActionFallbackToHuman**
```python
action_fallback_to_human
```
**Propósito:** Fallback cuando hay problemas

**Casos de uso:**
- Error técnico
- Usuario confundido
- Tarjeta no encontrada
- Timeout de sistema

**Acción:**
- Mensaje: "Te transferiré con un ejecutivo"
- Pausa conversación: `ConversationPaused()`

#### **6. ActionVerificarTarjeta**
```python
action_verificar_tarjeta
```
**Propósito:** Valida últimos 4 dígitos de tarjeta

**Entrada flexible:**
- **DTMF (teclado):** "1234"
- **Voz (números):** "uno dos tres cuatro"
- **Voz (palabras):** "doce treinta y cuatro"

**Lógica de extracción:**
1. Intenta extraer 4 dígitos consecutivos: `\d{4}`
2. Si no, convierte palabras a números:
   ```python
   "uno" → "1", "dos" → "2", ...
   "diez" → "10", "once" → "11", ...
   "veinte" → "20", "veintiuno" → "21", ...
   ```
3. Valida longitud: exactamente 4 dígitos
4. **Si válido:**
   - Guarda en slot: `digitos`
   - Marca: `tarjeta_valida=True`
5. **Si inválido:**
   - Marca: `tarjeta_valida=False`
   - Solicita reintentar

**Helper:**
```python
convertir_palabras_a_numeros(texto)
```
- Soporte completo español chileno
- Maneja: "uno", "doce", "veinte", "veintiuno", etc.

#### **7. ActionTransferirEjecutivo**
```python
action_transferir_a_ejecutivo
```
**Propósito:** Transfiere llamada a ejecutivo humano

**Flujo:**
1. Mensaje: "Un momento por favor, te transferiré"
2. **Implementación futura:**
   - TwiML: `<Dial>` a número de ejecutivos
   - Queue: Sistema de colas
   - IVR: Integración con call center

---

## 🗄️ COMPONENTE 4: Base de Datos (MySQL/MariaDB)

**Puerto:** 3306 (local) / 3307 (Docker)  
**Motor:** MySQL 8.0 (GCP) / MariaDB 10.6 (Local)

### **Tabla: `customers`**

```sql
CREATE TABLE customers (
    id VARCHAR(36) NOT NULL,              -- UUID
    rut VARCHAR(9) NOT NULL,               -- Sin dígito verificador
    nombre VARCHAR(64) NOT NULL,           -- Nombre corto
    nombre_completo VARCHAR(128) NOT NULL, -- Nombre completo
    telefono VARCHAR(12) NOT NULL,         -- +56912345678
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uk_telefono (telefono),     -- 1 teléfono = 1 cliente
    UNIQUE KEY uk_rut (rut)                -- 1 RUT = 1 cliente
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

### **Clientes de Prueba:**

| Nombre | Teléfono | RUT |
|--------|----------|-----|
| Mauricio | +56982079489 | 12345678 |
| María | +56987654321 | 98765432 |
| Carlos | +56955556666 | 55556666 |
| Nicolas | +56984593400 | 87654321 |

---

## 🔄 Flujo Completo de una Llamada

### **Fase 1: Identificación (5-10 seg)**

```
1. Cliente marca número Twilio
2. Twilio → POST /webhook/twilio/voice
3. Server extrae teléfono: request.values.get("From")
4. Consulta BD: get_customer_by_phone(telefono)
5. Si NO existe:
   → "Tu número no está registrado"
   → Cuelga
6. Si existe:
   → "Hola {nombre}, te habla Scotiabank"
   → Asigna voz (fem/masc) aleatoria
   → Solicita RUT
```

### **Fase 2: Autenticación (10-15 seg)**

```
7. Usuario ingresa RUT (8 dígitos)
8. Server → POST /webhook/twilio/collect_rut
9. Valida: verificar_rut_en_bd(rut)
10. Si RUT incorrecto:
    → Incrementa intentos (máx 3)
    → Si excede → Transfiere a ejecutivo
11. Si RUT correcto:
    → autorizacion_cache[call_sid] = True
    → "Perfecto. Ahora puede decir su solicitud"
```

### **Fase 3: Conversación con Rasa (Variable)**

```
12. Usuario dice: "Quiero bloquear mi tarjeta"
13. Server → POST /webhook/twilio/rasa_conversation
14. Rasa procesa intent: solicitar_bloqueo
15. Rasa solicita: "¿Cuáles son los últimos 4 dígitos?"
16. Usuario: "1 2 3 4" (voz) o "1234" (teclado)
17. Actions → action_verificar_tarjeta
    → Extrae y valida dígitos
18. Rasa → action_preguntar_confirmacion
    → "Encontré tu tarjeta terminada en 1 2 3 4. ¿Confirmas?"
19. Usuario: "Sí"
20. Actions → action_generar_ticket
    → Crea ticket en Freshdesk
    → Retorna ticket_id
21. Rasa: "Caso {ticket_id} creado. Tu tarjeta está bloqueada"
22. Actions → action_despedida_contextual
23. Llamada termina
```

### **Fase 4: Limpieza (Inmediata)**

```
24. Twilio → POST /webhook/twilio/status (CallStatus=completed)
25. Server → limpiar_cache_de_llamada(call_sid)
    → Elimina audio de RAM
    → Limpia todos los caches
    → Libera recursos
```

---

## 🎨 Características Avanzadas

### **1. Audio en Memoria (Zero Disk I/O)**

**Problema resuelto:** No llenar disco con archivos `.mp3`

**Implementación:**
```python
# Generación
audio_bytes = elevenlabs_api.generate()
audio_cache[filename] = audio_bytes  # RAM

# Servir
@app.route("/audio/<filename>")
def serve_audio(filename):
    return Response(audio_cache[filename], mimetype="audio/mpeg")

# Limpieza
def limpiar_cache_de_llamada(call_sid):
    for key in list(audio_cache.keys()):
        if call_sid in key:
            del audio_cache[key]  # Libera RAM
```

**Beneficios:**
- No llena disco
- Más rápido (RAM > Disk)
- Auto-limpieza
- Escalable

### **2. Voces Aleatorias Consistentes**

**Problema resuelto:** Humanizar interacciones

**Lógica:**
```python
# Primera interacción
voice_id, voice_type = random.choice([
    (ELEVEN_VOICE_ID, "femenina"),
    (ELEVEN_VOICE_ID2, "masculina")
])
voice_assignment_cache[call_sid] = (voice_id, voice_type)

# Resto de la llamada
voice_id, voice_type = voice_assignment_cache[call_sid]  # Misma voz
```

**Resultado:** Cliente escucha la misma voz durante toda la llamada

### **3. Entrada Multimodal (Voz + Teclado)**

**Flexibilidad:**
```python
# Configuración
<Gather input="speech dtmf" num_digits="4">
    <Say>Dígame los últimos 4 dígitos</Say>
</Gather>

# Procesamiento
speech_text = request.form.get("SpeechResult", "")
dtmf_digits = request.form.get("Digits", "")
user_input = speech_text if speech_text else dtmf_digits
```

**Casos de uso:**
- Entorno ruidoso → Usa teclado
- Manos ocupadas → Usa voz
- Preferencia personal → Cualquiera

### **4. Conversión Inteligente de Palabras a Números**

**Soporte natural:**
- "uno dos tres cuatro" → "1234"
- "doce treinta y cuatro" → "1234"
- "mil doscientos treinta y cuatro" → "1234"

### **5. Autenticación Multi-Factor**

**Capas de seguridad:**
1. **Teléfono registrado** (posesión)
2. **RUT correcto** (conocimiento)
3. **Últimos 4 dígitos tarjeta** (posesión)

**Resultado:** Triple verificación antes de bloquear

---

## 📊 Métricas y Logging

### **Logs por Acción:**

```
[INFO] Llamada entrante CA123... de +56912345678
[INFO] Cliente encontrado: Nicolas Navarro
[INFO] Voz asignada: masculina (OFrdGXwC...)
[MEMORIA] Audio generado: auth_success.mp3 (78621 bytes)
[INFO] RUT validado correctamente
[INFO] Metadata enviada a Rasa
[OK] Ticket creado: #12345
[MEMORIA] Limpiando cache para CA123...
```

### **Métricas Clave:**

- Llamadas/hora
- Tiempo promedio de llamada
- Tasa de éxito de autenticación
- Tickets generados
- Uso de RAM (audio cache)
- Llamadas exitosas vs fallidas

---

## 🔒 Seguridad

### **1. Datos Sensibles**

**Nunca en logs:**
- ❌ Passwords de BD
- ❌ API Keys
- ❌ RUT completo (solo últimos 4 dígitos)

**Protección:**
```python
logger.info(f"RUT validado: {rut[-4:]}...")  # Solo últimos 4
```

### **2. Validación de Entrada**

- Sanitización de teléfonos
- Validación de RUT (formato y BD)
- Límite de intentos (3 máx)

### **3. HTTPS Obligatorio**

- Webhooks de Twilio → HTTPS only
- Cloud Run → SSL automático
- Certificados: Let's Encrypt

---

## 🚀 Performance

### **Optimizaciones:**

1. **Audio en RAM:** 10x más rápido que disco
2. **Caches por sesión:** Evita lookups repetidos
3. **Pool de conexiones BD:** Reutiliza conexiones
4. **Respuestas rápidas:** Velocidad 1.3x en mensajes cortos
5. **Cleanup automático:** Libera recursos inmediatamente

### **Capacidad:**

- **Local:** 1-5 llamadas concurrentes
- **Cloud Run:** 100+ llamadas concurrentes (auto-escala)

---

## 📦 Dependencias Clave

### **Twilio Server:**
- Flask 3.0.0
- Twilio SDK 8.10.0
- PyMySQL 1.1.0
- ElevenLabs 0.2.27
- python-dotenv 1.1.0

### **Rasa:**
- Rasa Pro 3.13.5
- Rasa SDK 3.9.0

### **Actions:**
- requests 2.31.0
- python-dotenv 1.1.0

---

## 🔧 Configuración Completa

Ver `env.example` para todas las variables de entorno necesarias.

**Críticas:**
- ELEVEN_API_KEY, ELEVEN_VOICE_ID, ELEVEN_VOICE_ID2
- DB_HOST, DB_USER, DB_PASSWORD, DB_NAME
- RASA_URL
- FRESHDESK_API_KEY, FRESHDESK_DOMAIN
- BASE_URL (URL pública del servidor)

---

**Última actualización:** Octubre 2025  
**Mantenedor:** Nicolas Navarro  
**Versión sistema:** 2.0 (Dockerizado)

