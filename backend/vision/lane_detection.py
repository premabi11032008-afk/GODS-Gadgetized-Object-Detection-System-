import cv2
import numpy as np

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
    
    # Detect lines using Hough Transform
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
