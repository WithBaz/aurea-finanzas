from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models import Cuenta
from backend.app.schemas import CuentaCreate, CuentaResponse

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
