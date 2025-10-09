# ⚡ Quick Start - Bloqueo SCTBNK Voice

Guía rápida para usuarios avanzados. Para documentación completa, consulta [SETUP.md](SETUP.md).

## 🚀 Setup en 5 Minutos

### 1. Clonar e Instalar

```bash
# Clonar repositorio
git clone https://github.com/nicolasnavarro-2brains/bloqueo-sctbnk-voice.git
cd bloqueo-sctbnk-voice

# Crear y activar entorno virtual
python -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows

# Instalar dependencias
pip install --upgrade pip
pip install -r requirements.txt
pip install -r twilio_requirements.txt

# Descargar modelo spaCy
python -m spacy download es_core_news_sm
```

### 2. Configurar Base de Datos

```bash
# Conectar a MariaDB
mysql -u root -p

# Ejecutar en MySQL:
CREATE DATABASE IF NOT EXISTS bank CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'nico'@'localhost' IDENTIFIED BY 'tu_password';
GRANT ALL PRIVILEGES ON bank.* TO 'nico'@'localhost';
FLUSH PRIVILEGES;
EXIT;

# Configurar datos de prueba
cp env.example .env
# Editar .env con tus credenciales
python setup_test_data.py
```

### 3. Configurar Variables de Entorno

```bash
# Editar .env
nano .env
```

**Mínimo requerido:**
```bash
# Freshdesk
API_KEY=tu_api_key
DOMAIN=tu_dominio

# Base de datos
DB_HOST=localhost
DB_USER=nico
DB_PASSWORD=tu_password
DB_NAME=bank
DB_PORT=3306
```

### 4. Entrenar Modelo

```bash
rasa train
```

### 5. Lanzar Sistema (3 Terminales)

**Terminal 1:**
```bash
source venv/bin/activate
rasa run actions --port 5055 --debug
```

**Terminal 2:**
```bash
source venv/bin/activate
rasa run --enable-api --cors "*" --port 5005 --debug
```

**Terminal 3:**
```bash
source venv/bin/activate
python twilio_voice_server.py
```

### 6. Probar

```bash
# Testing automático
./test_conversation.sh +56982079489

# Testing interactivo
rasa shell
```

---

## 📝 Comandos de Un Solo Paso

### Setup Completo (Copy-Paste)

```bash
# ⚠️ Asegúrate de tener Python 3.10.12 y MariaDB instalados

# Setup completo
git clone https://github.com/kaolong/bloqueo-sctbnk-voice.git && \
cd bloqueo-sctbnk-voice && \
python -m venv venv && \
source venv/bin/activate && \
pip install --upgrade pip && \
pip install -r requirements.txt && \
pip install -r twilio_requirements.txt && \
python -m spacy download es_core_news_sm && \
cp env.example .env && \
echo "✅ Setup completado. Ahora edita .env y ejecuta python setup_test_data.py"
```

### Lanzar Sistema (Script)

Guarda esto como `start_system.sh`:

```bash
#!/bin/bash

# Activar entorno
source venv/bin/activate

echo "🚀 Iniciando sistema completo..."

# Terminal 1: Action Server
osascript -e 'tell app "Terminal" to do script "cd '$(pwd)' && source venv/bin/activate && rasa run actions --port 5055 --debug"'

# Esperar 5 segundos
sleep 5

# Terminal 2: Rasa Server
osascript -e 'tell app "Terminal" to do script "cd '$(pwd)' && source venv/bin/activate && rasa run --enable-api --cors \"*\" --port 5005 --debug"'

# Esperar 10 segundos
sleep 10

# Terminal 3: Twilio Server
osascript -e 'tell app "Terminal" to do script "cd '$(pwd)' && source venv/bin/activate && python twilio_voice_server.py"'

echo "✅ Sistema iniciado en 3 terminales"
```

Usar:
```bash
chmod +x start_system.sh
./start_system.sh
```

---

## 🔧 Comandos Útiles

### Gestión de Servicios

