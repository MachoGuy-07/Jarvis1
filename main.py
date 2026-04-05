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

# Mouse smoothing
prev_x, prev_y = 0, 0
smoothening = 6

# Control area
frameR = 120

# Click state
clicking = False

# Swipe variables
swipe_start_x = None
swipe_start_time = None


def count_fingers(hand_landmarks):
    fingers = []

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

    # Draw control box
    cv2.rectangle(img, (frameR, frameR),
                  (w - frameR, h - frameR),
                  (255, 0, 255), 2)

    if results.multi_hand_landmarks:
        for handLms in results.multi_hand_landmarks:

            mp_draw.draw_landmarks(img, handLms, mp_hands.HAND_CONNECTIONS)

            total_fingers = count_fingers(handLms)

            cv2.putText(img, f'Fingers: {total_fingers}', (10, 70),
                        cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 3)

            # 🖐️ MOUSE MODE (5 fingers)
            if total_fingers == 5:

                index = handLms.landmark[8]
                thumb = handLms.landmark[4]

                x1 = int(index.x * w)
                y1 = int(index.y * h)

                x1 = max(frameR, min(w - frameR, x1))
                y1 = max(frameR, min(h - frameR, y1))

                x = (x1 - frameR) * screen_w / (w - 2 * frameR)
                y = (y1 - frameR) * screen_h / (h - 2 * frameR)

                curr_x = prev_x + (x - prev_x) / smoothening
                curr_y = prev_y + (y - prev_y) / smoothening

                pyautogui.moveTo(curr_x, curr_y)
                prev_x, prev_y = curr_x, curr_y

                # Pinch click
                distance = get_distance(index, thumb)

                if distance < 0.035:
                    if not clicking:
                        pyautogui.mouseDown()
                        clicking = True
                else:
                    if clicking:
                        pyautogui.mouseUp()
                        clicking = False

                continue

            # ☝️ ONE FINGER SWIPE MODE
            if total_fingers == 1:

                x = int(handLms.landmark[8].x * w)
                current_time = time.time()

                if swipe_start_x is None:
                    swipe_start_x = x
                    swipe_start_time = current_time

                else:
                    dx = x - swipe_start_x
                    dt = current_time - swipe_start_time

                    # LEFT → RIGHT
                    if dx > w * 0.2 and dt < 0.8:
                        pyautogui.hotkey('command', 'tab')
                        swipe_start_x = None

                    # RIGHT → LEFT
                    elif dx < -w * 0.2 and dt < 0.8:
                        pyautogui.hotkey('command', 'shift', 'tab')
                        swipe_start_x = None

                    elif dt > 0.8:
                        swipe_start_x = None

                continue

            else:
                # reset swipe if hand changes
                swipe_start_x = None

            # 🎯 Gesture mode
            current_time = time.time()

            if total_fingers != current_gesture:
                current_gesture = total_fingers
                gesture_start_time = current_time

            elif current_time - gesture_start_time > hold_time_required:

                if current_gesture == 0:
                    pyautogui.press('space')

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