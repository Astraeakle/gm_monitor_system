from utils.principles import MonitoringPrinciples
from scripts.generate_deliverables import generate_kpi_document
from scripts.insert_test_data import insert_test_data
from tests.test_connection import test_mysql_connection
from scripts.data_standardization import DataStandardizer
import os
import sys
from datetime import datetime

# Configurar paths
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)


def show_system_principles():
    """Muestra los principios del sistema de monitoreo"""
    principles = MonitoringPrinciples.get_non_intrusive_principles()
    print(f"\n{principles['title'].upper()}")
    print("-" * len(principles['title']))
    print(principles['description'])
    print("\nPrincipios:")
    for i, principle in enumerate(principles['principles'], 1):
        print(f"{i}. {principle}")
    print()


def main():
    print("=" * 80)
    print(" SISTEMA DE MONITOREO DE PRODUCTIVIDAD REMOTA Y CALIDAD DE ENTREGABLES ")
    print("=" * 80)
    print(
        f"Fecha de ejecucion: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 80)

    print("\n1. Verificando conexion a la base de datos...")
    test_mysql_connection()

    print("\n2. Verificando y cargando datos de prueba...")
    insert_test_data()

    print("\n3. Iniciando proceso de estandarizacion de datos...")
    standardizer = DataStandardizer()
    df = standardizer.run()

    if df is not None and not df.empty:
        print("\n4. Generando documentos entregables...")
        kpi_doc = generate_kpi_document()
        print(f"Documento de KPIs generado: {kpi_doc}")

        print("\nProceso completado con exito.")
    else:
        print("\nNo se pudo completar el proceso debido a errores en los datos.")


if __name__ == "__main__":
    main()