```bash
# Ver puertos ocupados
lsof -i :5000  # Twilio
lsof -i :5005  # Rasa
lsof -i :5055  # Actions

# Matar todos los servicios
pkill -f rasa
pkill -f twilio_voice_server

# Matar proceso específico
kill -9 $(lsof -ti:5005)
```

### Base de Datos

```bash
# Conectar a BD
mysql -u nico -p bank

# Ver clientes
mysql -u nico -p bank -e "SELECT * FROM customers;"

# Re-inicializar datos
python setup_test_data.py

# Verificar conexión
python test_customer_lookup.py
```

### Modelo de Rasa

```bash
# Entrenar
rasa train

# Validar datos
rasa data validate

# Ver modelos
ls -lh models/

# Eliminar modelos antiguos
rm -rf models/*.tar.gz

# Testing interactivo
rasa shell --debug

# Testing con modelo específico
rasa shell --model models/nombre-modelo.tar.gz
```

### Testing

```bash
# Cliente conocido
./test_conversation.sh +56982079489

# Cliente desconocido
./test_conversation.sh +56912345678

# Todos los escenarios
./test_all_scenarios.sh

# Shell interactivo
rasa shell

# Debug del servidor
python debug_server.py
```

---

## 🐛 Troubleshooting Rápido

### Puerto ocupado
```bash
kill -9 $(lsof -ti:5005)
```

### No encuentra módulo
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Error de BD
```bash
# Verificar servicio
brew services list | grep mariadb        # macOS
sudo systemctl status mariadb            # Linux

# Iniciar servicio
brew services start mariadb              # macOS
sudo systemctl start mariadb             # Linux

# Probar conexión
mysql -u nico -p bank
```

### Modelo no encontrado
```bash
rasa train
```

### Error de Freshdesk
```bash
# Verificar API Key
curl -v https://tudominio.freshdesk.com/api/v2/tickets \
  -u tu_api_key:X \
  -H "Content-Type: application/json"
```

### Reinicio completo
```bash
# Matar todo
pkill -f rasa
pkill -f twilio_voice_server

# Re-entrenar
rasa train

# Reiniciar servicios
# Terminal 1: rasa run actions --port 5055 --debug
# Terminal 2: rasa run --enable-api --cors "*" --port 5005 --debug
# Terminal 3: python twilio_voice_server.py
```

---

## 📊 Verificación del Sistema

### Checklist de Servicios

- [ ] MariaDB corriendo en puerto 3306
- [ ] Action Server corriendo en puerto 5055
- [ ] Rasa Server corriendo en puerto 5005
- [ ] Twilio Server corriendo en puerto 5000
- [ ] Base de datos `bank` creada
- [ ] Tabla `customers` con datos de prueba
- [ ] Variables de entorno configuradas en `.env`
- [ ] Modelo entrenado en `models/`

### Comando de Verificación

```bash
# Verificar todo de una vez
echo "🔍 Verificando sistema..."

# Python
python --version | grep "3.10" && echo "✅ Python 3.10" || echo "❌ Python 3.10"

# Rasa
rasa --version | grep "3.13" && echo "✅ Rasa 3.13" || echo "❌ Rasa 3.13"

# MariaDB
mysql -u nico -p bank -e "SELECT COUNT(*) FROM customers;" && echo "✅ Base de datos OK" || echo "❌ Base de datos"

# Puertos
lsof -i :5000 >/dev/null && echo "✅ Puerto 5000 (Twilio)" || echo "❌ Puerto 5000"
lsof -i :5005 >/dev/null && echo "✅ Puerto 5005 (Rasa)" || echo "❌ Puerto 5005"
lsof -i :5055 >/dev/null && echo "✅ Puerto 5055 (Actions)" || echo "❌ Puerto 5055"

# Modelo
ls models/*.tar.gz >/dev/null 2>&1 && echo "✅ Modelo entrenado" || echo "❌ Modelo no encontrado"
```

---

## 🎯 Flujo de Trabajo Diario

### Al Iniciar

