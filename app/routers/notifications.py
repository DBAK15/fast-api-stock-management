from typing import List

from fastapi import APIRouter, HTTPException, status

from ..dependencies import db_dependency, user_dependency
from ..logging_config import setup_logger  # Import the setup_logger function
from ..models import Notifications
from ..schemas import NotificationRead, NotificationCreate, NotificationUpdate
from ..utils import check_permissions, verify_user

# Configure logging
logger = setup_logger("notificationManagementLogger")

router = APIRouter()

#
# # Dépendance pour récupérer la session de la base de données
# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()
#
#
# db_dependency = Annotated[Session, Depends(get_db)]
# user_dependency = Annotated[dict, Depends(get_current_user)]
required_permissions = [
    "VIEW_NOTIFICATIONS",         # Pour lire toutes les notifications
    "VIEW_NOTIFICATION",          # Pour lire une notification spécifique
    "CREATE_NOTIFICATION",        # Pour créer une notification
    "EDIT_NOTIFICATION",          # Pour mettre à jour une notification
    "DELETE_NOTIFICATION"         # Pour supprimer une notification
]

# Helper functions
# def verify_user(user: dict) -> None:
#     """
#     Vérifie si l'utilisateur est authentifié.
#     Lève une exception HTTP 401 si ce n'est pas le cas.
#     """
#     if user is None:
#         logger.warning("Authorization failed: No user provided")
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Authorization failed"
#         )


### Endpoints ###

@router.get("/", response_model=List[NotificationRead])
async def read_all_notifications(db: db_dependency, user: user_dependency):
    """
    Récupérer la liste de toutes les notifications non supprimées.
    """
    verify_user(user)
    # Vérifier si l'utilisateur a les permissions requises
    check_permissions(user, required_permissions)
    logger.info(f"Fetching all notifications for user_id: {user.get('id')}")
    notifications = db.query(Notifications).filter(Notifications.is_deleted == False).all()
    return notifications


@router.get("/notification/{notification_id}", response_model=NotificationRead)
async def read_notification(notification_id: int, db: db_dependency, user: user_dependency):
    """
    Récupérer une notification spécifique par son ID.
    """
    verify_user(user)
    # Vérifier si l'utilisateur a les permissions requises
    check_permissions(user, required_permissions)

    notification = db.query(Notifications).filter(Notifications.id == notification_id,
                                                  Notifications.is_deleted == False).first()
    if not notification:
        logger.warning(f"Notification with ID {notification_id} not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    logger.info(f"Retrieved notification {notification_id} for user_id: {user.get('id')}")
    return notification


@router.post("/notification", response_model=NotificationRead, status_code=status.HTTP_201_CREATED)
async def create_notification(notification: NotificationCreate, db: db_dependency, user: user_dependency):
    """
    Créer une nouvelle notification.
    """
    verify_user(user)
    # Vérifier si l'utilisateur a les permissions requises
    check_permissions(user, required_permissions)

    new_notification = Notifications(**notification.dict(), user_id=user.get('id'), created_by=user.get('id'))
    db.add(new_notification)
    db.commit()
    db.refresh(new_notification)
    logger.info(f"Created notification {new_notification.id} for user_id: {user.get('id')}")
    return new_notification


@router.put("/notification/{notification_id}", response_model=NotificationRead)
async def update_notification(notification_id: int, notification: NotificationUpdate, db: db_dependency,
                              user: user_dependency):
    """
    Mettre à jour une notification existante par son ID.
    """
    verify_user(user)
    # Vérifier si l'utilisateur a les permissions requises
    check_permissions(user, required_permissions)

    existing_notification = db.query(Notifications).filter(Notifications.id == notification_id,
                                                           Notifications.is_deleted == False).first()
    if not existing_notification:
        logger.warning(f"Notification with ID {notification_id} not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")

    for key, value in notification.dict(exclude_unset=True).items():
        setattr(existing_notification, key, value)

    existing_notification.updated_by = user.get('id')

    db.commit()
    db.refresh(existing_notification)
    logger.info(f"Updated notification {notification_id} for user_id: {user.get('id')}")
    return existing_notification


@router.delete("/notification/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_notification(notification_id: int, db: db_dependency, user: user_dependency):
    """
    Supprimer une notification par son ID.
    """
    verify_user(user)
    # Vérifier si l'utilisateur a les permissions requises
    check_permissions(user, required_permissions)

    db_notification = db.query(Notifications).filter(Notifications.id == notification_id).first()
    if not db_notification:
        logger.warning(f"Notification with ID {notification_id} not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")

    db_notification.is_deleted = True
    db.commit()
    logger.info(f"Deleted notification {notification_id} for user_id: {user.get('id')}")
