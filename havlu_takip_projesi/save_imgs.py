import cv2
import numpy as np
import sys
sys.path.insert(0, 'c:/Users/Samet Uçar/Desktop/Bitirme_Projesi/havlu_takip_projesi')
from cv_engine.detector import detect_towel

def save_imgs(video_path, frame_pos, prefix):
    cap = cv2.VideoCapture(video_path)
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_pos)
    ret, frame = cap.read()
    if not ret: return
    
    res = detect_towel(frame)
    if not res['bbox']: return
    
    x, y, w, h = res['bbox']
    edges = res['edges']
    mask = res['mask']
    
    inner_edges = cv2.bitwise_and(edges, mask)
    
    # Ust yariyi kirp
    top_y = int(y + h * 0.1)
    bottom_y = int(y + h * 0.5)
    left_x = int(x + w * 0.1)
    right_x = int(x + w * 0.9)
    
    sub_edges = inner_edges[top_y:bottom_y, left_x:right_x]
    
    cv2.imwrite(f'c:/Users/Samet Uçar/Desktop/Bitirme_Projesi/havlu_takip_projesi/{prefix}_frame.jpg', frame)
    cv2.imwrite(f'c:/Users/Samet Uçar/Desktop/Bitirme_Projesi/havlu_takip_projesi/{prefix}_edges.jpg', sub_edges)

save_imgs('c:/Users/Samet Uçar/Desktop/Bitirme_Projesi/havlu_takip_projesi/data/3.hatali_video.mp4', 550, 'state2_err')
save_imgs('c:/Users/Samet Uçar/Desktop/Bitirme_Projesi/havlu_takip_projesi/data/Ornek_Video.mp4', 380, 'state2_ok')
