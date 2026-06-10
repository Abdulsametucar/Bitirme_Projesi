# Bitirme Projesi Haftalık İlerleme Raporu

## Proje Bilgileri

| Alan | Bilgi |
|------|-------|
| **Öğrenci Adı Soyadı** | *Abdulsamet Uçar* |
| **Öğrenci No** | *21360859075* |
| **Proje Başlığı** | Bilgisayarlı Görü ile Üretim Bandında Havlu Katlama Takip ve Performans Analiz Sistemi |
| **Danışman** | Prof. Dr. Turgay Tugay Bilgin |
| **Dönem** | 2025-2026 Bahar |

---

## İş Planı

> **Kullanım:** Dönem başında aşağıdaki tabloyu projenize göre doldurun. Her hafta için planlanan işi ve o haftanın sonunda projenin tahmini tamamlanma oranını yazın. Dönem ilerledikçe "Durum" sütununu güncelleyin.

| Hafta | Tarih Aralığı | Planlanan İş | Tahmini Tamamlanma (%) | Durum |
|-------|---------------|--------------|------------------------|-------|
| 1 | 04.04 - 11.04 | Literatür araştırması, proje klasör yapısının (Flask/FastAPI, cv_engine, db) kurulması ve test video ve fotoğraflarının ayarlanması. | %10 | ✅ Tamamlandı |
| 2 | 11.04 - 18.04 | Görüntü bölütleme (segmentasyon) algoritmalarının (Canny, Sobel, Prewitt, K-Means, DBSCAN vb.) test scripti ile karşılaştırılması ve en verimli yöntemin seçilmesi. | %20 | ✅ Tamamlandı |
| 3 | 25.04 - 02.05 | Seçilen algoritma ile `detector.py` modülünün yazılması. Görüntüden havlunun ayrılması, Bounding Box (sınırlayıcı kutu) ve X/Y boyutlarının anlık hesaplanması. | %30 | ✅ Tamamlandı |
| 4 | 02.05 - 09.05 | Katlama adımlarını oransal (%15, %33, %50 vb.) olarak takip edecek Durum Makinesi (State Machine) mantığının `tracker.py` içerisine kodlanması. | %40 | ✅ Tamamlandı |
| 5 | 09.05 - 16.05 | Zaman ölçüm metriklerinin sisteme entegre edilmesi. Her bir katlama aşamasının ve toplam işlemin ne kadar sürdüğünün ölçülmesi. Doğru katlama / hatalı katlama karar mantığının oluşturulması. | %50 | ✅ Tamamlandı |
| 6 | 16.05 - 23.05 | `database` modülünün ayarlanması. SQLite/PostgreSQL veritabanı tablolarının (İşçi, Havlu_Islemi, Adimlar) oluşturulması ve CRUD operasyonlarının yazılması. | %60 | ✅ Tamamlandı |
| 7 | 30.05 - 06.06 | Görüntü işleme motoru (CV Engine) ile veritabanının birbirine bağlanması. İşlenen verilerin anlık olarak veritabanına kaydedilmesi. | %70 | ✅ Tamamlandı |
| 8 | 06.06 - 13.06 | Web uygulamasının backend (main.py) ve frontend (HTML/CSS/JS) iskeletinin ayağa kaldırılması. `live_feed.html` üzerinden kamera/video akışının webe aktarılması. | %80 | ✅ Tamamlandı |
| 9 | 13.06 - 20.06 | `index.html` (Dashboard) arayüzünün geliştirilmesi. Gün sonu toplam katlanan havlu sayısı ve en iyi performans gösteren işçi verilerinin grafiksel gösterimi. | %90 | ✅ Tamamlandı |
| 10 | 20.06 - 27.06 | Sistemin uçtan uca test edilmesi, hataların (bug) giderilmesi, performans optimizasyonları ve Bitirme Projesi Raporu / Sunumu hazırlıkları. | %100 | 🔄 Devam Ediyor |

