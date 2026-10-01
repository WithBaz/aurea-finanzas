import pytest
from tests.conftest import TestingSessionLocal
from backend.app.models import Cuenta, TipoCuenta, Transaccion, TipoTransaccion, MedioCaptura
from backend.app.services.nlp_expense_parser import NLPSmartExpenseParser


def test_extraer_montos_nlp():
    assert NLPSmartExpenseParser._extraer_monto("Pagué 15 mil de taxi") == 15000.0
    assert NLPSmartExpenseParser._extraer_monto("Almuerzo 25k") == 25000.0
    assert NLPSmartExpenseParser._extraer_monto("Compré $45.000 en el D1") == 45000.0
    assert NLPSmartExpenseParser._extraer_monto("Café 8500") == 8500.0
    assert NLPSmartExpenseParser._extraer_monto("Almuerzo 10 mil pesos") == 10000.0
    assert NLPSmartExpenseParser._extraer_monto("Almuerzo diez mil") == 10000.0
    assert NLPSmartExpenseParser._extraer_monto("Taxi 10 000") == 10000.0
    assert NLPSmartExpenseParser._extraer_monto("Comida 10 lucas") == 10000.0
    assert NLPSmartExpenseParser._extraer_monto("Almuerzo 10") == 10000.0
    assert NLPSmartExpenseParser._extraer_monto("500") == 500000.0
    assert NLPSmartExpenseParser._extraer_monto("500 mil") == 500000.0
    assert NLPSmartExpenseParser._extraer_monto("500. mil") == 500000.0
    assert NLPSmartExpenseParser._extraer_monto("500, mil") == 500000.0
    assert NLPSmartExpenseParser._extraer_monto("quinientos mil") == 500000.0
    assert NLPSmartExpenseParser._extraer_monto("fotocopia 500 pesos") == 500.0
    assert NLPSmartExpenseParser._extraer_monto("un millón") == 1000000.0
    assert NLPSmartExpenseParser._extraer_monto("un millon") == 1000000.0
    assert NLPSmartExpenseParser._extraer_monto("1 millón") == 1000000.0
    assert NLPSmartExpenseParser._extraer_monto("1 millon") == 1000000.0
    assert NLPSmartExpenseParser._extraer_monto("2 millones") == 2000000.0
    assert NLPSmartExpenseParser._extraer_monto("dos millones") == 2000000.0
    assert NLPSmartExpenseParser._extraer_monto("1.5 millones") == 1500000.0
    assert NLPSmartExpenseParser._extraer_monto("1,5 millones") == 1500000.0
    assert NLPSmartExpenseParser._extraer_monto("un millón y medio") == 1500000.0
    assert NLPSmartExpenseParser._extraer_monto("1 millon y medio") == 1500000.0
    assert NLPSmartExpenseParser._extraer_monto("1 millón 200") == 1200000.0
    assert NLPSmartExpenseParser._extraer_monto("1 millón 200 mil") == 1200000.0
    assert NLPSmartExpenseParser._extraer_monto("un millón 500") == 1500000.0
    assert NLPSmartExpenseParser._extraer_monto("un palo") == 1000000.0
    assert NLPSmartExpenseParser._extraer_monto("2 palos") == 2000000.0
    assert NLPSmartExpenseParser._extraer_monto("un palo y medio") == 1500000.0
    assert NLPSmartExpenseParser._extraer_monto("1 palo 200") == 1200000.0
    assert NLPSmartExpenseParser._extraer_monto("mil") == 1000.0
    assert NLPSmartExpenseParser._extraer_monto("mil pesos") == 1000.0
    assert NLPSmartExpenseParser._extraer_monto("mil pesos en efectivo") == 1000.0
    assert NLPSmartExpenseParser._extraer_monto("dos mil pesos") == 2000.0
    assert NLPSmartExpenseParser._extraer_monto("10,000 pesos en efectivo") == 10000.0
    assert NLPSmartExpenseParser._extraer_monto("10.000 pesos en efectivo") == 10000.0
    assert NLPSmartExpenseParser._extraer_monto("20,000 pesos en efectivo") == 20000.0
    assert NLPSmartExpenseParser._extraer_monto("100,000 pesos en efectivo") == 100000.0
    assert NLPSmartExpenseParser._extraer_monto("100.000 pesos en efectivo") == 100000.0
    assert NLPSmartExpenseParser._extraer_monto("100 mil") == 100000.0
    assert NLPSmartExpenseParser._extraer_monto("100 mil pesos") == 100000.0
    assert NLPSmartExpenseParser._extraer_monto("1,000,000 pesos en efectivo") == 1000000.0


