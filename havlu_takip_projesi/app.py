import os
import sys
import time
import cv2
import numpy as np
from flask import Flask, render_template, Response, jsonify

# Script dizinini yola ekle
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from cv_engine.detector import detect_towel
from cv_engine.tracker import TowelTracker
from database.db_config import init_db
from database.crud import isci_ekle, islem_kaydet_toplu, genel_dashboard_raporu

app = Flask(__name__)

# ================================================================
# YAPILANDIRMA
# ================================================================
VIDEO_PLAYLIST = [
    os.path.join(SCRIPT_DIR, 'data', 'Video1.mp4'),
    os.path.join(SCRIPT_DIR, 'data', 'Video2.mp4'),
    os.path.join(SCRIPT_DIR, 'data', '1.hatali_video.mp4'),
    os.path.join(SCRIPT_DIR, 'data', '2.hatali_video.mp4')
]

RESIZE_WIDTH = 960
OVERLAY_ALPHA = 0.65
FONT = cv2.FONT_HERSHEY_SIMPLEX
TOTAL_FOLD_STEPS = 5

# --- Renk Filtresi Ayarlari ---
def get_hsv_limits(video_source):
    if 'Video2' in video_source:
        return np.array([90, 10, 15]), np.array([140, 255, 200])
    else:
        return np.array([95, 25, 15]), np.array([135, 255, 160])

frame_skip = 3
DEBUG_OVERLAY = True

# Renk Paleti
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

# Veritabani baslatma
init_db()
VARSAYILAN_ISCI_ID = isci_ekle('Varsayilan Isci')


# ================================================================
# YARDIMCI FONKSIYONLAR (Cizim)
# ================================================================
def draw_overlay_bg(frame, x, y, w, h, color=CLR_DARK_BG, alpha=OVERLAY_ALPHA):
    overlay = frame.copy()
    cv2.rectangle(overlay, (x, y), (x + w, y + h), color, -1)
    cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)

def draw_text(frame, text, pos, font=FONT, scale=0.55, color=CLR_WHITE, thickness=1, line_type=cv2.LINE_AA):
    x, y = pos
    cv2.putText(frame, text, (x+1, y+1), font, scale, (0,0,0), thickness+1, line_type)
    cv2.putText(frame, text, (x, y), font, scale, color, thickness, line_type)

def resize_proportional(frame, target_width):
    h, w = frame.shape[:2]
    ratio = target_width / w
    return cv2.resize(frame, (target_width, int(h * ratio)))

