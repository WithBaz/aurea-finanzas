import hashlib
from datetime import datetime, timezone
from typing import Union, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models import (
    Cuenta,
    Transaccion,
    TipoCuenta,
    TipoTransaccion,
    MedioCaptura,
)
from backend.app.schemas import (
    ApplePayWebhookPayload,
    SMSWebhookPayload,
    WebhookIngestResponse,
)
from backend.app.services.sms_parser import SMSParser
from backend.app.services.categorizer import CategorizadorComercios

router = APIRouter()


def calcular_hash_idempotencia(monto: float, comercio: str, fecha_str: str) -> str:
    cadena = f"{monto:.2f}_{comercio.lower().strip()}_{fecha_str}"
    return hashlib.sha256(cadena.encode("utf-8")).hexdigest()


@router.post("/ios-shortcut", response_model=WebhookIngestResponse)
def procesar_atajo_ios(
    payload: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """
    Endpoint receptor para las Automatizaciones de Atajos de iOS (Apple Shortcuts).
    Procesa tanto pagos con Apple Pay como mensajes SMS de bancos colombianos.
    """
    medio_raw = str(payload.get("medio", "SMS")).upper()
    fecha_movimiento = datetime.now(timezone.utc)

    # 1. Rama Apple Pay
    if medio_raw == "APPLE_PAY":
        monto = float(payload.get("monto", 0.0))
        comercio = str(payload.get("comercio", "Comercio Apple Pay")).strip()
        tarjeta_nombre = payload.get("tarjeta")

        if monto <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El monto de la transacción de Apple Pay debe ser superior a 0 COP"
            )

        # Buscar cuenta asociada (o cuenta débito/crédito por defecto)
        cuenta = None
        if tarjeta_nombre:
            cuenta = db.query(Cuenta).filter(Cuenta.nombre.ilike(f"%{tarjeta_nombre}%"), Cuenta.activa == True).first()
        if not cuenta:
            cuenta = db.query(Cuenta).filter(Cuenta.tipo.in_([TipoCuenta.DEBITO, TipoCuenta.CREDITO]), Cuenta.activa == True).first()
        
        if not cuenta:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No hay cuentas activas registradas para asociar el pago de Apple Pay"
            )

        # Idempotencia
        fecha_clave = fecha_movimiento.strftime("%Y-%m-%d_%H:%M")
        hash_idemp = calcular_hash_idempotencia(monto, comercio, fecha_clave)
        transaccion_existente = db.query(Transaccion).filter(Transaccion.hash_idempotencia == hash_idemp).first()
        if transaccion_existente:
            return WebhookIngestResponse(
                status="ignorado_duplicado",
                mensaje="Transacción ya registrada previamente (Idempotencia)",
                transaccion_id=transaccion_existente.id,
                tipo_detectado=transaccion_existente.tipo.value,
                monto_cop=transaccion_existente.monto,
                comercio=transaccion_existente.comercio,
                cuenta_afectada=cuenta.nombre,
                es_transferencia_interna=False
            )

        # Categorizar
        cat_nombre, cat_id = CategorizadorComercios.sugerir_categoria(comercio, db)
        es_hormiga = CategorizadorComercios.es_gasto_hormiga(monto)

        # Descontar saldo o registrar deuda
        if cuenta.tipo == TipoCuenta.DEBITO:
            cuenta.saldo_actual -= monto
        elif cuenta.tipo == TipoCuenta.CREDITO:
            cuenta.saldo_actual += monto  # Deuda acumulada

        transaccion = Transaccion(
            monto=monto,
            tipo=TipoTransaccion.EGRESO,
            medio=MedioCaptura.APPLE_PAY,
            fecha=fecha_movimiento,
            comercio=comercio,
            descripcion=f"Pago Apple Pay con {cuenta.nombre}",
            cuenta_origen_id=cuenta.id,
            categoria_id=cat_id,
            es_gasto_hormiga=es_hormiga,
            hash_idempotencia=hash_idemp,
            raw_payload=str(payload)
        )
        db.add(transaccion)
        db.commit()
        db.refresh(transaccion)

        return WebhookIngestResponse(
            status="exitoso",
            mensaje=f"Pago Apple Pay de ${monto:,.0f} COP registrado en {comercio}",
            transaccion_id=transaccion.id,
            tipo_detectado="EGRESO",
            monto_cop=monto,
            comercio=comercio,
            cuenta_afectada=cuenta.nombre,
            es_transferencia_interna=False
        )

    # 2. Rama SMS Bancario
    texto_sms = payload.get("texto_sms", "")
    if not texto_sms:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Se requiere el campo 'texto_sms' para procesar la automatización SMS"
        )

    resultado_parser = SMSParser.parse_sms(texto_sms, remitente=payload.get("remitente"))
    if not resultado_parser.get("es_valido"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=resultado_parser.get("mensaje", "No se pudo interpretar el SMS")
        )

    monto = resultado_parser["monto"]
    comercio = resultado_parser["comercio"]
    tipo_str = resultado_parser["tipo"]
    es_retiro = resultado_parser.get("es_retiro_cajero", False)

    # Idempotencia
    fecha_clave = fecha_movimiento.strftime("%Y-%m-%d_%H:%M")
    hash_idemp = calcular_hash_idempotencia(monto, comercio, fecha_clave)
    transaccion_existente = db.query(Transaccion).filter(Transaccion.hash_idempotencia == hash_idemp).first()
    if transaccion_existente:
        return WebhookIngestResponse(
            status="ignorado_duplicado",
            mensaje="Transacción ya registrada previamente (Idempotencia)",
            transaccion_id=transaccion_existente.id,
            tipo_detectado=transaccion_existente.tipo.value,
            monto_cop=transaccion_existente.monto,
            comercio=transaccion_existente.comercio,
            cuenta_afectada="Existente",
            es_transferencia_interna=transaccion_existente.tipo == TipoTransaccion.TRANSFERENCIA_INTERNA
        )

    # Caso Especial: Retiro en cajero -> Transferencia interna (Débito a Efectivo)
    if es_retiro or tipo_str == "TRANSFERENCIA_INTERNA":
        cuenta_bancaria = db.query(Cuenta).filter(Cuenta.tipo == TipoCuenta.DEBITO, Cuenta.activa == True).first()
        billetera_efectivo = db.query(Cuenta).filter(Cuenta.tipo == TipoCuenta.EFECTIVO, Cuenta.activa == True).first()

        if not billetera_efectivo:
            billetera_efectivo = Cuenta(
                nombre="Billetera Efectivo",
                tipo=TipoCuenta.EFECTIVO,
                saldo_actual=0.0
            )
            db.add(billetera_efectivo)
            db.commit()
            db.refresh(billetera_efectivo)

        if cuenta_bancaria:
            cuenta_bancaria.saldo_actual -= monto
        billetera_efectivo.saldo_actual += monto

        transaccion = Transaccion(
            monto=monto,
            tipo=TipoTransaccion.TRANSFERENCIA_INTERNA,
            medio=MedioCaptura.SMS,
            fecha=fecha_movimiento,
            comercio="Retiro en Cajero Automático",
            descripcion="Retiro de efectivo conciliado como transferencia interna",
            cuenta_origen_id=cuenta_bancaria.id if cuenta_bancaria else billetera_efectivo.id,
            cuenta_destino_id=billetera_efectivo.id,
            es_gasto_hormiga=False,
            hash_idempotencia=hash_idemp,
            raw_payload=texto_sms
        )
        db.add(transaccion)
        db.commit()
        db.refresh(transaccion)

        return WebhookIngestResponse(
            status="exitoso",
            mensaje=f"Retiro de ${monto:,.0f} COP transferido a Billetera Efectivo sin duplicar gasto",
            transaccion_id=transaccion.id,
            tipo_detectado="TRANSFERENCIA_INTERNA",
            monto_cop=monto,
            comercio="Cajero Automático",
            cuenta_afectada="Débito -> Efectivo",
            es_transferencia_interna=True
        )

    # Caso Compra / Egreso
    if tipo_str == "EGRESO":
        es_credito = resultado_parser.get("es_credito", False)
        tipo_filtro = TipoCuenta.CREDITO if es_credito else TipoCuenta.DEBITO
        cuenta = db.query(Cuenta).filter(Cuenta.tipo == tipo_filtro, Cuenta.activa == True).first()
        if not cuenta:
            cuenta = db.query(Cuenta).filter(Cuenta.tipo == TipoCuenta.DEBITO, Cuenta.activa == True).first()

        if cuenta:
            if cuenta.tipo == TipoCuenta.DEBITO:
                cuenta.saldo_actual -= monto
            else:
                cuenta.saldo_actual += monto

        cat_nombre, cat_id = CategorizadorComercios.sugerir_categoria(comercio, db)
        es_hormiga = CategorizadorComercios.es_gasto_hormiga(monto)

        transaccion = Transaccion(
            monto=monto,
            tipo=TipoTransaccion.EGRESO,
            medio=MedioCaptura.SMS,
            fecha=fecha_movimiento,
            comercio=comercio,
            descripcion=resultado_parser.get("descripcion", "Egreso detectado por SMS"),
            cuenta_origen_id=cuenta.id if cuenta else 1,
            categoria_id=cat_id,
            es_gasto_hormiga=es_hormiga,
            hash_idempotencia=hash_idemp,
            raw_payload=texto_sms
        )
        db.add(transaccion)
        db.commit()
        db.refresh(transaccion)

        return WebhookIngestResponse(
            status="exitoso",
            mensaje=f"Compra de ${monto:,.0f} COP en {comercio} registrada por SMS",
            transaccion_id=transaccion.id,
            tipo_detectado="EGRESO",
            monto_cop=monto,
            comercio=comercio,
            cuenta_afectada=cuenta.nombre if cuenta else "Cuenta Principal",
            es_transferencia_interna=False
        )

    # Caso Ingreso
    cuenta_ingreso = db.query(Cuenta).filter(Cuenta.tipo == TipoCuenta.DEBITO, Cuenta.activa == True).first()
    if cuenta_ingreso:
        cuenta_ingreso.saldo_actual += monto

    transaccion = Transaccion(
        monto=monto,
        tipo=TipoTransaccion.INGRESO,
        medio=MedioCaptura.SMS,
        fecha=fecha_movimiento,
        comercio=comercio,
        descripcion=resultado_parser.get("descripcion", "Ingreso detectado por SMS"),
        cuenta_origen_id=cuenta_ingreso.id if cuenta_ingreso else 1,
        es_gasto_hormiga=False,
        hash_idempotencia=hash_idemp,
        raw_payload=texto_sms
    )
    db.add(transaccion)
    db.commit()
    db.refresh(transaccion)

    return WebhookIngestResponse(
        status="exitoso",
        mensaje=f"Ingreso de ${monto:,.0f} COP registrado por SMS",
        transaccion_id=transaccion.id,
        tipo_detectado="INGRESO",
        monto_cop=monto,
        comercio=comercio,
        cuenta_afectada=cuenta_ingreso.nombre if cuenta_ingreso else "Cuenta Principal",
        es_transferencia_interna=False
    )
