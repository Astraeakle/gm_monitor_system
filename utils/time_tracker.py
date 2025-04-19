# Añadir/actualizar este archivo
import pandas as pd
from datetime import datetime, timedelta


class TimeTracker:
    @staticmethod
    def calculate_worked_hours(start_time, end_time, date):
        """Calcula las horas trabajadas entre dos tiempos en una fecha"""
        start_dt = datetime.combine(date, start_time)
        end_dt = datetime.combine(date, end_time)

        # Si la hora de fin es menor que la de inicio, se asume que terminó al día siguiente
        if end_dt < start_dt:
            end_dt += timedelta(days=1)

        duration = (end_dt - start_dt).total_seconds() / 3600
        return round(duration, 2)

    @staticmethod
    def summarize_productivity(df_tiempo):
        """Genera un resumen de productividad basado en registros de tiempo"""
        if df_tiempo.empty:
            return pd.DataFrame()

        # Asegurar que tenemos las columnas necesarias
        if 'id_empleado' not in df_tiempo.columns or 'horas_trabajadas' not in df_tiempo.columns:
            return pd.DataFrame()

        # Agrupar por empleado
        resumen = df_tiempo.groupby('id_empleado').agg({
            'horas_trabajadas': 'sum',
            'id_registro': 'count'
        }).reset_index()

        # Renombrar columnas
        resumen.columns = ['id_empleado', 'total_horas', 'total_registros']

        # Calcular productividad por hora (registros por hora)
        resumen['productividad'] = resumen['total_registros'] / \
            resumen['total_horas']

        return resumen
