from ultralytics import YOLO
import cv2

# Try a pretrained traffic sign YOLO model (community model).
# If it fails, we will switch to the default yolov8n.pt
MODEL_NAME = "runs/detect/train2/weights/best.pt"
  # 120 classes
# MODEL_NAME = "yolov8n.pt"  # fallback (general objects, not traffic signs)

# Load YOLO model
print("Loading model, please wait...")
model = YOLO(MODEL_NAME)
print("Model loaded!")

# Open webcam
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Cannot open camera! Try changing 0 to 1 or 2.")
    raise SystemExit

print("YOLO is running. Press Q to quit.")

while True:
    ret, frame = cap.read()
    if not ret:
        print("Failed to grab frame")
        break

    # Run YOLO prediction
    results = model.predict(frame, conf=0.35, imgsz=640, verbose=False)

    # Draw detections
    annotated = results[0].plot()

    # Display
    cv2.imshow("YOLO Traffic Sign Detection", annotated)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
