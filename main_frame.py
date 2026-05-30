"""
main_frame.py — Khung giao diện chính & Điểm khởi chạy hệ thống
===============================================================
Chạy trực tiếp file này bằng lệnh: python main_frame.py
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Type
from tkinter import ttk, filedialog
import cv2
from PIL import Image, ImageTk
from detector import ProductDetector
# ─── Theme toàn cục — import ở panel con để dùng chung ───────────
THEME = {
    "bg":          "#111318",   # nền chính
    "bg2":         "#1a1d24",   # nền panel / card
    "bg3":         "#22262f",   # nền input, row hover
    "border":      "#2c303a",   # đường kẻ
    "fg":          "#e8eaf0",   # chữ chính
    "fg_muted":    "#7a8099",   # chữ phụ
    "fg_hint":     "#3d424f",   # chữ gợi ý / disabled
    "accent":      "#3b82f6",   # xanh dương (nút bấm chính)
    "green":       "#4ade80",   # xanh lá (thành công, giá tiền)
    "yellow":      "#facc15",   # vàng (cảnh báo)
    "red":         "#f87171",   # đỏ (lỗi / xóa)
}

class AppShell:
    """ Khung giao diện dạng Shell với thanh điều hướng Tab phía trên """
    def __init__(self, root: tk.Tk, title: str = "Hệ thống", size: tuple = (1060, 620)):
        self.root = root
        self.root.title(title)
        self.base_title = title
        self.root.geometry(f"{size[0]}x{size[1]}")
        self.root.configure(bg=THEME["bg"])
        
        self.tab_classes = []
        self.tab_buttons = []
        self.tab_panels = {}
        self.current_idx = -1

        # 1. Thanh tiêu đề phía trên cùng (Topbar)
        self.top_bar = tk.Frame(self.root, bg=THEME["bg"], height=60, 
                                highlightbackground=THEME["border"], highlightthickness=1)
        self.top_bar.pack(side="top", fill="x")
        self.top_bar.pack_propagate(False)

        # Tiêu đề bên trái
        self.lbl_title = tk.Label(self.top_bar, text=title, bg=THEME["bg"], 
                                  fg=THEME["fg"], font=("Segoe UI", 14, "bold"))
        self.lbl_title.pack(side="left", padx=20)

        # Khung chứa nút chuyển đổi tab bên phải Topbar
        self.nav_frame = tk.Frame(self.top_bar, bg=THEME["bg"])
        self.nav_frame.pack(side="right", padx=10, fill="y")

        # 2. Vùng hiển thị nội dung chính (Content Area)
        self.content_area = tk.Frame(self.root, bg=THEME["bg"])
        self.content_area.pack(side="bottom", fill="both", expand=True)

    def dang_ky_tab(self, name: str, panel_class: Type[tk.Frame]) -> int:
        idx = len(self.tab_classes)
        self.tab_classes.append((name, panel_class))

        btn = tk.Button(
            self.nav_frame, text=name, bg=THEME["bg"], fg=THEME["fg_muted"],
            font=("Segoe UI", 10, "bold"), bd=0, activebackground=THEME["bg"],
            activeforeground=THEME["fg"], cursor="hand2", padx=15,
            command=lambda: self.hien_thi_tab(idx)
        )
        btn.pack(side="left", fill="y")
        
        # Tạo hiệu ứng đường gạch dưới khi hover chuột vào Tab
        btn.bind("<Enter>", lambda e, b=btn: b.config(fg=THEME["fg"]) if self.tab_buttons[idx] != btn else None)
        btn.bind("<Leave>", lambda e, b=btn: b.config(fg=THEME["fg_muted"]) if self.current_idx != idx else None)

        self.tab_buttons.append(btn)
        return idx

    def hien_thi_tab(self, idx: int):
        if idx == self.current_idx:
            return

        # Ẩn panel hiện tại nếu có
        if self.current_idx != -1:
            old_panel = self.tab_panels.get(self.current_idx)
            if old_panel:
                old_panel.place_forget()
                if hasattr(old_panel, "on_hide"):
                    old_panel.on_hide()
            self.tab_buttons[self.current_idx].config(fg=THEME["fg_muted"])

        # Hiển thị panel mới
        self.current_idx = idx
        
        name, _ = self.tab_classes[idx]
        self.root.title(f"{self.base_title} | {name}")  
        
        self.tab_buttons[idx].config(fg=THEME["green"]) # Làm nổi bật Tab đang chọn

        panel = self.tab_panels.get(idx)
        if not panel:
            name, p_class = self.tab_classes[idx]
            panel = p_class(self.content_area)
            self.tab_panels[idx] = panel

        panel.place(x=0, y=0, relwidth=1, relheight=1)
        
        if hasattr(panel, "on_show"):
            panel.on_show()

    def lay_panel(self, idx: int) -> tk.Frame:
        return self.tab_panels.get(idx)
class PanelNhanDienAnh(tk.Frame):
    """ TAB MỚI: Chức năng nhận diện sản phẩm qua file hình ảnh tải lên máy """
    def __init__(self, parent):
        super().__init__(parent, bg=THEME["bg"])
        self.detector = ProductDetector()
        # Chia layout làm 2 phần trái (Ảnh) và phải (Thông tin kết quả) giống Tab Camera
        self.left_frame = tk.Frame(self, bg=THEME["bg"])
        self.left_frame.pack(side="left", fill="both", expand=True, padx=20, pady=20)
        
        self.right_frame = tk.Frame(self, bg=THEME["bg2"], width=320, 
                                    highlightbackground=THEME["border"], highlightthickness=1)
        self.right_frame.pack(side="right", fill="y", padx=(0, 20), pady=20)
        self.right_frame.pack_propagate(False)

        # --- Bố cục Khu vực bên Trái (Xử lý Chọn Ảnh & Hiển thị) ---
        # Thanh công cụ chứa nút bấm chọn ảnh
        self.toolbar = tk.Frame(self.left_frame, bg=THEME["bg"])
        self.toolbar.pack(side="top", fill="x", pady=(0, 10))
        
        self.btn_upload = tk.Button(
            self.toolbar, text="📁 Chọn ảnh từ thiết bị", bg=THEME["accent"], fg=THEME["fg"],
            font=("Segoe UI", 10, "bold"), bd=0, padx=15, pady=8, cursor="hand2",
            activebackground="#2563eb", activeforeground=THEME["fg"], command=self.chon_va_xu_ly_anh
        )
        self.btn_upload.pack(side="left")
        
        self.lbl_path = tk.Label(self.toolbar, text="Chưa chọn file nào", bg=THEME["bg"], 
                                 fg=THEME["fg_muted"], font=("Segoe UI", 9, "italic"))
        self.lbl_path.pack(side="left", padx=15)

        # Khung đen hiển thị hình ảnh (Giống khung camera)
        self.canvas_img = tk.Frame(self.left_frame, bg="#000000", 
                                   highlightbackground=THEME["border"], highlightthickness=1)
        self.canvas_img.pack(side="bottom", fill="both", expand=True)
        
        self.lbl_preview = tk.Label(self.canvas_img, text="Hình ảnh xem trước và kết quả vẽ Box sẽ hiển thị ở đây", 
                                    bg="#000000", fg=THEME["fg_muted"], font=("Segoe UI", 10))
        self.lbl_preview.place(relx=0.5, rely=0.5, anchor="center")

        # --- Bố cục Khu vực bên Phải (Hiển thị dữ liệu Sản phẩm) ---
        tk.Label(self.right_frame, text="TÊN SẢN PHẨM", bg=THEME["bg2"], fg=THEME["fg_muted"], 
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=20, pady=(20, 5))
        self.lbl_ten_sp = tk.Label(self.right_frame, text="—", bg=THEME["bg2"], fg=THEME["fg"], 
                                   font=("Segoe UI", 14, "bold"))
        self.lbl_ten_sp.pack(anchor="w", padx=20)

        tk.Label(self.right_frame, text="GIÁ THAM KHẢO", bg=THEME["bg2"], fg=THEME["fg_muted"], 
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=20, pady=(20, 5))
        self.lbl_gia_sp = tk.Label(self.right_frame, text="—", bg=THEME["bg2"], fg=THEME["green"], 
                                   font=("Segoe UI", 14, "bold"))
        self.lbl_gia_sp.pack(anchor="w", padx=20)
        
        tk.Label(self.right_frame, text="ĐỘ CHÍNH XÁC AI", bg=THEME["bg2"], fg=THEME["fg_muted"], 
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=20, pady=(20, 5))
        self.lbl_conf = tk.Label(self.right_frame, text="0.0%", bg=THEME["bg2"], fg=THEME["yellow"], 
                                 font=("Segoe UI", 12, "bold"))
        self.lbl_conf.pack(anchor="w", padx=20)

    def chon_va_xu_ly_anh(self):
        from db import tra_gia, luu_lich_su
        file_path = filedialog.askopenfilename(
            filetypes=[("Image Files", "*.jpg;*.jpeg;*.png;*.bmp;*.webp")]
        )
        if not file_path:
            return
            
        self.lbl_path.config(text=file_path.split("/")[-1])
        try:
            # 1. Gọi detector xử lý
            annotated_frame, info = self.detector.predict_image(file_path)
            
            # 2. Chuyển đổi màu sắc
            img_rgb = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
            img_pil = Image.fromarray(img_rgb)
            
            # --- TỐI ƯU HIỂN THỊ TOÀN Ô ---
            self.update_idletasks() # Cập nhật lại kích thước thực tế của các widget
            
            # Lấy kích thước khung đen
            canvas_w = self.canvas_img.winfo_width()
            canvas_h = self.canvas_img.winfo_height()
            
            # Nếu winfo chưa kịp lấy (trả về 1), đặt mặc định theo tỷ lệ khung hình
            if canvas_w < 10: canvas_w, canvas_h = 700, 500 

            # Tính toán tỷ lệ để phóng to ảnh nhưng không làm biến dạng (Aspect Ratio)
            img_w, img_h = img_pil.size
            ratio = min(canvas_w/img_w, canvas_h/img_h)
            new_size = (int(img_w * ratio), int(img_h * ratio))
            
            # Sử dụng Resampling chất lượng cao (LANCZOS thay vì thumbnail mặc định)
            img_pil = img_pil.resize(new_size, Image.Resampling.LANCZOS)
            img_tk = ImageTk.PhotoImage(image=img_pil)
            
            # Đẩy ảnh lên màn hình
            self.lbl_preview.config(image=img_tk, text="")
            self.lbl_preview.image = img_tk 
            # ------------------------------

            # 3. Xử lý logic Database (giữ nguyên phần cũ của bạn)
            if info["found"]:
                # ... code tra cứu DB và hiển thị của bạn ...
                name_en = info["name_en"]
                do_chinh_xac = info["conf"]
                data_sp = tra_gia(name_en)
                if data_sp:
                    ten_vn, gia_min, gia_max, don_vi = data_sp
                    self.lbl_ten_sp.config(text=f"{ten_vn} ({name_en.upper()})")
                    self.lbl_gia_sp.config(text=f"{gia_min:,} - {gia_max:,}đ / {don_vi}")
                    luu_lich_su(ten_vn, do_chinh_xac)
                else:
                    self.lbl_ten_sp.config(text=f"{name_en.upper()} (Chưa có trong DB)")
                    self.lbl_gia_sp.config(text="—")
                    luu_lich_su(name_en, do_chinh_xac)
                self.lbl_conf.config(text=f"{do_chinh_xac:.1f}%")
            else:
                self.lbl_ten_sp.config(text="Không nhận diện được")
                self.lbl_gia_sp.config(text="—")
                self.lbl_conf.config(text="0.0%")
                
        except Exception as e:
            self.lbl_preview.config(text=f"Lỗi hiển thị hình ảnh: {e}")

class PanelLichSu(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=THEME["bg2"])
        tk.Label(self, text="Lịch sử nhận diện dữ liệu", bg=THEME["bg2"], fg=THEME["fg"], font=("Segoe UI", 14, "bold")).pack(pady=30)

class PanelQuanLy(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=THEME["bg2"])
        tk.Label(self, text="Quản lý danh mục sản phẩm", bg=THEME["bg2"], fg=THEME["fg"], font=("Segoe UI", 14, "bold")).pack(pady=30)

# ══════════════════════════════════════════════════════════════════
#  ĐIỀU HÀNH VÀ KHỞI CHẠY HỆ THỐNG CHÍNH ĐÚNG YÊU CẦU
# ══════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    from db import tao_database
    from app import PanelQuet  # Nhúng trực tiếp Panel xử lý camera thật từ app.py

    print("🔧 [Hệ thống] Đang kiểm tra cấu trúc cơ sở dữ liệu...")
    tao_database()

    # Định nghĩa các Panel phụ (Bạn có thể tách file tương tự nếu cần)
    class PanelLichSu(tk.Frame):
        def __init__(self, parent):
            super().__init__(parent, bg=THEME["bg2"])
            tk.Label(self, text="Lịch sử nhận diện dữ liệu", bg=THEME["bg2"], fg=THEME["fg"], font=("Segoe UI", 14, "bold")).pack(pady=30)

    class PanelQuanLy(tk.Frame):
        def __init__(self, parent):
            super().__init__(parent, bg=THEME["bg2"])
            tk.Label(self, text="Quản lý danh mục sản phẩm", bg=THEME["bg2"], fg=THEME["fg"], font=("Segoe UI", 14, "bold")).pack(pady=30)

    root = tk.Tk()
    shell = AppShell(root, title="Hệ thống nhận diện sản phẩm AI", size=(1060, 620))

    # Đăng ký các Tab nghiệp vụ vào Khung chính Shell
    idx_quet   = shell.dang_ky_tab("Quét sản phẩm",      PanelQuet)  # Load Panel thực tế từ app.py
    idx_image   = shell.dang_ky_tab("Nhận diện qua ảnh",   PanelNhanDienAnh)
    idx_lichsu = shell.dang_ky_tab("Lịch sử nhận diện",  PanelLichSu)
    idx_quanly = shell.dang_ky_tab("Quản lý sản phẩm",   PanelQuanLy)

    # Đóng gói hàm thoát ứng dụng dọn dẹp camera
    def thuc_hien_dong_app():
        p_quet = shell.lay_panel(idx_quet)
        if p_quet and hasattr(p_quet, "on_hide"):
            p_quet.on_hide()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", thuc_hien_dong_app)
    
    # Kích hoạt mở Tab quét sản phẩm và bật camera ngay khi ứng dụng lên màn hình
    shell.hien_thi_tab(0)
    root.mainloop()