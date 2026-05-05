import requests
import cv2
import mediapipe as mp
import numpy as np
from scipy.spatial import distance
import threading
import winsound

# 🔊 Alarm control (no spam)
alarm_on = False
 
def start_alarm():
    winsound.PlaySound("loud_alarm_sound.wav", winsound.SND_ASYNC)

def stop_alarm():
    winsound.PlaySound(None, winsound.SND_PURGE)

# 📡 URLs
CAMERA_URL = "http://10.48.82.94:81/stream"
ESP32_IP = "http://10.48.82.94"

cap = cv2.VideoCapture(CAMERA_URL)

if not cap.isOpened():
    print("❌ Cannot open camera")
    exit()

# 🎯 MediaPipe setup
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(refine_landmarks=True)

# 👁️ Eye landmarks
LEFT_EYE = [33, 160, 158, 133, 153, 144]
RIGHT_EYE = [362, 385, 387, 263, 373, 380]

# 📏 EAR function
def eye_aspect_ratio(eye):
    A = distance.euclidean(eye[1], eye[5])
    B = distance.euclidean(eye[2], eye[4])
    C = distance.euclidean(eye[0], eye[3])
    return (A + B) / (2.0 * C)

# 🚨 Parameters
THRESHOLD = 0.20
FRAME_CHECK = 15
flag = 0

while True:
    ret, frame = cap.read()

    if not ret:
        print("⚠️ Frame not received, retrying...")
        continue

    # 🔥 Upscale for better detection
    frame = cv2.resize(frame, (480,320))
    frame = cv2.flip(frame, 1)

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(rgb)

    if results.multi_face_landmarks:
        for face_landmarks in results.multi_face_landmarks:
            h, w, _ = frame.shape

            left_eye = []
            right_eye = []

            # Left eye
            for idx in LEFT_EYE:
                x = int(face_landmarks.landmark[idx].x * w)
                y = int(face_landmarks.landmark[idx].y * h)
                left_eye.append((x, y))
                cv2.circle(frame, (x, y), 2, (0,255,0), -1)

            # Right eye
            for idx in RIGHT_EYE:
                x = int(face_landmarks.landmark[idx].x * w)
                y = int(face_landmarks.landmark[idx].y * h)
                right_eye.append((x, y))
                cv2.circle(frame, (x, y), 2, (0,255,0), -1)

            left_eye = np.array(left_eye)
            right_eye = np.array(right_eye)

            leftEAR = eye_aspect_ratio(left_eye)
            rightEAR = eye_aspect_ratio(right_eye)
            ear = (leftEAR + rightEAR) / 2.0

            # Display EAR
            cv2.putText(frame, f"EAR: {ear:.2f}", (30, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,0,255), 2)

            # 🚨 DROWSINESS LOGIC
            if ear < THRESHOLD:
                flag += 1

                if flag >= FRAME_CHECK:
                    cv2.putText(frame, "DROWSINESS DETECTED!",
                                (50, 100),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                1, (0,0,255), 3)

                    # 🔊 Alarm ON (only once)
                    if not alarm_on:
                        start_alarm()
                        alarm_on = True

                    # 🔥 Buzzer ON
                    try:
                        requests.get(f"{ESP32_IP}/on", timeout=0.5)
                    except:
                        pass

            else:
                flag = 0

                # 🔊 Alarm OFF
                if alarm_on:
                    stop_alarm()
                    alarm_on = False

                # 🔕 Buzzer OFF
                try:
                    requests.get(f"{ESP32_IP}/off", timeout=0.5)
                except:
                    pass

    cv2.imshow("Drowsiness Detection", frame)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows() 