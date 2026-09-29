import pytest
from backend.app.models import Cuenta, Transaccion, TipoCuenta, TipoTransaccion, MedioCaptura, Usuario
from tests.conftest import TestingSessionLocal


def test_auth_registro_login_y_face_id(client):
    # 1. Verificar estado inicial
    res = client.get("/api/v1/auth/estado")
    assert res.status_code == 200

    # 2. Registrar usuario inicial con PIN de 4 dígitos
    reg_payload = {"username": "jorge", "pin": "1234"}
    res_reg = client.post("/api/v1/auth/registro", json=reg_payload)
    assert res_reg.status_code == 201
    data_reg = res_reg.json()
    assert data_reg["username"] == "jorge"

    # 3. Login con PIN correcto
    res_login = client.post("/api/v1/auth/login", json={"username": "jorge", "pin": "1234"})
    assert res_login.status_code == 200
    assert res_login.json()["status"] == "autenticado"

    # 4. Login con PIN incorrecto
    res_bad = client.post("/api/v1/auth/login", json={"username": "jorge", "pin": "9999"})
    assert res_bad.status_code == 401

    # 5. Activar Face ID
    res_face = client.post("/api/v1/auth/face-id", json={"enabled": True, "credential_id": "test_cred_123"})
    assert res_face.status_code == 200
    assert res_face.json()["face_id_enabled"] is True

    # 6. Login con Face ID
    res_face_login = client.post("/api/v1/auth/face-id-login")
    assert res_face_login.status_code == 200
    assert res_face_login.json()["status"] == "autenticado"

    # 7. Cambiar PIN
    res_cambio = client.post("/api/v1/auth/cambiar-pin", json={"pin_actual": "1234", "pin_nuevo": "5678"})
    assert res_cambio.status_code == 200

    # 8. Verificar nuevo PIN
    res_nuevo_pin = client.post("/api/v1/auth/login", json={"pin": "5678"})
    assert res_nuevo_pin.status_code == 200


def test_creacion_tarjeta_credito_con_cupo_disponible(client):
    # Crear tarjeta con cupo total 5M y cupo disponible 3.5M
    payload = {
        "nombre": "Nu Mastercard Test",
        "tipo": "CREDITO",
        "cupo_total": 5000000.0,
        "cupo_disponible": 3500000.0,
        "saldo_actual": 0.0
    }
    res = client.post("/api/v1/cuentas", json=payload)
    assert res.status_code == 201
    cuenta = res.json()
    # La deuda actual debe ser 5.000.000 - 3.500.000 = 1.500.000
    assert cuenta["saldo_actual"] == 1500000.0
    assert cuenta["cupo_total"] == 5000000.0

    # Consultar dashboard y verificar cupo_disponible
    res_dash = client.get("/api/v1/metricas/dashboard")
    assert res_dash.status_code == 200
    cuentas = res_dash.json()["cuentas"]
    c_nu = next(c for c in cuentas if c["id"] == cuenta["id"])
    assert c_nu["cupo_disponible"] == 3500000.0

    # Limpiar
    client.delete(f"/api/v1/cuentas/{cuenta['id']}")


