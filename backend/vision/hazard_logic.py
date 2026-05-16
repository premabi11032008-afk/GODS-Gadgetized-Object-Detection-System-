import cv2

def check_hazards(frame, detections, lane_detected):
    """
    Determine if there are any immediate hazards:
    1. Object too close (large bounding box or bottom of box near bottom frame).
    2. Lane departure warning.
    """
    height, width = frame.shape[:2]
    hazard_warning = False
    pothole_detected = False
    min_distance = 999.0
    max_risk_score = 0
    latest_log = "Scan active. No immediate hazards detected."
    max_risk_class = None
    
    # 1. Check for objects too close
    for det in detections:
        # Check if the object is specifically a pothole
        if det['class'].lower() == 'pothole':
            pothole_detected = True

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
            max_risk_class = det['class'].lower()
        
        # Hazard condition: Risk score > 60 (more sensitive)
        if risk_score > 60:
            hazard_warning = True
            
    hazard_action = None
    if hazard_warning and max_risk_class:
        collision_classes = ['person', 'bicycle', 'car', 'motorcycle', 'bus', 'truck']
        if max_risk_class in collision_classes:
            hazard_action = "hit_brake"
        else:
            hazard_action = "slow_down"

    if hazard_warning:
        warning_text = "WARNING: OBJECT TOO CLOSE!" if hazard_action == "hit_brake" else "WARNING: ROAD DAMAGE AHEAD!"
        cv2.putText(frame, warning_text, (30, 80), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 3)
                    
    # 2. Check for lane departure
    if not lane_detected:
        cv2.putText(frame, "LANE DEPARTURE WARNING!", (30, 130), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 165, 255), 3)
                    
    metadata = {
        'distance': round(min_distance, 1) if min_distance != 999.0 else None,
        'risk_score': max_risk_score,
        'log': latest_log,
        'pothole_detected': pothole_detected,
        'hazard_action': hazard_action
    }
    return frame, hazard_warning, metadata
