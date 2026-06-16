"""
crud.py - Veritabani CRUD (Create, Read, Update, Delete) Islemleri

Tracker (State Machine) ve Web Arayuzu tarafindan kullanilacak
veritabani fonksiyonlarini icerir. Tum fonksiyonlar try-except ile
hata yakalama mekanizmasina sahiptir.

Fonksiyonlar:
    - isci_ekle(ad_soyad)              : Yeni isci ekler
    - yeni_islem_baslat(isci_id)       : Yeni havlu islemi baslatir
    - adim_kaydet(islem_id, ...)       : Katlama adimi kaydeder
    - islem_bitir(islem_id, ...)       : Islemi sonlandirir
    - gunluk_performans_raporu()       : Gun sonu analiz raporu uretir
    - islem_kaydet_toplu(process_data) : tracker.py'dan gelen topluca kayit
"""

from datetime import datetime, date
from sqlalchemy import func

from database.db_config import get_session
from database.models import Isci, HavluIslemi, Adim


# ================================================================
# CRUD FONKSIYONLARI
# ================================================================

def isci_ekle(ad_soyad: str) -> int | None:
    """
    Yeni isci ekler ve ID'sini dondurur.

    Ayni isimde isci varsa mevcut kaydin ID'sini dondurur (tekrar eklemez).

    Args:
        ad_soyad: Iscinin adi ve soyadi.

    Returns:
        int: Eklenen veya mevcut iscinin ID degeri.
        None: Hata durumunda.
    """
    session = get_session()
    try:
        # Ayni isimde isci var mi kontrol et
        mevcut = session.query(Isci).filter_by(ad_soyad=ad_soyad).first()
        if mevcut:
            return mevcut.id

        yeni_isci = Isci(ad_soyad=ad_soyad)
        session.add(yeni_isci)
        session.commit()
        print(f"[DB] Yeni isci eklendi: {ad_soyad} (ID: {yeni_isci.id})")
        return yeni_isci.id

    except Exception as e:
        session.rollback()
        print(f"[DB HATA] isci_ekle: {e}")
        return None

    finally:
        session.close()


def yeni_islem_baslat(isci_id: int) -> int | None:
    """
    HavluIslemi tablosuna baslangic zamani ile yeni kayit acar.

    Args:
        isci_id: Islemi yapacak iscinin ID degeri.

    Returns:
        int: Yeni islem kaydinin ID degeri (islem_id).
        None: Hata durumunda.
    """
    session = get_session()
    try:
        yeni_islem = HavluIslemi(
            isci_id=isci_id,
            baslangic_zamani=datetime.now(),
            durum='Devam Ediyor'
        )
        session.add(yeni_islem)
        session.commit()
        print(f"[DB] Yeni islem basladi (islem_id: {yeni_islem.id}, "
              f"isci_id: {isci_id})")
        return yeni_islem.id

    except Exception as e:
        session.rollback()
        print(f"[DB HATA] yeni_islem_baslat: {e}")
        return None

    finally:
        session.close()


def adim_kaydet(islem_id: int, adim_adi: str, gecen_sure: float) -> int | None:
    """
    State Machine'den gelen her adimi veritabanina kaydeder.

    Args:
        islem_id:   Adimin ait oldugu islemin ID degeri.
        adim_adi:   Adimin adi (ornegin: '1. Katlama (Sagdan)').
        gecen_sure: Bu adimda gecen sure (saniye cinsinden).

    Returns:
        int: Kaydedilen adimin ID degeri.
        None: Hata durumunda.
    """
    session = get_session()
    try:
        yeni_adim = Adim(
            islem_id=islem_id,
            adim_adi=adim_adi,
            gecen_sure_saniye=round(gecen_sure, 2)
        )
        session.add(yeni_adim)
        session.commit()
        return yeni_adim.id

    except Exception as e:
        session.rollback()
        print(f"[DB HATA] adim_kaydet: {e}")
        return None

    finally:
        session.close()


def islem_bitir(islem_id: int, durum: str, toplam_sure: float,
                hata_mesaji: str = None) -> bool:
    """
    Islemi bitirir: bitis zamanini, durumunu ve toplam suresini gunceller.

    Args:
        islem_id:     Bitirilecek islemin ID degeri.
        durum:        Sonuc durumu ('Basarili' veya 'Hatali').
        toplam_sure:  Islemin toplam suresi (saniye cinsinden).
        hata_mesaji:  Hata detayi (opsiyonel, sadece hatali islemlerde).

    Returns:
        bool: Basarili ise True, hata ise False.
    """
    session = get_session()
    try:
        islem = session.query(HavluIslemi).filter_by(id=islem_id).first()
        if not islem:
            print(f"[DB HATA] islem_bitir: islem_id={islem_id} bulunamadi.")
            return False

        islem.bitis_zamani = datetime.now()
        islem.toplam_sure_saniye = round(toplam_sure, 2)
        islem.durum = durum
        islem.hata_mesaji = hata_mesaji

        session.commit()
        print(f"[DB] Islem tamamlandi (islem_id: {islem_id}, "
              f"durum: {durum}, sure: {toplam_sure:.2f}s)")
        return True

    except Exception as e:
        session.rollback()
        print(f"[DB HATA] islem_bitir: {e}")
        return False

    finally:
        session.close()


