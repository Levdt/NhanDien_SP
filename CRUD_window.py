"""
CRUD_window.py — Panel Quản Lý Sản Phẩm
=========================================
Dùng làm Tab "Quản lý sản phẩm" trong AppShell của main_frame.py.
Tương thích hoàn toàn với THEME và cấu trúc tab hiện có.

Cách nhúng vào main_frame.py:
    from CRUD_window import PanelQuanLy
    idx_quanly = shell.dang_ky_tab("Quản lý sản phẩm", PanelQuanLy)
"""

import tkinter as tk
from tkinter import ttk, messagebox

# Dùng chung bảng màu với toàn bộ dự án
from main_frame import THEME
from db import get_conn


# ══════════════════════════════════════════════════════════════════
#  DB HELPERS — Tất cả câu lệnh SQL của panel này
# ══════════════════════════════════════════════════════════════════

def _lay_tat_ca() -> list:
    """SELECT toàn bộ sản phẩm, sắp xếp theo id."""
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute(
            "SELECT id, ten_en, ten_vn, gia_min, gia_max, don_vi "
            "FROM san_pham ORDER BY id"
        )
        rows = cur.fetchall()
        cur.close(); conn.close()
        return rows
    except Exception as e:
        messagebox.showerror("Lỗi DB", f"Không thể tải dữ liệu:\n{e}")
        return []


def _them(ten_en, ten_vn, gia_min, gia_max, don_vi):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO san_pham (ten_en, ten_vn, gia_min, gia_max, don_vi) "
        "VALUES (%s, %s, %s, %s, %s)",
        (ten_en.lower().strip(), ten_vn.strip(),
         int(gia_min), int(gia_max), don_vi.strip())
    )
    conn.commit(); cur.close(); conn.close()


def _sua(sp_id, ten_en, ten_vn, gia_min, gia_max, don_vi):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "UPDATE san_pham "
        "SET ten_en=%s, ten_vn=%s, gia_min=%s, gia_max=%s, don_vi=%s "
        "WHERE id=%s",
        (ten_en.lower().strip(), ten_vn.strip(),
         int(gia_min), int(gia_max), don_vi.strip(), sp_id)
    )
    conn.commit(); cur.close(); conn.close()


