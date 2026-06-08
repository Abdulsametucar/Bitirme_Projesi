import cv2
import numpy as np
import sys
sys.path.insert(0, 'c:/Users/Samet Uçar/Desktop/Bitirme_Projesi/havlu_takip_projesi')
from cv_engine.detector import detect_towel

def get_edge_density(video_path, frame_idx):
    cap = cv2.VideoCapture(video_path)
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
    ret, frame = cap.read()
    if not ret: return -1
    
    res = detect_towel(frame)
    if not res['bbox']: return -1
    
    x, y, w, h = res['bbox']
    edges = res['edges']
    mask = res['mask']
    
    # Kesisim alani (sadece havlu uzerindeki kenarlar)
    inner_edges = cv2.bitwise_and(edges, mask)
    
    # Sag yari (veya sag ucte birlik bolum)
    right_x = int(x + w * 0.5)
    sub_edges = inner_edges[y:y+h, right_x:x+w]
    
    density = np.sum(sub_edges > 0) / (sub_edges.shape[0] * sub_edges.shape[1] + 1e-5)
    return density

d1 = get_edge_density('c:/Users/Samet Uçar/Desktop/Bitirme_Projesi/havlu_takip_projesi/data/1.hatali_video.mp4', 350)
d2 = get_edge_density('c:/Users/Samet Uçar/Desktop/Bitirme_Projesi/havlu_takip_projesi/data/Ornek_Video.mp4', 200)

print(f"Hatali Video (One Katlama) Edge Density: {d1:.5f}")
print(f"Ornek Video (Arkaya Katlama) Edge Density: {d2:.5f}")
