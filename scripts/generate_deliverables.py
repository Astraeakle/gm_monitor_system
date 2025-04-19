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

        # KPI 1: Horas trabajadas
        f.write("## 1. Horas Trabajadas\n\n")

        if 'horas_trabajadas' in df.columns and 'id_empleado' in df.columns:
            # Por empleado
            horas_por_empleado = df.groupby('id_empleado')[
                'horas_trabajadas'].sum().reset_index()
            horas_por_empleado = horas_por_empleado.sort_values(
                'horas_trabajadas', ascending=False)

            f.write("### 1.1 Total de Horas Trabajadas por Empleado\n\n")
            f.write("| ID Empleado | Horas Totales |\n")
            f.write("|------------|---------------|\n")

            for _, row in horas_por_empleado.iterrows():
                f.write(
                    f"| {row['id_empleado']} | {row['horas_trabajadas']:.2f} |\n")

            f.write("\n")

            # Mostrar estadísticas generales
            media_horas = horas_por_empleado['horas_trabajadas'].mean()
            max_horas = horas_por_empleado['horas_trabajadas'].max()
            min_horas = horas_por_empleado['horas_trabajadas'].min()

            f.write("### 1.2 Estadísticas de Horas Trabajadas\n\n")
            f.write(
                f"- **Promedio de horas trabajadas por empleado:** {media_horas:.2f}\n")
            f.write(
                f"- **Máximo de horas trabajadas por un empleado:** {max_horas:.2f}\n")
            f.write(
                f"- **Mínimo de horas trabajadas por un empleado:** {min_horas:.2f}\n\n")

            # Por proyecto
            if 'nombre_proyecto' in df.columns:
                horas_por_proyecto = df.groupby(['id_proyecto', 'nombre_proyecto'])[
                    'horas_trabajadas'].sum().reset_index()
                horas_por_proyecto = horas_por_proyecto.sort_values(
                    'horas_trabajadas', ascending=False)

                f.write("### 1.3 Total de Horas Trabajadas por Proyecto\n\n")
                f.write("| ID Proyecto | Nombre Proyecto | Horas Totales |\n")
                f.write("|------------|----------------|---------------|\n")

                for _, row in horas_por_proyecto.iterrows():
                    f.write(
                        f"| {row['id_proyecto']} | {row['nombre_proyecto']} | {row['horas_trabajadas']:.2f} |\n")

                f.write("\n")

        # KPI 2: Calidad de entregables
        f.write("## 2. Calidad de Entregables\n\n")

        # Entregables rechazados
        if 'entregables_rechazados' in df.columns and 'id_empleado' in df.columns:
            rechazos_por_empleado = df.groupby(
                'id_empleado')['entregables_rechazados'].sum().reset_index()
            rechazos_por_empleado = rechazos_por_empleado.sort_values(
                'entregables_rechazados', ascending=False)

            f.write("### 2.1 Entregables Rechazados por Empleado\n\n")
            f.write("| ID Empleado | Entregables Rechazados |\n")
            f.write("|------------|------------------------|\n")

            for _, row in rechazos_por_empleado.iterrows():
                f.write(
                    f"| {row['id_empleado']} | {int(row['entregables_rechazados'])} |\n")

            f.write("\n")

        # Tasa de rechazo
        if 'tasa_rechazo' in df.columns and 'id_empleado' in df.columns:
            tasa_por_empleado = df.groupby('id_empleado')[
                'tasa_rechazo'].mean().reset_index()
            tasa_por_empleado = tasa_por_empleado.sort_values(
                'tasa_rechazo', ascending=False)

            f.write("### 2.2 Tasa de Rechazo por Empleado (%)\n\n")
            f.write("| ID Empleado | Tasa de Rechazo (%) |\n")
            f.write("|------------|---------------------|\n")

            for _, row in tasa_por_empleado.iterrows():
                f.write(
                    f"| {row['id_empleado']} | {row['tasa_rechazo']:.2f}% |\n")

            f.write("\n")

        # KPI 3: Productividad
        f.write("## 3. Productividad\n\n")

        if 'horas_trabajadas' in df.columns and 'total_entregables' in df.columns:
            # Calcular entregables por hora
            df_prod = df.copy()
            df_prod['entregables_por_hora'] = df_prod.apply(
                lambda x: x['total_entregables'] /
                x['horas_trabajadas'] if x['horas_trabajadas'] > 0 else 0,
                axis=1
            )

            prod_por_empleado = df_prod.groupby(
                'id_empleado')['entregables_por_hora'].mean().reset_index()
            prod_por_empleado = prod_por_empleado.sort_values(
                'entregables_por_hora', ascending=False)

            f.write("### 3.1 Entregables por Hora Trabajada\n\n")
            f.write("| ID Empleado | Entregables por Hora |\n")
            f.write("|------------|----------------------|\n")

            for _, row in prod_por_empleado.iterrows():
                f.write(
                    f"| {row['id_empleado']} | {row['entregables_por_hora']:.2f} |\n")

            f.write("\n")

        # Conclusiones y recomendaciones
        f.write("## 4. Conclusiones y Recomendaciones\n\n")
        f.write(
            "- Se recomienda establecer metas de horas productivas por empleado y proyecto.\n")
        f.write("- Implementar revisiones periódicas de la calidad de entregables.\n")
        f.write(
            "- Definir acciones correctivas para mejorar la tasa de aprobación de entregables.\n")
        f.write(
            "- Crear un sistema de recompensas para los empleados con mayor eficiencia.\n")
        f.write(
            "- Establecer umbrales de alerta para tasas de rechazo superiores al 15%.\n")

    print(f"Documento de KPIs generado exitosamente: {kpi_file}")
    return kpi_file

if __name__ == "__main__":
    generate_kpi_document()
