#!/bin/bash

echo "=========================================="
echo "📊 CARGANDO DATOS EN CLOUD SQL"
echo "=========================================="
echo ""

echo "1️⃣  Conectando a Cloud SQL..."
echo "   Nombre instancia: voicebot-db"
echo "   Usuario: root"
echo ""

# Crear archivo temporal con SQL
cat > /tmp/setup_cloud_sql.sql << 'SQL'
-- Usar base de datos bank
USE bank;

-- Crear tabla si no existe
CREATE TABLE IF NOT EXISTS customers (
    id VARCHAR(36) PRIMARY KEY,
    rut VARCHAR(9) NOT NULL UNIQUE,
    nombre VARCHAR(64) NOT NULL,
    nombre_completo VARCHAR(128) NOT NULL,
    telefono VARCHAR(12) NOT NULL UNIQUE,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insertar datos de prueba (si no existen)
INSERT IGNORE INTO customers (id, rut, nombre, nombre_completo, telefono) VALUES
(UUID(), '87654321', 'Nicolas', 'Nicolas Navarro Aravena', '+56984593400'),
(UUID(), '12345678', 'Mauricio', 'Mauricio González López', '+56982079489'),
(UUID(), '98765432', 'María', 'María Fernández Silva', '+56987654321'),
(UUID(), '55556666', 'Carlos', 'Carlos Rodríguez Pérez', '+56955556666');

-- Verificar datos cargados
SELECT 'Datos cargados exitosamente:' as mensaje;
SELECT telefono, nombre, rut FROM customers;
SQL

echo "2️⃣  Ejecutando script SQL..."
echo ""
echo "📝 SQL que se ejecutará:"
cat /tmp/setup_cloud_sql.sql
echo ""
echo "=========================================="
echo ""
echo "⚠️  EJECUTA ESTE COMANDO EN TU TERMINAL:"
echo ""
echo "gcloud sql connect voicebot-db --user=root --quiet < /tmp/setup_cloud_sql.sql"
echo ""
echo "=========================================="
