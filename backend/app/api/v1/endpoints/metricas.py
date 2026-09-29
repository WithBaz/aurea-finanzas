from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.api.deps import get_current_user_id, require_current_user_id, check_auth_if_users_exist
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
def obtener_semaforo_mensual(
    db: Session = Depends(get_db),
    current_uid: Optional[int] = Depends(get_current_user_id)
):
    """
    Calcula el estado del semáforo diario basado en el presupuesto mensual del usuario en COP.
    """
    check_auth_if_users_exist(current_uid, db, "el semáforo financiero")
    return FinancialEngine.calcular_semaforo_mensual(db, usuario_id=current_uid)


@router.get("/rendimientos", response_model=List[RendimientoDiarioResponse])
def obtener_rendimientos_diarios(
    db: Session = Depends(get_db),
    current_uid: Optional[int] = Depends(get_current_user_id)
):
    """
    Calcula los rendimientos generados hoy por cuentas remuneradas (Nu Colombia, Lulo, Pibank).
    """
    check_auth_if_users_exist(current_uid, db, "los rendimientos")
    return FinancialEngine.calcular_rendimientos_diarios(db, usuario_id=current_uid)


@router.get("/perfil", response_model=PerfilFinancieroResponse)
def obtener_perfil(
    db: Session = Depends(get_db),
    current_uid: Optional[int] = Depends(get_current_user_id)
):
    """
    Obtiene el perfil financiero y parámetros del ciclo de nómina del usuario.
    """
    check_auth_if_users_exist(current_uid, db, "tu perfil financiero")
    perfil_q = db.query(PerfilFinanciero)
    if current_uid:
        perfil = perfil_q.filter((PerfilFinanciero.usuario_id == current_uid) | (PerfilFinanciero.usuario_id == None)).first()
    else:
        perfil = perfil_q.first()

    if not perfil:
        perfil = PerfilFinanciero(
            usuario_id=current_uid,
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
    db: Session = Depends(get_db),
    current_uid: Optional[int] = Depends(get_current_user_id)
):
    """
    Actualiza ingresos reales, compromisos fijos y día de cobro de nómina.
    """
    check_auth_if_users_exist(current_uid, db, "actualizar perfil")
    perfil_q = db.query(PerfilFinanciero)
    if current_uid:
        perfil = perfil_q.filter((PerfilFinanciero.usuario_id == current_uid) | (PerfilFinanciero.usuario_id == None)).first()
    else:
        perfil = perfil_q.first()

    if not perfil:
        perfil = PerfilFinanciero(usuario_id=current_uid, **perfil_in.model_dump())
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
def reiniciar_todo_desde_cero(
    db: Session = Depends(get_db),
    current_uid: int = Depends(require_current_user_id)
):
    """
    Elimina datos asociados al usuario actual para empezar desde cero de manera segura.
    Requiere autenticación obligatoria y jamás toca datos de otros usuarios.
    """
    from backend.app.models import MetaAhorro, GastoFijo
    db.query(Transaccion).filter(Transaccion.usuario_id == current_uid).delete(synchronize_session=False)
    db.query(MetaAhorro).filter(MetaAhorro.usuario_id == current_uid).delete(synchronize_session=False)
    db.query(Cuenta).filter(Cuenta.usuario_id == current_uid).delete(synchronize_session=False)
    db.query(GastoFijo).filter(GastoFijo.usuario_id == current_uid).delete(synchronize_session=False)
    perfil = db.query(PerfilFinanciero).filter(PerfilFinanciero.usuario_id == current_uid).first()
    if perfil:
        perfil.ingreso_mensual_estimado = 0.0
        perfil.compromisos_fijos_mensual = 0.0
    db.commit()
    return {"status": "exitoso", "mensaje": "Tus datos financieros personales han sido reiniciados a cero."}


@router.get("/dashboard")
def obtener_resumen_dashboard(
    db: Session = Depends(get_db),
    current_uid: Optional[int] = Depends(get_current_user_id)
):
    """
    Consolida todo el estado del dashboard (cuentas, semáforo, rendimientos, gastos fijos y transacciones)
    en una sola petición HTTP ultra-rápida para el usuario actual.
    """
    check_auth_if_users_exist(current_uid, db, "el dashboard")
    from backend.app.models import TipoCuenta
    semaforo = FinancialEngine.calcular_semaforo_mensual(db, usuario_id=current_uid)
    rendimientos = FinancialEngine.calcular_rendimientos_diarios(db, usuario_id=current_uid)
    gastos_fijos = FinancialEngine.obtener_resumen_gastos_fijos(db, usuario_id=current_uid)

    cuentas_q = db.query(Cuenta).filter(Cuenta.activa == True)
    if current_uid:
        cuentas_q = cuentas_q.filter((Cuenta.usuario_id == current_uid) | (Cuenta.usuario_id == None))
    cuentas = cuentas_q.all()

    transacciones_q = db.query(Transaccion)
    if current_uid:
        transacciones_q = transacciones_q.filter((Transaccion.usuario_id == current_uid) | (Transaccion.usuario_id == None))
    transacciones = transacciones_q.order_by(Transaccion.fecha.desc()).limit(30).all()

    total_saldo = sum(c.saldo_actual for c in cuentas if c.tipo != TipoCuenta.CREDITO)

    return {
        "db_motor": db.bind.dialect.name,
        "es_postgresql": db.bind.dialect.name == "postgresql",
        "semaforo": semaforo,
        "rendimientos": rendimientos,
        "gastos_fijos": gastos_fijos,
        "cuentas": [
            {
                "id": c.id,
                "nombre": c.nombre,
                "tipo": c.tipo.value if hasattr(c.tipo, "value") else str(c.tipo),
                "saldo_actual": c.saldo_actual,
                "cupo_total": c.cupo_total,
                "cupo_disponible": max(0.0, (c.cupo_total or 0.0) - c.saldo_actual) if c.tipo == TipoCuenta.CREDITO else None,
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
                "cuenta_origen_id": t.cuenta_origen_id,
                "cuenta_tipo": (t.cuenta_origen.tipo.value if hasattr(t.cuenta_origen.tipo, "value") else str(t.cuenta_origen.tipo)) if t.cuenta_origen else None,
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


@router.get("/migrar-esquema")
def ejecutar_migracion_esquema(
    current_uid: int = Depends(require_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Ejecuta bajo demanda la migración de columnas y tablas, y reporta las columnas existentes.
    """
    from backend.app.database import migrar_esquema_multi_usuario
    from sqlalchemy import inspect
    migrar_esquema_multi_usuario(db.bind)
    inspector = inspect(db.bind)
    columnas = {}
    for table in ["usuarios", "cuentas", "transacciones", "gastos_fijos", "perfil_financiero"]:
        if table in inspector.get_table_names():
            columnas[table] = [c["name"] for c in inspector.get_columns(table)]
    return {
        "status": "migracion_ejecutada",
        "motor": db.bind.dialect.name,
        "columnas": columnas
    }


