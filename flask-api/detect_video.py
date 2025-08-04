import torch
import cv2
import time

model = torch.hub.load('ultralytics/yolov5', 'yolov5s', force_reload=False)

def detect_objects_in_video(video_path, is_video=True):
    try:
        cap = cv2.VideoCapture(video_path)
        
        # Check if video opened successfully
        if not cap.isOpened():
            return {"error": "Could not open video file"}
        
        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        if fps <= 0 or total_frames <= 0:
            cap.release()
            return {"error": "Invalid video file"}
        
        # Process every Nth frame for efficiency (e.g., every 30th frame = 1 per second for 30fps video)
        frame_skip = max(1, int(fps))  # Skip frames to process ~1 frame per second
        max_frames_to_process = 10  # Limit total frames processed
        
        frame_counts = []
        frame_number = 0
        processed_frames = 0
        
        print(f"Processing video: {total_frames} total frames, FPS: {fps}, processing every {frame_skip} frames")
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Skip frames for efficiency
            if frame_number % frame_skip == 0 and processed_frames < max_frames_to_process:
                try:
                    # Resize frame for faster processing
                    height, width = frame.shape[:2]
                    if width > 640:
                        scale = 640 / width
                        new_width = 640
                        new_height = int(height * scale)
                        frame = cv2.resize(frame, (new_width, new_height))
                    
                    results = model(frame)
                    labels = results.xyxyn[0][:, -1].int().tolist()
                    names = results.names
                    
                    # Count objects in this frame
                    frame_counts_dict = {}
                    for label in labels:
                        name = names[label]
                        frame_counts_dict[name] = frame_counts_dict.get(name, 0) + 1
                    
                    frame_counts.append(frame_counts_dict)
                    processed_frames += 1
                    print(f"Processed frame {frame_number}, objects found: {frame_counts_dict}")
                    
                except Exception as e:
                    print(f"Error processing frame {frame_number}: {e}")
                    continue
            
            frame_number += 1
        
        cap.release()
        
        if not frame_counts:
            return {"error": "No frames could be processed"}
        
        # Calculate average/maximum counts across all processed frames
        all_objects = set()
        for frame_count in frame_counts:
            all_objects.update(frame_count.keys())
        
        # Use maximum count found in any single frame (more realistic than sum)
        final_counts = {}
        for obj in all_objects:
            max_count = max(frame_count.get(obj, 0) for frame_count in frame_counts)
            final_counts[obj] = max_count
        
        print(f"Final detection results: {final_counts}")
        return final_counts
        
    except Exception as e:
        print(f"Error in video detection: {e}")
        return {"error": f"Video processing failed: {str(e)}"}
