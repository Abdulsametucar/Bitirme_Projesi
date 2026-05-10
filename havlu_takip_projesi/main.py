"""
main.py - Havlu Katlama Takip Sistemi (OpenCV Video Dongusu)

data/Ornek_Video.mp4 videosunu okur, her kareyi detector.py'a gonderip
(x, y, w, h) koordinatlarini alir, tracker.py'a ileterek durumu gunceller.

Ekranda gosterilen bilgiler:
    - Mevcut State adi (yesil / kirmizi)
    - W x H boyutlari ve oranlari
    - Bu adimin suresi / Toplam sure
    - Ilerleme cubugu (5 adim uzerinden)
    - Hata mesaji varsa (KIRMIZI)
    - FPS gostergesi
    - Isleme suresi (ms) ve dinamik delay bilgisi

Performans Notu:
    Video oynatma hizi Delta Time mantigi ile kontrol edilir.
    Her karenin isleme suresi olculur ve cv2.waitKey() icin
    dinamik bir gecikme hesaplanir. Boylece video gercek 1x
    hizinda akar.

Cikis: 'q' tusu veya video bittiginde konsola detayli rapor yazdirir.
"""

import cv2
import time
import os
import sys
import numpy as np

# Script dizinini bul ve sys.path'e ekle (herhangi bir dizinden calistirma icin)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from cv_engine.detector import detect_towel
from cv_engine.tracker import TowelTracker

# Veritabani modulleri
from database.db_config import init_db
from database.crud import isci_ekle, islem_kaydet_toplu, gunluk_performans_raporu


# ================================================================
# YAPILANDIRMA
# ================================================================
VIDEO_SOURCE = os.path.join(SCRIPT_DIR, 'data', 'Ornek_Video.mp4')
WINDOW_NAME = 'Havlu Katlama Takip Sistemi'
RESIZE_WIDTH = 960
OVERLAY_ALPHA = 0.65
FONT = cv2.FONT_HERSHEY_SIMPLEX
TOTAL_FOLD_STEPS = 5

# Debug modu: True ise ekstra bilgiler (isleme suresi, delay) ekranda gosterilir
DEBUG_OVERLAY = True


# ================================================================
# RENK PALETI (BGR)
# ================================================================
CLR_GREEN    = (0, 220, 100)
CLR_RED      = (0, 0, 240)
CLR_YELLOW   = (0, 230, 255)
CLR_WHITE    = (255, 255, 255)
CLR_CYAN     = (230, 220, 0)
CLR_DARK_BG  = (30, 30, 30)
CLR_ERROR_BG = (30, 20, 60)
CLR_SUCCESS  = (0, 200, 80)
CLR_GRAY     = (120, 120, 120)
CLR_PROGRESS = (200, 160, 0)


# ================================================================
# YARDIMCI FONKSIYONLAR
# ================================================================

def draw_overlay_bg(frame, x, y, w, h, color=CLR_DARK_BG, alpha=OVERLAY_ALPHA):
    """Yari-saydam dikdortgen arka plan cizer."""
    overlay = frame.copy()
    cv2.rectangle(overlay, (x, y), (x + w, y + h), color, -1)
    cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)


def draw_text(frame, text, pos, font=FONT, scale=0.55, color=CLR_WHITE,
              thickness=1, line_type=cv2.LINE_AA):
    """Golge efektli metin cizer (okunabilirlik icin)."""
    x, y = pos
    cv2.putText(frame, text, (x+1, y+1), font, scale, (0,0,0),
                thickness+1, line_type)
    cv2.putText(frame, text, (x, y), font, scale, color, thickness, line_type)


def resize_proportional(frame, target_width):
    """Frame'i orantili olarak yeniden boyutlandirir."""
    h, w = frame.shape[:2]
    ratio = target_width / w
    return cv2.resize(frame, (target_width, int(h * ratio)))


def draw_progress_bar(frame, x, y, w, h, current_step, total_steps,
                      bg_color=CLR_GRAY, fill_color=CLR_PROGRESS):
    """State ilerlemesini gosteren cubuk cizer."""
    cv2.rectangle(frame, (x, y), (x+w, y+h), bg_color, -1)
    cv2.rectangle(frame, (x, y), (x+w, y+h), CLR_WHITE, 1)

    progress = min(current_step / total_steps, 1.0)
    fill_w = int(w * progress)
    if fill_w > 0:
        cv2.rectangle(frame, (x, y), (x+fill_w, y+h), fill_color, -1)

    pct_text = f"{int(progress * 100)}%"
    text_size = cv2.getTextSize(pct_text, FONT, 0.35, 1)[0]
    tx = x + (w - text_size[0]) // 2
    ty = y + (h + text_size[1]) // 2
    cv2.putText(frame, pct_text, (tx, ty), FONT, 0.35, CLR_WHITE, 1, cv2.LINE_AA)


# ================================================================
# ANA DONGU
# ================================================================