**Durum simgeleri:** ⬜ Başlamadı | 🔄 Devam Ediyor | ✅ Tamamlandı | ⚠️ Gecikti

---

## Haftalık İlerleme Kayıtları

> **Kullanım:** Her hafta aşağıdaki şablonu kopyalayıp doldurun. En güncel hafta en üstte olacak şekilde ekleyin.

---

### Hafta 9 *(Tarih: 13.06.2026 - 20.06.2026)*

**Plandaki hedef:**
- `index.html` (Dashboard) arayüzünün geliştirilmesi. Gün sonu toplam katlanan havlu sayısı ve en iyi performans gösteren işçi verilerinin grafiksel gösterimi.

**Bu hafta yaptıklarım:**
- Yöneticilerin sistemi kolayca takip edebilmesi için Bootstrap 5 kullanılarak modern, duyarlı (responsive) ve endüstriyel temaya uygun bir Dashboard (`index.html`) tasarlandı.
- Flask backend üzerinde `/api/stats` endpoint'i yazılarak veritabanındaki (SQLite) işçi işlem metrikleri JSON formatında dışa açıldı.
- Frontend tarafında JavaScript (Fetch API/AJAX) kullanılarak asenkron veri iletişim altyapısı kuruldu. Sayfanın tamamı yenilenmeden, arka planda çalışan görüntü işleme sisteminin veritabanına attığı kayıtlar (başarılı havlu, hata sayısı, ortalama süre) her 3-5 saniyede bir tablolara yansıtıldı.
- Gelecekte eklenebilecek kameralar için çoklu işçi (worker_id) takibine olanak tanıyan mimari altyapı arayüze bağlandı.

**Plana göre durumum:**
- Hedeflere tam anlamıyla ulaşıldı. Projenin yazılım geliştirme aşamaları "uçtan uca" (end-to-end) entegrasyonla tamamlandı.

**Karşılaştığım sorunlar / zorluklar:**
- Arayüzdeki performans tablolarının JavaScript ile sık sık güncellenmesi ekranda anlık kırpışmalara (flickering) neden oldu.
- **Çözüm:** DOM manipülasyonu optimize edilerek, sadece veritabanında yeni bir değişiklik olduğunda ilgili HTML elemanlarının içeriğinin güncellenmesi sağlandı.

**Gelecek hafta hedefim:**
- Sistemin farklı senaryolar (hatalı katlama yapan işçi vb.) altında uçtan uca test edilmesi, oluşabilecek anlık hataların (bug) giderilmesi, son performans optimizasyonlarının yapılması ve Bitirme Projesi Nihai Raporu'nun (Tez) yazımına başlanması.

---

### Hafta 8 *(Tarih: 06.06.2026 - 13.06.2026)*

**Plandaki hedef:**
- Web uygulamasının backend (main.py) ve frontend (HTML/CSS/JS) iskeletinin ayağa kaldırılması. `live_feed.html` üzerinden kamera/video akışının webe aktarılması.

**Bu hafta yaptıklarım:**
- Görüntü işleme (`cv_engine`) ve veritabanı (`database`) modülleri **Flask** web framework'ü kullanılarak tek bir ana çatı altında (`app.py`) birleştirildi.
- OpenCV'nin saniyede 30 kare (FPS) işleyen döngüsü web ortamına taşındı. Generator (`yield`) mimarisi kullanılarak `/video_feed` endpoint'i oluşturuldu.
- İşlenen görüntüler (üzerindeki Bounding Box, durum metinleri ve uyarı çizimleriyle birlikte) anlık (stream) olarak `multipart/x-mixed-replace` formatında `live_feed` sayfasına başarıyla aktarıldı.

**Plana göre durumum:**
- Hedeflere ulaşıldı. Masaüstü formunda çalışan sistem başarılı bir şekilde web tabanlı bir mimariye geçirildi.

