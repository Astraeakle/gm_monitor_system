import os
import sys
import mysql.connector
from mysql.connector import Error

# Añadir directorio raíz al path para importaciones
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.db_config import DB_CONFIG

def test_mysql_connection():
    """Prueba la conexion a MySQL y muestra informacion básica de la base de datos"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        
        if conn.is_connected():
            db_info = conn.get_server_info()
            print(f"Conectado a MySQL version: {db_info}")
            
            cursor = conn.cursor()
            
            # Obtener la version de MySQL
            cursor.execute("SELECT VERSION();")
            version = cursor.fetchone()
            print(f"Version de la base de datos: {version[0]}")
            
            # Listar tablas en la base de datos
            cursor.execute("SHOW TABLES;")
            tables = cursor.fetchall()
            
            print("\nTablas disponibles en la base de datos:")
            for table in tables:
                print(f"- {table[0]}")
                
                # Contar numero de registros en cada tabla
                cursor.execute(f"SELECT COUNT(*) FROM {table[0]};")
                count = cursor.fetchone()[0]
                print(f"  - Numero de registros: {count}")
            
            # Verificar conexion a base de datos cruzada (gmadministracion)
            try:
                cursor.execute("SELECT COUNT(*) FROM gmadministracion.empleados;")
                count = cursor.fetchone()[0]
                print(f"\nConexion a gmadministracion.empleados exitosa. Registros: {count}")
            except Error as e:
                print(f"\nError al conectar con la base de datos gmadministracion: {e}")
            
            cursor.close()
            
    except Error as e:
        print(f"Error al conectar a MySQL: {e}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            conn.close()
            print("\nConexion a MySQL cerrada.")

if __name__ == "__main__":
    print("Probando conexion a la base de datos...")
    test_mysql_connection()