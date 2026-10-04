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


def desanidar_y_normalizar_dict(obj: Any, nivel: int = 0) -> Dict[str, Any]:
    """
    Desanida recursivamente cualquier estructura enviada por Atajos de iOS,
    manejando claves anidadas (ej. {"Entrada de atajo": {...}}, {"transaccion": {...}}),
    cadenas con JSON serializado, o listas de diccionarios.
    Normaliza todas las claves eliminando mayúsculas, espacios y acentos.
    """
    if nivel > 6 or obj is None:
        return {}

    resultado: Dict[str, Any] = {}

    if isinstance(obj, str):
        s = obj.strip()
        if (s.startswith("{") and s.endswith("}")) or (s.startswith("[") and s.endswith("]")):
            try:
                import json
                return desanidar_y_normalizar_dict(json.loads(s), nivel + 1)
            except Exception:
                pass
        return {}

    if isinstance(obj, list):
        for item in obj:
            if isinstance(item, (dict, list, str)):
                sub = desanidar_y_normalizar_dict(item, nivel + 1)
                resultado.update(sub)
        return resultado

    if not isinstance(obj, dict):
        return {}

    for k, v in obj.items():
        if k is None:
            continue
        k_str = str(k).strip().lower()
        k_norm = (
            k_str.replace("á", "a")
            .replace("é", "e")
            .replace("í", "i")
            .replace("ó", "o")
            .replace("ú", "u")
            .replace("ñ", "n")
        )

        # Si el valor es a su vez un diccionario, lista o string JSON, desanidar recursivamente
        if isinstance(v, (dict, list)):
            sub = desanidar_y_normalizar_dict(v, nivel + 1)
            resultado.update(sub)
        elif isinstance(v, str) and ((v.strip().startswith("{") and v.strip().endswith("}")) or (v.strip().startswith("[") and v.strip().endswith("]"))):
            try:
                import json
                sub = desanidar_y_normalizar_dict(json.loads(v.strip()), nivel + 1)
                resultado.update(sub)
            except Exception:
                pass

        # Preservar el valor en el resultado si es significativo
        if v is not None and v != "":
            if k_norm not in resultado or resultado[k_norm] is None or resultado[k_norm] == "":
                resultado[k_norm] = v
            else:
                if isinstance(v, (int, float)) or (isinstance(v, str) and not v.startswith("{")):
                    resultado[k_norm] = v

    return resultado


def extraer_primer_valor(payload: Dict[str, Any], alias_list: list[str], default: Any = None) -> Any:
    """Busca el primer valor disponible en payload según la lista priorizada de alias."""
    for alias in alias_list:
        alias_clean = alias.strip().lower()
        alias_clean = (
            alias_clean.replace("á", "a")
            .replace("é", "e")
            .replace("í", "i")
            .replace("ó", "o")
            .replace("ú", "u")
            .replace("ñ", "n")
        )
        if alias_clean in payload:
            val = payload[alias_clean]
            if val is not None and str(val).strip() != "":
                return val
    return default


ALIAS_MONTO = [
    "monto", "amount", "valor", "precio", "total", "costo",
    "value", "price", "sum", "cantidad", "pago", "payment",
    "importe", "cobro", "charge"
]

ALIAS_COMERCIO = [
    "comercio", "merchant", "store", "tienda", "establecimiento",
    "nombre", "name", "vendor", "business", "lugar", "place",
    "destinatario", "recipient", "payee", "descripcion", "description",
    "titulo", "title", "concepto"
]

ALIAS_TARJETA = [
    "tarjeta", "card", "card_name", "cardname", "card_title",
    "cardtitle", "cuenta", "account", "banco", "bank",
    "metodo", "metodo_pago", "payment_method", "paymentmethod",
    "tarjeta_nombre", "tipo_tarjeta", "franquicia"
]

ALIAS_MEDIO = [
    "medio", "source", "channel", "tipo", "type", "medio_captura", "channel_name"
]

