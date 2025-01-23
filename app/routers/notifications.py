from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .auth import get_current_user
from ..database import SessionLocal
from ..models import Notifications
from ..schemas import NotificationRead, NotificationCreate, NotificationUpdate

router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"],
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


### Endpoints ###

@router.get("/", response_model=List[NotificationRead])
async def read_all_notifications(db: db_dependency, user: user_dependency):
    """
    Récupérer la liste de toutes les notifications non supprimées.
    """
    verify_user(user)
    notifications = db.query(Notifications).filter(Notifications.is_deleted == False).all()
    return notifications


@router.get("/notification/{notification_id}", response_model=NotificationRead)
async def read_notification(notification_id: int, db: db_dependency, user: user_dependency):
    """
    Récupérer une notification spécifique par son ID.
    """
    verify_user(user)
    notification = db.query(Notifications).filter(Notifications.id == notification_id,
                                                  Notifications.is_deleted == False).first()
    if not notification:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    return notification


@router.post("/notification", response_model=NotificationRead, status_code=status.HTTP_201_CREATED)
async def create_notification(notification: NotificationCreate, db: db_dependency, user: user_dependency):
    """
    Créer une nouvelle notification.
    """
    verify_user(user)
    new_notification = Notifications(**notification.dict(), user_id=user.get('id'), created_by=user.get('id'))
    db.add(new_notification)
    db.commit()
    db.refresh(new_notification)
    return new_notification


@router.put("/notification/{notification_id}", response_model=NotificationRead)
async def update_notification(notification_id: int, notification: NotificationUpdate, db: db_dependency,
                              user: user_dependency):
    """
    Mettre à jour une notification existante par son ID.
    """
    verify_user(user)
    existing_notification = db.query(Notifications).filter(Notifications.id == notification_id,
                                                     Notifications.is_deleted == False).first()
    if not existing_notification:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")

    for key, value in notification.dict(exclude_unset=True).items():
        setattr(existing_notification, key, value)

    existing_notification.updated_by = user.get('id')

    db.commit()
    db.refresh(existing_notification)
    return existing_notification


@router.delete("/notification/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_notification(notification_id: int, db: db_dependency, user: user_dependency):
    """
    Supprimer une notification par son ID.
    """
    verify_user(user)
    db_notification = db.query(Notifications).filter(Notifications.id == notification_id).first()
    if not db_notification:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")

    db_notification.is_deleted = True
    db.commit()
