import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from backend.app.database import Base, get_db
from backend.app.main import app
import backend.app.models
from backend.app.models import Cuenta, TipoCuenta

test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()
    c_debito = Cuenta(nombre="Bancolombia Principal", tipo=TipoCuenta.DEBITO, saldo_actual=1000000.0)
    c_credito = Cuenta(nombre="Tarjeta Visa", tipo=TipoCuenta.CREDITO, saldo_actual=0.0, cupo_total=3000000.0)
    c_efectivo = Cuenta(nombre="Billetera Efectivo", tipo=TipoCuenta.EFECTIVO, saldo_actual=50000.0)
    db.add_all([c_debito, c_credito, c_efectivo])
    db.commit()
    db.close()
    yield
