import hashlib
from datetime import datetime, timezone
from typing import Union, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Header, Query, Request
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models import (
    Cuenta,
    Transaccion,
    TipoCuenta,
    TipoTransaccion,
    MedioCaptura,
    Usuario,
)
from backend.app.schemas import (
    ApplePayWebhookPayload,
    SMSWebhookPayload,
    WebhookIngestResponse,
)
from backend.app.services.sms_parser import SMSParser, limpiar_monto
from backend.app.services.categorizer import CategorizadorComercios
from backend.app.timezone import ahora_colombia, ahora_utc_db, parsear_fecha_para_db



router = APIRouter()


def calcular_hash_idempotencia(monto: float, comercio: str, fecha_str: str) -> str:
    cadena = f"{monto:.2f}_{comercio.lower().strip()}_{fecha_str}"
    return hashlib.sha256(cadena.encode("utf-8")).hexdigest()


@router.api_route("/ios-shortcut", methods=["GET", "POST"], response_model=WebhookIngestResponse)
async def procesar_atajo_ios(
    request: Request,
    payload: Optional[Dict[str, Any]] = None,
    token: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None),
    x_aurea_token: Optional[str] = Header(None, alias="X-Aurea-Token"),
    db: Session = Depends(get_db)
):
    """
    Endpoint receptor para las Automatizaciones de Atajos de iOS (Apple Shortcuts).
    Procesa tanto pagos con Apple Pay como mensajes SMS de bancos colombianos con verificación opcional de token.
    Soporta POST (JSON, Form) y GET (Query params) para pruebas inmediatas sin costo.
    """
    # 1. Extraer payload de JSON, Form o Query Params
    final_payload: Dict[str, Any] = {}
    if request.method == "POST":
        try:
            parsed_json = await request.json()
            if isinstance(parsed_json, dict):
                final_payload.update(parsed_json)
        except Exception:
            try:
                form = await request.form()
                final_payload.update(dict(form))
            except Exception:
                pass

    # Combinar con query parameters
    for k, v in request.query_params.items():
        if k not in final_payload or final_payload[k] is None or final_payload[k] == "":
            final_payload[k] = v

    if payload and isinstance(payload, dict):
        final_payload.update(payload)

    # 2. Verificación de token criptográfico
    token_val = None
    if authorization and authorization.lower().startswith("bearer "):
        token_val = authorization[7:].strip()
    elif x_aurea_token:
        token_val = x_aurea_token.strip()
    elif token:
        token_val = token.strip()
    elif final_payload.get("token"):
        token_val = str(final_payload.get("token")).strip()
    elif request.query_params.get("token"):
        token_val = str(request.query_params.get("token")).strip()

    user_from_token = None
    if token_val:
        user_from_token = db.query(Usuario).filter(Usuario.biometric_token == token_val).first()
        if not user_from_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token de atajo iOS inválido o no reconocido."
            )

    total_usuarios = db.query(Usuario).count()
    if not user_from_token:
        if total_usuarios == 1:
            # En instalación de un único usuario (caso personal), asociar automáticamente sin exigir token
            user_from_token = db.query(Usuario).first()
        elif total_usuarios > 1:
            # En multi-usuario, permitir ?usuario=username o exigir token
            user_param = (
                final_payload.get("usuario")
                or final_payload.get("user")
                or final_payload.get("username")
            )
            if user_param:
                user_from_token = db.query(Usuario).filter(Usuario.username.ilike(str(user_param).strip())).first()
            if not user_from_token:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token de autorización requerido para ejecutar atajos de iOS en entorno multi-usuario."
                )

    if user_from_token and final_payload.get("usuario_id") and int(final_payload.get("usuario_id")) != user_from_token.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para ejecutar atajos para otro usuario."
        )

    target_user_id = user_from_token.id if user_from_token else final_payload.get("usuario_id")

    # Detección inteligente de medio (APPLE_PAY vs SMS)
    medio_raw = str(
        final_payload.get("medio")
        or final_payload.get("source")
        or final_payload.get("channel")
        or final_payload.get("tipo")
        or ""
    ).upper().strip()

    tiene_tarjeta = any(k in final_payload for k in ("tarjeta", "card", "card_name", "cardName", "account", "cuenta"))
    tiene_monto = any(k in final_payload for k in ("monto", "amount", "valor", "precio", "total"))
    es_sms = "texto_sms" in final_payload or "sms" in final_payload or "body" in final_payload

    if not medio_raw:
        if tiene_tarjeta or (tiene_monto and not es_sms):
            medio_raw = "APPLE_PAY"
        else:
            medio_raw = "SMS"

    if medio_raw in ("APPLE_PAY", "APPLEPAY", "WALLET", "APPLE PAY"):
        medio_raw = "APPLE_PAY"

    fecha_param = final_payload.get("fecha") or final_payload.get("date")
    fecha_movimiento = parsear_fecha_para_db(fecha_param) if fecha_param else ahora_utc_db()

    def _filtrar_cuenta(query):
        if target_user_id:
            return query.filter((Cuenta.usuario_id == target_user_id) | (Cuenta.usuario_id == None))
        return query

    # 1. Rama Apple Pay
    if medio_raw == "APPLE_PAY":
        monto_raw = (
            final_payload.get("monto")
            or final_payload.get("amount")
            or final_payload.get("valor")
            or final_payload.get("precio")
            or final_payload.get("total")
            or 0.0
        )
        monto = limpiar_monto(monto_raw)

        comercio = str(
            final_payload.get("comercio")
            or final_payload.get("merchant")
            or final_payload.get("store")
            or final_payload.get("tienda")
            or final_payload.get("establecimiento")
            or final_payload.get("nombre")
            or "Comercio Apple Pay"
        ).strip()

        tarjeta_nombre = (
            final_payload.get("tarjeta")
            or final_payload.get("card")
            or final_payload.get("card_name")
            or final_payload.get("cardName")
            or final_payload.get("cuenta")
            or final_payload.get("account")
        )

        if monto <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El monto de la transacción de Apple Pay debe ser superior a 0 COP"
            )

        # Buscar cuenta asociada (o auto-crear si es nueva / fallback)
        STOPWORDS_TARJETA = {"visa", "mastercard", "tarjeta", "card", "credito", "crédito", "debito", "débito", "de", "the"}
        cuenta = None
        if tarjeta_nombre:
            tarjeta_clean = str(tarjeta_nombre).strip()
            # 1. Búsqueda directa (ej: cuenta="Bancolombia Principal", Apple Pay="Bancolombia")
            cuenta = _filtrar_cuenta(db.query(Cuenta).filter(Cuenta.nombre.ilike(f"%{tarjeta_clean}%"), Cuenta.activa == True)).first()
            
            # 2. Búsqueda inversa: el nombre de la cuenta está dentro del string de Apple Pay (ej: cuenta="Nu", Apple Pay="Nu Mastercard")
            if not cuenta:
                cuentas_activas = _filtrar_cuenta(db.query(Cuenta).filter(Cuenta.activa == True)).all()
                for c in cuentas_activas:
                    c_nom = c.nombre.strip().lower()
                    if c_nom not in STOPWORDS_TARJETA and len(c_nom) >= 3 and c_nom in tarjeta_clean.lower():
                        cuenta = c
                        break

            # 3. Búsqueda por palabras significativas descartando franquicias genéricas
            if not cuenta:
                palabras = [p for p in tarjeta_clean.split() if len(p) >= 3 and p.lower() not in STOPWORDS_TARJETA]
                for p in palabras:
                    c = _filtrar_cuenta(db.query(Cuenta).filter(Cuenta.nombre.ilike(f"%{p}%"), Cuenta.activa == True)).first()
                    if c:
                        cuenta = c
                        break

            # 4. Si la tarjeta enviada es genérica (ej: "Visa", "Mastercard", "Tarjeta de Crédito")
            # y el usuario ya tiene una tarjeta de crédito activa, asociarla directamente en vez de crear una duplicada
            if not cuenta:
                es_generica = all(p.lower() in STOPWORDS_TARJETA for p in tarjeta_clean.split())
                if es_generica:
                    cuenta = _filtrar_cuenta(db.query(Cuenta).filter(Cuenta.tipo == TipoCuenta.CREDITO, Cuenta.activa == True)).first()

            # 5. Si no existe ninguna coincidencia y no es puramente genérica, crear la tarjeta de crédito automáticamente (Zero-Setup)
            if not cuenta and tarjeta_clean:
                es_generica = all(p.lower() in STOPWORDS_TARJETA for p in tarjeta_clean.split())
                if not es_generica:
                    cuenta = Cuenta(
                        nombre=tarjeta_clean,
                        tipo=TipoCuenta.CREDITO,
                        saldo_actual=0.0,
                        cupo_total=0.0,
                        activa=True,
                        usuario_id=target_user_id
                    )
                    db.add(cuenta)
                    db.commit()
                    db.refresh(cuenta)

        # 6. Fallback final: Si no se especificó o no se encontró tarjeta, asociar a la tarjeta de crédito activa principal
        if not cuenta:
            cuenta = _filtrar_cuenta(db.query(Cuenta).filter(Cuenta.tipo == TipoCuenta.CREDITO, Cuenta.activa == True)).first()
            if not cuenta:
                cuenta = _filtrar_cuenta(db.query(Cuenta).filter(Cuenta.tipo.in_([TipoCuenta.DEBITO, TipoCuenta.ALTO_RENDIMIENTO, TipoCuenta.EFECTIVO]), Cuenta.activa == True)).first()
        
        if not cuenta:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No hay cuentas activas registradas para asociar el pago de Apple Pay"
            )

        # Idempotencia (se omite para pruebas manuales si test=True)
        es_prueba = bool(final_payload.get("test"))
        es_dry_run = bool(final_payload.get("dry_run") or final_payload.get("simular"))
        if es_dry_run:
            monto_pesos = f"{int(monto):,}".replace(",", ".") + " pesos"
            return WebhookIngestResponse(
                status="simulacion_exitosa",
                mensaje=f"Simulación de Apple Pay exitosa ({monto_pesos} en {comercio}). Cuenta vinculada: {cuenta.nombre}. Saldo intacto.",
                transaccion_id=-1,
                tipo_detectado="EGRESO",
                monto_cop=monto,
                comercio=comercio,
                cuenta_afectada=cuenta.nombre,
                es_transferencia_interna=False
            )
        fecha_clave = fecha_movimiento.strftime("%Y-%m-%d_%H:%M")
        hash_idemp = None if es_prueba else calcular_hash_idempotencia(monto, comercio, fecha_clave)
        if hash_idemp:
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

        # Descontar saldo o registrar deuda de tarjeta de crédito
        if cuenta.tipo == TipoCuenta.CREDITO:
            cuenta.saldo_actual += monto  # Deuda acumulada en la tarjeta
        else:
            cuenta.saldo_actual -= monto  # Débito de cuenta líquida

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
            raw_payload=str(final_payload),
            usuario_id=cuenta.usuario_id if (cuenta and cuenta.usuario_id) else target_user_id,
        )
        db.add(transaccion)
        db.commit()
        db.refresh(transaccion)

        monto_pesos = f"{int(monto):,}".replace(",", ".") + " pesos"
        return WebhookIngestResponse(
            status="exitoso",
            mensaje=f"Pago Apple Pay de {monto_pesos} registrado en {comercio}",
            transaccion_id=transaccion.id,
            tipo_detectado="EGRESO",
            monto_cop=monto,
            comercio=comercio,
            cuenta_afectada=cuenta.nombre,
            es_transferencia_interna=False
        )

    # 2. Rama SMS Bancario
    texto_sms = final_payload.get("texto_sms", final_payload.get("sms", final_payload.get("body", "")))
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
        cuenta_bancaria = _filtrar_cuenta(db.query(Cuenta).filter(Cuenta.tipo == TipoCuenta.DEBITO, Cuenta.activa == True)).first()
        billetera_efectivo = _filtrar_cuenta(db.query(Cuenta).filter(Cuenta.tipo == TipoCuenta.EFECTIVO, Cuenta.activa == True)).first()

        if not billetera_efectivo:
            billetera_efectivo = Cuenta(
                nombre="Billetera Efectivo",
                tipo=TipoCuenta.EFECTIVO,
                saldo_actual=0.0,
                usuario_id=target_user_id
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
            raw_payload=texto_sms,
            usuario_id=target_user_id,
        )
        db.add(transaccion)
        db.commit()
        db.refresh(transaccion)

        monto_pesos = f"{int(monto):,}".replace(",", ".") + " pesos"
        return WebhookIngestResponse(
            status="exitoso",
            mensaje=f"Retiro de {monto_pesos} transferido a Billetera Efectivo sin duplicar gasto",
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
        cuenta = _filtrar_cuenta(db.query(Cuenta).filter(Cuenta.tipo == tipo_filtro, Cuenta.activa == True)).first()
        if not cuenta:
            cuenta = _filtrar_cuenta(db.query(Cuenta).filter(Cuenta.tipo == TipoCuenta.DEBITO, Cuenta.activa == True)).first()

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
            raw_payload=texto_sms,
            usuario_id=target_user_id,
        )
        db.add(transaccion)
        db.commit()
        db.refresh(transaccion)

        monto_pesos = f"{int(monto):,}".replace(",", ".") + " pesos"
        return WebhookIngestResponse(
            status="exitoso",
            mensaje=f"Compra de {monto_pesos} en {comercio} registrada por SMS",
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
        raw_payload=texto_sms,
        usuario_id=cuenta_ingreso.usuario_id if (cuenta_ingreso and cuenta_ingreso.usuario_id) else payload.get("usuario_id"),
    )
    db.add(transaccion)
    db.commit()
    db.refresh(transaccion)

    monto_pesos = f"{int(monto):,}".replace(",", ".") + " pesos"
    return WebhookIngestResponse(
        status="exitoso",
        mensaje=f"Ingreso de {monto_pesos} registrado por SMS",
        transaccion_id=transaccion.id,
        tipo_detectado="INGRESO",
        monto_cop=monto,
        comercio=comercio,
        cuenta_afectada=cuenta_ingreso.nombre if cuenta_ingreso else "Cuenta Principal",
        es_transferencia_interna=False
    )


