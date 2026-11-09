import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


class Settings:
    MONGODB_URI: str = os.getenv("MONGODB_URI", "").strip()
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "agrosmart_hydrosoil").strip()
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "agrosmart-utc-super-secret-key-2026")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

    AI_MODELS_DIR: Path = BASE_DIR / os.getenv("AI_MODELS_DIR", "ai_models")
    PLAGUE_MODEL_FILE: Path = BASE_DIR / os.getenv(
        "PLAGUE_MODEL_FILE", "ai_models/modelo_plagas_nlp.joblib"
    )
    PLAGUE_VECTORIZER_FILE: Path = BASE_DIR / os.getenv(
        "PLAGUE_VECTORIZER_FILE", "ai_models/vectorizador_plagas.joblib"
    )
    IRRIGATION_MODEL_FILE: Path = BASE_DIR / os.getenv(
        "IRRIGATION_MODEL_FILE", "ai_models/modelo_prevision_riego.joblib"
    )

    EXTERNAL_PLAGUE_API_URL: str = os.getenv("EXTERNAL_PLAGUE_API_URL", "").strip()
    EXTERNAL_IRRIGATION_API_URL: str = os.getenv("EXTERNAL_IRRIGATION_API_URL", "").strip()


settings = Settings()
