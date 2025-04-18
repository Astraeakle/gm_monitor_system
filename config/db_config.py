import os
from dotenv import load_dotenv

# Cargar variables de entorno desde .env (crear este archivo con tus credenciales)
load_dotenv()

# Configuracion de la conexion a MySQL
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': 'gm_monitor_system',
    'raise_on_warnings': True
}

# String de conexion para SQLAlchemy
SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}/{DB_CONFIG['database']}"