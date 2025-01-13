from fastapi import APIRouter

from app.schemas import CategoryCreate

router = APIRouter()

@router.get("/categories")
async def get_categories():
    # Code pour récupérer toutes les catégories
    pass

@router.get("/categories/{category_id}")
async def get_category(category_id: int):
    # Code pour récupérer une catégorie spécifique
    pass

@router.post("/categories")
async def create_category(category: CategoryCreate):
    # Code pour créer une nouvelle catégorie
    pass

@router.put("/categories/{category_id}")
async def update_category(category_id: int, category: Category):
    # Code pour mettre à jour une catégorie existante
    pass

@router.delete("/categories/{category_id}")
async def delete_category(category_id: int):
    # Code pour supprimer une catégorie
    pass