# ================================================================
# TOPLU KAYIT (tracker.py ENTEGRASYONU)
# ================================================================

def islem_kaydet_toplu(isci_id: int, process_data: dict) -> int | None:
    """
    tracker.py'nin _build_process() ciktisini tek seferde veritabanina kaydeder.

    Bu fonksiyon, tracker.get_status()['process'] dict'ini alir ve:
    1. HavluIslemi kaydini olusturur (baslangic/bitis zamani, durum, sure)
    2. Icindeki tum adimlari Adim tablosuna kaydeder

    Args:
        isci_id:      Islemi yapan iscinin ID degeri.
        process_data: tracker.get_status()['process'] dict'i.
                      Beklenen anahtarlar:
                        - start_time (datetime)
                        - end_time (datetime)
                        - duration_seconds (float)
                        - correct_fold (bool)
                        - steps (list[dict])
                        - errors (list[str])

    Returns:
        int: Kaydedilen islemin ID degeri.
        None: Hata durumunda.
    """
    if not process_data:
        print("[DB HATA] islem_kaydet_toplu: process_data bos.")
        return None

    session = get_session()
    try:
        # Durum belirle
        durum = 'Basarili' if process_data.get('correct_fold') else 'Hatali'

        # Hata mesajlarini birlestir
        hatalar = process_data.get('errors', [])
        hata_mesaji = ' | '.join(hatalar) if hatalar else None

        # Ana islem kaydini olustur
        islem = HavluIslemi(
            isci_id=isci_id,
            baslangic_zamani=process_data['start_time'],
            bitis_zamani=process_data['end_time'],
            toplam_sure_saniye=round(process_data['duration_seconds'], 2),
            durum=durum,
            hata_mesaji=hata_mesaji,
        )
        session.add(islem)
        session.flush()  # ID'yi almak icin flush

        # Adimlari kaydet
        for step in process_data.get('steps', []):
            adim = Adim(
                islem_id=islem.id,
                adim_adi=step.get('name', 'Bilinmiyor'),
                gecen_sure_saniye=round(step.get('duration_seconds', 0.0), 2),
            )
            session.add(adim)

        session.commit()
        print(f"[DB] Toplu kayit tamamlandi (islem_id: {islem.id}, "
              f"durum: {durum}, adim: {len(process_data.get('steps', []))})")
        return islem.id

    except Exception as e:
        session.rollback()
        print(f"[DB HATA] islem_kaydet_toplu: {e}")
        return None

    finally:
        session.close()


# ================================================================
# RAPORLAMA
# ================================================================

