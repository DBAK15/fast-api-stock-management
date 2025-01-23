from datetime import datetime
from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .auth import get_current_user
from ..database import SessionLocal
from ..models import AuditLogs
from ..schemas import AuditLogRead, AuditLogCreate

router = APIRouter(
    prefix="/auditLogs",
    tags=["Audit Logs"],
)


# Dépendance pour récupérer la session de la base de données
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]


# Helper functions
def verify_user(user: dict) -> None:
    """
    Vérifie si l'utilisateur est authentifié.
    Lève une exception HTTP 401 si ce n'est pas le cas.
    """
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization failed"
        )


def log_user_action(db: db_dependency, user: user_dependency, log_action: AuditLogCreate):
    new_log = AuditLogs(**log_action.dict(), user_id=user.get('id'), created_by=user.get('id'))
    db.add(new_log)
    db.commit()
    db.refresh(new_log)
    return new_log


### Endpoints ###

@router.get("/", response_model=List[AuditLogRead])
async def read_all_logs(db: db_dependency, user: user_dependency):
    """
    Récupérer la liste de tous logs non supprimées.
    """
    verify_user(user)
    logs = db.query(AuditLogs).filter(AuditLogs.is_deleted == False).all()
    return logs


@router.get("/log/{log_id}", response_model=AuditLogRead)
async def read_log(log_id: int, db: db_dependency, user: user_dependency):
    """
    Récupérer un log spécifique par son ID.
    """
    verify_user(user)
    log = db.query(AuditLogs).filter(AuditLogs.id == log_id, AuditLogs.is_deleted == False).first()
    if not log:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Log not found")
    return log


@router.post("/log", response_model=AuditLogRead, status_code=status.HTTP_201_CREATED)
async def create_log(log: AuditLogCreate, db: db_dependency, user: user_dependency):
    """
    Créer un log d'audit.
    """
    verify_user(user)
    new_log = AuditLogs(**log.dict(), created_by=user["id"])
    db.add(new_log)
    db.commit()
    db.refresh(new_log)
    return new_log


@router.delete("/log/{log_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_log(log_id: int, db: db_dependency, user: user_dependency):
    """
    Supprimer un log (soft delete).
    """
    verify_user(user)
    log = db.query(AuditLogs).filter(AuditLogs.id == log_id).first()
    if not log:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Log not found")

    log.is_deleted = True
    db.commit()
    return
