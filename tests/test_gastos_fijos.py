import pytest
from backend.app.models import GastoFijo, PerfilFinanciero, Transaccion, TipoTransaccion, MedioCaptura
from tests.conftest import TestingSessionLocal


def test_crear_y_listar_gasto_fijo(client):
    # 1. Crear gasto fijo
    payload = {
        "nombre": "Arriendo Apartamento",
        "monto": 1200000.0,
        "dia_pago": 5,
        "categoria": "Hogar y Vivienda"
    }
    res = client.post("/api/v1/gastos-fijos", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["nombre"] == "Arriendo Apartamento"
    assert data["monto"] == 1200000.0
    assert data["dia_pago"] == 5
    gasto_id = data["id"]

    # 2. Listar gastos fijos y verificar resumen
    res_list = client.get("/api/v1/gastos-fijos")
    assert res_list.status_code == 200
    resumen = res_list.json()
    assert resumen["total_fijos"] >= 1200000.0
    assert resumen["cantidad_compromisos"] >= 1
    assert any(item["id"] == gasto_id for item in resumen["items"])

    # 3. Toggle pagado
    res_toggle = client.patch(f"/api/v1/gastos-fijos/{gasto_id}/toggle-pagado")
    assert res_toggle.status_code == 200
    assert res_toggle.json()["pagado_este_mes"] is True

    # 4. Eliminar gasto fijo
    res_del = client.delete(f"/api/v1/gastos-fijos/{gasto_id}")
    assert res_del.status_code == 204


def test_descuento_automatico_gastos_fijos_en_dashboard(client):
    # Limpiar y registrar un gasto fijo conocido
    db = TestingSessionLocal()
    try:
        db.query(GastoFijo).delete()
        gf = GastoFijo(nombre="Internet Fibra", monto=150000.0, dia_pago=10, activo=True)
        db.add(gf)
        db.commit()
    finally:
        db.close()

    res = client.get("/api/v1/metricas/dashboard")
    assert res.status_code == 200
    data = res.json()
    assert "gastos_fijos" in data
    assert data["gastos_fijos"]["total_fijos"] == 150000.0
    assert len(data["gastos_fijos"]["items"]) == 1
    assert data["gastos_fijos"]["items"][0]["nombre"] == "Internet Fibra"

    # Verificar que el semáforo y presupuesto disponible descuentan los 150.000 de gasto fijo
    assert data["semaforo"]["total_gastos_fijos"] == 150000.0


def test_crear_gasto_fijo_ya_cubierto_no_pendiente(client):
    # Crear un gasto fijo marcado expresamente como ya cubierto este mes
    payload = {
        "nombre": "Seguro de Salud",
        "monto": 350000.0,
        "dia_pago": 1,
        "pagado_este_mes": True
    }
    res = client.post("/api/v1/gastos-fijos", json=payload)
    assert res.status_code == 201
    item = res.json()
    assert item["pagado_este_mes"] is True
    gasto_id = item["id"]

    # Verificar que en el resumen aparezca en total_apartado_nomina y NO en total_pendiente
    res_list = client.get("/api/v1/gastos-fijos")
    assert res_list.status_code == 200
    resumen = res_list.json()
    assert resumen["total_apartado_nomina"] >= 350000.0
    
    # Limpiar
    client.delete(f"/api/v1/gastos-fijos/{gasto_id}")


def test_dashboard_transacciones_incluyen_tipo_cuenta_y_origen_id(client):
    res = client.get("/api/v1/metricas/dashboard")
    assert res.status_code == 200
    data = res.json()
    assert "transacciones" in data
    for tx in data["transacciones"]:
        assert "cuenta_origen_id" in tx
        assert "cuenta_tipo" in tx

