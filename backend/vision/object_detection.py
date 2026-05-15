import os
import cv2
from ultralytics import YOLO
import torch
import ultralytics.nn.tasks

if hasattr(torch.serialization, 'add_safe_globals'):
    torch.serialization.add_safe_globals([ultralytics.nn.tasks.DetectionModel])

# Load custom YOLOv8 model for road damage
# Fallback to yolov8n.pt if training is not completely finished yet
model_path = r'c:\Users\HAPPY\NEW PROJECTS\DT PROJECTS\DT PROJECT  2\runs\detect\road_damage_v1\weights\best.pt'
if not os.path.exists(model_path):
    model_path = 'yolov8s.pt' # Training uses 8s, so fallback to generic 8s

model = YOLO(model_path) 

# All road damage classes from our trained dataset
# 0: alligator cracking, 1: edge cracking, 2: longitudinal cracking
# 3: manhole, 4: patching, 5: pothole, 6: rutting, 7: transverse cracking
RELEVANT_CLASSES = [0, 1, 2, 3, 4, 5, 6, 7]

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