**Karşılaştığım sorunlar / zorluklar:**
- **Sunucu Bloklanması (Blocking Loop):** OpenCV'nin video okuyan sonsuz `while` döngüsü aynı ana thread üzerinde çalıştığı için, Flask sunucusunun diğer web sayfalarına ve HTTP isteklerine yanıt verememesine (kilitlenmesine) neden oldu.
- **Çözüm:** Görüntü işleme süreci Flask'ın asenkron generator yapısına uyarlanarak ve gerekli yerlerde threading/stream adaptasyonu yapılarak sunucunun kilitlenmesi sorunu kesin olarak çözüldü.

**Gelecek hafta hedefim:**
- `index.html` (Dashboard) arayüzünün geliştirilmesi ve veritabanındaki günlük istatistiklerin görselleştirilmesi.

---

### Hafta 7 *(Tarih: 30.05.2026 - 06.06.2026)*

**Plandaki hedef:**
- Görüntü işleme motoru (CV Engine) ile veritabanının birbirine bağlanması. İşlenen verilerin anlık olarak veritabanına kaydedilmesi.

**Bu hafta yaptıklarım:**
- `tracker.py` içerisindeki Durum Makinesi'nin (State Machine) ürettiği veriler (her bir adımın süresi, işlemin başlangıç-bitiş zamanı, hata kodları ve başarı durumu) veritabanı modülüyle eşleştirildi.
- `database/crud.py` içerisindeki fonksiyonlar ana görüntü işleme döngüsüne entegre (import) edildi. Havlu masaya konduğunda veritabanında yeni bir kayıt (session) açılması ve işlem bittiğinde (veya hata fırlatıldığında) bu kaydın güncellenmesi sağlandı.

**Plana göre durumum:**
- Hedeflere ulaşıldı. Analiz motoru ile veri depolama birimi arasındaki veri akışı eksiksiz sağlandı.

**Karşılaştığım sorunlar / zorluklar:**
- Görüntü işleme döngüsü çok hızlı (milisaniyeler içinde) çalıştığı için, sisteme gereksiz yere her karede veritabanı bağlantısı açıp veri yazmaya çalışması SQLite veritabanının kilitlenmesine ("database is locked" hatası) ve diskin yorulmasına sebep oldu.
- **Çözüm:** Veritabanı kayıt tetikleyicisi (trigger) optimize edildi. Yazma işlemi sadece "State (Durum)" gerçekten değiştiğinde veya işlem tamamen sonlandığında çalışacak şekilde kısıtlandı.

**Gelecek hafta hedefim:**
- Web uygulamasının backend (Flask) ve frontend iskeletinin kurularak video akışının webe aktarılması.


### Hafta 6 *(Tarih: 16.05.2026 - 23.05.2026)*

**Plandaki hedef:**
- `database` modülünün ayarlanması. SQLite/PostgreSQL veritabanı tablolarının (İşçi, Havlu_Islemi, Adimlar) oluşturulması ve CRUD operasyonlarının yazılması.

**Bu hafta yaptıklarım:**
- Projenin MVP (Minimum Viable Product) yapısına ve taşınabilirliğine en uygun veritabanı motoru olarak **SQLite** seçildi. Doğrudan SQL sorguları yazmak yerine, nesne yönelimli ve güvenli bir yapı sunan **SQLAlchemy (ORM)** kütüphanesi kullanıldı.
- `database/db_config.py` oluşturularak lokal veritabanı (`data/app.db`) bağlantı motoru ve oturum (session) ayarları yapılandırıldı.
- `database/models.py` modülü içerisinde, ilişkisel veritabanı standartlarına (Primary Key, Foreign Key) uygun olarak `Isci`, `HavluIslemi` ve `Adimlar` tabloları oluşturuldu.
- `database/crud.py` dosyası yazılarak, sisteme yeni işçi ekleme, yeni işlem başlatma, adım kaydetme ve işlemi bitirme gibi temel veri manipülasyon (CRUD) fonksiyonları modüler hale getirildi.
- Görüntü işleme motorundan (`tracker.py`) dönen anlık metriklerin (katlama süreleri, başarı/hata durumları) `main.py` üzerinden doğrudan veritabanına kaydedilmesi sağlandı.

