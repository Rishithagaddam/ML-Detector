import torch
from PIL import Image
import cv2

model = torch.hub.load('ultralytics/yolov5', 'yolov5s', force_reload=False)

def detect_objects(image_path, filter_class=None):
    img = Image.open(image_path)
    results = model(img)
    labels = results.xyxyn[0][:, -1].int().tolist()
    names = results.names

    counts = {}
    for label in labels:
        name = names[label]
        if not filter_class or name == filter_class:
            counts[name] = counts.get(name, 0) + 1
    return counts
