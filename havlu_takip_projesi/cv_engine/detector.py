"""
detector.py - Hibrit Havlu Tespit Modulu (HSV + Ten Rengi Filtresi + DBSCAN)

Koyu lacivert havluyu acik renkli ahsap masadan ayirir.

Yaklasim (Pipeline):
    1. HSV renk uzayinda koyu mavi/lacivert havluyu maskele
    1b. Ten rengi (skin color) filtresi - iscinin ellerini/kollarini cikar
    2. DBSCAN kumeleme ile HSV maskesindeki bolgeleri dogrula ve
       gurultu noktalarini (outlier) temizle
    3. Morfolojik temizlik (closing + opening)
    4. Canny kenar tespiti ile sinir hassaslastirmasi
    5. En buyuk kontur -> BoundingRect -> (x, y, w, h)

Performans Notu:
    DBSCAN tum pikseller uzerinde calistirilmaz. Sadece HSV maske ile
    on-filtrelenmis beyaz pikseller, uzaysal koordinatlariyla birlikte
    DBSCAN'e verilir. Ayrica goruntuyu kucultme (downsample) uygulanarak
    gercek zamanli calisma saglanir.

Returns (dict):
    frame      : Uzerine cizim yapilmis BGR goruntusu
    mask       : Doldurulmus ikili maske
    edges      : Canny kenar goruntusu
    bbox       : (x, y, w, h) tuple veya None
    x, y, w, h : BoundingRect koordinatlari (int)
    center_x   : Havlu merkezi X
    center_y   : Havlu merkezi Y
    contour    : En buyuk kontur (numpy array) veya None
"""

import cv2
import numpy as np
from sklearn.cluster import DBSCAN


# =================================================================
# DBSCAN YARDIMCI: HSV maskesinden anlamli kumeyi cikart
# =================================================================

def _dbscan_refine_mask(binary_mask, eps=8, min_samples=20, downsample=4):
    """
    HSV maskesindeki beyaz pikselleri DBSCAN ile kumeler,
    en buyuk kumeyi koruyup gerisi noise olarak temizler.

    Performans icin goruntu once 'downsample' kati kucultulur.

    Args:
        binary_mask:  uint8 ikili maske (0 veya 255)
        eps:          DBSCAN komsuluk mesafesi (piksel)
        min_samples:  DBSCAN minimum nokta sayisi
        downsample:   Kucultme kati (4 = 1/4 boyut)

    Returns:
        refined_mask: Temizlenmis uint8 ikili maske (orijinal boyut)
    """
    h_orig, w_orig = binary_mask.shape[:2]

    # Kucult
    small_mask = cv2.resize(binary_mask, (w_orig // downsample, h_orig // downsample),
                            interpolation=cv2.INTER_NEAREST)

    # Beyaz piksel koordinatlarini al
    coords = np.column_stack(np.where(small_mask > 0))

    if len(coords) < min_samples:
        # Yeterli piksel yoksa maskeyi oldugu gibi dondur
        return binary_mask

    # DBSCAN kumeleme (uzaysal koordinatlar uzerinde)
    clustering = DBSCAN(eps=eps, min_samples=min_samples).fit(coords)
    labels = clustering.labels_

    # En buyuk kumeyi bul (noise = -1 label)
    unique_labels = set(labels)
    unique_labels.discard(-1)

    if not unique_labels:
        return binary_mask

    # Her kumenin piksel sayisini hesapla, en buyugunu sec
    best_label = max(unique_labels, key=lambda lb: np.sum(labels == lb))

    # Kucuk boyutta temiz maske olustur
    clean_small = np.zeros_like(small_mask)
    best_coords = coords[labels == best_label]
    clean_small[best_coords[:, 0], best_coords[:, 1]] = 255

    # Orijinal boyuta geri buyut
    refined_mask = cv2.resize(clean_small, (w_orig, h_orig),
                              interpolation=cv2.INTER_NEAREST)

    return refined_mask


# =================================================================
# TEN RENGI FILTRESI: Iscinin ellerini/kollarini cikar
# =================================================================

def _create_skin_mask(frame_bgr, hsv_img=None):
    """
    HSV + YCrCb uzayinda ten rengine uyan pikselleri tespit eder.

    Iki renk uzayinin kesisimi kullanilarak daha guvenilir sonuc elde edilir.
    Sonuc olarak ten rengine uyan bolgeleri gosteren ikili maske dondurulur.

    Args:
        frame_bgr: BGR formatinda giris goruntusu
        hsv_img:   Onceden hesaplanmis HSV goruntusu (performans icin)

    Returns:
        skin_mask: uint8 ikili maske (255 = ten rengi, 0 = degil)
    """
    if hsv_img is None:
        hsv_img = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)

    # HSV uzayinda ten rengi araligi
    # Hue: 0-25 (kirmizi-turuncu), Sat: 30-170, Val: 60-255
    lower_skin_hsv = np.array([0, 30, 60])
    upper_skin_hsv = np.array([25, 170, 255])
    skin_hsv = cv2.inRange(hsv_img, lower_skin_hsv, upper_skin_hsv)

    # YCrCb uzayinda ten rengi araligi (HSV'yi destekler)
    ycrcb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2YCrCb)
    lower_skin_ycrcb = np.array([0, 135, 85])
    upper_skin_ycrcb = np.array([255, 180, 135])
    skin_ycrcb = cv2.inRange(ycrcb, lower_skin_ycrcb, upper_skin_ycrcb)

    # Iki maskenin kesisimi (daha az false positive)
    skin_mask = cv2.bitwise_and(skin_hsv, skin_ycrcb)

    # Morfolojik temizlik: kucuk delikleri kapat, gurultuleri sil
    k = np.ones((7, 7), np.uint8)
    skin_mask = cv2.morphologyEx(skin_mask, cv2.MORPH_CLOSE, k)
    skin_mask = cv2.morphologyEx(skin_mask, cv2.MORPH_OPEN, k)

    # Ten bolgelerini biraz genislet (havlu kenarindaki gecisin temizlenmesi)
    skin_mask = cv2.dilate(skin_mask, np.ones((9, 9), np.uint8), iterations=2)

    return skin_mask


