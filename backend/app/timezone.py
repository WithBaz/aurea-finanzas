from datetime import datetime, timezone, timedelta
from typing import Optional, Union

# Colombia Time (COT) es UTC-5 de forma permanente todo el año (sin Daylight Saving Time).
# Esto evita problemas con dependencias externas como tzdata en sistemas operativos Windows o Linux mínimos.
COLOMBIA_TZ = timezone(timedelta(hours=-5))


def ahora_colombia() -> datetime:
    """
    Retorna la fecha y hora actual en la zona horaria oficial de Colombia (UTC-5).
    """
    return datetime.now(COLOMBIA_TZ)


def to_colombia_tz(dt: Optional[datetime]) -> Optional[datetime]:
    """
    Normaliza cualquier datetime (naive o timezone-aware) a la zona horaria de Colombia (UTC-5).
    - Si es None: retorna None.
    - Si es naive (sin tzinfo): se asume que representa la hora local colombiana y se le asocia COLOMBIA_TZ.
    - Si es aware (con tzinfo, ej: UTC de PostgreSQL): se convierte con precisión matemática a UTC-5.
    """
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=COLOMBIA_TZ)
    return dt.astimezone(COLOMBIA_TZ)


def formatear_fecha_iso_colombia(dt: Optional[datetime]) -> Optional[str]:
    """
    Retorna la cadena ISO 8601 con el offset explícito de Colombia (-05:00),
    garantizando que tanto navegadores web (Safari/Chrome) como clientes móviles
    y atajos de iOS interpreten exactamente la fecha y hora colombiana.
    """
    if dt is None:
        return None
    col_dt = to_colombia_tz(dt)
    return col_dt.isoformat() if col_dt else None


def parsear_fecha_colombia(val: Union[str, datetime, None]) -> Optional[datetime]:
    """
    Parsea una fecha proveniente de parámetros de URL, Atajos de Apple o JSON,
    asegurando que quede localizada en la zona horaria de Colombia.
    """
    if val is None:
        return None
    if isinstance(val, datetime):
        return to_colombia_tz(val)
    if isinstance(val, str):
        val_clean = val.strip()
        if not val_clean:
            return None
        try:
            # Soporta formato ISO 8601 nativo
            dt = datetime.fromisoformat(val_clean.replace("Z", "+00:00"))
            return to_colombia_tz(dt)
        except Exception:
            try:
                from dateutil import parser
                dt = parser.parse(val_clean)
                return to_colombia_tz(dt)
            except Exception:
                return ahora_colombia()
    return ahora_colombia()
