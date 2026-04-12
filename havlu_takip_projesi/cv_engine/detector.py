import cv2
import numpy as np


def detect_towel(frame,
                 canny_low=40,
                 canny_high=120,
                 blur_ksize=5,
                 dilate_iter=2,
                 min_area_ratio=0.02):
    """
    Hibrit Havlu Tespit Algoritması  (HSV Renk Filtre + Canny Edge Detection)

    Koyu lacivert havluyu açık renkli ahşap masadan ayırır.

    Yaklaşım:
        1. HSV renk uzayında koyu mavi/lacivert havluyu maskele
        2. Canny kenar tespiti ile güçlü kenarları bul
        3. Flood-fill ile kapalı bölgelerin içini doldur
        4. HSV maskesini ana filtre olarak kullan, Canny bilgisiyle destekle
        5. Morfolojik temizlik → en büyük kontur → bounding box + boyut

    Args:
        frame:          BGR formatında giriş görüntüsü
        canny_low:      Canny alt eşik
        canny_high:     Canny üst eşik
        blur_ksize:     GaussianBlur kernel boyutu
        dilate_iter:    Dilation iterasyon sayısı
        min_area_ratio: Minimum kontur alanı oranı

    Returns:
        dict: frame, mask, edges, bbox, w, h, center_x, center_y, contour
    """

    h_img, w_img = frame.shape[:2]
    total_area = h_img * w_img

    # ═══════════════════════════════════════════════════════════════
    # 1. HSV Renk Filtresi – Koyu mavi/lacivert hedefle
    # ═══════════════════════════════════════════════════════════════
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Lacivert havlu: Hue=~100-130 (mavi aralığı),
    #   düşük-orta Saturation, düşük-orta Value
    lower_blue = np.array([95, 25, 15])
    upper_blue = np.array([135, 255, 160])
    color_mask = cv2.inRange(hsv, lower_blue, upper_blue)

    # ═══════════════════════════════════════════════════════════════
    # 2. Canny Edge Detection
    # ═══════════════════════════════════════════════════════════════
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (blur_ksize, blur_ksize), 0)
    edges = cv2.Canny(blurred, canny_low, canny_high)

    # Kenarları genişlet
    dilate_kernel = np.ones((3, 3), np.uint8)
    edges_dilated = cv2.dilate(edges, dilate_kernel, iterations=dilate_iter)

    # ═══════════════════════════════════════════════════════════════
    # 3. HSV Maskesi Üzerinde Morfolojik Temizlik
    # ═══════════════════════════════════════════════════════════════
    morph_kernel = np.ones((11, 11), np.uint8)
    # Closing: renk maskesindeki küçük delikleri kapat
    color_mask = cv2.morphologyEx(color_mask, cv2.MORPH_CLOSE, morph_kernel)
    # Opening: küçük gürültüleri temizle
    color_mask = cv2.morphologyEx(color_mask, cv2.MORPH_OPEN, morph_kernel)

    # ═══════════════════════════════════════════════════════════════
    # 4. Canny Kenarlarını HSV ile Birleştir (Kesinleştirme)
    # ═══════════════════════════════════════════════════════════════
    # Canny kenarlarından flood-fill ile kapalı iç bölgeleri bul
    close_kernel = np.ones((9, 9), np.uint8)
    edges_closed = cv2.morphologyEx(edges_dilated, cv2.MORPH_CLOSE, close_kernel)

    flood_mask = edges_closed.copy()
    fill_helper = np.zeros((h_img + 2, w_img + 2), np.uint8)
    cv2.floodFill(flood_mask, fill_helper, (0, 0), 255)
    flood_inv = cv2.bitwise_not(flood_mask)

    # Canny flood bölgesi + HSV maskesinin kesişimi → güvenilir havlu bölgesi
    # VEYA salt HSV maskesi (ana bilgi kaynağı)
    # Mantık: HSV zaten havluyu iyi buluyor, Canny sınırları hassaslaştırıyor
    intersection = cv2.bitwise_and(color_mask, flood_inv)

    # Final maske: HSV maskesini kullan, Canny kesişimi ile destekle
    combined_mask = cv2.bitwise_or(color_mask, intersection)

    # Son morfolojik düzeltme
    combined_mask = cv2.morphologyEx(
        combined_mask, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8)
    )
    combined_mask = cv2.morphologyEx(
        combined_mask, cv2.MORPH_OPEN, np.ones((7, 7), np.uint8)
    )

    # ═══════════════════════════════════════════════════════════════
    # 5. En Büyük Konturu Bul + İçini Doldur
    # ═══════════════════════════════════════════════════════════════
    contours, _ = cv2.findContours(
        combined_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    min_area = total_area * min_area_ratio
    valid_contours = [c for c in contours if cv2.contourArea(c) > min_area]

    bbox = None
    bw, bh = 0, 0
    cx, cy = 0, 0
    best_contour = None
    filled_mask = np.zeros((h_img, w_img), dtype=np.uint8)

    if valid_contours:
        best_contour = max(valid_contours, key=cv2.contourArea)

        # İçini beyazla doldur
        cv2.drawContours(filled_mask, [best_contour], -1, 255, thickness=cv2.FILLED)

        # Bounding box hesapla
        x, y, bw, bh = cv2.boundingRect(best_contour)
        bbox = (x, y, bw, bh)

        # Merkez koordinatları
        cx = x + bw // 2
        cy = y + bh // 2

        # ── Görsel Çizimler ────────────────────────────────
        # Bounding box (sarı)
        cv2.rectangle(frame, (x, y), (x + bw, y + bh), (0, 255, 255), 2)
        
        # Kontur çizgisi (yeşil, ince)
        cv2.drawContours(frame, [best_contour], -1, (0, 255, 0), 1)

        # Merkez noktası (kırmızı)
        cv2.circle(frame, (cx, cy), 5, (0, 0, 255), -1)

        # Boyut bilgisi
        cv2.putText(frame, f"W:{bw} H:{bh}",
                    (x, max(y - 10, 20)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

    return {
        'frame': frame,
        'mask': filled_mask,
        'edges': edges,
        'bbox': bbox,
        'w': bw,
        'h': bh,
        'center_x': cx,
        'center_y': cy,
        'contour': best_contour,
    }
