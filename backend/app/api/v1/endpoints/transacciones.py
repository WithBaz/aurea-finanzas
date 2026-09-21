from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models import Cuenta, Transaccion, TipoCuenta, TipoTransaccion, MedioCaptura
from backend.app.schemas import TransaccionCreate, TransaccionResponse
from backend.app.services.categorizer import CategorizadorComercios

router = APIRouter()


@router.get("", response_model=List[TransaccionResponse])
def listar_transacciones(
    tipo: Optional[TipoTransaccion] = None,
    medio: Optional[MedioCaptura] = None,
    cuenta_id: Optional[int] = None,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """
    Lista las transacciones históricas con filtros opcionales.
    """
    query = db.query(Transaccion)
    if tipo:
        query = query.filter(Transaccion.tipo == tipo)
    if medio:
        query = query.filter(Transaccion.medio == medio)
    if cuenta_id:
        query = query.filter((Transaccion.cuenta_origen_id == cuenta_id) | (Transaccion.cuenta_destino_id == cuenta_id))
    return query.order_by(Transaccion.fecha.desc()).limit(limit).all()


@router.post("", response_model=TransaccionResponse, status_code=status.HTTP_201_CREATED)
def crear_transaccion_manual(
    tx_in: TransaccionCreate,
    db: Session = Depends(get_db)
):
    """
    Registro manual de transacciones (especialmente útil para efectivo y ajustes rápidos).
    """
    cuenta_origen = db.query(Cuenta).filter(Cuenta.id == tx_in.cuenta_origen_id).first()
    if not cuenta_origen:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cuenta de origen no encontrada"
        )

    # Actualizar saldos según tipo
    if tx_in.tipo == TipoTransaccion.EGRESO:
        if cuenta_origen.tipo == TipoCuenta.DEBITO or cuenta_origen.tipo == TipoCuenta.EFECTIVO:
            cuenta_origen.saldo_actual -= tx_in.monto
        elif cuenta_origen.tipo == TipoCuenta.CREDITO:
            cuenta_origen.saldo_actual += tx_in.monto
    elif tx_in.tipo == TipoTransaccion.INGRESO:
        cuenta_origen.saldo_actual += tx_in.monto
    elif tx_in.tipo == TipoTransaccion.TRANSFERENCIA_INTERNA:
        if not tx_in.cuenta_destino_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Las transferencias internas requieren 'cuenta_destino_id'"
            )
        cuenta_destino = db.query(Cuenta).filter(Cuenta.id == tx_in.cuenta_destino_id).first()
        if not cuenta_destino:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cuenta de destino no encontrada")
        cuenta_origen.saldo_actual -= tx_in.monto
        cuenta_destino.saldo_actual += tx_in.monto

    # Auto-categorizar si no se envió categoría
    cat_id = tx_in.categoria_id
    if not cat_id:
        _, cat_id = CategorizadorComercios.sugerir_categoria(tx_in.comercio, db)

    es_hormiga = CategorizadorComercios.es_gasto_hormiga(tx_in.monto)

    tx = Transaccion(
        monto=tx_in.monto,
        tipo=tx_in.tipo,
        medio=tx_in.medio,
        fecha=tx_in.fecha or datetime.utcnow(),
        comercio=tx_in.comercio,
        descripcion=tx_in.descripcion,
        cuenta_origen_id=tx_in.cuenta_origen_id,
        cuenta_destino_id=tx_in.cuenta_destino_id,
        categoria_id=cat_id,
        cuotas_totales=tx_in.cuotas_totales,
        cuota_actual=tx_in.cuota_actual,
        es_gasto_hormiga=es_hormiga
    )
    db.add(tx)
    db.commit()
    db.refresh(tx)
    return tx
