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

