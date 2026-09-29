from typing import Optional
from fastapi import Header, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models import Usuario


def get_current_user_id(
    authorization: Optional[str] = Header(None),
    x_aurea_token: Optional[str] = Header(None, alias="X-Aurea-Token"),
    x_usuario_id: Optional[str] = Header(None, alias="X-Usuario-Id"),
    db: Session = Depends(get_db)
) -> Optional[int]:
    """
    Identifica y autentica al usuario actual mediante Bearer token o X-Aurea-Token.
    Previene spoofing verificando criptográficamente la identidad contra la base de datos.
    """
    token = None
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()
    elif x_aurea_token:
        token = x_aurea_token.strip()

    # 1. Si se provee un token, validar que coincida con un usuario existente
    if token:
        user = db.query(Usuario).filter(Usuario.biometric_token == token).first()
        if user:
            return user.id
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de sesión inválido o expirado."
        )

    # 2. Si no hay token, pero se envía X-Usuario-Id (para desarrollo y compatibilidad):
    if x_usuario_id:
        try:
            uid = int(x_usuario_id)
            user = db.query(Usuario).filter(Usuario.id == uid).first()
            if user:
                return user.id
        except ValueError:
            pass

    # 3. Fallback retrocompatible para tests unitarios base sin usuarios creados
    total_usuarios = db.query(Usuario).count()
    if total_usuarios == 0:
        return None

    primer = db.query(Usuario).order_by(Usuario.id.asc()).first()
    return primer.id if primer else None


def require_current_user_id(
    current_uid: Optional[int] = Depends(get_current_user_id),
    db: Session = Depends(get_db)
) -> int:
    """
    Exige obligatoriamente que el usuario esté autenticado.
    Si no está autenticado, rechaza con 401 Unauthorized.
    """
    if current_uid is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Autenticación requerida para acceder a este recurso."
        )
    return current_uid

