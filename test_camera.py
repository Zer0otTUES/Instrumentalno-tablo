import cv2

cap = cv2.VideoCapture(0)  # try 1 or 2 if 0 doesn't work

if not cap.isOpened():
    print("Cannot open camera! Try a different index (1 or 2) and close other apps using it.")
    raise SystemExit

print("Camera opened! Press Q to quit.")

while True:
    ok, frame = cap.read()
    if not ok:
        print("Failed to grab frame")
        break

    cv2.imshow("Camera Test", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