def _xoa(sp_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM san_pham WHERE id=%s", (sp_id,))
    conn.commit(); cur.close(); conn.close()


# ══════════════════════════════════════════════════════════════════
#  HỘP THOẠI THÊM / SỬA  (Modal dùng chung)
# ══════════════════════════════════════════════════════════════════

class _FormDialog(tk.Toplevel):
    """
    Pop-up nhập liệu dùng chung cho Thêm và Sửa.
    Sau khi đóng, kiểm tra self.result:
        None  → người dùng bấm Huỷ
        dict  → dữ liệu hợp lệ đã được validate
    """

    # Cấu hình các trường nhập liệu: (key, nhãn hiển thị, placeholder)
    _FIELDS = [
        ("ten_en",  "Tên tiếng Anh",   "vd: apple"),
        ("ten_vn",  "Tên tiếng Việt",  "vd: Táo"),
        ("gia_min", "Giá thấp nhất (đ)", "vd: 40000"),
        ("gia_max", "Giá cao nhất (đ)",  "vd: 70000"),
        ("don_vi",  "Đơn vị tính",           "vd: kg / trái / cái"),
    ]

    def __init__(self, parent: tk.Widget, tieu_de: str, data: dict = None):
        super().__init__(parent)
        self.title(tieu_de)
        self.configure(bg=THEME["bg2"])
        self.resizable(False, False)
        self.grab_set()          # Khoá tương tác cửa sổ cha (modal)
        self.result = None

        # ── Căn giữa so với cửa sổ gốc ──────────────────────────
        self.update_idletasks()
        px = parent.winfo_rootx() + parent.winfo_width()  // 2
        py = parent.winfo_rooty() + parent.winfo_height() // 2
        self.geometry(f"420x370+{px - 210}+{py - 185}")

        # ── Tiêu đề dialog ───────────────────────────────────────
        tk.Label(
            self, text=tieu_de,
            bg=THEME["bg2"], fg=THEME["fg"],
            font=("Segoe UI", 12, "bold")
        ).pack(anchor="w", padx=24, pady=(20, 2))

        tk.Frame(self, bg=THEME["border"], height=1).pack(
            fill="x", padx=24, pady=(0, 16))

        # ── Các trường nhập liệu ─────────────────────────────────
        form = tk.Frame(self, bg=THEME["bg2"])
        form.pack(fill="x", padx=24)

        self.entries = {}
        for key, label, placeholder in self._FIELDS:
            row = tk.Frame(form, bg=THEME["bg2"])
            row.pack(fill="x", pady=4)

            tk.Label(
                row, text=label, width=22, anchor="w",
                bg=THEME["bg2"], fg=THEME["fg_muted"],
                font=("Segoe UI", 9)
            ).pack(side="left")

            ent = tk.Entry(
                row,
                bg=THEME["bg3"], fg=THEME["fg"],
                insertbackground=THEME["fg"],
                relief="flat",
                font=("Segoe UI", 10),
                highlightthickness=1,
                highlightbackground=THEME["border"],
                highlightcolor=THEME["accent"]
            )
            ent.pack(side="left", fill="x", expand=True, ipady=5)

            # Hiển thị placeholder xám khi ô trống
            ent.insert(0, placeholder)
            ent.config(fg=THEME["fg_hint"])
            ent.bind("<FocusIn>",  lambda e, en=ent, ph=placeholder: self._clear_ph(en, ph))
            ent.bind("<FocusOut>", lambda e, en=ent, ph=placeholder: self._restore_ph(en, ph))

            self.entries[key] = ent

        # Điền dữ liệu gốc nếu đang ở chế độ Sửa
        if data:
            for key, val in data.items():
                if key in self.entries:
                    ent = self.entries[key]
                    ent.delete(0, "end")
                    ent.insert(0, str(val))
                    ent.config(fg=THEME["fg"])   # Màu chữ thật (không phải placeholder)

        # ── Thanh nút ────────────────────────────────────────────
        tk.Frame(self, bg=THEME["border"], height=1).pack(
            fill="x", padx=24, pady=(16, 0))

        btn_row = tk.Frame(self, bg=THEME["bg2"])
        btn_row.pack(fill="x", padx=24, pady=14)

        tk.Button(
            btn_row, text="Huỷ",
            bg=THEME["bg3"], fg=THEME["fg_muted"],
            activebackground=THEME["border"],
            font=("Segoe UI", 10), relief="flat",
            cursor="hand2", padx=18, pady=7,
            command=self.destroy
        ).pack(side="right", padx=(8, 0))

        tk.Button(
            btn_row, text="✓  Lưu",
            bg="#14532d", fg=THEME["green"],
            activebackground="#166534",
            font=("Segoe UI", 10, "bold"), relief="flat",
            cursor="hand2", padx=18, pady=7,
            command=self._luu
        ).pack(side="right")

    # ── Placeholder helpers ───────────────────────────────────────
    def _clear_ph(self, entry: tk.Entry, placeholder: str):
        if entry.get() == placeholder:
            entry.delete(0, "end")
            entry.config(fg=THEME["fg"])

    def _restore_ph(self, entry: tk.Entry, placeholder: str):
        if not entry.get():
            entry.insert(0, placeholder)
            entry.config(fg=THEME["fg_hint"])

    # ── Validate & lưu ───────────────────────────────────────────
    def _lay_gia_tri(self, key: str) -> str:
        """Lấy giá trị, trả về "" nếu vẫn là placeholder."""
        val = self.entries[key].get().strip()
        _, _, ph = next(f for f in self._FIELDS if f[0] == key)
        return "" if val == ph else val

    def _luu(self):
        vals = {key: self._lay_gia_tri(key) for key, *_ in self._FIELDS}

        # --- Data validation ---
        if not vals["ten_en"] or not vals["ten_vn"]:
            messagebox.showwarning(
                "Thiếu thông tin",
                "Tên tiếng Anh và Tên tiếng Việt không được để trống.",
                parent=self)
            return

        for key, label, _ in self._FIELDS:
            if key in ("gia_min", "gia_max"):
                try:
                    int(vals[key])
                except ValueError:
                    messagebox.showwarning(
                        "Giá không hợp lệ",
                        f"'{label}' phải là số nguyên (không có chữ, dấu phẩy).",
                        parent=self)
                    return

        if int(vals["gia_min"]) <= 0 or int(vals["gia_max"]) <= 0:
            messagebox.showwarning(
                "Giá không hợp lệ",
                "Giá thấp nhất và giá cao nhất phải lớn hơn 0.",
                parent=self)
            return
        
        if int(vals["gia_min"]) > int(vals["gia_max"]):
            messagebox.showwarning(
                "Giá không hợp lệ",
                "Giá thấp nhất không được lớn hơn giá cao nhất.",
                parent=self)
            return

        if not vals["don_vi"]:
            vals["don_vi"] = "kg"

        self.result = vals
        self.destroy()


# ══════════════════════════════════════════════════════════════════
#  PANEL CHÍNH  —  nhúng thẳng vào AppShell như một Tab
# ══════════════════════════════════════════════════════════════════

class PanelQuanLy(tk.Frame):
    """
    Tab "Quản lý sản phẩm" — CRUD đầy đủ cho bảng san_pham.
    Tương thích hook on_show / on_hide của AppShell.
    """

    def __init__(self, parent):
        super().__init__(parent, bg=THEME["bg"])
        self._du_lieu: list = []          # Cache dữ liệu gốc từ DB
        self._xay_giao_dien()

    # ── Hook của AppShell ─────────────────────────────────────────
    def on_show(self):
        """Tự động tải lại dữ liệu mỗi lần mở tab."""
        self._tai_du_lieu()

    # ══════════════════════════════════════════════════════════════
    #  XÂY DỰNG GIAO DIỆN
    # ══════════════════════════════════════════════════════════════

    def _xay_giao_dien(self):
        # ── Thanh công cụ trên cùng ───────────────────────────────
        toolbar = tk.Frame(
            self, bg=THEME["bg2"],
            highlightbackground=THEME["border"], highlightthickness=1
        )
        toolbar.pack(fill="x")

        tk.Label(
            toolbar, text="QUẢN LÝ SẢN PHẨM",
            bg=THEME["bg2"], fg=THEME["fg"],
            font=("Segoe UI", 11, "bold")
        ).pack(side="left", padx=20, pady=14)

        # Ô tìm kiếm
        search_wrap = tk.Frame(
            toolbar, bg=THEME["bg3"],
            highlightbackground=THEME["border"], highlightthickness=1
        )
        search_wrap.pack(side="left", padx=8, pady=10)

        tk.Label(
            search_wrap, text="🔍",
            bg=THEME["bg3"], fg=THEME["fg_muted"],
            font=("Segoe UI", 10)
        ).pack(side="left", padx=(8, 0))

        self._var_search = tk.StringVar()
        self._var_search.trace_add("write", lambda *_: self._loc())
        tk.Entry(
            search_wrap,
            textvariable=self._var_search,
            bg=THEME["bg3"], fg=THEME["fg"],
            insertbackground=THEME["fg"],
            relief="flat", font=("Segoe UI", 10), width=22
        ).pack(side="left", padx=6, ipady=5)

        # Nút Thêm
        tk.Button(
            toolbar, text="＋  Thêm sản phẩm",
            bg=THEME["accent"], fg=THEME["fg"],
            activebackground="#2563eb",
            font=("Segoe UI", 10, "bold"), relief="flat",
            cursor="hand2", padx=16, pady=8,
            command=self._them
        ).pack(side="right", padx=16, pady=10)

        # ── Bảng dữ liệu ─────────────────────────────────────────
        table_wrap = tk.Frame(self, bg=THEME["bg"])
        table_wrap.pack(fill="both", expand=True, padx=16, pady=12)

        self._ap_style_bang()

        cols = ("ID", "Tên EN", "Tên VN", "Giá thấp", "Giá cao", "Đơn vị")
        self.tree = ttk.Treeview(
            table_wrap,
            columns=cols,
            show="headings",
            style="CRUD.Treeview",
            selectmode="browse"
        )

        do_rong = {
            "ID": 50, "Tên EN": 140, "Tên VN": 150,
            "Giá thấp": 120, "Giá cao": 120, "Đơn vị": 80
        }
        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(
                col,
                width=do_rong[col],
                anchor="center" if col == "ID" else "w",
                stretch=(col == "Tên VN")
            )

        sb = ttk.Scrollbar(table_wrap, orient="vertical",
                           command=self.tree.yview)
        self.tree.configure(yscroll=sb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        # ── Thanh hành động dưới cùng ─────────────────────────────
        footer = tk.Frame(
            self, bg=THEME["bg2"],
            highlightbackground=THEME["border"], highlightthickness=1
        )
        footer.pack(fill="x", side="bottom")

        self._lbl_status = tk.Label(
            footer, text="",
            bg=THEME["bg2"], fg=THEME["fg_muted"],
            font=("Segoe UI", 9)
        )
        self._lbl_status.pack(side="left", padx=20, pady=12)

        tk.Button(
            footer, text="🗑  Xoá",
            bg=THEME["bg3"], fg=THEME["red"],
            activebackground=THEME["border"],
            font=("Segoe UI", 10), relief="flat",
            cursor="hand2", padx=14, pady=7,
            command=self._xoa
        ).pack(side="right", padx=8, pady=10)

        tk.Button(
            footer, text="✎  Sửa",
            bg=THEME["bg3"], fg=THEME["yellow"],
            activebackground=THEME["border"],
            font=("Segoe UI", 10), relief="flat",
            cursor="hand2", padx=14, pady=7,
            command=self._sua
        ).pack(side="right", pady=10)

    def _ap_style_bang(self):
        """Áp màu THEME lên ttk.Treeview — phải gọi trước khi tạo widget."""
        s = ttk.Style(self)
        s.theme_use("default")
        s.configure(
            "CRUD.Treeview",
            background=THEME["bg2"],
            foreground=THEME["fg"],
            fieldbackground=THEME["bg2"],
            borderwidth=0,
            rowheight=34,
            font=("Segoe UI", 10)
        )
        s.configure(
            "CRUD.Treeview.Heading",
            background=THEME["bg3"],
            foreground=THEME["fg_muted"],
            borderwidth=0,
            font=("Segoe UI", 9, "bold"),
            relief="flat"
        )
        s.map(
            "CRUD.Treeview",
            background=[("selected", "#1e3a4f")],
            foreground=[("selected", THEME["accent"])]
        )
        # Xoá đường viền mặc định của treearea
        s.layout("CRUD.Treeview", [
            ("CRUD.Treeview.treearea", {"sticky": "nswe"})
        ])

    # ══════════════════════════════════════════════════════════════
    #  DỮ LIỆU
    # ══════════════════════════════════════════════════════════════

    def _tai_du_lieu(self):
        self._du_lieu = _lay_tat_ca()
        self._hien_bang(self._du_lieu)

    def _hien_bang(self, rows: list):
        for item in self.tree.get_children():
            self.tree.delete(item)
        # iid using real ID for func, ID on UI is for counting
        for stt, row in enumerate(rows, start=1):
            sp_id, ten_en, ten_vn, gia_min, gia_max, don_vi = row
            self.tree.insert(
                "", "end",
                iid=str(sp_id),   
                values=(
                    stt,          # Hiển thị STT liên tục, không phụ thuộc ID DB
                    ten_en, ten_vn,
                    f"{gia_min:,}đ",
                    f"{gia_max:,}đ",
                    don_vi
                )
            )
 
        total = len(self._du_lieu)
        shown = len(rows)
        if shown < total:
            self._lbl_status.config(text=f"{shown}/{total} sản phẩm (đang lọc)")
        else:
            self._lbl_status.config(text=f"{total} sản phẩm")

    def _loc(self):
        q = self._var_search.get().strip().lower()
        if not q:
            self._hien_bang(self._du_lieu)
            return
        ket_qua = [
            r for r in self._du_lieu
            if q in r[1].lower() or q in r[2].lower()
        ]
        self._hien_bang(ket_qua)

    def _lay_hang_dang_chon(self) -> dict | None:
        """Trả về dict dữ liệu hàng đang được chọn; None nếu chưa chọn."""
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo(
                "Chưa chọn hàng",
                "Vui lòng bấm vào một sản phẩm trong bảng trước.",
                parent=self
            )
            return None
        sp_id = int(sel[0])
        row = next((r for r in self._du_lieu if r[0] == sp_id), None)
        if row is None:
            return None
        return {
            "id": row[0], "ten_en": row[1], "ten_vn": row[2],
            "gia_min": row[3], "gia_max": row[4], "don_vi": row[5]
        }

    # ══════════════════════════════════════════════════════════════
    #  HÀNH ĐỘNG CRUD
    # ══════════════════════════════════════════════════════════════

    def _them(self):
        dlg = _FormDialog(self, "Thêm sản phẩm mới")
        self.wait_window(dlg)
        if dlg.result is None:
            return
        try:
            d = dlg.result
            _them(d["ten_en"], d["ten_vn"], d["gia_min"], d["gia_max"], d["don_vi"])
            self._tai_du_lieu()
            self._thong_bao(f"✓  Đã thêm  '{d['ten_vn']}'", THEME["green"])
        except Exception as e:
            messagebox.showerror("Lỗi khi thêm", str(e), parent=self)

    def _sua(self):
        data = self._lay_hang_dang_chon()
        if data is None:
            return
        dlg = _FormDialog(self, f"Sửa — {data['ten_vn']}", data=data)
        self.wait_window(dlg)
        if dlg.result is None:
            return
        try:
            d = dlg.result
            _sua(data["id"], d["ten_en"], d["ten_vn"],
                 d["gia_min"], d["gia_max"], d["don_vi"])
            self._tai_du_lieu()
            self._thong_bao(f"✓  Đã cập nhật  '{d['ten_vn']}'", THEME["green"])
        except Exception as e:
            messagebox.showerror("Lỗi khi sửa", str(e), parent=self)

    def _xoa(self):
        data = self._lay_hang_dang_chon()
        if data is None:
            return
        xac_nhan = messagebox.askyesno(
            "Xác nhận xoá",
            f"Xoá  '{data['ten_vn']} ({data['ten_en']})'?\n\nThao tác này không thể hoàn tác.",
            icon="warning",
            parent=self
        )
        if not xac_nhan:
            return
        try:
            _xoa(data["id"])
            self._tai_du_lieu()
            self._thong_bao(f"🗑  Đã xoá  '{data['ten_vn']}'", THEME["red"])
        except Exception as e:
            messagebox.showerror("Lỗi khi xoá", str(e), parent=self)

    # ── Hiển thị thông báo tạm thời ở footer ─────────────────────
    def _thong_bao(self, msg: str, mau: str, ms: int = 3000):
        self._lbl_status.config(text=msg, fg=mau)
        self.after(ms, lambda: self._lbl_status.config(
            text=f"{len(self._du_lieu)} sản phẩm",
            fg=THEME["fg_muted"]
        ))