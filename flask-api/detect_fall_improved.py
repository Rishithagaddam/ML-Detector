import torch
import cv2
import numpy as np
from pathlib import Path
import math

class ImprovedFallDetector:
    """Improved fall detector with better logic for detecting falls"""
    
    def __init__(self):
        # Load pre-trained YOLOv5 model
        self.model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True)
        self.model.conf = 0.15  # Lower confidence threshold for better detection
        
    def detect_fall_in_image(self, image_path, save_path=None):
        """Enhanced fall detection using multiple criteria"""
        
        # Load image
        img = cv2.imread(image_path)
        if img is None:
            return {"error": "Could not load image"}
        
        # Run detection
        results = self.model(img)
        
        # Get person detections
        persons = []
        fall_detected = False
        
        for *box, conf, cls in results.xyxy[0].cpu().numpy():
            if int(cls) == 0 and conf > 0.15:  # Person class with lower threshold
                x1, y1, x2, y2 = map(int, box)
                
                # Calculate various fall indicators
                width = x2 - x1
                height = y2 - y1
                aspect_ratio = width / height if height > 0 else 0
                
                # Get center position
                center_x = (x1 + x2) / 2
                center_y = (y1 + y2) / 2
                
                # Multiple fall detection criteria
                fall_indicators = []
                fall_score = 0
                
                # 1. Aspect ratio check (horizontal orientation)
                if aspect_ratio > 1.2:  # More lenient than before
                    fall_indicators.append("horizontal_orientation")
                    fall_score += 0.3
                
                # 2. Low height relative to width (person lying down)
                if aspect_ratio > 0.8:  # Even if not fully horizontal
                    fall_indicators.append("low_height_ratio")
                    fall_score += 0.2
                
                # 3. Position in image (falls often happen in lower portions)
                vertical_position = center_y / img.shape[0]
                if vertical_position > 0.4:  # Lower half of image
                    fall_indicators.append("lower_position")
                    fall_score += 0.2
                
                # 4. Small height relative to image (person compressed/fallen)
                height_ratio = height / img.shape[0]
                if height_ratio < 0.6:  # Less than 60% of image height
                    fall_indicators.append("compressed_height")
                    fall_score += 0.3
                
                # 5. Unusual aspect ratio (very wide or unusual proportions)
                if aspect_ratio > 1.5 or (aspect_ratio > 1.0 and height_ratio < 0.4):
                    fall_indicators.append("unusual_proportions")
                    fall_score += 0.4
                
                # 6. Check if person is more horizontal than vertical
                if width > height:
                    fall_indicators.append("width_exceeds_height")
                    fall_score += 0.3
                
                # Determine if this is a fall (multiple criteria or high score)
                is_fallen = fall_score >= 0.4 or len(fall_indicators) >= 2
                
                persons.append({
                    "bbox": [x1, y1, x2, y2],
                    "confidence": float(conf),
                    "fallen": is_fallen,
                    "fall_score": fall_score,
                    "fall_indicators": fall_indicators,
                    "aspect_ratio": aspect_ratio,
                    "height_ratio": height_ratio,
                    "vertical_position": vertical_position
                })
                
                if is_fallen:
                    fall_detected = True
        
        # Save annotated image if requested
        if save_path and persons:
            annotated_img = img.copy()
            for person in persons:
                x1, y1, x2, y2 = person["bbox"]
                color = (0, 0, 255) if person["fallen"] else (0, 255, 0)  # Red for fallen, green for standing
                thickness = 3 if person["fallen"] else 2
                cv2.rectangle(annotated_img, (x1, y1), (x2, y2), color, thickness)
                
                if person["fallen"]:
                    label = f"FALL DETECTED {person['confidence']:.2f} (Score: {person['fall_score']:.2f})"
                    # Add fall indicators
                    indicators_text = f"Indicators: {', '.join(person['fall_indicators'])}"
                    cv2.putText(annotated_img, label, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                    cv2.putText(annotated_img, indicators_text, (x1, y1-30), cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
                else:
                    label = f"PERSON {person['confidence']:.2f}"
                    cv2.putText(annotated_img, label, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            
            cv2.imwrite(save_path, annotated_img)
        
        return {
            "fall_detected": fall_detected,
            "num_detections": len([p for p in persons if p["fallen"]]),
            "total_persons": len(persons),
            "detections": persons,
            "model_confidence_threshold": 0.15,
            "detection_method": "Enhanced Multi-Criteria Fall Detection"
        }

# Compatibility functions
def detect_fall_image(image_path, save_path=None):
    detector = ImprovedFallDetector()
    return detector.detect_fall_in_image(image_path, save_path)

def detect_fall_video(video_path, output_path=None):
    detector = ImprovedFallDetector()
    
    cap = cv2.VideoCapture(video_path)
    fall_incidents = 0
    fall_detections = []
    frame_count = 0
    
    while cap.read()[0]:
        frame_count += 1
    
    cap.release()
    
    # Process video frames
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    frame_num = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        if frame_num % 15 == 0:  # Check every 15th frame for better accuracy
            # Save frame temporarily
            temp_frame = "temp_frame.jpg"
            cv2.imwrite(temp_frame, frame)
            
            # Detect falls in frame
            result = detector.detect_fall_in_image(temp_frame)
            
            if result.get("fall_detected", False):
                fall_incidents += 1
                fall_detections.append({
                    "frame": frame_num,
                    "timestamp": frame_num / fps,
                    "detections": result.get("num_detections", 0),
                    "details": result.get("detections", [])
                })
        
        frame_num += 1
    
    cap.release()
    
    return {
        "fall_incidents": fall_incidents,
        "total_frames": frame_count,
        "duration_seconds": frame_count / fps if fps > 0 else 0,
        "fall_detections": fall_detections
    }