from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models import Cuenta, Transaccion, TipoCuenta, TipoTransaccion, MedioCaptura
from backend.app.schemas import (
    CuentaCreate,
    CuentaUpdate,
    CuentaResponse,
    PagoTarjetaRequest,
    PagoTarjetaResponse
)
from backend.app.api.deps import get_current_user_id

router = APIRouter()


@router.get("", response_model=List[CuentaResponse])
def listar_cuentas(
    current_uid: Optional[int] = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Lista todos los instrumentos financieros del usuario actual (Débito, Crédito, Alto Rendimiento, Efectivo).
    """
    query = db.query(Cuenta).filter(Cuenta.activa == True)
    if current_uid:
        query = query.filter((Cuenta.usuario_id == current_uid) | (Cuenta.usuario_id == None))
    return query.all()


@router.post("", response_model=CuentaResponse, status_code=status.HTTP_201_CREATED)
def crear_cuenta(
    cuenta_in: CuentaCreate,
    current_uid: Optional[int] = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Registra un nuevo instrumento financiero para el usuario actual.
    Para tarjetas de crédito, si se especifica cupo_disponible y cupo_total,
    calcula la deuda inicial automáticamente: saldo_actual = max(0.0, cupo_total - cupo_disponible).
    """
    data = cuenta_in.model_dump()
    cupo_disp = data.pop("cupo_disponible", None)

    if data.get("tipo") == TipoCuenta.CREDITO and cupo_disp is not None:
        cupo_tot = float(data.get("cupo_total") or 0.0)
        data["saldo_actual"] = max(0.0, cupo_tot - float(cupo_disp))

    if current_uid:
        data["usuario_id"] = current_uid

    cuenta = Cuenta(**data)
    db.add(cuenta)
    db.commit()
    db.refresh(cuenta)
    return cuenta


@router.get("/{cuenta_id}", response_model=CuentaResponse)
def obtener_cuenta(cuenta_id: int, db: Session = Depends(get_db)):
    cuenta = db.query(Cuenta).filter(Cuenta.id == cuenta_id).first()
    if not cuenta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cuenta no encontrada"
        )
    return cuenta


@router.put("/{cuenta_id}", response_model=CuentaResponse)
def actualizar_cuenta(
    cuenta_id: int,
    cuenta_in: CuentaUpdate,
    db: Session = Depends(get_db)
):
    """
    Actualiza el saldo o datos de una cuenta existente.
    """
    cuenta = db.query(Cuenta).filter(Cuenta.id == cuenta_id).first()
    if not cuenta:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cuenta no encontrada")

    update_data = cuenta_in.model_dump(exclude_unset=True)
    cupo_disp = update_data.pop("cupo_disponible", None)
    if cuenta.tipo == TipoCuenta.CREDITO and cupo_disp is not None:
        cupo_tot = float(update_data.get("cupo_total") if update_data.get("cupo_total") is not None else (cuenta.cupo_total or 0.0))
        update_data["saldo_actual"] = max(0.0, cupo_tot - float(cupo_disp))

    for field, value in update_data.items():
        setattr(cuenta, field, value)

    db.commit()
    db.refresh(cuenta)
    return cuenta


