from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.api.deps import get_current_user_id, check_auth_if_users_exist
from backend.app.models import (
    GastoFijo,
    PerfilFinanciero,
    Cuenta,
    Transaccion,
    TipoCuenta,
    TipoTransaccion,
    MedioCaptura,
)
from backend.app.schemas import (
    GastoFijoCreate,
    GastoFijoUpdate,
    GastoFijoResponse,
    GastosFijosResumen,
    GastoFijoPagarRequest,
)
from backend.app.services.financial_engine import FinancialEngine
from backend.app.services.categorizer import CategorizadorComercios
from backend.app.timezone import ahora_colombia, ahora_utc_db

router = APIRouter()


@router.get("", response_model=GastosFijosResumen)
@router.get("/", response_model=GastosFijosResumen)
def listar_gastos_fijos(
    db: Session = Depends(get_db),
    current_uid: Optional[int] = Depends(get_current_user_id)
):
    """
    Obtiene el listado de compromisos fijos y el estado del ciclo salarial (apartados de nómina vs pendientes).
    Aplica reset mensual automático al inicio del mes según zona horaria de Colombia.
    """
    check_auth_if_users_exist(current_uid, db, "tus gastos fijos")
    return FinancialEngine.obtener_resumen_gastos_fijos(db, usuario_id=current_uid)


