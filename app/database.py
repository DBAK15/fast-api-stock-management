import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pydantic_settings import BaseSettings


# Charger les variables d'environnement depuis .env
load_dotenv()

# DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/gestionnaire-stock")
# engine = create_engine(DATABASE_URL)

# for sqlite3

SQLACHEMY_DATABASE_URL = 'sqlite:///./stockManagementApp.db'
engine = create_engine(SQLACHEMY_DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
