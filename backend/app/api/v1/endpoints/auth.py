import hashlib
import secrets
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models import Usuario, PerfilFinanciero
from backend.app.schemas import (
    UsuarioRegistro,
    UsuarioLogin,
    FaceIdLogin,
    UsuarioEstado,
    UsuarioPerfil,
    UsuarioCambiarPin,
    FaceIdToggle,
)
from backend.app.api.deps import get_current_user_id

router = APIRouter()

SALT = "AUREA_COLOMBIA_SALT_2026"


def calcular_hash_pin(pin: str) -> str:
    cadena = f"{SALT}_{pin.strip()}"
    return hashlib.sha256(cadena.encode("utf-8")).hexdigest()


@router.get("/estado", response_model=UsuarioEstado)
def obtener_estado_auth(
    current_uid: Optional[int] = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Retorna el estado de registro y la lista de todos los perfiles de usuario disponibles en AUREA.
    """
    usuarios = db.query(Usuario).order_by(Usuario.id.asc()).all()
    if not usuarios:
        return UsuarioEstado(registrado=False, username=None, face_id_enabled=False, usuarios=[])

    usuario_activo = None
    if current_uid:
        usuario_activo = next((u for u in usuarios if u.id == current_uid), None)
    if not usuario_activo:
        usuario_activo = usuarios[0]

    return UsuarioEstado(
        registrado=True,
        username=usuario_activo.username,
        face_id_enabled=usuario_activo.face_id_enabled,
        usuarios=[
            UsuarioPerfil(
                id=u.id,
                username=u.username,
                face_id_enabled=u.face_id_enabled
            )
            for u in usuarios
        ]
    )


@router.get("/usuarios", response_model=List[UsuarioPerfil])
def listar_usuarios(db: Session = Depends(get_db)):
    """
    Lista todos los usuarios registrados para el selector de cuentas personal/amigos.
    """
    usuarios = db.query(Usuario).order_by(Usuario.id.asc()).all()
    return [
        UsuarioPerfil(
            id=u.id,
            username=u.username,
            face_id_enabled=u.face_id_enabled
        )
        for u in usuarios
    ]


@router.post("/registro", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
def registrar_usuario(
    payload: UsuarioRegistro,
    db: Session = Depends(get_db)
):
    """
    Registra una cuenta de usuario nueva e independiente (para el titular o un amigo).
    """
    if not payload.pin or len(payload.pin) < 4:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La contraseña debe tener al menos 4 caracteres."
        )

    clean_username = payload.username.strip()
    existente = db.query(Usuario).filter(Usuario.username.ilike(clean_username)).first()
    pin_hash = calcular_hash_pin(payload.pin)

    if existente:
        # Si ya existe con ese nombre, verificar si el PIN/contraseña coincide para iniciar sesión
        if existente.pin_hash == pin_hash:
            return {
                "status": "exitoso",
                "mensaje": f"Bienvenido de nuevo, {existente.username}.",
                "usuario_id": existente.id,
                "username": existente.username,
                "face_id_enabled": existente.face_id_enabled,
                "biometric_token": existente.biometric_token
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El usuario '{clean_username}' ya existe. Si eres tú, ingresa con tu contraseña habitual."
            )

    token = secrets.token_hex(24)
    nuevo_usuario = Usuario(
        username=clean_username,
        pin_hash=pin_hash,
        face_id_enabled=False,
        biometric_token=token
    )
    db.add(nuevo_usuario)
    db.commit()
    db.refresh(nuevo_usuario)

    # Crear perfil financiero inicial en limpio para este usuario
    perfil = PerfilFinanciero(
        usuario_id=nuevo_usuario.id,
        dia_pago_mensual=1,
        ingreso_mensual_estimado=0.0,
        compromisos_fijos_mensual=0.0,
        porcentaje_ahorro_meta=15.0,
        umbral_gasto_hormiga=25000.0
    )
    db.add(perfil)
    db.commit()

    return {
        "status": "exitoso",
        "mensaje": f"¡Bienvenido {nuevo_usuario.username}! Tu espacio financiero personal ha sido creado.",
        "usuario_id": nuevo_usuario.id,
        "username": nuevo_usuario.username,
        "face_id_enabled": False,
        "biometric_token": nuevo_usuario.biometric_token
    }


@router.post("/login", response_model=Dict[str, Any])
def iniciar_sesion(
    payload: UsuarioLogin,
    db: Session = Depends(get_db)
):
    """
    Verifica el PIN de 4 dígitos para desbloquear la sesión de un usuario específico.
    """
    usuario = None
    if payload.username:
        usuario = db.query(Usuario).filter(Usuario.username.ilike(payload.username.strip())).first()
    else:
        usuario = db.query(Usuario).first()

    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontró el usuario. Crea tu cuenta primero."
        )

    pin_hash = calcular_hash_pin(payload.pin)
    if pin_hash != usuario.pin_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Contraseña o PIN incorrecto. Intenta de nuevo."
        )

    if not usuario.biometric_token:
        usuario.biometric_token = secrets.token_hex(24)
        db.commit()

    return {
        "status": "autenticado",
        "mensaje": f"Bienvenido, {usuario.username}.",
        "usuario_id": usuario.id,
        "username": usuario.username,
        "face_id_enabled": usuario.face_id_enabled,
        "biometric_token": usuario.biometric_token
    }


@router.post("/face-id-login", response_model=Dict[str, Any])
def login_con_face_id(
    payload: Optional[FaceIdLogin] = None,
    current_uid: Optional[int] = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Verifica inicio de sesión biométrico (Face ID / Touch ID / Acceso Rápido).
    """
    usuario = None
    if payload and payload.username:
        usuario = db.query(Usuario).filter(Usuario.username.ilike(payload.username.strip())).first()
    elif current_uid:
        usuario = db.query(Usuario).filter(Usuario.id == current_uid).first()
    else:
        usuario = db.query(Usuario).first()

    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No hay usuario registrado."
        )

    if not usuario.biometric_token:
        usuario.biometric_token = secrets.token_hex(24)
        db.commit()

    return {
        "status": "autenticado",
        "mensaje": f"Desbloqueado con Face ID para {usuario.username}.",
        "usuario_id": usuario.id,
        "username": usuario.username,
        "face_id_enabled": True,
        "biometric_token": usuario.biometric_token
    }