def test_interpretar_gasto_con_cuenta_efectivo():
    db = TestingSessionLocal()
    resultado = NLPSmartExpenseParser.interpretar_texto_gasto("Pagué 15 mil de taxi en efectivo", db)
    db.close()

    assert resultado["monto"] == 15000.0
    assert resultado["tipo"] == "EGRESO"
    assert resultado["cuenta_nombre"] == "Billetera Efectivo"
    assert resultado["requiere_confirmar_cuenta"] is False


def test_interpretar_ingreso_nlp():
    db = TestingSessionLocal()
    resultado = NLPSmartExpenseParser.interpretar_texto_gasto("Me pagaron 500 mil de sueldo en efectivo", db)
    db.close()
    assert resultado["monto"] == 500000.0
    assert resultado["tipo"] == "INGRESO"
    assert resultado["cuenta_nombre"] == "Billetera Efectivo"


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


def test_api_ia_rapida_get_query_param(client):
    res = client.get("/api/v1/transacciones/ia-rapida?texto=Almuerzo 25k con Bancolombia")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "registrado"
    assert data["monto"] == 25000.0
    assert data["cuenta"] == "Bancolombia Principal"
    assert data["saldo_cuenta_actual"] == 975000.0  # 1.000.000 - 25.000


def test_api_ia_rapida_ingreso(client):
    res = client.post("/api/v1/transacciones/ia-rapida", json={"texto": "Recibí 100 mil de nómina en Bancolombia"})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "registrado"
    assert data["monto"] == 100000.0
    assert data["cuenta"] == "Bancolombia Principal"
    assert data["saldo_cuenta_actual"] == 1100000.0  # 1.000.000 + 100.000


def test_api_ia_rapida_ingreso_override_500(client):
    # Simula el atajo de iOS Registrar Ingreso llamando ?tipo=INGRESO y texto "500 con Bancolombia"
    res = client.post("/api/v1/transacciones/ia-rapida?tipo=INGRESO", json={"texto": "500 con Bancolombia"})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "registrado"
    assert data["monto"] == 500000.0
    assert data["cuenta"] == "Bancolombia Principal"


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


def test_interpretar_nequi_y_daviplata_voz():
    db = TestingSessionLocal()
    # Crear cuenta Nequi si no existe
    nequi = db.query(Cuenta).filter(Cuenta.nombre.ilike("%nequi%")).first()
    if not nequi:
        nequi = Cuenta(nombre="Billetera Nequi", tipo=TipoCuenta.DEBITO, saldo_actual=150000.0)
        db.add(nequi)
        db.commit()

    # 1. Ingreso por Nequi
    res_ingreso = NLPSmartExpenseParser.interpretar_texto_gasto("Me pasaron 80 mil a Nequi de Carlos", db)
    assert res_ingreso["monto"] == 80000.0
    assert res_ingreso["tipo"] == "INGRESO"
    assert "nequi" in res_ingreso["cuenta_nombre"].lower()

    # 2. Egreso por Nequi
    res_egreso = NLPSmartExpenseParser.interpretar_texto_gasto("Pagué 20 mil de almuerzo en Nequi", db)
    assert res_egreso["monto"] == 20000.0
    assert res_egreso["tipo"] == "EGRESO"
    assert "nequi" in res_egreso["cuenta_nombre"].lower()

    # 3. Egreso explícito "mandé" o "envié"
    res_envio = NLPSmartExpenseParser.interpretar_texto_gasto("Envié 35 mil con Nequi", db)
    assert res_envio["monto"] == 35000.0
    assert res_envio["tipo"] == "EGRESO"

    db.close()


