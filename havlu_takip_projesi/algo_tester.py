import cv2
import numpy as np

def on_trackbar(val):
    pass

video_path = 'data/Ornek_Video.mp4' 
cap = cv2.VideoCapture(video_path)

cv2.namedWindow("Canny Ayarlari")
cv2.createTrackbar("Alt Esik", "Canny Ayarlari", 50, 255, on_trackbar)
cv2.createTrackbar("Ust Esik", "Canny Ayarlari", 150, 255, on_trackbar)

while True:
    ret, frame = cap.read()
    if not ret:
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        continue

    # Performans için görüntüyü biraz küçültelim (K-Means'in videoyu dondurmaması için)
    frame = cv2.resize(frame, (640, 360))
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # ---------------------------------------------------------
    # 1. SOBEL EDGE DETECTOR (Türev tabanlı kenar bulma)
    # ---------------------------------------------------------
    sobelx = cv2.Sobel(blurred, cv2.CV_64F, 1, 0, ksize=3)
    sobely = cv2.Sobel(blurred, cv2.CV_64F, 0, 1, ksize=3)
    sobel_combined = cv2.magnitude(sobelx, sobely)
    sobel_combined = np.uint8(sobel_combined)

    # ---------------------------------------------------------
    # 2. CANNY EDGE DETECTOR (En popüler ve optimize kenar bulucu)
    # ---------------------------------------------------------
    lower_thresh = cv2.getTrackbarPos("Alt Esik", "Canny Ayarlari")
    upper_thresh = cv2.getTrackbarPos("Ust Esik", "Canny Ayarlari")
    canny_edges = cv2.Canny(blurred, lower_thresh, upper_thresh)

    # Canny kenarlarını birleştirmek için ufak bir genişletme (Dilation) yapalım
    kernel = np.ones((3,3), np.uint8)
    canny_dilated = cv2.dilate(canny_edges, kernel, iterations=1)

    # ---------------------------------------------------------
    # 3. K-MEANS CLUSTERING (Renk Kümeleme)
    # ---------------------------------------------------------
    # K-Means için veriyi düzleştiriyoruz (reshape) ve float32 yapıyoruz
    Z = frame.reshape((-1, 3))
    Z = np.float32(Z)
    
    # Kriterler: Maksimum 10 iterasyon veya 1.0 epsilon hassasiyeti
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
    K = 3 # Görüntüyü sadece 3 renge indirgeyeceğiz (Masa, Havlu, Kollar/Arka plan)
    
    _, label, center = cv2.kmeans(Z, K, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
    
    # Merkezleri tam sayıya çevirip görüntüyü yeniden oluşturuyoruz
    center = np.uint8(center)
    res = center[label.flatten()]
    kmeans_result = res.reshape((frame.shape))

    # ---------------------------------------------------------
    # EKRANDA GÖSTERİM
    # ---------------------------------------------------------
    cv2.imshow("0- Orijinal Goruntu", frame)
    cv2.imshow("1- Sobel", sobel_combined)
    cv2.imshow("2- Canny (Trackbar ile ayarla)", canny_dilated)
    cv2.imshow("3- K-Means (3 Renk)", kmeans_result)

    key = cv2.waitKey(30) & 0xFF
    if key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()