@router.post("/face-id", response_model=Dict[str, Any])
def configurar_face_id(
    payload: FaceIdToggle,
    current_uid: Optional[int] = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Activa o desactiva Face ID para el usuario actual.
    """
    usuario = None
    if current_uid:
        usuario = db.query(Usuario).filter(Usuario.id == current_uid).first()
    else:
        usuario = db.query(Usuario).first()

    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No hay usuario registrado."
        )

    usuario.face_id_enabled = payload.enabled
    if payload.credential_id:
        usuario.face_id_credential_id = payload.credential_id
    if payload.enabled and not usuario.biometric_token:
        usuario.biometric_token = secrets.token_hex(24)

    db.commit()
    db.refresh(usuario)

    return {
        "status": "exitoso",
        "usuario_id": usuario.id,
        "face_id_enabled": usuario.face_id_enabled,
        "biometric_token": usuario.biometric_token,
        "mensaje": "Face ID activado exitosamente." if usuario.face_id_enabled else "Face ID desactivado."
    }


@router.post("/cambiar-pin", response_model=Dict[str, Any])
def cambiar_pin(
    payload: UsuarioCambiarPin,
    current_uid: Optional[int] = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Permite al usuario cambiar su PIN de 4 dígitos validando primero el actual.
    """
    usuario = None
    if current_uid:
        usuario = db.query(Usuario).filter(Usuario.id == current_uid).first()
    else:
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

    if len(payload.pin_nuevo) < 4:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La nueva contraseña debe tener al menos 4 caracteres."
        )

    usuario.pin_hash = calcular_hash_pin(payload.pin_nuevo)
    db.commit()
    return {"status": "exitoso", "mensaje": "Contraseña actualizada correctamente."}
