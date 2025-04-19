from models.entities import engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from config.db_config import SQLALCHEMY_DATABASE_URI
import pandas as pd
from sqlalchemy import text
import os
import sys

# Añadir directorio raíz al path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class ProductivityMetrics:
    """Clase para calcular métricas de productividad usando SQL"""

    def __init__(self):
        """Inicializa la conexión a la base de datos"""
        self.engine = engine

    def get_approved_deliverables_percentage(self):
        """Calcula el porcentaje de entregables aprobados por empleado"""
        query = """
        SELECT
            e.id_empleado,
            CONCAT(emp.nombres, ' ', emp.apellidos) AS nombre_empleado,
            COUNT(e.id_entregable) AS total_entregables,
            SUM(CASE WHEN e.estado = 'Aprobado' THEN 1 ELSE 0 END) AS entregables_aprobados,
            ROUND((SUM(CASE WHEN e.estado = 'Aprobado' THEN 1 ELSE 0 END) / COUNT(e.id_entregable)) * 100, 2) AS porcentaje_aprobados
        FROM
            entregables e
        LEFT JOIN
            gmadministracion.empleados emp ON e.id_empleado = emp.idempleado
        GROUP BY
            e.id_empleado, nombre_empleado
        ORDER BY
            porcentaje_aprobados DESC
        """

        try:
            with self.engine.connect() as connection:
                result = connection.execute(text(query))
                df = pd.DataFrame(result.fetchall())
                if not df.empty:
                    df.columns = result.keys()
                return df
        except Exception as e:
            print(f"Error al obtener porcentaje de entregables aprobados: {e}")
            return pd.DataFrame()

    def get_average_time_per_task(self):
        """Calcula el tiempo promedio por tarea en horas"""
        query = """
        SELECT
            a.id_actividad,
            a.nombre_actividad,
            p.nombre_proyecto,
            AVG(TIMESTAMPDIFF(SECOND, CONCAT(fecha, ' ', rt.hora_inicio), 
                CONCAT(fecha, ' ', rt.hora_fin)) / 3600) AS tiempo_promedio_horas,
            COUNT(DISTINCT rt.id_empleado) AS num_empleados_involucrados
        FROM
            registro_tiempo rt
        JOIN
            actividades a ON rt.id_actividad = a.id_actividad
        JOIN
            proyectos p ON a.id_proyecto = p.id_proyecto
        GROUP BY
            a.id_actividad, a.nombre_actividad, p.nombre_proyecto
        ORDER BY
            tiempo_promedio_horas DESC
        """

        try:
            with self.engine.connect() as connection:
                result = connection.execute(text(query))
                df = pd.DataFrame(result.fetchall())
                if not df.empty:
                    df.columns = result.keys()
                return df
        except Exception as e:
            print(f"Error al obtener tiempo promedio por tarea: {e}")
            return pd.DataFrame()

    def get_deliverable_quality_metrics(self):
        """Obtiene métricas de calidad de entregables"""
        query = """
        SELECT
            e.id_empleado,
            CONCAT(emp.nombres, ' ', emp.apellidos) AS nombre_empleado,
            COUNT(e.id_entregable) AS total_entregables,
            ROUND(AVG(ec.calificacion_general), 2) AS calificacion_promedio,
            SUM(CASE WHEN ec.cumple_formato = TRUE THEN 1 ELSE 0 END) / COUNT(e.id_entregable) * 100 AS pct_cumple_formato,
            SUM(CASE WHEN ec.cumple_contenido = TRUE THEN 1 ELSE 0 END) / COUNT(e.id_entregable) * 100 AS pct_cumple_contenido,
            SUM(CASE WHEN ec.cumple_normativa = TRUE THEN 1 ELSE 0 END) / COUNT(e.id_entregable) * 100 AS pct_cumple_normativa
        FROM
            entregables e
        LEFT JOIN
            evaluacion_calidad ec ON e.id_entregable = ec.id_entregable
        LEFT JOIN
            gmadministracion.empleados emp ON e.id_empleado = emp.idempleado
        GROUP BY
            e.id_empleado, nombre_empleado
        ORDER BY
            calificacion_promedio DESC
        """

        try:
            with self.engine.connect() as connection:
                result = connection.execute(text(query))
                df = pd.DataFrame(result.fetchall())
                if not df.empty:
                    df.columns = result.keys()
                return df
        except Exception as e:
            print(f"Error al obtener métricas de calidad: {e}")
            return pd.DataFrame()

    def get_project_time_investment(self):
        """Calcula el tiempo total invertido por proyecto"""
        query = """
        SELECT
            p.id_proyecto,
            p.nombre_proyecto,
            COUNT(DISTINCT a.id_actividad) AS total_actividades,
            SUM(TIMESTAMPDIFF(SECOND, CONCAT(fecha, ' ', rt.hora_inicio), 
                CONCAT(fecha, ' ', rt.hora_fin)) / 3600) AS total_horas_trabajadas,
            COUNT(DISTINCT rt.id_empleado) AS num_empleados,
            ROUND(SUM(TIMESTAMPDIFF(SECOND, CONCAT(fecha, ' ', rt.hora_inicio), 
                CONCAT(fecha, ' ', rt.hora_fin)) / 3600) / COUNT(DISTINCT a.id_actividad), 2) AS promedio_horas_por_actividad
        FROM
            registro_tiempo rt
        JOIN
            actividades a ON rt.id_actividad = a.id_actividad
        JOIN
            proyectos p ON a.id_proyecto = p.id_proyecto
        GROUP BY
            p.id_proyecto, p.nombre_proyecto
        ORDER BY
            total_horas_trabajadas DESC
        """

        try:
            with self.engine.connect() as connection:
                result = connection.execute(text(query))
                df = pd.DataFrame(result.fetchall())
                if not df.empty:
                    df.columns = result.keys()
                return df
        except Exception as e:
            print(f"Error al obtener inversión de tiempo por proyecto: {e}")
            return pd.DataFrame()

    def get_employee_productivity(self):
        """Calcula la productividad por empleado (entregables por hora)"""
        query = """
        SELECT
            rt.id_empleado,
            CONCAT(emp.nombres, ' ', emp.apellidos) AS nombre_empleado,
            SUM(TIMESTAMPDIFF(SECOND, CONCAT(rt.fecha, ' ', rt.hora_inicio), 
                CONCAT(rt.fecha, ' ', rt.hora_fin)) / 3600) AS total_horas,
            COUNT(DISTINCT e.id_entregable) AS total_entregables,
            ROUND(COUNT(DISTINCT e.id_entregable) / SUM(TIMESTAMPDIFF(SECOND, 
                CONCAT(rt.fecha, ' ', rt.hora_inicio), CONCAT(rt.fecha, ' ', rt.hora_fin)) / 3600), 2) AS entregables_por_hora
        FROM
            registro_tiempo rt
        LEFT JOIN
            gmadministracion.empleados emp ON rt.id_empleado = emp.idempleado
        LEFT JOIN
            entregables e ON rt.id_empleado = e.id_empleado AND rt.id_actividad = e.id_actividad
        GROUP BY
            rt.id_empleado, nombre_empleado
        HAVING
            total_horas > 0
        ORDER BY
            entregables_por_hora DESC
        """

        try:
            with self.engine.connect() as connection:
                result = connection.execute(text(query))
                df = pd.DataFrame(result.fetchall())
                if not df.empty:
                    df.columns = result.keys()
                return df
        except Exception as e:
            print(f"Error al obtener productividad por empleado: {e}")
            return pd.DataFrame()

    def get_project_rejection_rate(self):
        """Calcula la tasa de rechazo de entregables por proyecto"""
        query = """
        SELECT
            p.id_proyecto,
            p.nombre_proyecto,
            COUNT(DISTINCT e.id_entregable) AS total_entregables,
            SUM(CASE WHEN e.estado = 'Rechazado' THEN 1 ELSE 0 END) AS entregables_rechazados,
            ROUND((SUM(CASE WHEN e.estado = 'Rechazado' THEN 1 ELSE 0 END) / 
                COUNT(DISTINCT e.id_entregable)) * 100, 2) AS tasa_rechazo
        FROM
            entregables e
        JOIN
            actividades a ON e.id_actividad = a.id_actividad
        JOIN
            proyectos p ON a.id_proyecto = p.id_proyecto
        GROUP BY
            p.id_proyecto, p.nombre_proyecto
        ORDER BY
            tasa_rechazo DESC
        """

        try:
            with self.engine.connect() as connection:
                result = connection.execute(text(query))
                df = pd.DataFrame(result.fetchall())
                if not df.empty:
                    df.columns = result.keys()
                return df
        except Exception as e:
            print(f"Error al obtener tasa de rechazo por proyecto: {e}")
            return pd.DataFrame()

    def get_dashboard_data(self):
        """Obtiene datos para el panel de control principal"""
        query = """
        SELECT
            e.id_empleado,
            CONCAT(emp.nombres, ' ', emp.apellidos) AS nombre_empleado,
            p.id_proyecto,
            p.nombre_proyecto,
            COUNT(DISTINCT a.id_actividad) AS total_actividades,
            SUM(CASE WHEN a.estado = 'Completada' THEN 1 ELSE 0 END) AS actividades_completadas,
            ROUND((SUM(CASE WHEN a.estado = 'Completada' THEN 1 ELSE 0 END) / 
                COUNT(DISTINCT a.id_actividad)) * 100, 2) AS pct_completado,
            SUM(TIMESTAMPDIFF(SECOND, CONCAT(rt.fecha, ' ', rt.hora_inicio), 
                CONCAT(rt.fecha, ' ', rt.hora_fin)) / 3600) AS total_horas,
            COUNT(DISTINCT e.id_entregable) AS total_entregables,
            SUM(CASE WHEN e.estado = 'Aprobado' THEN 1 ELSE 0 END) AS entregables_aprobados,
            SUM(CASE WHEN e.estado = 'Rechazado' THEN 1 ELSE 0 END) AS entregables_rechazados,
            ROUND(AVG(COALESCE(ec.calificacion_general, 0)), 2) AS calificacion_promedio
        FROM
            registro_tiempo rt
        JOIN
            actividades a ON rt.id_actividad = a.id_actividad
        JOIN
            proyectos p ON a.id_proyecto = p.id_proyecto
        LEFT JOIN
            gmadministracion.empleados emp ON rt.id_empleado = emp.idempleado
        LEFT JOIN
            entregables e ON rt.id_empleado = e.id_empleado AND rt.id_actividad = e.id_actividad
        LEFT JOIN
            evaluacion_calidad ec ON e.id_entregable = ec.id_entregable
        GROUP BY
            e.id_empleado, nombre_empleado, p.id_proyecto, p.nombre_proyecto
        """

        try:
            with self.engine.connect() as connection:
                result = connection.execute(text(query))
                df = pd.DataFrame(result.fetchall())
                if not df.empty:
                    df.columns = result.keys()
                return df
        except Exception as e:
            print(f"Error al obtener datos para el panel principal: {e}")
            return pd.DataFrame()

    def create_dashboard_view(self):
        """Crea o actualiza la vista para el panel de control principal"""
        query = """
        CREATE OR REPLACE VIEW vista_panel_control AS
        SELECT
            e.id_empleado,
            CONCAT(emp.nombres, ' ', emp.apellidos) AS nombre_empleado,
            p.id_proyecto,
            p.nombre_proyecto,
            COUNT(DISTINCT a.id_actividad) AS total_actividades,
            SUM(CASE WHEN a.estado = 'Completada' THEN 1 ELSE 0 END) AS actividades_completadas,
            ROUND((SUM(CASE WHEN a.estado = 'Completada' THEN 1 ELSE 0 END) / 
                COUNT(DISTINCT a.id_actividad)) * 100, 2) AS pct_completado,
            SUM(TIMESTAMPDIFF(SECOND, CONCAT(rt.fecha, ' ', rt.hora_inicio), 
                CONCAT(rt.fecha, ' ', rt.hora_fin)) / 3600) AS total_horas,
            COUNT(DISTINCT e.id_entregable) AS total_entregables,
            SUM(CASE WHEN e.estado = 'Aprobado' THEN 1 ELSE 0 END) AS entregables_aprobados,
            SUM(CASE WHEN e.estado = 'Rechazado' THEN 1 ELSE 0 END) AS entregables_rechazados,
            ROUND(AVG(COALESCE(ec.calificacion_general, 0)), 2) AS calificacion_promedio
        FROM
            registro_tiempo rt
        JOIN
            actividades a ON rt.id_actividad = a.id_actividad
        JOIN
            proyectos p ON a.id_proyecto = p.id_proyecto
        LEFT JOIN
            gmadministracion.empleados emp ON rt.id_empleado = emp.idempleado
        LEFT JOIN
            entregables e ON rt.id_empleado = e.id_empleado AND rt.id_actividad = e.id_actividad
        LEFT JOIN
            evaluacion_calidad ec ON e.id_entregable = ec.id_entregable
        GROUP BY
            e.id_empleado, nombre_empleado, p.id_proyecto, p.nombre_proyecto
        """

        try:
            with self.engine.connect() as connection:
                connection.execute(text(query))
                print("Vista 'vista_panel_control' creada exitosamente")
                return True
        except Exception as e:
            print(f"Error al crear vista para el panel: {e}")
            return False

    def export_metrics_to_csv(self, output_dir=None):
        """Exporta todas las métricas a archivos CSV"""
        if output_dir is None:
            output_dir = os.path.join(os.path.dirname(
                os.path.dirname(__file__)), 'entregables', 'metricas')

        os.makedirs(output_dir, exist_ok=True)

        # Recopilar todas las métricas
        metrics = {
            'porcentaje_aprobados': self.get_approved_deliverables_percentage(),
            'tiempo_por_tarea': self.get_average_time_per_task(),
            'calidad_entregables': self.get_deliverable_quality_metrics(),
            'tiempo_proyecto': self.get_project_time_investment(),
            'productividad_empleado': self.get_employee_productivity(),
            'rechazo_proyecto': self.get_project_rejection_rate(),
            'datos_dashboard': self.get_dashboard_data()
        }

        # Exportar cada métrica a un archivo CSV
        for name, df in metrics.items():
            if not df.empty:
                file_path = os.path.join(output_dir, f'{name}.csv')
                df.to_csv(file_path, index=False)
                print(f"Métricas de '{name}' exportadas a {file_path}")

        return metrics


def run_metrics_report():
    """Función principal para ejecutar el reporte de métricas de productividad"""
    print("Generando métricas de productividad...")
    metrics = ProductivityMetrics()

    # Crear la vista para el panel de control
    metrics.create_dashboard_view()

    # Exportar métricas a CSV
    export_dir = os.path.join(os.path.dirname(
        os.path.dirname(__file__)), 'entregables', 'metricas')
    result_metrics = metrics.export_metrics_to_csv(export_dir)

    # Imprimir resumen de resultados
    print("\nResumen de métricas generadas:")
    for name, df in result_metrics.items():
        if not df.empty:
            print(f"- {name}: {len(df)} registros")

    print(f"\nMétricas exportadas al directorio: {export_dir}")
    return result_metrics


if __name__ == "__main__":
    run_metrics_report()
