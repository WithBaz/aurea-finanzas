import enum
from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    DateTime,
    Date,
    ForeignKey,
    Enum,
    Text,
)
from sqlalchemy.orm import relationship
from backend.app.database import Base


class TipoCuenta(str, enum.Enum):
    DEBITO = "DEBITO"
    CREDITO = "CREDITO"
    ALTO_RENDIMIENTO = "ALTO_RENDIMIENTO"
    EFECTIVO = "EFECTIVO"


class TipoTransaccion(str, enum.Enum):
    INGRESO = "INGRESO"
    EGRESO = "EGRESO"
    TRANSFERENCIA_INTERNA = "TRANSFERENCIA_INTERNA"


class MedioCaptura(str, enum.Enum):
    APPLE_PAY = "APPLE_PAY"
    SMS = "SMS"
    MANUAL = "MANUAL"
    WEBHOOK = "WEBHOOK"


class Cuenta(Base):
    __tablename__ = "cuentas"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    tipo = Column(Enum(TipoCuenta), nullable=False)
    saldo_actual = Column(Float, default=0.0, nullable=False)
    cupo_total = Column(Float, default=0.0, nullable=True)  # Para tarjetas de crédito
    tasa_ea = Column(Float, default=0.0, nullable=True)     # Tasa E.A. en % (ej. 12.5)
    dia_corte = Column(Integer, nullable=True)              # Día del mes para tarjetas de crédito
    dia_limite_pago = Column(Integer, nullable=True)        # Día límite de pago para tarjetas de crédito
    activa = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    transacciones_origen = relationship("Transaccion", foreign_keys="Transaccion.cuenta_origen_id", back_populates="cuenta_origen")
    transacciones_destino = relationship("Transaccion", foreign_keys="Transaccion.cuenta_destino_id", back_populates="cuenta_destino")


class Categoria(Base):
    __tablename__ = "categorias"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False, unique=True)
    icono = Column(String(50), default="tag", nullable=False)
    color_hex = Column(String(20), default="#3B82F6", nullable=False)
    palabras_clave = Column(Text, default="", nullable=False)  # Coma-separadas (ej: "d1,éxito,jumbo,ara")

    transacciones = relationship("Transaccion", back_populates="categoria")


class Transaccion(Base):
    __tablename__ = "transacciones"

    id = Column(Integer, primary_key=True, index=True)
    monto = Column(Float, nullable=False)
    tipo = Column(Enum(TipoTransaccion), nullable=False)
    medio = Column(Enum(MedioCaptura), default=MedioCaptura.MANUAL, nullable=False)
    fecha = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    comercio = Column(String(150), nullable=False)
    descripcion = Column(String(255), nullable=True)
    cuenta_origen_id = Column(Integer, ForeignKey("cuentas.id"), nullable=False)
    cuenta_destino_id = Column(Integer, ForeignKey("cuentas.id"), nullable=True)
    categoria_id = Column(Integer, ForeignKey("categorias.id"), nullable=True)
    cuotas_totales = Column(Integer, default=1, nullable=False)
    cuota_actual = Column(Integer, default=1, nullable=False)
    es_gasto_hormiga = Column(Boolean, default=False, nullable=False)
    raw_payload = Column(Text, nullable=True)
    hash_idempotencia = Column(String(64), unique=True, index=True, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    cuenta_origen = relationship("Cuenta", foreign_keys=[cuenta_origen_id], back_populates="transacciones_origen")
    cuenta_destino = relationship("Cuenta", foreign_keys=[cuenta_destino_id], back_populates="transacciones_destino")
    categoria = relationship("Categoria", back_populates="transacciones")


class MetaAhorro(Base):
    __tablename__ = "metas_ahorro"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(150), nullable=False)
    monto_objetivo = Column(Float, nullable=False)
    monto_actual = Column(Float, default=0.0, nullable=False)
    fecha_limite = Column(Date, nullable=True)
    icono = Column(String(50), default="target", nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)


class PerfilFinanciero(Base):
    __tablename__ = "perfil_financiero"

    id = Column(Integer, primary_key=True, index=True)
    dia_pago_mensual = Column(Integer, default=1, nullable=False)
    ingreso_mensual_estimado = Column(Float, default=4000000.0, nullable=False)
    compromisos_fijos_mensual = Column(Float, default=1800000.0, nullable=False) # Arriendo, servicios
    porcentaje_ahorro_meta = Column(Float, default=15.0, nullable=False)
    umbral_gasto_hormiga = Column(Float, default=25000.0, nullable=False)       # Gastos menores a este valor


class GastoFijo(Base):
    __tablename__ = "gastos_fijos"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    monto = Column(Float, nullable=False)
    dia_pago = Column(Integer, default=5, nullable=False)  # Día habitual de pago en el mes (ej: 5)
    categoria = Column(String(50), default="Hogar y Servicios", nullable=True)
    activo = Column(Boolean, default=True, nullable=False)
    pagado_este_mes = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
