import cv2
import numpy as np
import sys
sys.path.insert(0, 'c:/Users/Samet Uçar/Desktop/Bitirme_Projesi/havlu_takip_projesi')

def test_clahe_line(video_path, frame_pos):
    cap = cv2.VideoCapture(video_path)
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_pos)
    ret, frame = cap.read()
    if not ret: return -1
    
    from cv_engine.detector import detect_towel
    if 'Video2' in video_path:
        res = detect_towel(frame, hsv_lower=np.array([90, 10, 15]), hsv_upper=np.array([140, 255, 200]))
    else:
        res = detect_towel(frame)
        
    if not res['bbox']: return -1
    
    x, y, w, h = res['bbox']
    
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    roi_gray = gray[y:y+h, x:x+w]
    
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    cl1 = clahe.apply(roi_gray)
    
    edges = cv2.Canny(cv2.GaussianBlur(cl1, (5,5), 0), 20, 60)
    
    top_y = int(h * 0.3)
    bottom_y = int(h * 0.7)
    left_x = int(w * 0.1)
    right_x = int(w * 0.9)
    
    sub_edges = edges[top_y:bottom_y, left_x:right_x]
    
    min_len = w * 0.15
    lines = cv2.HoughLinesP(sub_edges, 1, np.pi/180, threshold=20, 
                            minLineLength=min_len, maxLineGap=40)
                            
    horizontal_count = 0
    if lines is not None:
        for line in lines:
            x1, y1, x2, y2 = line[0]
            angle = np.abs(np.arctan2(y2 - y1, x2 - x1) * 180.0 / np.pi)
            if angle < 25 or angle > 155:
                horizontal_count += 1
                
    return horizontal_count

c_err = test_clahe_line('c:/Users/Samet Uçar/Desktop/Bitirme_Projesi/havlu_takip_projesi/data/3.hatali_video.mp4', 550)
c_ok = test_clahe_line('c:/Users/Samet Uçar/Desktop/Bitirme_Projesi/havlu_takip_projesi/data/Ornek_Video.mp4', 380)
c_vid2 = test_clahe_line('c:/Users/Samet Uçar/Desktop/Bitirme_Projesi/havlu_takip_projesi/data/Video2.mp4', 220)

print(f"Hatali Video (Arkaya) Horizontal Lines (CLAHE): {c_err}")
print(f"Ornek Video (One) Horizontal Lines (CLAHE): {c_ok}")
print(f"Video2 (One) Horizontal Lines (CLAHE): {c_vid2}")
