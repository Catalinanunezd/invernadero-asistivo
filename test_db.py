"""
PROYECTO: Verificación de Conexión a MySQL en XAMPP
ARCHIVO: test_db.py
PROPÓSITO: Confirmar que MySQL está activo y que las tablas existen.
LENGUAJE: Python 3
"""

import pymysql

# Configuración de conexión con XAMPP
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '', # Vacío por defecto en XAMPP
    'database': 'invernadero_asistivo',
    'port': 3306
}

def probar_conexion():
    print("=======================================================")
    print("   PROBANDO CONEXIÓN DE CÓDIGO PYTHON CON XAMPP        ")
    print("=======================================================")
    try:
        conexion = pymysql.connect(**DB_CONFIG)
        print("✅ ÉXITO: Python se conectó correctamente a MySQL en XAMPP.\n")
        
        with conexion.cursor() as cursor:
            cursor.execute("SHOW TABLES;")
            tablas = cursor.fetchall()
            print("📋 Tablas encontradas en 'invernadero_asistivo':")
            if tablas:
                for tabla in tablas:
                    print(f"   -> {tabla[0]}")
            else:
                print("   (La base de datos existe pero está vacía. Faltan las tablas)")
            
        conexion.close()
    except pymysql.err.OperationalError as error:
        print("❌ ERROR DE CONEXIÓN:")
        print("   Asegúrate de que el botón 'Start' de MySQL en XAMPP esté en VERDE.")
        print(f"   Detalle técnico: {error}")
    except pymysql.err.ProgrammingError as error:
        print("⚠️ ERROR DE BASE DE DATOS:")
        print("   MySQL está prendido, pero aún no has creado la base de datos 'invernadero_asistivo'.")
        print("   Recuerda pegar el archivo schema.sql en phpMyAdmin.")
        print(f"   Detalle técnico: {error}")

if __name__ == '__main__':
    probar_conexion()