@router.delete("/{cuenta_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_cuenta(cuenta_id: int, db: Session = Depends(get_db)):
    """
    Elimina una cuenta y sus transacciones asociadas.
    """
    cuenta = db.query(Cuenta).filter(Cuenta.id == cuenta_id).first()
    if not cuenta:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cuenta no encontrada")
    
    # Eliminar en cascada las transacciones asociadas a la cuenta
    db.query(Transaccion).filter(
        (Transaccion.cuenta_origen_id == cuenta_id) | (Transaccion.cuenta_destino_id == cuenta_id)
    ).delete(synchronize_session=False)

    db.delete(cuenta)
    db.commit()
    return None


@router.post("/sincronizar", response_model=List[CuentaResponse])
def sincronizar_cuentas(cuentas_in: List[CuentaCreate], db: Session = Depends(get_db)):
    """
    Sincroniza y rehidrata cuentas desde la caché local del cliente cuando
    un contenedor efímero se reinicia o se conecta por primera vez.
    """
    resultados = []
    for c_data in cuentas_in:
        existente = db.query(Cuenta).filter(Cuenta.nombre == c_data.nombre, Cuenta.activa == True).first()
        if existente:
            existente.saldo_actual = c_data.saldo_actual
            existente.tipo = c_data.tipo
            existente.tasa_ea = c_data.tasa_ea
            existente.cupo_total = c_data.cupo_total
            resultados.append(existente)
        else:
            d = c_data.model_dump()
            d.pop("cupo_disponible", None)
            nueva = Cuenta(**d)
            db.add(nueva)
            resultados.append(nueva)
    db.commit()
    for r in resultados:
        db.refresh(r)
    return resultados


@router.post("/{cuenta_id}/corte", response_model=CuentaResponse)
def registrar_corte_tarjeta(
    cuenta_id: int,
    db: Session = Depends(get_db)
):
    """
    Registra la fecha de corte para una tarjeta de crédito, fijando la deuda actual como
    el saldo facturado al corte (saldo_al_corte) y marcando el estado como PENDIENTE_PAGO.
    """
    cuenta = db.query(Cuenta).filter(Cuenta.id == cuenta_id).first()
    if not cuenta:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cuenta no encontrada")
    if cuenta.tipo != TipoCuenta.CREDITO:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Solo las tarjetas de crédito tienen fecha de corte")

    cuenta.saldo_al_corte = max(0.0, cuenta.saldo_actual)
    cuenta.fecha_ultimo_corte = datetime.now(timezone.utc)
    cuenta.estado_corte = "PENDIENTE_PAGO" if cuenta.saldo_al_corte > 0 else "AL_DIA"
    db.commit()
    db.refresh(cuenta)
    return cuenta


@router.post("/{cuenta_id}/pagar", response_model=PagoTarjetaResponse)
def registrar_pago_tarjeta(
    cuenta_id: int,
    pago_in: PagoTarjetaRequest,
    db: Session = Depends(get_db)
):
    """
    Registra el pago total o parcial de una tarjeta de crédito.
    Si se especifica cuenta_origen_id, descuenta de la cuenta de ahorros/débito y
    genera una transacción de TRANSFERENCIA_INTERNA (sin computar doble gasto en el presupuesto).
    Disminuye la deuda de la tarjeta y restablece su cupo disponible.
    """
    cuenta = db.query(Cuenta).filter(Cuenta.id == cuenta_id).first()
    if not cuenta:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tarjeta no encontrada")
    if cuenta.tipo != TipoCuenta.CREDITO:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Solo se pueden registrar pagos a tarjetas de crédito")

    monto = float(pago_in.monto)
    if monto <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El monto a pagar debe ser mayor a 0 COP")

    cuenta_origen = None
    tx_creada_id = None
    if pago_in.cuenta_origen_id:
        cuenta_origen = db.query(Cuenta).filter(Cuenta.id == pago_in.cuenta_origen_id).first()
        if not cuenta_origen:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cuenta de origen para el pago no encontrada")
        # Descontar de la cuenta líquida
        cuenta_origen.saldo_actual -= monto
        
        # Registrar movimiento de transferencia interna
        tx = Transaccion(
            monto=monto,
            tipo=TipoTransaccion.TRANSFERENCIA_INTERNA,
            medio=MedioCaptura.MANUAL,
            fecha=datetime.now(timezone.utc),
            comercio=f"Pago {cuenta.nombre}",
            descripcion=pago_in.descripcion or f"Pago de tarjeta {cuenta.nombre} con fondos de {cuenta_origen.nombre}",
            cuenta_origen_id=cuenta_origen.id,
            cuenta_destino_id=cuenta.id,
            usuario_id=cuenta.usuario_id
        )
        db.add(tx)
        db.flush()
        tx_creada_id = tx.id

    # Reducir deuda de la tarjeta de crédito
    cuenta.saldo_actual = max(0.0, cuenta.saldo_actual - monto)
    
    # Reducir saldo al corte si existe
    if cuenta.saldo_al_corte:
        cuenta.saldo_al_corte = max(0.0, cuenta.saldo_al_corte - monto)
    if not cuenta.saldo_al_corte or cuenta.saldo_al_corte <= 0.0:
        cuenta.saldo_al_corte = 0.0
        cuenta.estado_corte = "AL_DIA"

    cuenta.fecha_ultimo_pago = datetime.now(timezone.utc)
    db.commit()
    db.refresh(cuenta)

    cupo_disp = max(0.0, (cuenta.cupo_total or 0.0) - cuenta.saldo_actual)
    monto_fmt = f"{int(monto):,}".replace(",", ".") + " pesos"

    return PagoTarjetaResponse(
        status="exitoso",
        mensaje=f"Pago de {monto_fmt} registrado exitosamente para {cuenta.nombre}",
        monto_pagado=monto,
        saldo_deuda_restante=cuenta.saldo_actual,
        cupo_disponible=cupo_disp,
        saldo_al_corte_restante=cuenta.saldo_al_corte or 0.0,
        estado_corte=cuenta.estado_corte or "AL_DIA",
        transaccion_id=tx_creada_id
    )

