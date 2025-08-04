from flask import Flask, request, jsonify, render_template, flash
from detect_person import detect_objects
from detect_video import detect_objects_in_video
from detect_roboflow import detect_fire_objects
from detect_fall_improved import detect_fall_image, detect_fall_video  # Use improved detection
# from detect_fall_quick import detect_fall_image, detect_fall_video  # Comment out the old one
import time
import os

app = Flask(__name__)
app.secret_key = 'your-secret-key-for-fall-detection-system-2025'  # Add this line
app.config['UPLOAD_FOLDER'] = 'uploads/'  # Folder to store uploaded files

# Make sure uploads directory exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        # Check if this is a fall detection request via URL parameters
        image_param = request.args.get('image')
        use_fall = request.args.get('use_fall')
        
        if image_param and use_fall == 'true':
            # This is a fall detection request, but we need the actual file
            # Redirect to the main page with a message
            flash('Please upload an image file for fall detection', 'warning')
    
    return render_template('index.html')

# Make sure the detect-image route properly handles fall detection
@app.route('/detect-image', methods=['POST'])
def detect_image():
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({'error': 'No image file selected'}), 400
        
        use_fall = request.form.get('use_fall', 'false').lower() == 'true'
        
        if use_fall:
            # Use quick fall detection
            temp_path = os.path.join(app.config['UPLOAD_FOLDER'], 'temp_' + file.filename)
            file.save(temp_path)
            
            try:
                # Use the quick fall detection functions that are already imported
                result = detect_fall_image(temp_path, save_path=None)
                
                # Clean up temp file
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                
                return jsonify({
                    "image_processed": True,
                    "fall_detection": True,
                    "fall_detected": result.get("fall_detected", False),
                    "num_detections": result.get("num_detections", 0),
                    "detections": result.get("detections", []),
                    "confidence_threshold": result.get("model_confidence_threshold", 0.25),
                    "detection_source": "Quick YOLOv5 Fall Detection"
                })
                
            except Exception as e:
                return jsonify({
                    'error': 'Fall detection failed',
                    'details': str(e)
                }), 500
        else:
            # Use regular object detection (existing code)
            # Check detection type
            use_fire_detection = request.form.get("use_fire", "false").lower() == "true"
            use_fall_detection = request.form.get("use_fall", "false").lower() == "true"
            
            if use_fall_detection:
                # Use fall detection
                result = detect_fall_image(image_path, save_path="temp_fall_result.jpg")
                
                if isinstance(result, dict) and "error" in result:
                    return jsonify(result), 500
                
                return jsonify({
                    "image_processed": True,
                    "fall_detection": True,
                    "fall_detected": result.get("fall_detected", False),
                    "num_detections": result.get("num_detections", 0),
                    "detections": result.get("detections", []),
                    "confidence_threshold": result.get("model_confidence_threshold", 0.25),
                    "detection_source": "Custom YOLOv5 Fall Detection Model"
                })
            elif use_fire_detection:
                # Use fire detection
                result = detect_fire_objects(image_path, ['general', 'fire'], is_video=False)
                
                if isinstance(result, dict) and "error" in result:
                    return jsonify(result), 500
                
                return jsonify({
                    "image_processed": True,
                    "fire_detection": True,
                    "detections": result,
                    "person_count": result.get("persons", 0),
                    "fire_smoke_detected": result.get("fire_smoke", {}),
                    "vehicles_detected": result.get("vehicles", {}),
                    "other_objects": result.get("other_objects", {})
                })
            else:
                # Use original detection
                filter_class = request.form.get("filter", "").strip().lower()
                detections = detect_objects(image_path, filter_class)
                
                return jsonify({
                    "objects_detected": detections,
                    "person_count": detections.get("person", 0)
                })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/detect-video', methods=['POST'])
def detect_video():
    if 'video' not in request.files:
        return jsonify({'error': 'No video provided'}), 400

    video = request.files['video']
    if video.filename == '':
        return jsonify({'error': 'No video file selected'}), 400
    
    video_path = "temp_video.mp4"
    
    try:
        video.save(video_path)
        
        # Check detection type
        use_fire_detection = request.form.get("use_fire", "false").lower() == "true"
        use_fall_detection = request.form.get("use_fall", "false").lower() == "true"
        
        if use_fall_detection:
            # Use fall detection
            print(f"Processing video with FALL DETECTION: {video.filename}")
            result = detect_fall_video(video_path, output_path="temp_fall_result.mp4")
            
            if isinstance(result, dict) and "error" in result:
                return jsonify(result), 500
            
            return jsonify({
                "video_processed": True,
                "filename": video.filename,
                "fall_detection": True,
                "fall_incidents": result.get("fall_incidents", 0),
                "total_frames": result.get("total_frames", 0),
                "duration_seconds": result.get("duration_seconds", 0),
                "fall_detections": result.get("fall_detections", []),
                "detection_source": "Custom YOLOv5 Fall Detection Model"
            })
        elif use_fire_detection:
            # Use fire detection
            print(f"Processing video with FIRE DETECTION: {video.filename}")
            result = detect_fire_objects(video_path, ['general', 'fire'], is_video=True)
            
            if isinstance(result, dict) and "error" in result:
                return jsonify(result), 500
            
            return jsonify({
                "video_processed": True,
                "filename": video.filename,
                "fire_detection": True,
                "detections": result,
                "person_count": result.get("persons", 0),
                "fire_smoke_detected": result.get("fire_smoke", {}),
                "vehicles_detected": result.get("vehicles", {}),
                "other_objects": result.get("other_objects", {})
            })
        else:
            # Use original detection
            print(f"Processing video with GENERAL DETECTION: {video.filename}")
            detections = detect_objects_in_video(video_path, is_video=True)
            
            if isinstance(detections, dict) and "error" in detections:
                return jsonify(detections), 500
            
            return jsonify({
                "video_processed": True,
                "person_count": detections.get("person", 0),
                "objects_detected": detections,
                "filename": video.filename
            })
        
    except Exception as e:
        print(f"Error in video upload/processing: {e}")
        return jsonify({'error': f'Video processing failed: {str(e)}'}), 500

