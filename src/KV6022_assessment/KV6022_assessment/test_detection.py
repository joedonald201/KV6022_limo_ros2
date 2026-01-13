#!/usr/bin/env python3
"""
Test pothole detection algorithm locally (no ROS needed)
"""
import cv2
import numpy as np

def detect_pink_potholes(image):
    """
    Detect pink potholes in an image
    Returns: list of (x, y, width, height, area) tuples
    """
    # Convert BGR to HSV
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    
    # Pink color range in HSV
    # Hue: 140-170 (pink/magenta)
    # Saturation: 50-255 (not too pale)
    # Value: 50-255 (not too dark)
    lower_pink = np.array([140, 50, 50])
    upper_pink = np.array([170, 255, 255])
    
    # Create binary mask
    mask = cv2.inRange(hsv, lower_pink, upper_pink)
    
    # Optional: morphological operations to clean up mask
    kernel = np.ones((5,5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    
    # Find contours
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    potholes = []
    for contour in contours:
        area = cv2.contourArea(contour)
        
        # Filter by minimum size
        if area > 100:  # Adjust this threshold
            x, y, w, h = cv2.boundingRect(contour)
            potholes.append((x, y, w, h, area))
            
    return potholes, mask

def main():
    # Create a test image with pink regions
    print("Creating test image with pink circles...")
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    
    # Draw some pink "potholes" (BGR format: Blue=180, Green=105, Red=255)
    cv2.circle(img, (160, 120), 40, (180, 105, 255), -1)  
    cv2.circle(img, (480, 360), 60, (180, 105, 255), -1)
    cv2.circle(img, (320, 240), 30, (180, 105, 255), -1)
    
    # Add some noise (non-pink objects to test filtering)
    cv2.rectangle(img, (50, 50), (100, 100), (0, 255, 0), -1)  # Green
    cv2.circle(img, (500, 100), 25, (255, 0, 0), -1)  # Blue
    
    # Detect potholes
    potholes, mask = detect_pink_potholes(img)
    
    print(f"\n✅ Detected {len(potholes)} potholes!")
    
    # Draw bounding boxes on original image
    result = img.copy()
    for i, (x, y, w, h, area) in enumerate(potholes):
        cv2.rectangle(result, (x, y), (x+w, y+h), (0, 255, 0), 2)
        cv2.putText(result, f"#{i+1}", (x, y-10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        print(f"  Pothole #{i+1}: Position ({x}, {y}), Size: {w}x{h}, Area: {area}")
    
    # Display results
    cv2.imshow('Original Image', img)
    cv2.imshow('Binary Mask (White = Pink Detected)', mask)
    cv2.imshow('Detected Potholes', result)
    
    print("\n👀 Check the windows! Press any key to close...")
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    
    print("\n🎉 Detection test complete!")
    print("\nNext steps:")
    print("  1. Try with real pink pothole images from Gazebo")
    print("  2. Tune the HSV color range if needed")
    print("  3. Adjust the minimum area threshold")

if __name__ == "__main__":
    main()