# Guía de Despliegue e Integración de Modelos desde Google Colab

Dado que el backend de **AgroSmart Hydro-Soil** está construido en **Python con FastAPI**, la forma más óptima, rápida y sin latencia de red adicional es **exportar los modelos entrenados en Google Colab como archivos `.joblib` (o `.keras` / `.h5`) y colocarlos directamente en esta carpeta (`ai_models/`)**.

El servicio `app/services/ai_service.py` detecta automáticamente si los archivos existen al iniciar el servidor:
- **Con archivos en `ai_models/`**: Ejecuta inferencia real con tus modelos entrenados.
- **Mientras siguen en entrenamiento**: Utiliza el motor heurístico/genético y léxico integrado para que toda la plataforma web funcione sin interrupciones.

---

## 1. Cómo exportar el Modelo 1: Detección de Plagas (Minería de Texto)

Al final de tu notebook de Google Colab donde entrenas el clasificador de bitácoras (`bitacoras_sensores`), agrega y ejecuta esta celda:

```python
import joblib
from google.colab import files

# Si usaste un Pipeline de Scikit-Learn (ej. TfidfVectorizer + MultinomialNB / RandomForest / SVM):
joblib.dump(modelo_plagas, 'modelo_plagas_nlp.joblib')
files.download('modelo_plagas_nlp.joblib')

# Si entrenaste el vectorizador por separado del clasificador:
joblib.dump(vectorizador_tfidf, 'vectorizador_plagas.joblib')
files.download('vectorizador_plagas.joblib')
```

### Ubicación y Formato Esperado
Coloca `modelo_plagas_nlp.joblib` (y opcionalmente `vectorizador_plagas.joblib`) dentro de `Backend-AgroSmart-HydroSoil/ai_models/`.
- **Entrada que le pasará FastAPI**: `texto_raw` (string redactado por el agricultor).
- **Salida generada para MongoDB (`procesamiento_ia`)**:
  ```json
  {
    "categoria": "Control Fitosanitario",
    "clasificado": true,
    "nivel_urgencia": "Alta",
    "palabras_clave": ["mosca blanca", "envés", "amarillamiento"],
    "plaga_detectada": "Mosca Blanca (Bemisia tabaci)"
  }
  ```

---

## 2. Cómo exportar el Modelo 2: Previsión de Riego y Evaporación

Al final de tu notebook de Google Colab donde entrenas la predicción de evaporación y optimización de riego:

```python
import joblib
from google.colab import files

# Para modelos Scikit-Learn / XGBoost / Redes Neuronales MLPRegressor:
joblib.dump(modelo_riego, 'modelo_prevision_riego.joblib')
files.download('modelo_prevision_riego.joblib')
```

*(Nota: Si usas TensorFlow/Keras, puedes guardarlo como `modelo_prevision_riego.keras` y cargarlo con `tf.keras.models.load_model` en `app/services/ai_service.py`).*

### Ubicación y Formato Esperado
Coloca `modelo_prevision_riego.joblib` dentro de `Backend-AgroSmart-HydroSoil/ai_models/`.
- **Vector de características de entrada (`X`)**:
  `[humedad_suelo, ph, electroconductividad, es_hidroponico (1 o 0)]`
- **Salida generada para MongoDB (`rutinas_riego` y `lecturas_sensores`)**:
  - `evaporacion_predicha` (mm/día)
  - `duracion_minutos` (int)
  - `volumen_agua_litros` (double)
  - `mezcla_fertirriego`: `{ "nutriente_a": int, "nutriente_b": int }`
  - `algoritmo_utilizado`: `"Red Neuronal MLP + Algoritmo Genético (Colab)"`
