"""
Detector modülünü adım adım havlu fotoğrafları üzerinde test eder.
Her adım için: orijinal görüntü, Canny kenarları, doldurulmuş maske
ve bounding box çizilmiş sonucu yan yana gösterir.
"""
import cv2
import glob
import os
from cv_engine.detector import detect_towel


def main():
    image_dir = 'data'
    pattern = os.path.join(image_dir, 'Adim_*.jpeg')
    image_paths = sorted(glob.glob(pattern))

    if not image_paths:
        print("HATA: data/ klasöründe Step_*.jpeg bulunamadı!")
        return

    print(f"Toplam {len(image_paths)} adet test görüntüsü bulundu.\n")
    print("Tuşlar: [SPACE/ENTER] → Sonraki  |  [Q] → Çıkış\n")

    for path in image_paths:
        filename = os.path.basename(path)
        frame = cv2.imread(path)
        if frame is None:
            print(f"  [!] {filename} okunamadı, atlanıyor.")
            continue

        # Performans için biraz küçült
        frame = cv2.resize(frame, (640, 480))

        result = detect_towel(frame)

        # Sonuçları yazdır
        print(f"─── {filename} ───")
        print(f"  Bounding Box : {result['bbox']}")
        print(f"  Genişlik (W) : {result['w']} px")
        print(f"  Yükseklik (H): {result['h']} px")
        print(f"  Merkez (X,Y) : ({result['center_x']}, {result['center_y']})")
        print()

        # Görselleştirme
        edges_bgr = cv2.cvtColor(result['edges'], cv2.COLOR_GRAY2BGR)
        mask_bgr = cv2.cvtColor(result['mask'], cv2.COLOR_GRAY2BGR)

        top_row = cv2.hconcat([result['frame'], edges_bgr])
        bottom_row = cv2.hconcat([mask_bgr, result['frame']])

        # Etiketler
        cv2.putText(top_row, "Bbox + Cizim", (10, 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(top_row, "Canny Kenarlari", (650, 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(bottom_row, "Dolmus Maske (Beyaz)", (10, 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        combined = cv2.vconcat([top_row, bottom_row])
        cv2.imshow(f"Detector Test - {filename}", combined)

        key = cv2.waitKey(0) & 0xFF
        cv2.destroyAllWindows()
        if key == ord('q'):
            break

    print("Test tamamlandı.")


if __name__ == '__main__':
    main()
