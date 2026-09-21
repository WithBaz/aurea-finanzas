import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.database import Base
from backend.app.models import (
    Cuenta,
    PerfilFinanciero,
    Transaccion,
    TipoCuenta,
    TipoTransaccion,
    MedioCaptura,
)
from backend.app.services.financial_engine import FinancialEngine
from backend.app.services.categorizer import CategorizadorComercios


@pytest.fixture
def db_session():
    test_engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=test_engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_categorizador_comercios_colombianos():
    cat, _ = CategorizadorComercios.sugerir_categoria("Tiendas D1 Calle 100")
    assert cat == "Alimentación y Supermercado"

    cat, _ = CategorizadorComercios.sugerir_categoria("Estación Terpel Autonorte")
    assert cat == "Transporte y Movilidad"

    cat, _ = CategorizadorComercios.sugerir_categoria("Suscripción Spotify mensual")
    assert cat == "Ocio y Suscripciones"

    cat, _ = CategorizadorComercios.sugerir_categoria("Farmatodo Pepe Sierra")
    assert cat == "Salud y Cuidado Personal"


def test_es_gasto_hormiga():
    assert CategorizadorComercios.es_gasto_hormiga(12000.0) is True
    assert CategorizadorComercios.es_gasto_hormiga(25000.0) is True
    assert CategorizadorComercios.es_gasto_hormiga(25001.0) is False
    assert CategorizadorComercios.es_gasto_hormiga(150000.0) is False


def test_calculo_rendimientos_diarios_nu(db_session):
    cuenta_nu = Cuenta(
        nombre="Nu Colombia Cajita",
        tipo=TipoCuenta.ALTO_RENDIMIENTO,
        saldo_actual=10000000.0, # 10 Millones COP
        tasa_ea=12.5,             # 12.5% E.A.
        activa=True
    )
    db_session.add(cuenta_nu)
    db_session.commit()

    rendimientos = FinancialEngine.calcular_rendimientos_diarios(db_session)
    assert len(rendimientos) == 1
    r = rendimientos[0]
    assert r["cuenta_nombre"] == "Nu Colombia Cajita"
    # Interés diario aproximado de 10 millones al 12.5% E.A. es ~ $3.227 COP diarios
    assert 3000.0 < r["rendimiento_diario_estimado"] < 3500.0
    # Interés mensual aproximado es ~ $98.000 COP
    assert 90000.0 < r["rendimiento_mensual_proyectado"] < 110000.0


def test_semaforo_mensual_verde(db_session):
    perfil = PerfilFinanciero(
        dia_pago_mensual=30,
        ingreso_mensual_estimado=4000000.0,
        compromisos_fijos_mensual=1500000.0,
        porcentaje_ahorro_meta=10.0,
        umbral_gasto_hormiga=25000.0
    )
    cuenta = Cuenta(
        nombre="Bancolombia",
        tipo=TipoCuenta.DEBITO,
        saldo_actual=2000000.0
    )
    db_session.add_all([perfil, cuenta])
    db_session.commit()

    res = FinancialEngine.calcular_semaforo_mensual(db_session)
    assert res["color"] in ["VERDE", "AMARILLO", "ROJO"]
    assert res["presupuesto_disponible_total"] > 0
    assert res["limite_gasto_diario_sugerido"] > 0
