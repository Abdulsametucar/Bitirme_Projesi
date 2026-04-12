"""
TowelTracker test: Adım adım fotoğraflardan okunan gerçek boyutları
simüle ederek state machine geçişlerini doğrular.
"""
import cv2
import glob
import os
from cv_engine.detector import detect_towel
from cv_engine.tracker import TowelTracker


def main():
    # ── Tracker oluştur (confirmation_frames=1 çünkü fotoğraf bazlı test) ──
    tracker = TowelTracker(confirmation_frames=1)

    image_dir = 'data'
    pattern = os.path.join(image_dir, 'Adim_*.jpeg')
    image_paths = sorted(glob.glob(pattern))

    if not image_paths:
        print("HATA: data/ klasöründe Adim_*.jpeg bulunamadı!")
        return

    print(f"Toplam {len(image_paths)} adet test görüntüsü bulundu.\n")
    print("=" * 65)

    for path in image_paths:
        filename = os.path.basename(path)
        frame = cv2.imread(path)
        if frame is None:
            print(f"  [!] {filename} okunamadı")
            continue

        frame = cv2.resize(frame, (640, 480))
        result = detect_towel(frame)

        if result['bbox']:
            w, h = result['w'], result['h']
            status = tracker.update(w, h)

            print(f"─── {filename} ───")
            print(f"  Detector  : W={w:4d}  H={h:4d}")
            print(f"  W Oranı   : {status['w_ratio']:.3f}  |  H Oranı : {status['h_ratio']:.3f}")
            print(f"  State     : [{status['current_state']}] {status['state_name']}")
            if status['errors']:
                for err in status['errors']:
                    print(f"  ⚠ HATA    : {err}")
            print()
        else:
            print(f"─── {filename} ─── Havlu bulunamadı!")
            # Havlu masadan kalktı simülasyonu
            status = tracker.update(0, 0)
            print(f"  State     : [{status['current_state']}] {status['state_name']}")
            print()

    # Son durum raporu
    print("=" * 65)
    print("SONUÇ RAPORU:")
    print(tracker.get_status_text())

    if tracker.steps:
        print("\nGeçiş Geçmişi:")
        for step in tracker.steps:
            print(f"  → {step['name']}  |  W:{step['w_ratio']:.3f}  H:{step['h_ratio']:.3f}"
                  f"  |  Süre: {step['duration_seconds']:.2f} sn")


if __name__ == '__main__':
    main()
