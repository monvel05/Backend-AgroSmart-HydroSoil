"""
Script ejecutable para poblar/reiniciar la base de datos (MongoDB Atlas o respaldo local)
con los datos de prueba de AgroSmart Hydro-Soil.

Uso:
    python seed.py
"""

from app.database import db_manager

if __name__ == "__main__":
    print("=== AgroSmart Hydro-Soil: Inicializando Datos de Prueba (Seed) ===")
    resumen = db_manager.reset_seed_data()
    print(f"Estado de conexión: {db_manager.connection_status}")
    for coleccion, cantidad in resumen.items():
        print(f"  - {coleccion}: {cantidad} documentos insertados")
    print("=== Proceso finalizado con éxito ===")
