from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.api.deps import get_current_user_id, check_auth_if_users_exist
from backend.app.models import MetaAhorro
from backend.app.schemas import MetaAhorroCreate, MetaAhorroResponse

router = APIRouter()


@router.get("", response_model=List[MetaAhorroResponse])
def listar_metas(
    db: Session = Depends(get_db),
    current_uid: Optional[int] = Depends(get_current_user_id)
):
    """
    Lista las metas de ahorro y su avance en COP.
    """
    check_auth_if_users_exist(current_uid, db, "tus metas de ahorro")
    query = db.query(MetaAhorro)
    if current_uid:
        query = query.filter((MetaAhorro.usuario_id == current_uid) | (MetaAhorro.usuario_id == None))
    return query.all()


@router.post("", response_model=MetaAhorroResponse, status_code=status.HTTP_201_CREATED)
def crear_meta(
    meta_in: MetaAhorroCreate,
    db: Session = Depends(get_db),
    current_uid: Optional[int] = Depends(get_current_user_id)
):
    check_auth_if_users_exist(current_uid, db, "crear metas de ahorro")
    meta = MetaAhorro(usuario_id=current_uid, **meta_in.model_dump())
    db.add(meta)
    db.commit()
    db.refresh(meta)
    return meta