def test_nequi_con_tilde_y_variaciones_voz():
    """
    Verifica que transcripciones de Siri con tildes ('Nequí'), modismos ('plata por Nequi')
    o variantes fonéticas resuelvan SIEMPRE a Nequi y NUNCA a Efectivo.
    """
    db = TestingSessionLocal()
    nequi = db.query(Cuenta).filter(Cuenta.nombre.ilike("%nequi%")).first()
    if not nequi:
        nequi = Cuenta(nombre="Nequi", tipo=TipoCuenta.DEBITO, saldo_actual=200000.0)
        db.add(nequi)
        db.commit()

    frases_nequi = [
        "Pagué 15 mil en Nequí",
        "Pagué 15 mil en Nequi.",
        "Mandé plata por Nequi 25 mil",
        "15 mil de taxi por Nequí",
        "Almuerzo 20k en Nequí",
        "gasté una plata en Nequi",
        "plata de nequi 15 mil",
        "nequi 50000",
        "pagué con nequi 10 mil"
    ]

    for f in frases_nequi:
        res = NLPSmartExpenseParser.interpretar_texto_gasto(f, db)
        assert res["cuenta_nombre"] == nequi.nombre, f"Falló '{f}': se resolvió a {res['cuenta_nombre']} en vez de Nequi"
        assert "efectivo" not in res["cuenta_nombre"].lower()

    db.close()


def test_diferenciacion_estricta_nequi_vs_efectivo_en_api(client):
    """
    Valida a nivel de endpoint API (/ia-rapida) que:
    1. Un gasto en Nequi debita únicamente de Nequi y deja Efectivo intacto.
    2. Un gasto en Efectivo debita únicamente de Efectivo y deja Nequi intacto.
    """
    db = TestingSessionLocal()
    # Asegurar cuentas iniciales
    c_nequi = db.query(Cuenta).filter(Cuenta.nombre.ilike("%nequi%")).first()
    if not c_nequi:
        c_nequi = Cuenta(nombre="Nequi", tipo=TipoCuenta.DEBITO, saldo_actual=100000.0)
        db.add(c_nequi)
        db.commit()
    else:
        c_nequi.saldo_actual = 100000.0
        db.commit()

    c_efectivo = db.query(Cuenta).filter(Cuenta.tipo == TipoCuenta.EFECTIVO).first()
    c_efectivo.saldo_actual = 50000.0
    db.commit()
    db.close()

    # 1. Gasto por voz en Nequi (usando tilde 'Nequí' común en dictado Siri)
    res_neq = client.post("/api/v1/transacciones/ia-rapida", json={"texto": "Pagué 20 mil de almuerzo en Nequí"})
    assert res_neq.status_code == 200
    data_neq = res_neq.json()
    assert data_neq["status"] == "registrado"
    assert data_neq["cuenta"] == "Nequi"
    assert data_neq["saldo_cuenta_actual"] == 80000.0  # 100k - 20k

    # Verificar que Efectivo no se tocó
    db = TestingSessionLocal()
    ef_check = db.query(Cuenta).filter(Cuenta.tipo == TipoCuenta.EFECTIVO).first()
    assert ef_check.saldo_actual == 50000.0
    db.close()

    # 2. Gasto por voz en Efectivo
    res_ef = client.post("/api/v1/transacciones/ia-rapida", json={"texto": "Pagué 10 mil de taxi en efectivo"})
    assert res_ef.status_code == 200
    data_ef = res_ef.json()
    assert data_ef["status"] == "registrado"
    assert "efectivo" in data_ef["cuenta"].lower()
    assert data_ef["saldo_cuenta_actual"] == 40000.0  # 50k - 10k

    # Verificar que Nequi no se tocó en el segundo movimiento
    db = TestingSessionLocal()
    neq_check = db.query(Cuenta).filter(Cuenta.nombre.ilike("%nequi%")).first()
    assert neq_check.saldo_actual == 80000.0
    db.close()


def test_auto_aprovisionar_nequi_si_no_existe_y_evitar_efectivo(client):
    """
    Si el usuario sólo tiene Billetera Efectivo creada en su app y dice por voz
    'Pagué 15 mil en Nequi', el sistema NO debe debitar de Efectivo; debe auto-aprovisionar
    la cuenta Nequi para no corromper la plata física.
    """
    db = TestingSessionLocal()
    # Dejar sólo la cuenta de efectivo
    db.query(Cuenta).filter(Cuenta.nombre != "Billetera Efectivo").delete()
    ef = db.query(Cuenta).filter(Cuenta.nombre == "Billetera Efectivo").first()
    if not ef:
        ef = Cuenta(nombre="Billetera Efectivo", tipo=TipoCuenta.EFECTIVO, saldo_actual=50000.0)
        db.add(ef)
    ef.saldo_actual = 50000.0
    db.commit()
    db.close()

    # El usuario envía comando por voz mencionando Nequi
    res = client.post("/api/v1/transacciones/ia-rapida", json={"texto": "Pagué 15 mil en Nequí"})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "registrado"
    assert data["cuenta"] == "Nequi"

    # Verificar que Efectivo quedó INTACTO en 50.000
    db = TestingSessionLocal()
    ef_despues = db.query(Cuenta).filter(Cuenta.nombre == "Billetera Efectivo").first()
    assert ef_despues.saldo_actual == 50000.0
    db.close()