**Plana göre durumum:**
- Planlanan hedeflere ulaşıldı. Proje takviminin oldukça önünde, güvenli bir şekilde ilerliyorum.

**Karşılaştığım sorunlar / zorluklar:**
- Görüntü işleme motorunun veritabanına attığı logları ve süre metriklerini doğrulayabilmek için `.db` dosyasının içeriğini görsel olarak inceleme ihtiyacı doğdu. Bu ihtiyaç, geliştirme ortamına "SQLite Viewer" eklentisi ve "DB Browser for SQLite" aracı entegre edilerek çözüldü; verilerin tutarlılığı arayüz üzerinden teyit edildi.

**Gelecek hafta hedefim:**
- Web uygulamasının backend (Flask veya FastAPI) ve frontend (HTML/CSS/JS) iskeletinin ayağa kaldırılması. `live_feed.html` sayfası oluşturularak, OpenCV üzerinden işlenen canlı kamera/video akışının ve anlık tespit verilerinin web tarayıcısına aktarılması çalışmalarına başlanması.

### Hafta 5 *(Tarih: 09.05.2026 - 16.05.2026)*

**Plandaki hedef:**
- Zaman ölçüm metriklerinin sisteme entegre edilmesi. Her bir katlama aşamasının ve toplam işlemin ne kadar sürdüğünün ölçülmesi. Doğru katlama / hatalı katlama karar mantığının oluşturulması.

**Bu hafta yaptıklarım:**
- `tracker.py` içerisindeki durum makinesine (State Machine) `time` modülü entegre edildi. Her bir katlama aşamasının (State) geçiş süresi ve işin başlangıcından bitişine kadar geçen toplam süre saniye cinsinden hesaplanarak raporlandı.
- Adımlar arası geçişlerde "Doğru Katlama" ve "Hatalı Katlama" (örn: adım atlama, ters yönden katlama) senaryoları test edildi ve karar mantığı oturtuldu.
- İşlem tamamlanma koşulu güncellendi: `tracker.py` içerisindeki State 3 mantığı "alttan üste doğru" katlama senaryosuna göre güncellendi. State 5 (Final) için gereksiz bekleme süresi kaldırılarak, boyutlar hedefe ulaştığında sistemin doğrudan "BAŞARILI" sonucunu döndürmesi sağlandı.
- `main.py` içerisindeki video oynatma döngüsüne dinamik FPS hesaplaması (`delay = int(1000 / fps)`) eklenerek analiz sürecinin gerçek hızında (1x) çalışması sağlandı.

**Plana göre durumum:**
- Hedeflere tam anlamıyla ulaşıldı. 3., 4. ve 5. haftanın görevleri yoğun bir çalışma ile birleştirilerek tamamlandığı için proje takviminin yaklaşık 2 hafta önünde ilerliyorum.

**Karşılaştığım sorunlar / zorluklar:**
- Sonuç ekranında video akışının asenkron olması ve ağır çekimde oynatılması sorunu yaşandı. Görüntü okuma gecikmesi videonun kendi FPS değerine senkronize edilerek çözüldü.

**Gelecek hafta hedefim:**
- `database` modülünün ayarlanması. Veritabanı tablolarının (İşçi, Havlu_Islemi, Adimlar) oluşturulması ve CRUD operasyonlarının yazılması.

---

### Hafta 4 *(Tarih: 02.05.2026 - 09.05.2026)*

**Plandaki hedef:**
- Katlama adımlarını oransal (%15, %33, %50 vb.) olarak takip edecek Durum Makinesi (State Machine) mantığının `tracker.py` içerisine kodlanması.

