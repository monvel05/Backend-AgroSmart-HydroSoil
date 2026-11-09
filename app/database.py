"""
Capa de Acceso a Datos (MongoDB + Respaldo Local Automático).
- Si `MONGODB_URI` está configurada en `.env` y el servidor MongoDB responde,
  opera directamente sobre MongoDB (Atlas o Local) e inicializa las 4 colecciones
  con los datos de prueba si están vacías.
- Si `MONGODB_URI` aún está vacía (mientras el usuario crea su cluster en Atlas),
  utiliza un almacén persistente en JSON (`local_db_store.json`) pre-poblado con
  los mismos datos de prueba (`seed_data.py`), garantizando que todo el sistema
  funcione al 100% de inmediato.
"""

import copy
import json
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional
from pymongo import MongoClient
from pymongo.errors import PyMongoError

from app.config import settings, BASE_DIR
from app.seed_data import (
    SEED_BITACORAS_SENSORES,
    SEED_DISPOSITIVOS_SEGURIDAD,
    SEED_LECTURAS_SENSORES,
    SEED_RUTINAS_RIEGO,
    SEED_USUARIOS,
)

LOCAL_STORE_PATH: Path = BASE_DIR / "local_db_store.json"


class DatabaseManager:
    def __init__(self):
        self.client: Optional[MongoClient] = None
        self.db = None
        self.using_mongodb: bool = False
        self.connection_status: str = "Modo Local con Datos de Prueba (Configura MONGODB_URI en .env para MongoDB Atlas)"
        self._local_data: Dict[str, List[Dict[str, Any]]] = {}
        self.connect()

    def connect(self):
        uri = settings.MONGODB_URI
        if uri and "<usuario>" not in uri and "tu_usuario" not in uri:
            try:
                self.client = MongoClient(uri, serverSelectionTimeoutMS=4000)
                self.client.admin.command("ping")
                self.db = self.client[settings.DATABASE_NAME]
                self.using_mongodb = True
                self.connection_status = f"Conectado a MongoDB ({settings.DATABASE_NAME})"
                print(f"[DB] {self.connection_status}")
                self._ensure_mongodb_seeded()
                return
            except PyMongoError as e:
                print(f"[DB] No se pudo conectar a MongoDB ({e}). Activando almacén local de respaldo.")
                self.using_mongodb = False
                self.connection_status = f"Respaldo Local Activo (Error al conectar a MongoDB: {str(e)[:80]})"

        self._load_or_init_local_store()

    def _ensure_mongodb_seeded(self):
        """Si la base de datos en MongoDB está vacía, inserta los datos de prueba iniciales."""
        if not self.using_mongodb or self.db is None:
            return
        collections_map = {
            "usuarios": SEED_USUARIOS,
            "dispositivos_seguridad": SEED_DISPOSITIVOS_SEGURIDAD,
            "lecturas_sensores": SEED_LECTURAS_SENSORES,
            "rutinas_riego": SEED_RUTINAS_RIEGO,
            "bitacoras_sensores": SEED_BITACORAS_SENSORES,
        }
        for col_name, seed_items in collections_map.items():
            if self.db[col_name].count_documents({}) == 0:
                self.db[col_name].insert_many(copy.deepcopy(seed_items))
                print(f"[DB Seed] Colección '{col_name}' inicializada con {len(seed_items)} documentos.")

    def _load_or_init_local_store(self):
        if LOCAL_STORE_PATH.exists():
            try:
                with open(LOCAL_STORE_PATH, "r", encoding="utf-8") as f:
                    self._local_data = json.load(f)
                return
            except Exception:
                pass
        self.reset_seed_data()

    def _save_local_store(self):
        try:
            with open(LOCAL_STORE_PATH, "w", encoding="utf-8") as f:
                json.dump(self._local_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[DB Local] Error guardando local_db_store.json: {e}")

    def reset_seed_data(self) -> Dict[str, int]:
        """Restaura o inicializa todas las colecciones con los datos de prueba."""
        seed_map = {
            "usuarios": copy.deepcopy(SEED_USUARIOS),
            "dispositivos_seguridad": copy.deepcopy(SEED_DISPOSITIVOS_SEGURIDAD),
            "lecturas_sensores": copy.deepcopy(SEED_LECTURAS_SENSORES),
            "rutinas_riego": copy.deepcopy(SEED_RUTINAS_RIEGO),
            "bitacoras_sensores": copy.deepcopy(SEED_BITACORAS_SENSORES),
        }
        if self.using_mongodb and self.db is not None:
            for col_name, docs in seed_map.items():
                self.db[col_name].delete_many({})
                if docs:
                    self.db[col_name].insert_many(docs)
        else:
            self._local_data = seed_map
            self._save_local_store()

        return {k: len(v) for k, v in seed_map.items()}

    # Métodos CRUD unificados (funcionan idéntico en MongoDB Atlas o en respaldo local)
    def find_all(self, collection: str) -> List[Dict[str, Any]]:
        if self.using_mongodb and self.db is not None:
            docs = list(self.db[collection].find({}))
            for d in docs:
                d["_id"] = str(d["_id"])
            return docs
        return copy.deepcopy(self._local_data.get(collection, []))

    def find_one(self, collection: str, filters: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if self.using_mongodb and self.db is not None:
            doc = self.db[collection].find_one(filters)
            if doc:
                doc["_id"] = str(doc["_id"])
            return doc
        for item in self._local_data.get(collection, []):
            if all(item.get(k) == v for k, v in filters.items()):
                return copy.deepcopy(item)
        return None

    def insert_one(self, collection: str, doc: Dict[str, Any], prefix: str = "doc") -> Dict[str, Any]:
        new_doc = copy.deepcopy(doc)
        if not new_doc.get("_id"):
            new_doc["_id"] = f"{prefix}_{uuid.uuid4().hex[:8]}"
        if self.using_mongodb and self.db is not None:
            self.db[collection].insert_one(copy.deepcopy(new_doc))
        else:
            self._local_data.setdefault(collection, []).insert(0, new_doc)
            self._save_local_store()
        return new_doc

    def update_one(self, collection: str, filters: Dict[str, Any], update_fields: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if self.using_mongodb and self.db is not None:
            self.db[collection].update_one(filters, {"$set": update_fields})
            return self.find_one(collection, filters)

        items = self._local_data.get(collection, [])
        for idx, item in enumerate(items):
            if all(item.get(k) == v for k, v in filters.items()):
                for uk, uv in update_fields.items():
                    if "." in uk:
                        parent, child = uk.split(".", 1)
                        item.setdefault(parent, {})[child] = uv
                    else:
                        item[uk] = uv
                items[idx] = item
                self._save_local_store()
                return copy.deepcopy(item)
        return None

    def delete_one(self, collection: str, filters: Dict[str, Any]) -> bool:
        if self.using_mongodb and self.db is not None:
            res = self.db[collection].delete_one(filters)
            return res.deleted_count > 0

        items = self._local_data.get(collection, [])
        for idx, item in enumerate(items):
            if all(item.get(k) == v for k, v in filters.items()):
                items.pop(idx)
                self._save_local_store()
                return True
        return False


db_manager = DatabaseManager()
