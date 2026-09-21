import pytest
from tests.conftest import TestingSessionLocal
from backend.app.models import Cuenta, TipoCuenta, Transaccion, TipoTransaccion, MedioCaptura
from backend.app.services.nlp_expense_parser import NLPSmartExpenseParser


def test_extraer_montos_nlp():
    assert NLPSmartExpenseParser._extraer_monto("Pagué 15 mil de taxi") == 15000.0
    assert NLPSmartExpenseParser._extraer_monto("Almuerzo 25k") == 25000.0
    assert NLPSmartExpenseParser._extraer_monto("Compré $45.000 en el D1") == 45000.0
    assert NLPSmartExpenseParser._extraer_monto("Café 8500") == 8500.0


def test_interpretar_gasto_con_cuenta_efectivo():
    db = TestingSessionLocal()
    resultado = NLPSmartExpenseParser.interpretar_texto_gasto("Pagué 15 mil de taxi en efectivo", db)
    db.close()

    assert resultado["monto"] == 15000.0
    assert resultado["tipo"] == "EGRESO"
    assert resultado["cuenta_nombre"] == "Billetera Efectivo"
    assert resultado["requiere_confirmar_cuenta"] is False


def test_interpretar_gasto_sin_cuenta_requiere_confirmacion():
    db = TestingSessionLocal()
    resultado = NLPSmartExpenseParser.interpretar_texto_gasto("Café 8500", db)
    db.close()

    assert resultado["monto"] == 8500.0
    assert resultado["cuenta_id"] is None
    assert resultado["requiere_confirmar_cuenta"] is True


def test_api_ia_rapida_con_cuenta_detectada(client):
    res = client.post("/api/v1/transacciones/ia-rapida", json={"texto": "Pagué 15 mil de taxi en efectivo"})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "registrado"
    assert data["monto"] == 15000.0
    assert data["cuenta"] == "Billetera Efectivo"
    assert data["saldo_cuenta_actual"] == 35000.0  # 50.000 - 15.000


def test_api_ia_rapida_sin_cuenta_solicita_seleccion(client):
    res = client.post("/api/v1/transacciones/ia-rapida", json={"texto": "Compré mercado 45.000"})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "requiere_cuenta"
    assert data["monto"] == 45000.0
    assert "comercio" in data


def test_api_asignar_cuenta_a_transaccion(client):
    # Creamos primero una transacción asociada a Bancolombia
    db = TestingSessionLocal()
    banco = db.query(Cuenta).filter(Cuenta.tipo == TipoCuenta.DEBITO).first()
    tx = Transaccion(
        monto=20000.0,
        tipo=TipoTransaccion.EGRESO,
        medio=MedioCaptura.MANUAL,
        comercio="Farmacia",
        cuenta_origen_id=banco.id
    )
    banco.saldo_actual -= 20000.0
    db.add(tx)
    db.commit()
    tx_id = tx.id
    db.close()

    # Reasignar a Efectivo
    db = TestingSessionLocal()
    efectivo = db.query(Cuenta).filter(Cuenta.tipo == TipoCuenta.EFECTIVO).first()
    efectivo_id = efectivo.id
    db.close()

    res = client.patch(f"/api/v1/transacciones/{tx_id}/asignar-cuenta", json={"cuenta_id": efectivo_id})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "exitoso"

    # Verificar que el dinero se devolvió a Bancolombia y se descontó de Efectivo
    db = TestingSessionLocal()
    banco_upd = db.query(Cuenta).filter(Cuenta.tipo == TipoCuenta.DEBITO).first()
    efectivo_upd = db.query(Cuenta).filter(Cuenta.tipo == TipoCuenta.EFECTIVO).first()
    assert banco_upd.saldo_actual == 1000000.0
    assert efectivo_upd.saldo_actual == 30000.0  # 50.000 - 20.000
    db.close()
