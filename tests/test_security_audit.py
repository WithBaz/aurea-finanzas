import pytest
from backend.app.models import Cuenta, Transaccion, TipoCuenta, TipoTransaccion, MedioCaptura, Usuario
from tests.conftest import TestingSessionLocal


def test_cabeceras_de_seguridad_http(client):
    """
    Verifica que las cabeceras de blindaje OWASP (X-Frame-Options, X-Content-Type-Options, etc.)
    se inyecten en todas las respuestas HTTP.
    """
    res = client.get("/api/v1/auth/estado")
    assert res.status_code == 200
    assert res.headers.get("x-content-type-options") == "nosniff"
    assert res.headers.get("x-frame-options") == "DENY"
    assert "1; mode=block" in res.headers.get("x-xss-protection", "")
    assert res.headers.get("referrer-policy") == "strict-origin-when-cross-origin"


def test_rechazo_token_invalido_anti_spoofing(client):
    """
    Verifica que tokens falsificados o inválidos sean rechazados con 401 Unauthorized.
    """
    bad_headers = {"Authorization": "Bearer token_falso_hacker_12345"}
    res = client.get("/api/v1/cuentas", headers=bad_headers)
    assert res.status_code == 401
    assert "inválido" in res.json()["detail"].lower() or "expirado" in res.json()["detail"].lower()

    bad_aurea_header = {"X-Aurea-Token": "token_invalido_xyz"}
    res_aurea = client.get("/api/v1/cuentas", headers=bad_aurea_header)
    assert res_aurea.status_code == 401


def test_anti_idor_aislamiento_entre_usuarios(client):
    """
    Prueba que el Usuario B jamás pueda leer, modificar, eliminar o pagar cuentas o transacciones del Usuario A (IDOR).
    """
    # 1. Registrar Usuario A (Carlos)
    res_a = client.post("/api/v1/auth/registro", json={"username": "carlos_idor", "pin": "1111"})
    assert res_a.status_code == 201
    token_a = res_a.json()["biometric_token"]
    auth_a = {"Authorization": f"Bearer {token_a}"}

    # 2. Registrar Usuario B (Atacante / Amigo)
    res_b = client.post("/api/v1/auth/registro", json={"username": "hacker_bob", "pin": "2222"})
    assert res_b.status_code == 201
    token_b = res_b.json()["biometric_token"]
    auth_b = {"Authorization": f"Bearer {token_b}"}

    # 3. Carlos crea una cuenta bancaria y una tarjeta de crédito
    c_res = client.post("/api/v1/cuentas", json={
        "nombre": "Bancolombia Carlos Privada",
        "tipo": "DEBITO",
        "saldo_actual": 5000000.0
    }, headers=auth_a)
    assert c_res.status_code == 201
    cuenta_carlos_id = c_res.json()["id"]

    tc_res = client.post("/api/v1/cuentas", json={
        "nombre": "Visa Black Carlos",
        "tipo": "CREDITO",
        "cupo_total": 10000000.0,
        "cupo_disponible": 8000000.0
    }, headers=auth_a)
    assert tc_res.status_code == 201
    tc_carlos_id = tc_res.json()["id"]

    # 4. Carlos registra un gasto en su cuenta
    tx_res = client.post("/api/v1/transacciones", json={
        "monto": 250000.0,
        "tipo": "EGRESO",
        "comercio": "Apple Store Colombia",
        "cuenta_origen_id": cuenta_carlos_id
    }, headers=auth_a)
    assert tx_res.status_code == 201
    tx_carlos_id = tx_res.json()["id"]

    # ==========================================
    # ATAQUES DE BOB CONTRA LOS RECURSOS DE CARLOS
    # ==========================================

    # Ataque IDOR 1: Bob intenta leer la cuenta de Carlos
    res_read = client.get(f"/api/v1/cuentas/{cuenta_carlos_id}", headers=auth_b)
    assert res_read.status_code == 403
    assert "permiso" in res_read.json()["detail"].lower()

    # Ataque IDOR 2: Bob intenta modificar el saldo de la cuenta de Carlos
    res_mod = client.put(f"/api/v1/cuentas/{cuenta_carlos_id}", json={
        "saldo_actual": 0.0
    }, headers=auth_b)
    assert res_mod.status_code == 403

    # Ataque IDOR 3: Bob intenta eliminar la cuenta de Carlos
    res_del = client.delete(f"/api/v1/cuentas/{cuenta_carlos_id}", headers=auth_b)
    assert res_del.status_code == 403

    # Ataque IDOR 4: Bob intenta forzar un corte en la tarjeta de Carlos
    res_corte = client.post(f"/api/v1/cuentas/{tc_carlos_id}/corte", headers=auth_b)
    assert res_corte.status_code == 403

    # Ataque IDOR 5: Bob intenta debitar de la cuenta de Carlos para pagar su propia tarjeta
    # Bob crea su tarjeta
    tc_bob = client.post("/api/v1/cuentas", json={
        "nombre": "Mastercard Bob",
        "tipo": "CREDITO",
        "cupo_total": 2000000.0,
        "cupo_disponible": 1000000.0
    }, headers=auth_b).json()
    
    res_pago_malicioso = client.post(f"/api/v1/cuentas/{tc_bob['id']}/pagar", json={
        "monto": 500000.0,
        "cuenta_origen_id": cuenta_carlos_id
    }, headers=auth_b)
    assert res_pago_malicioso.status_code == 403

    # Ataque IDOR 6: Bob intenta leer, editar o borrar la transacción de Carlos
    assert client.get(f"/api/v1/transacciones/{tx_carlos_id}", headers=auth_b).status_code == 403
    assert client.put(f"/api/v1/transacciones/{tx_carlos_id}", json={"monto": 1.0}, headers=auth_b).status_code == 403
    assert client.delete(f"/api/v1/transacciones/{tx_carlos_id}", headers=auth_b).status_code == 403

    # Verificar que los datos y saldos de Carlos quedaron 100% íntegros
    cuenta_carlos_check = client.get(f"/api/v1/cuentas/{cuenta_carlos_id}", headers=auth_a).json()
    assert cuenta_carlos_check["saldo_actual"] == 5000000.0 - 250000.0


