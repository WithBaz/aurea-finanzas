import pytest
from backend.app.services.sms_parser import SMSParser, limpiar_monto


def test_limpiar_monto_colombiano():
    assert limpiar_monto("$45.000") == 45000.0
    assert limpiar_monto("$ 1.250.000 COP") == 1250000.0
    assert limpiar_monto("200.000") == 200000.0
    assert limpiar_monto("$15.500,50") == 15500.50
    assert limpiar_monto("") == 0.0


def test_parse_bancolombia_compra_debito():
    sms = "Bancolombia le informa compra por $45.000 con T.Deb *1234 en D1 CALLE 53 a las 14:30. 21/09/2026."
    res = SMSParser.parse_sms(sms)
    assert res["es_valido"] is True
    assert res["tipo"] == "EGRESO"
    assert res["monto"] == 45000.0
    assert "D1" in res["comercio"]
    assert res["es_credito"] is False
    assert res["es_retiro_cajero"] is False


def test_parse_bancolombia_compra_credito():
    sms = "Bancolombia le informa compra por $180.000 con T.Cred *5678 en ZARA CC TITAN a las 18:20. 21/09/2026."
    res = SMSParser.parse_sms(sms)
    assert res["es_valido"] is True
    assert res["tipo"] == "EGRESO"
    assert res["monto"] == 180000.0
    assert "ZARA" in res["comercio"]
    assert res["es_credito"] is True


def test_parse_bancolombia_retiro_cajero():
    sms = "Bancolombia le informa retiro por $200.000 en CAJERO EXITO a las 10:15. 21/09/2026. Saldo $1.800.000"
    res = SMSParser.parse_sms(sms)
    assert res["es_valido"] is True
    assert res["tipo"] == "TRANSFERENCIA_INTERNA"
    assert res["monto"] == 200000.0
    assert res["es_retiro_cajero"] is True


def test_parse_bancolombia_transferencia_recibida():
    sms = "Bancolombia le informa transferencia recibida de SEBASTIAN FLOREZ por $350.000 el 21/09/2026"
    res = SMSParser.parse_sms(sms)
    assert res["es_valido"] is True
    assert res["tipo"] == "INGRESO"
    assert res["monto"] == 350000.0
    assert "SEBASTIAN FLOREZ" in res["comercio"]


def test_parse_nequi_pago():
    sms = "Pagaste $18.000 a RESTAURANTE EL CORRAL con Nequi. Tu saldo disponible es $120.000"
    res = SMSParser.parse_sms(sms)
    assert res["es_valido"] is True
    assert res["tipo"] == "EGRESO"
    assert res["monto"] == 18000.0


def test_parse_nequi_recibido():
    sms = "Te enviaron $85.000 de parte de MARIA GOMEZ. ¡Disfrútalos!"
    res = SMSParser.parse_sms(sms)
    assert res["es_valido"] is True
    assert res["tipo"] == "INGRESO"
    assert res["monto"] == 85000.0


def test_parse_daviplata_pago():
    sms = "DaviPlata le informa que paso plata por $30.000 a 3101234567. Nuevo saldo $45.000."
    res = SMSParser.parse_sms(sms)
    assert res["es_valido"] is True
    assert res["tipo"] == "EGRESO"
    assert res["monto"] == 30000.0
