from datetime import datetime, timezone, timedelta
import pytest
from backend.app.timezone import (
    COLOMBIA_TZ,
    ahora_colombia,
    to_colombia_tz,
    formatear_fecha_iso_colombia,
    parsear_fecha_colombia,
)
from backend.app.models import Transaccion, TipoTransaccion, MedioCaptura
from backend.app.services.financial_engine import FinancialEngine


def test_colombia_tz_offset():
    """Valida que la zona horaria oficial de Colombia sea UTC-5 de forma permanente."""
    now_col = ahora_colombia()
    assert now_col.tzinfo is not None
    assert now_col.utcoffset() == timedelta(hours=-5)

    # Verificar que el desfase con UTC sea exactamente 5 horas
    now_utc = datetime.now(timezone.utc)
    # Al convertir now_utc a hora colombiana, la diferencia en horas de reloj debe ser -5
    diff_hours = (now_utc.astimezone(COLOMBIA_TZ).hour - now_utc.hour) % 24
    assert diff_hours == 19  # (24 - 5) = 19 mod 24


def test_to_colombia_tz_conversions():
    """Valida la conversión de datetimes naive y timezone-aware a Colombia."""
    # 1. None
    assert to_colombia_tz(None) is None

    # 2. Naive (asume Colombia)
    dt_naive = datetime(2026, 9, 30, 21, 45, 0)
    col_dt = to_colombia_tz(dt_naive)
    assert col_dt.tzinfo == COLOMBIA_TZ
    assert col_dt.hour == 21
    assert col_dt.day == 30

    # 3. UTC aware (ej: 2:45 AM del 1 de octubre UTC -> 9:45 PM del 30 de septiembre en Colombia)
    dt_utc = datetime(2026, 10, 1, 2, 45, 0, tzinfo=timezone.utc)
    col_from_utc = to_colombia_tz(dt_utc)
    assert col_from_utc.year == 2026
    assert col_from_utc.month == 9
    assert col_from_utc.day == 30
    assert col_from_utc.hour == 21
    assert col_from_utc.minute == 45
    assert col_from_utc.utcoffset() == timedelta(hours=-5)


def test_formatear_fecha_iso_colombia():
    """Valida que el string ISO contenga el offset explícito -05:00."""
    dt = datetime(2026, 9, 30, 21, 30, 0)
    iso_str = formatear_fecha_iso_colombia(dt)
    assert iso_str == "2026-09-30T21:30:00-05:00"
    assert iso_str.endswith("-05:00")


def test_parsear_fecha_colombia():
    """Valida el parsing de fechas en diferentes formatos hacia UTC-5."""
    parsed_iso = parsear_fecha_colombia("2026-09-30T21:30:00-05:00")
    assert parsed_iso.hour == 21
    assert parsed_iso.utcoffset() == timedelta(hours=-5)

    # Parsing de UTC string
    parsed_utc_str = parsear_fecha_colombia("2026-10-01T02:30:00Z")
    assert parsed_utc_str.day == 30
    assert parsed_utc_str.hour == 21
    assert parsed_utc_str.utcoffset() == timedelta(hours=-5)


from tests.conftest import TestingSessionLocal


def test_transaccion_ia_rapida_guarda_fecha_colombia(client):
    """Valida que una transacción registrada por voz / NLP tenga fecha en hora colombiana."""
    res = client.post("/api/v1/transacciones/ia-rapida", json={"texto": "Pagué café 8500 en efectivo"})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "registrado"
    assert "fecha" in data
    assert "-05:00" in data["fecha"]

    # Verificar en la base de datos
    tx_id = data["transaccion_id"]
    res_get = client.get(f"/api/v1/transacciones/{tx_id}")
    assert res_get.status_code == 200
    tx_data = res_get.json()
    assert "-05:00" in tx_data["fecha"]


def test_dashboard_muestra_fechas_colombia(client):
    """Valida que el consolidado del dashboard retorne fechas con offset colombiano."""
    client.post("/api/v1/transacciones/ia-rapida", json={"texto": "Pagué cena 45000 en Bancolombia Principal"})
    res_dash = client.get("/api/v1/metricas/dashboard")
    assert res_dash.status_code == 200
    dash_data = res_dash.json()
    assert len(dash_data["transacciones"]) > 0
    primera_tx = dash_data["transacciones"][0]
    assert "-05:00" in primera_tx["fecha"]


def test_financial_engine_corte_medianoche_colombia():
    """
    Verifica que transacciones hechas en la noche (ej: 9:30 PM en Colombia)
    no se computen para el día siguiente como ocurriría con un servidor en UTC.
    """
    from backend.app.models import Cuenta, TipoCuenta, PerfilFinanciero

    db_session = TestingSessionLocal()
    try:
        perfil = PerfilFinanciero(
            dia_pago_mensual=1,
            ingreso_mensual_estimado=3000000.0,
            compromisos_fijos_mensual=1000000.0,
            porcentaje_ahorro_meta=10.0,
            umbral_gasto_hormiga=25000.0
        )
        cuenta = Cuenta(nombre="Bancolombia Test", tipo=TipoCuenta.DEBITO, saldo_actual=2000000.0)
        db_session.add_all([perfil, cuenta])
        db_session.commit()

        # Transacción a las 9:30 PM del 30 de septiembre en Colombia
        # (en UTC sería 2:30 AM del 1 de octubre)
        tx_noche = Transaccion(
            monto=50000.0,
            tipo=TipoTransaccion.EGRESO,
            medio=MedioCaptura.MANUAL,
            fecha=datetime(2026, 9, 30, 21, 30, 0),
            comercio="Restaurante Noche",
            cuenta_origen_id=cuenta.id
        )
        db_session.add(tx_noche)
        db_session.commit()

        # Si evaluamos el semáforo para el 30 de septiembre a las 10:00 PM:
        fecha_ref_colombia = datetime(2026, 9, 30, 22, 0, 0, tzinfo=COLOMBIA_TZ)
        res_30 = FinancialEngine.calcular_semaforo_mensual(db_session, fecha_referencia=fecha_ref_colombia)
        assert res_30["gasto_hoy"] == 50000.0

        # Si evaluamos el semáforo para el 1 de octubre a las 8:00 AM:
        fecha_ref_1_oct = datetime(2026, 10, 1, 8, 0, 0, tzinfo=COLOMBIA_TZ)
        res_1_oct = FinancialEngine.calcular_semaforo_mensual(db_session, fecha_referencia=fecha_ref_1_oct)
        # En el 1 de octubre, el gasto de hoy debe ser 0.0, no 50000.0
        assert res_1_oct["gasto_hoy"] == 0.0
    finally:
        db_session.close()
