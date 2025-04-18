import sys
import os
import random
from datetime import datetime, timedelta
from sqlalchemy import text
# Añadir directorio raíz al path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.entities import (Proyecto, Actividad, Asignacion, CapturaTrabajo,
                         RegistroAplicacion, RegistroTiempo, TipoEntregable,
                         Entregable, EvaluacionCalidad, MetricaProductividad, 
                         Session, engine)

def insert_test_data():
    """Inserta datos de prueba en las tablas"""
    with Session() as session:
        # Verificar si ya hay datos
        if session.query(Proyecto).count() > 0:
            print("Ya existen datos en las tablas. Omitiendo insercion.")
            return
        
        print("Insertando datos de prueba...")
        
        # Insertar proyectos
        proyectos = [
            Proyecto(
                nombre_proyecto=f"Proyecto {i}",
                cliente=f"Cliente {i}",
                fecha_inicio=datetime.now() - timedelta(days=random.randint(10, 100)),
                fecha_fin_estimada=datetime.now() + timedelta(days=random.randint(30, 180)),
                estado=random.choice(['Planificacion', 'En Progreso', 'Finalizado']),
                descripcion=f"Descripcion del proyecto {i}"
            ) for i in range(1, 6)
        ]
        
        session.add_all(proyectos)
        session.flush()
        
        # Insertar tipos de entregables
        tipos_entregables = [
            TipoEntregable(
                nombre=f"Tipo Entregable {i}",
                descripcion=f"Descripcion del tipo de entregable {i}",
                parametros_calidad=f"Parámetros de calidad para tipo {i}"
            ) for i in range(1, 4)
        ]
        
        session.add_all(tipos_entregables)
        session.flush()
        
        # Insertar actividades
        actividades = []
        for proyecto in proyectos:
            for i in range(1, 4):
                actividad = Actividad(
                    id_proyecto=proyecto.id_proyecto,
                    nombre_actividad=f"Actividad {i} del Proyecto {proyecto.id_proyecto}",
                    descripcion=f"Descripcion de la actividad {i}",
                    prioridad=random.choice(['Baja', 'Media', 'Alta']),
                    fecha_asignacion=datetime.now() - timedelta(days=random.randint(5, 30)),
                    fecha_limite=datetime.now() + timedelta(days=random.randint(1, 45)),
                    estado=random.choice(['Pendiente', 'En Progreso', 'Completada'])
                )
                actividades.append(actividad)
        
        session.add_all(actividades)
        session.flush()
        
        # Obtener IDs de empleados existentes
        result = session.execute(text("SELECT idempleado FROM gmadministracion.empleados LIMIT 10"))
        empleados_ids = [row[0] for row in result.fetchall()]

        if not empleados_ids:
            empleados_ids = ['EM01', 'EM02', 'EM03', 'EM04', 'EM05']
        
        # Insertar asignaciones
        asignaciones = []
        for actividad in actividades:
            asignacion = Asignacion(
                id_actividad=actividad.id_actividad,
                id_empleado=random.choice(empleados_ids),
                fecha_asignacion=datetime.now() - timedelta(days=random.randint(1, 30))
            )
            asignaciones.append(asignacion)
        
        session.add_all(asignaciones)
        session.flush()
        
        # Insertar registros de tiempo
        for asignacion in asignaciones:
            for _ in range(random.randint(1, 5)):
                fecha = datetime.now() - timedelta(days=random.randint(0, 15))
                hora_inicio = datetime.strptime(f"{random.randint(8, 12)}:00:00", "%H:%M:%S").time()
                hora_fin = datetime.strptime(f"{random.randint(13, 18)}:00:00", "%H:%M:%S").time()
                
                registro = RegistroTiempo(
                    id_empleado=asignacion.id_empleado,
                    id_actividad=asignacion.id_actividad,
                    fecha=fecha.date(),
                    hora_inicio=hora_inicio,
                    hora_fin=hora_fin,
                    descripcion_actividad=f"Trabajo en actividad {asignacion.id_actividad}",
                    ubicacion="Remoto",
                    aplicaciones_usadas='{"apps": ["Excel", "Word", "AutoCAD"]}'
                )
                session.add(registro)
        
        # Insertar entregables
        for actividad in actividades:
            for _ in range(random.randint(1, 3)):
                empleado_id = random.choice(empleados_ids)
                entregable = Entregable(
                    id_actividad=actividad.id_actividad,
                    id_empleado=empleado_id,
                    id_tipo_entregable=random.choice([t.id_tipo_entregable for t in tipos_entregables]),
                    nombre_archivo=f"entregable_{actividad.id_actividad}_{random.randint(1, 1000)}.docx",
                    ruta_archivo=f"/entregables/proyecto_{actividad.id_proyecto}/",
                    fecha_entrega=datetime.now() - timedelta(days=random.randint(1, 10)),
                    version=random.randint(1, 3),
                    estado=random.choice(['Pendiente Revision', 'Aprobado', 'Rechazado'])
                )
                session.add(entregable)
                session.flush()
                
                # Insertar evaluacion de calidad si el entregable no está pendiente
                if entregable.estado != 'Pendiente Revision':
                    evaluacion = EvaluacionCalidad(
                        id_entregable=entregable.id_entregable,
                        id_evaluador=random.choice(empleados_ids),
                        fecha_evaluacion=datetime.now() - timedelta(days=random.randint(0, 5)),
                        cumple_formato=random.choice([True, False]),
                        cumple_contenido=random.choice([True, False]),
                        cumple_normativa=random.choice([True, False]),
                        calificacion_general=random.randint(1, 5),
                        observaciones="Observaciones sobre el entregable",
                        acciones_correctivas="Acciones correctivas sugeridas"
                    )
                    session.add(evaluacion)
        
        session.commit()
        print("Datos de prueba insertados correctamente.")

if __name__ == "__main__":
    insert_test_data()
    