@app.route('/fire-scan', methods=['POST'])
def fire_scan():
    """Dedicated fire detection endpoint"""
    if 'media' not in request.files:
        return jsonify({'error': 'No media file provided'}), 400

    media = request.files['media']
    if media.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    is_video = any(ext in media.filename.lower() for ext in ['.mp4', '.avi', '.mov', '.mkv'])
    file_extension = 'mp4' if is_video else 'jpg'
    file_path = f"temp_fire.{file_extension}"
    
    try:
        media.save(file_path)
        
        print(f"Fire detection scan on {media.filename}")
        result = detect_fire_objects(file_path, ['general', 'fire'], is_video=is_video)
        
        if isinstance(result, dict) and "error" in result:
            return jsonify(result), 500
        
        # Calculate fire threat level
        threat_level = "SAFE"
        threat_details = []
        
        if result.get("fire_smoke", {}):
            fire_count = sum(result["fire_smoke"].values())
            fire_types = list(result["fire_smoke"].keys())
            
            if fire_count > 0:
                threat_level = "FIRE DETECTED"
                threat_details.append(f"🔥 FIRE HAZARD: {fire_count} fire/smoke incident(s) detected")
                threat_details.append(f"Fire types: {', '.join(fire_types)}")
        
        person_count = result.get("persons", 0)
        if person_count > 0 and threat_level == "FIRE DETECTED":
            threat_details.append(f"⚠️ {person_count} people detected in fire zone - IMMEDIATE EVACUATION REQUIRED")
        
        if threat_level == "SAFE":
            threat_details.append("✅ No fire or smoke detected")
        
        return jsonify({
            "fire_scan": True,
            "filename": media.filename,
            "media_type": "video" if is_video else "image",
            "fire_threat_level": threat_level,
            "threat_details": threat_details,
            "detections": result,
            "person_count": person_count,
            "fire_smoke_detected": result.get("fire_smoke", {}),
            "detection_source": "Roboflow Fire Detection Model",
            "timestamp": time.time()
        })
        
    except Exception as e:
        print(f"Error in fire scan: {e}")
        return jsonify({'error': f'Fire scan failed: {str(e)}'}), 500

@app.route('/fall-scan', methods=['POST'])
def fall_scan():
    """Dedicated fall detection endpoint"""
    if 'media' not in request.files:
        return jsonify({'error': 'No media file provided'}), 400

    media = request.files['media']
    if media.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    is_video = any(ext in media.filename.lower() for ext in ['.mp4', '.avi', '.mov', '.mkv'])
    file_extension = 'mp4' if is_video else 'jpg'
    file_path = f"temp_fall.{file_extension}"
    
    try:
        media.save(file_path)
        
        print(f"Fall detection scan on {media.filename}")
        
        if is_video:
            result = detect_fall_video(file_path, output_path="temp_fall_result.mp4")
        else:
            result = detect_fall_image(file_path, save_path="temp_fall_result.jpg")
        
        if isinstance(result, dict) and "error" in result:
            return jsonify(result), 500
        
        # Calculate fall threat level
        threat_level = "SAFE"
        threat_details = []
        
        if is_video:
            fall_incidents = result.get("fall_incidents", 0)
            if fall_incidents > 0:
                threat_level = "FALL DETECTED"
                threat_details.append(f"🚨 FALL EMERGENCY: {fall_incidents} fall incident(s) detected in video")
                
                # Add details about when falls occurred
                fall_detections = result.get("fall_detections", [])
                for detection in fall_detections[:3]:  # Show first 3 incidents
                    timestamp = detection.get("timestamp", 0)
                    threat_details.append(f"⏰ Fall detected at {timestamp:.1f}s (frame {detection.get('frame', 0)})")
                
                if len(fall_detections) > 3:
                    threat_details.append(f"... and {len(fall_detections) - 3} more incidents")
                
                threat_details.append("🏥 IMMEDIATE MEDICAL ATTENTION MAY BE REQUIRED")
            else:
                threat_details.append("✅ No falls detected in video")
        else:
            fall_detected = result.get("fall_detected", False)
            if fall_detected:
                threat_level = "FALL DETECTED"
                num_detections = result.get("num_detections", 0)
                threat_details.append(f"🚨 FALL EMERGENCY: {num_detections} fall(s) detected in image")
                threat_details.append("🏥 IMMEDIATE MEDICAL ATTENTION MAY BE REQUIRED")
            else:
                threat_details.append("✅ No falls detected in image")
        
        return jsonify({
            "fall_scan": True,
            "filename": media.filename,
            "media_type": "video" if is_video else "image",
            "fall_threat_level": threat_level,
            "threat_details": threat_details,
            "detections": result,
            "detection_source": "Custom YOLOv5 Fall Detection Model",
            "timestamp": time.time()
        })
        
    except Exception as e:
        print(f"Error in fall scan: {e}")
        return jsonify({'error': f'Fall scan failed: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True)
