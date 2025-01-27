from fastapi import APIRouter, HTTPException
from passlib.context import CryptContext
from starlette import status

from ..dependencies import user_dependency, db_dependency, bcrypt_context
from ..logging_config import setup_logger  # Import the setup_logger function
from ..models import Users
from ..schemas import UserVerification, UserResponse

# Configure logger
logger = setup_logger("userManagementLogger")

router = APIRouter()
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
# user_dependency = Annotated[dict, Depends(get_current_user)]
required_permissions = ["VIEW_USERS", "CREATE_USERS", "EDIT_USERS", "DELETE_USERS", "MANAGE_PERMISSIONS"]


@router.get('/', status_code=status.HTTP_200_OK, response_model=UserResponse)
async def get_user(user: user_dependency, db: db_dependency):
    if user is None:
        logger.warning("Authorization failed: No user provided")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization failed")
    logger.info(f"Fetching user info for user_id: {user.get('id')}")
    return db.query(Users).filter(Users.id == user.get('id')).first()


@router.put('/password', status_code=status.HTTP_204_NO_CONTENT)
async def change_password(user: user_dependency, db: db_dependency, user_verification: UserVerification):
    if user is None:
        logger.warning("Authorization failed: No user provided")
        raise HTTPException(status_code=401, detail="Authorization failed")
    user_model = db.query(Users).filter(Users.id == user.get('id')).first()

    if not bcrypt_context.verify(user_verification.password, user_model.hashed_password):
        logger.warning(f"Password verification failed for user_id: {user.get('id')}")
        raise HTTPException(status_code=401, detail="Error on password change.")

    user_model.hashed_password = bcrypt_context.hash(user_verification.new_password)
    db.add(user_model)
    db.commit()
    logger.info(f"Password successfully updated for user_id: {user.get('id')}")


@router.put('/phonenumber/{phone_number}', status_code=status.HTTP_204_NO_CONTENT)
async def change_phone_number(user: user_dependency, db: db_dependency, phone: str):
    if user is None:
        logger.warning("Authorization failed: No user provided")
        raise HTTPException(status_code=401, detail="Authorization failed")
    user_model = db.query(Users).filter(Users.id == user.get('id')).first()
    user_model.phone = phone
    db.add(user_model)
    db.commit()
    logger.info(f"Phone number updated for user_id: {user.get('id')} to {phone}")
