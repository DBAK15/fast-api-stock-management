# from typing import Annotated
#
# from fastapi import Request, Depends
# from datetime import datetime
# import logging
# import json
#
# from sqlalchemy.orm import Session
#
# from app.database import SessionLocal
# from app.routers.auditLogs import log_user_action
# from app.routers.auth import get_current_user
# from app.schemas import AuditLogCreate
#
# logger = logging.getLogger("audit")
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
#
#
# async def log_request_response(db: db_dependency, user: user_dependency, request: Request, call_next):
#     """
#     Middleware pour logger les requêtes et les réponses.
#     """
#     # Capture les détails de la requête
#     start_time = datetime.utcnow()
#     request_info = {
#         "method": request.method,
#         "url": str(request.url),
#         "client_ip": request.client.host,
#         "headers": dict(request.headers),
#     }
#
#     logger.info(f"Request started: {json.dumps(request_info)}")
#
#     # Essayer de capturer le corps de la requête
#     try:
#         request_body = await request.json()
#         logger.info(f"Request body: {json.dumps(request_body)}")
#     except Exception:
#         logger.info("Request body could not be parsed or is empty")
#
#     # Appelle la route FastAPI
#     response = await call_next(request)
#
#     # Capture les détails de la réponse
#     end_time = datetime.utcnow()
#     duration = (end_time - start_time).total_seconds()
#     response_info = {
#         "status_code": response.status_code,
#         "duration": duration,
#         "headers": dict(response.headers),
#     }
#
#     logger.info(
#         f"Request completed: {json.dumps(request_info)} | Response: {json.dumps(response_info)} | Duration: {duration}s"
#     )
#
#     # Enregistre l'action utilisateur dans la base si applicable
#     if request.method in ["POST", "PUT", "DELETE"]:
#         log_action = AuditLogCreate(
#             action=f"{request.method} {request.url.path}",
#             description=f"Request to {request.url.path}",
#             user_id=user.get('id'),
#         )
#         log_user_action(db=db, user=user, log_action=log_action)
#
#     return response

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from datetime import datetime
import logging
import json

from app.routers.auditLogs import log_user_action
from app.schemas import AuditLogCreate

logger = logging.getLogger("audit")


class LoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, get_db, get_user):
        super().__init__(app)
        self.get_db = get_db
        self.get_user = get_user

    async def dispatch(self, request: Request, call_next):
        # Début du traitement de la requête
        start_time = datetime.utcnow()
        request_info = {
            "method": request.method,
            "url": str(request.url),
            "client_ip": request.client.host,
            "headers": dict(request.headers),
        }

        logger.info(f"Request started: {json.dumps(request_info)}")

        # Essayer de capturer le corps de la requête
        try:
            request_body = await request.json()
            logger.info(f"Request body: {json.dumps(request_body)}")
        except Exception:
            logger.info("Request body could not be parsed or is empty")

        # Appelle la route FastAPI
        response = await call_next(request)

        # Capture les détails de la réponse
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        response_info = {
            "status_code": response.status_code,
            "duration": duration,
            "headers": dict(response.headers),
        }

        logger.info(
            f"Request completed: {json.dumps(request_info)} | Response: {json.dumps(response_info)} | Duration: {duration}s"
        )

        # Enregistre l'action utilisateur dans la base si applicable
        if request.method in ["POST", "PUT", "DELETE", "GET"]:
            try:
                # Extraire les dépendances
                db = next(self.get_db())
                user = await self.get_user(request)

                log_action = AuditLogCreate(
                    action=f"{request.method} {request.url.path}",
                    description=f"Request to {request.url.path}",
                    user_id=user.get('id'),
                )
                log_user_action(db=db, user=user, log_action=log_action)
            except Exception as e:
                logger.error(f"Error logging user action: {e}")

        return response
