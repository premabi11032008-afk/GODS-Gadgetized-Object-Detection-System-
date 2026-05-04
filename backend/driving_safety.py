import cv2
import numpy as np
from ultralytics import YOLO

import torch
import ultralytics.nn.tasks
if hasattr(torch.serialization, 'add_safe_globals'):
    torch.serialization.add_safe_globals([ultralytics.nn.tasks.DetectionModel])

# 1. Initialization
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

def detect_lanes(frame):
    """
    Simple lane detection using grayscale, blur, Canny edge detection, 
    and Hough Transform focused on the lower region of the frame.
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blur, 50, 150)
    
    height, width = frame.shape[:2]
    
    # Create a mask for the region of interest (lower half of the image)
    mask = np.zeros_like(edges)
    polygon = np.array([[
        (0, height),
        (width, height),
        (width, int(height * 0.5)),
        (0, int(height * 0.5)),
    ]], np.int32)
    
    cv2.fillPoly(mask, polygon, 255)
    masked_edges = cv2.bitwise_and(edges, mask)
    
    # 3. Detect lines using Hough Transform
    lines = cv2.HoughLinesP(masked_edges, rho=1, theta=np.pi/180, threshold=150, 
                            minLineLength=150, maxLineGap=30)
    
    lane_detected = False
    if lines is not None:
        # A simple heuristic: if we detect multiple line segments, assume lanes exist
        lane_detected = len(lines) >= 2 
        for line in lines:
            x1, y1, x2, y2 = line[0]
            # Draw the lane lines in blue
            cv2.line(frame, (x1, y1), (x2, y2), (255, 0, 0), 3)
            
    return frame, lane_detected

def check_hazards(frame, detections, lane_detected):
    """
    Determine if there are any immediate hazards:
    1. Object too close (large bounding box or bottom of box near bottom frame).
    2. Lane departure warning.
    """
    height, width = frame.shape[:2]
    hazard_warning = False
    min_distance = 999.0
    max_risk_score = 0
    latest_log = "Scan active. No immediate hazards detected."
    
    # 1. Check for objects too close
    for det in detections:
        x1, y1, x2, y2 = det['box']
        box_width = x2 - x1
        box_height = y2 - y1
        box_area = box_width * box_height
        frame_area = height * width
        
        # Heuristic distance estimation
        # Increased multiplier to make distance less sensitive
        distance = max(1.0, (height / max(1, box_height)) * 3.0) 
        
        # Calculate risk score (0-100) based on distance and area
        area_ratio = box_area / frame_area
        
        # Risk drops much faster with distance (at 10m, risk is 0)
        dist_risk = max(0, 100 - (distance * 10))
        area_risk = min(100, area_ratio * 300)
        
        # Give more weight to distance
        risk_score = int(min(100, (dist_risk * 0.7) + (area_risk * 0.3)))
        
        # Update globals if this is the riskiest object
        if risk_score > max_risk_score:
            max_risk_score = risk_score
            min_distance = distance
            latest_log = f"{det['class'].capitalize()} detected at ~{distance:.1f}m (Risk: {risk_score})"
        
        # Hazard condition: Risk score > 85 (less sensitive)
        if risk_score > 85:
            hazard_warning = True
            
    if hazard_warning:
        cv2.putText(frame, "WARNING: OBJECT TOO CLOSE!", (30, 80), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 3)
                    
    # 2. Check for lane departure
    if not lane_detected:
        cv2.putText(frame, "LANE DEPARTURE WARNING!", (30, 130), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 165, 255), 3)
                    
    metadata = {
        'distance': round(min_distance, 1) if min_distance != 999.0 else None,
        'risk_score': max_risk_score,
        'log': latest_log
    }
    return frame, hazard_warning, metadata

def run_system(source=0):
    """
    Main loop to capture video, run detections, and display output.
    `source`: 0 for webcam, or string path to a video file.
    """
    cap = cv2.VideoCapture(source)
    
    if not cap.isOpened():
        print(f"Error: Could not open video source '{source}'")
        return
        
    print(f"Starting Driving Safety Prototype using source: {source}")
    print("Press 'q' in the video window to quit.")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Video stream ended or cannot be read.")
            break
            
        # Optional: resize frame for faster processing and standard aspect ratio
        frame = cv2.resize(frame, (640, 480))
        
        # -- 1. Object Detection --
        detections = detect_objects(frame)
        frame = draw_detections(frame, detections)
        
        # -- 2. Lane Detection --
        frame, lane_detected = detect_lanes(frame)
        
        # -- 3. Hazard Logic & Alerts --
        frame, hazard, metadata = check_hazards(frame, detections, lane_detected)
        
        # Display the result
        cv2.imshow("Driving Safety Prototype", frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
            
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="AI Driving Safety Prototype")
    parser.add_argument('--source', type=str, default='0', 
                        help="Video source: '0' for webcam, or path to an mp4 file")
    args = parser.parse_args()
    
    # Convert '0' (string) to 0 (int) for webcam usage
    source = int(args.source) if args.source.isdigit() else args.source
    run_system(source)