def test_edicion_y_eliminacion_transaccion(client):
    # 1. Crear cuenta
    c_res = client.post("/api/v1/cuentas", json={"nombre": "Billetera Efectivo Test", "tipo": "EFECTIVO", "saldo_actual": 200000.0})
    cuenta_id = c_res.json()["id"]

    # 2. Registrar egreso de 50.000 (saldo pasa a 150.000)
    tx_res = client.post("/api/v1/transacciones", json={
        "monto": 50000.0,
        "comercio": "Almuerzo Restaurante",
        "tipo": "EGRESO",
        "cuenta_origen_id": cuenta_id,
        "medio": "MANUAL"
    })
    tx_id = tx_res.json()["id"]

    # Verificar saldo descontado
    c_check = client.get(f"/api/v1/cuentas/{cuenta_id}").json()
    assert c_check["saldo_actual"] == 150000.0

    # 3. Editar transacción: cambiar monto a 30.000 y cuotas a 3
    tx_edit = client.put(f"/api/v1/transacciones/{tx_id}", json={
        "monto": 30000.0,
        "comercio": "Almuerzo Ejecutivo",
        "cuotas_totales": 3
    })
    assert tx_edit.status_code == 200
    assert tx_edit.json()["monto"] == 30000.0
    assert tx_edit.json()["comercio"] == "Almuerzo Ejecutivo"
    assert tx_edit.json()["cuotas_totales"] == 3

    c_check2 = client.get(f"/api/v1/cuentas/{cuenta_id}").json()
    assert c_check2["saldo_actual"] == 170000.0

    # 4. Eliminar transacción (debe revertir los 30.000, saldo vuelve a 200.000)
    del_res = client.delete(f"/api/v1/transacciones/{tx_id}")
    assert del_res.status_code == 204

    c_check3 = client.get(f"/api/v1/cuentas/{cuenta_id}").json()
    assert c_check3["saldo_actual"] == 200000.0

    # Limpiar cuenta
    client.delete(f"/api/v1/cuentas/{cuenta_id}")


def test_multi_usuario_aislamiento_de_datos(client):
    """
    Verifica que dos usuarios independientes (ej. titular y un amigo) tengan sus cuentas,
    gastos fijos y movimientos 100% aislados y seguros.
    """
    # 1. Registrar Usuario A (Carlos)
    res_a = client.post("/api/v1/auth/registro", json={"username": "carlos", "pin": "4321"})
    assert res_a.status_code == 201
    uid_a = res_a.json()["usuario_id"]

    # 2. Registrar Usuario B (Pedro / Amigo)
    res_b = client.post("/api/v1/auth/registro", json={"username": "pedro_amigo", "pin": "9876"})
    assert res_b.status_code == 201
    uid_b = res_b.json()["usuario_id"]

    # 3. Listar perfiles en el selector multi-cuenta
    res_usuarios = client.get("/api/v1/auth/usuarios")
    assert res_usuarios.status_code == 200
    nombres_usuarios = [u["username"] for u in res_usuarios.json()]
    assert "carlos" in nombres_usuarios
    assert "pedro_amigo" in nombres_usuarios

    # 4. Carlos crea una cuenta y un gasto fijo
    header_a = {"X-Usuario-Id": str(uid_a)}
    c_a = client.post("/api/v1/cuentas", json={"nombre": "Ahorros Carlos", "tipo": "DEBITO", "saldo_actual": 1200000.0}, headers=header_a)
    assert c_a.status_code == 201
    cuenta_a_id = c_a.json()["id"]

    gf_a = client.post("/api/v1/gastos-fijos", json={"nombre": "Internet Carlos", "monto": 80000.0, "dia_pago": 10}, headers=header_a)
    assert gf_a.status_code == 201
    gasto_a_id = gf_a.json()["id"]

    # 5. Pedro consulta su dashboard y cuentas: NO debe ver las cuentas ni gastos de Carlos
    header_b = {"X-Usuario-Id": str(uid_b)}
    cuentas_pedro = client.get("/api/v1/cuentas", headers=header_b).json()
    assert all(c["id"] != cuenta_a_id for c in cuentas_pedro)

    gastos_pedro = client.get("/api/v1/gastos-fijos", headers=header_b).json()
    assert all(g["id"] != gasto_a_id for g in gastos_pedro["items"])

    dash_pedro = client.get("/api/v1/metricas/dashboard", headers=header_b).json()
    assert all(c["id"] != cuenta_a_id for c in dash_pedro["cuentas"])

    # 6. Pedro crea su propia cuenta personal
    c_b = client.post("/api/v1/cuentas", json={"nombre": "Billetera Pedro", "tipo": "EFECTIVO", "saldo_actual": 300000.0}, headers=header_b)
    assert c_b.status_code == 201
    cuenta_b_id = c_b.json()["id"]

    # 7. Carlos consulta sus cuentas: NO debe ver la cuenta de Pedro
    cuentas_carlos = client.get("/api/v1/cuentas", headers=header_a).json()
    assert any(c["id"] == cuenta_a_id for c in cuentas_carlos)
    assert all(c["id"] != cuenta_b_id for c in cuentas_carlos)

    # 8. Face ID independiente
    res_face_b = client.post("/api/v1/auth/face-id", json={"enabled": True}, headers=header_b)
    assert res_face_b.status_code == 200
    assert res_face_b.json()["face_id_enabled"] is True

    res_face_login_b = client.post("/api/v1/auth/face-id-login", json={"username": "pedro_amigo"}, headers=header_b)
    assert res_face_login_b.status_code == 200
    assert res_face_login_b.json()["username"] == "pedro_amigo"