def draw_progress_bar(frame, x, y, w, h, current_step, total_steps, bg_color=CLR_GRAY, fill_color=CLR_PROGRESS):
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
# GENERATOR (VIDEO STREAM)
# ================================================================
def generate_frames():
    playlist_index = 0
    current_video = VIDEO_PLAYLIST[playlist_index]
    hsv_lower, hsv_upper = get_hsv_limits(current_video)
    
    cap = cv2.VideoCapture(current_video)
    
    fps_video = cap.get(cv2.CAP_PROP_FPS)
    if fps_video is None or fps_video == 0:
        fps_video = 30.0
    
    target_frame_time_ms = int(1000 / fps_video)
    tracker = TowelTracker(confirmation_frames=3, towel_lost_frames=10, debounce_time=0.5)

    frame_count = 0
    fps_timer = time.perf_counter()
    display_fps = 0.0
    last_state = 0
    transition_flash_end = 0

    last_bbox = None
    last_tx, last_ty, last_tw, last_th = 0, 0, 0, 0
    last_status = None

    while True:
        start_time = time.time()
        ret, frame = cap.read()
        
        # Video bitince sıradaki videoya geç
        if not ret:
            print(f"[INFO] Video bitti: {current_video}. Siradaki videoya geciliyor...")
            # DB'ye kaydet 
            final_status = tracker.get_status()
            if final_status.get('process') and not getattr(tracker, '_db_saved', False):
                islem_kaydet_toplu(VARSAYILAN_ISCI_ID, final_status['process'])
                tracker._db_saved = True
            
            # Sonraki videoyu ayarla
            playlist_index = (playlist_index + 1) % len(VIDEO_PLAYLIST)
            current_video = VIDEO_PLAYLIST[playlist_index]
            hsv_lower, hsv_upper = get_hsv_limits(current_video)
            
            cap.release()
            cap = cv2.VideoCapture(current_video)
            
            fps_video = cap.get(cv2.CAP_PROP_FPS)
            if fps_video is None or fps_video == 0:
                fps_video = 30.0
            target_frame_time_ms = int(1000 / fps_video)
            
            tracker = TowelTracker(confirmation_frames=3, towel_lost_frames=10, debounce_time=0.5)
            frame_count = 0
            last_bbox = None
            last_tx, last_ty, last_tw, last_th = 0, 0, 0, 0
            last_status = None
            continue

        frame = resize_proportional(frame, RESIZE_WIDTH)
        h_frame, w_frame = frame.shape[:2]

        if frame_count % frame_skip == 0:
            result = detect_towel(frame, hsv_lower=hsv_lower, hsv_upper=hsv_upper)
            if result['bbox'] is not None:
                tx, ty, tw, th = result['bbox']
                status = tracker.update(tx, ty, tw, th, edges=result['edges'], mask=result['mask'], frame=result['frame'])
            else:
                tx, ty, tw, th = 0, 0, 0, 0
                status = tracker.update(0, 0, 0, 0, edges=None, mask=None, frame=None)
            
            # Eger state bitmis ve DB ye kayit bekliyorsa
            # Normalde Tracker basarili veya basarisiz sonlandiginda logluyor. 
            # Tracker resetlendigi icin yeni dongude bastan baslar.
            
            frame = result['frame']
            last_bbox = (tx, ty, tw, th)
            last_tx, last_ty, last_tw, last_th = tx, ty, tw, th
            last_status = status
        else:
            tx, ty, tw, th = last_tx, last_ty, last_tw, last_th
            status = last_status
            if last_bbox is not None and last_tw > 0 and last_th > 0:
                cv2.rectangle(frame, (last_tx, last_ty), (last_tx + last_tw, last_ty + last_th), CLR_GREEN, 2)

        # -- Arayuz Cizimleri --
        if status:
            current_state = status['current_state']
            state_name = status['state_name']
            is_error = status['is_error']
            is_completed = status['completed']
            is_stable = status.get('is_stable', True)
            errors = status['errors']
            elapsed_total = status['elapsed_total']
            elapsed_state = status['elapsed_state']
            w_ratio = status.get('w_ratio', 0)
            h_ratio = status.get('h_ratio', 0)

            now_perf = time.perf_counter()
            if current_state != last_state:
                transition_flash_end = now_perf + 0.8
                last_state = current_state
            in_flash = now_perf < transition_flash_end

            panel_h = 180
            if errors:
                panel_h += 25 * min(len(errors), 3)

            bg_color = CLR_ERROR_BG if is_error else CLR_DARK_BG
            draw_overlay_bg(frame, 5, 5, 430, panel_h, color=bg_color)

            if is_error:
                state_color = CLR_RED
            elif in_flash:
                state_color = CLR_YELLOW
            elif is_completed and not is_error:
                state_color = CLR_SUCCESS
            else:
                state_color = CLR_GREEN

            draw_text(frame, f"State [{current_state}]: {state_name}", (15, 30), scale=0.55, color=state_color, thickness=2)

            if tw > 0:
                draw_text(frame, f"Boyut: {tw} x {th} px  |  Konum: ({tx},{ty})", (15, 55), scale=0.42, color=CLR_CYAN)
                draw_text(frame, f"W Orani: {w_ratio:.3f}  |  H Orani: {h_ratio:.3f}", (15, 78), scale=0.45, color=CLR_WHITE)
            else:
                draw_text(frame, "Havlu tespit edilemedi", (15, 55), scale=0.45, color=CLR_YELLOW)

            draw_text(frame, f"Bu adim: {elapsed_state:.1f} sn  |  Toplam: {elapsed_total:.1f} sn", (15, 103), scale=0.45, color=CLR_WHITE)

            if tracker.initial_w and tracker.initial_h:
                draw_text(frame, f"Ref: {tracker.initial_w}x{tracker.initial_h}", (15, 125), scale=0.40, color=(180, 180, 180))
                if is_stable:
                    stab_text, stab_color = "[STABIL]", CLR_GREEN
                else:
                    stab_text, stab_color = "[BEKLENIYOR...]", CLR_YELLOW
                draw_text(frame, stab_text, (230, 125), scale=0.40, color=stab_color)

            progress_step = min(current_state, TOTAL_FOLD_STEPS)
            bar_clr = CLR_RED if is_error else (CLR_SUCCESS if is_completed else CLR_PROGRESS)
            draw_text(frame, "Ilerleme:", (15, 148), scale=0.38, color=CLR_WHITE)
            draw_progress_bar(frame, 100, 138, 200, 16, progress_step, TOTAL_FOLD_STEPS, fill_color=bar_clr)
            draw_text(frame, f"{progress_step}/{TOTAL_FOLD_STEPS}", (310, 150), scale=0.38, color=CLR_WHITE)

            if errors:
                y_err = 175
                for err_msg in errors[-3:]:
                    disp = err_msg[:58] + "..." if len(err_msg) > 60 else err_msg
                    draw_text(frame, disp, (15, y_err), scale=0.38, color=CLR_RED, thickness=1)
                    y_err += 22

            if not is_stable and tw > 0 and not is_error and not is_completed:
                cv2.rectangle(frame, (0, 0), (w_frame - 1, h_frame - 1), CLR_YELLOW, 2)

            info_panel_w = 160 if DEBUG_OVERLAY else 100
            draw_overlay_bg(frame, w_frame - info_panel_w - 5, 5, info_panel_w, 55 if DEBUG_OVERLAY else 30)
            draw_text(frame, f"FPS: {display_fps:.0f}", (w_frame - info_panel_w, 25), scale=0.50, color=CLR_CYAN)

            if is_error:
                cv2.rectangle(frame, (0,0), (w_frame-1, h_frame-1), CLR_RED, 3)
                warn = "! HATALI KATLAMA !"
                ts = cv2.getTextSize(warn, FONT, 1.0, 2)[0]
                wx, wy = (w_frame - ts[0]) // 2, h_frame - 40
                draw_overlay_bg(frame, wx-15, wy-30, ts[0]+30, 45, color=CLR_ERROR_BG, alpha=0.8)
                draw_text(frame, warn, (wx, wy), scale=1.0, color=CLR_RED, thickness=2)
            elif is_completed and not is_error:
                cv2.rectangle(frame, (0,0), (w_frame-1, h_frame-1), CLR_SUCCESS, 3)
                done = "BASARILI KATLAMA"
                ts = cv2.getTextSize(done, FONT, 1.0, 2)[0]
                dx, dy = (w_frame - ts[0]) // 2, h_frame - 40
                draw_overlay_bg(frame, dx-15, dy-30, ts[0]+30, 45, color=CLR_DARK_BG, alpha=0.8)
                draw_text(frame, done, (dx, dy), scale=1.0, color=CLR_SUCCESS, thickness=2)
            
            # Eger islem tamamlandiysa DB'ye kaydet ve yeni basla 
            # Tracker birkac saniye bekledikten sonra (örn is_completed olunca) otomatik reset atmali ki diger isleme gecsin
            if is_completed or is_error:
                # Ekranda sonucu biraz gostermek icin wait de koyabiliriz veya
                # status'a process_saved gibi bir flag atayabiliriz. 
                # Simdilik sadece dongu calissin, basari veya hata olunca 
                # tracking bitti kabul ediyoruz. Gercek senaryoda tracker.reset() yapilacak
                if status.get('process') and getattr(tracker, '_db_saved', False) == False:
                    islem_kaydet_toplu(VARSAYILAN_ISCI_ID, status['process'])
                    tracker._db_saved = True # Flag to avoid multiple saves
                # Eger kadrajdan ciktiysa otomatik reset olur (tracker state_0 a doner)

        end_time = time.time()
        processing_time_ms = int((end_time - start_time) * 1000)
        delay = target_frame_time_ms - processing_time_ms
        if delay < 1: delay = 1

        if DEBUG_OVERLAY:
            draw_text(frame, f"Proc: {processing_time_ms}ms  Delay: {delay}ms", (w_frame - info_panel_w, 50), scale=0.35, color=CLR_YELLOW)

        # -- Encode and Yield --
        ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        if not ret:
            continue
        frame_bytes = buffer.tobytes()
        
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

        frame_count += 1
        if frame_count % 10 == 0:
            now = time.perf_counter()
            display_fps = 10.0 / max(now - fps_timer, 0.001)
            fps_timer = now

        # Flask ile thread bloklanmamasi icin kucuk bir sleep eklenebilir,
        # gercek hizinda oynatmak icin delay kullanacagiz:
        time.sleep(delay / 1000.0)

# ================================================================
# FLASK ROUTE'LAR
# ================================================================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    # Multipart HTTP stream
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/stats')
def api_stats():
    # Veritabanindan genel performansi dondur
    rapor = genel_dashboard_raporu()
    return jsonify(rapor)

if __name__ == '__main__':
    print("[INFO] Web arayuzu baslatiliyor: http://localhost:5000")
    # debug=False, threaded=True stream icin onemli
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
