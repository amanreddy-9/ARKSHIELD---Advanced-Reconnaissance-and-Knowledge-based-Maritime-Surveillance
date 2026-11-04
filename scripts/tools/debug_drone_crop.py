import cv2
from pathlib import Path

VIDEO = Path(
    r"data\test_mp4\Oil tanker with a drone! #shorts #merchantnavy #ships #viral #trending #dronevideo #drone #oiltanker.mp4"
)

OUTPUT = Path(r"data\test_mp4\debug_oil_tanker_crop.jpg")

cap = cv2.VideoCapture(str(VIDEO))

if not cap.isOpened():
    raise RuntimeError("Could not open video")

ret, frame = cap.read()
cap.release()

if not ret:
    raise RuntimeError("Could not read first frame")

# YOLO detection from your previous result
x1, y1, x2, y2 = 484.45, 1051.78, 582.39, 1079.92

# Expand the crop by 50%
w = x2 - x1
h = y2 - y1

margin_x = max(w * 0.50, 30)
margin_y = max(h * 0.50, 30)

x1 -= margin_x
y1 -= margin_y
x2 += margin_x
y2 += margin_y

# Clamp to image
height, width = frame.shape[:2]

x1 = max(0, int(x1))
y1 = max(0, int(y1))
x2 = min(width, int(x2))
y2 = min(height, int(y2))

crop = frame[y1:y2, x1:x2]

cv2.imwrite(str(OUTPUT), crop)

print("Original frame:", width, "x", height)
print("Crop:", x1, y1, x2, y2)
print("Crop size:", crop.shape[1], "x", crop.shape[0])
print("Saved:", OUTPUT)