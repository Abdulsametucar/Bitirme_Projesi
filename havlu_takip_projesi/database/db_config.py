from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import Base

DB_PATH = Path(__file__).resolve().parent.parent / 'data' / 'app.db'
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

ENGINE = create_engine(f'sqlite:///{DB_PATH}', echo=False, connect_args={'check_same_thread': False})
SessionLocal = sessionmaker(bind=ENGINE)


def init_db():
    Base.metadata.create_all(bind=ENGINE)


def get_session():
    return SessionLocal()
