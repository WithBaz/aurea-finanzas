import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = (
    os.getenv("DATABASE_URL")
    or os.getenv("POSTGRES_URL")
    or os.getenv("POSTGRES_PRISMA_URL")
    or os.getenv("POSTGRES_URL_NON_POOLING")
)
if not DATABASE_URL:
    if os.getenv("VERCEL"):
        DATABASE_URL = "sqlite:////tmp/aurea_finanzas.db"
    else:
        DATABASE_URL = "sqlite:///./aurea_finanzas.db"

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg2://", 1)
elif DATABASE_URL.startswith("postgresql://") and not DATABASE_URL.startswith("postgresql+"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)

is_sqlite = "sqlite" in DATABASE_URL

engine_kwargs = {}
if is_sqlite:
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    # Configuración de resiliencia para PostgreSQL (Neon / Supabase / Vercel Postgres)
    engine_kwargs["pool_pre_ping"] = True
    engine_kwargs["pool_recycle"] = 300
    engine_kwargs["connect_args"] = {"connect_timeout": 5}

engine = create_engine(
    DATABASE_URL,
    **engine_kwargs,
    echo=False,
)

# Activar claves foráneas en SQLite
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if "sqlite" in DATABASE_URL:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON;")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def migrar_esquema_multi_usuario(eng=engine):
    """
    Garantiza que la tabla de usuarios y todas las columnas requeridas existan
    en SQLite local o PostgreSQL en la nube de forma segura, granular e idempotente.
    """
    from sqlalchemy import text, inspect
    import logging
    try:
        # Asegurar creación de tablas base
        Base.metadata.create_all(bind=eng)

        inspector = inspect(eng)
        dialect_name = eng.dialect.name
        is_pg = (dialect_name == "postgresql")
        time_type = "TIMESTAMP" if is_pg else "DATETIME"
        float_type = "FLOAT"
        int_type = "INTEGER"
        bool_type = "BOOLEAN"

        columnas_por_tabla = {
            "usuarios": [
                ("biometric_token", "VARCHAR(256)"),
                ("face_id_credential_id", "TEXT"),
            ],
            "cuentas": [
                ("usuario_id", int_type),
                ("cupo_total", f"{float_type} DEFAULT 0.0"),
                ("saldo_al_corte", f"{float_type} DEFAULT 0.0"),
                ("fecha_ultimo_corte", time_type),
                ("fecha_ultimo_pago", time_type),
                ("estado_corte", "VARCHAR(30) DEFAULT 'AL_DIA'"),
                ("tasa_ea", f"{float_type} DEFAULT 0.0"),
                ("dia_corte", int_type),
                ("dia_limite_pago", int_type),
            ],
            "transacciones": [
                ("usuario_id", int_type),
                ("cuotas_totales", f"{int_type} DEFAULT 1"),
                ("cuota_actual", f"{int_type} DEFAULT 1"),
                ("es_gasto_hormiga", f"{bool_type} DEFAULT FALSE"),
            ],
            "gastos_fijos": [
                ("usuario_id", int_type),
                ("pagado_este_mes", f"{bool_type} DEFAULT FALSE"),
                ("es_frecuente", f"{bool_type} DEFAULT FALSE"),
                ("frecuencia_veces", f"{int_type} DEFAULT 1"),
                ("veces_pagadas", f"{int_type} DEFAULT 0"),
                ("ultimo_mes_pagado", "VARCHAR(7)"),
                ("ultima_transaccion_id", int_type),
            ],
            "perfil_financiero": [
                ("usuario_id", int_type),
            ],
            "metas_ahorro": [
                ("usuario_id", int_type),
            ],
        }

        existing_tables = inspector.get_table_names()
        for table, cols in columnas_por_tabla.items():
            if table not in existing_tables:
                continue
            existing_cols = [c["name"] for c in inspector.get_columns(table)]
            for col_name, col_def in cols:
                if col_name not in existing_cols:
                    try:
                        with eng.begin() as conn:
                            if is_pg:
                                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {col_name} {col_def};"))
                            else:
                                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_def};"))
                    except Exception as err_col:
                        logging.warning(f"Aviso migración {table}.{col_name}: {err_col}")

        # Si ya existen usuarios, asociar registros huérfanos anteriores al primer usuario
        if "usuarios" in existing_tables:
            try:
                with eng.begin() as conn:
                    first_user_res = conn.execute(text("SELECT id FROM usuarios ORDER BY id ASC LIMIT 1;")).fetchone()
                    if first_user_res:
                        first_uid = first_user_res[0]
                        for table in ["cuentas", "transacciones", "gastos_fijos", "perfil_financiero", "metas_ahorro"]:
                            if table in existing_tables:
                                try:
                                    conn.execute(text(f"UPDATE {table} SET usuario_id = :uid WHERE usuario_id IS NULL;"), {"uid": first_uid})
                                except Exception:
                                    pass
            except Exception as err_orphan:
                logging.warning(f"Aviso asociar huérfanos: {err_orphan}")

    except Exception as e:
        logging.warning(f"Nota de migración esquema general: {e}")



