from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from passlib.context import CryptContext
from typing import Annotated
from sqlalchemy.orm import Session
from ..database import SessionLocal
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt, JWTError
from datetime import datetime, timedelta
import os
import logging

from ..models import Users, Roles, Permissions, RolePermissions
from ..schemas import Token, UserCreate

router = APIRouter(
    prefix="/auth",
    tags=["Auth"]
)

# Charger les variables d'environnement
load_dotenv()

# Configuration depuis l'environnement
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 20))

# Vérification des variables d'environnement
if not SECRET_KEY or not ALGORITHM:
    raise ValueError("Missing essential environment variables (SECRET_KEY or ALGORITHM)")

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_bearer = OAuth2PasswordBearer(tokenUrl="auth/token")
logger = logging.getLogger(__name__)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]


### Fonctions ###
def authenticate_user(username: str, password: str, db):
    user = db.query(Users).filter(Users.username == username).first()
    if not user:
        logger.warning(f"Failed login attempt: Username '{username}' not found.")
        return False
    if not bcrypt_context.verify(password, user.hashed_password):
        logger.warning(f"Failed login attempt: Incorrect password for user '{username}'.")
        return False
    return user


def create_access_token(
        username: str,
        user_id: int,
        role: str,
        expires_delta: timedelta,
        db: db_dependency
):
    # Rechercher le rôle associé dans la base de données
    role_obj = db.query(Roles).filter(Roles.name == role, Roles.is_deleted == False).first()
    if not role_obj:
        raise ValueError(f"Role '{role}' does not exist or is deleted.")

    # Récupérer les permissions directement via la table RolePermissions
    permissions = db.query(Permissions.name).join(RolePermissions).filter(RolePermissions.role_id == role_obj.id).all()

    # Extraire les noms des permissions
    permissions = {perm[0] for perm in permissions}

    if not permissions:
        raise ValueError(f"Role '{role}' has no valid permissions.")
    print('permissions', permissions)

    # Construire le payload du JWT
    encode = {
        'sub': username,
        'id': user_id,
        'role': role,
        'permissions': list(permissions),  # Ajouter les permissions au payload
        'exp': datetime.utcnow() + expires_delta
    }

    # Générer le token
    try:
        return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)
    except JWTError as e:
        logger.error(f"Error encoding JWT: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="JWT encoding error")


# Decode JWT
async def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get('sub')
        user_id: int = payload.get('id')
        user_role: str = payload.get('role')
        permissions: list = payload.get('permissions', [])
        if not username or not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Could not validate credentials'
            )
        return {
            "id": user_id,
            "username": username,
            "user_role": user_role,
            "permissions": permissions
        }
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Could not validate credentials'
        )


### Endpoints ###
@router.post("/users", status_code=status.HTTP_201_CREATED)
async def create_user(db: db_dependency, user_request: UserCreate):
    existing_user = db.query(Users).filter(Users.username == user_request.username).first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists")

    create_user_model = Users(
        username=user_request.username,
        email=user_request.email,
        first_name=user_request.first_name,
        last_name=user_request.last_name,
        role_id=user_request.role_id,
        hashed_password=bcrypt_context.hash(user_request.password),
        is_active=True,
        phone=user_request.phone,
    )
    try:
        db.add(create_user_model)
        db.commit()

        return {"message": "User created successfully"}
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="An error occurred while creating the user")



@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: db_dependency):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")
    token = create_access_token(
        username=user.username,
        user_id=user.id,
        role=user.role.name,
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        db=db  # Ajouter ici la dépendance db
    )

    return {'access_token': token, 'token_type': 'bearer'}

# from dotenv import load_dotenv
# from fastapi import APIRouter, Depends, HTTPException, status
# from pydantic import BaseModel
# from passlib.context import CryptContext
# from typing import Annotated
# from sqlalchemy.orm import Session
# from ..database import SessionLocal
# from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
# from jose import jwt, JWTError
# from datetime import datetime, timedelta
# import os
# import logging
#
# from ..models import Users, Roles
# from ..schemas import Token, UserCreate
#
# router = APIRouter(
#     prefix="/auth",
#     tags=["Auth"]
# )
#
# # Charger les variables d'environnement
# load_dotenv()
#
# # Configuration depuis l'environnement
# SECRET_KEY = os.getenv("SECRET_KEY")
# ALGORITHM = os.getenv("ALGORITHM")
# ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 20))
#
# # Vérification des variables d'environnement
# if not SECRET_KEY or not ALGORITHM:
#     raise ValueError("Missing essential environment variables (SECRET_KEY or ALGORITHM)")
#
# bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# oauth2_bearer = OAuth2PasswordBearer(tokenUrl="auth/token")
# logger = logging.getLogger(__name__)
#
#
# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()
#
#
# db_dependency = Annotated[Session, Depends(get_db)]
#
#
# ### Fonctions ###
# def authenticate_user(username: str, password: str, db):
#
#     user = db.query(Users).filter(Users.username == username).first()
#     if not user:
#         return False
#     if not bcrypt_context.verify(password, user.hashed_password):
#         return False
#     return user
#
#
#
# def create_access_token(username: str, user_id: int, role: str, expires_delta: timedelta):
#     encode = {'sub': username, 'id': user_id, 'role': role, 'exp': datetime.utcnow() + expires_delta}
#     return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)
#
# Decode JWT
# async def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]):
#     try:
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         username: str = payload.get('sub')
#         user_id: int = payload.get('id')
#         user_role: str = payload.get('role')
#         if not username or not user_id:
#             raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not validate credentials')
#         return {"id": user_id, "username": username, "user_role": user_role}
#     except JWTError:
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not validate credentials')
#
#
#
# ### Endpoints ###
# @router.post("/users", status_code=status.HTTP_201_CREATED)
# async def create_user(db: db_dependency, user_request: UserCreate):
#     existing_user = db.query(Users).filter(Users.username == user_request.username).first()
#     if existing_user:
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists")
#
#     create_user_model = Users(
#         username=user_request.username,
#         email=user_request.email,
#         first_name=user_request.first_name,
#         last_name=user_request.last_name,
#         role_id=user_request.role_id,
#         hashed_password=bcrypt_context.hash(user_request.password),
#         is_active=True,
#         phone=user_request.phone,
#     )
#     try:
#         db.add(create_user_model)
#         db.commit()
#         return {"message": "User created successfully"}
#     except Exception as e:
#         logger.error(f"Error creating user: {e}")
#         db.rollback()
#         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                             detail="An error occurred while creating the user")
#
#
# @router.post("/token", response_model=Token)
# async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: db_dependency):
#     user = authenticate_user(form_data.username, form_data.password, db)
#     if not user:
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")
#     token = create_access_token(
#         username=user.username,
#         user_id=user.id,
#         role=user.role.name,
#         expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
#     )
#
#     return {'access_token': token, 'token_type': 'bearer'}
#