def gunluk_performans_raporu() -> dict:
    """
    Gun sonu performans analiz raporu uretir.

    Geri Donus (dict):
        {
            'tarih': '2026-05-10',
            'toplam_islem': 45,
            'basarili': 38,
            'hatali': 7,
            'basari_orani': 84.4,
            'ortalama_sure_saniye': 12.5,
            'isci_detaylari': [
                {
                    'ad_soyad': 'Ahmet Yilmaz',
                    'toplam': 15,
                    'basarili': 13,
                    'hatali': 2,
                    'basari_orani': 86.7,
                    'ortalama_sure': 11.2
                },
                ...
            ]
        }
    """
    session = get_session()
    try:
        bugun = date.today()
        bugun_baslangic = datetime.combine(bugun, datetime.min.time())
        bugun_bitis = datetime.combine(bugun, datetime.max.time())

        # Bugune ait tum islemler
        gunluk_islemler = (
            session.query(HavluIslemi)
            .filter(HavluIslemi.baslangic_zamani.between(bugun_baslangic, bugun_bitis))
            .all()
        )

        toplam = len(gunluk_islemler)
        basarili = sum(1 for i in gunluk_islemler if i.durum == 'Basarili')
        hatali = sum(1 for i in gunluk_islemler if i.durum == 'Hatali')

        sureler = [i.toplam_sure_saniye for i in gunluk_islemler
                   if i.toplam_sure_saniye and i.toplam_sure_saniye > 0]
        ort_sure = round(sum(sureler) / len(sureler), 2) if sureler else 0.0

        basari_orani = round((basarili / toplam) * 100, 1) if toplam > 0 else 0.0

        # Isci bazli detay
        isci_detaylari = []
        isciler = session.query(Isci).all()

        for isci in isciler:
            isci_islemleri = [
                i for i in gunluk_islemler if i.isci_id == isci.id
            ]
            if not isci_islemleri:
                continue

            isci_toplam = len(isci_islemleri)
            isci_basarili = sum(1 for i in isci_islemleri if i.durum == 'Basarili')
            isci_hatali = sum(1 for i in isci_islemleri if i.durum == 'Hatali')

            isci_sureler = [i.toplam_sure_saniye for i in isci_islemleri
                            if i.toplam_sure_saniye and i.toplam_sure_saniye > 0]
            isci_ort = (round(sum(isci_sureler) / len(isci_sureler), 2)
                        if isci_sureler else 0.0)

            isci_detaylari.append({
                'ad_soyad': isci.ad_soyad,
                'toplam': isci_toplam,
                'basarili': isci_basarili,
                'hatali': isci_hatali,
                'basari_orani': round(
                    (isci_basarili / isci_toplam) * 100, 1
                ) if isci_toplam > 0 else 0.0,
                'ortalama_sure': isci_ort,
            })

        # En basarili isciyi basa koy
        isci_detaylari.sort(key=lambda x: x['basari_orani'], reverse=True)

        rapor = {
            'tarih': bugun.isoformat(),
            'toplam_islem': toplam,
            'basarili': basarili,
            'hatali': hatali,
            'basari_orani': basari_orani,
            'ortalama_sure_saniye': ort_sure,
            'isci_detaylari': isci_detaylari,
        }

        print(f"[DB] Gunluk rapor olusturuldu: {toplam} islem, "
              f"%{basari_orani} basari orani")
        return rapor

    except Exception as e:
        print(f"[DB HATA] gunluk_performans_raporu: {e}")
        return {
            'tarih': date.today().isoformat(),
            'toplam_islem': 0,
            'basarili': 0,
            'hatali': 0,
            'basari_orani': 0.0,
            'ortalama_sure_saniye': 0.0,
            'isci_detaylari': [],
        }

    finally:
        session.close()


def genel_dashboard_raporu() -> dict:
    """
    Tüm zamanların genel durumunu ve son işlem adımlarını içeren rapor.
    """
    session = get_session()
    try:
        # Toplam işlem (kullanıcının isteğine göre havlu_islemleri son id'si veya kayıt sayısı)
        toplam_islem = session.query(func.max(HavluIslemi.id)).scalar() or 0
        
        # Hatalı
        hatali_islem = session.query(func.count(HavluIslemi.id)).filter(HavluIslemi.durum == 'Hatali').scalar() or 0
        
        # Başarılı (Başarı oranı hesabı için)
        basarili_islem = session.query(func.count(HavluIslemi.id)).filter(HavluIslemi.durum == 'Basarili').scalar() or 0
        
        # Başarı Oranı
        hesaplanan_toplam = basarili_islem + hatali_islem
        if hesaplanan_toplam > 0:
            basari_orani = round((basarili_islem / hesaplanan_toplam) * 100, 1)
        else:
            basari_orani = 0.0
            
        # Ortalama süre
        ortalama_sure = session.query(func.avg(HavluIslemi.toplam_sure_saniye)).filter(HavluIslemi.toplam_sure_saniye > 0).scalar() or 0.0
        ortalama_sure = round(ortalama_sure, 1)
        
        # İşçi Performansları (Adımlar -> İslem -> Isci sırasıyla)
        # Son eklenen 20 adımı listeleyelim
        son_adimlar_sorgu = (
            session.query(Adim, HavluIslemi, Isci)
            .join(HavluIslemi, Adim.islem_id == HavluIslemi.id)
            .join(Isci, HavluIslemi.isci_id == Isci.id)
            .order_by(Adim.id.desc())
            .limit(20)
            .all()
        )
        
        adim_listesi = []
        for adim, islem, isci in son_adimlar_sorgu:
            adim_listesi.append({
                'isci_ad_soyad': isci.ad_soyad,
                'adim_adi': adim.adim_adi,
                'gecen_sure_saniye': adim.gecen_sure_saniye
            })
            
        return {
            'toplam_islem': toplam_islem,
            'basarili': basarili_islem,
            'hatali': hatali_islem,
            'basari_orani': basari_orani,
            'ortalama_sure_saniye': ortalama_sure,
            'son_adimlar': adim_listesi
        }

    except Exception as e:
        print(f"[DB HATA] genel_dashboard_raporu: {e}")
        return {
            'toplam_islem': 0,
            'basarili': 0,
            'hatali': 0,
            'basari_orani': 0.0,
            'ortalama_sure_saniye': 0.0,
            'son_adimlar': []
        }

    finally:
        session.close()