**Bu hafta yaptıklarım:**
- `tracker.py` modülü kodlanarak, `detector.py`'den anlık olarak gelen X, Y, Genişlik (W) ve Yükseklik (H) verilerini işleyen 5 aşamalı bir Durum Makinesi (State Machine) oluşturuldu.
- Senaryoya uygun olarak; sağdan %15, üstten %33, alttan %50 gibi belirlenen oranlar ile havlunun boyut küçülmeleri eşleştirildi.
- Beklenmeyen bir eksende daralma olduğunda veya adımlar arasında atlama yapıldığında sürecin iptal edilip hatayı loglayan bir yapı geliştirildi.

**Plana göre durumum:**
- Hızlı bir ilerleme kaydedildi, planlanan işler takvimin ilerisinde tamamlandı.

**Karşılaştığım sorunlar / zorluklar:**
- **Oklüzyon (Kapanma) Sorunu:** İşçinin kolları ve elleri katlama esnasında kadraja girdiğinde, sistem kolları havlunun bir parçası zannederek sınırlayıcı kutuyu (Bounding Box) aniden büyüttü. Bu da sistemin "Yanlış Eksen (h_drift)" hatası fırlatmasına neden oldu.
- **Çözüm:** State Machine içerisine bir "Debounce (Stabilizasyon)" mantığı yazıldı. Yeni boyutların geçerli sayılabilmesi için hareketin bitmesi ve boyutların belirli bir frame/saniye boyunca sabit kalması şartı eklendi.

**Gelecek hafta hedefim:**
- Zaman ölçüm metriklerinin sisteme entegre edilmesi ve hata/başarı durumlarının raporlanabilir hale getirilmesi.

---

### Hafta 3 *(Tarih: 25.04.2026 - 02.05.2026)*

**Plandaki hedef:**
- Seçilen algoritma ile `detector.py` modülünün yazılması. Görüntüden havlunun ayrılması, Bounding Box (sınırlayıcı kutu) ve X/Y boyutlarının anlık hesaplanması.

**Bu hafta yaptıklarım:**
- Görüntü işleme motorunun temelini oluşturan `detector.py` modülü kodlandı.
- Algoritma ile havlu arka plandan (tezgahtan) başarıyla ayrıştırıldı ve nesnenin etrafına bir Bounding Box çizilmesi sağlandı.
- Her bir video karesi (frame) için havlunun başlangıç X/Y koordinatları ve anlık Genişlik (W) / Yükseklik (H) değerleri hesaplanarak dışarı aktarıldı (return edildi).
- Ellerin ve kolların tespit kalitesini bozmaması için görüntü işleme adımından önce opsiyonel bir HSV tabanlı ten rengi maskesi (Skin Mask) altyapısı araştırılıp sisteme uyarlanabilir hale getirildi.

**Plana göre durumum:**
- Planlanan hedef başarıyla tamamlandı. Görüntü işleme modülü stabil çalışıyor.

**Karşılaştığım sorunlar / zorluklar:**
- Gürültü ve ortam ışığı değişimleri Bounding Box'ın titremesine neden oldu. Morfolojik işlemler (Erosion/Dilation) ile maske pürüzsüzleştirilerek bu sorun aşıldı.

**Gelecek hafta hedefim:**
- Bu anlık boyut verilerini alıp, havlunun katlanma evrelerini (%15, %33 gibi) kontrol edecek Durum Makinesinin (State Machine) kodlanması.

### Hafta 2 *(Tarih: 11.04.2026 - 18.04.2026)*

**Plandaki hedef:**
- Görüntü bölütleme (segmentasyon) algoritmalarının (Canny, Sobel, Prewitt, K-Means, DBSCAN vb.) test scripti ile karşılaştırılması ve en verimli yöntemin seçilmesi.

