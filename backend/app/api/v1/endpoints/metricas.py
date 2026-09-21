from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.schemas import SemaforoResponse, RendimientoDiarioResponse
from backend.app.services.financial_engine import FinancialEngine

router = APIRouter()


@router.get("/semaforo", response_model=SemaforoResponse)
def obtener_semaforo_mensual(db: Session = Depends(get_db)):
    """
    Calcula el estado del semáforo diario basado en el presupuesto mensual del usuario en COP.
    """
    return FinancialEngine.calcular_semaforo_mensual(db)


@router.get("/rendimientos", response_model=List[RendimientoDiarioResponse])
def obtener_rendimientos_diarios(db: Session = Depends(get_db)):
    """
    Calcula los rendimientos generados hoy por cuentas remuneradas (Nu Colombia, Lulo, Pibank).
    """
    return FinancialEngine.calcular_rendimientos_diarios(db)
