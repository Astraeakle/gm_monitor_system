from utils.principles import MonitoringPrinciples
from scripts.generate_deliverables import generate_kpi_document
from scripts.insert_test_data import verify_data_exists
from scripts.sql_metrics import run_metrics_report
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
        f"Fecha de ejecución: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 80)

    # Mostrar principios del sistema
    show_system_principles()

    print("\n1. Verificando conexión a la base de datos...")
    test_mysql_connection()

    print("\n2. Verificando existencia de datos...")
    data_exists = verify_data_exists()

    if not data_exists:
        print(
            "\n[ADVERTENCIA] ADVERTENCIA: No se encontraron datos suficientes en la base de datos.")
        print("Por favor, verifique que los datos han sido correctamente cargados.")
        return

    print("\n3. Iniciando proceso de estandarización de datos...")
    standardizer = DataStandardizer()
    df = standardizer.run()

    if df is not None and not df.empty:
        print(
            f"\nDataset unificado creado exitosamente con {len(df)} registros")
        print("\n4. Generando documento de KPIs...")
        kpi_doc = generate_kpi_document()
        print(f"Documento de KPIs generado: {kpi_doc}")

        # Guardar el dataset unificado
        output_dir = os.path.join(current_dir, 'entregables')
        os.makedirs(output_dir, exist_ok=True)
        dataset_file = os.path.join(
            output_dir, f'dataset_unificado_{datetime.now().strftime("%Y%m%d")}.csv')
        df.to_csv(dataset_file, index=False)
        print(f"\nDataset unificado guardado en: {dataset_file}")

        print("\n[OK] Proceso completado con exito.")
        print("\nEntregables generados:")
        print(f"- Documento de KPIs: {os.path.basename(kpi_doc)}")
        print(f"- Dataset unificado: {os.path.basename(dataset_file)}")

    else:
        print(
            "\n[ERROR] No se pudo completar el proceso debido a errores en los datos.")

    print("\n5. Generando métricas SQL de productividad...")
    metrics_results = run_metrics_report()
    
if __name__ == "__main__":
    main()
