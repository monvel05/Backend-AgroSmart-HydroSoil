from typing import List, Optional
from pydantic import BaseModel, Field


# ==============================================================================
# 1. COLECCIÓN: bitacoras_sensores (Minería de Texto - IA)
# ==============================================================================
class ProcesamientoIA(BaseModel):
    categoria: str = Field(..., description="Categoría clasificada de la bitácora")
    clasificado: bool = Field(default=True)
    nivel_urgencia: str = Field(..., description="Baja | Media | Alta | Crítica")
    palabras_clave: List[str] = Field(default_factory=list)
    plaga_detectada: str = Field(..., description="Nombre de la plaga o 'Ninguna'")


class BitacoraSensor(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    agricultor_id: str
    fecha_registro: str
    procesamiento_ia: ProcesamientoIA
    texto_raw: str
    sector_id: Optional[str] = "Sector Norte - Parcela A1"
    dispositivo_id: Optional[str] = "ESP32-CIRCUITO-01"

    class Config:
        populate_by_name = True


class BitacoraCreateRequest(BaseModel):
    agricultor_id: str
    texto_raw: str
    sector_id: Optional[str] = "Sector Norte - Parcela A1"
    dispositivo_id: Optional[str] = "ESP32-CIRCUITO-01"


# ==============================================================================
# 2. COLECCIÓN: dispositivos_seguridad (Seguridad Informática & Multi-Circuito ESP32)
# ==============================================================================
class SeguridadDispositivo(BaseModel):
    intentos_no_autorizados: int = Field(default=0)
    ip_asignada: str = Field(default="192.168.1.101")
    token_autenticacion: str
    ultimo_acceso_autorizado: str


class DispositivoSeguridad(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    dispositivo_id: str
    estado_actual: str = Field(default="Activo", description="Activo | En Riego | Alerta | Inactivo")
    seguridad: SeguridadDispositivo
    tipo: str = Field(default="ESP32 - Controlador de Circuito + Válvula")
    # Metadatos extendidos para soporte multi-circuito (retrocompatibles con el diagrama)
    nombre_circuito: Optional[str] = "Circuito Principal"
    sector_id: Optional[str] = "Sector Norte - Parcela A1"
    tipo_cultivo: Optional[str] = "rodado"
    valvula_abierta: Optional[bool] = False
    area_cobertura_m2: Optional[float] = 250.0

    class Config:
        populate_by_name = True


class NuevoCircuitoRequest(BaseModel):
    dispositivo_id: str
    nombre_circuito: str
    sector_id: str
    tipo_cultivo: str = "rodado"
    ip_asignada: str = "192.168.1.110"
    tipo: str = "ESP32 + Sensores pH/EC/Humedad + Electroválvula"
    area_cobertura_m2: float = 250.0


# ==============================================================================
# 3. COLECCIÓN: lecturas_sensores (Bases de Datos en la Nube & Previsión IA)
# ==============================================================================
class LecturasDetalle(BaseModel):
    electroconductividad: float = Field(..., description="mS/cm")
    evaporacion_predicha: float = Field(..., description="mm/día predichos por IA")
    humedad_suelo: float = Field(..., description="Porcentaje %")
    ph: float = Field(..., description="Nivel de pH (0-14)")


class UbicacionSensor(BaseModel):
    coordenadas: List[float] = Field(default_factory=lambda: [21.8469, -102.7188])
    sector: str


class LecturaSensor(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    dispositivo_id: str
    lecturas: LecturasDetalle
    timestamp: str
    tipo_cultivo: str = Field(..., description="rodado | hidroponico")
    ubicacion: UbicacionSensor

    class Config:
        populate_by_name = True


class TelemetriaIoTInput(BaseModel):
    dispositivo_id: str
    tipo_cultivo: str = "rodado"
    ip_asignada: Optional[str] = None
    lecturas: dict
    ubicacion: UbicacionSensor


# ==============================================================================
# 4. COLECCIÓN: rutinas_riego (Fundamentos de IA & Riegos Manuales)
# ==============================================================================
class MezclaFertirriego(BaseModel):
    nutriente_a: int = Field(..., description="ml o gramos de Nutriente A (N-P-K base)")
    nutriente_b: int = Field(..., description="ml o gramos de Nutriente B (Microelementos/Calcio)")


class ParametrosOptimizados(BaseModel):
    duracion_minutos: int
    mezcla_fertirriego: MezclaFertirriego
    volumen_agua_litros: float


class RutinaRiego(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    algoritmo_utilizado: str
    estado: str = Field(..., description="Programado | En Curso | Completado | Manual Activo | Cancelado")
    fecha_programada: str
    parametros_optimizados: ParametrosOptimizados
    sector_id: str
    dispositivo_id: Optional[str] = "ESP32-CIRCUITO-01"
    tipo_cultivo: Optional[str] = "rodado"
    modo: Optional[str] = "automatico_ia"  # "automatico_ia" | "manual"

    class Config:
        populate_by_name = True


class RiegoManualRequest(BaseModel):
    dispositivo_id: str
    sector_id: str
    tipo_cultivo: str = "rodado"
    duracion_minutos: int
    volumen_agua_litros: float
    nutriente_a: int = 0
    nutriente_b: int = 0
    ejecutar_ahora: bool = True
    fecha_programada: Optional[str] = None
    notas: Optional[str] = None


class OptimizarRiegoIARequest(BaseModel):
    dispositivo_id: str
    sector_id: str
    tipo_cultivo: str = "rodado"
    humedad_suelo: Optional[float] = None
    ph: Optional[float] = None
    electroconductividad: Optional[float] = None


class ToggleValvulaRequest(BaseModel):
    abrir_valvula: bool
    duracion_minutos: int = 15
    volumen_agua_litros: float = 120.0
    nutriente_a: int = 20
    nutriente_b: int = 15


# ==============================================================================
# 5. AUTENTICACIÓN Y USUARIOS (LOGIN)
# ==============================================================================
class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    nombre: str
    email: str
    password: str
    rol: str = "Agricultor Senior / Administrador"
    agricultor_id: Optional[str] = None
