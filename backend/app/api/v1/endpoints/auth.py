import hashlib
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models import Usuario
from backend.app.schemas import (
    UsuarioRegistro,
    UsuarioLogin,
    UsuarioEstado,
    UsuarioCambiarPin,
    FaceIdToggle,
)

router = APIRouter()

SALT = "AUREA_COLOMBIA_SALT_2026"


def calcular_hash_pin(pin: str) -> str:
    cadena = f"{SALT}_{pin.strip()}"
    return hashlib.sha256(cadena.encode("utf-8")).hexdigest()


@router.get("/estado", response_model=UsuarioEstado)
def obtener_estado_auth(db: Session = Depends(get_db)):
    """
    Retorna si ya existe un usuario registrado en el sistema y si Face ID está activado.
    Permite a la app móvil saber si mostrar pantalla de Registro inicial o Login con PIN/Face ID.
    """
    usuario = db.query(Usuario).first()
    if not usuario:
        return UsuarioEstado(registrado=False, username=None, face_id_enabled=False)
    return UsuarioEstado(
        registrado=True,
        username=usuario.username,
        face_id_enabled=usuario.face_id_enabled,
    )


@router.post("/registro", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
def registrar_usuario(
    payload: UsuarioRegistro,
    db: Session = Depends(get_db)
):
    """
    Registra el usuario inicial con su nombre y PIN de 4 dígitos.
    """
    if len(payload.pin) != 4 or not payload.pin.isdigit():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El PIN debe ser exactamente de 4 dígitos numéricos."
        )

    usuario = db.query(Usuario).first()
    pin_hash = calcular_hash_pin(payload.pin)

    if usuario:
        # Si ya existe, actualiza su configuración
        usuario.username = payload.username.strip()
        usuario.pin_hash = pin_hash
    else:
        usuario = Usuario(
            username=payload.username.strip(),
            pin_hash=pin_hash,
            face_id_enabled=False
        )
        db.add(usuario)

    db.commit()
    db.refresh(usuario)
    return {
        "status": "exitoso",
        "mensaje": f"¡Bienvenido {usuario.username}! Tu PIN de 4 dígitos ha sido configurado.",
        "username": usuario.username,
        "face_id_enabled": usuario.face_id_enabled
    }


@router.post("/login", response_model=Dict[str, Any])
def iniciar_sesion(
    payload: UsuarioLogin,
    db: Session = Depends(get_db)
):
    """
    Verifica el PIN de 4 dígitos para desbloquear la aplicación.
    """
    usuario = db.query(Usuario).first()
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No hay usuario registrado. Realiza el registro inicial primero."
        )

    pin_hash = calcular_hash_pin(payload.pin)
    if pin_hash != usuario.pin_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="PIN incorrecto. Intenta de nuevo."
        )

    return {
        "status": "autenticado",
        "mensaje": f"Bienvenido de nuevo, {usuario.username}.",
        "username": usuario.username,
        "face_id_enabled": usuario.face_id_enabled
    }


@router.post("/face-id-login", response_model=Dict[str, Any])
def login_con_face_id(db: Session = Depends(get_db)):
    """
    Verifica inicio de sesión cuando Face ID / Touch ID fue validado exitosamente en el dispositivo iPhone.
    """
    usuario = db.query(Usuario).first()
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No hay usuario registrado."
        )
    if not usuario.face_id_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Face ID no está activado para este usuario."
        )

    return {
        "status": "autenticado",
        "mensaje": f"Desbloqueado con Face ID para {usuario.username}.",
        "username": usuario.username,
        "face_id_enabled": True
    }


@router.post("/face-id", response_model=Dict[str, Any])
def configurar_face_id(
    payload: FaceIdToggle,
    db: Session = Depends(get_db)
):
    """
    Activa o desactiva Face ID para el usuario actual.
    """
    usuario = db.query(Usuario).first()
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No hay usuario registrado."
        )

    usuario.face_id_enabled = payload.enabled
    if payload.credential_id:
        usuario.face_id_credential_id = payload.credential_id
    db.commit()
    db.refresh(usuario)

    return {
        "status": "exitoso",
        "face_id_enabled": usuario.face_id_enabled,
        "mensaje": "Face ID activado exitosamente." if usuario.face_id_enabled else "Face ID desactivado."
    }


@router.post("/cambiar-pin", response_model=Dict[str, Any])
def cambiar_pin(
    payload: UsuarioCambiarPin,
    db: Session = Depends(get_db)
):
    """
    Permite al usuario cambiar su PIN de 4 dígitos validando primero el actual.
    """
    usuario = db.query(Usuario).first()
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No hay usuario registrado."
        )

    if calcular_hash_pin(payload.pin_actual) != usuario.pin_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="El PIN actual no coincide."
        )

    if len(payload.pin_nuevo) != 4 or not payload.pin_nuevo.isdigit():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El nuevo PIN debe ser exactamente de 4 dígitos numéricos."
        )

    usuario.pin_hash = calcular_hash_pin(payload.pin_nuevo)
    db.commit()
    return {"status": "exitoso", "mensaje": "PIN actualizado correctamente."}
