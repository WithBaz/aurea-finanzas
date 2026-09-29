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
            # Si también se envía X-Usuario-Id, verificar que no haya discrepancia / suplantación
            if x_usuario_id:
                try:
                    if int(x_usuario_id) != user.id:
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail="Discrepancia de seguridad: el token no corresponde al X-Usuario-Id especificado."
                        )
                except ValueError:
                    pass
            return user.id
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de sesión inválido o expirado."
        )

    # 2. Si no hay token, NO confiar jamás en X-Usuario-Id en solitario (previene Header Spoofing / Account Takeover)
    total_usuarios = db.query(Usuario).count()
    if total_usuarios == 0:
        # Modo instalación / pre-autenticación / tests unitarios base sin usuarios
        return None

    # Si hay usuarios registrados y no se presentó token válido, el usuario NO está autenticado
    return None


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


def check_auth_if_users_exist(
    current_uid: Optional[int],
    db: Session,
    recurso: str = "este recurso"
):
    """
    Valida que, si existen usuarios en la base de datos, la petición esté debidamente autenticada.
    Si no lo está, lanza 401 Unauthorized para evitar fugas de información o manipulación anónima.
    """
    total_usuarios = db.query(Usuario).count()
    if total_usuarios > 0 and current_uid is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Autenticación requerida para acceder a {recurso}."
        )

