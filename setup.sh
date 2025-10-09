#!/bin/bash

# ========================================
# SETUP AUTOMÁTICO - BLOQUEO SCTBNK VOICE
# ========================================
# Script de instalación y configuración automática
# Autor: Mauricio Martínez
# Proyecto: Sistema de Asistente Virtual para Bloqueo de Tarjetas

set -e  # Salir si hay algún error

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Funciones de utilidad
print_header() {
    echo -e "${BLUE}"
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║     SETUP AUTOMÁTICO - BLOQUEO SCTBNK VOICE                    ║"
    echo "║     Sistema de Asistente Virtual con Rasa Pro 3.13.5          ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_step() {
    echo -e "${BLUE}▶ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Función para verificar si un comando existe
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Función para verificar versión de Python
check_python_version() {
    if command_exists python3; then
        PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
        PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
        PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
        
        if [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -ge 10 ]; then
            return 0
        fi
    fi
    return 1
}

# Inicio del script
clear
print_header

echo "Este script te guiará por el proceso de instalación completo."
echo "Asegúrate de tener Python 3.10+ y MariaDB instalados."
echo ""
read -p "¿Deseas continuar? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Instalación cancelada."
    exit 1
fi

# ========================================
# 1. VERIFICAR PRERREQUISITOS
# ========================================
print_step "1. Verificando prerrequisitos..."

# Verificar Python 3.10+
if check_python_version; then
    print_success "Python 3.10+ encontrado: $(python3 --version)"
else
    print_error "Python 3.10 o superior no encontrado."
    echo "Por favor instala Python 3.10.12 antes de continuar."
    echo ""
    echo "Opciones:"
    echo "  - Usar pyenv: pyenv install 3.10.12 && pyenv local 3.10.12"
    echo "  - macOS: brew install python@3.10"
    echo "  - Ubuntu: sudo apt install python3.10"
    exit 1
fi

# Verificar pip
if command_exists pip3; then
    print_success "pip3 encontrado"
else
    print_error "pip3 no encontrado"
    echo "Instalando pip..."
    python3 -m ensurepip --upgrade
fi

# Verificar git
if command_exists git; then
    print_success "git encontrado"
else
    print_warning "git no encontrado (opcional, pero recomendado)"
fi

# Verificar MariaDB/MySQL
if command_exists mysql; then
    print_success "MySQL/MariaDB encontrado"
else
    print_warning "MySQL/MariaDB no encontrado"
    echo "Por favor instala MariaDB antes de continuar:"
    echo "  - macOS: brew install mariadb && brew services start mariadb"
    echo "  - Ubuntu: sudo apt install mariadb-server"
    echo ""
    read -p "¿Deseas continuar de todas formas? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo ""

# ========================================
# 2. CREAR ENTORNO VIRTUAL
# ========================================
print_step "2. Creando entorno virtual..."

if [ -d "venv" ]; then
    print_warning "Entorno virtual ya existe"
    read -p "¿Deseas recrearlo? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf venv
        python3 -m venv venv
        print_success "Entorno virtual recreado"
    else
        print_success "Usando entorno virtual existente"
    fi
else
    python3 -m venv venv
    print_success "Entorno virtual creado"
fi

# Activar entorno virtual
source venv/bin/activate
print_success "Entorno virtual activado"

echo ""

# ========================================
# 3. ACTUALIZAR PIP
# ========================================
print_step "3. Actualizando pip..."

pip install --upgrade pip --quiet
print_success "pip actualizado a versión $(pip --version | awk '{print $2}')"

echo ""

# ========================================
# 4. INSTALAR DEPENDENCIAS
# ========================================
print_step "4. Instalando dependencias..."

echo "   📦 Instalando dependencias principales de Rasa..."
if pip install -r requirements.txt --quiet; then
    print_success "Dependencias principales instaladas"
else
    print_error "Error instalando dependencias principales"
    exit 1
fi

echo "   📦 Instalando dependencias del servidor Twilio..."
if pip install -r twilio_requirements.txt --quiet; then
    print_success "Dependencias de Twilio instaladas"
else
    print_error "Error instalando dependencias de Twilio"
    exit 1
fi

echo "   📦 Descargando modelo de spaCy en español..."
if python -m spacy download es_core_news_sm --quiet; then
    print_success "Modelo de spaCy descargado"
else
    print_error "Error descargando modelo de spaCy"
    exit 1
fi

echo ""

# ========================================
# 5. CONFIGURAR VARIABLES DE ENTORNO
# ========================================
print_step "5. Configurando variables de entorno..."

if [ -f ".env" ]; then
    print_warning "Archivo .env ya existe"
    read -p "¿Deseas sobrescribirlo? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cp env.example .env
        print_success "Archivo .env sobrescrito desde env.example"
    else
        print_success "Usando archivo .env existente"
    fi
else
    cp env.example .env
    print_success "Archivo .env creado desde env.example"
fi

echo ""
print_warning "IMPORTANTE: Debes editar el archivo .env con tus credenciales"
echo "   - API_KEY: Tu API Key de Freshdesk"
echo "   - DOMAIN: Tu dominio de Freshdesk"
echo "   - DB_PASSWORD: La contraseña de tu base de datos"
echo ""
read -p "¿Deseas editar .env ahora? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if command_exists nano; then
        nano .env
    elif command_exists vim; then
        vim .env
    elif command_exists vi; then
        vi .env
    else
        echo "No se encontró editor de texto. Edita .env manualmente."
    fi
else
    print_warning "Recuerda editar .env antes de ejecutar el sistema"
fi

echo ""

# ========================================
# 6. CONFIGURAR BASE DE DATOS
# ========================================
print_step "6. Configurando base de datos..."

if command_exists mysql; then
    echo ""
    echo "Ahora vamos a configurar la base de datos MariaDB."
    echo ""
    read -p "¿Deseas configurar la base de datos ahora? (y/n): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo ""
        echo "Ejecuta estos comandos en MySQL (se abrirá en un momento):"
        echo ""
        echo "CREATE DATABASE IF NOT EXISTS bank CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
        echo "CREATE USER IF NOT EXISTS 'nico'@'localhost' IDENTIFIED BY 'tu_password';"
        echo "GRANT ALL PRIVILEGES ON bank.* TO 'nico'@'localhost';"
        echo "FLUSH PRIVILEGES;"
        echo "EXIT;"
        echo ""
        read -p "Presiona Enter para abrir MySQL..."
        
        mysql -u root -p
        
        print_success "Base de datos configurada"
        
        echo ""
        read -p "¿Deseas cargar datos de prueba? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            if python setup_test_data.py; then
                print_success "Datos de prueba cargados exitosamente"
            else
                print_error "Error cargando datos de prueba"
                print_warning "Verifica tu configuración en .env"
            fi
        fi
    else
        print_warning "Recuerda configurar la base de datos manualmente"
    fi
else
    print_warning "MySQL/MariaDB no encontrado, saltando configuración de BD"
fi

echo ""

# ========================================
# 7. ENTRENAR MODELO DE RASA
# ========================================
print_step "7. Entrenando modelo de Rasa..."

echo "   🧠 Esto puede tomar varios minutos..."
if rasa train; then
    print_success "Modelo entrenado exitosamente"
    
    # Mostrar modelo generado
    LATEST_MODEL=$(ls -t models/*.tar.gz 2>/dev/null | head -1)
    if [ -n "$LATEST_MODEL" ]; then
        MODEL_SIZE=$(du -h "$LATEST_MODEL" | cut -f1)
        echo "   📦 Modelo generado: $(basename $LATEST_MODEL) ($MODEL_SIZE)"
    fi
else
    print_error "Error entrenando modelo"
    exit 1
fi

echo ""

# ========================================
# 8. VERIFICAR INSTALACIÓN
# ========================================
print_step "8. Verificando instalación..."

# Verificar Rasa
if command_exists rasa; then
    RASA_VERSION=$(rasa --version 2>&1 | head -1)
    print_success "Rasa: $RASA_VERSION"
else
    print_error "Rasa no encontrado"
fi

# Verificar módulos Python
if python -c "import rasa, flask, twilio, pymysql" 2>/dev/null; then
    print_success "Todas las dependencias Python instaladas"
else
    print_warning "Algunas dependencias Python faltan"
fi

# Verificar modelo
if ls models/*.tar.gz 1> /dev/null 2>&1; then
    print_success "Modelo de Rasa disponible"
else
    print_error "Modelo de Rasa no encontrado"
fi

# Verificar .env
if [ -f ".env" ]; then
    print_success "Archivo .env configurado"
else
    print_error "Archivo .env no encontrado"
fi

echo ""

# ========================================
# 9. RESUMEN Y PRÓXIMOS PASOS
# ========================================
print_header

echo -e "${GREEN}🎉 ¡INSTALACIÓN COMPLETADA EXITOSAMENTE!${NC}"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${BLUE}📋 PRÓXIMOS PASOS:${NC}"
echo ""
echo "1. ${YELLOW}Edita el archivo .env${NC} con tus credenciales reales:"
echo "   nano .env"
echo ""
echo "2. ${YELLOW}Lanza los 3 servicios${NC} (en 3 terminales separadas):"
echo ""
echo "   ${GREEN}Terminal 1 - Action Server:${NC}"
echo "   source venv/bin/activate"
echo "   rasa run actions --port 5055 --debug"
echo ""
echo "   ${GREEN}Terminal 2 - Rasa Server:${NC}"
echo "   source venv/bin/activate"
echo "   rasa run --enable-api --cors \"*\" --port 5005 --debug"
echo ""
echo "   ${GREEN}Terminal 3 - Twilio Server:${NC}"
echo "   source venv/bin/activate"
echo "   python twilio_voice_server.py"
echo ""
echo "3. ${YELLOW}Prueba el sistema:${NC}"
echo "   ./test_conversation.sh +56982079489"
echo ""
echo "   O usa el shell interactivo:"
echo "   rasa shell"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${BLUE}📚 DOCUMENTACIÓN:${NC}"
echo ""
echo "   - SETUP.md       - Guía completa de instalación"
echo "   - QUICKSTART.md  - Comandos rápidos"
echo "   - README.md      - Documentación del proyecto"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${BLUE}💡 COMANDOS ÚTILES:${NC}"
echo ""
echo "   ${YELLOW}Activar entorno:${NC}      source venv/bin/activate"
echo "   ${YELLOW}Re-entrenar modelo:${NC}   rasa train"
echo "   ${YELLOW}Validar datos:${NC}        rasa data validate"
echo "   ${YELLOW}Testing:${NC}              ./test_conversation.sh +56982079489"
echo "   ${YELLOW}Shell interactivo:${NC}    rasa shell"
echo "   ${YELLOW}Matar servicios:${NC}      pkill -f rasa && pkill -f twilio_voice_server"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${BLUE}🆘 SOPORTE:${NC}"
echo ""
echo "   Si encuentras problemas, consulta:"
echo "   - SETUP.md (sección de Troubleshooting)"
echo "   - Logs de los servicios en las terminales"
echo "   - memory-bank/ (documentación técnica)"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${GREEN}✨ ¡Listo para empezar!${NC}"
echo ""

# Preguntar si desea ver el contenido de .env
read -p "¿Deseas ver el contenido actual de .env? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "CONTENIDO DE .env:"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    cat .env
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
fi

# Mensaje final
echo -e "${YELLOW}⚠️  RECUERDA: Edita .env con tus credenciales reales antes de ejecutar el sistema.${NC}"
echo ""