```bash
# 1. Activar entorno
source venv/bin/activate

# 2. Actualizar código
git pull

# 3. Verificar dependencias
pip install -r requirements.txt

# 4. Re-entrenar si hay cambios
rasa train

# 5. Lanzar servicios (3 terminales)
# Terminal 1: rasa run actions --port 5055 --debug
# Terminal 2: rasa run --enable-api --cors "*" --port 5005 --debug
# Terminal 3: python twilio_voice_server.py
```

### Al Finalizar

```bash
# Matar servicios
pkill -f rasa
pkill -f twilio_voice_server

# Desactivar entorno
deactivate
```

### Hacer Cambios

```bash
# 1. Editar archivos (data/flows.yml, data/nlu.yml, actions/actions.py)

# 2. Validar
rasa data validate

# 3. Re-entrenar
rasa train

# 4. Probar
rasa shell

# 5. Commit
git add .
git commit -m "Descripción de cambios"
git push
```

---

## 📚 Archivos de Configuración Clave

| Archivo | Descripción |
|---------|-------------|
| `config.yml` | Pipeline NLU y políticas |
| `domain/shared.yml` | Intents, slots, responses, actions |
| `data/flows.yml` | Flujos conversacionales CALM |
| `data/nlu.yml` | Ejemplos de entrenamiento |
| `data/rules.yml` | Reglas de activación |
| `actions/actions.py` | Acciones personalizadas |
| `endpoints.yml` | Configuración de endpoints |
| `.env` | Variables de entorno |
| `twilio_voice_server.py` | Servidor intermediario Twilio |

---

## 🚀 Testing por Componente

### Testing de NLU

```bash
# Shell interactivo
rasa shell nlu

# Ejemplos:
# User: quiero bloquear mi tarjeta
# User: perdí mi tarjeta
# User: 1234
# User: sí
```

### Testing de Actions

```bash
# Lanzar action server con logs
rasa run actions --port 5055 --debug

# En otra terminal, probar endpoint
curl -X POST http://localhost:5055/webhook \
  -H "Content-Type: application/json" \
  -d '{"next_action": "action_saludo_contextual"}'
```

### Testing de Flows

```bash
# Shell interactivo con debug
rasa shell --debug

# Probar flujo completo
```

### Testing de Integración

```bash
# Script completo
./test_conversation.sh +56982079489

# O escenarios específicos
./test_all_scenarios.sh
```

---

## 🔗 Enlaces Útiles

- **Documentación completa:** [SETUP.md](SETUP.md)
- **Flujo conversacional:** [FLUJO_CONVERSACIONAL.md](FLUJO_CONVERSACIONAL.md)
- **Memory Bank:** [memory-bank/README.md](memory-bank/README.md)
- **Rasa Docs:** https://rasa.com/docs/rasa/
- **Twilio Docs:** https://www.twilio.com/docs/voice
- **Freshdesk API:** https://developers.freshdesk.com/api/

---

## 💡 Tips Pro

1. **Alias útiles** (añadir a `.bashrc` o `.zshrc`):

```bash
alias rasa-activate='source venv/bin/activate'
alias rasa-actions='rasa run actions --port 5055 --debug'
alias rasa-server='rasa run --enable-api --cors "*" --port 5005 --debug'
alias rasa-twilio='python twilio_voice_server.py'
alias rasa-test='./test_conversation.sh +56982079489'
alias rasa-kill='pkill -f rasa && pkill -f twilio_voice_server'
```

2. **Script de desarrollo** (`dev.sh`):

```bash
#!/bin/bash
source venv/bin/activate
rasa train && echo "✅ Modelo entrenado" && rasa shell
```

3. **Monitoreo de logs en tiempo real**:

```bash
# En una terminal separada
tail -f logs/*.log
```

4. **Backup de BD**:

```bash
mysqldump -u nico -p bank > backup_$(date +%Y%m%d).sql
```

---

**¿Problemas?** Consulta [SETUP.md](SETUP.md) para documentación completa o revisa [Troubleshooting](#-troubleshooting-rápido).

