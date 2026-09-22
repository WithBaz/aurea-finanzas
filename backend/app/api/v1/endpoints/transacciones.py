from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status, Request
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models import Cuenta, Transaccion, TipoCuenta, TipoTransaccion, MedioCaptura
from backend.app.schemas import TransaccionCreate, TransaccionResponse
from backend.app.services.categorizer import CategorizadorComercios
from backend.app.services.nlp_expense_parser import NLPSmartExpenseParser

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
        fecha=tx_in.fecha or datetime.now(timezone.utc),
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


@router.api_route("/ia-rapida", methods=["GET", "POST"])
async def registrar_gasto_ia_rapida(
    request: Request,
    texto: Optional[str] = Query(None),
    cuenta_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Interpreta un comando por voz o texto con Apple Intelligence / NLP
    (ej: 'Pagué 15 mil de taxi en efectivo', 'Almuerzo 22000 con Bancolombia')
    y registra el movimiento o solicita confirmar cuenta si es ambiguo.
    Soporta POST JSON y GET con query parameter en la URL (?texto=...).
    """
    texto_final = texto
    cuenta_id_final = cuenta_id

    if request.method == "POST":
        # 1. Intentar JSON
        try:
            body = await request.json()
            if isinstance(body, dict):
                if not texto_final:
                    texto_final = body.get("texto")
                if not cuenta_id_final and body.get("cuenta_id"):
                    cuenta_id_final = int(body.get("cuenta_id"))
        except Exception:
            pass

        # 2. Intentar Formulario (Form en Atajos iOS)
        if not texto_final:
            try:
                form = await request.form()
                if form.get("texto"):
                    texto_final = str(form.get("texto"))
                if not cuenta_id_final and form.get("cuenta_id"):
                    cuenta_id_final = int(form.get("cuenta_id"))
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

    interpretacion = NLPSmartExpenseParser.interpretar_texto_gasto(texto_final, db)
    monto = interpretacion["monto"]
    comercio = interpretacion["comercio"]
    tipo = interpretacion["tipo"]
    cuenta_detectada_id = cuenta_id_final or interpretacion["cuenta_id"]

    if monto <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se detectó un monto válido en el mensaje")

    if cuenta_detectada_id:
        cuenta = db.query(Cuenta).filter(Cuenta.id == cuenta_detectada_id).first()
        if cuenta:
            interpretacion["cuenta_nombre"] = cuenta.nombre
    else:
        cuenta = None

    # Si no se detectó cuenta, preguntar al usuario
    if not cuenta_detectada_id:
        return {
            "status": "requiere_cuenta",
            "mensaje": f"Se detectó un gasto de ${monto:,.0f} COP en '{comercio}'. ¿De qué cuenta lo pagaste?",
            "monto": monto,
            "comercio": comercio,
            "tipo": tipo,
            "categoria_id": interpretacion["categoria_id"],
            "categoria_nombre": interpretacion["categoria_nombre"]
        }

    cuenta = db.query(Cuenta).filter(Cuenta.id == cuenta_detectada_id).first()
    if not cuenta:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cuenta no encontrada")

    if tipo == "EGRESO":
        if cuenta.tipo in [TipoCuenta.DEBITO, TipoCuenta.EFECTIVO]:
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
        descripcion=f"Registrado con Apple Intelligence: '{texto}'",
        cuenta_origen_id=cuenta.id,
        categoria_id=interpretacion["categoria_id"],
        es_gasto_hormiga=es_hormiga,
        raw_payload=texto
    )
    db.add(tx)
    db.commit()
    db.refresh(tx)

    return {
        "status": "registrado",
        "mensaje": f"¡Listo! Registrado {tipo.lower()} de ${monto:,.0f} COP en '{comercio}' con {cuenta.nombre}.",
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
    db: Session = Depends(get_db)
):
    """
    Permite asignar o cambiar la cuenta de un gasto cuando el sistema preguntó de dónde fue.
    """
    tx = db.query(Transaccion).filter(Transaccion.id == transaccion_id).first()
    if not tx:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transacción no encontrada")

    nueva_cuenta_id = payload.get("cuenta_id")
    nueva_cuenta = db.query(Cuenta).filter(Cuenta.id == nueva_cuenta_id).first()
    if not nueva_cuenta:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cuenta no encontrada")

    # Revertir saldo anterior si aplica
    antigua_cuenta = tx.cuenta_origen
    if antigua_cuenta and antigua_cuenta.id != nueva_cuenta.id:
        if tx.tipo == TipoTransaccion.EGRESO:
            if antigua_cuenta.tipo in [TipoCuenta.DEBITO, TipoCuenta.EFECTIVO]:
                antigua_cuenta.saldo_actual += tx.monto
            elif antigua_cuenta.tipo == TipoCuenta.CREDITO:
                antigua_cuenta.saldo_actual -= tx.monto

            if nueva_cuenta.tipo in [TipoCuenta.DEBITO, TipoCuenta.EFECTIVO]:
                nueva_cuenta.saldo_actual -= tx.monto
            elif nueva_cuenta.tipo == TipoCuenta.CREDITO:
                nueva_cuenta.saldo_actual += tx.monto

    tx.cuenta_origen_id = nueva_cuenta.id
    db.commit()
    db.refresh(tx)
    return {"status": "exitoso", "mensaje": f"Gasto asignado correctamente a {nueva_cuenta.nombre}"}