ALIAS_SMS = [
    "texto_sms", "textosms", "sms", "body", "mensaje", "message",
    "texto", "text", "cuerpo", "raw_sms", "sms_body"
]

ALIAS_TOKEN = [
    "token", "auth_token", "api_key", "key", "secret", "bearer", "biometric_token"
]

ALIAS_USUARIO = [
    "usuario", "user", "username", "usuario_id", "user_id"
]

ALIAS_FECHA = [
    "fecha", "date", "datetime", "time", "timestamp", "fecha_hora"
]

ALIAS_DRY_RUN = [
    "dry_run", "dryrun", "simular", "simulacion", "dry"
]

ALIAS_TEST = [
    "test", "prueba", "is_test"
]


@router.api_route("/ios-shortcut", methods=["GET", "POST"], response_model=WebhookIngestResponse)
async def procesar_atajo_ios(
    request: Request,
    payload: Optional[Any] = None,
    token: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None),
    x_aurea_token: Optional[str] = Header(None, alias="X-Aurea-Token"),
    db: Session = Depends(get_db)
):
    """
    Endpoint receptor para las Automatizaciones de Atajos de iOS (Apple Shortcuts).
    Procesa tanto pagos con Apple Pay como mensajes SMS de bancos colombianos con verificación opcional de token.
    Soporta POST (JSON, Form, Raw) y GET (Query params) para pruebas inmediatas sin costo.
    """
    # 1. Extraer fuentes crudas de datos
    raw_sources: list[Any] = []

    if payload and isinstance(payload, dict):
        raw_sources.append(payload)

    if request.method == "POST":
        try:
            parsed_json = await request.json()
            if parsed_json:
                raw_sources.append(parsed_json)
        except Exception:
            pass

        try:
            form = await request.form()
            if form:
                raw_sources.append(dict(form))
        except Exception:
            pass

        try:
            body_bytes = await request.body()
            if body_bytes:
                body_str = body_bytes.decode("utf-8", errors="ignore").strip()
                if body_str:
                    if (body_str.startswith("{") and body_str.endswith("}")) or (body_str.startswith("[") and body_str.endswith("]")):
                        import json
                        try:
                            raw_sources.append(json.loads(body_str))
                        except Exception:
                            pass
                    elif "=" in body_str:
                        import urllib.parse
                        try:
                            qs_dict = {k: v[0] if len(v) == 1 else v for k, v in urllib.parse.parse_qs(body_str).items()}
                            if qs_dict:
                                raw_sources.append(qs_dict)
                        except Exception:
                            pass
        except Exception:
            pass

    if request.query_params:
        raw_sources.append(dict(request.query_params))

    # 2. Desanidar recursivamente y normalizar claves (eliminar mayúsculas, espacios y acentos)
    final_payload: Dict[str, Any] = {}
    for src in raw_sources:
        aplanado = desanidar_y_normalizar_dict(src)
        for k, v in aplanado.items():
            if k not in final_payload or final_payload[k] is None or final_payload[k] == "":
                final_payload[k] = v
            elif v is not None and v != "":
                final_payload[k] = v

    # 3. Verificación de token criptográfico
    token_val = None
    if authorization and authorization.lower().startswith("bearer "):
        token_val = authorization[7:].strip()
    elif x_aurea_token:
        token_val = x_aurea_token.strip()
    elif token:
        token_val = token.strip()
    else:
        payload_token = extraer_primer_valor(final_payload, ALIAS_TOKEN)
        if payload_token:
            token_val = str(payload_token).strip()

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
            user_param = extraer_primer_valor(final_payload, ALIAS_USUARIO)
            if user_param:
                user_from_token = db.query(Usuario).filter(Usuario.username.ilike(str(user_param).strip())).first()
            if not user_from_token:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token de autorización requerido para ejecutar atajos de iOS en entorno multi-usuario."
                )

    payload_usuario_id = extraer_primer_valor(final_payload, ["usuario_id", "user_id"])
    if user_from_token and payload_usuario_id:
        try:
            if int(payload_usuario_id) != user_from_token.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No tienes permiso para ejecutar atajos para otro usuario."
                )
        except ValueError:
            pass

    target_user_id = user_from_token.id if user_from_token else payload_usuario_id

    # 4. Extracción de variables normalizadas mediante alias
    medio_raw = str(extraer_primer_valor(final_payload, ALIAS_MEDIO, "")).upper().strip()
    sms_texto = str(extraer_primer_valor(final_payload, ALIAS_SMS, "")).strip()
    monto_val = extraer_primer_valor(final_payload, ALIAS_MONTO)
    comercio_val = extraer_primer_valor(final_payload, ALIAS_COMERCIO)
    tarjeta_val = extraer_primer_valor(final_payload, ALIAS_TARJETA)

    # Identificación inequívoca de medio (APPLE_PAY vs SMS)
    es_apple_pay_explicito = any(x in medio_raw for x in ["APPLE", "PAY", "WALLET", "DATA"])
    es_sms_explicito = medio_raw in ["SMS", "TEXTO", "MENSAJE"]

    # Detectar si el texto contiene patrones de SMS bancarios de Colombia
    sms_lower = sms_texto.lower()
    es_sms_bancario = bool(sms_texto and any(b in sms_lower for b in [
        "le informa", "bancolombia le", "nequi:", "daviplata", "davivienda",
        "banco de bogota", "compra por", "retiro por", "transferencia recibida"
    ]))

    if es_apple_pay_explicito:
        medio_final = "APPLE_PAY"
    elif es_sms_explicito or es_sms_bancario:
        medio_final = "SMS"
    elif (monto_val is not None) or (comercio_val is not None) or (tarjeta_val is not None):
        # Si trae monto, comercio o tarjeta estructurados, SIEMPRE es Apple Pay
        medio_final = "APPLE_PAY"
    elif sms_texto:
        medio_final = "SMS"
    else:
        # Fallback predeterminado a Apple Pay
        medio_final = "APPLE_PAY"

    fecha_param = extraer_primer_valor(final_payload, ALIAS_FECHA)
    fecha_movimiento = parsear_fecha_para_db(fecha_param) if fecha_param else ahora_utc_db()

    def _filtrar_cuenta(query):
        if target_user_id:
            return query.filter((Cuenta.usuario_id == target_user_id) | (Cuenta.usuario_id == None))
        return query

    # 1. Rama Apple Pay (Receptor universal tolerante a cualquier tarjeta colombiana)
    if medio_final == "APPLE_PAY":
        monto_raw = monto_val if monto_val is not None else 0.0
        monto = abs(limpiar_monto(monto_raw))

        comercio = str(comercio_val or "Comercio Apple Pay").strip()
        tarjeta_nombre = str(tarjeta_val).strip() if tarjeta_val else None

        if monto <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El monto de la transacción de Apple Pay debe ser superior a 0 COP"
            )

        # Buscar cuenta asociada (Bancolombia, Nu, o auto-crear si es nueva / fallback)
        STOPWORDS_TARJETA = {
            "visa", "mastercard", "tarjeta", "card", "credito", "crédito",
            "debito", "débito", "de", "the", "cuenta", "ahorros", "corriente",
            "banco", "bank", "digital", "unica", "única", "principal"
        }
        cuenta = None
        if tarjeta_nombre:
            tarjeta_clean = str(tarjeta_nombre).strip()
            # 1. Búsqueda directa por coincidencia de subcadena (ej: cuenta="Bancolombia Única", Apple Pay="Bancolombia")
            cuenta = _filtrar_cuenta(db.query(Cuenta).filter(Cuenta.nombre.ilike(f"%{tarjeta_clean}%"), Cuenta.activa == True)).first()

            # 2. Búsqueda inversa: el nombre de la cuenta está dentro del string de Apple Pay (ej: cuenta="Nu", Apple Pay="Nu Mastercard")
            if not cuenta:
                cuentas_activas = _filtrar_cuenta(db.query(Cuenta).filter(Cuenta.activa == True)).all()
                for c in cuentas_activas:
                    c_nom = c.nombre.strip().lower()
                    if c_nom not in STOPWORDS_TARJETA and len(c_nom) >= 3 and c_nom in tarjeta_clean.lower():
                        cuenta = c
                        break

            # 3. Búsqueda cruzada por palabras significativas (ej. "Bancolombia" en "Mastercard Bancolombia" -> Bancolombia Única)
            if not cuenta:
                palabras_tarjeta = [p for p in tarjeta_clean.split() if len(p) >= 3 and p.lower() not in STOPWORDS_TARJETA]
                for p in palabras_tarjeta:
                    c = _filtrar_cuenta(db.query(Cuenta).filter(Cuenta.nombre.ilike(f"%{p}%"), Cuenta.activa == True)).first()
                    if c:
                        cuenta = c
                        break

            # 4. Búsqueda por palabras significativas de las cuentas existentes
            if not cuenta:
                cuentas_activas = _filtrar_cuenta(db.query(Cuenta).filter(Cuenta.activa == True)).all()
                for c in cuentas_activas:
                    palabras_c = [w for w in c.nombre.lower().split() if len(w) >= 3 and w not in STOPWORDS_TARJETA]
                    if any(w in tarjeta_clean.lower() for w in palabras_c):
                        cuenta = c
                        break

            # 5. Si la tarjeta enviada es genérica (ej: "Visa", "Mastercard", "Tarjeta de Crédito")
            # asociarla a la tarjeta de crédito activa o débito activa
            if not cuenta:
                es_generica = all(p.lower() in STOPWORDS_TARJETA for p in tarjeta_clean.split())
                if es_generica:
                    cuenta = _filtrar_cuenta(db.query(Cuenta).filter(Cuenta.tipo == TipoCuenta.CREDITO, Cuenta.activa == True)).first()
                    if not cuenta:
                        cuenta = _filtrar_cuenta(db.query(Cuenta).filter(Cuenta.tipo == TipoCuenta.DEBITO, Cuenta.activa == True)).first()

            # 6. Si no existe ninguna coincidencia y no es puramente genérica, auto-crear la tarjeta de crédito (Zero-Setup)
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

        # 7. Fallback final: Si no se especificó o no se encontró tarjeta, asociar a la tarjeta de crédito o cuenta principal
        if not cuenta:
            cuenta = _filtrar_cuenta(db.query(Cuenta).filter(Cuenta.tipo == TipoCuenta.CREDITO, Cuenta.activa == True)).first()
            if not cuenta:
                cuenta = _filtrar_cuenta(db.query(Cuenta).filter(Cuenta.tipo.in_([TipoCuenta.DEBITO, TipoCuenta.ALTO_RENDIMIENTO, TipoCuenta.EFECTIVO]), Cuenta.activa == True)).first()

        if not cuenta:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No hay cuentas activas registradas para asociar el pago de Apple Pay"
            )

        # Idempotencia y modo prueba/dry_run
        test_val = extraer_primer_valor(final_payload, ALIAS_TEST)
        es_prueba = bool(test_val)
        dry_run_val = extraer_primer_valor(final_payload, ALIAS_DRY_RUN)
        es_dry_run = str(dry_run_val).lower() in ("true", "1", "yes") if dry_run_val is not None else False
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
    texto_sms = str(extraer_primer_valor(final_payload, ALIAS_SMS, "")).strip()
    if not texto_sms:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Se requiere el campo 'texto_sms' para procesar la automatización SMS o 'monto' para Apple Pay."
        )

    remitente_val = extraer_primer_valor(final_payload, ["remitente", "sender", "from"])
    resultado_parser = SMSParser.parse_sms(texto_sms, remitente=remitente_val)
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

