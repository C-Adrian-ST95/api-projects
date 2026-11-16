import os 
from dotenv import load_dotenv
from sqlalchemy import create_engine, URL
from sqlalchemy.orm import DeclarativeBase, sessionmaker

load_dotenv()

# construir la direccion de PostgreSQL
DATABASE_URL= URL.create(
    drivername="postgresql+psycopg",
    username=os.environ["DB_USER"],
    password=os.environ["DB_PASSWORD"],
    host=os.getenv("DB_HOST", "localhost"),
    port=int(os.getenv("DB_POST", "5432")),
    database=os.environ["DB_NAME"],
)

# Administrar conexiones a PostgreSQL
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)

# Crearr sesiones de trabajo
SessionLocal = sessionmaker(
    bind=engine, 
    autoflush=False, 
    expire_on_commit=False
)

# Clase base para las tablas

class Base(DeclarativeBase):
    pass

# Una sesión por solicitud HTTP 
def obtener_sesion():
    with SessionLocal() as sesion:
        yield sesion