from flask import Flask, request, jsonify, render_template
from detect_person import detect_objects
from detect_video import detect_objects_in_video
from detect_roboflow import detect_fire_objects
import time

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/detect-image', methods=['POST'])
def detect_image():
    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400

    image = request.files['image']
    image_path = "temp.jpg"
    image.save(image_path)

    # Check if user wants fire detection
    use_fire_detection = request.form.get("use_fire", "false").lower() == "true"
    
    if use_fire_detection:
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
        
        # Check if user wants fire detection
        use_fire_detection = request.form.get("use_fire", "false").lower() == "true"
        
        if use_fire_detection:
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

if __name__ == '__main__':
    app.run(debug=True)
