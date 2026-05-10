"""
db_config.py - Veritabani Baglanti Ayarlari

SQLite veritabani icin motor (engine) ve oturum (session) yapisi olusturur.
Veritabani dosyasi: <proje_koku>/data/app.db

Kullanim:
    from database.db_config import init_db, get_session

    # Uygulama basinda bir kez cagir (tablolari olusturur):
    init_db()

    # CRUD islemlerinde oturum al:
    session = get_session()
"""

from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# ================================================================
# VERITABANI YOLU
# ================================================================
# Veritabani dosyasi projenin ana dizinindeki data/app.db konumuna olusturulur
# __file__ -> database/db_config.py
# parent   -> database/
# parent   -> havlu_takip_projesi/  (proje koku)
DB_PATH = Path(__file__).resolve().parent.parent / 'data' / 'app.db'

# data/ klasoru yoksa otomatik olustur
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


# ================================================================
# SQLALCHEMY MOTOR VE OTURUM
# ================================================================

# SQLite baglanti motoru
# check_same_thread=False: Flask/multi-thread ortamlarda guvenli calisma
# echo=False: SQL sorgularini konsola yazdirma (debug icin True yapilabilir)
ENGINE = create_engine(
    f'sqlite:///{DB_PATH}',
    echo=False,
    connect_args={'check_same_thread': False},
    pool_pre_ping=True
)

# Oturum fabrikasi (Session Factory)
SessionLocal = sessionmaker(
    bind=ENGINE,
    autocommit=False,
    autoflush=False
)


# ================================================================
# YARDIMCI FONKSIYONLAR
# ================================================================

def init_db():
    """
    Veritabani tablolarini olusturur.

    Uygulama baslatildiginda bir kez cagrilmalidir.
    models.py icindeki Base'e bagli tum tablolari (Isci, HavluIslemi, Adim)
    SQLite dosyasinda olusturur. Zaten varsa atlar (IF NOT EXISTS).
    """
    # Circular import'u onlemek icin burada import ediyoruz
    from database.models import Base
    Base.metadata.create_all(bind=ENGINE)
    print(f"[DB] Veritabani hazir: {DB_PATH}")


def get_session():
    """
    Yeni bir veritabani oturumu (session) dondurur.

    Her islemden sonra session.close() ile kapatilmalidir.
    Context manager olarak da kullanilabilir.

    Returns:
        Session: SQLAlchemy oturum nesnesi.
    """
    return SessionLocal()
