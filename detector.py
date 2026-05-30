# detector.py
import cv2
from ultralytics import YOLO

class ProductDetector:
    def __init__(self, model_path="yolov8n.pt"):
        # Load model 1 lần duy nhất khi khởi tạo
        self.model = YOLO(model_path)
        
    def predict_image(self, file_path: str):
        """
        Nhận diện ảnh từ đường dẫn file.
        Trả về: Ảnh đã vẽ box (numpy array) và thông tin box đầu tiên tìm thấy
        """
        results = self.model(file_path)[0]
        
        # Lấy ảnh đã vẽ sẵn khung Bounding Box từ YOLO
        annotated_frame = results.plot()
        
        # Mặc định nếu không tìm thấy gì
        detect_info = {
            "found": False,
            "name_en": "",
            "conf": 0.0
        }
        
        # Nếu phát hiện ra ít nhất 1 vật thể
        if len(results.boxes) > 0:
            box = results.boxes[0]
            class_id = int(box.cls[0])
            name_en = self.model.names[class_id]  # Tên tiếng Anh gốc (ví dụ: 'apple')
            conf = float(box.conf[0]) * 100       # % chính xác
            
            detect_info = {
                "found": True,
                "name_en": name_en,
                "conf": conf
            }
            
        return annotated_frame, detect_info