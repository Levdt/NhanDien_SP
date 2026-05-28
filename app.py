"""
app.py — Điểm khởi chạy chính & Tích hợp Panel Quét vào AppShell cũ
====================================================================
Giữ nguyên vẹn 100% giao diện main_frame.py của bạn.
"""

import cv2
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
from ultralytics import YOLO
import mediapipe as mp
from db import get_conn, tao_database, tra_gia, luu_lich_su
import time

# Nhúng trực tiếp AppShell và hệ thống màu THEME từ file main_frame.py gốc
from main_frame import AppShell, THEME          

# Thử import các panel phụ của bạn, nếu chưa có thì bỏ qua không ảnh hưởng
try:
    from lich_su_window import lay_lich_su, thong_ke_nhanh, xuat_excel
except ImportError:
    pass

# ─── Khởi tạo mô hình AI & Bàn tay ───────────────────────────────
model = YOLO("yolov8n.pt")
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    max_num_hands=2,
    min_detection_confidence=0.6,
    min_tracking_confidence=0.5
)

# ─── Hằng số Cấu hình ─────────────────────────────────────────────
CONF_NGUONG  = 0.50
LUU_COOLDOWN = 3.0
BO_QUA = {"person", "chair", "couch", "bed", "dining table",
          "laptop", "tv", "cell phone", "vase", "scissors"}

# Định kích thước luồng hiển thị Camera (Khớp tỉ lệ ô trống bên trái)
CAM_W, CAM_H = 640, 460   

def hop_giao_nhau(box_a, box_b) -> bool:
    """Kiểm tra xem vùng bàn tay và vùng vật thể có chạm nhau không."""
    ax1, ay1, ax2, ay2 = box_a
    bx1, by1, bx2, by2 = box_b
    return ax1 < bx2 and ax2 > bx1 and ay1 < by2 and ay2 > by1

def dinh_dang_gia(gia_min: int, gia_max: int, don_vi: str) -> str:
    return f"{gia_min:,}đ – {gia_max:,}đ / {don_vi}"


