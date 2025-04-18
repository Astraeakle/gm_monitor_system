from scripts.data_standardization import DataStandardizer
import sys
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

# Añadir directorio raíz al path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def generate_kpi_document():
    """Genera un documento de KPIs basado en los datos del sistema"""
    print("Generando documento de KPIs...")

    # Crear la carpeta de entregables si no existe
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'entregables')
    os.makedirs(output_dir, exist_ok=True)

    # Obtener los datos estandarizados
    standardizer = DataStandardizer()
    df = standardizer.run()

    if df is None or df.empty:
        print("No hay datos suficientes para generar el documento de KPIs.")
        return

    # Ruta del archivo de salida
    kpi_file = os.path.join(
        output_dir, f'kpi_document_{datetime.now().strftime("%Y%m%d")}.md')

    # Calcular KPIs
    with open(kpi_file, 'w', encoding='utf-8') as f:
        f.write("# Documento de KPIs - Sistema de Monitoreo de Productividad\n\n")
        f.write(
            f"Generado el: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        f.write("## 1. Horas Trabajadas\n\n")

        # KPI: Horas trabajadas por empleado
        if 'horas_trabajadas' in df.columns and 'id_empleado' in df.columns:
            horas_por_empleado = df.groupby('id_empleado')[
                'horas_trabajadas'].sum().reset_index()
            horas_por_empleado = horas_por_empleado.sort_values(
                'horas_trabajadas', ascending=False)

            f.write("### 1.1 Total de Horas Trabajadas por Empleado\n\n")
            f.write("| ID Empleado | Horas Totales |\n")
            f.write("|-------------|---------------|\n")

            for _, row in horas_por_empleado.iterrows():
                f.write(
                    f"| {row['id_empleado']} | {row['horas_trabajadas']:.2f} |\n")

            f.write("\n")

        # KPI: Horas trabajadas por proyecto
        if 'horas_trabajadas' in df.columns and 'id_proyecto' in df.columns:
            horas_por_proyecto = df.groupby(['id_proyecto', 'nombre_proyecto'])[
                'horas_trabajadas'].sum().reset_index()
            horas_por_proyecto = horas_por_proyecto.sort_values(
                'horas_trabajadas', ascending=False)

            f.write("### 1.2 Total de Horas Trabajadas por Proyecto\n\n")
            f.write("| ID Proyecto | Nombre Proyecto | Horas Totales |\n")
            f.write("|-------------|-----------------|---------------|\n")

            for _, row in horas_por_proyecto.iterrows():
                f.write(
                    f"| {row['id_proyecto']} | {row['nombre_proyecto']} | {row['horas_trabajadas']:.2f} |\n")

            f.write("\n")

        f.write("## 2. Calidad de Entregables\n\n")

        # KPI: Entregables rechazados
        if 'estado' in df.columns:
            try:
                # Verificar si existe la columna estado y tiene los valores esperados
                entregables_status = df['estado'].value_counts().reset_index()
                entregables_status.columns = ['Estado', 'Cantidad']

                f.write("### 2.1 Estado de Entregables\n\n")
                f.write("| Estado | Cantidad |\n")
                f.write("|--------|----------|\n")

                for _, row in entregables_status.iterrows():
                    f.write(f"| {row['Estado']} | {row['Cantidad']} |\n")

                f.write("\n")
            except:
                f.write(
                    "No se pudieron calcular metricas de estado de entregables.\n\n")

        # Indicadores adicionales si existen
        if 'eficiencia' in df.columns:
            f.write("## 3. Eficiencia\n\n")

            eficiencia_media = df['eficiencia'].mean()
            eficiencia_max = df['eficiencia'].max()
            eficiencia_min = df['eficiencia'].min()

            f.write(f"- Eficiencia promedio: {eficiencia_media:.4f}\n")
            f.write(f"- Eficiencia máxima: {eficiencia_max:.4f}\n")
            f.write(f"- Eficiencia mínima: {eficiencia_min:.4f}\n\n")

        f.write("## 4. Conclusiones y Recomendaciones\n\n")
        f.write(
            "- Se recomienda establecer metas de horas productivas por empleado y proyecto.\n")
        f.write("- Implementar revisiones periodicas de la calidad de entregables.\n")
        f.write(
            "- Definir acciones correctivas para mejorar la tasa de aprobacion de entregables.\n")
        f.write(
            "- Crear un sistema de recompensas para los empleados con mayor eficiencia.\n")

    print(f"Documento de KPIs generado exitosamente: {kpi_file}")
    return kpi_file


if __name__ == "__main__":
    generate_kpi_document()
