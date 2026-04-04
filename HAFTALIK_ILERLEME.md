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
| 1 | 04.04 - 11.04 | Literatür araştırması, proje klasör yapısının (Flask/FastAPI, cv_engine, db) kurulması ve test videolarının ayarlanması. | %10 | 🔄 Devam Ediyor |
| 2 | 11.04 - 18.04 | Görüntü bölütleme (segmentasyon) algoritmalarının (Canny, Sobel, Prewitt, K-Means, DBSCAN vb.) test scripti ile karşılaştırılması ve en verimli yöntemin seçilmesi. | %20 | ⬜ Başlamadı |
| 3 | 25.04 - 02.05 | Seçilen algoritma ile `detector.py` modülünün yazılması. Görüntüden havlunun ayrılması, Bounding Box (sınırlayıcı kutu) ve X/Y boyutlarının anlık hesaplanması. | %30 | ⬜ Başlamadı |
| 4 | 02.05 - 09.05 | Katlama adımlarını oransal (%15, %33, %50 vb.) olarak takip edecek Durum Makinesi (State Machine) mantığının `tracker.py` içerisine kodlanması. | %40 | ⬜ Başlamadı |
| 5 | 09.05 - 16.05 | Zaman ölçüm metriklerinin sisteme entegre edilmesi. Her bir katlama aşamasının ve toplam işlemin ne kadar sürdüğünün ölçülmesi. Doğru katlama / hatalı katlama karar mantığının oluşturulması. | %50 | ⬜ Başlamadı |
| 6 | 16.05 - 23.05 | `database` modülünün ayarlanması. SQLite/PostgreSQL veritabanı tablolarının (İşçi, Havlu_Islemi, Adimlar) oluşturulması ve CRUD operasyonlarının yazılması. | %60 | ⬜ Başlamadı |
| 7 | 30.05 - 06.06 | Görüntü işleme motoru (CV Engine) ile veritabanının birbirine bağlanması. İşlenen verilerin anlık olarak veritabanına kaydedilmesi. | %70 | ⬜ Başlamadı |
| 8 | 06.06 - 13.06 | Web uygulamasının backend (main.py) ve frontend (HTML/CSS/JS) iskeletinin ayağa kaldırılması. `live_feed.html` üzerinden kamera/video akışının webe aktarılması. | %80 | ⬜ Başlamadı |
| 9 | 13.06 - 20.06 | `index.html` (Dashboard) arayüzünün geliştirilmesi. Gün sonu toplam katlanan havlu sayısı ve en iyi performans gösteren işçi verilerinin grafiksel gösterimi. | %90 | ⬜ Başlamadı |
| 10 | 20.06 - 27.06 | Sistemin uçtan uca test edilmesi, hataların (bug) giderilmesi, performans optimizasyonları ve Bitirme Projesi Raporu / Sunumu hazırlıkları. | %100 | ⬜ Başlamadı |

**Durum simgeleri:** ⬜ Başlamadı | 🔄 Devam Ediyor | ✅ Tamamlandı | ⚠️ Gecikti

---

## Haftalık İlerleme Kayıtları

> **Kullanım:** Her hafta aşağıdaki şablonu kopyalayıp doldurun. En güncel hafta en üstte olacak şekilde ekleyin.

---

### Hafta 1 *(Tarih: 04.04.2026 - 11.04.2026)*

**Plandaki hedef:**
- Literatür araştırması, proje klasör yapısının (Flask/FastAPI, cv_engine, db) kurulması ve test videolarının ayarlanması.

**Bu hafta yaptıklarım:**
- Proje kapsamı danışman hocalarla netleştirildi ve MVP (Minimum Viable Product) hedefleri belirlendi.
- Derin öğrenme yerine geleneksel görüntü işleme metotları (Canny, Sobel, eşikleme vb.) kullanılması kararlaştırıldı.
- Projenin `main.py`, `cv_engine`, `database`, `static` ve `templates` mimarisinden oluşan modüler klasör yapısı oluşturuldu.
- Sistemin üzerinde çalışacağı örnek referans havlu katlama videosu indirildi ve test klasörüne (`data/sample_video.mp4`) eklendi.

**Plana göre durumum:**
- Hedeflere ulaşıldı, planlanan takvime uygun ilerliyorum.

**Karşılaştığım sorunlar / zorluklar:**
- Görüntü işleme algoritmalarından hangisinin sabit kamera ve tezgah ortamında en iyi sonucu vereceği henüz belirsiz, deneme-yanılma yapılması gerekiyor.

**Gelecek hafta hedefim:**
- Canny, Sobel, Prewitt, K-Means ve DBSCAN gibi algoritmaları aynı frame üzerinde deneyerek sonuçlarını karşılaştıracağım bir test scripti hazırlamak ve havluyu arka plandan ayırmak için en verimli metodu seçmek.

---