def test_ia_rapida_formatos_cuerpo_atajos(client):
    """
    Verifica que /ia-rapida acepte peticiones desde Atajos de iOS sin importar si se envían como:
    1. Texto plano crudo en el body.
    2. Formulario urlencoded crudo.
    3. Frase donde no se detectó monto (debe devolver status: 'error' con clave 'mensaje' para Siri).
    """
    # 1. Texto plano directo en el body
    res_raw = client.post("/api/v1/transacciones/ia-rapida", content=b"Pague 25 mil en Bancolombia", headers={"Content-Type": "text/plain"})
    assert res_raw.status_code == 200
    assert res_raw.json()["status"] == "registrado"
    assert res_raw.json()["monto"] == 25000.0

    # 2. Formulario crudo en el body
    res_form = client.post("/api/v1/transacciones/ia-rapida", content=b"texto=Almuerzo+18000+en+Bancolombia", headers={"Content-Type": "application/x-www-form-urlencoded"})
    assert res_form.status_code == 200
    assert res_form.json()["status"] == "registrado"
    assert res_form.json()["monto"] == 18000.0

    # 3. Monto no detectado (Siri recibe el mensaje amigable en vez de error 400)
    res_err = client.post("/api/v1/transacciones/ia-rapida", json={"texto": "Hola Siri"})
    assert res_err.status_code == 200
    assert res_err.json()["status"] == "error"
    assert "mensaje" in res_err.json()
    assert "No detecté el monto" in res_err.json()["mensaje"]


def test_nlp_reconocimiento_amplio_ingresos_y_gastos():
    """
    Verifica que el parser diferencie de forma natural y robusta entre gastos e ingresos
    en expresiones cotidianas colombianas sin requerir forzar parámetros.
    """
    db = TestingSessionLocal()
    casos = [
        ("Ingresaron 100 mil a Bancolombia", "INGRESO", 100000.0, "Bancolombia Principal"),
        ("Entraron 200 mil a Bancolombia", "INGRESO", 200000.0, "Bancolombia Principal"),
        ("Venta de 80 mil en efectivo", "INGRESO", 80000.0, "Billetera Efectivo"),
        ("Cobro de 50 mil en efectivo", "INGRESO", 50000.0, "Billetera Efectivo"),
        ("Me devolvieron 30 mil en Nequi", "INGRESO", 30000.0, "Nequi"),
        ("Plata que me debian 50 mil en Nequi", "INGRESO", 50000.0, "Nequi"),
        ("Sueldo de 2 millones en Bancolombia", "INGRESO", 2000000.0, "Bancolombia Principal"),
        ("Gasto de 15 mil en efectivo", "EGRESO", 15000.0, "Billetera Efectivo"),
        ("Gasto 20 mil en Nequi", "EGRESO", 20000.0, "Nequi"),
        ("Pagué 15 mil en Nequi", "EGRESO", 15000.0, "Nequi"),
        ("Taxi 12 mil en efectivo", "EGRESO", 12000.0, "Billetera Efectivo"),
    ]
    for frase, tipo_esperado, monto_esperado, cuenta_esperada in casos:
        res = NLPSmartExpenseParser.interpretar_texto_gasto(frase, db)
        assert res["tipo"] == tipo_esperado, f"Fallo en tipo para '{frase}': esperado {tipo_esperado}, obtenido {res['tipo']}"
        assert res["monto"] == monto_esperado, f"Fallo en monto para '{frase}': esperado {monto_esperado}, obtenido {res['monto']}"
        if cuenta_esperada:
            assert res["cuenta_nombre"] == cuenta_esperada, f"Fallo en cuenta para '{frase}': esperado {cuenta_esperada}, obtenido {res['cuenta_nombre']}"
    db.close()


