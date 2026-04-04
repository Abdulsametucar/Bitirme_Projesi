# Bitirme_Projesi

havlu_takip_projesi/
│
├── main.py                  # Web sunucusunu (Flask/FastAPI) başlatan ana dosya.
├── requirements.txt         # Proje kütüphaneleri (opencv-python, flask, sqlalchemy vb.)
│
├── cv_engine/               # Görüntü işleme mantığının bulunduğu klasör
│   ├── __init__.py
│   ├── detector.py          # Görüntüden havluyu ayıran (Background Subtraction), kontur ve X/Y boyutlarını (Bounding Box) bulan kodlar.
│   ├── tracker.py           # Hocanın bahsettiği %15, %33 oranlarını ve zamanı takip eden "Durum Makinesi (State Machine)".
│   └── video_stream.py      # Kameradan veya test videosundan kareleri (frame) okuyan sınıf.
│
├── database/                # Veritabanı ve modellerin bulunduğu klasör
│   ├── __init__.py
│   ├── db_config.py         # SQLite/PostgreSQL bağlantı ayarları.
│   ├── models.py            # Tablo yapıları (İşçi, Havlu_Islemi, Adimlar).
│   └── crud.py              # Veritabanına veri ekleme/okuma fonksiyonları (Create, Read, Update, Delete).
│
├── static/                  # Web arayüzü statik dosyaları
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── dashboard.js     # Gün sonu verilerini grafiklendirmek için.
│
├── templates/               # HTML şablonları
│   ├── base.html            # Ortak iskelet.
│   ├── index.html           # Ana Dashboard (İşçi performansları, toplam havlu).
│   └── live_feed.html       # Canlı kamera akışının ve anlık katlama adımlarının izlendiği sayfa.
│
└── data/                    # Test verileri
    ├── sample_video.mp4     # Hocanın attığı veya senin çektiğin test videoları.
    └── app.db               # SQLite veritabanı dosyası.
