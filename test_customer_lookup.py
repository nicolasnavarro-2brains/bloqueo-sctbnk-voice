#!/usr/bin/env python3
"""
Script simple para probar la búsqueda de clientes por número de teléfono
"""

import os
import pymysql
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def test_customer_lookup():
    """Prueba la búsqueda de clientes"""
    print("🔍 Probando búsqueda de clientes...")
    
    # Configuración de base de datos
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'user': os.getenv('DB_USER', 'mauro'),
        'password': os.getenv('DB_PASSWORD', 'santiago01'),
        'database': os.getenv('DB_NAME', 'bank'),
        'charset': 'utf8mb4',
        'cursorclass': pymysql.cursors.DictCursor
    }
    
    print(f"📊 Configuración BD: {db_config['host']}:{db_config['database']}")
    
    try:
        # Conectar a la base de datos
        connection = pymysql.connect(**db_config)
        print("✅ Conexión exitosa a la base de datos")
        
        with connection.cursor() as cursor:
            # Probar diferentes formatos de teléfono
            test_phones = [
                '+56982221070',
                '56982221070',
                '+56987654321',
                '56987654321',
                '+56912345678',
                '56912345678',
                '+56984593400',
            ]
            
            for phone in test_phones:
                print(f"\n📱 Probando teléfono: {phone}")
                
                # Buscar cliente
                sql = """
                SELECT id, rut, nombre, nombre_completo, telefono, fecha_creacion
                FROM customers 
                WHERE telefono = %s
                """
                cursor.execute(sql, (phone,))
                customer = cursor.fetchone()
                
                if customer:
                    print(f"✅ Cliente encontrado: {customer['nombre_completo']}")
                    print(f"   📱 Teléfono en BD: {customer['telefono']}")
                    print(f"   👤 Nombre: {customer['nombre']}")
                else:
                    print(f"❌ Cliente no encontrado")
                
                # También probar con LIKE para ver si hay diferencias de formato
                sql_like = """
                SELECT id, rut, nombre, nombre_completo, telefono, fecha_creacion
                FROM customers 
                WHERE telefono LIKE %s
                """
                cursor.execute(sql_like, (f"%{phone.replace('+', '')}%",))
                customers_like = cursor.fetchall()
                
                if customers_like:
                    print(f"🔍 Con LIKE se encontraron {len(customers_like)} clientes:")
                    for c in customers_like:
                        print(f"   - {c['nombre_completo']} ({c['telefono']})")
                else:
                    print(f"🔍 Con LIKE tampoco se encontraron clientes")
        
        connection.close()
        print("\n🔌 Conexión cerrada")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_customer_lookup()
