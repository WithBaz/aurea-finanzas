from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.database import get_db
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
def listar_gastos_fijos(db: Session = Depends(get_db)):
    """
    Obtiene el listado de compromisos fijos y el estado del ciclo salarial (apartados de nómina vs pendientes).
    """
    return FinancialEngine.obtener_resumen_gastos_fijos(db)


@router.post("", response_model=GastoFijoResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=GastoFijoResponse, status_code=status.HTTP_201_CREATED)
def crear_gasto_fijo(gasto_in: GastoFijoCreate, db: Session = Depends(get_db)):
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
    )
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)

    # Actualizar total en PerfilFinanciero
    perfil = db.query(PerfilFinanciero).first()
    if perfil:
        activos = db.query(GastoFijo).filter(GastoFijo.activo == True).all()
        perfil.compromisos_fijos_mensual = sum(g.monto for g in activos)
        db.commit()

    return nuevo


@router.patch("/{gasto_id}/toggle-pagado", response_model=GastoFijoResponse)
def toggle_pagado_gasto_fijo(gasto_id: int, db: Session = Depends(get_db)):
    """
    Alterna el estado de pagado este mes para un compromiso fijo.
    """
    gasto = db.query(GastoFijo).filter(GastoFijo.id == gasto_id).first()
    if not gasto:
        raise HTTPException(status_code=404, detail="Gasto fijo no encontrado")
    gasto.pagado_este_mes = not gasto.pagado_este_mes
    db.commit()
    db.refresh(gasto)
    return gasto


@router.delete("/{gasto_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_gasto_fijo(gasto_id: int, db: Session = Depends(get_db)):
    """
    Elimina un compromiso fijo y recalcula el total mensual.
    """
    gasto = db.query(GastoFijo).filter(GastoFijo.id == gasto_id).first()
    if not gasto:
        raise HTTPException(status_code=404, detail="Gasto fijo no encontrado")
    db.delete(gasto)
    db.commit()

    perfil = db.query(PerfilFinanciero).first()
    if perfil:
        activos = db.query(GastoFijo).filter(GastoFijo.activo == True).all()
        perfil.compromisos_fijos_mensual = sum(g.monto for g in activos)
        db.commit()
    return None