# =================================================================
# ANA TESPIT FONKSIYONU
# =================================================================

def detect_towel(frame,
                 canny_low=40,
                 canny_high=120,
                 blur_ksize=5,
                 dilate_iter=2,
                 min_area_ratio=0.02,
                 use_dbscan=True,
                 dbscan_eps=8,
                 dbscan_min_samples=20,
                 dbscan_downsample=4,
                 use_skin_filter=True):
    """
    Hibrit Havlu Tespit Algoritmasi (HSV + Ten Filtresi + DBSCAN + Canny)

    Koyu lacivert havluyu acik renkli ahsap masadan ayirir.
    Iscinin elleri/kollari ten rengi filtresiyle cikarilir.

    Args:
        frame:              BGR formatinda giris goruntusu
        canny_low:          Canny alt esik
        canny_high:         Canny ust esik
        blur_ksize:         GaussianBlur kernel boyutu
        dilate_iter:        Dilation iterasyon sayisi
        min_area_ratio:     Minimum kontur alani orani
        use_dbscan:         DBSCAN filtreleme aktif mi
        dbscan_eps:         DBSCAN komsuluk mesafesi
        dbscan_min_samples: DBSCAN minimum nokta sayisi
        dbscan_downsample:  DBSCAN icin kucultme kati
        use_skin_filter:    Ten rengi filtresi aktif mi

    Returns:
        dict: frame, mask, edges, bbox, x, y, w, h, center_x, center_y, contour
    """

    h_img, w_img = frame.shape[:2]
    total_area = h_img * w_img

    # =============================================================
    # 1. HSV RENK FILTRESI - Koyu mavi/lacivert hedefle
    # =============================================================
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Lacivert havlu: Hue=~95-135 (mavi araligi),
    #   dusuk-orta Saturation, dusuk-orta Value
    lower_blue = np.array([95, 25, 15])
    upper_blue = np.array([135, 255, 160])
    color_mask = cv2.inRange(hsv, lower_blue, upper_blue)

    # =============================================================
    # 1b. TEN RENGI FILTRESI - Iscinin ellerini cikar
    # =============================================================
    # Ten rengine uyan pikselleri havlu maskesinDEN cikarir.
    # Boylece Bounding Box sadece havlunun etrafinda kalir,
    # iscinin elleri/kollari dahil edilmez.
    if use_skin_filter:
        skin_mask = _create_skin_mask(frame, hsv_img=hsv)
        # Ten bolgelerini havlu maskesinden cikar
        color_mask = cv2.bitwise_and(color_mask, cv2.bitwise_not(skin_mask))

    # =============================================================
    # 2. DBSCAN KUMELEME - Gurultu temizleme
    # =============================================================
    # HSV maskesindeki beyaz pikselleri DBSCAN ile kumeleyerek
    # rastgele gurultu noktalarini (outlier) temizle.
    # Sadece en buyuk kume korunur.
    if use_dbscan:
        color_mask = _dbscan_refine_mask(
            color_mask,
            eps=dbscan_eps,
            min_samples=dbscan_min_samples,
            downsample=dbscan_downsample
        )

    # =============================================================
    # 3. MORFOLOJIK TEMIZLIK
    # =============================================================
    morph_kernel = np.ones((11, 11), np.uint8)
    # Closing: renk maskesindeki kucuk delikleri kapat
    color_mask = cv2.morphologyEx(color_mask, cv2.MORPH_CLOSE, morph_kernel)
    # Opening: kucuk gurultuleri temizle
    color_mask = cv2.morphologyEx(color_mask, cv2.MORPH_OPEN, morph_kernel)

    # =============================================================
    # 4. CANNY KENAR TESPITI - Sinir hassaslastirma
    # =============================================================
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (blur_ksize, blur_ksize), 0)
    edges = cv2.Canny(blurred, canny_low, canny_high)

    # Kenarlari genislet
    dilate_kernel = np.ones((3, 3), np.uint8)
    edges_dilated = cv2.dilate(edges, dilate_kernel, iterations=dilate_iter)

    # Canny kenarlarindan flood-fill ile kapali ic bolgeleri bul
    close_kernel = np.ones((9, 9), np.uint8)
    edges_closed = cv2.morphologyEx(edges_dilated, cv2.MORPH_CLOSE, close_kernel)

    flood_mask = edges_closed.copy()
    fill_helper = np.zeros((h_img + 2, w_img + 2), np.uint8)
    cv2.floodFill(flood_mask, fill_helper, (0, 0), 255)
    flood_inv = cv2.bitwise_not(flood_mask)

    # HSV maskesini Canny bilgisiyle destekle
    intersection = cv2.bitwise_and(color_mask, flood_inv)
    combined_mask = cv2.bitwise_or(color_mask, intersection)

    # Son morfolojik duzeltme
    combined_mask = cv2.morphologyEx(
        combined_mask, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8)
    )
    combined_mask = cv2.morphologyEx(
        combined_mask, cv2.MORPH_OPEN, np.ones((7, 7), np.uint8)
    )

    # =============================================================
    # 5. EN BUYUK KONTURU BUL + BOUNDING BOX
    # =============================================================
    contours, _ = cv2.findContours(
        combined_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    min_area = total_area * min_area_ratio
    valid_contours = [c for c in contours if cv2.contourArea(c) > min_area]

    bbox = None
    bx, by, bw, bh = 0, 0, 0, 0
    cx, cy = 0, 0
    best_contour = None
    filled_mask = np.zeros((h_img, w_img), dtype=np.uint8)

    if valid_contours:
        best_contour = max(valid_contours, key=cv2.contourArea)

        # Icini beyazla doldur
        cv2.drawContours(filled_mask, [best_contour], -1, 255,
                         thickness=cv2.FILLED)

        # Bounding box hesapla
        bx, by, bw, bh = cv2.boundingRect(best_contour)
        bbox = (bx, by, bw, bh)

        # Merkez koordinatlari
        cx = bx + bw // 2
        cy = by + bh // 2

        # -- Gorsel Cizimler --
        # Bounding box (sari)
        cv2.rectangle(frame, (bx, by), (bx + bw, by + bh), (0, 255, 255), 2)

        # Kontur cizgisi (yesil, ince)
        cv2.drawContours(frame, [best_contour], -1, (0, 255, 0), 1)

        # Merkez noktasi (kirmizi)
        cv2.circle(frame, (cx, cy), 5, (0, 0, 255), -1)

        # Boyut bilgisi
        cv2.putText(frame, f"W:{bw} H:{bh}",
                    (bx, max(by - 10, 20)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

    return {
        'frame': frame,
        'mask': filled_mask,
        'edges': edges,
        'bbox': bbox,
        'x': bx,
        'y': by,
        'w': bw,
        'h': bh,
        'center_x': cx,
        'center_y': cy,
        'contour': best_contour,
    }
