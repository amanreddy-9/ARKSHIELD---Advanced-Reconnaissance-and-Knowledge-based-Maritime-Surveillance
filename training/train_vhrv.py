import argparse
from ultralytics import YOLO
p=argparse.ArgumentParser()
p.add_argument("--data",default="configs/vhrv.yaml")
p.add_argument("--epochs",type=int,default=50)
p.add_argument("--model",default="yolov8n-obb.pt")
p.add_argument("--imgsz",type=int,default=1024)
a=p.parse_args()
YOLO(a.model).train(data=a.data,epochs=a.epochs,imgsz=a.imgsz,task="obb",project="outputs/vhrv",name="train")
