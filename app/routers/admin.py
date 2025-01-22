from typing import Annotated

from starlette import status
from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session

from .auth import get_current_user
from ..database import SessionLocal
from ..models import Categories

router = APIRouter(
    prefix="/admin",
    tags=["Admin"]
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]
db_1: Session = SessionLocal()


def permission_required(permission_name: str):
    def dependency(current_user: dict = Depends(get_current_user)):
        permissions = current_user.get("permissions", [])
        if permission_name not in permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission_name}' is required for this operation."
            )
        return True

    return dependency


from sqlalchemy.orm import Session
from ..models import Roles, Permissions, RolePermissions


def assign_permission_to_role(db: db_dependency, role_id: int, permission_name: str):
    """
    Assigne une permission à un rôle.
    """
    # Rechercher le rôle et la permission
    role = db.query(Roles).filter(Roles.id == role_id, Roles.is_deleted == False).first()
    permission = db.query(Permissions).filter(Permissions.name == permission_name,
                                              Permissions.is_deleted == False).first()

    if not role:
        raise ValueError(f"Role with ID {role_id} not found or is deleted.")
    if not permission:
        raise ValueError(f"Permission with name '{permission_name}' not found or is deleted.")

    # Vérifier si la permission est déjà assignée au rôle
    existing_relation = db.query(RolePermissions).filter_by(role_id=role_id, permission_id=permission.id).first()
    if existing_relation:
        raise ValueError(f"Permission '{permission_name}' is already assigned to role '{role.name}'.")

    # Ajouter la relation dans la table RolePermissions
    role_permission = RolePermissions(role_id=role_id, permission_id=permission.id)
    db.add(role_permission)
    db.commit()


def remove_permission_from_role(db: db_dependency, role_id: int, permission_name: str):
    """
    Supprime une permission d'un rôle.
    """
    # Rechercher le rôle et la permission
    role = db.query(Roles).filter(Roles.id == role_id, Roles.is_deleted == False).first()
    permission = db.query(Permissions).filter(Permissions.name == permission_name,
                                              Permissions.is_deleted == False).first()

    if not role:
        raise ValueError(f"Role with ID {role_id} not found or is deleted.")
    if not permission:
        raise ValueError(f"Permission with name '{permission_name}' not found or is deleted.")

    # Vérifier si la relation existe dans la table RolePermissions
    role_permission = db.query(RolePermissions).filter_by(role_id=role_id, permission_id=permission.id).first()
    if not role_permission:
        raise ValueError(f"Permission '{permission_name}' is not assigned to role '{role.name}'.")

    # Supprimer la relation
    db.delete(role_permission)
    db.commit()


#
# def seed_roles_and_permissions(db: Session):
#     # Ajouter les permissions
#     permissions = ["view_dashboard", "edit_users", "create_user"]
#     for perm_name in permissions:
#         # Vérifier si la permission existe déjà
#         existing_permission = db.query(Permissions).filter_by(name=perm_name).first()
#         if not existing_permission:
#             new_permission = Permissions(name=perm_name)
#             db.add(new_permission)
#
#     db.commit()  # S'assurer que les permissions sont bien ajoutées avant de les associer aux rôles
#
#     # Ajouter les rôles avec leurs permissions
#     roles_with_permissions = {
#         "admin": permissions,  # L'admin a toutes les permissions
#         "viewer": ["view_dashboard"],  # Le viewer n'a accès qu'à la vue du tableau de bord
#     }
#
#     for role_name, perm_names in roles_with_permissions.items():
#         # Vérifier si le rôle existe déjà
#         role = db.query(Roles).filter_by(name=role_name).first()
#         if not role:
#             role = Roles(name=role_name)
#             db.add(role)
#             db.commit()  # Commit après avoir ajouté un nouveau rôle pour obtenir son ID
#
#         # Associer les permissions au rôle
#         for perm_name in perm_names:
#             permission = db.query(Permissions).filter_by(name=perm_name).first()
#             if permission:
#                 # Vérifier si la relation rôle-permission existe déjà
#                 existing_role_permission = db.query(RolePermissions).filter_by(
#                     role_id=role.id, permission_id=permission.id
#                 ).first()
#                 if not existing_role_permission:
#                     role_permission = RolePermissions(role_id=role.id, permission_id=permission.id)
#                     db.add(role_permission)
#
#     db.commit()  # Commit final pour sauvegarder les relations
#
#
# seed_roles_and_permissions(db_1)
# #
# # # Permissions à ajouter
# # permissions = [
# #     {"name": "VIEW_PRODUCTS", "description": "Voir les produits"},
# #     {"name": "CREATE_PRODUCTS", "description": "Créer des produits"},
# #     {"name": "EDIT_PRODUCTS", "description": "Modifier des produits"},
# #     {"name": "DELETE_PRODUCTS", "description": "Supprimer des produits"},
# #     {"name": "VIEW_ORDERS", "description": "Voir les commandes"},
# #     {"name": "CREATE_ORDERS", "description": "Créer des commandes"},
# #     {"name": "EDIT_ORDERS", "description": "Modifier des commandes"},
# #     {"name": "DELETE_ORDERS", "description": "Supprimer des commandes"},
# # ]
#
# permissions = [
#     {"name": "VIEW_STOCKS", "description": "Voir les stocks"},
#     {"name": "UPDATE_STOCKS", "description": "Mettre à jour les stocks (ajouter/retirer des produits)"},
#     {"name": "VIEW_REPORTS", "description": "Voir les rapports (performance, ventes, stocks)"},
#     {"name": "VALIDATE_ORDERS", "description": "Valider les commandes des clients"},
#     {"name": "VIEW_USERS", "description": "Voir les utilisateurs du système"},
#     {"name": "CREATE_USERS", "description": "Créer des utilisateurs"},
#     {"name": "EDIT_USERS", "description": "Modifier les utilisateurs"},
#     {"name": "DELETE_USERS", "description": "Supprimer des utilisateurs"},
#     {"name": "MANAGE_PERMISSIONS", "description": "Gérer les permissions des utilisateurs"},
# ]
#
# # Créer une session pour interagir avec la base de données
# db = SessionLocal()
#
# # Ajouter les permissions
# for perm in permissions:
#     permission = Permissions(name=perm["name"], description=perm["description"])
#     db.add(permission)
#
# # Commit les changements dans la base de données
# db.commit()
#
# # Fermer la session
# db.close()

