"""
models.py - Havlu Katlama Takip Sistemi Veritabani Modelleri

SQLAlchemy ORM kullanarak iliskisel tablo yapilari tanimlar.
3 ana tablo:
    1. Isci          : Katlama yapan iscilerin kaydini tutar.
    2. HavluIslemi   : Bir havlunun bastan sona katlanma surecini tutar.
    3. Adim          : Her islemin icindeki alt katlama adimlarini tutar.

Iliskiler:
    Isci  --1:N-->  HavluIslemi  --1:N-->  Adim
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import declarative_base, relationship

# Tum modeller icin temel sinif (Base)
Base = declarative_base()


class Isci(Base):
    """
    Isci (Worker) Tablosu.

    Katlama islemini gerceklestiren iscilerin kaydini tutar.
    Bir iscinin birden fazla havlu islemi olabilir (1:N iliskisi).
    """
    __tablename__ = 'isciler'

    id = Column(Integer, primary_key=True, autoincrement=True)
    ad_soyad = Column(String(100), unique=True, nullable=False,
                      comment='Iscinin adi ve soyadi')

    # 1:N iliskisi -> Bir iscinin birden fazla havlu islemi olabilir
    islemler = relationship(
        'HavluIslemi',
        back_populates='isci',
        cascade='all, delete-orphan',
        lazy='dynamic'
    )

    def __repr__(self):
        return f"<Isci(id={self.id}, ad_soyad='{self.ad_soyad}')>"


class HavluIslemi(Base):
    """
    Havlu Islemi (Ana Islem) Tablosu.

    Her bir havlunun bastan sona katlanma surecini tutar.
    Bir islemin icinde birden fazla adim (State gecisi) bulunur (1:N iliskisi).

    Durum Degerleri:
        - "Basarili" : Tum adimlar dogru sirayla tamamlandi.
        - "Hatali"   : Yanlis katlama, adim atlama vb. hata olustu.
    """
    __tablename__ = 'havlu_islemleri'

    id = Column(Integer, primary_key=True, autoincrement=True)
    isci_id = Column(Integer, ForeignKey('isciler.id'), nullable=False,
                     comment='Islemi yapan iscinin ID degeri')

    baslangic_zamani = Column(DateTime, nullable=False,
                              comment='Islemin baslama zamani')
    bitis_zamani = Column(DateTime, nullable=True,
                          comment='Islemin bitis zamani (devam ediyorsa None)')

    toplam_sure_saniye = Column(Float, nullable=True, default=0.0,
                                comment='Islemin toplam suresi (saniye)')

    durum = Column(String(20), nullable=False, default='Devam Ediyor',
                   comment='Islem durumu: Basarili / Hatali / Devam Ediyor')

    hata_mesaji = Column(Text, nullable=True,
                         comment='Hata detay mesaji (opsiyonel)')

    # Foreign Key iliskisi -> Isci
    isci = relationship('Isci', back_populates='islemler')

    # 1:N iliskisi -> Bir islemin birden fazla adimi olabilir
    adimlar = relationship(
        'Adim',
        back_populates='islem',
        cascade='all, delete-orphan',
        order_by='Adim.id',
        lazy='joined'
    )

    def __repr__(self):
        return (f"<HavluIslemi(id={self.id}, isci_id={self.isci_id}, "
                f"durum='{self.durum}')>")


class Adim(Base):
    """
    Adim (Detay) Tablosu.

    Havlu isleminin icindeki her bir katlama adimini (State gecisini) tutar.
    Ornegin: "1. Katlama (Sagdan)" -> 2.35 saniye suren bir adim.
    """
    __tablename__ = 'adimlar'

    id = Column(Integer, primary_key=True, autoincrement=True)
    islem_id = Column(Integer, ForeignKey('havlu_islemleri.id'), nullable=False,
                      comment='Bu adimin ait oldugu islemin ID degeri')

    adim_adi = Column(String(100), nullable=False,
                      comment='Adimin adi (ornegin: 1. Katlama (Sagdan))')

    gecen_sure_saniye = Column(Float, nullable=False, default=0.0,
                               comment='Bu adimin suresi (saniye)')

    # Foreign Key iliskisi -> HavluIslemi
    islem = relationship('HavluIslemi', back_populates='adimlar')

    def __repr__(self):
        return (f"<Adim(id={self.id}, islem_id={self.islem_id}, "
                f"adim_adi='{self.adim_adi}', sure={self.gecen_sure_saniye:.2f}s)>")
