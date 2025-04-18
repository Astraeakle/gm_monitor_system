from models.entities import (Proyecto, Actividad, Asignacion, CapturaTrabajo,
                             RegistroAplicacion, RegistroTiempo, TipoEntregable,
                             Entregable, EvaluacionCalidad, MetricaProductividad, engine)
from utils.data_validator import DataValidator
import pandas as pd
import numpy as np
from sqlalchemy import select, text
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import json
import os
import sys

# Añadir directorio raíz al path para importaciones
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class DataStandardizer:
    def __init__(self):
        """Inicializa el estandarizador de datos"""
        self.engine = engine
        self.validator = DataValidator()

    def get_table_structure(self, table_name="gmadministracion.empleados"):
        """Obtiene la estructura de una tabla para verificar sus columnas"""
        query = text(f"DESCRIBE {table_name}")
        try:
            with self.engine.connect() as connection:
                result = connection.execute(query)
                columns = result.fetchall()
                print(f"\nEstructura de la tabla {table_name}:")
                for col in columns:
                    print(f"- {col[0]}: {col[1]}")
                return columns
        except Exception as e:
            print(f"Error al obtener estructura de la tabla: {e}")
            return None

    def get_cross_database_data(self):
        """Obtiene datos de empleados desde la otra base de datos"""
        # Primero obtenemos la estructura real
        self.get_table_structure("gmadministracion.empleados")

        # Ahora intentamos una consulta más segura que solo selecciona idempleado
        # y los campos que probablemente existan
        query = text("""
            SELECT e.idempleado, e.*, 'Activo' as estado
            FROM u.empleados e
        """)
        try:
            with self.engine.connect() as connection:
                result = connection.execute(query)
                df_empleados = pd.DataFrame(result.fetchall())
                if not df_empleados.empty:
                    df_empleados.columns = result.keys()
                    print(
                        f"Columnas obtenidas de empleados: {df_empleados.columns.tolist()}")
                return df_empleados
        except Exception as e:
            print(f"Error al obtener datos de empleados: {e}")
            # Crear un DataFrame mínimo para que el proceso continue
            return pd.DataFrame({"idempleado": ["EMP01"], "nombre_completo": ["Usuario Temporal"]})

    def get_activities_data(self):
        """Obtiene datos de actividades y proyectos"""
        with Session(self.engine) as session:
            query = (
                select(
                    Actividad.id_actividad,
                    Actividad.nombre_actividad,
                    Actividad.descripcion,
                    Actividad.prioridad,
                    Actividad.fecha_asignacion,
                    Actividad.fecha_limite,
                    Actividad.estado,
                    Proyecto.id_proyecto,
                    Proyecto.nombre_proyecto,
                    Proyecto.cliente,
                    Proyecto.estado.label('estado_proyecto')
                )
                .join(Proyecto, Actividad.id_proyecto == Proyecto.id_proyecto)
            )

            result = session.execute(query)
            df_actividades = pd.DataFrame(result.fetchall())
            if not df_actividades.empty:
                df_actividades.columns = result.keys()
            return df_actividades

    def get_time_records(self):
        """Obtiene registros de tiempo trabajado"""
        with Session(self.engine) as session:
            query = (
                select(
                    RegistroTiempo.id_registro,
                    RegistroTiempo.id_empleado,
                    RegistroTiempo.id_actividad,
                    RegistroTiempo.fecha,
                    RegistroTiempo.hora_inicio,
                    RegistroTiempo.hora_fin,
                    RegistroTiempo.descripcion_actividad,
                    RegistroTiempo.ubicacion,
                    RegistroTiempo.aplicaciones_usadas
                )
            )

            result = session.execute(query)
            df_tiempo = pd.DataFrame(result.fetchall())
            if not df_tiempo.empty:
                df_tiempo.columns = result.keys()
            return df_tiempo

    def get_deliverables_data(self):
        """Obtiene datos de entregables y su evaluacion"""
        with Session(self.engine) as session:
            query = (
                select(
                    Entregable.id_entregable,
                    Entregable.id_actividad,
                    Entregable.id_empleado,
                    Entregable.nombre_archivo,
                    Entregable.fecha_entrega,
                    Entregable.version,
                    Entregable.estado,
                    TipoEntregable.nombre.label('tipo_entregable'),
                    EvaluacionCalidad.cumple_formato,
                    EvaluacionCalidad.cumple_contenido,
                    EvaluacionCalidad.cumple_normativa,
                    EvaluacionCalidad.calificacion_general
                )
                .join(TipoEntregable, Entregable.id_tipo_entregable == TipoEntregable.id_tipo_entregable)
                .outerjoin(EvaluacionCalidad, Entregable.id_entregable == EvaluacionCalidad.id_entregable)
            )

            result = session.execute(query)
            df_entregables = pd.DataFrame(result.fetchall())
            if not df_entregables.empty:
                df_entregables.columns = result.keys()
            return df_entregables

    def standardize_time_records(self, df_tiempo):
        """Estandariza los registros de tiempo y calcula horas trabajadas"""
        if df_tiempo.empty:
            return df_tiempo

        # Convertir columnas a tipos adecuados
        df_tiempo['fecha'] = pd.to_datetime(df_tiempo['fecha']).dt.date

        # Asegurar que hora_inicio y hora_fin son objetos de tiempo
        df_tiempo['hora_inicio'] = pd.to_datetime(
            df_tiempo['hora_inicio'], format='%H:%M:%S').dt.time
        df_tiempo['hora_fin'] = pd.to_datetime(
            df_tiempo['hora_fin'], format='%H:%M:%S').dt.time

        # Calcular duracion (horas trabajadas)
        def calcular_horas(row):
            inicio_dt = datetime.combine(row['fecha'], row['hora_inicio'])
            fin_dt = datetime.combine(row['fecha'], row['hora_fin'])

            # Si la hora de fin es menor que la de inicio, se asume que termino al día siguiente
            if fin_dt < inicio_dt:
                fin_dt += timedelta(days=1)

            duracion = (fin_dt - inicio_dt).total_seconds() / 3600
            return round(duracion, 2)

        df_tiempo['horas_trabajadas'] = df_tiempo.apply(calcular_horas, axis=1)

        # Procesar el campo JSON de aplicaciones usadas
        def parse_apps(json_str):
            if pd.isnull(json_str):
                return []
            try:
                return json.loads(json_str)
            except:
                return []

        df_tiempo['apps_list'] = df_tiempo['aplicaciones_usadas'].apply(
            parse_apps)

        return df_tiempo

    def standardize_deliverables(self, df_entregables):
        """Estandariza los datos de entregables"""
        if df_entregables.empty:
            return df_entregables

        # Convertir fecha de entrega a datetime
        df_entregables['fecha_entrega'] = pd.to_datetime(
            df_entregables['fecha_entrega'])

        # Convertir valores booleanos de NULL a False
        bool_columns = ['cumple_formato',
                        'cumple_contenido', 'cumple_normativa']
        for col in bool_columns:
            df_entregables[col] = df_entregables[col].fillna(False)

        # Calcular un score de calidad basado en los cumplimientos
        df_entregables['score_calidad'] = (
            df_entregables['cumple_formato'].astype(int) +
            df_entregables['cumple_contenido'].astype(int) +
            df_entregables['cumple_normativa'].astype(int)
        ) / 3 * 100

        # Clasificar entregables por calidad
        def clasificar_calidad(score):
            if score >= 80:
                return 'Alta'
            elif score >= 50:
                return 'Media'
            else:
                return 'Baja'

        df_entregables['clasificacion_calidad'] = df_entregables['score_calidad'].apply(
            clasificar_calidad)

        return df_entregables

    def create_unified_dataset(self):
        """Crea un dataset unificado de actividades remotas"""
        # Obtener datos
        df_empleados = self.get_cross_database_data()
        df_actividades = self.get_activities_data()
        df_tiempo = self.get_time_records()
        df_entregables = self.get_deliverables_data()

        # Estandarizar datos
        df_tiempo_std = self.standardize_time_records(df_tiempo)
        df_entregables_std = self.standardize_deliverables(df_entregables)

        # Crear dataset unificado para actividades remotas
        if not df_tiempo_std.empty and not df_actividades.empty and not df_empleados.empty:
            # Unir datos de tiempo con actividades
            df_unified = pd.merge(
                df_tiempo_std,
                df_actividades,
                on='id_actividad',
                how='left'
            )

            # Paso 3: Modificar la parte que usa estos campos en create_unified_dataset()
            # Actualiza el codigo que hace merge con los datos de empleados:
            # Ajustar el codigo de merge con los datos que realmente existen
            empleados_columns = df_empleados.columns.tolist()
            join_columns = ['idempleado']

            # Determinar que columnas podemos usar basado en lo que existe
            if 'nombre' in empleados_columns:
                join_columns.append('nombre')
            elif 'nombres' in empleados_columns:
                join_columns.append('nombres')
            elif 'nombre_completo' in empleados_columns:
                join_columns.append('nombre_completo')

            if 'apellidos' in empleados_columns:
                join_columns.append('apellidos')
            elif 'apellido' in empleados_columns:
                join_columns.append('apellido')

            if 'email' in empleados_columns:
                join_columns.append('email')

            # Ahora hacemos el merge con solo las columnas disponibles
            df_unified = pd.merge(
                df_unified,
                df_empleados[join_columns],
                left_on='id_empleado',
                right_on='idempleado',
                how='left'
            )

            # Agregar metricas de entregables si existen
            if not df_entregables_std.empty:
                # Agrupar entregables por empleado y actividad
                df_entregables_agg = df_entregables_std.groupby(['id_empleado', 'id_actividad']).agg({
                    'id_entregable': 'count',
                    'score_calidad': 'mean',
                    'estado': lambda x: (x == 'Aprobado').sum(),
                }).reset_index()

                df_entregables_agg.columns = [
                    'id_empleado', 'id_actividad', 'total_entregables',
                    'calidad_promedio', 'entregables_aprobados'
                ]

                df_unified = pd.merge(
                    df_unified,
                    df_entregables_agg,
                    on=['id_empleado', 'id_actividad'],
                    how='left'
                )

            return df_unified

    def run(self):
        """Metodo de ejecución principal para estandarizar datos y crear un conjunto de datos unificado"""
        print("Ejecutando proceso de estandarización de datos...")
        # Crear dataset unificado
        df_unified = self.create_unified_dataset()

        if df_unified is not None and not df_unified.empty:
            print(
                f"Dataset unificado creado exitosamente con {len(df_unified)} registros")
            return df_unified
        else:
            print("No se pudo crear el dataset unificado")
            return None

        return pd.DataFrame()


if __name__ == "__main__":
    standardizer = DataStandardizer()
    standardizer.run()
