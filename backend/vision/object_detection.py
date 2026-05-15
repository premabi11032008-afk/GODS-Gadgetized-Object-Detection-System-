import cv2
from ultralytics import YOLO
import torch
import ultralytics.nn.tasks

if hasattr(torch.serialization, 'add_safe_globals'):
    torch.serialization.add_safe_globals([ultralytics.nn.tasks.DetectionModel])

# Load YOLOv8 nano model (lightweight, runs fast on CPU)
model = YOLO('yolov8n.pt') 

# Define relevant COCO classes for Indian roads:
# 0: person, 1: bicycle, 2: car, 3: motorcycle, 5: bus, 7: truck
# 9: traffic light, 16: dog, 17: horse, 19: cow
RELEVANT_CLASSES = [0, 1, 2, 3, 5, 7, 9, 16, 17, 19]

def detect_objects(frame):
    """
    Detect objects using YOLOv8, filter by relevant classes.
    """
    # Run YOLOv8 inference on the frame (smaller imgsz for much faster CPU inference)
    results = model(frame, imgsz=320, stream=True, verbose=False)
    detections = []
    
    for r in results:
        boxes = r.boxes
        for box in boxes:
            cls = int(box.cls[0])
            if cls in RELEVANT_CLASSES:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                conf = float(box.conf[0])
                class_name = model.names[cls]
                detections.append({
                    'box': (x1, y1, x2, y2), 
                    'class': class_name, 
                    'conf': conf
                })
    return detections

def draw_detections(frame, detections):
    """
    Draw bounding boxes and labels for the detected objects.
    """
    for det in detections:
        x1, y1, x2, y2 = det['box']
        label = f"{det['class']} {det['conf']:.2f}"
        
        # Draw bounding box
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        # Draw label
        cv2.putText(frame, label, (x1, max(30, y1 - 10)), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    return frame
