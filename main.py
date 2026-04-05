import cv2
import mediapipe as mp
import pyautogui
import time
import math

pyautogui.FAILSAFE = False

# MediaPipe setup
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1)
mp_draw = mp.solutions.drawing_utils

# Camera
cap = cv2.VideoCapture(0)
cap.set(3, 640)
cap.set(4, 480)

screen_w, screen_h = pyautogui.size()

# Gesture control
gesture_start_time = 0
current_gesture = None
hold_time_required = 1

# Mouse state
prev_x, prev_y = 0, 0

# 🔥 Control tuning (Fixed independent margins for 640x480 resolution)
frameR_X = 200  # Left/Right margin
frameR_Y = 150  # Top/Bottom margin

# Click state
clicking = False


def count_fingers(hand_landmarks):
    fingers = []
    # Thumb logic
    if hand_landmarks.landmark[4].x < hand_landmarks.landmark[3].x:
        fingers.append(1)
    else:
        fingers.append(0)

    tips = [8, 12, 16, 20]
    for tip in tips:
        if hand_landmarks.landmark[tip].y < hand_landmarks.landmark[tip - 2].y:
            fingers.append(1)
        else:
            fingers.append(0)
    return sum(fingers)


def get_distance(p1, p2):
    return math.hypot(p2.x - p1.x, p2.y - p1.y)


while True:
    success, img = cap.read()
    if not success:
        break

    img = cv2.flip(img, 1)
    h, w, _ = img.shape

    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb)

    # Draw control box using the new X and Y margins
    cv2.rectangle(img,
                  (frameR_X, frameR_Y),
                  (w - frameR_X, h - frameR_Y),
                  (255, 0, 255), 2)

    if results.multi_hand_landmarks:
        for handLms in results.multi_hand_landmarks:
            mp_draw.draw_landmarks(img, handLms, mp_hands.HAND_CONNECTIONS)

            total_fingers = count_fingers(handLms)

            cv2.putText(img, f'Fingers: {total_fingers}', (10, 70),
                        cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 3)

            # 🖐️ MOUSE MODE
            if total_fingers >= 4:

                index = handLms.landmark[8]
                thumb = handLms.landmark[4]

                # Camera coords
                x1 = int(index.x * w)
                y1 = int(index.y * h)

                # Clamp to control box
                x1 = max(frameR_X, min(w - frameR_X, x1))
                y1 = max(frameR_Y, min(h - frameR_Y, y1))

               # Normalize (0–1)
                x_norm = (x1 - frameR_X) / (w - 2 * frameR_X)
                y_norm = (y1 - frameR_Y) / (h - 2 * frameR_Y)

                # 🔥 EXTREME OVERSCAN FIX
                # 1.35 means you only need to move ~75% of the way to the box edge 
                # to hit the absolute edge of your physical monitor.
                overscan = 1.35 
                x_norm = (x_norm - 0.5) * overscan + 0.5
                y_norm = (y_norm - 0.5) * overscan + 0.5

                # Clamp safely between 0 and 1 so mouse doesn't go out of bounds
                x_norm = max(0.0, min(1.0, x_norm))
                y_norm = max(0.0, min(1.0, y_norm))

                # Map to screen
                x = x_norm * screen_w
                y = y_norm * screen_h

                # 🔥 HIGH SENSITIVITY + ACCELERATION
                dx = x - prev_x
                dy = y - prev_y

                distance = math.hypot(dx, dy)

                # soft adaptive gain
                gain = 1 + min(distance / 50, 4)

                curr_x = prev_x + dx * 0.75 * gain
                curr_y = prev_y + dy * 0.75 * gain

                pyautogui.moveTo(curr_x, curr_y)
                prev_x, prev_y = curr_x, curr_y

                # Pinch click
                pinch_dist = get_distance(index, thumb)
                if pinch_dist < 0.035:
                    if not clicking:
                        pyautogui.mouseDown()
                        clicking = True
                else:
                    if clicking:
                        pyautogui.mouseUp()
                        clicking = False

                continue

            # 🎯 Gesture mode
            current_time = time.time()
            if total_fingers != current_gesture:
                current_gesture = total_fingers
                gesture_start_time = current_time

            elif current_time - gesture_start_time > hold_time_required:
                if current_gesture == 0:
                    pyautogui.press('space')
                elif current_gesture == 1:
                    pyautogui.hotkey('command', 'left')
                elif current_gesture == 2:
                    pyautogui.hotkey('command', 'right')
                elif current_gesture == 3:
                    pyautogui.press('space')

                gesture_start_time = current_time

    cv2.imshow("Jarvis System", img)
    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()