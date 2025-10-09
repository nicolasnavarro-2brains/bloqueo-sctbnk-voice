# 🚀 Guía Completa de Setup - Bloqueo SCTBNK Voice

Esta guía te llevará paso a paso por todo el proceso de instalación y configuración del sistema de asistente virtual para bloqueo de tarjetas de Scotiabank.

## 📋 Tabla de Contenidos

1. [Prerrequisitos](#1-prerrequisitos)
2. [Clonar el Repositorio](#2-clonar-el-repositorio)
3. [Crear Entorno Virtual](#3-crear-entorno-virtual)
4. [Instalar Dependencias](#4-instalar-dependencias)
5. [Configurar Base de Datos MariaDB](#5-configurar-base-de-datos-mariadb)
6. [Configurar Variables de Entorno](#6-configurar-variables-de-entorno)
7. [Entrenar Modelo de Rasa](#7-entrenar-modelo-de-rasa)
8. [Lanzar Servicios](#8-lanzar-servicios)
9. [Testing del Sistema](#9-testing-del-sistema)
10. [Solución de Problemas](#10-solución-de-problemas)

---

## 1. Prerrequisitos

Antes de comenzar, asegúrate de tener instalados los siguientes componentes:

### 1.1 Python 3.10.12

**Opción 1: Usando pyenv (Recomendado)**

```bash
# Instalar pyenv
curl https://pyenv.run | bash

# Configurar shell (añadir a ~/.bashrc o ~/.zshrc)
export PATH="$HOME/.pyenv/bin:$PATH"
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"

# Instalar Python 3.10.12
pyenv install 3.10.12
pyenv global 3.10.12

# Verificar instalación
python --version  # Debe mostrar: Python 3.10.12
```

**Opción 2: Instalación directa**

```bash
# macOS
brew install python@3.10

# Ubuntu/Debian
sudo apt update
sudo apt install python3.10 python3.10-venv python3.10-dev

# Verificar instalación
python3.10 --version
```

### 1.2 MariaDB/MySQL

**macOS**

```bash
# Instalar MariaDB
brew install mariadb

# Iniciar servicio
brew services start mariadb

# Configuración inicial (seguir el wizard)
mysql_secure_installation
```

**Ubuntu/Debian**

```bash
# Instalar MariaDB
sudo apt update
sudo apt install mariadb-server mariadb-client

# Iniciar servicio
sudo systemctl start mariadb
sudo systemctl enable mariadb

# Configuración inicial
sudo mysql_secure_installation
```

**Windows**

Descargar desde: https://mariadb.org/download/

### 1.3 Git

```bash
# macOS
brew install git

# Ubuntu/Debian
sudo apt install git

# Verificar instalación
git --version
```

### 1.4 Herramientas Adicionales

```bash
# pip (si no viene con Python)
python -m ensurepip --upgrade

# virtualenv
pip install virtualenv
```

---

## 2. Clonar el Repositorio

```bash
# Clonar repositorio
git clone https://github.com/kaolong/bloqueo-sctbnk-voice.git

# Entrar al directorio
cd bloqueo-sctbnk-voice

# Verificar estructura
ls -la
```

**Estructura esperada:**
```
bloqueo-sctbnk-voice/
├── actions/              # Acciones personalizadas de Rasa
├── audio/               # Archivos de audio generados
├── data/                # Datos de entrenamiento (flows, nlu, rules)
├── domain/              # Configuración del dominio
├── memory-bank/         # Documentación del proyecto
├── models/              # Modelos entrenados (se genera)
├── config.yml           # Configuración de Rasa
├── endpoints.yml        # Configuración de endpoints
├── requirements.txt     # Dependencias principales
├── twilio_requirements.txt  # Dependencias del servidor Twilio
└── README.md           # Documentación principal
```

---

## 3. Crear Entorno Virtual

Es altamente recomendado usar un entorno virtual para aislar las dependencias del proyecto.

```bash
# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# macOS/Linux:
source venv/bin/activate

# Windows:
venv\Scripts\activate

# Verificar activación (debe aparecer (venv) en el prompt)
which python  # Debe apuntar a venv/bin/python
```

**Nota:** Cada vez que abras una nueva terminal, debes activar el entorno virtual con `source venv/bin/activate`.

---

## 4. Instalar Dependencias

### 4.1 Actualizar pip

```bash
pip install --upgrade pip
```

### 4.2 Instalar dependencias principales de Rasa

```bash
pip install -r requirements.txt
```

**Esto instalará:**
- Rasa Pro 3.13.5 con CALM
- Spacy 3.7.0
- Twilio SDK
- PyMySQL para MariaDB
- Otras dependencias necesarias

### 4.3 Instalar dependencias del servidor Twilio

```bash
pip install -r twilio_requirements.txt
```

**Esto instalará:**
- Flask (servidor web)
- Gunicorn (servidor WSGI para producción)
- Flask-CORS (manejo de CORS)
- Otras dependencias específicas de Twilio

### 4.4 Descargar modelo de spaCy en español

```bash
python -m spacy download es_core_news_sm
```

### 4.5 Verificar instalación

```bash
# Verificar Rasa
rasa --version  # Debe mostrar: Rasa 3.13.5

# Verificar Python packages
python -c "import rasa, flask, twilio, pymysql; print('✅ Todas las dependencias instaladas correctamente')"
```

---

## 5. Configurar Base de Datos MariaDB

### 5.1 Conectar a MariaDB

```bash
# Conectar como root
mysql -u root -p
# O si no tiene password:
mysql -u root
```

### 5.2 Crear base de datos y usuario

```sql
-- Crear base de datos
CREATE DATABASE IF NOT EXISTS bank CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Crear usuario (cambia 'tu_password' por una contraseña segura)
CREATE USER IF NOT EXISTS 'nico'@'localhost' IDENTIFIED BY 'tu_password';

-- Otorgar permisos
GRANT ALL PRIVILEGES ON bank.* TO 'nico'@'localhost';

-- Aplicar cambios
FLUSH PRIVILEGES;

-- Verificar
SHOW DATABASES;
SELECT User, Host FROM mysql.user WHERE User='nico';

-- Salir
EXIT;
```

### 5.3 Configurar datos de prueba

El proyecto incluye un script para crear la tabla `customers` e insertar datos de prueba:

```bash
# Asegúrate de haber configurado las variables de entorno primero (ver sección 6)
python setup_test_data.py
```

**El script creará:**
- Tabla `customers` con estructura optimizada
- 4 clientes de prueba (Mauricio, María, Carlos, Nicolas)
- Índices para búsqueda rápida por teléfono y RUT

**Clientes de prueba incluidos:**

| Nombre    | Teléfono       | RUT      |
|-----------|----------------|----------|
| Mauricio  | +56982079489  | 12345678 |
| María     | +56987654321  | 98765432 |
| Carlos    | +56955556666  | 55556666 |
| Nicolas   | +56984593400  | 87654321 |

### 5.4 Verificar datos

```bash
# Conectar a la base de datos
mysql -u nico -p bank

# Verificar tabla
DESCRIBE customers;

# Ver datos
SELECT * FROM customers;

# Salir
EXIT;
```

---

## 6. Configurar Variables de Entorno

### 6.1 Crear archivo .env

```bash
# Copiar archivo de ejemplo
cp env.example .env

# Editar con tu editor preferido
nano .env
# o
vim .env
# o
code .env  # Si usas VS Code
```

### 6.2 Configurar credenciales

Edita el archivo `.env` con tus credenciales:

```bash
# ========================================
# CONFIGURACIÓN DE FRESHDESK
# ========================================

# Obtén tu API Key desde: https://tudominio.freshdesk.com/a/admin/api_settings
API_KEY=tu_api_key_de_freshdesk

# Tu dominio de Freshdesk (sin https:// y sin .freshdesk.com)
DOMAIN=pocsctbnk

# ========================================
# CONFIGURACIÓN DE BASE DE DATOS
# ========================================

# Configuración de MariaDB
DB_HOST=localhost
DB_USER=nico
DB_PASSWORD=tu_password  # La que configuraste en el paso 5.2
DB_NAME=bank
DB_PORT=3306

# ========================================
# CONFIGURACIÓN DE RASA PRO (OPCIONAL)
# ========================================

RASA_TOKEN=tu_rasa_token_aqui  # Si tienes licencia de Rasa Pro

# ========================================
# CONFIGURACIÓN DE LOGGING
# ========================================

LOG_LEVEL=INFO
LOG_FILE=./logs/rasa.log
```

### 6.3 Verificar configuración

```bash
# Probar conexión a base de datos
python test_customer_lookup.py

# Debe mostrar los clientes registrados
```

---

## 7. Entrenar Modelo de Rasa

### 7.1 Validar datos de entrenamiento

```bash
# Validar que no haya errores en los datos
rasa data validate

# Si hay warnings, léelos y corrígelos si es necesario
```

### 7.2 Entrenar modelo

```bash
# Entrenar modelo completo
rasa train

# Esto puede tomar varios minutos
# Una vez completado, verás un mensaje indicando el nombre del modelo
```

**Output esperado:**
```
✅ Your Rasa model is trained and saved at 'models/20250109-123456-fresh-interest.tar.gz'.
```

### 7.3 Verificar modelo

```bash
# Verificar que se generó el modelo
ls -lh models/

# Debe haber al menos un archivo .tar.gz
```

---

## 8. Lanzar Servicios

El sistema requiere **3 servicios** ejecutándose simultáneamente. Abre **3 terminales** diferentes:

### Terminal 1: Rasa Action Server

Este servidor maneja todas las acciones personalizadas (saludos, generación de tickets, etc.)

```bash
# Activar entorno virtual
source venv/bin/activate

# Lanzar Action Server
rasa run actions --port 5055 --debug
```

**Verificación:**
- Debe mostrar: `Rasa SDK is up and running on http://0.0.0.0:5055`
- Puerto: `5055`
- Modo: `--debug` para ver logs detallados

### Terminal 2: Rasa Server

Este es el servidor principal de Rasa que procesa las conversaciones.

```bash
# Activar entorno virtual
source venv/bin/activate

# Lanzar Rasa Server
rasa run --enable-api --cors "*" --port 5005 --debug
```

**Verificación:**
- Debe mostrar: `Rasa server is up and running`
- Puerto: `5005`
- API habilitada para comunicación con otros servicios

### Terminal 3: Twilio Voice Server

Este servidor intermediario maneja la comunicación con Twilio (voz).

```bash
# Activar entorno virtual
source venv/bin/activate

# Lanzar servidor Twilio
python twilio_voice_server.py
```

**Verificación:**
- Debe mostrar: `🚀 Servidor Twilio Voice iniciado en http://0.0.0.0:5000`
- Puerto: `5000`
- Endpoints disponibles:
  - `/webhook/twilio/voice` - Manejo de llamadas entrantes
  - `/webhook/twilio/speech` - Procesamiento de voz a texto

### 8.1 Verificar que todos los servicios estén corriendo

```bash
# En una cuarta terminal
# Verificar puertos ocupados
lsof -i :5000  # Twilio Voice Server
lsof -i :5005  # Rasa Server
lsof -i :5055  # Rasa Action Server

# Todos deben mostrar procesos de Python corriendo
```

### 8.2 Logs esperados

**Action Server (Terminal 1):**
```
INFO:rasa_sdk.endpoint:Registered function for 'action_saludo_contextual'.
INFO:rasa_sdk.endpoint:Registered function for 'action_generar_ticket'.
INFO:rasa_sdk.endpoint:Rasa SDK is up and running on http://0.0.0.0:5055
```

**Rasa Server (Terminal 2):**
```
INFO:rasa.core.agent:Model loaded.
INFO:rasa.core.http_interpreter:Rasa server is up and running.
```

**Twilio Server (Terminal 3):**
```
🚀 Servidor Twilio Voice iniciado en http://0.0.0.0:5000
📱 Identificación de clientes: ACTIVA
🗄️  Base de datos: Conectada
```

---

## 9. Testing del Sistema

### 9.1 Testing rápido con script automatizado

El proyecto incluye un script de testing completo:

```bash
# Testing con cliente conocido (Mauricio)
./test_conversation.sh +56982079489

# Testing con cliente desconocido
./test_conversation.sh +56912345678
```

**El script probará:**
1. ✅ Saludo inicial (personalizado si el cliente existe)
2. ✅ Intención de bloqueo: "quiero bloquear mi tarjeta"
3. ✅ Validación de dígitos: "1234"
4. ✅ Confirmación: "sí"
5. ✅ Generación de ticket en Freshdesk
6. ✅ Despedida contextual

### 9.2 Testing interactivo con Rasa Shell

```bash
# En una nueva terminal con el entorno activado
rasa shell --debug

# Probar conversación manualmente:
# Usuario: quiero bloquear mi tarjeta
# Bot: ¡Buenas tardes! Soy el asistente de Scotiabank...
# Usuario: 1234
# Bot: Perfecto, encontré tu tarjeta terminada en 1234...
# Usuario: sí
# Bot: Excelente, se ha generado el caso número BLK-20250109-XX...
```

### 9.3 Testing de identificación de clientes

```bash
# Script específico para probar lookup de clientes
python test_customer_lookup.py
```

### 9.4 Verificar tickets en Freshdesk

1. Accede a tu cuenta de Freshdesk: `https://tudominio.freshdesk.com`
2. Ve a la sección de Tickets
3. Busca tickets con formato: `BLK-YYYYMMDD-XX`
4. Verifica que contengan toda la información del cliente

### 9.5 Testing de todos los escenarios

```bash
# Script que prueba múltiples escenarios
./test_all_scenarios.sh
```

---

## 10. Solución de Problemas

### 10.1 Error: "Port already in use"

**Problema:** Uno de los puertos (5000, 5005, 5055) ya está ocupado.

**Solución:**
```bash
# Identificar proceso que usa el puerto
lsof -i :5005  # Cambia el puerto según el error

# Matar proceso (reemplaza PID con el número mostrado)
kill -9 PID

# O encontrar y matar todos los procesos de Rasa
pkill -f rasa
pkill -f twilio_voice_server
```

### 10.2 Error: "No module named 'rasa'"

**Problema:** Rasa no está instalado o el entorno virtual no está activado.

**Solución:**
```bash
# Activar entorno virtual
source venv/bin/activate

# Reinstalar Rasa
pip install -r requirements.txt

# Verificar
rasa --version
```

### 10.3 Error de conexión a base de datos

**Problema:** No se puede conectar a MariaDB.

**Solución:**
```bash
# Verificar que MariaDB esté corriendo
# macOS:
brew services list | grep mariadb

# Ubuntu/Debian:
sudo systemctl status mariadb

# Iniciar si está detenido:
# macOS:
brew services start mariadb

# Ubuntu/Debian:
sudo systemctl start mariadb

# Verificar credenciales en .env
cat .env | grep DB_

# Probar conexión manualmente
mysql -u nico -p bank
```

### 10.4 Error: "Model not found"

**Problema:** No hay modelo entrenado o no se encuentra.

**Solución:**
```bash
# Verificar modelos existentes
ls -lh models/

# Entrenar nuevo modelo
rasa train

# Si persiste el error, especifica el modelo manualmente
rasa run --model models/nombre-del-modelo.tar.gz
```

### 10.5 Error en Freshdesk API

**Problema:** No se pueden crear tickets en Freshdesk.

**Solución:**
```bash
# Verificar API Key en .env
cat .env | grep API_KEY

# Probar conexión manualmente
curl -v https://tudominio.freshdesk.com/api/v2/tickets \
  -u tu_api_key:X \
  -H "Content-Type: application/json"

# Si obtienes 401: API Key incorrecta
# Si obtienes 403: Permisos insuficientes
# Si obtienes 200: Conexión OK
```

### 10.6 Problemas con spaCy

**Problema:** Error relacionado con modelos de spaCy.

**Solución:**
```bash
# Descargar modelo en español
python -m spacy download es_core_news_sm

# Verificar instalación
python -c "import spacy; nlp = spacy.load('es_core_news_sm'); print('✅ spaCy OK')"
```

### 10.7 Logs para debugging

```bash
# Ver logs de Action Server
# (los logs aparecen en la Terminal 1)

# Ver logs de Rasa Server
# (los logs aparecen en la Terminal 2)

# Ver logs de Twilio Server
# (los logs aparecen en la Terminal 3)

# Para guardar logs en archivos:
# Terminal 1:
rasa run actions --port 5055 --debug 2>&1 | tee logs/actions.log

# Terminal 2:
rasa run --enable-api --cors "*" --port 5005 --debug 2>&1 | tee logs/rasa.log

# Terminal 3:
python twilio_voice_server.py 2>&1 | tee logs/twilio.log
```

### 10.8 Comando para limpiar y reiniciar

Si todo falla, intenta un reinicio completo:

```bash
# Matar todos los procesos
pkill -f rasa
pkill -f twilio_voice_server

# Limpiar modelos antiguos (opcional)
rm -rf models/*

# Re-entrenar
rasa train

# Reiniciar servicios (en 3 terminales separadas)
# Terminal 1: rasa run actions --port 5055 --debug
# Terminal 2: rasa run --enable-api --cors "*" --port 5005 --debug
# Terminal 3: python twilio_voice_server.py
```

---

## 🎯 Comandos de Referencia Rápida

```bash
# Activar entorno
source venv/bin/activate

# Entrenar modelo
rasa train

# Validar datos
rasa data validate

# Testing interactivo
rasa shell

# Ver versión
rasa --version

# Lanzar servicios
rasa run actions --port 5055 --debug
rasa run --enable-api --cors "*" --port 5005 --debug
python twilio_voice_server.py

# Testing automático
./test_conversation.sh +56982079489
```

---

## 📚 Próximos Pasos

Una vez que tengas el sistema funcionando:

1. **Configurar Twilio** - Conectar con número real de Twilio
2. **Despliegue en producción** - Usar gunicorn y configurar servidor
3. **Monitoreo** - Implementar logging y alertas
4. **Optimización** - Ajustar tiempos de respuesta y parámetros

Consulta la documentación adicional:
- `QUICKSTART.md` - Comandos rápidos
- `FLUJO_CONVERSACIONAL.md` - Diagramas del flujo
- `memory-bank/` - Documentación técnica completa

---

## 💡 Consejos Útiles

1. **Siempre activa el entorno virtual** antes de trabajar con el proyecto
2. **Mantén 3 terminales abiertas** para monitorear los servicios
3. **Revisa los logs** regularmente para detectar problemas temprano
4. **Usa el modo --debug** durante desarrollo para ver información detallada
5. **Haz backups** de tu base de datos regularmente

---

## 🤝 Soporte

Si encuentras problemas no cubiertos en esta guía:

1. Revisa los logs de los 3 servicios
2. Verifica que todas las dependencias estén instaladas
3. Consulta la documentación en `memory-bank/`
4. Revisa los issues en GitHub

---

**¡Felicidades! Has completado la configuración del sistema.** 🎉