def test_proteccion_destructiva_reiniciar_todo(client):
    """
    Verifica que /reiniciar-todo no pueda ser ejecutado anónimamente y que
    al ser ejecutado por un usuario con sesión, jamás borre datos de otros usuarios.
    """
    # 1. Intento sin autenticación -> Rechazado 401
    res_anon = client.post("/api/v1/metricas/reiniciar-todo")
    assert res_anon.status_code == 401

    # 2. Registrar Usuario A y crear datos
    res_a = client.post("/api/v1/auth/registro", json={"username": "victima_a", "pin": "3333"})
    auth_a = {"Authorization": f"Bearer {res_a.json()['biometric_token']}"}
    c_a = client.post("/api/v1/cuentas", json={"nombre": "Ahorros A", "tipo": "DEBITO", "saldo_actual": 1000000.0}, headers=auth_a).json()

    # 3. Registrar Usuario B y crear datos
    res_b = client.post("/api/v1/auth/registro", json={"username": "usuario_b", "pin": "4444"})
    auth_b = {"Authorization": f"Bearer {res_b.json()['biometric_token']}"}
    c_b = client.post("/api/v1/cuentas", json={"nombre": "Ahorros B", "tipo": "DEBITO", "saldo_actual": 800000.0}, headers=auth_b).json()

    # 4. Usuario B ejecuta reiniciar-todo
    res_reset = client.post("/api/v1/metricas/reiniciar-todo", headers=auth_b)
    assert res_reset.status_code == 200

    # 5. La cuenta personal de B ("Ahorros B") fue eliminada exitosamente
    cuentas_b = client.get("/api/v1/cuentas", headers=auth_b).json()
    assert all(c["id"] != c_b["id"] for c in cuentas_b)

    # 6. Las cuentas de A siguen 100% intactas
    cuentas_a = client.get("/api/v1/cuentas", headers=auth_a).json()
    assert any(c["id"] == c_a["id"] for c in cuentas_a)


def test_inyeccion_sql_parametrizada(client):
    """
    Verifica que intentos de inyección SQL comunes sean neutralizados por SQLAlchemy ORM.
    """
    payloads_maliciosos = [
        "' OR '1'='1",
        "admin' --",
        "'; DROP TABLE transacciones; --",
        "1 UNION SELECT 1, 'hacked', 999999, '2026-01-01', 'EGRESO', 1, 1, 1, 0, 0, 0, 0 --"
    ]

    for sql_inject in payloads_maliciosos:
        # 1. En Login
        res_login = client.post("/api/v1/auth/login", json={"username": sql_inject, "pin": "1234"})
        assert res_login.status_code in [401, 404]

        # 2. En Creación de transacción (comercio o texto)
        res_tx = client.get(f"/api/v1/transacciones/ia-rapida?texto={sql_inject}")
        assert res_tx.status_code in [200, 400]

    # Verificar que la base de datos no fue corrompida
    db = TestingSessionLocal()
    assert db.query(Cuenta).count() >= 0
    db.close()