def test_ia_rapida_con_parametro_tipo_alias(client):
    """
    Verifica que el endpoint /ia-rapida respete el parámetro tipo
    con alias como 'gasto', 'GASTO', 'ingreso', 'INGRESO', 'entrada', tanto en GET como en POST.
    """
    # 1. GET con tipo=gasto
    res1 = client.get("/api/v1/transacciones/ia-rapida?texto=15000 en Nequi&tipo=gasto")
    assert res1.status_code == 200
    d1 = res1.json()
    assert d1["status"] == "registrado"
    assert d1["tipo"] == "EGRESO"
    assert d1["monto"] == 15000.0

    # 2. GET con tipo=ingreso
    res2 = client.get("/api/v1/transacciones/ia-rapida?texto=50000 en Nequi&tipo=ingreso")
    assert res2.status_code == 200
    d2 = res2.json()
    assert d2["status"] == "registrado"
    assert d2["tipo"] == "INGRESO"
    assert d2["monto"] == 50000.0

    # 3. POST JSON con tipo='GASTO'
    res3 = client.post("/api/v1/transacciones/ia-rapida", json={"texto": "20000 en efectivo", "tipo": "GASTO"})
    assert res3.status_code == 200
    d3 = res3.json()
    assert d3["status"] == "registrado"
    assert d3["tipo"] == "EGRESO"
    assert d3["monto"] == 20000.0

    # 4. POST Form con tipo='entrada'
    res4 = client.post("/api/v1/transacciones/ia-rapida", content=b"texto=100000+en+Bancolombia&tipo=entrada", headers={"Content-Type": "application/x-www-form-urlencoded"})
    assert res4.status_code == 200
    d4 = res4.json()
    assert d4["status"] == "registrado"
    assert d4["tipo"] == "INGRESO"
    assert d4["monto"] == 100000.0


def test_ia_rapida_flujo_validaciones_prioritarias(client):
    """
    Verifica la regla de negocio:
    1. Si el usuario dice '20 mil en Nequi' sin especificar ingreso o gasto,
       el sistema debe preguntar primero '¿Es un ingreso o es un gasto?' (status: requiere_tipo).
    2. Al responder con tipo='gasto', como la cuenta ya se conocía (Nequi), debe registrar de inmediato.
    3. Si el usuario dice '30 mil' (sin tipo ni cuenta):
       - Primero debe preguntar si es ingreso o gasto (status: requiere_tipo).
       - Al responder el tipo, debe preguntar '¿De qué cuenta lo pagaste?' (status: requiere_cuenta).
       - Al dar la cuenta, debe registrar exitosamente.
    """
    # 1. Frase ambigua '20 mil en Nequi' -> solicita tipo
    res1 = client.post("/api/v1/transacciones/ia-rapida", json={"texto": "20 mil en Nequi"})
    assert res1.status_code == 200
    d1 = res1.json()
    assert d1["status"] == "requiere_tipo"
    assert "¿Es un ingreso o es un gasto?" in d1["mensaje"]
    assert d1["cuenta_nombre"] == "Nequi"
    assert d1["monto"] == 20000.0

    # 2. Responde 'gasto' -> Registra directamente porque Nequi ya estaba detectado
    res2 = client.post("/api/v1/transacciones/ia-rapida", json={"texto": "20 mil en Nequi", "tipo": "gasto"})
    assert res2.status_code == 200
    d2 = res2.json()
    assert d2["status"] == "registrado"
    assert d2["tipo"] == "EGRESO"
    assert d2["monto"] == 20000.0
    assert d2["cuenta"] == "Nequi"

    # 3. Frase '30 mil' (ni tipo ni cuenta) -> Pregunta primero tipo
    res3 = client.post("/api/v1/transacciones/ia-rapida", json={"texto": "30 mil"})
    assert res3.status_code == 200
    d3 = res3.json()
    assert d3["status"] == "requiere_tipo"

    # 4. Al indicar tipo pero aún sin cuenta -> Pregunta por la cuenta
    res4 = client.post("/api/v1/transacciones/ia-rapida", json={"texto": "30 mil", "tipo": "gasto"})
    assert res4.status_code == 200
    d4 = res4.json()
    assert d4["status"] == "requiere_cuenta"
    assert "¿De qué cuenta" in d4["mensaje"]

    # 5. Al proveer la cuenta -> Registra
    res5 = client.post("/api/v1/transacciones/ia-rapida", json={"texto": "30 mil en efectivo", "tipo": "gasto"})
    assert res5.status_code == 200
    d5 = res5.json()
    assert d5["status"] == "registrado"
    assert d5["cuenta"] == "Billetera Efectivo"





