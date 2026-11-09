from datetime import datetime
import secrets
from typing import Optional
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from app.database import db_manager
from app.models import (
    BitacoraCreateRequest,
    LoginRequest,
    NuevoCircuitoRequest,
    OptimizarRiegoIARequest,
    RegisterRequest,
    RiegoManualRequest,
    TelemetriaIoTInput,
    ToggleValvulaRequest,
)
from app.services.ai_service import ai_service

app = FastAPI(
    title="AgroSmart Hydro-Soil API",
    description=(
        "Sistema Integral para la Gestión y Optimización de Riegos Agrícolas (Rodado e Hidropónico). "
        "Incluye integración con MongoDB, 2 Modelos de IA (Minería de Texto para Plagas y Previsión/Optimización de Riego) "
        "y Gestión Multi-Circuito IoT para ESP32."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def now_iso() -> str:
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


# ==============================================================================
# 0. ESTADO DEL SISTEMA Y SEED DE BASE DE DATOS
# ==============================================================================
@app.get("/api/status")
def get_system_status():
    return {
        "sistema": "AgroSmart Hydro-Soil API",
        "timestamp": now_iso(),
        "database": {
            "using_mongodb": db_manager.using_mongodb,
            "status": db_manager.connection_status,
        },
        "ia_models": ai_service.get_status(),
    }


@app.post("/api/seed")
def seed_database():
    counts = db_manager.reset_seed_data()
    return {
        "mensaje": "Datos de prueba restaurados correctamente en las colecciones.",
        "colecciones": counts,
        "using_mongodb": db_manager.using_mongodb,
    }


# ==============================================================================
# 1. AUTENTICACIÓN Y USUARIOS (LOGIN)
# ==============================================================================
@app.post("/api/auth/login")
def login(req: LoginRequest):
    usuarios = db_manager.find_all("usuarios")
    user = next(
        (
            u
            for u in usuarios
            if u.get("email", "").lower() == req.email.strip().lower()
            and u.get("password") == req.password
        ),
        None,
    )
    if not user:
        raise HTTPException(status_code=401, detail="Credenciales incorrectas. Verifica tu correo y contraseña.")

    token = f"jwt_ags_{secrets.token_hex(16)}"
    return {
        "access_token": token,
        "token_type": "bearer",
        "usuario": {
            "_id": user.get("_id"),
            "agricultor_id": user.get("agricultor_id", "AGR-UTC-01"),
            "nombre": user.get("nombre"),
            "email": user.get("email"),
            "rol": user.get("rol"),
            "unidad_produccion": user.get("unidad_produccion", "Rancho Experimental UTC"),
        },
    }


@app.post("/api/auth/register")
def register(req: RegisterRequest):
    usuarios = db_manager.find_all("usuarios")
    if any(u.get("email", "").lower() == req.email.strip().lower() for u in usuarios):
        raise HTTPException(status_code=400, detail="El correo electrónico ya está registrado.")

    agricultor_id = req.agricultor_id or f"AGR-UTC-0{len(usuarios) + 1}"
    nuevo_usuario = db_manager.insert_one(
        "usuarios",
        {
            "agricultor_id": agricultor_id,
            "nombre": req.nombre,
            "email": req.email.strip().lower(),
            "password": req.password,
            "rol": req.rol,
            "unidad_produccion": "Rancho Experimental UTC - Calvillo",
        },
        prefix="usr",
    )
    token = f"jwt_ags_{secrets.token_hex(16)}"
    return {
        "access_token": token,
        "token_type": "bearer",
        "usuario": {
            "_id": nuevo_usuario["_id"],
            "agricultor_id": nuevo_usuario["agricultor_id"],
            "nombre": nuevo_usuario["nombre"],
            "email": nuevo_usuario["email"],
            "rol": nuevo_usuario["rol"],
            "unidad_produccion": nuevo_usuario["unidad_produccion"],
        },
    }


# ==============================================================================
# 2. DASHBOARD PRINCIPAL CONSOLIDADO
# ==============================================================================
@app.get("/api/dashboard")
def get_dashboard(dispositivo_id: Optional[str] = None, tipo_cultivo: Optional[str] = None):
    circuitos = db_manager.find_all("dispositivos_seguridad")
    lecturas = db_manager.find_all("lecturas_sensores")
    rutinas = db_manager.find_all("rutinas_riego")
    bitacoras = db_manager.find_all("bitacoras_sensores")

    if dispositivo_id and dispositivo_id != "todos":
        lecturas_filtradas = [l for l in lecturas if l.get("dispositivo_id") == dispositivo_id]
        rutinas_filtradas = [
            r for r in rutinas if r.get("dispositivo_id") == dispositivo_id or r.get("sector_id") in [
                c.get("sector_id") for c in circuitos if c.get("dispositivo_id") == dispositivo_id
            ]
        ]
    else:
        lecturas_filtradas = lecturas
        rutinas_filtradas = rutinas

    if tipo_cultivo and tipo_cultivo != "todos":
        lecturas_filtradas = [l for l in lecturas_filtradas if l.get("tipo_cultivo") == tipo_cultivo]

    # Ordenar lecturas más recientes primero
    lecturas_filtradas.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    ultima_lectura = lecturas_filtradas[0] if lecturas_filtradas else (lecturas[0] if lecturas else None)

    total_intentos_intrusion = sum(
        c.get("seguridad", {}).get("intentos_no_autorizados", 0) for c in circuitos
    )
    valvulas_activas = sum(1 for c in circuitos if c.get("valvula_abierta") is True)
    alertas_plagas = [
        b
        for b in bitacoras
        if b.get("procesamiento_ia", {}).get("nivel_urgencia") in ["Alta", "Crítica"]
    ]

    return {
        "resumen": {
            "total_circuitos": len(circuitos),
            "valvulas_abiertas": valvulas_activas,
            "total_lecturas": len(lecturas),
            "rutinas_activas": sum(1 for r in rutinas if r.get("estado") in ["Programado", "En Curso", "Manual Activo"]),
            "alertas_plagas_activas": len(alertas_plagas),
            "intentos_no_autorizados_totales": total_intentos_intrusion,
        },
        "ultima_lectura": ultima_lectura,
        "lecturas_recientes": lecturas_filtradas[:8],
        "circuitos": circuitos,
        "rutinas_recientes": rutinas_filtradas[:6],
        "bitacoras_recientes": bitacoras[:5],
        "estado_ia": ai_service.get_status(),
        "database_status": db_manager.connection_status,
    }


# ==============================================================================
# 3. LECTURAS DE SENSORES (`lecturas_sensores`)
# ==============================================================================
@app.get("/api/lecturas")
def listar_lecturas(dispositivo_id: Optional[str] = None, tipo_cultivo: Optional[str] = None):
    lecturas = db_manager.find_all("lecturas_sensores")
    if dispositivo_id and dispositivo_id != "todos":
        lecturas = [l for l in lecturas if l.get("dispositivo_id") == dispositivo_id]
    if tipo_cultivo and tipo_cultivo != "todos":
        lecturas = [l for l in lecturas if l.get("tipo_cultivo") == tipo_cultivo]
    lecturas.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    return lecturas


@app.post("/api/lecturas/simular")
def simular_nueva_lectura(req: OptimizarRiegoIARequest):
    """Permite simular o registrar una lectura de sensores desde la interfaz web calculando la evaporación predicha por IA."""
    humedad = req.humedad_suelo if req.humedad_suelo is not None else 44.0
    ph = req.ph if req.ph is not None else 6.2
    ec = req.electroconductividad if req.electroconductividad is not None else 1.8

    pred_ia = ai_service.optimizar_riego(
        humedad_suelo=humedad,
        ph=ph,
        electroconductividad=ec,
        tipo_cultivo=req.tipo_cultivo,
    )

    nueva_lectura = {
        "dispositivo_id": req.dispositivo_id,
        "timestamp": now_iso(),
        "tipo_cultivo": req.tipo_cultivo,
        "lecturas": {
            "electroconductividad": round(ec, 2),
            "evaporacion_predicha": pred_ia["evaporacion_predicha"],
            "humedad_suelo": round(humedad, 1),
            "ph": round(ph, 2),
        },
        "ubicacion": {
            "coordenadas": [21.8469, -102.7188],
            "sector": req.sector_id,
        },
    }
    guardada = db_manager.insert_one("lecturas_sensores", nueva_lectura, prefix="lec")
    return guardada


# ==============================================================================
# 4. RUTINAS DE RIEGO: MANUALES Y OPTIMIZADAS CON IA (`rutinas_riego`)
# ==============================================================================
@app.get("/api/rutinas")
def listar_rutinas(dispositivo_id: Optional[str] = None):
    rutinas = db_manager.find_all("rutinas_riego")
    if dispositivo_id and dispositivo_id != "todos":
        rutinas = [r for r in rutinas if r.get("dispositivo_id") == dispositivo_id]
    return rutinas


@app.post("/api/rutinas/manual")
def crear_riego_manual(req: RiegoManualRequest):
    """Configura un riego manual para un circuito ESP32 específico y abre la electroválvula si ejecutar_ahora=True."""
    estado_rutina = "Manual Activo" if req.ejecutar_ahora else "Programado"
    fecha = req.fecha_programada if req.fecha_programada else now_iso()

    nueva_rutina = {
        "dispositivo_id": req.dispositivo_id,
        "sector_id": req.sector_id,
        "tipo_cultivo": req.tipo_cultivo,
        "modo": "manual",
        "algoritmo_utilizado": "Configuración Manual de Operador",
        "estado": estado_rutina,
        "fecha_programada": fecha,
        "parametros_optimizados": {
            "duracion_minutos": req.duracion_minutos,
            "volumen_agua_litros": req.volumen_agua_litros,
            "mezcla_fertirriego": {
                "nutriente_a": req.nutriente_a,
                "nutriente_b": req.nutriente_b,
            },
        },
    }
    doc = db_manager.insert_one("rutinas_riego", nueva_rutina, prefix="rut")

    # Si se ordena ejecutar ahora, abrimos la electroválvula del circuito ESP32 correspondiente
    if req.ejecutar_ahora:
        db_manager.update_one(
            "dispositivos_seguridad",
            {"dispositivo_id": req.dispositivo_id},
            {
                "valvula_abierta": True,
                "estado_actual": "En Riego Manual",
                "seguridad.ultimo_acceso_autorizado": now_iso(),
            },
        )

    return doc


@app.post("/api/rutinas/optimizar-ia")
def generar_rutina_optimizada_ia(req: OptimizarRiegoIARequest):
    """
    Ejecuta el Modelo 2 de IA (Previsión de Evaporación + Optimización Genética/Heurística)
    usando las últimas lecturas del circuito ESP32 o los valores enviados, y guarda la rutina en `rutinas_riego`.
    """
    circuito = db_manager.find_one("dispositivos_seguridad", {"dispositivo_id": req.dispositivo_id})
    area_m2 = circuito.get("area_cobertura_m2", 250.0) if circuito else 250.0

    # Buscar última lectura del circuito si no se enviaron parámetros manuales
    lecturas = [
        l for l in db_manager.find_all("lecturas_sensores") if l.get("dispositivo_id") == req.dispositivo_id
    ]
    lecturas.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    ultima = lecturas[0]["lecturas"] if lecturas else {}

    humedad = req.humedad_suelo if req.humedad_suelo is not None else ultima.get("humedad_suelo", 42.0)
    ph = req.ph if req.ph is not None else ultima.get("ph", 6.2)
    ec = req.electroconductividad if req.electroconductividad is not None else ultima.get("electroconductividad", 1.8)

    resultado_ia = ai_service.optimizar_riego(
        humedad_suelo=humedad,
        ph=ph,
        electroconductividad=ec,
        tipo_cultivo=req.tipo_cultivo,
        area_cobertura_m2=area_m2,
    )

    nueva_rutina = {
        "dispositivo_id": req.dispositivo_id,
        "sector_id": req.sector_id,
        "tipo_cultivo": req.tipo_cultivo,
        "modo": "automatico_ia",
        "algoritmo_utilizado": resultado_ia["algoritmo_utilizado"],
        "estado": "Programado",
        "fecha_programada": now_iso(),
        "parametros_optimizados": resultado_ia["parametros_optimizados"],
    }
    guardada = db_manager.insert_one("rutinas_riego", nueva_rutina, prefix="rut")
    return {
        "rutina": guardada,
        "evaporacion_predicha": resultado_ia["evaporacion_predicha"],
        "lecturas_base": {
            "humedad_suelo": humedad,
            "ph": ph,
            "electroconductividad": ec,
        },
    }


@app.patch("/api/rutinas/{rutina_id}/estado")
def actualizar_estado_rutina(rutina_id: str, estado: str):
    rutina = db_manager.update_one("rutinas_riego", {"_id": rutina_id}, {"estado": estado})
    if not rutina:
        raise HTTPException(status_code=404, detail="Rutina no encontrada.")

    # Sincronizar estado de válvula del circuito si pasa a En Curso o Completado
    disp_id = rutina.get("dispositivo_id")
    if disp_id:
        if estado in ["En Curso", "Manual Activo"]:
            db_manager.update_one(
                "dispositivos_seguridad",
                {"dispositivo_id": disp_id},
                {"valvula_abierta": True, "estado_actual": "En Riego"},
            )
        elif estado in ["Completado", "Cancelado"]:
            db_manager.update_one(
                "dispositivos_seguridad",
                {"dispositivo_id": disp_id},
                {"valvula_abierta": False, "estado_actual": "Activo"},
            )
    return rutina


@app.delete("/api/rutinas/{rutina_id}")
def eliminar_rutina(rutina_id: str):
    ok = db_manager.delete_one("rutinas_riego", {"_id": rutina_id})
    if not ok:
        raise HTTPException(status_code=404, detail="Rutina no encontrada.")
    return {"eliminado": True, "_id": rutina_id}


# ==============================================================================
# 5. BITÁCORAS DE CAMPO Y DETECCIÓN DE PLAGAS IA (`bitacoras_sensores`)
# ==============================================================================
@app.get("/api/bitacoras")
def listar_bitacoras():
    bitacoras = db_manager.find_all("bitacoras_sensores")
    bitacoras.sort(key=lambda x: x.get("fecha_registro", ""), reverse=True)
    return bitacoras


@app.post("/api/ia/analizar-texto")
def previsualizar_analisis_plagas(payload: dict):
    """Permite probar en vivo el Modelo 1 (Minería de Texto) sin guardar todavía en BD."""
    texto = payload.get("texto_raw", "")
    if not texto.strip():
        raise HTTPException(status_code=400, detail="El texto de la bitácora no puede estar vacío.")
    return ai_service.analizar_bitacora_plagas(texto)


@app.post("/api/bitacoras")
def crear_bitacora_con_ia(req: BitacoraCreateRequest):
    """
    Recibe `texto_raw` del agricultor, ejecuta el Modelo 1 de Minería de Texto para detectar plagas,
    extraer palabras clave y calcular urgencia, y almacena el documento en `bitacoras_sensores`.
    """
    procesamiento = ai_service.analizar_bitacora_plagas(req.texto_raw)
    nueva_bitacora = {
        "agricultor_id": req.agricultor_id,
        "dispositivo_id": req.dispositivo_id,
        "sector_id": req.sector_id,
        "fecha_registro": now_iso(),
        "texto_raw": req.texto_raw,
        "procesamiento_ia": procesamiento,
    }
    return db_manager.insert_one("bitacoras_sensores", nueva_bitacora, prefix="bit")


# ==============================================================================
# 6. GESTIÓN MULTI-CIRCUITO ESP32 Y SEGURIDAD (`dispositivos_seguridad`)
# ==============================================================================
@app.get("/api/circuitos")
def listar_circuitos():
    return db_manager.find_all("dispositivos_seguridad")


@app.post("/api/circuitos")
def agregar_nuevo_circuito(req: NuevoCircuitoRequest):
    """
    Registra un nuevo circuito de riego con ESP32 para cubrir una nueva área/sector,
    generando automáticamente su token criptográfico en `dispositivos_seguridad`.
    """
    existente = db_manager.find_one("dispositivos_seguridad", {"dispositivo_id": req.dispositivo_id})
    if existente:
        raise HTTPException(
            status_code=400,
            detail=f"Ya existe un circuito registrado con el ID '{req.dispositivo_id}'.",
        )

    token = f"ags_tok_{secrets.token_hex(10)}"
    nuevo_circuito = {
        "dispositivo_id": req.dispositivo_id.strip().upper(),
        "nombre_circuito": req.nombre_circuito.strip(),
        "sector_id": req.sector_id.strip(),
        "tipo_cultivo": req.tipo_cultivo,
        "estado_actual": "Activo",
        "valvula_abierta": False,
        "area_cobertura_m2": req.area_cobertura_m2,
        "tipo": req.tipo,
        "seguridad": {
            "intentos_no_autorizados": 0,
            "ip_asignada": req.ip_asignada,
            "token_autenticacion": token,
            "ultimo_acceso_autorizado": now_iso(),
        },
    }
    creado = db_manager.insert_one("dispositivos_seguridad", nuevo_circuito, prefix="disp")

    # Crear lectura inicial para que el nuevo circuito tenga telemetría inmediata en el Dashboard
    db_manager.insert_one(
        "lecturas_sensores",
        {
            "dispositivo_id": creado["dispositivo_id"],
            "timestamp": now_iso(),
            "tipo_cultivo": req.tipo_cultivo,
            "lecturas": {
                "electroconductividad": 2.1 if req.tipo_cultivo == "hidroponico" else 1.6,
                "evaporacion_predicha": 2.9 if req.tipo_cultivo == "hidroponico" else 4.1,
                "humedad_suelo": 75.0 if req.tipo_cultivo == "hidroponico" else 46.0,
                "ph": 5.9 if req.tipo_cultivo == "hidroponico" else 6.5,
            },
            "ubicacion": {
                "coordenadas": [21.8469, -102.7188],
                "sector": req.sector_id.strip(),
            },
        },
        prefix="lec",
    )
    return creado


@app.post("/api/circuitos/{dispositivo_id}/valvula")
def controlar_valvula_circuito(dispositivo_id: str, req: ToggleValvulaRequest):
    """Abre o cierra directamente la electroválvula de un circuito ESP32 y registra la acción."""
    circuito = db_manager.find_one("dispositivos_seguridad", {"dispositivo_id": dispositivo_id})
    if not circuito:
        raise HTTPException(status_code=404, detail="Circuito ESP32 no encontrado.")

    nuevo_estado = "En Riego Manual" if req.abrir_valvula else "Activo"
    actualizado = db_manager.update_one(
        "dispositivos_seguridad",
        {"dispositivo_id": dispositivo_id},
        {
            "valvula_abierta": req.abrir_valvula,
            "estado_actual": nuevo_estado,
            "seguridad.ultimo_acceso_autorizado": now_iso(),
        },
    )

    if req.abrir_valvula:
        db_manager.insert_one(
            "rutinas_riego",
            {
                "dispositivo_id": dispositivo_id,
                "sector_id": circuito.get("sector_id", "Sector Principal"),
                "tipo_cultivo": circuito.get("tipo_cultivo", "rodado"),
                "modo": "manual",
                "algoritmo_utilizado": "Activación Directa de Válvula (Manual)",
                "estado": "Manual Activo",
                "fecha_programada": now_iso(),
                "parametros_optimizados": {
                    "duracion_minutos": req.duracion_minutos,
                    "volumen_agua_litros": req.volumen_agua_litros,
                    "mezcla_fertirriego": {
                        "nutriente_a": req.nutriente_a,
                        "nutriente_b": req.nutriente_b,
                    },
                },
            },
            prefix="rut",
        )

    return actualizado


@app.post("/api/circuitos/{dispositivo_id}/rotar-token")
def rotar_token_seguridad(dispositivo_id: str):
    """Renueva el token de autenticación del ESP32 y reinicia el contador de intentos no autorizados."""
    circuito = db_manager.find_one("dispositivos_seguridad", {"dispositivo_id": dispositivo_id})
    if not circuito:
        raise HTTPException(status_code=404, detail="Circuito no encontrado.")

    nuevo_token = f"ags_tok_{secrets.token_hex(10)}"
    actualizado = db_manager.update_one(
        "dispositivos_seguridad",
        {"dispositivo_id": dispositivo_id},
        {
            "estado_actual": "Activo",
            "seguridad.token_autenticacion": nuevo_token,
            "seguridad.intentos_no_autorizados": 0,
            "seguridad.ultimo_acceso_autorizado": now_iso(),
        },
    )
    return actualizado


@app.post("/api/circuitos/{dispositivo_id}/simular-intruso")
def simular_intento_no_autorizado(dispositivo_id: str):
    """Simula un intento de manipulación de válvula sin token válido (demostración de Seguridad Informática)."""
    circuito = db_manager.find_one("dispositivos_seguridad", {"dispositivo_id": dispositivo_id})
    if not circuito:
        raise HTTPException(status_code=404, detail="Circuito no encontrado.")

    intentos = circuito.get("seguridad", {}).get("intentos_no_autorizados", 0) + 1
    estado = "Alerta Seguridad" if intentos >= 3 else circuito.get("estado_actual", "Activo")
    actualizado = db_manager.update_one(
        "dispositivos_seguridad",
        {"dispositivo_id": dispositivo_id},
        {
            "estado_actual": estado,
            "seguridad.intentos_no_autorizados": intentos,
        },
    )
    return actualizado


@app.get("/api/circuitos/{dispositivo_id}/codigo-ino")
def obtener_codigo_arduino_esp32(dispositivo_id: str):
    """Genera el código C++ (.ino) personalizado para flashear en el ESP32 de ese circuito específico."""
    circuito = db_manager.find_one("dispositivos_seguridad", {"dispositivo_id": dispositivo_id})
    if not circuito:
        raise HTTPException(status_code=404, detail="Circuito no encontrado.")

    token = circuito.get("seguridad", {}).get("token_autenticacion", "ags_tok_default")
    sector = circuito.get("sector_id", "Sector Norte")
    tipo_cultivo = circuito.get("tipo_cultivo", "rodado")
    nombre = circuito.get("nombre_circuito", dispositivo_id)

    codigo_ino = f"""// ============================================================================
// FIRMWARE GENERADO AUTOMÁTICAMENTE — {nombre}
// ID Dispositivo: {dispositivo_id} | Sector: {sector}
// ============================================================================
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

const char* WIFI_SSID          = "TU_RED_WIFI";
const char* WIFI_PASSWORD      = "TU_PASSWORD_WIFI";
const char* BACKEND_BASE_URL   = "http://192.168.1.100:8000";

const char* DISPOSITIVO_ID      = "{dispositivo_id}";
const char* TOKEN_AUTENTICACION = "{token}";
const char* TIPO_CULTIVO        = "{tipo_cultivo}";
const char* SECTOR_RIEGO        = "{sector}";

const int PIN_SENSOR_HUMEDAD = 34;
const int PIN_SENSOR_PH      = 35;
const int PIN_SENSOR_EC      = 32;
const int PIN_RELE_VALVULA   = 26;

void setup() {{
  Serial.begin(115200);
  pinMode(PIN_RELE_VALVULA, OUTPUT);
  digitalWrite(PIN_RELE_VALVULA, LOW);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  while (WiFi.status() != WL_CONNECTED) {{ delay(500); Serial.print("."); }}
  Serial.println("\\nConectado! IP: " + WiFi.localIP().toString());
}}

void loop() {{
  if (WiFi.status() == WL_CONNECTED) {{
    // 1. Enviar lectura de sensores con token de seguridad
    HTTPClient http;
    http.begin(String(BACKEND_BASE_URL) + "/api/iot/telemetria");
    http.addHeader("Content-Type", "application/json");
    http.addHeader("X-Device-Token", TOKEN_AUTENTICACION);

    String payload = "{{\\"dispositivo_id\\":\\"{dispositivo_id}\\",\\"tipo_cultivo\\":\\"{tipo_cultivo}\\",\\"lecturas\\":{{\\"humedad_suelo\\":45.2,\\"ph\\":6.3,\\"electroconductividad\\":1.75}},\\"ubicacion\\":{{\\"sector\\":\\"{sector}\\",\\"coordenadas\\":[21.8469,-102.7188]}} }}";
    http.POST(payload);
    http.end();

    // 2. Consultar estado de electroválvula (Manual o IA)
    http.begin(String(BACKEND_BASE_URL) + "/api/iot/comando/{dispositivo_id}");
    http.addHeader("X-Device-Token", TOKEN_AUTENTICACION);
    if (http.GET() == 200) {{
      String res = http.getString();
      bool abrir = res.indexOf("\\"abrir_valvula\\":true") != -1;
      digitalWrite(PIN_RELE_VALVULA, abrir ? HIGH : LOW);
    }}
    http.end();
  }}
  delay(10000);
}}
"""
    return {
        "dispositivo_id": dispositivo_id,
        "nombre_archivo": f"{dispositivo_id.lower().replace('-', '_')}.ino",
        "codigo_ino": codigo_ino,
    }


# ==============================================================================
# 7. ENDPOINTS HARDWARE IoT PARA EL ESP32 (`/api/iot/*`)
# ==============================================================================
@app.post("/api/iot/telemetria")
def recibir_telemetria_esp32(
    payload: TelemetriaIoTInput,
    request: Request,
    x_device_token: Optional[str] = Header(default=None),
):
    """
    Endpoint consumido directamente por los nodos físicos ESP32.
    Verifica el `X-Device-Token` contra `dispositivos_seguridad`. Si falla, registra el intento no autorizado.
    """
    circuito = db_manager.find_one("dispositivos_seguridad", {"dispositivo_id": payload.dispositivo_id})
    if not circuito:
        raise HTTPException(status_code=404, detail="Dispositivo ESP32 no registrado.")

    token_esperado = circuito.get("seguridad", {}).get("token_autenticacion")
    if not x_device_token or x_device_token != token_esperado:
        intentos = circuito.get("seguridad", {}).get("intentos_no_autorizados", 0) + 1
        db_manager.update_one(
            "dispositivos_seguridad",
            {"dispositivo_id": payload.dispositivo_id},
            {
                "estado_actual": "Alerta Seguridad" if intentos >= 3 else circuito.get("estado_actual", "Activo"),
                "seguridad.intentos_no_autorizados": intentos,
            },
        )
        raise HTTPException(
            status_code=403,
            detail="Acceso denegado: Token de dispositivo ESP32 inválido. Intento no autorizado registrado.",
        )

    humedad = float(payload.lecturas.get("humedad_suelo", 50.0))
    ph = float(payload.lecturas.get("ph", 6.5))
    ec = float(payload.lecturas.get("electroconductividad", 1.5))

    pred_ia = ai_service.optimizar_riego(
        humedad_suelo=humedad,
        ph=ph,
        electroconductividad=ec,
        tipo_cultivo=payload.tipo_cultivo,
        area_cobertura_m2=circuito.get("area_cobertura_m2", 250.0),
    )

    ip_cliente = payload.ip_asignada or (request.client.host if request.client else "192.168.1.101")
    db_manager.update_one(
        "dispositivos_seguridad",
        {"dispositivo_id": payload.dispositivo_id},
        {
            "seguridad.ip_asignada": ip_cliente,
            "seguridad.ultimo_acceso_autorizado": now_iso(),
        },
    )

    nueva_lectura = db_manager.insert_one(
        "lecturas_sensores",
        {
            "dispositivo_id": payload.dispositivo_id,
            "timestamp": now_iso(),
            "tipo_cultivo": payload.tipo_cultivo,
            "lecturas": {
                "electroconductividad": round(ec, 2),
                "evaporacion_predicha": pred_ia["evaporacion_predicha"],
                "humedad_suelo": round(humedad, 1),
                "ph": round(ph, 2),
            },
            "ubicacion": payload.ubicacion.model_dump(),
        },
        prefix="lec",
    )

    return {
        "ok": True,
        "lectura_guardada": nueva_lectura,
        "recomendacion_ia": pred_ia,
    }


@app.get("/api/iot/comando/{dispositivo_id}")
def consultar_comando_esp32(
    dispositivo_id: str,
    x_device_token: Optional[str] = Header(default=None),
):
    """El ESP32 consulta este endpoint para saber si debe abrir o cerrar la electroválvula."""
    circuito = db_manager.find_one("dispositivos_seguridad", {"dispositivo_id": dispositivo_id})
    if not circuito:
        raise HTTPException(status_code=404, detail="Dispositivo ESP32 no registrado.")

    token_esperado = circuito.get("seguridad", {}).get("token_autenticacion")
    if x_device_token and x_device_token != token_esperado:
        intentos = circuito.get("seguridad", {}).get("intentos_no_autorizados", 0) + 1
        db_manager.update_one(
            "dispositivos_seguridad",
            {"dispositivo_id": dispositivo_id},
            {"seguridad.intentos_no_autorizados": intentos},
        )
        raise HTTPException(status_code=403, detail="Token de dispositivo inválido.")

    rutinas_activas = [
        r
        for r in db_manager.find_all("rutinas_riego")
        if r.get("dispositivo_id") == dispositivo_id and r.get("estado") in ["En Curso", "Manual Activo"]
    ]
    rutina_actual = rutinas_activas[0] if rutinas_activas else None
    params = (
        rutina_actual.get("parametros_optimizados", {})
        if rutina_actual
        else {"duracion_minutos": 0, "volumen_agua_litros": 0, "mezcla_fertirriego": {"nutriente_a": 0, "nutriente_b": 0}}
    )

    return {
        "dispositivo_id": dispositivo_id,
        "abrir_valvula": bool(circuito.get("valvula_abierta", False)),
        "estado_actual": circuito.get("estado_actual", "Activo"),
        "duracion_minutos": params.get("duracion_minutos", 15),
        "volumen_agua_litros": params.get("volumen_agua_litros", 0),
        "mezcla_fertirriego": params.get("mezcla_fertirriego", {"nutriente_a": 0, "nutriente_b": 0}),
    }