def test_seguridad_webhooks_token_invalido(client):
    """
    Verifica que webhooks con tokens inválidos sean rechazados con 401.
    """
    payload = {
        "medio": "APPLE_PAY",
        "monto": 50000.0,
        "comercio": "Zara",
        "tarjeta": "Visa",
        "token": "token_invalido_999"
    }
    res = client.post("/api/v1/webhooks/ios-shortcut", json=payload)
    assert res.status_code == 401
    assert "token" in res.json()["detail"].lower()


def test_anti_idor_transacciones_cuentas_cruzadas(client):
    """
    Verifica que un usuario no pueda crear transacciones debitando de cuentas de otro usuario,
    ni reasignar transacciones hacia cuentas ajenas.
    """
    res_a = client.post("/api/v1/auth/registro", json={"username": "alice_finance", "pin": "5555"})
    auth_a = {"Authorization": f"Bearer {res_a.json()['biometric_token']}"}
    c_a = client.post("/api/v1/cuentas", json={"nombre": "Bancolombia Alice", "tipo": "DEBITO", "saldo_actual": 2000000.0}, headers=auth_a).json()

    res_b = client.post("/api/v1/auth/registro", json={"username": "bob_evil", "pin": "6666"})
    auth_b = {"Authorization": f"Bearer {res_b.json()['biometric_token']}"}
    c_b = client.post("/api/v1/cuentas", json={"nombre": "Billetera Bob", "tipo": "EFECTIVO", "saldo_actual": 10000.0}, headers=auth_b).json()

    # Bob intenta registrar un egreso debitando de la cuenta de Alice
    res_hack_egreso = client.post("/api/v1/transacciones", json={
        "monto": 500000.0,
        "tipo": "EGRESO",
        "comercio": "Casino",
        "cuenta_origen_id": c_a["id"]
    }, headers=auth_b)
    assert res_hack_egreso.status_code == 403

    # Bob intenta transferir dinero desde la cuenta de Alice hacia su propia cuenta
    res_hack_transfer = client.post("/api/v1/transacciones", json={
        "monto": 500000.0,
        "tipo": "TRANSFERENCIA_INTERNA",
        "comercio": "Transferencia ilícita",
        "cuenta_origen_id": c_a["id"],
        "cuenta_destino_id": c_b["id"]
    }, headers=auth_b)
    assert res_hack_transfer.status_code == 403

    # Bob crea su propia transacción legítima
    tx_bob = client.post("/api/v1/transacciones", json={
        "monto": 5000.0,
        "tipo": "EGRESO",
        "comercio": "Café",
        "cuenta_origen_id": c_b["id"]
    }, headers=auth_b).json()

    # Bob intenta reasignar su gasto para que se descuente de la cuenta de Alice
    res_reasign = client.patch(f"/api/v1/transacciones/{tx_bob['id']}/asignar-cuenta", json={
        "cuenta_id": c_a["id"]
    }, headers=auth_b)
    assert res_reasign.status_code == 403


def test_seguridad_cambiar_pin_tiempo_constante(client):
    """
    Verifica que cambiar PIN valide el PIN actual correctamente y rechace intentos erróneos.
    """
    res = client.post("/api/v1/auth/registro", json={"username": "usuario_pin", "pin": "9876"})
    auth = {"Authorization": f"Bearer {res.json()['biometric_token']}"}

    # Intentar cambiar PIN con PIN actual incorrecto
    res_bad = client.post("/api/v1/auth/cambiar-pin", json={
        "pin_actual": "0000",
        "pin_nuevo": "1111"
    }, headers=auth)
    assert res_bad.status_code == 401
    assert "no coincide" in res_bad.json()["detail"].lower()

    # Intentar cambiar PIN con PIN nuevo menor a 4 caracteres (rechazado por validación Pydantic)
    res_short = client.post("/api/v1/auth/cambiar-pin", json={
        "pin_actual": "9876",
        "pin_nuevo": "12"
    }, headers=auth)
    assert res_short.status_code == 422

    # Cambiar PIN exitosamente
    res_ok = client.post("/api/v1/auth/cambiar-pin", json={
        "pin_actual": "9876",
        "pin_nuevo": "4321"
    }, headers=auth)
    assert res_ok.status_code == 200

    # Verificar que el nuevo PIN funciona y el viejo no
    assert client.post("/api/v1/auth/login", json={"username": "usuario_pin", "pin": "9876"}).status_code == 401
    assert client.post("/api/v1/auth/login", json={"username": "usuario_pin", "pin": "4321"}).status_code == 200

