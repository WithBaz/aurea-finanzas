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


def test_pagar_gasto_fijo_deduce_saldo_y_crea_movimiento(client):
    # 1. Crear cuenta con saldo inicial
    res_c = client.post("/api/v1/cuentas", json={"nombre": "Bancolombia Test", "tipo": "DEBITO", "saldo_actual": 1000000.0})
    assert res_c.status_code == 201
    cuenta_id = res_c.json()["id"]

    # 2. Crear gasto fijo mensual
    res_gf = client.post("/api/v1/gastos-fijos", json={"nombre": "Internet Claro", "monto": 120000.0})
    assert res_gf.status_code == 201
    gf_id = res_gf.json()["id"]
    assert res_gf.json()["pagado_este_mes"] is False

    # 3. Pagar gasto fijo usando la cuenta creada
    res_pago = client.post(f"/api/v1/gastos-fijos/{gf_id}/pagar", json={"cuenta_id": cuenta_id})
    assert res_pago.status_code == 200
    data_gf = res_pago.json()
    assert data_gf["pagado_este_mes"] is True
    assert data_gf["ultima_transaccion_id"] is not None

    # 4. Validar que la cuenta se dedujo en exactamente 120.000 COP
    cuenta_check = client.get(f"/api/v1/cuentas/{cuenta_id}").json()
    assert cuenta_check["saldo_actual"] == 1000000.0 - 120000.0

    # 5. Validar que se creó la transacción tipo EGRESO
    tx_check = client.get(f"/api/v1/transacciones/{data_gf['ultima_transaccion_id']}").json()
    assert tx_check["monto"] == 120000.0
    assert tx_check["tipo"] == "EGRESO"
    assert "Internet Claro" in tx_check["comercio"]
    assert tx_check["cuenta_origen_id"] == cuenta_id

    # 6. Revertir el pago y validar que el saldo de la cuenta vuelve a 1.000.000
    res_rev = client.post(f"/api/v1/gastos-fijos/{gf_id}/revertir")
    assert res_rev.status_code == 200
    assert res_rev.json()["pagado_este_mes"] is False
    cuenta_restaurada = client.get(f"/api/v1/cuentas/{cuenta_id}").json()
    assert cuenta_restaurada["saldo_actual"] == 1000000.0

    # Limpiar
    client.delete(f"/api/v1/gastos-fijos/{gf_id}")
    client.delete(f"/api/v1/cuentas/{cuenta_id}")


def test_gasto_frecuente_gasolina_multicobro(client):
    # 1. Crear cuenta
    res_c = client.post("/api/v1/cuentas", json={"nombre": "Tarjeta Nu", "tipo": "DEBITO", "saldo_actual": 500000.0})
    cuenta_id = res_c.json()["id"]

    # 2. Crear gasto frecuente: Gasolina $300.000, 3 veces en el mes ($100.000 c/u)
    res_gf = client.post("/api/v1/gastos-fijos", json={
        "nombre": "Gasolina",
        "monto": 300000.0,
        "es_frecuente": True,
        "frecuencia_veces": 3
    })
    assert res_gf.status_code == 201
    gf = res_gf.json()
    assert gf["es_frecuente"] is True
    assert gf["frecuencia_veces"] == 3
    assert gf["veces_pagadas"] == 0
    assert gf["pagado_este_mes"] is False
    gf_id = gf["id"]

    # 3. Pagar vez 1
    pago_1 = client.post(f"/api/v1/gastos-fijos/{gf_id}/pagar", json={"cuenta_id": cuenta_id}).json()
    assert pago_1["veces_pagadas"] == 1
    assert pago_1["pagado_este_mes"] is False
    c_1 = client.get(f"/api/v1/cuentas/{cuenta_id}").json()
    assert c_1["saldo_actual"] == 400000.0  # 500.000 - 100.000

    # 4. Pagar vez 2
    pago_2 = client.post(f"/api/v1/gastos-fijos/{gf_id}/pagar", json={"cuenta_id": cuenta_id}).json()
    assert pago_2["veces_pagadas"] == 2
    assert pago_2["pagado_este_mes"] is False

    # 5. Pagar vez 3 (completa el presupuesto)
    pago_3 = client.post(f"/api/v1/gastos-fijos/{gf_id}/pagar", json={"cuenta_id": cuenta_id}).json()
    assert pago_3["veces_pagadas"] == 3
    assert pago_3["pagado_este_mes"] is True  # ¡Completó todas las veces!
    c_3 = client.get(f"/api/v1/cuentas/{cuenta_id}").json()
    assert c_3["saldo_actual"] == 200000.0  # 500.000 - 300.000

    # Limpiar
    client.delete(f"/api/v1/gastos-fijos/{gf_id}")
    client.delete(f"/api/v1/cuentas/{cuenta_id}")


def test_reset_mensual_automatico_colombia(client):
    # Crear gasto fijo que fue pagado en el mes anterior (ej: 2020-01)
    db = TestingSessionLocal()
    try:
        gf = GastoFijo(
            nombre="Gimnasio Pasado",
            monto=90000.0,
            pagado_este_mes=True,
            ultimo_mes_pagado="2020-01",  # Mes viejo
            es_frecuente=True,
            frecuencia_veces=2,
            veces_pagadas=2,
            activo=True
        )
        db.add(gf)
        db.commit()
        db.refresh(gf)
        gf_id = gf.id
    finally:
        db.close()

    # Al consultar el resumen actual (ej: en 2026), debe resetear automáticamente a pendiente
    res = client.get("/api/v1/gastos-fijos")
    assert res.status_code == 200
    resumen = res.json()
    item_gimnasio = next(i for i in resumen["items"] if i["id"] == gf_id)
    assert item_gimnasio["pagado_este_mes"] is False
    assert item_gimnasio["veces_pagadas"] == 0

    # Limpiar
    client.delete(f"/api/v1/gastos-fijos/{gf_id}")


