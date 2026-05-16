import os
import cv2
from ultralytics import YOLO
import torch
import ultralytics.nn.tasks

if hasattr(torch.serialization, 'add_safe_globals'):
    torch.serialization.add_safe_globals([ultralytics.nn.tasks.DetectionModel])

# Load custom YOLOv8 model for road damage
road_model_path = r'c:\Users\HAPPY\NEW PROJECTS\DT PROJECTS\DT PROJECT  2\backend\runs\detect\road_damage_v1\weights\best.pt'
if not os.path.exists(road_model_path):
    road_model_path = 'yolov8s.pt'
road_model = YOLO(road_model_path)

# Load general pre-trained YOLOv8 model
general_model = YOLO('yolov8s.pt')

# Road damage classes from custom model
ROAD_CLASSES = [0, 1, 2, 3, 4, 5, 6, 7]

# General classes from COCO (0: person, 1: bicycle, 2: car, 3: motorcycle, 5: bus, 7: truck)
GENERAL_CLASSES = [0, 1, 2, 3, 5, 7]

def detect_objects(frame):
    """
    Detect objects using YOLOv8, filter by relevant classes from both models.
    """
    # Run YOLOv8 inference on the frame for both models
    road_results = road_model(frame, imgsz=320, stream=True, verbose=False)
    general_results = general_model(frame, imgsz=320, stream=True, verbose=False)
    
    detections = []
    
    # Process road damage detections
    for r in road_results:
        boxes = r.boxes
        for box in boxes:
            cls = int(box.cls[0])
            if cls in ROAD_CLASSES:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                conf = float(box.conf[0])
                class_name = road_model.names[cls]
                detections.append({
                    'box': (x1, y1, x2, y2), 
                    'class': class_name, 
                    'conf': conf
                })
                
    # Process general detections
    for r in general_results:
        boxes = r.boxes
        for box in boxes:
            cls = int(box.cls[0])
            if cls in GENERAL_CLASSES:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                conf = float(box.conf[0])
                class_name = general_model.names[cls]
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
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(frame, label, (x1, max(30, y1 - 10)), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    return frame