@router.api_route("/test-apple-pay", methods=["GET", "POST"], response_model=WebhookIngestResponse)
async def simular_prueba_apple_pay(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Endpoint de prueba y simulación inmediata para Apple Pay ($0 costo).
    Permite validar la conexión con AUREA desde Atajos de iOS, navegador o cURL sin realizar compras reales.
    Acepta parámetros opcionales por query string o JSON:
      ?monto=1000&comercio=Prueba+Datáfono&tarjeta=Visa&dry_run=true
    """
    params: Dict[str, Any] = dict(request.query_params)
    if request.method == "POST":
        try:
            body = await request.json()
            if isinstance(body, dict):
                params.update(body)
        except Exception:
            try:
                form = await request.form()
                params.update(dict(form))
            except Exception:
                pass

    monto_val = params.get("monto") or params.get("amount") or 1000.0
    comercio_val = params.get("comercio") or params.get("merchant") or "Prueba Datáfono Apple Pay"
    tarjeta_val = params.get("tarjeta") or params.get("card")
    dry_run_val = str(params.get("dry_run", "")).lower() in ("true", "1", "yes")

    payload_simulado = {
        "medio": "APPLE_PAY",
        "monto": monto_val,
        "comercio": comercio_val,
        "tarjeta": tarjeta_val,
        "test": True,
        "dry_run": dry_run_val,
    }

    return await procesar_atajo_ios(
        request=request,
        payload=payload_simulado,
        token=params.get("token"),
        authorization=request.headers.get("authorization"),
        x_aurea_token=request.headers.get("x-aurea-token"),
        db=db
    )

