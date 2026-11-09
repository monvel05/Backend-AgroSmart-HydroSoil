# Backend — AgroSmart Hydro-Soil (FastAPI + MongoDB + IA + IoT ESP32)

Backend RESTful desarrollado en **Python con FastAPI** para el **Sistema Integral para la Gestión y Optimización de Riegos Agrícolas (Rodado e Hidropónico)**.

## Características Principales
- **Conexión a MongoDB Atlas (`.env`) + Respaldo Local Automático**: Funciona inmediatamente con los datos de prueba (`seed_data.py`) y se sincroniza automáticamente con MongoDB Atlas al colocar `MONGODB_URI` en `.env`.
- **4 Colecciones Oficiales**:
  1. `lecturas_sensores` (`electroconductividad`, `evaporacion_predicha`, `humedad_suelo`, `ph`, `tipo_cultivo`, `ubicacion`)
  2. `rutinas_riego` (`algoritmo_utilizado`, `estado`, `fecha_programada`, `parametros_optimizados`, `sector_id`)
  3. `bitacoras_sensores` (`agricultor_id`, `fecha_registro`, `texto_raw`, `procesamiento_ia`)
  4. `dispositivos_seguridad` (`dispositivo_id`, `estado_actual`, `tipo`, `seguridad`)
- **Despliegue Nativo de Modelos de Google Colab**: Coloca tus archivos `.joblib` en `ai_models/` (ver `ai_models/README_COLAB.md`).
- **Soporte Multi-Circuito IoT (ESP32)**: Endpoints `/api/iot/telemetria` y `/api/iot/comando/{dispositivo_id}` protegidos con `X-Device-Token` y generador de código `.ino`.

## Ejecución Rápida

```bash
# 1. Crear entorno virtual e instalar dependencias
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt

# 2. (Opcional) Poblar datos de prueba manualmente
.venv\Scripts\python seed.py

# 3. Iniciar servidor FastAPI en http://localhost:8000
.venv\Scripts\uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Documentación interactiva Swagger disponible en: `http://localhost:8000/docs`
