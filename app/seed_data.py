"""
Datos semilla (Seed Data) para AgroSmart Hydro-Soil.
Incluye las 4 colecciones del diagrama de Base de Datos:
1. dispositivos_seguridad (Circuitos ESP32 por área de riego)
2. lecturas_sensores (Lecturas pH, EC, Humedad y Evaporación Predicha)
3. rutinas_riego (Rutinas optimizadas por IA y riegos manuales)
4. bitacoras_sensores (Reportes de campo clasificados con Minería de Texto)
+ Colección de usuarios para el Login.
"""

SEED_USUARIOS = [
    {
        "_id": "usr_001",
        "agricultor_id": "AGR-UTC-01",
        "nombre": "Ing. Monserrat Valdivia",
        "email": "admin@agrosmart.mx",
        "password": "admin123",
        "rol": "Administradora de Riego e IA",
        "unidad_produccion": "Rancho Experimental UTC - Calvillo",
    },
    {
        "_id": "usr_002",
        "agricultor_id": "AGR-UTC-02",
        "nombre": "Carlos Mendoza",
        "email": "campo@agrosmart.mx",
        "password": "campo123",
        "rol": "Operador de Campo y Fitosanidad",
        "unidad_produccion": "Invernaderos Hidropónicos Sur",
    },
]

SEED_DISPOSITIVOS_SEGURIDAD = [
    {
        "_id": "disp_001",
        "dispositivo_id": "ESP32-CIRCUITO-01",
        "nombre_circuito": "Circuito 1 — Guayaba y Maíz (Riego Rodado)",
        "sector_id": "Sector Norte - Parcela A1",
        "tipo_cultivo": "rodado",
        "estado_actual": "Activo",
        "valvula_abierta": False,
        "area_cobertura_m2": 450.0,
        "tipo": "ESP32 + Sensores pH/EC/Humedad + Electroválvula 1\"",
        "seguridad": {
            "intentos_no_autorizados": 0,
            "ip_asignada": "192.168.1.101",
            "token_autenticacion": "ags_tok_9f8e7d6c5b4a3f2e1d0c",
            "ultimo_acceso_autorizado": "2026-11-09T10:45:00",
        },
    },
    {
        "_id": "disp_002",
        "dispositivo_id": "ESP32-CIRCUITO-02",
        "nombre_circuito": "Circuito 2 — Fresa y Jitomate NFT (Hidropónico)",
        "sector_id": "Invernadero Hidropónico B2",
        "tipo_cultivo": "hidroponico",
        "estado_actual": "En Riego",
        "valvula_abierta": True,
        "area_cobertura_m2": 220.0,
        "tipo": "ESP32 + Bombas Dosificadoras A/B + Sonda EC/pH",
        "seguridad": {
            "intentos_no_autorizados": 1,
            "ip_asignada": "192.168.1.102",
            "token_autenticacion": "ags_tok_4a5b6c7d8e9f0a1b2c3d",
            "ultimo_acceso_autorizado": "2026-11-09T10:48:30",
        },
    },
    {
        "_id": "disp_003",
        "dispositivo_id": "ESP32-CIRCUITO-03",
        "nombre_circuito": "Circuito 3 — Hortalizas de Hoja (Cama Sustrato)",
        "sector_id": "Sector Sur - Parcela C1",
        "tipo_cultivo": "rodado",
        "estado_actual": "Alerta Seguridad",
        "valvula_abierta": False,
        "area_cobertura_m2": 320.0,
        "tipo": "ESP32 + Nodo LoRa/WiFi + Válvula Solenoide",
        "seguridad": {
            "intentos_no_autorizados": 4,
            "ip_asignada": "192.168.1.103",
            "token_autenticacion": "ags_tok_7c8d9e0f1a2b3c4d5e6f",
            "ultimo_acceso_autorizado": "2026-11-09T09:15:10",
        },
    },
]

SEED_LECTURAS_SENSORES = [
    {
        "_id": "lec_001",
        "dispositivo_id": "ESP32-CIRCUITO-01",
        "timestamp": "2026-11-09T10:45:00",
        "tipo_cultivo": "rodado",
        "lecturas": {
            "electroconductividad": 1.65,
            "evaporacion_predicha": 4.2,
            "humedad_suelo": 41.5,
            "ph": 6.4,
        },
        "ubicacion": {
            "coordenadas": [21.8469, -102.7188],
            "sector": "Sector Norte - Parcela A1",
        },
    },
    {
        "_id": "lec_002",
        "dispositivo_id": "ESP32-CIRCUITO-02",
        "timestamp": "2026-11-09T10:48:00",
        "tipo_cultivo": "hidroponico",
        "lecturas": {
            "electroconductividad": 2.35,
            "evaporacion_predicha": 2.8,
            "humedad_suelo": 78.2,
            "ph": 5.8,
        },
        "ubicacion": {
            "coordenadas": [21.8475, -102.7195],
            "sector": "Invernadero Hidropónico B2",
        },
    },
    {
        "_id": "lec_003",
        "dispositivo_id": "ESP32-CIRCUITO-03",
        "timestamp": "2026-11-09T10:40:00",
        "tipo_cultivo": "rodado",
        "lecturas": {
            "electroconductividad": 1.85,
            "evaporacion_predicha": 5.1,
            "humedad_suelo": 29.4,
            "ph": 6.9,
        },
        "ubicacion": {
            "coordenadas": [21.8452, -102.7172],
            "sector": "Sector Sur - Parcela C1",
        },
    },
    {
        "_id": "lec_004",
        "dispositivo_id": "ESP32-CIRCUITO-01",
        "timestamp": "2026-11-09T08:00:00",
        "tipo_cultivo": "rodado",
        "lecturas": {
            "electroconductividad": 1.58,
            "evaporacion_predicha": 3.9,
            "humedad_suelo": 48.0,
            "ph": 6.5,
        },
        "ubicacion": {
            "coordenadas": [21.8469, -102.7188],
            "sector": "Sector Norte - Parcela A1",
        },
    },
    {
        "_id": "lec_005",
        "dispositivo_id": "ESP32-CIRCUITO-02",
        "timestamp": "2026-11-09T08:00:00",
        "tipo_cultivo": "hidroponico",
        "lecturas": {
            "electroconductividad": 2.28,
            "evaporacion_predicha": 2.6,
            "humedad_suelo": 74.0,
            "ph": 5.9,
        },
        "ubicacion": {
            "coordenadas": [21.8475, -102.7195],
            "sector": "Invernadero Hidropónico B2",
        },
    },
]

