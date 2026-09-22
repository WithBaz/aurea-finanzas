import pytest
from tests.conftest import TestingSessionLocal
from backend.app.models import Cuenta, TipoCuenta, TipoTransaccion, PerfilFinanciero


def test_listar_cuentas_api(client):
    response = client.get("/api/v1/cuentas")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 3
    nombres = [c["nombre"] for c in data]
    assert "Bancolombia Principal" in nombres


def test_webhook_apple_pay(client):
    payload = {
        "medio": "APPLE_PAY",
        "monto": 35000.0,
        "comercio": "Starbucks Gran Estacion",
        "tarjeta": "Bancolombia"
    }
    response = client.post("/api/v1/webhooks/ios-shortcut", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "exitoso"
    assert data["monto_cop"] == 35000.0
    assert data["comercio"] == "Starbucks Gran Estacion"
    assert data["tipo_detectado"] == "EGRESO"

    # Verificar que el saldo de la cuenta de débito se descontó
    c_res = client.get("/api/v1/cuentas")
    banco = next(c for c in c_res.json() if c["nombre"] == "Bancolombia Principal")
    assert banco["saldo_actual"] == 1000000.0 - 35000.0


def test_webhook_sms_retiro_cajero_transferencia_interna(client):
    sms = "Bancolombia le informa retiro por $100.000 en CAJERO EXITO a las 11:00. 21/09/2026"
    payload = {
        "medio": "SMS",
        "texto_sms": sms
    }
    response = client.post("/api/v1/webhooks/ios-shortcut", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "exitoso"
    assert data["es_transferencia_interna"] is True
    assert data["monto_cop"] == 100000.0

    # Validar rebalanceo de cuentas: Bancolombia -100k, Efectivo +100k
    c_res = client.get("/api/v1/cuentas")
    banco = next(c for c in c_res.json() if c["nombre"] == "Bancolombia Principal")
    efectivo = next(c for c in c_res.json() if c["nombre"] == "Billetera Efectivo")
    assert banco["saldo_actual"] == 900000.0
    assert efectivo["saldo_actual"] == 150000.0  # 50.000 iniciales + 100.000 retirados


def test_webhook_idempotencia(client):
    payload = {
        "medio": "APPLE_PAY",
        "monto": 50000.0,
        "comercio": "D1 Mercado",
        "tarjeta": "Bancolombia"
    }
    # Primera llamada
    res1 = client.post("/api/v1/webhooks/ios-shortcut", json=payload)
    assert res1.status_code == 200
    assert res1.json()["status"] == "exitoso"

    # Segunda llamada inmediata idéntica (el atajo se dispara dos veces)
    res2 = client.post("/api/v1/webhooks/ios-shortcut", json=payload)
    assert res2.status_code == 200
    assert res2.json()["status"] == "ignorado_duplicado"


def test_obtener_metricas_semaforo(client):
    response = client.get("/api/v1/metricas/semaforo")
    assert response.status_code == 200
    data = response.json()
    assert data["color"] in ["VERDE", "AMARILLO", "ROJO"]
    assert "dias_restantes" in data
    assert "limite_gasto_diario_sugerido" in data


def test_obtener_resumen_dashboard(client):
    response = client.get("/api/v1/metricas/dashboard")
    assert response.status_code == 200
    data = response.json()
    assert "semaforo" in data
    assert "rendimientos" in data
    assert "cuentas" in data
    assert "transacciones" in data
    assert "total_saldo" in data
    assert len(data["cuentas"]) >= 3


def test_sincronizar_cuentas(client):
    payload = [
        {"nombre": "Nequi Ahorro", "tipo": "DEBITO", "saldo_actual": 350000.0},
        {"nombre": "Efectivo Bolsillo", "tipo": "EFECTIVO", "saldo_actual": 80000.0}
    ]
    response = client.post("/api/v1/cuentas/sincronizar", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    nombres = [c["nombre"] for c in data]
    assert "Nequi Ahorro" in nombres
    assert "Efectivo Bolsillo" in nombres


def test_eliminar_cuenta_con_transacciones(client):
    # 1. Crear cuenta
    res_crear = client.post("/api/v1/cuentas", json={
        "nombre": "Cuenta Temporal Para Borrar",
        "tipo": "DEBITO",
        "saldo_actual": 50000.0
    })
    assert res_crear.status_code == 201
    cuenta_id = res_crear.json()["id"]

    # 2. Registrar transacción sobre esta cuenta
    res_tx = client.post("/api/v1/transacciones", json={
        "monto": 10000.0,
        "tipo": "EGRESO",
        "comercio": "Tienda Test",
        "cuenta_origen_id": cuenta_id
    })
    assert res_tx.status_code == 201

    # 3. Eliminar la cuenta (debe eliminar la cuenta y cascada de transacciones sin error 500)
    res_del = client.delete(f"/api/v1/cuentas/{cuenta_id}")
    assert res_del.status_code == 204

    # 4. Verificar que la cuenta ya no existe
    res_get = client.get(f"/api/v1/cuentas/{cuenta_id}")
    assert res_get.status_code == 404

