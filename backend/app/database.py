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
    Garantiza que la tabla de usuarios y las columnas usuario_id existan
    en SQLite local o PostgreSQL en la nube de forma segura e idempotente.
    """
    from sqlalchemy import text, inspect
    try:
        # Asegurar creación de tablas
        Base.metadata.create_all(bind=eng)

        inspector = inspect(eng)
        dialect_name = eng.dialect.name
        tables_to_update = ['cuentas', 'transacciones', 'gastos_fijos', 'perfil_financiero', 'metas_ahorro', 'usuarios']

        with eng.begin() as conn:
            existing_tables = inspector.get_table_names()
            for table in tables_to_update:
                if table in existing_tables:
                    existing_cols = [c['name'] for c in inspector.get_columns(table)]
                    if table != 'usuarios' and 'usuario_id' not in existing_cols:
                        if dialect_name == 'sqlite':
                            conn.execute(text(f"ALTER TABLE {table} ADD COLUMN usuario_id INTEGER;"))
                        else:
                            conn.execute(text(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS usuario_id INTEGER;"))
                    if table == 'usuarios' and 'biometric_token' not in existing_cols:
                        if dialect_name == 'sqlite':
                            conn.execute(text(f"ALTER TABLE {table} ADD COLUMN biometric_token VARCHAR(256);"))
                        else:
                            conn.execute(text(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS biometric_token VARCHAR(256);"))

            # Si ya existen usuarios, asociar registros huérfanos anteriores al primer usuario
            if 'usuarios' in existing_tables:
                first_user_res = conn.execute(text("SELECT id FROM usuarios ORDER BY id ASC LIMIT 1;")).fetchone()
                if first_user_res:
                    first_uid = first_user_res[0]
                    for table in ['cuentas', 'transacciones', 'gastos_fijos', 'perfil_financiero', 'metas_ahorro']:
                        if table in existing_tables:
                            conn.execute(text(f"UPDATE {table} SET usuario_id = :uid WHERE usuario_id IS NULL;"), {"uid": first_uid})
    except Exception as e:
        import logging
        logging.warning(f"Nota de migración esquema: {e}")


