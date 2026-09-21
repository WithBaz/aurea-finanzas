from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models import MetaAhorro
from backend.app.schemas import MetaAhorroCreate, MetaAhorroResponse

router = APIRouter()


@router.get("", response_model=List[MetaAhorroResponse])
def listar_metas(db: Session = Depends(get_db)):
    """
    Lista las metas de ahorro y su avance en COP.
    """
    return db.query(MetaAhorro).all()


@router.post("", response_model=MetaAhorroResponse, status_code=status.HTTP_201_CREATED)
def crear_meta(meta_in: MetaAhorroCreate, db: Session = Depends(get_db)):
    meta = MetaAhorro(**meta_in.model_dump())
    db.add(meta)
    db.commit()
    db.refresh(meta)
    return meta
