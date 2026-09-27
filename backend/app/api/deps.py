from typing import Optional
from fastapi import Header, Depends
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models import Usuario


def get_current_user_id(
    x_usuario_id: Optional[str] = Header(None, alias="X-Usuario-Id"),
    db: Session = Depends(get_db)
) -> Optional[int]:
    """
    Identifica al usuario actual para soporte multi-usuario personal mediante el header X-Usuario-Id.
    Si no se provee, retorna el primer usuario registrado o None para máxima retrocompatibilidad con tests.
    """
    if x_usuario_id:
        try:
            uid = int(x_usuario_id)
            user = db.query(Usuario).filter(Usuario.id == uid).first()
            if user:
                return user.id
        except ValueError:
            pass

    primer = db.query(Usuario).first()
    return primer.id if primer else None
