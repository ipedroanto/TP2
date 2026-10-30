import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Lee la URL de la base de datos desde las variables de entorno de Docker
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "mysql+pymysql://feedback_user:feedback_pass@mysql:3306/feedback_db"
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Dependencia para inyectar la sesión en los endpoints de FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()