def main():
    # ---- Veritabani Baslat ----
    init_db()
    varsayilan_isci_id = isci_ekle('Varsayilan Isci')

    cap = cv2.VideoCapture(VIDEO_SOURCE)
    if not cap.isOpened():
        print(f"HATA: Video dosyasi acilamadi: {VIDEO_SOURCE}")
        return

    # ---- Videonun Gercek FPS Degerini Guvenli Oku ----
    fps_video = cap.get(cv2.CAP_PROP_FPS)
    if fps_video is None or fps_video == 0:
        fps_video = 30.0  # Varsayilan deger (FPS okunamazsa)
        print("UYARI: Video FPS degeri okunamadi, varsayilan 30 FPS kullaniliyor.")

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    # ---- Hedef Frame Suresini Hesapla (milisaniye) ----
    target_frame_time_ms = int(1000 / fps_video)

    print(f"Video: {VIDEO_SOURCE}")
    print(f"FPS: {fps_video:.1f} | Toplam Kare: {total_frames}")
    print(f"Hedef frame suresi: {target_frame_time_ms} ms")
    print(f"Cikmak icin 'q' tusuna basin.\n")

    tracker = TowelTracker(confirmation_frames=3, towel_lost_frames=10)

    frame_count = 0
    fps_timer = time.perf_counter()
    display_fps = 0.0
    last_state = 0
    transition_flash_end = 0

    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)

    while True:
        # ---- Delta Time: Dongu basinda zamani kaydet ----
        start_time = time.time()

        ret, frame = cap.read()
        if not ret:
            break

        frame = resize_proportional(frame, RESIZE_WIDTH)
        h_frame, w_frame = frame.shape[:2]

        # Detector calistir
        result = detect_towel(frame)

        # Tracker'i guncelle - artik (x, y, w, h) gonderiyor
        if result['bbox'] is not None:
            tx, ty, tw, th = result['bbox']
            status = tracker.update(tx, ty, tw, th)
        else:
            tx, ty, tw, th = 0, 0, 0, 0
            status = tracker.update(0, 0, 0, 0)

        frame = result['frame']

        # ============================================================
        # OVERLAY BILGILERI
        # ============================================================
        current_state = status['current_state']
        state_name = status['state_name']
        is_error = status['is_error']
        is_completed = status['completed']
        is_stable = status.get('is_stable', True)
        errors = status['errors']
        elapsed_total = status['elapsed_total']
        elapsed_state = status['elapsed_state']
        w_ratio = status['w_ratio']
        h_ratio = status['h_ratio']

        # State gecis flash animasyonu
        now_perf = time.perf_counter()
        if current_state != last_state:
            transition_flash_end = now_perf + 0.8
            last_state = current_state
        in_flash = now_perf < transition_flash_end

        # -- Sol ust: Bilgi paneli --
        panel_h = 180
        if errors:
            panel_h += 25 * min(len(errors), 3)

        bg_color = CLR_ERROR_BG if is_error else CLR_DARK_BG
        draw_overlay_bg(frame, 5, 5, 430, panel_h, color=bg_color)

        # State adi rengi
        if is_error:
            state_color = CLR_RED
        elif in_flash:
            state_color = CLR_YELLOW
        elif is_completed and not is_error:
            state_color = CLR_SUCCESS
        else:
            state_color = CLR_GREEN

        draw_text(frame, f"State [{current_state}]: {state_name}",
                  (15, 30), scale=0.55, color=state_color, thickness=2)

        # Boyutlar ve oranlar
        if tw > 0:
            draw_text(frame, f"Boyut: {tw} x {th} px  |  Konum: ({tx},{ty})",
                      (15, 55), scale=0.42, color=CLR_CYAN)
            draw_text(frame, f"W Orani: {w_ratio:.3f}  |  H Orani: {h_ratio:.3f}",
                      (15, 78), scale=0.45, color=CLR_WHITE)
        else:
            draw_text(frame, "Havlu tespit edilemedi",
                      (15, 55), scale=0.45, color=CLR_YELLOW)

        # Sureler
        draw_text(frame, f"Bu adim: {elapsed_state:.1f} sn  |  Toplam: {elapsed_total:.1f} sn",
                  (15, 103), scale=0.45, color=CLR_WHITE)

        # Referans boyut
        if tracker.initial_w and tracker.initial_h:
            draw_text(frame,
                      f"Ref: {tracker.initial_w}x{tracker.initial_h}",
                      (15, 125), scale=0.40, color=(180, 180, 180))

            # Stabilizasyon durumu gostergesi
            if is_stable:
                stab_text = "[STABIL]"
                stab_color = CLR_GREEN
            else:
                stab_text = "[BEKLENIYOR...]"
                stab_color = CLR_YELLOW
            draw_text(frame, stab_text,
                      (230, 125), scale=0.40, color=stab_color)

        # Ilerleme cubugu
        progress_step = min(current_state, TOTAL_FOLD_STEPS)
        bar_clr = CLR_RED if is_error else (CLR_SUCCESS if is_completed else CLR_PROGRESS)
        draw_text(frame, "Ilerleme:", (15, 148), scale=0.38, color=CLR_WHITE)
        draw_progress_bar(frame, 100, 138, 200, 16, progress_step,
                          TOTAL_FOLD_STEPS, fill_color=bar_clr)
        draw_text(frame, f"{progress_step}/{TOTAL_FOLD_STEPS}",
                  (310, 150), scale=0.38, color=CLR_WHITE)

        # Hata mesajlari (kirmizi)
        if errors:
            y_err = 175
            for err_msg in errors[-3:]:
                disp = err_msg[:58] + "..." if len(err_msg) > 60 else err_msg
                draw_text(frame, disp, (15, y_err), scale=0.38,
                          color=CLR_RED, thickness=1)
                y_err += 22

        # Stabilizasyon beklerken sari cerceve
        if not is_stable and tw > 0 and not is_error and not is_completed:
            cv2.rectangle(frame, (0, 0), (w_frame - 1, h_frame - 1),
                          CLR_YELLOW, 2)

        # -- Sag ust: FPS ve isleme suresi --
        info_panel_w = 160 if DEBUG_OVERLAY else 100
        draw_overlay_bg(frame, w_frame - info_panel_w - 5, 5, info_panel_w, 55 if DEBUG_OVERLAY else 30)
        draw_text(frame, f"FPS: {display_fps:.0f}",
                  (w_frame - info_panel_w, 25), scale=0.50, color=CLR_CYAN)

        # -- Hata / Basari cercevesi ve buyuk yazi --
        if is_error:
            cv2.rectangle(frame, (0,0), (w_frame-1, h_frame-1), CLR_RED, 3)
            warn = "! HATALI KATLAMA !"
            ts = cv2.getTextSize(warn, FONT, 1.0, 2)[0]
            wx = (w_frame - ts[0]) // 2
            wy = h_frame - 40
            draw_overlay_bg(frame, wx-15, wy-30, ts[0]+30, 45,
                            color=CLR_ERROR_BG, alpha=0.8)
            draw_text(frame, warn, (wx, wy), scale=1.0,
                      color=CLR_RED, thickness=2)

        elif is_completed and not is_error:
            cv2.rectangle(frame, (0,0), (w_frame-1, h_frame-1), CLR_SUCCESS, 3)
            done = "BASARILI KATLAMA"
            ts = cv2.getTextSize(done, FONT, 1.0, 2)[0]
            dx = (w_frame - ts[0]) // 2
            dy = h_frame - 40
            draw_overlay_bg(frame, dx-15, dy-30, ts[0]+30, 45,
                            color=CLR_DARK_BG, alpha=0.8)
            draw_text(frame, done, (dx, dy), scale=1.0,
                      color=CLR_SUCCESS, thickness=2)

        # ============================================================
        # ISLEME SURESI OLCUMU VE DINAMIK DELAY HESAPLAMA
        # ============================================================
        end_time = time.time()
        processing_time_ms = int((end_time - start_time) * 1000)

        # Dinamik delay: hedef frame suresinden isleme suresini cikar
        delay = target_frame_time_ms - processing_time_ms
        if delay <= 0:
            delay = 1  # Minimum 1 ms (cv2.waitKey(0) sonsuz bekler)

        # Debug overlay: isleme suresi ve delay bilgisini ekrana yaz
        if DEBUG_OVERLAY:
            draw_text(frame, f"Proc: {processing_time_ms}ms  Delay: {delay}ms",
                      (w_frame - info_panel_w, 50), scale=0.35, color=CLR_YELLOW)

        # ============================================================
        # GOSTERIM VE FPS
        # ============================================================
        cv2.imshow(WINDOW_NAME, frame)

        frame_count += 1
        if frame_count % 10 == 0:
            now = time.perf_counter()
            display_fps = 10.0 / max(now - fps_timer, 0.001)
            fps_timer = now

        # Dinamik bekleme: sadece arta kalan sure kadar bekle
        key = cv2.waitKey(delay) & 0xFF
        if key == ord('q'):
            print("\nKullanici tarafindan durduruldu (q).")
            break

    # ============================================================
    # TEMIZLIK, VERITABANI KAYDI VE RAPOR
    # ============================================================
    cap.release()
    cv2.destroyAllWindows()

    # Tracker raporunu konsola yazdir
    print(tracker.get_report())

    # Islem tamamlandiysa veritabanina kaydet
    final_status = tracker.get_status()
    if final_status.get('process'):
        islem_kaydet_toplu(varsayilan_isci_id, final_status['process'])
    else:
        print("[DB] Islem tamamlanmadi, veritabanina kayit yapilmadi.")


if __name__ == '__main__':
    main()