SEED_RUTINAS_RIEGO = [
    {
        "_id": "rut_001",
        "dispositivo_id": "ESP32-CIRCUITO-01",
        "sector_id": "Sector Norte - Parcela A1",
        "tipo_cultivo": "rodado",
        "modo": "automatico_ia",
        "algoritmo_utilizado": "Algoritmo Genético + Red Neuronal Evaporación",
        "estado": "Programado",
        "fecha_programada": "2026-11-09T18:30:00",
        "parametros_optimizados": {
            "duracion_minutos": 35,
            "volumen_agua_litros": 420.5,
            "mezcla_fertirriego": {
                "nutriente_a": 45,
                "nutriente_b": 30,
            },
        },
    },
    {
        "_id": "rut_002",
        "dispositivo_id": "ESP32-CIRCUITO-02",
        "sector_id": "Invernadero Hidropónico B2",
        "tipo_cultivo": "hidroponico",
        "modo": "automatico_ia",
        "algoritmo_utilizado": "Búsqueda Heurística A* + Red Neuronal Sustrato",
        "estado": "En Curso",
        "fecha_programada": "2026-11-09T10:30:00",
        "parametros_optimizados": {
            "duracion_minutos": 18,
            "volumen_agua_litros": 145.0,
            "mezcla_fertirriego": {
                "nutriente_a": 80,
                "nutriente_b": 65,
            },
        },
    },
    {
        "_id": "rut_003",
        "dispositivo_id": "ESP32-CIRCUITO-03",
        "sector_id": "Sector Sur - Parcela C1",
        "tipo_cultivo": "rodado",
        "modo": "manual",
        "algoritmo_utilizado": "Configuración Manual de Operador",
        "estado": "Completado",
        "fecha_programada": "2026-11-09T06:30:00",
        "parametros_optimizados": {
            "duracion_minutos": 25,
            "volumen_agua_litros": 310.0,
            "mezcla_fertirriego": {
                "nutriente_a": 25,
                "nutriente_b": 20,
            },
        },
    },
]

SEED_BITACORAS_SENSORES = [
    {
        "_id": "bit_001",
        "agricultor_id": "AGR-UTC-01",
        "dispositivo_id": "ESP32-CIRCUITO-02",
        "sector_id": "Invernadero Hidropónico B2",
        "fecha_registro": "2026-11-09T09:30:00",
        "texto_raw": "Se observan colonias de mosca blanca en el envés de las hojas de jitomate hidropónico de la línea 3, con ligero amarillamiento y melaza pegajosa.",
        "procesamiento_ia": {
            "categoria": "Alerta Fitosanitaria - Plaga",
            "clasificado": True,
            "nivel_urgencia": "Alta",
            "palabras_clave": ["mosca blanca", "envés", "amarillamiento", "melaza", "jitomate"],
            "plaga_detectada": "Mosca Blanca (Bemisia tabaci)",
        },
    },
    {
        "_id": "bit_002",
        "agricultor_id": "AGR-UTC-02",
        "dispositivo_id": "ESP32-CIRCUITO-03",
        "sector_id": "Sector Sur - Parcela C1",
        "fecha_registro": "2026-11-09T08:15:00",
        "texto_raw": "Presencia de araña roja y pequeñas telarañas en los brotes tiernos del sector sur debido a las altas temperaturas y baja humedad de ayer.",
        "procesamiento_ia": {
            "categoria": "Alerta Fitosanitaria - Ácaros",
            "clasificado": True,
            "nivel_urgencia": "Crítica",
            "palabras_clave": ["araña roja", "telarañas", "brotes tiernos", "baja humedad"],
            "plaga_detectada": "Araña Roja (Tetranychus urticae)",
        },
    },
    {
        "_id": "bit_003",
        "agricultor_id": "AGR-UTC-01",
        "dispositivo_id": "ESP32-CIRCUITO-01",
        "sector_id": "Sector Norte - Parcela A1",
        "fecha_registro": "2026-11-08T17:40:00",
        "texto_raw": "Revisión rutinaria del circuito 1 de riego rodado. Las plantas presentan vigor saludable, follaje verde oscuro y sin rastro de insectos ni hongos.",
        "procesamiento_ia": {
            "categoria": "Monitoreo Preventivo - Sin Plaga",
            "clasificado": True,
            "nivel_urgencia": "Baja",
            "palabras_clave": ["revisión rutinaria", "vigor saludable", "follaje verde", "sin rastro"],
            "plaga_detectada": "Ninguna (Cultivo Sano)",
        },
    },
]
