#!/usr/bin/env python3
"""
Script para probar la conexión a la base de datos
"""
import os
import pymysql
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

print("\n" + "="*60)
print("PRUEBA DE CONEXIÓN A BASE DE DATOS")
print("="*60)

# Mostrar configuración
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'nico'),
    'password': os.getenv('DB_PASSWORD', 'nico'),
    'database': os.getenv('DB_NAME', 'bank'),
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

print("\n📋 Configuración de BD:")
print(f"   Host: {DB_CONFIG['host']}")
print(f"   User: {DB_CONFIG['user']}")
print(f"   Password: {'*' * len(DB_CONFIG['password'])}")
print(f"   Database: {DB_CONFIG['database']}")
print("")

# Intentar conectar
try:
    print("🔌 Intentando conectar...")
    connection = pymysql.connect(**DB_CONFIG)
    print("✅ CONEXIÓN EXITOSA!")
    
    # Verificar tabla customers
    with connection.cursor() as cursor:
        cursor.execute("SHOW TABLES;")
        tables = cursor.fetchall()
        print(f"\n📊 Tablas en la base de datos:")
        for table in tables:
            table_name = list(table.values())[0]
            print(f"   - {table_name}")
        
        # Verificar si existe la tabla customers
        cursor.execute("SHOW TABLES LIKE 'customers';")
        customer_table = cursor.fetchone()
        
        if customer_table:
            print("\n✅ Tabla 'customers' encontrada")
            
            # Contar clientes
            cursor.execute("SELECT COUNT(*) as total FROM customers;")
            result = cursor.fetchone()
            total = result['total']
            print(f"   Total de clientes registrados: {total}")
            
            # Mostrar clientes
            if total > 0:
                cursor.execute("SELECT nombre, telefono FROM customers;")
                customers = cursor.fetchall()
                print("\n📱 Clientes registrados:")
                for customer in customers:
                    print(f"   - {customer['nombre']}: {customer['telefono']}")
            
            # Buscar tu número específico
            print("\n🔍 Buscando número +56984593400...")
            cursor.execute("SELECT * FROM customers WHERE telefono = %s;", ('+56984593400',))
            result = cursor.fetchone()
            
            if result:
                print("✅ NÚMERO ENCONTRADO:")
                print(f"   ID: {result['id']}")
                print(f"   RUT: {result['rut']}")
                print(f"   Nombre: {result['nombre']}")
                print(f"   Nombre Completo: {result['nombre_completo']}")
                print(f"   Teléfono: {result['telefono']}")
            else:
                print("❌ Número NO encontrado en la base de datos")
                print("   Ejecuta: python setup_test_data.py")
        else:
            print("\n❌ Tabla 'customers' NO existe")
            print("   Ejecuta: python setup_test_data.py")
    
    connection.close()
    print("\n" + "="*60)
    print("✅ CONEXIÓN A BD: OK")
    print("="*60 + "\n")
    
except pymysql.err.OperationalError as e:
    print(f"\n❌ ERROR DE CONEXIÓN:")
    print(f"   {e}")
    print("\n💡 Posibles soluciones:")
    print("   1. Verifica que MariaDB esté corriendo:")
    print("      brew services list | grep mariadb")
    print("   2. Verifica las credenciales en .env")
    print("   3. Intenta conectar manualmente:")
    print(f"      mysql -u {DB_CONFIG['user']} -p {DB_CONFIG['database']}")
    print("")
    
except Exception as e:
    print(f"\n❌ ERROR:")
    print(f"   {e}")
    print("")

