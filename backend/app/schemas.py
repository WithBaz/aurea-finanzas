from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from backend.app.models import TipoCuenta, TipoTransaccion, MedioCaptura


# --- Cuentas ---
class CuentaBase(BaseModel):
    nombre: str = Field(...)
    tipo: TipoCuenta
    saldo_actual: float = Field(0.0)
    cupo_total: Optional[float] = Field(0.0)
    tasa_ea: Optional[float] = Field(0.0)
    dia_corte: Optional[int] = Field(None, ge=1, le=31)
    dia_limite_pago: Optional[int] = Field(None, ge=1, le=31)
    activa: bool = True


class CuentaCreate(CuentaBase):
    pass


class CuentaUpdate(BaseModel):
    nombre: Optional[str] = None
    tipo: Optional[TipoCuenta] = None
    saldo_actual: Optional[float] = None
    cupo_total: Optional[float] = None
    tasa_ea: Optional[float] = None
    dia_corte: Optional[int] = None
    dia_limite_pago: Optional[int] = None
    activa: Optional[bool] = None


class CuentaResponse(CuentaBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# --- Categorias ---
class CategoriaBase(BaseModel):
    nombre: str = Field(...)
    icono: str = Field("tag")
    color_hex: str = Field("#3B82F6")
    palabras_clave: str = Field("")


class CategoriaCreate(CategoriaBase):
    pass


class CategoriaResponse(CategoriaBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


# --- Transacciones ---
class TransaccionBase(BaseModel):
    monto: float = Field(..., gt=0)
    tipo: TipoTransaccion
    medio: MedioCaptura = MedioCaptura.MANUAL
    fecha: Optional[datetime] = None
    comercio: str = Field(...)
    descripcion: Optional[str] = None
    cuenta_origen_id: int
    cuenta_destino_id: Optional[int] = None
    categoria_id: Optional[int] = None
    cuotas_totales: int = Field(1, ge=1)
    cuota_actual: int = Field(1, ge=1)
    es_gasto_hormiga: bool = False


class TransaccionCreate(TransaccionBase):
    pass


class TransaccionResponse(TransaccionBase):
    id: int
    hash_idempotencia: Optional[str] = None
    created_at: datetime
    categoria: Optional[CategoriaResponse] = None
    model_config = ConfigDict(from_attributes=True)


# --- Metas de Ahorro ---
class MetaAhorroBase(BaseModel):
    nombre: str = Field(...)
    monto_objetivo: float = Field(..., gt=0)
    monto_actual: float = Field(0.0, ge=0)
    fecha_limite: Optional[date] = None
    icono: str = "target"


class MetaAhorroCreate(MetaAhorroBase):
    pass


class MetaAhorroResponse(MetaAhorroBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# --- Webhooks iOS Shortcuts ---
class ApplePayWebhookPayload(BaseModel):
    medio: str = "APPLE_PAY"
    monto: float
    comercio: str
    tarjeta: Optional[str] = None
    fecha: Optional[datetime] = None


class SMSWebhookPayload(BaseModel):
    medio: str = "SMS"
    texto_sms: str
    remitente: Optional[str] = None
    fecha: Optional[datetime] = None


class WebhookIngestResponse(BaseModel):
    status: str
    mensaje: str
    transaccion_id: Optional[int] = None
    tipo_detectado: str
    monto_cop: float
    comercio: str
    cuenta_afectada: str
    es_transferencia_interna: bool = False


# --- Métricas y Semáforo ---
class SemaforoResponse(BaseModel):
    color: str  # "VERDE", "AMARILLO", "ROJO"
    dia_actual_ciclo: int
    dias_totales_mes: int
    dias_restantes: int
    presupuesto_disponible_total: float
    limite_gasto_diario_sugerido: float
    gasto_hoy: float
    disponible_hoy_restante: float
    gasto_acumulado_mes: float
    gastos_hormiga_acumulados: float
    mensaje_guia: str


class RendimientoDiarioResponse(BaseModel):
    cuenta_id: int
    cuenta_nombre: str
    saldo_actual: float
    tasa_ea: float
    rendimiento_diario_estimado: float
    rendimiento_mensual_proyectado: float


# --- Perfil Financiero ---
class PerfilFinancieroBase(BaseModel):
    dia_pago_mensual: int = Field(30, ge=1, le=31)
    ingreso_mensual_estimado: float = Field(..., ge=0)
    compromisos_fijos_mensual: float = Field(0.0, ge=0)
    porcentaje_ahorro_meta: float = Field(15.0, ge=0, le=100)
    umbral_gasto_hormiga: float = Field(25000.0, ge=0)


class PerfilFinancieroUpdate(BaseModel):
    dia_pago_mensual: Optional[int] = Field(None, ge=1, le=31)
    ingreso_mensual_estimado: Optional[float] = Field(None, ge=0)
    compromisos_fijos_mensual: Optional[float] = Field(None, ge=0)
    porcentaje_ahorro_meta: Optional[float] = Field(None, ge=0, le=100)
    umbral_gasto_hormiga: Optional[float] = Field(None, ge=0)


class PerfilFinancieroResponse(PerfilFinancieroBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


# --- Gastos Fijos ---
class GastoFijoBase(BaseModel):
    nombre: str = Field(...)
    monto: float = Field(..., gt=0)
    dia_pago: int = Field(5, ge=1, le=31)
    categoria: Optional[str] = "Hogar y Servicios"
    activo: bool = True
    pagado_este_mes: bool = False


class GastoFijoCreate(BaseModel):
    nombre: str = Field(...)
    monto: float = Field(..., gt=0)
    dia_pago: Optional[int] = Field(5, ge=1, le=31)
    categoria: Optional[str] = "Hogar y Servicios"
    pagado_este_mes: Optional[bool] = False


class GastoFijoUpdate(BaseModel):
    nombre: Optional[str] = None
    monto: Optional[float] = Field(None, gt=0)
    dia_pago: Optional[int] = Field(None, ge=1, le=31)
    categoria: Optional[str] = None
    activo: Optional[bool] = None
    pagado_este_mes: Optional[bool] = None


class GastoFijoResponse(GastoFijoBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class GastosFijosResumen(BaseModel):
    total_fijos: float
    total_apartado_nomina: float
    total_pendiente: float
    cantidad_compromisos: int
    nomina_recibida: bool
    items: List[GastoFijoResponse]

