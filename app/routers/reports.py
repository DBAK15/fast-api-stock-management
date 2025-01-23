from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .auth import get_current_user
from ..database import SessionLocal
from ..models import Reports
from ..schemas import ReportRead, ReportCreate, ReportUpdate

router = APIRouter(
    prefix="/reports",
    tags=["Reports"],
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

@router.get("/", response_model=List[ReportRead])
async def read_all_reports(db: db_dependency, user: user_dependency):
    """
    Récupérer la liste de tous les rapports non supprimés.
    """
    verify_user(user)
    reports = db.query(Reports).filter(Reports.is_deleted == False).all()
    return reports


@router.get("/report/{report_id}", response_model=ReportRead)
async def read_report(report_id: int, db: db_dependency, user: user_dependency):
    """
    Récupérer un rapport spécifique par son ID.
    """
    verify_user(user)
    report = db.query(Reports).filter(Reports.id == report_id, Reports.is_deleted == False).first()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    return report


@router.post("/report", response_model=ReportRead, status_code=status.HTTP_201_CREATED)
async def create_report(report: ReportCreate, db: db_dependency, user: user_dependency):
    """
    Créer un nouveau rapport.
    """
    verify_user(user)
    new_report = Reports(**report.dict())
    db.add(new_report)
    db.commit()
    db.refresh(new_report)
    return new_report


@router.put("/report/{report_id}", response_model=ReportRead)
async def update_report(report_id: int, report: ReportUpdate, db: db_dependency, user: user_dependency):
    """
    Mettre à jour un rapport existant.
    """
    verify_user(user)
    existing_report = db.query(Reports).filter(Reports.id == report_id, Reports.is_deleted == False).first()
    if not existing_report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    for key, value in report.dict(exclude_unset=True).items():
        setattr(existing_report, key, value)

    existing_report.updated_by = user.get('id')

    db.commit()
    db.refresh(existing_report)
    return existing_report


@router.delete("/report/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_report(report_id: int, db: db_dependency, user: user_dependency):
    """
    Supprimer un rapport (suppression logique).
    """
    verify_user(user)
    existing_report = db.query(Reports).filter(Reports.id == report_id, Reports.is_deleted == False).first()
    if not existing_report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    existing_report.is_deleted = True
    db.commit()
    return None
