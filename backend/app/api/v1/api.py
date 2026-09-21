from fastapi import APIRouter
from backend.app.api.v1.endpoints import (
    webhooks,
    cuentas,
    transacciones,
    metricas,
    metas,
)

api_router = APIRouter()
api_router.include_router(webhooks.router, prefix="/webhooks", tags=["Webhooks Atajos iOS"])
api_router.include_router(cuentas.router, prefix="/cuentas", tags=["Cuentas e Instrumentos"])
api_router.include_router(transacciones.router, prefix="/transacciones", tags=["Transacciones"])
api_router.include_router(metricas.router, prefix="/metricas", tags=["Métricas y Semáforo"])
api_router.include_router(metas.router, prefix="/metas", tags=["Metas de Ahorro"])
