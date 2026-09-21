import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.database import Base, get_db
from backend.app.main import app
from sqlalchemy.pool import StaticPool
import backend.app.models  # Importa todos los modelos para registrar las tablas en Base.metadata
from backend.app.models import Cuenta, TipoCuenta, TipoTransaccion, PerfilFinanciero

# Base de datos de prueba en memoria compartida
test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
Base.metadata.create_all(bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()
    
    # Crear cuentas iniciales
    c_debito = Cuenta(nombre="Bancolombia Principal", tipo=TipoCuenta.DEBITO, saldo_actual=1000000.0)
    c_credito = Cuenta(nombre="Tarjeta Visa", tipo=TipoCuenta.CREDITO, saldo_actual=0.0, cupo_total=3000000.0)
    c_efectivo = Cuenta(nombre="Billetera Efectivo", tipo=TipoCuenta.EFECTIVO, saldo_actual=50000.0)
    db.add_all([c_debito, c_credito, c_efectivo])
    db.commit()
    db.close()


def test_listar_cuentas_api():
    response = client.get("/api/v1/cuentas")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 3
    nombres = [c["nombre"] for c in data]
    assert "Bancolombia Principal" in nombres


def test_webhook_apple_pay():
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


def test_webhook_sms_retiro_cajero_transferencia_interna():
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


def test_webhook_idempotencia():
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


def test_obtener_metricas_semaforo():
    response = client.get("/api/v1/metricas/semaforo")
    assert response.status_code == 200
    data = response.json()
    assert data["color"] in ["VERDE", "AMARILLO", "ROJO"]
    assert "dias_restantes" in data
    assert "limite_gasto_diario_sugerido" in data