@router.post("", response_model=GastoFijoResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=GastoFijoResponse, status_code=status.HTTP_201_CREATED)
def crear_gasto_fijo(
    gasto_in: GastoFijoCreate,
    db: Session = Depends(get_db),
    current_uid: Optional[int] = Depends(get_current_user_id)
):
    """
    Crea un nuevo gasto fijo mensual (arriendo, servicios, suscripción, o frecuente como gasolina).
    """
    check_auth_if_users_exist(current_uid, db, "crear gastos fijos")
    ahora_col = ahora_colombia()
    mes_actual = ahora_col.strftime("%Y-%m")

    es_frecuente = bool(gasto_in.es_frecuente)
    frecuencia = max(1, int(gasto_in.frecuencia_veces or 1)) if es_frecuente else 1
    pagado = bool(gasto_in.pagado_este_mes)
    veces = frecuencia if (pagado and es_frecuente) else int(gasto_in.veces_pagadas or 0)

    nuevo = GastoFijo(
        nombre=gasto_in.nombre.strip(),
        monto=float(gasto_in.monto),
        dia_pago=gasto_in.dia_pago or 1,
        categoria=gasto_in.categoria or "Hogar y Servicios",
        activo=True,
        pagado_este_mes=pagado,
        es_frecuente=es_frecuente,
        frecuencia_veces=frecuencia,
        veces_pagadas=veces,
        ultimo_mes_pagado=mes_actual if pagado else None,
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


@router.post("/{gasto_id}/pagar", response_model=GastoFijoResponse)
def pagar_gasto_fijo(
    gasto_id: int,
    payload: GastoFijoPagarRequest,
    db: Session = Depends(get_db),
    current_uid: Optional[int] = Depends(get_current_user_id)
):
    """
    Paga un gasto fijo deduciendo el monto del método de pago/cuenta seleccionada,
    creando la transacción correspondiente y actualizando el estado a cubierto (o aumentando la cuota frecuente).
    """
    check_auth_if_users_exist(current_uid, db, "pagar este gasto fijo")
    gasto_q = db.query(GastoFijo).filter(GastoFijo.id == gasto_id)
    if current_uid:
        gasto_q = gasto_q.filter((GastoFijo.usuario_id == current_uid) | (GastoFijo.usuario_id == None))
    gasto = gasto_q.first()
    if not gasto:
        raise HTTPException(status_code=404, detail="Gasto fijo no encontrado")

    cuenta_q = db.query(Cuenta).filter(Cuenta.id == payload.cuenta_id)
    if current_uid:
        cuenta_q = cuenta_q.filter((Cuenta.usuario_id == current_uid) | (Cuenta.usuario_id == None))
    cuenta = cuenta_q.first()
    if not cuenta:
        raise HTTPException(status_code=404, detail="Cuenta de pago no encontrada")

    # Determinar monto a descontar
    if payload.monto and payload.monto > 0:
        monto_cobro = float(payload.monto)
    elif gasto.es_frecuente:
        frecuencia = max(1, gasto.frecuencia_veces or 1)
        monto_cobro = round(gasto.monto / frecuencia, 2)
    else:
        monto_cobro = float(gasto.monto)

    # 1. Descontar del saldo o cargar deuda a tarjeta de crédito
    if cuenta.tipo in (TipoCuenta.DEBITO, TipoCuenta.EFECTIVO, TipoCuenta.ALTO_RENDIMIENTO):
        cuenta.saldo_actual -= monto_cobro
    elif cuenta.tipo == TipoCuenta.CREDITO:
        cuenta.saldo_actual += monto_cobro

    # 2. Sugerir categoría
    cat_nombre, cat_id = CategorizadorComercios.sugerir_categoria(gasto.nombre, db)

    # 3. Crear Transacción
    if gasto.es_frecuente:
        nueva_vez = (gasto.veces_pagadas or 0) + 1
        descripcion_tx = f"Compromiso frecuente: {gasto.nombre} ({nueva_vez}/{gasto.frecuencia_veces})"
    else:
        descripcion_tx = f"Compromiso fijo mensual: {gasto.nombre}"

    tx = Transaccion(
        monto=monto_cobro,
        tipo=TipoTransaccion.EGRESO,
        medio=MedioCaptura.MANUAL,
        fecha=ahora_utc_db(),
        comercio=gasto.nombre,
        descripcion=descripcion_tx,
        cuenta_origen_id=cuenta.id,
        categoria_id=cat_id,
        es_gasto_hormiga=CategorizadorComercios.es_gasto_hormiga(monto_cobro),
        usuario_id=current_uid or cuenta.usuario_id
    )
    db.add(tx)
    db.flush()

    # 4. Actualizar Gasto Fijo
    ahora_col = ahora_colombia()
    gasto.ultimo_mes_pagado = ahora_col.strftime("%Y-%m")
    gasto.ultima_transaccion_id = tx.id

    if gasto.es_frecuente:
        gasto.veces_pagadas = (gasto.veces_pagadas or 0) + 1
        if gasto.veces_pagadas >= (gasto.frecuencia_veces or 1):
            gasto.pagado_este_mes = True
    else:
        gasto.veces_pagadas = 1
        gasto.pagado_este_mes = True

    db.commit()
    db.refresh(gasto)
    return gasto


@router.post("/{gasto_id}/revertir", response_model=GastoFijoResponse)
def revertir_pago_gasto_fijo(
    gasto_id: int,
    db: Session = Depends(get_db),
    current_uid: Optional[int] = Depends(get_current_user_id)
):
    """
    Anula el último pago de un gasto fijo, reintegrando el dinero a la cuenta o saldo original
    y eliminando el movimiento correspondiente.
    """
    check_auth_if_users_exist(current_uid, db, "este gasto fijo")
    gasto_q = db.query(GastoFijo).filter(GastoFijo.id == gasto_id)
    if current_uid:
        gasto_q = gasto_q.filter((GastoFijo.usuario_id == current_uid) | (GastoFijo.usuario_id == None))
    gasto = gasto_q.first()
    if not gasto:
        raise HTTPException(status_code=404, detail="Gasto fijo no encontrado")

    # 1. Si hay transacción asociada, revertir el saldo de la cuenta y eliminar la transacción
    if gasto.ultima_transaccion_id:
        tx = db.query(Transaccion).filter(Transaccion.id == gasto.ultima_transaccion_id).first()
        if tx and tx.cuenta_origen:
            if tx.cuenta_origen.tipo in (TipoCuenta.DEBITO, TipoCuenta.EFECTIVO, TipoCuenta.ALTO_RENDIMIENTO):
                tx.cuenta_origen.saldo_actual += tx.monto
            elif tx.cuenta_origen.tipo == TipoCuenta.CREDITO:
                tx.cuenta_origen.saldo_actual -= tx.monto
            db.delete(tx)

    # 2. Reducir contador o desmarcar
    if gasto.es_frecuente:
        gasto.veces_pagadas = max(0, (gasto.veces_pagadas or 0) - 1)
        if gasto.veces_pagadas < (gasto.frecuencia_veces or 1):
            gasto.pagado_este_mes = False
    else:
        gasto.veces_pagadas = 0
        gasto.pagado_este_mes = False

    if gasto.veces_pagadas == 0:
        gasto.ultimo_mes_pagado = None
        gasto.ultima_transaccion_id = None

    db.commit()
    db.refresh(gasto)
    return gasto


@router.patch("/{gasto_id}/toggle-pagado", response_model=GastoFijoResponse)
def toggle_pagado_gasto_fijo(
    gasto_id: int,
    db: Session = Depends(get_db),
    current_uid: Optional[int] = Depends(get_current_user_id)
):
    """
    Alterna el estado de pagado para un compromiso fijo (compatibilidad hacia atrás).
    Si pasa a cubierto, deduce de la primera cuenta activa y genera el movimiento.
    Si pasa a pendiente, revierte el saldo y elimina el movimiento.
    """
    check_auth_if_users_exist(current_uid, db, "este gasto fijo")
    gasto_q = db.query(GastoFijo).filter(GastoFijo.id == gasto_id)
    if current_uid:
        gasto_q = gasto_q.filter((GastoFijo.usuario_id == current_uid) | (GastoFijo.usuario_id == None))
    gasto = gasto_q.first()
    if not gasto:
        raise HTTPException(status_code=404, detail="Gasto fijo no encontrado")

    if gasto.pagado_este_mes or (gasto.veces_pagadas and gasto.veces_pagadas > 0):
        return revertir_pago_gasto_fijo(gasto_id, db, current_uid)
    else:
        # Buscar cuenta activa para pagar
        cuentas_q = db.query(Cuenta).filter(Cuenta.activa == True)
        if current_uid:
            cuentas_q = cuentas_q.filter((Cuenta.usuario_id == current_uid) | (Cuenta.usuario_id == None))
        cuenta = cuentas_q.first()
        if cuenta:
            return pagar_gasto_fijo(gasto_id, GastoFijoPagarRequest(cuenta_id=cuenta.id), db, current_uid)
        else:
            gasto.pagado_este_mes = True
            gasto.ultimo_mes_pagado = ahora_colombia().strftime("%Y-%m")
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
    check_auth_if_users_exist(current_uid, db, "este gasto fijo")
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
