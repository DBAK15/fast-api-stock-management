from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Annotated

from .auth import get_current_user
from ..database import SessionLocal
from ..models import Roles
from ..schemas import RoleCreate, RoleRead, RoleUpdate

router = APIRouter(
    prefix="/roles",
    tags=["Roles"]
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

@router.get("/", response_model=List[RoleRead])
async def read_all(db: db_dependency, user: user_dependency):
    """
    Récupérer la liste de tous les rôles non supprimés.
    """
    verify_user(user)
    roles = db.query(Roles).filter(Roles.is_deleted == False).all()
    return roles


@router.get("/role/{role_id}", response_model=RoleRead)
async def read_role(role_id: int, db: db_dependency, user: user_dependency):
    """
    Récupérer un rôle spécifique par son ID.
    """
    verify_user(user)
    role = db.query(Roles).filter(Roles.id == role_id, Roles.is_deleted == False).first()
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    return role


@router.post("/role", response_model=RoleRead, status_code=status.HTTP_201_CREATED)
async def create_role(role: RoleCreate, db: db_dependency, user: user_dependency):
    """
    Créer un nouveau rôle.
    """
    verify_user(user)

    # Vérifier si le rôle existe déjà
    existing_role = db.query(Roles).filter(Roles.name == role.name).first()
    if existing_role:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Role already exists")

    # Créer le nouveau rôle
    new_role = Roles(name=role.name, description=role.description, created_by=user.get('id'))
    db.add(new_role)
    db.commit()
    db.refresh(new_role)
    return new_role


@router.put("/role/{role_id}", response_model=RoleRead)
async def update_role(role_id: int, role_update: RoleUpdate, db: db_dependency, user: user_dependency):
    """
    Mettre à jour un rôle existant.
    """
    verify_user(user)

    role = db.query(Roles).filter(Roles.id == role_id, Roles.is_deleted == False).first()
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")

    # Mettre à jour les champs du rôle
    if role_update.name:
        role.name = role_update.name
    if role_update.description:
        role.description = role_update.description
    role.updated_by = user.get('id')  # Mettre à jour par l'utilisateur actuel

    db.commit()
    db.refresh(role)
    return role


@router.delete("/role/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role(role_id: int, db: db_dependency, user: user_dependency):
    """
    Supprimer un rôle (suppression logique).
    """
    verify_user(user)

    role = db.query(Roles).filter(Roles.id == role_id, Roles.is_deleted == False).first()
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")

    # Suppression logique
    role.is_deleted = True
    # role.updated_by = user.get('id')  # Mettre à jour par l'utilisateur actuel
    db.commit()
    return {"message": "Role deleted successfully"}




# from fastapi import APIRouter, Depends, HTTPException, status
# from sqlalchemy.orm import Session
# from pydantic import BaseModel
# from typing import List, Annotated
#
# from .auth import get_current_user
# from ..database import SessionLocal
# from ..models import Roles
# from ..schemas import RoleCreate, RoleRead, RoleUpdate
#
# router = APIRouter(
#     prefix="/roles",
#     tags=["Roles"]
# )
#
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
#
#
# ### Endpoints ###
#
# @router.get("/", response_model=List[RoleRead])
# async def real_all(db: db_dependency):
#     roles = db.query(Roles).all()
#     return roles
#
#
# @router.get("/role/{role_id}", response_model=RoleRead)
# async def read_role(role_id: int, db: db_dependency):
#     role = db.query(Roles).filter(Roles.id == role_id).first()
#     if not role:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
#     return role
#
#
# @router.post("/", response_model=RoleRead, status_code=status.HTTP_201_CREATED)
# async def create_role(role: RoleCreate, db: db_dependency):
#     # Vérifier si le rôle existe déjà
#     existing_role = db.query(Roles).filter(Roles.name == role.name).first()
#     if existing_role:
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Role already exists")
#
#     # Créer le nouveau rôle
#     new_role = Roles(name=role.name, description=role.description)
#     db.add(new_role)
#     db.commit()
#     return new_role
#
#
# @router.put("/role/{role_id}", response_model=RoleRead)
# async def update_role(role_id: int, role_update: RoleUpdate, db: db_dependency):
#     role = db.query(Roles).filter(Roles.id == role_id).first()
#     if not role:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
#
#     # Mettre à jour le rôle
#     role.name = role_update.name
#     db.commit()
#     return role
#
#
# @router.delete("/role/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
# async def delete_role(role_id: int, db: db_dependency):
#     role = db.query(Roles).filter(Roles.id == role_id).first()
#     if not role:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
#
#     db.delete(role)
#     db.commit()
#     return {"message": "Role deleted successfully"}
