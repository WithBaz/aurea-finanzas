from datetime import datetime, timezone, timedelta
from typing import Optional, Union

# Colombia Time (COT) es UTC-5 de forma permanente todo el año (sin Daylight Saving Time).
COLOMBIA_TZ = timezone(timedelta(hours=-5))


def ahora_colombia() -> datetime:
    """
    Retorna la fecha y hora actual en la zona horaria oficial de Colombia (UTC-5).
    """
    return datetime.now(COLOMBIA_TZ)


def ahora_utc_db() -> datetime:
    """
    Retorna la fecha y hora actual en UTC naive para almacenamiento estándar en SQL.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)


def db_dt_to_colombia(dt: Optional[datetime]) -> Optional[datetime]:
    """
    Convierte una fecha leída de la base de datos (donde los registros DateTime
    se almacenan en UTC) a la hora oficial de Colombia (UTC-5).
    
    - Si dt es None: retorna None.
    - Si dt es naive (como devuelve SQLite o PostgreSQL timestamp without time zone):
      los valores de hora representan UTC. Se asocia timezone.utc y se traslada con
      astimezone(COLOMBIA_TZ), restando exactamente las 5 horas de diferencia.
    - Si dt ya tiene timezone (aware):
      se convierte matemáticamente a UTC-5 usando astimezone(COLOMBIA_TZ).
    """
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc).astimezone(COLOMBIA_TZ)
    return dt.astimezone(COLOMBIA_TZ)


# Alias
to_colombia_tz = db_dt_to_colombia


def formatear_fecha_iso_colombia(dt: Optional[datetime]) -> Optional[str]:
    """
    Retorna la cadena ISO 8601 con el offset explícito de Colombia (-05:00),
    asegurando que cualquier cliente web o móvil interprete exactamente
    la fecha y hora colombiana.
    """
    if dt is None:
        return None
    col_dt = db_dt_to_colombia(dt)
    return col_dt.isoformat() if col_dt else None


def parsear_fecha_para_db(val: Union[str, datetime, None]) -> datetime:
    """
    Parsea una fecha proveniente de parámetros de URL, Atajos de Apple o JSON,
    y la normaliza a UTC naive para ser persistida en la base de datos.
    - Si val es None: retorna la hora actual en UTC naive.
    - Si es string: lo parsea. Si viene sin zona horaria, se asume hora de Colombia.
    - Retorna datetime en UTC naive listo para SQLAlchemy / SQLite / Postgres.
    """
    if val is None:
        return ahora_utc_db()

    if isinstance(val, datetime):
        dt = val
    elif isinstance(val, str):
        val_clean = val.strip()
        if not val_clean:
            return ahora_utc_db()
        try:
            dt = datetime.fromisoformat(val_clean.replace("Z", "+00:00"))
        except Exception:
            try:
                from dateutil import parser
                dt = parser.parse(val_clean)
            except Exception:
                return ahora_utc_db()
    else:
        return ahora_utc_db()

    # Si es naive, se interpreta que el usuario la registró en hora local de Colombia
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=COLOMBIA_TZ)

    # Convertir a UTC y guardar naive
    return dt.astimezone(timezone.utc).replace(tzinfo=None)


def parsear_fecha_colombia(val: Union[str, datetime, None]) -> Optional[datetime]:
    """
    Parsea una fecha y la retorna como datetime timezone-aware en zona de Colombia (UTC-5).
    """
    if val is None:
        return None
    utc_dt = parsear_fecha_para_db(val)
    return utc_dt.replace(tzinfo=timezone.utc).astimezone(COLOMBIA_TZ)
