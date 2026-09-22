from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models import Cuenta
from backend.app.schemas import CuentaCreate, CuentaUpdate, CuentaResponse

router = APIRouter()


@router.get("", response_model=List[CuentaResponse])
def listar_cuentas(db: Session = Depends(get_db)):
    """
    Lista todos los instrumentos financieros (Débito, Crédito, Alto Rendimiento, Efectivo).
    """
    return db.query(Cuenta).filter(Cuenta.activa == True).all()


@router.post("", response_model=CuentaResponse, status_code=status.HTTP_201_CREATED)
def crear_cuenta(cuenta_in: CuentaCreate, db: Session = Depends(get_db)):
    """
    Registra un nuevo instrumento financiero.
    """
    cuenta = Cuenta(**cuenta_in.model_dump())
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
    for field, value in update_data.items():
        setattr(cuenta, field, value)

    db.commit()
    db.refresh(cuenta)
    return cuenta


@router.delete("/{cuenta_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_cuenta(cuenta_id: int, db: Session = Depends(get_db)):
    """
    Elimina o desactiva una cuenta.
    """
    cuenta = db.query(Cuenta).filter(Cuenta.id == cuenta_id).first()
    if not cuenta:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cuenta no encontrada")
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
            nueva = Cuenta(**c_data.model_dump())
            db.add(nueva)
            resultados.append(nueva)
    db.commit()
    for r in resultados:
        db.refresh(r)
    return resultados
