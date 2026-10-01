from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status, Request
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models import Cuenta, Transaccion, TipoCuenta, TipoTransaccion, MedioCaptura
from backend.app.schemas import TransaccionCreate, TransaccionResponse, TransaccionUpdate
from backend.app.services.categorizer import CategorizadorComercios
from backend.app.services.nlp_expense_parser import NLPSmartExpenseParser
from backend.app.api.deps import get_current_user_id, check_auth_if_users_exist

router = APIRouter()


@router.get("", response_model=List[TransaccionResponse])
def listar_transacciones(
    tipo: Optional[TipoTransaccion] = None,
    medio: Optional[MedioCaptura] = None,
    cuenta_id: Optional[int] = None,
    limit: int = Query(50, ge=1, le=200),
    current_uid: Optional[int] = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Lista las transacciones históricas del usuario actual con filtros opcionales.
    """
    check_auth_if_users_exist(current_uid, db, "tus transacciones")
    query = db.query(Transaccion)
    if current_uid:
        query = query.filter((Transaccion.usuario_id == current_uid) | (Transaccion.usuario_id == None))
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
    current_uid: Optional[int] = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Registro manual de transacciones (especialmente útil para efectivo y ajustes rápidos).
    """
    check_auth_if_users_exist(current_uid, db, "registrar transacciones")
    cuenta_origen = db.query(Cuenta).filter(Cuenta.id == tx_in.cuenta_origen_id).first()
    if not cuenta_origen:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cuenta de origen no encontrada"
        )
    if current_uid is not None and cuenta_origen.usuario_id is not None and cuenta_origen.usuario_id != current_uid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para operar con esta cuenta de origen."
        )

    # Actualizar saldos según tipo
    if tx_in.tipo == TipoTransaccion.EGRESO:
        if cuenta_origen.tipo in (TipoCuenta.DEBITO, TipoCuenta.EFECTIVO, TipoCuenta.ALTO_RENDIMIENTO):
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
        if current_uid is not None and cuenta_destino.usuario_id is not None and cuenta_destino.usuario_id != current_uid:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para operar con esta cuenta de destino."
            )
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
        fecha=tx_in.fecha or datetime.now(timezone.utc),
        comercio=tx_in.comercio,
        descripcion=tx_in.descripcion,
        cuenta_origen_id=tx_in.cuenta_origen_id,
        cuenta_destino_id=tx_in.cuenta_destino_id,
        categoria_id=cat_id,
        cuotas_totales=tx_in.cuotas_totales,
        cuota_actual=tx_in.cuota_actual,
        es_gasto_hormiga=es_hormiga,
        usuario_id=current_uid
    )
    db.add(tx)
    db.commit()
    db.refresh(tx)
    return tx


