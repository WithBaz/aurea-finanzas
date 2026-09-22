from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.schemas import (
    SemaforoResponse,
    RendimientoDiarioResponse,
    PerfilFinancieroResponse,
    PerfilFinancieroUpdate,
)
from backend.app.models import PerfilFinanciero, Transaccion, Cuenta
from backend.app.services.financial_engine import FinancialEngine

router = APIRouter()


@router.get("/semaforo", response_model=SemaforoResponse)
def obtener_semaforo_mensual(db: Session = Depends(get_db)):
    """
    Calcula el estado del semáforo diario basado en el presupuesto mensual del usuario en COP.
    """
    return FinancialEngine.calcular_semaforo_mensual(db)


@router.get("/rendimientos", response_model=List[RendimientoDiarioResponse])
def obtener_rendimientos_diarios(db: Session = Depends(get_db)):
    """
    Calcula los rendimientos generados hoy por cuentas remuneradas (Nu Colombia, Lulo, Pibank).
    """
    return FinancialEngine.calcular_rendimientos_diarios(db)


@router.get("/perfil", response_model=PerfilFinancieroResponse)
def obtener_perfil(db: Session = Depends(get_db)):
    """
    Obtiene el perfil financiero y parámetros del ciclo de nómina del usuario.
    """
    perfil = db.query(PerfilFinanciero).first()
    if not perfil:
        perfil = PerfilFinanciero(
            dia_pago_mensual=30,
            ingreso_mensual_estimado=4000000.0,
            compromisos_fijos_mensual=1800000.0,
            porcentaje_ahorro_meta=15.0,
            umbral_gasto_hormiga=25000.0,
        )
        db.add(perfil)
        db.commit()
        db.refresh(perfil)
    return perfil


@router.put("/perfil", response_model=PerfilFinancieroResponse)
def actualizar_perfil(
    perfil_in: PerfilFinancieroUpdate,
    db: Session = Depends(get_db)
):
    """
    Actualiza ingresos reales, compromisos fijos y día de cobro de nómina.
    """
    perfil = db.query(PerfilFinanciero).first()
    if not perfil:
        perfil = PerfilFinanciero(**perfil_in.model_dump())
        db.add(perfil)
    else:
        update_data = perfil_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(perfil, field, value)
    db.commit()
    db.refresh(perfil)
    return perfil


@router.post("/reiniciar-todo")
@router.post("/limpiar-demo")
def reiniciar_todo_desde_cero(db: Session = Depends(get_db)):
    """
    Elimina todas las transacciones, metas y cuentas, y resetea el perfil a 0 para empezar desde cero absoluto.
    """
    from backend.app.models import MetaAhorro
    db.query(Transaccion).delete()
    db.query(MetaAhorro).delete()
    db.query(Cuenta).delete()
    perfil = db.query(PerfilFinanciero).first()
    if perfil:
        perfil.ingreso_mensual_estimado = 0.0
        perfil.compromisos_fijos_mensual = 0.0
    db.commit()
    return {"status": "exitoso", "mensaje": "Base de datos reiniciada a cero. Tu aplicación está 100% limpia para registrar tus cuentas reales."}


@router.get("/dashboard")
def obtener_resumen_dashboard(db: Session = Depends(get_db)):
    """
    Consolida todo el estado del dashboard (cuentas, semáforo, rendimientos y transacciones)
    en una sola petición HTTP ultra-rápida para minimizar latencia en móviles y Apple Shortcuts.
    """
    from backend.app.models import TipoCuenta
    semaforo = FinancialEngine.calcular_semaforo_mensual(db)
    rendimientos = FinancialEngine.calcular_rendimientos_diarios(db)
    cuentas = db.query(Cuenta).filter(Cuenta.activa == True).all()
    transacciones = db.query(Transaccion).order_by(Transaccion.fecha.desc()).limit(30).all()

    total_saldo = sum(c.saldo_actual for c in cuentas if c.tipo != TipoCuenta.CREDITO)

    return {
        "db_motor": db.bind.dialect.name,
        "es_postgresql": db.bind.dialect.name == "postgresql",
        "semaforo": semaforo,
        "rendimientos": rendimientos,
        "cuentas": [
            {
                "id": c.id,
                "nombre": c.nombre,
                "tipo": c.tipo.value if hasattr(c.tipo, "value") else str(c.tipo),
                "saldo_actual": c.saldo_actual,
                "cupo_total": c.cupo_total,
                "tasa_ea": c.tasa_ea,
                "dia_corte": c.dia_corte,
                "dia_limite_pago": c.dia_limite_pago,
                "activa": c.activa,
            }
            for c in cuentas
        ],
        "total_saldo": total_saldo,
        "transacciones": [
            {
                "id": t.id,
                "monto": t.monto,
                "tipo": t.tipo.value if hasattr(t.tipo, "value") else str(t.tipo),
                "comercio": t.comercio,
                "fecha": t.fecha.isoformat() if t.fecha else None,
                "medio": t.medio.value if hasattr(t.medio, "value") else str(t.medio),
                "es_gasto_hormiga": t.es_gasto_hormiga,
                "cuenta_nombre": t.cuenta_origen.nombre if t.cuenta_origen else "General",
            }
            for t in transacciones
        ]
    }


@router.get("/estado-db")
def obtener_estado_db(db: Session = Depends(get_db)):
    """
    Verifica si la base de datos está conectada a PostgreSQL en la nube o a SQLite local.
    """
    import os
    dialect = db.bind.dialect.name
    is_postgres = dialect == "postgresql"
    db_url = (
        os.getenv("DATABASE_URL")
        or os.getenv("POSTGRES_URL")
        or os.getenv("POSTGRES_PRISMA_URL")
        or ""
    )
    host = ""
    if "@" in db_url:
        host = db_url.split("@")[1].split("/")[0].split("?")[0]
    return {
        "conectado": True,
        "motor": dialect,
        "es_postgresql": is_postgres,
        "host": host if host else ("local" if "sqlite" in dialect else "desconocido"),
        "mensaje": (
            "Base de datos PostgreSQL en la nube conectada con éxito y persistente."
            if is_postgres
            else "Ejecutando en SQLite local/temporal."
        )
    }