def test_auth_con_contrasena_alfanumerica(client):
    # 1. Registro con contraseña de texto estándar
    res_reg = client.post("/api/v1/auth/registro", json={
        "username": "lucia_tech",
        "password": "miClaveSegura2026"
    })
    assert res_reg.status_code == 201
    assert res_reg.json()["username"] == "lucia_tech"

    # 2. Login correcto con contraseña
    res_login = client.post("/api/v1/auth/login", json={
        "username": "lucia_tech",
        "password": "miClaveSegura2026"
    })
    assert res_login.status_code == 200
    assert res_login.json()["status"] == "autenticado"
    assert res_login.json()["username"] == "lucia_tech"

    # 3. Login con contraseña incorrecta
    res_bad = client.post("/api/v1/auth/login", json={
        "username": "lucia_tech",
        "password": "claveIncorrecta"
    })
    assert res_bad.status_code == 401
    assert "incorrecto" in res_bad.json()["detail"].lower()

    # 4. Login con usuario inexistente
    res_not_found = client.post("/api/v1/auth/login", json={
        "username": "no_existo",
        "password": "miClaveSegura2026"
    })
    assert res_not_found.status_code == 404


def test_registrar_corte_y_pago_tarjeta_credito(client):
    # 1. Crear tarjeta con 500k de deuda y 2M cupo total
    tc_res = client.post("/api/v1/cuentas", json={
        "nombre": "Nu Corte Test",
        "tipo": "CREDITO",
        "cupo_total": 2000000.0,
        "cupo_disponible": 1500000.0
    })
    assert tc_res.status_code == 201
    tc_id = tc_res.json()["id"]
    assert tc_res.json()["saldo_actual"] == 500000.0

    # 2. Registrar fecha de corte manual
    corte_res = client.post(f"/api/v1/cuentas/{tc_id}/corte")
    assert corte_res.status_code == 200
    tc_corte = corte_res.json()
    assert tc_corte["saldo_al_corte"] == 500000.0
    assert tc_corte["estado_corte"] == "PENDIENTE_PAGO"
    assert tc_corte["fecha_ultimo_corte"] is not None

    # 3. Obtener cuenta de débito para pagar (Bancolombia Principal con 1M)
    cuentas = client.get("/api/v1/cuentas").json()
    banco = next(c for c in cuentas if c["nombre"] == "Bancolombia Principal")
    banco_id = banco["id"]
    saldo_banco_antes = banco["saldo_actual"]

    # 4. Registrar pago parcial de 300.000 COP a la tarjeta desde Bancolombia
    pago_res = client.post(f"/api/v1/cuentas/{tc_id}/pagar", json={
        "monto": 300000.0,
        "cuenta_origen_id": banco_id
    })
    assert pago_res.status_code == 200
    data_pago = pago_res.json()
    assert data_pago["status"] == "exitoso"
    assert data_pago["monto_pagado"] == 300000.0
    assert data_pago["saldo_deuda_restante"] == 200000.0
    assert data_pago["saldo_al_corte_restante"] == 200000.0
    assert data_pago["estado_corte"] == "PENDIENTE_PAGO"

    # Verificar que Bancolombia se debitó
    banco_despues = client.get(f"/api/v1/cuentas/{banco_id}").json()
    assert banco_despues["saldo_actual"] == saldo_banco_antes - 300000.0

    # 5. Registrar pago del saldo restante (200.000 COP)
    pago_fin = client.post(f"/api/v1/cuentas/{tc_id}/pagar", json={
        "monto": 200000.0,
        "cuenta_origen_id": banco_id
    })
    assert pago_fin.status_code == 200
    assert pago_fin.json()["saldo_deuda_restante"] == 0.0
    assert pago_fin.json()["saldo_al_corte_restante"] == 0.0
    assert pago_fin.json()["estado_corte"] == "AL_DIA"


