import cv2
import sys
sys.path.insert(0, 'c:/Users/Samet Uçar/Desktop/Bitirme_Projesi/havlu_takip_projesi')
from cv_engine.tracker import TowelTracker
from cv_engine.detector import detect_towel

def test_video(video_path):
    cap = cv2.VideoCapture(video_path)
    tracker = TowelTracker(confirmation_frames=10) # main.py'de oyle baslatiliyor
    
    # We will monkey-patch the tracker to print the count
    original_check = tracker._check_horizontal_fold_line
    def patched_check(x, y, w, h, frame, expected_direction):
        import numpy as np
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        roi_gray = gray[y:y+h, x:x+w]
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        cl1 = clahe.apply(roi_gray)
        roi_edges = cv2.Canny(cv2.GaussianBlur(cl1, (5,5), 0), 20, 60)
        roi_mask = mask[y:y+h, x:x+w]
        roi_edges = cv2.bitwise_and(roi_edges, roi_mask)
        top_y = int(h * 0.3)
        bottom_y = int(h * 0.7)
        left_x = int(w * 0.1)
        right_x = int(w * 0.9)
        sub_edges = roi_edges[top_y:bottom_y, left_x:right_x]
        min_len = w * 0.15
        lines = cv2.HoughLinesP(sub_edges, 1, np.pi/180, threshold=20, minLineLength=min_len, maxLineGap=40)
        horizontal_count = 0
        if lines is not None:
            for line in lines:
                x1, y1, x2, y2 = line[0]
                angle = np.abs(np.arctan2(y2 - y1, x2 - x1) * 180.0 / np.pi)
                if angle < 25 or angle > 155:
                    horizontal_count += 1
        
        print(f"FRAME {frame_count}: Transitioning to State 2. horizontal_count = {horizontal_count}")
        return original_check(x, y, w, h, frame, expected_direction)
        
    tracker._check_horizontal_fold_line = patched_check

    frame_count = 0
    frame_skip = 3 # main.py'deki frame_skip
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret: break
        
        if frame_count % frame_skip == 0:
            res = detect_towel(frame)
            if res['bbox']:
                tx, ty, tw, th = res['bbox']
                tracker.update(tx, ty, tw, th, edges=res['edges'], mask=res['mask'], frame=res['frame'])
                if tracker.is_error:
                    print(f"Error triggered at frame {frame_count}: {tracker.errors[-1]}")
                    break
        frame_count += 1
        
    if not tracker.is_error:
        print("Video completed without error. Final state:", tracker.current_state)

print("Testing 3.hatali_video.mp4:")
test_video('c:/Users/Samet Uçar/Desktop/Bitirme_Projesi/havlu_takip_projesi/data/3.hatali_video.mp4')