**Bu hafta yaptıklarım:**
- Görüntü bölütleme algoritmalarını (Sobel, Canny, K-Means) aynı video karesi üzerinde eşzamanlı çalıştırarak yan yana karşılaştırmayı sağlayan bir Python test scripti geliştirildi.
- Temel eşikleme (Thresholding), Uyarlanabilir eşikleme (Adaptive Thresholding) ve HSV renk uzayı maskelemesi yöntemleri test edildi. Ortam ışığındaki değişimlerin ve havlu dokusunun maskede kopukluklara yol açtığı gözlemlendi.
- K-Means kümeleme algoritmasının temiz sonuç vermesine rağmen gerçek zamanlı (FPS) video işleme için çok yavaş kaldığı; Sobel operatörünün ise havlunun iç dokusundaki kırışıklıkları (gürültüyü) fazlasıyla algıladığı tespit edildi.
- Hız, işlemci yükü ve kenar netliği (dış çerçeve temizliği) metrikleri göz önüne alındığında, projede ana tespit yöntemi olarak **Canny Kenar Bulma (Canny Edge Detection)** algoritmasının kullanılmasına karar verildi.

**Plana göre durumum:**
- Hedeflere ulaşıldı, algoritma seçimi aşaması takvime uygun olarak başarıyla tamamlandı.

**Karşılaştığım sorunlar / zorluklar:**
- Havlunun üzerindeki doku farkları ve katlama sırasındaki kırışıklıklar, algoritmaların havluyu tek parça yerine çok sayıda küçük parça olarak algılamasına neden oldu. Bu sorunu aşmak için Canny algoritmasının eşik değerlerinin (hysteresis) ortama göre optimize edilmesi gerektiği anlaşıldı.

**Gelecek hafta hedefim:**
- Seçilen Canny algoritması ve morfolojik işlemler kullanılarak `detector.py` modülünün yazılması.
- Görüntüden havlunun tamamen ayrıştırılarak "solid (katı) maske" elde edilmesi ve Bounding Box üzerinden anlık X/Y ekseni genişlik/yükseklik hesaplamalarının yapılması.
  

### Hafta 1 *(Tarih: 04.04.2026 - 11.04.2026)*

**Plandaki hedef:**
- Literatür araştırması, proje klasör yapısının (Flask/FastAPI, cv_engine, db) kurulması ve test videolarının ayarlanması.

**Bu hafta yaptıklarım:**
- Proje kapsamı danışman hocalarla netleştirildi ve MVP (Minimum Viable Product) hedefleri belirlendi.
- Derin öğrenme yerine geleneksel görüntü işleme metotları (Canny, Sobel, eşikleme vb.) kullanılması kararlaştırıldı.
- Literatür araştırması yapılarak projeler incelendi.
  [https://www.frontiersin.org/journals/robotics-and-ai/articles/10.3389/frobt.2026.1752914/full], 
  [https://people.eecs.berkeley.edu/~pabbeel/papers/Maitin-ShepardCusumano-TownerLeiAbbeel_ICRA2010.pdf],
  [https://publications.ri.cmu.edu/storage/publications/2021/08/MSR_Thesis_SujayBajracharya.pdf]
- Projenin `main.py`, `cv_engine`, `database`, `static` ve `templates` mimarisinden oluşan modüler klasör yapısı oluşturuldu.
- Sistemin üzerinde çalışacağı referans havlu katlama videosu indirildi. Kendi ürettiğim video ve fotoğraflar test klasörüne (`data/sample_video.mp4`) eklendi.
  
**Plana göre durumum:**
- Hedeflere ulaşıldı, planlanan takvime uygun ilerliyorum.

**Karşılaştığım sorunlar / zorluklar:**
- Görüntü işleme algoritmalarından hangisinin sabit kamera ve tezgah ortamında en iyi sonucu vereceği henüz belirsiz, deneme-yanılma yapılması gerekiyor.

**Gelecek hafta hedefim:**
- Canny, Sobel, Prewitt, K-Means ve DBSCAN gibi algoritmaları aynı frame üzerinde deneyerek sonuçlarını karşılaştıracağım bir test scripti hazırlamak ve havluyu arka plandan ayırmak için en verimli metodu seçmek.

---
