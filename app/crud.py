from sqlalchemy.orm import Session
from app import models, schemas


def create_product(db: Session, product: schemas.ProductCreate):
    # Créer un nouvel objet Product à partir du schéma ProductCreate
    db_product = models.Product(**product.dict())

    # Ajouter l'objet Product à la session de la base de données
    db.add(db_product)

    # Commencer la transaction et enregistrer le produit dans la base de données
    db.commit()

    # Rafraîchir l'objet pour obtenir l'ID généré par la base de données
    db.refresh(db_product)

    # Retourner l'objet produit créé
    return db_product


def get_products(db: Session, skip: int = 0, limit: int = 10):
    # Exécuter une requête pour récupérer les produits avec les paramètres de pagination
    return db.query(models.Product).offset(skip).limit(limit).all()