def test_modo_claro_oscuro_y_animacion_face_id(client):
    """
    Verifica que la interfaz web de Aurea incluya:
    1. Soporte y selector de Modo Claro / Oscuro (CSS variables, selector en Ajustes, botón en Header).
    2. Pantalla de carga con animación biométrica moderna Apple Face ID HUD (SVG viewfinder, láser, radar, checkmark).
    """
    res = client.get("/")
    assert res.status_code == 200
    html = res.text

    # 1. Verificación de Modo Claro / Oscuro
    assert "theme-light" in html
    assert "--system-bg: #F2F2F7;" in html
    assert "--card-bg: #FFFFFF;" in html
    assert "btn-theme-toggle" in html
    assert "theme-opt-dark" in html
    assert "theme-opt-light" in html
    assert "theme-opt-auto" in html
    assert "aurea_theme" in html

    # 2. Verificación de Animación Apple Face ID HUD
    assert "overlay-login-animacion" in html
    assert "faceid-svg" in html
    assert "faceid-brackets" in html
    assert "faceid-radar" in html
    assert "faceid-mesh" in html
    assert "faceid-checkmark" in html
    assert "animate-laserScanHUD" in html


def test_login_liquid_glass_y_sin_splash_loader(client):
    """
    Verifica que:
    1. No exista apple-touch-startup-image para evitar pantallas de carga prematuras.
    2. El formulario de login use inputs y tarjetas liquid glass.
    3. Exista la guarda usuarioInteractuo para evitar autologin no solicitado al abrir la app.
    4. El icono de la aplicación se sirva correctamente en 180x180.
    """
    res = client.get("/")
    assert res.status_code == 200
    html = res.text

    assert "apple-touch-startup-image" not in html
    assert "glass-input" in html
    assert "usuarioInteractuo" in html

    # Verificar que el icono nuevo se sirve en 200 OK
    res_icon = client.get("/apple-touch-icon.png")
    assert res_icon.status_code == 200
    assert res_icon.headers["content-type"] == "image/png"


def test_aislamiento_navegacion_y_centrado_login(client):
    """
    Verifica que:
    1. La barra de navegación inferior y el contenedor principal estén estrictamente aislados y ocultos con clase hidden mientras la sesión no esté autenticada.
    2. #pantalla-auth cuente con posición fija completa, z-index superior, padding de área segura para notch/dynamic island y centrado flex.
    3. Las funciones JavaScript de autenticación controlen la visibilidad de nav-inferior y app-principal.
    4. El cambio de tabs y modales estén blindados ante accesos no autenticados.
    """
    res = client.get("/")
    assert res.status_code == 200
    html = res.text

    # 1. Elementos estructurales ocultos por defecto
    assert 'id="nav-inferior" class="fixed bottom-0 left-0 right-0 z-40 liquid-glass-nav hidden"' in html
    assert 'id="app-principal" class="w-full max-w-lg mx-auto px-4 sm:px-6 pt-2 hidden"' in html

    # 2. Reglas CSS estrictas
    assert "#nav-inferior.hidden" in html
    assert "#app-principal.hidden" in html
    assert "padding-top: calc(var(--sat) + 12px) !important;" in html
    assert "padding-bottom: calc(var(--sab) + 12px) !important;" in html
    assert "position: fixed !important;" in html
    assert "z-index: 80 !important;" in html

    # 3. Control de visibilidad en JS
    assert "document.getElementById('nav-inferior')?.classList.add('hidden');" in html
    assert "document.getElementById('app-principal')?.classList.add('hidden');" in html
    assert "document.getElementById('nav-inferior')?.classList.remove('hidden');" in html
    assert "document.getElementById('app-principal')?.classList.remove('hidden');" in html

    # 4. Guardas de autenticación
    assert "if (!sesionAutenticada) return;" in html






