import cv2
import numpy as np
import sys
sys.path.insert(0, 'c:/Users/Samet Uçar/Desktop/Bitirme_Projesi/havlu_takip_projesi')
from cv_engine.detector import detect_towel

def test_horizontal_line(video_path, frame_pos):
    cap = cv2.VideoCapture(video_path)
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_pos)
    ret, frame = cap.read()
    if not ret: return -1
    
    res = detect_towel(frame)
    if not res['bbox']: return -1
    
    x, y, w, h = res['bbox']
    edges = res['edges']
    mask = res['mask']
    
    inner_edges = cv2.bitwise_and(edges, mask)
    
    top_y = int(y + h * 0.1)
    bottom_y = int(y + h * 0.5)
    left_x = int(x + w * 0.1)
    right_x = int(x + w * 0.9)
    
    sub_edges = inner_edges[top_y:bottom_y, left_x:right_x]
    
    # Toleransi dusuruyoruz: W'nin %15'i kadar olsun
    min_len = w * 0.15
    lines = cv2.HoughLinesP(sub_edges, 1, np.pi/180, threshold=30, 
                            minLineLength=min_len, maxLineGap=40)
                            
    horizontal_count = 0
    if lines is not None:
        for line in lines:
            x1, y1, x2, y2 = line[0]
            angle = np.abs(np.arctan2(y2 - y1, x2 - x1) * 180.0 / np.pi)
            if angle < 30 or angle > 150: # Daha genis aci toleransi (+/- 30)
                horizontal_count += 1
                
    return horizontal_count

c_err = test_horizontal_line('c:/Users/Samet Uçar/Desktop/Bitirme_Projesi/havlu_takip_projesi/data/3.hatali_video.mp4', 550)
c_ok = test_horizontal_line('c:/Users/Samet Uçar/Desktop/Bitirme_Projesi/havlu_takip_projesi/data/Ornek_Video.mp4', 380) # 450'de state 3'te olabilir, biraz geriye alalim

print(f"Hatali Video (Arkaya) Horizontal Lines: {c_err}")
print(f"Ornek Video (One) Horizontal Lines: {c_ok}")
