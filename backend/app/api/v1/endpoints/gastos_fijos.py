from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.api.deps import get_current_user_id
from backend.app.models import GastoFijo, PerfilFinanciero
from backend.app.schemas import (
    GastoFijoCreate,
    GastoFijoUpdate,
    GastoFijoResponse,
    GastosFijosResumen,
)
from backend.app.services.financial_engine import FinancialEngine

router = APIRouter()


@router.get("", response_model=GastosFijosResumen)
@router.get("/", response_model=GastosFijosResumen)
def listar_gastos_fijos(
    db: Session = Depends(get_db),
    current_uid: Optional[int] = Depends(get_current_user_id)
):
    """
    Obtiene el listado de compromisos fijos y el estado del ciclo salarial (apartados de nómina vs pendientes).
    """
    return FinancialEngine.obtener_resumen_gastos_fijos(db, usuario_id=current_uid)


@router.post("", response_model=GastoFijoResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=GastoFijoResponse, status_code=status.HTTP_201_CREATED)
def crear_gasto_fijo(
    gasto_in: GastoFijoCreate,
    db: Session = Depends(get_db),
    current_uid: Optional[int] = Depends(get_current_user_id)
):
    """
    Crea un nuevo gasto fijo mensual (arriendo, servicios, suscripción, etc.).
    """
    nuevo = GastoFijo(
        nombre=gasto_in.nombre.strip(),
        monto=float(gasto_in.monto),
        dia_pago=gasto_in.dia_pago or 5,
        categoria=gasto_in.categoria or "Hogar y Servicios",
        activo=True,
        pagado_este_mes=bool(gasto_in.pagado_este_mes),
        usuario_id=current_uid,
    )
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)

    # Actualizar total en PerfilFinanciero
    perfil_q = db.query(PerfilFinanciero)
    if current_uid:
        perfil = perfil_q.filter((PerfilFinanciero.usuario_id == current_uid) | (PerfilFinanciero.usuario_id == None)).first()
    else:
        perfil = perfil_q.first()

    if perfil:
        activos_q = db.query(GastoFijo).filter(GastoFijo.activo == True)
        if current_uid:
            activos_q = activos_q.filter((GastoFijo.usuario_id == current_uid) | (GastoFijo.usuario_id == None))
        activos = activos_q.all()
        perfil.compromisos_fijos_mensual = sum(g.monto for g in activos)
        db.commit()

    return nuevo


@router.patch("/{gasto_id}/toggle-pagado", response_model=GastoFijoResponse)
def toggle_pagado_gasto_fijo(
    gasto_id: int,
    db: Session = Depends(get_db),
    current_uid: Optional[int] = Depends(get_current_user_id)
):
    """
    Alterna el estado de pagado este mes para un compromiso fijo.
    """
    gasto_q = db.query(GastoFijo).filter(GastoFijo.id == gasto_id)
    if current_uid:
        gasto_q = gasto_q.filter((GastoFijo.usuario_id == current_uid) | (GastoFijo.usuario_id == None))
    gasto = gasto_q.first()
    if not gasto:
        raise HTTPException(status_code=404, detail="Gasto fijo no encontrado")
    gasto.pagado_este_mes = not gasto.pagado_este_mes
    db.commit()
    db.refresh(gasto)
    return gasto


@router.delete("/{gasto_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_gasto_fijo(
    gasto_id: int,
    db: Session = Depends(get_db),
    current_uid: Optional[int] = Depends(get_current_user_id)
):
    """
    Elimina un compromiso fijo y recalcula el total mensual.
    """
    gasto_q = db.query(GastoFijo).filter(GastoFijo.id == gasto_id)
    if current_uid:
        gasto_q = gasto_q.filter((GastoFijo.usuario_id == current_uid) | (GastoFijo.usuario_id == None))
    gasto = gasto_q.first()
    if not gasto:
        raise HTTPException(status_code=404, detail="Gasto fijo no encontrado")
    db.delete(gasto)
    db.commit()

    perfil_q = db.query(PerfilFinanciero)
    if current_uid:
        perfil = perfil_q.filter((PerfilFinanciero.usuario_id == current_uid) | (PerfilFinanciero.usuario_id == None)).first()
    else:
        perfil = perfil_q.first()

    if perfil:
        activos_q = db.query(GastoFijo).filter(GastoFijo.activo == True)
        if current_uid:
            activos_q = activos_q.filter((GastoFijo.usuario_id == current_uid) | (GastoFijo.usuario_id == None))
        activos = activos_q.all()
        perfil.compromisos_fijos_mensual = sum(g.monto for g in activos)
        db.commit()
    return None