@router.api_route("/ia-rapida", methods=["GET", "POST"])
async def registrar_gasto_ia_rapida(
    request: Request,
    texto: Optional[str] = Query(None),
    cuenta_id: Optional[int] = Query(None),
    tipo: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Interpreta un comando por voz o texto con Apple Intelligence / NLP
    (ej: 'Pagué 15 mil de taxi en efectivo', 'Almuerzo 22000 con Bancolombia')
    y registra el movimiento o solicita confirmar cuenta si es ambiguo.
    Soporta POST JSON y GET con query parameter en la URL (?texto=...).
    Permite forzar tipo='INGRESO' o 'EGRESO' desde atajos dedicados.
    """
    texto_final = texto
    cuenta_id_final = cuenta_id
    tipo_final = tipo
    token_val = None

    if request.method == "POST":
        # 1. Intentar JSON
        try:
            body = await request.json()
            if isinstance(body, dict):
                if not texto_final:
                    texto_final = body.get("texto")
                if not cuenta_id_final and body.get("cuenta_id"):
                    cuenta_id_final = int(body.get("cuenta_id"))
                if not tipo_final and body.get("tipo"):
                    tipo_final = str(body.get("tipo"))
                if body.get("token"):
                    token_val = str(body.get("token")).strip()
        except Exception:
            pass

        # 2. Intentar Formulario (Form en Atajos iOS)
        if not texto_final or not token_val:
            try:
                form = await request.form()
                if not texto_final and form.get("texto"):
                    texto_final = str(form.get("texto"))
                if not cuenta_id_final and form.get("cuenta_id"):
                    cuenta_id_final = int(form.get("cuenta_id"))
                if not tipo_final and form.get("tipo"):
                    tipo_final = str(form.get("tipo"))
                if not token_val and form.get("token"):
                    token_val = str(form.get("token")).strip()
            except Exception:
                pass

        # 3. Intentar Texto Plano Directo en el Body
        if not texto_final:
            try:
                raw_bytes = await request.body()
                raw_str = raw_bytes.decode("utf-8").strip()
                if raw_str and not raw_str.startswith("{") and "=" not in raw_str:
                    texto_final = raw_str
            except Exception:
                pass

    texto_final = str(texto_final or "").strip()
    if not texto_final:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El campo 'texto' es requerido")

    # Autenticación segura mediante Bearer token, X-Aurea-Token o query param token
    auth_header = request.headers.get("Authorization")
    aurea_header = request.headers.get("X-Aurea-Token")
    token_param = request.query_params.get("token")

    if auth_header and auth_header.lower().startswith("bearer "):
        token_val = auth_header[7:].strip()
    elif aurea_header:
        token_val = aurea_header.strip()
    elif token_param:
        token_val = token_param.strip()

    current_uid = None
    if token_val:
        from backend.app.models import Usuario
        user = db.query(Usuario).filter(Usuario.biometric_token == token_val).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token de autorización inválido o expirado."
            )
        current_uid = user.id

    check_auth_if_users_exist(current_uid, db, "registrar transacciones con IA")

    interpretacion = NLPSmartExpenseParser.interpretar_texto_gasto(texto_final, db, usuario_id=current_uid)
    monto = interpretacion["monto"]
    comercio = interpretacion["comercio"]
    
    # Si el atajo forzó tipo explícito (ej. atajo de Registrar Ingreso)
    if tipo_final and tipo_final.upper() in ["INGRESO", "EGRESO"]:
        tipo = tipo_final.upper()
        if tipo == "INGRESO" and comercio == "Gasto General":
            comercio = "Ingreso General"
    else:
        tipo = interpretacion["tipo"]

    # En Colombia ningún ingreso es menor a $1.000 COP (< 1000 COP siempre son miles, ej. 500 -> 500.000 COP)
    if tipo == "INGRESO" and 0 < monto < 1000:
        monto *= 1000.0

    cuenta_detectada_id = cuenta_id_final or interpretacion["cuenta_id"]

    if monto <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se detectó un monto válido en el mensaje")

    if cuenta_detectada_id:
        cuenta = db.query(Cuenta).filter(Cuenta.id == cuenta_detectada_id).first()
        if cuenta:
            if current_uid is not None and cuenta.usuario_id is not None and cuenta.usuario_id != current_uid:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No tienes permiso para operar con esta cuenta."
                )
            interpretacion["cuenta_nombre"] = cuenta.nombre
    else:
        cuenta = None

    monto_texto = f"{int(monto):,}".replace(",", ".") + " pesos"

    # Si no se detectó cuenta, preguntar al usuario
    if not cuenta_detectada_id:
        pregunta = "¿A qué cuenta ingresó el dinero?" if tipo == "INGRESO" else "¿De qué cuenta lo pagaste?"
        texto_tipo = "un ingreso" if tipo == "INGRESO" else "un gasto"
        return {
            "status": "requiere_cuenta",
            "mensaje": f"Se detectó {texto_tipo} de {monto_texto} en '{comercio}'. {pregunta}",
            "monto": monto,
            "comercio": comercio,
            "tipo": tipo,
            "categoria_id": interpretacion["categoria_id"],
            "categoria_nombre": interpretacion["categoria_nombre"]
        }

    cuenta = db.query(Cuenta).filter(Cuenta.id == cuenta_detectada_id).first()
    if not cuenta:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cuenta no encontrada")
    if current_uid is not None and cuenta.usuario_id is not None and cuenta.usuario_id != current_uid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para operar con esta cuenta."
        )

    if tipo == "EGRESO":
        if cuenta.tipo in [TipoCuenta.DEBITO, TipoCuenta.EFECTIVO, TipoCuenta.ALTO_RENDIMIENTO]:
            cuenta.saldo_actual -= monto
        elif cuenta.tipo == TipoCuenta.CREDITO:
            cuenta.saldo_actual += monto
    else:
        cuenta.saldo_actual += monto

    es_hormiga = CategorizadorComercios.es_gasto_hormiga(monto)

    tx = Transaccion(
        monto=monto,
        tipo=TipoTransaccion[tipo],
        medio=MedioCaptura.MANUAL,
        fecha=datetime.now(timezone.utc),
        comercio=comercio,
        descripcion=f"Registrado con voz / NLP: '{texto_final}'",
        cuenta_origen_id=cuenta.id,
        categoria_id=interpretacion["categoria_id"],
        es_gasto_hormiga=es_hormiga,
        raw_payload=texto_final,
        usuario_id=cuenta.usuario_id if (cuenta and cuenta.usuario_id) else current_uid
    )
    db.add(tx)
    db.commit()
    db.refresh(tx)

    return {
        "status": "registrado",
        "mensaje": f"¡Listo! Registrado {tipo.lower()} de {monto_texto} en '{comercio}' con {cuenta.nombre}.",
        "transaccion_id": tx.id,
        "monto": monto,
        "comercio": comercio,
        "cuenta": cuenta.nombre,
        "saldo_cuenta_actual": cuenta.saldo_actual
    }


@router.patch("/{transaccion_id}/asignar-cuenta")
def reasignar_cuenta_transaccion(
    transaccion_id: int,
    payload: dict,
    current_uid: Optional[int] = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Permite asignar o cambiar la cuenta de un gasto cuando el sistema preguntó de dónde fue.
    """
    check_auth_if_users_exist(current_uid, db, "esta transacción")
    tx = db.query(Transaccion).filter(Transaccion.id == transaccion_id).first()
    if not tx:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transacción no encontrada")
    if current_uid is not None and tx.usuario_id is not None and tx.usuario_id != current_uid:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permiso para modificar esta transacción.")

    nueva_cuenta_id = payload.get("cuenta_id")
    nueva_cuenta = db.query(Cuenta).filter(Cuenta.id == nueva_cuenta_id).first()
    if not nueva_cuenta:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cuenta no encontrada")
    if current_uid is not None and nueva_cuenta.usuario_id is not None and nueva_cuenta.usuario_id != current_uid:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permiso para asignar a esta cuenta.")

    # Revertir saldo anterior si aplica
    antigua_cuenta = tx.cuenta_origen
    if antigua_cuenta and antigua_cuenta.id != nueva_cuenta.id:
        if tx.tipo == TipoTransaccion.EGRESO:
            if antigua_cuenta.tipo in [TipoCuenta.DEBITO, TipoCuenta.EFECTIVO, TipoCuenta.ALTO_RENDIMIENTO]:
                antigua_cuenta.saldo_actual += tx.monto
            elif antigua_cuenta.tipo == TipoCuenta.CREDITO:
                antigua_cuenta.saldo_actual -= tx.monto

            if nueva_cuenta.tipo in [TipoCuenta.DEBITO, TipoCuenta.EFECTIVO, TipoCuenta.ALTO_RENDIMIENTO]:
                nueva_cuenta.saldo_actual -= tx.monto
            elif nueva_cuenta.tipo == TipoCuenta.CREDITO:
                nueva_cuenta.saldo_actual += tx.monto

    tx.cuenta_origen_id = nueva_cuenta.id
    db.commit()
    db.refresh(tx)
    return {"status": "exitoso", "mensaje": f"Gasto asignado correctamente a {nueva_cuenta.nombre}"}


def _aplicar_efecto_saldo(cuenta: Cuenta, tipo_tx: TipoTransaccion, monto: float, aplicar: bool):
    """
    Aplica o revierte el impacto financiero de una transacción sobre una cuenta.
    aplicar=True: la transacción ocurre.
    aplicar=False: la transacción se cancela/revierte.
    """
    if tipo_tx == TipoTransaccion.EGRESO:
        if cuenta.tipo == TipoCuenta.CREDITO:
            cuenta.saldo_actual += monto if aplicar else -monto
        else:
            cuenta.saldo_actual += -monto if aplicar else monto
    elif tipo_tx == TipoTransaccion.INGRESO:
        cuenta.saldo_actual += monto if aplicar else -monto


@router.get("/{transaccion_id}", response_model=TransaccionResponse)
def obtener_detalle_transaccion(
    transaccion_id: int,
    current_uid: Optional[int] = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Obtiene los detalles completos de una transacción específica.
    """
    check_auth_if_users_exist(current_uid, db, "esta transacción")
    tx = db.query(Transaccion).filter(Transaccion.id == transaccion_id).first()
    if not tx:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transacción no encontrada")
    if current_uid is not None and tx.usuario_id is not None and tx.usuario_id != current_uid:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permiso para acceder a esta transacción.")
    return tx


@router.put("/{transaccion_id}", response_model=TransaccionResponse)
def actualizar_transaccion(
    transaccion_id: int,
    tx_in: TransaccionUpdate,
    current_uid: Optional[int] = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Actualiza el comercio, monto, tipo, cuenta o categoría de una transacción, reajustando saldos automáticamente.
    """
    check_auth_if_users_exist(current_uid, db, "modificar esta transacción")
    tx = db.query(Transaccion).filter(Transaccion.id == transaccion_id).first()
    if not tx:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transacción no encontrada")
    if current_uid is not None and tx.usuario_id is not None and tx.usuario_id != current_uid:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permiso para modificar esta transacción.")

    cuenta_anterior = tx.cuenta_origen
    cuenta_nueva = cuenta_anterior
    if tx_in.cuenta_origen_id and tx_in.cuenta_origen_id != tx.cuenta_origen_id:
        cuenta_nueva = db.query(Cuenta).filter(Cuenta.id == tx_in.cuenta_origen_id).first()
        if not cuenta_nueva:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nueva cuenta no encontrada")
        if current_uid is not None and cuenta_nueva.usuario_id is not None and cuenta_nueva.usuario_id != current_uid:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permiso para operar con esta cuenta.")

    # 1. Revertir saldo anterior
    if cuenta_anterior:
        _aplicar_efecto_saldo(cuenta_anterior, tx.tipo, tx.monto, aplicar=False)

    # 2. Aplicar nuevos valores
    nuevo_monto = tx_in.monto if tx_in.monto is not None else tx.monto
    nuevo_tipo = tx_in.tipo if tx_in.tipo is not None else tx.tipo

    if tx_in.comercio is not None:
        tx.comercio = tx_in.comercio.strip()
    if tx_in.descripcion is not None:
        tx.descripcion = tx_in.descripcion.strip()
    if tx_in.categoria_id is not None:
        tx.categoria_id = tx_in.categoria_id
    if tx_in.cuotas_totales is not None:
        tx.cuotas_totales = tx_in.cuotas_totales
    if tx_in.cuota_actual is not None:
        tx.cuota_actual = tx_in.cuota_actual

    tx.monto = nuevo_monto
    tx.tipo = nuevo_tipo
    tx.cuenta_origen_id = cuenta_nueva.id
    tx.es_gasto_hormiga = CategorizadorComercios.es_gasto_hormiga(nuevo_monto)

    # 3. Aplicar nuevo saldo
    _aplicar_efecto_saldo(cuenta_nueva, nuevo_tipo, nuevo_monto, aplicar=True)

    db.commit()
    db.refresh(tx)
    return tx


@router.delete("/{transaccion_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_transaccion(
    transaccion_id: int,
    current_uid: Optional[int] = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Elimina una transacción y revierte su impacto financiero en la cuenta o tarjeta de origen.
    """
    check_auth_if_users_exist(current_uid, db, "eliminar esta transacción")
    tx = db.query(Transaccion).filter(Transaccion.id == transaccion_id).first()
    if not tx:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transacción no encontrada")
    if current_uid is not None and tx.usuario_id is not None and tx.usuario_id != current_uid:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permiso para eliminar esta transacción.")

    if tx.cuenta_origen:
        _aplicar_efecto_saldo(tx.cuenta_origen, tx.tipo, tx.monto, aplicar=False)

    db.delete(tx)
    db.commit()
    return None