def seed_roles_and_permissions(db: Session):
    # Définition des permissions
    permissions = [
        {"name": "VIEW_STOCKS", "description": "Voir les stocks"},
        {"name": "UPDATE_STOCKS", "description": "Mettre à jour les stocks (ajouter/retirer des produits)"},
        {"name": "VIEW_REPORTS", "description": "Voir les rapports (performance, ventes, stocks)"},
        {"name": "VALIDATE_ORDERS", "description": "Valider les commandes des clients"},
        {"name": "VIEW_USERS", "description": "Voir les utilisateurs du système"},
        {"name": "CREATE_USERS", "description": "Créer des utilisateurs"},
        {"name": "EDIT_USERS", "description": "Modifier les utilisateurs"},
        {"name": "DELETE_USERS", "description": "Supprimer des utilisateurs"},
        {"name": "MANAGE_PERMISSIONS", "description": "Gérer les permissions des utilisateurs"},
    ]

    # Ajouter les permissions dans la base de données si elles n'existent pas déjà
    for perm in permissions:
        existing_permission = db.query(Permissions).filter_by(name=perm["name"]).first()
        if not existing_permission:
            new_permission = Permissions(name=perm["name"], description=perm["description"])
            db.add(new_permission)

    # Commit après avoir ajouté toutes les permissions
    db.commit()

    # Définition des rôles et des permissions associées
    roles_with_permissions = {
        "admin": permissions,  # L'admin a toutes les permissions
        "manager": [
            {"name": "VIEW_STOCKS", "description": "Voir les stocks"},
            {"name": "UPDATE_STOCKS", "description": "Mettre à jour les stocks (ajouter/retirer des produits)"},
            {"name": "VIEW_REPORTS", "description": "Voir les rapports (performance, ventes, stocks)"},
            {"name": "VALIDATE_ORDERS", "description": "Valider les commandes des clients"},
            {"name": "VIEW_USERS", "description": "Voir les utilisateurs du système"},
            {"name": "EDIT_USERS", "description": "Modifier les utilisateurs"},
        ],
        "clerk": [
            {"name": "VIEW_STOCKS", "description": "Voir les stocks"},
            {"name": "UPDATE_STOCKS", "description": "Mettre à jour les stocks (ajouter/retirer des produits)"},
            {"name": "VALIDATE_ORDERS", "description": "Valider les commandes des clients"},
        ],
        "client": [
            {"name": "VIEW_STOCKS", "description": "Voir les stocks"},
            {"name": "VALIDATE_ORDERS", "description": "Valider les commandes des clients"},
        ],
        "viewer": [
            {"name": "VIEW_STOCKS", "description": "Voir les stocks"},
        ]
    }

    # Ajouter les rôles et leurs permissions dans la base de données
    for role_name, perm_list in roles_with_permissions.items():
        # Vérifier si le rôle existe déjà
        role = db.query(Roles).filter_by(name=role_name).first()
        if not role:
            role = Roles(name=role_name)
            db.add(role)
            db.commit()  # Commit après avoir ajouté un rôle pour récupérer son ID

        # Associer les permissions au rôle
        for perm in perm_list:
            permission = db.query(Permissions).filter_by(name=perm["name"]).first()
            if permission:
                # Vérifier si la relation existe déjà pour éviter les doublons
                existing_role_permission = db.query(RolePermissions).filter_by(
                    role_id=role.id, permission_id=permission.id
                ).first()
                if not existing_role_permission:
                    role_permission = RolePermissions(role_id=role.id, permission_id=permission.id)
                    db.add(role_permission)

    # Commit final pour sauvegarder les relations
    db.commit()


seed_roles_and_permissions(db_1)


@router.get("/categories/", status_code=status.HTTP_200_OK)
async def read_all_categories(user: user_dependency, db: db_dependency):
    if user is None or user.get('user_role') != 'admin':
        from fastapi import HTTPException
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication failed.")
    return db.query(Categories).filter(Categories.is_deleted == False).all()


@router.delete("/category/{category_id}", status_code=status.HTTP_200_OK)
async def delete_category(user: user_dependency, db: db_dependency, category_id: int = Path(gt=0)):
    if user is None or user.get('user_role') != 'admin':
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Authentication failed.")

    category_model = db.query(Categories).filter(Categories.id == category_id).first()

    if category_model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    category_model.is_deleted = True
    db.add(category_model)
    db.commit()


@router.get("/admin/dashboard")
def admin_dashboard(
        has_permission: bool = Depends(permission_required("view_dashboard"))
):
    return {"message": "Access granted to the dashboard!"}


@router.post("/admin/create-user")
def create_user(
        has_permission: bool = Depends(permission_required("create_user"))
):
    return {"message": "User created successfully!"}
