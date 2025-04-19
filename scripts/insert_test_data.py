from models.entities import (Proyecto, Actividad, Session)
import sys
import os
from sqlalchemy import func

# Añadir directorio raíz al path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def verify_data_exists():
    """Verifica si existen datos en las tablas principales"""
    with Session() as session:
        proyecto_count = session.query(
            func.count(Proyecto.id_proyecto)).scalar()
        actividad_count = session.query(
            func.count(Actividad.id_actividad)).scalar()

        print(f"Verificación de datos existentes:")
        print(f"- Proyectos: {proyecto_count}")
        print(f"- Actividades: {actividad_count}")

        return proyecto_count > 0 and actividad_count > 0


if __name__ == "__main__":
    verify_data_exists()