# ══════════════════════════════════════════════════════════════════
#  PANEL QUÉT SẢN PHẨM (Sửa layout tương thích với AppShell gốc)
# ══════════════════════════════════════════════════════════════════
class PanelQuet(tk.Frame):
    def __init__(self, parent):
        # Kế thừa màu nền thẻ card (bg2) đồng bộ với thiết kế cũ của bạn
        super().__init__(parent, bg=THEME["bg2"])
        
        # Khung chứa chính bên trong lòng Tab (Sử dụng pack giãn cách an toàn)
        main_container = tk.Frame(self, bg=THEME["bg2"])
        main_container.pack(fill="both", expand=True, padx=20, pady=20)

        # 1. Khung hiển thị luồng Camera (Bên trái)
        self.lbl_cam = tk.Label(main_container, bg="#05070a", width=CAM_W, height=CAM_H)
        self.lbl_cam.pack(side="left", fill="both", expand=True)

        # 2. Khung thông tin chi tiết (Bên phải)
        info_panel = tk.Frame(main_container, bg=THEME["bg3"], width=300)
        info_panel.pack(side="right", fill="y", padx=(20, 0))
        info_panel.pack_propagate(False)

        # Cấu trúc các nhãn hiển thị thông tin sản phẩm
        tk.Label(info_panel, text="TÊN SẢN PHẨM", bg=THEME["bg3"], fg=THEME["fg_muted"], font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=15, pady=(20, 2))
        self.lbl_ten = tk.Label(info_panel, text="—", bg=THEME["bg3"], fg=THEME["fg"], font=("Segoe UI", 16, "bold"), wraplength=270, justify="left")
        self.lbl_ten.pack(anchor="w", padx=15, pady=(0, 5))

        self.lbl_conf = tk.Label(info_panel, text="", bg=THEME["bg3"], fg=THEME["fg_muted"], font=("Segoe UI", 10))
        self.lbl_conf.pack(anchor="w", padx=15, pady=(0, 15))

        tk.Label(info_panel, text="GIÁ THAM KHẢO", bg=THEME["bg3"], fg=THEME["fg_muted"], font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=15, pady=(5, 2))
        self.lbl_gia = tk.Label(info_panel, text="—", bg=THEME["bg3"], fg=THEME["green"], font=("Segoe UI", 14, "bold"))
        self.lbl_gia.pack(anchor="w", padx=15, pady=(0, 20))

        tk.Label(info_panel, text="TRẠNG THÁI TAY", bg=THEME["bg3"], fg=THEME["fg_muted"], font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=15, pady=(5, 2))
        self.lbl_tay = tk.Label(info_panel, text="Chưa phát hiện tay", bg=THEME["bg3"], fg=THEME["fg_muted"], font=("Segoe UI", 11))
        self.lbl_tay.pack(anchor="w", padx=15, pady=(0, 15))

        # Quản lý luồng trạng thái hoạt động
        self.cap = None
        self.running = False
        self.last_save = 0.0

    def on_show(self):
        """Hook tự động chạy khi kích hoạt tab 'Quét sản phẩm'"""
        if not self.running:
            self.cap = cv2.VideoCapture(0)
            self.running = True
            self._update()

    def on_hide(self):
        """Tự động tắt luồng camera khi chuyển sang tab khác để tránh đơ app"""
        self.running = False
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        self.lbl_cam.config(image="")

    def _update(self):
        if not self.running or self.cap is None:
            return

        ret, frame = self.cap.read()
        if not ret:
            self.lbl_cam.after(30, self._update)
            return

        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h_frame, w_frame = frame.shape[:2]

        # Nhận diện tay (MediaPipe)
        hand_result = hands.process(rgb)
        hand_boxes = []
        if hand_result.multi_hand_landmarks:
            for lm in hand_result.multi_hand_landmarks:
                xs = [p.x * w_frame for p in lm.landmark]
                ys = [p.y * h_frame for p in lm.landmark]
                hx1, hy1 = int(min(xs)) - 10, int(min(ys)) - 10
                hx2, hy2 = int(max(xs)) + 10, int(max(ys)) + 10
                hand_boxes.append((hx1, hy1, hx2, hy2))
                cv2.rectangle(rgb, (hx1, hy1), (hx2, hy2), (250, 204, 20), 2)

        # Nhận diện vật thể (YOLOv8)
        results = model(frame, verbose=False)[0]
        co_cam = False

        for box in results.boxes:
            conf = float(box.conf[0])
            if conf < CONF_NGUONG: 
                continue

            ten_en = model.names[int(box.cls[0])]
            if ten_en in BO_QUA: 
                continue

            x1, y1, x2, y2 = map(int, box.xyxy[0])
            sp_box = (x1, y1, x2, y2)

            # Phân tích xem tay có chạm/cầm hộp sản phẩm không
            dang_cam = any(hop_giao_nhau(hb, sp_box) for hb in hand_boxes)
            mau_box = (74, 222, 128) if dang_cam else (120, 120, 120)

            cv2.rectangle(rgb, (x1, y1), (x2, y2), mau_box, 2)
            cv2.putText(rgb, f"{ten_en} {conf*100:.0f}%", (x1, y1 - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.55, mau_box, 2)

            if dang_cam:
                co_cam = True
                info = tra_gia(ten_en)
                ten_hien = info[0] if info else ten_en.capitalize()

                self.lbl_ten.config(text=ten_hien)
                self.lbl_conf.config(text=f"Độ tin cậy: {conf*100:.0f}%")
                
                if info:
                    self.lbl_gia.config(text=dinh_dang_gia(info[1], info[2], info[3]))
                else:
                    self.lbl_gia.config(text="Chưa có dữ liệu giá")

                self.lbl_tay.config(text="✓ Đang cầm sản phẩm", fg=THEME["green"])

                # Lưu lịch sử tự động (Cooldown chặn trùng lặp 3 giây)
                now = time.time()
                if now - self.last_save >= LUU_COOLDOWN:
                    luu_lich_su(ten_hien, conf)
                    self.last_save = now

        if not co_cam:
            self.lbl_ten.config(text="—")
            self.lbl_conf.config(text="")
            self.lbl_gia.config(text="—")
            if hand_boxes:
                self.lbl_tay.config(text="Tay trống — hãy cầm sản phẩm", fg=THEME["yellow"])
            else:
                self.lbl_tay.config(text="Chưa phát hiện tay", fg=THEME["fg_muted"])

        # Đẩy luồng ảnh lên giao diện
        img_resized = cv2.resize(rgb, (CAM_W, CAM_H))
        self.imgtk = ImageTk.PhotoImage(Image.fromarray(img_resized))
        self.lbl_cam.config(image=self.imgtk)

        if self.running:
            self.lbl_cam.after(30, self._update)


# ─── Khung Panel mẫu để hệ thống không bị lỗi thiếu Class ───
class PanelLichSu(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=THEME["bg2"])
        tk.Label(self, text="Lịch sử nhận diện", bg=THEME["bg2"], fg=THEME["fg"], font=("Segoe UI", 14, "bold")).pack(pady=30)

class PanelQuanLy(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=THEME["bg2"])
        tk.Label(self, text="Quản lý sản phẩm", bg=THEME["bg2"], fg=THEME["fg"], font=("Segoe UI", 14, "bold")).pack(pady=30)


# ══════════════════════════════════════════════════════════════════
#  ĐIỀU HÀNH ỨNG DỤNG CHÍNH (Sử dụng nguyên gốc Shell từ main_frame)
# ══════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("🔧 Đang kiểm tra cơ sở dữ liệu...")
    tao_database()

    root = tk.Tk()
    # Gọi trực tiếp AppShell từ main_frame.py
    shell = AppShell(root, title="Hệ thống nhận diện sản phẩm", size=(1060, 620))

    # Đăng ký các Panel vào hệ thống tab nguyên bản bằng phương thức có sẵn
    panel_quet   = shell.dang_ky_tab("Quét sản phẩm",      PanelQuet)
    panel_lichsu = shell.dang_ky_tab("Lịch sử nhận diện",  PanelLichSu)
    panel_quanly = shell.dang_ky_tab("Quản lý sản phẩm",   PanelQuanLy)

    # Gắn sự kiện hook để giải phóng camera và ngắt tiến trình an toàn khi tắt app
    def xử_lý_thoát():
        shell.lay_panel(panel_quet).on_hide()
        root.destroy()

    # Đồng bộ bộ chuyển đổi Tab để tự động tắt camera khi bấm xem tab lịch sử/quản lý
    def hien_thi_tab_co_kiem_soat(idx):
        if idx != panel_quet:
            shell.lay_panel(panel_quet).on_hide()
        shell_hien_thi_goc(idx)

    # Ghi đè phương thức hiển thị tab để kiểm soát vòng lặp camera thông minh
    shell_hien_thi_goc = shell.hien_thi_tab
    shell.hien_thi_tab = hien_thi_tab_co_kiem_soat

    root.protocol("WM_DELETE_WINDOW", xử_lý_thoát)
    shell.hien_thi_tab(0)  # Mặc định mở tab quét đầu tiên khi bật ứng dụng
    root.mainloop()