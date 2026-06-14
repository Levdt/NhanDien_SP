"""
lich_su_panel.py — Panel lịch sử nhận diện (tách từ main_frame.py)
===================================================================
Import vào main_frame.py bằng:
    from lich_su_panel import PanelLichSu
"""

import tkinter as tk
from tkinter import ttk
from main_frame import THEME   # dùng chung bảng màu với toàn hệ thống


class PanelLichSu(tk.Frame):
    """
    Panel lịch sử nhận diện — đã sửa toàn bộ:
      • Validate tên / ngày / confidence không dùng textvariable để tránh xung đột trace
      • Ngày tự chèn '/', chặn ngày > 31 (28/29 cho T2), tháng > 12
      • Nút Làm mới reset hẳn nội dung entry lẫn placeholder
      • Hủy chọn dùng Button-1 trên tree thay vì ButtonRelease-1 để không can thiệp vào selection
    """

    # ────────────────────────────────────────────────────────────────
    #  Khởi tạo giao diện
    # ────────────────────────────────────────────────────────────────
    def __init__(self, parent):
        super().__init__(parent, bg=THEME["bg2"])
        self._all_rows  = []
        self._loading   = False          # cờ chặn _ap_bo_loc khi đang reset
        self.sort_var   = tk.StringVar(value="Thời gian (Mới → Cũ)")

        # ── Các Entry widget — lưu để reset từ bên ngoài ────────────
        self._search_entry = None
        self._efrom        = None
        self._eto          = None
        self._econf_min    = None
        self._econf_max    = None

        # ── StringVar nội bộ — KHÔNG gắn textvariable vào Entry ─────
        # (tránh xung đột giữa validate-cmd và trace)
        self.search_var = tk.StringVar(value="")
        self.date_from  = tk.StringVar(value="")
        self.date_to    = tk.StringVar(value="")
        self.conf_min   = tk.StringVar(value="0")
        self.conf_max   = tk.StringVar(value="100")

        self._build_ui()

    # ────────────────────────────────────────────────────────────────
    #  Xây dựng giao diện
    # ────────────────────────────────────────────────────────────────
    def _build_ui(self):
        # ── Row 0: Tìm kiếm + Làm mới ───────────────────────────────
        row0 = tk.Frame(self, bg=THEME["bg2"])
        row0.pack(fill="x", padx=20, pady=(16, 6))

        tk.Label(row0, text="Tìm kiếm theo tên", bg=THEME["bg2"], fg=THEME["fg_muted"],
                 font=("Segoe UI", 11)).pack(side="left", padx=(0, 5))

        self._search_entry = tk.Entry(
            row0, bg=THEME["bg3"], fg=THEME["fg_hint"],
            insertbackground=THEME["fg"],
            font=("Segoe UI", 10), bd=0,
            highlightbackground=THEME["border"],
            highlightthickness=1, relief="flat", width=26)
        self._search_entry.pack(side="left", ipady=6, padx=(0, 12))
        self._setup_search_entry(self._search_entry)

        tk.Label(row0, text="Ctrl+Click để chọn nhiều hàng",
                 bg=THEME["bg2"], fg=THEME["fg_hint"],
                 font=("Segoe UI", 8, "italic")).pack(side="left")

        tk.Button(row0, text="Làm mới", bg=THEME["accent"], fg=THEME["fg"],
                  font=("Segoe UI", 9, "bold"), bd=0, padx=12, pady=5,
                  cursor="hand2", activebackground="#2563eb",
                  activeforeground=THEME["fg"],
                  command=self.tai_lich_su).pack(side="right")

        # ── Nhóm lọc ────────────────────────────────────────────────
        grp_filter = tk.LabelFrame(
            self, text="   Bộ lọc  ", bg=THEME["bg2"], fg=THEME["fg_muted"],
            font=("Segoe UI", 8, "bold"), bd=1, relief="groove",
            highlightbackground=THEME["border"])
        grp_filter.pack(fill="x", padx=20, pady=(0, 6))

        tk.Label(grp_filter, text="Thời gian quét:", bg=THEME["bg2"],
                 fg=THEME["fg_muted"], font=("Segoe UI", 9, "bold")).pack(
                     side="left", padx=(12, 6), pady=8)

        self._efrom = tk.Entry(grp_filter, width=11,
                               bg=THEME["bg3"], fg=THEME["fg_hint"],
                               insertbackground=THEME["fg"], font=("Segoe UI", 10),
                               bd=0, highlightbackground=THEME["border"],
                               highlightthickness=1, relief="flat")
        self._efrom.pack(side="left", ipady=5, padx=(0, 4))
        self._setup_date_entry(self._efrom, self.date_from)

        tk.Label(grp_filter, text="→", bg=THEME["bg2"],
                 fg=THEME["fg_muted"], font=("Segoe UI", 10)).pack(side="left", padx=3)

        self._eto = tk.Entry(grp_filter, width=11,
                             bg=THEME["bg3"], fg=THEME["fg_hint"],
                             insertbackground=THEME["fg"], font=("Segoe UI", 10),
                             bd=0, highlightbackground=THEME["border"],
                             highlightthickness=1, relief="flat")
        self._eto.pack(side="left", ipady=5, padx=(4, 20))
        self._setup_date_entry(self._eto, self.date_to)

        tk.Frame(grp_filter, bg=THEME["border"], width=1).pack(
            side="left", fill="y", pady=6, padx=(0, 16))

        tk.Label(grp_filter, text="Độ chính xác:", bg=THEME["bg2"],
                 fg=THEME["fg_muted"], font=("Segoe UI", 9, "bold")).pack(
                     side="left", padx=(0, 6))

        self._econf_min = tk.Entry(grp_filter, width=5,
                                   bg=THEME["bg3"], fg=THEME["fg"],
                                   insertbackground=THEME["fg"],
                                   font=("Segoe UI", 10), bd=0,
                                   highlightbackground=THEME["border"],
                                   highlightthickness=1, relief="flat",
                                   justify="center")
        self._econf_min.pack(side="left", ipady=5)
        self._setup_conf_entry(self._econf_min, self.conf_min)

        tk.Label(grp_filter, text="% → ", bg=THEME["bg2"],
                 fg=THEME["fg_muted"], font=("Segoe UI", 9)).pack(side="left", padx=3)

        self._econf_max = tk.Entry(grp_filter, width=5,
                                   bg=THEME["bg3"], fg=THEME["fg"],
                                   insertbackground=THEME["fg"],
                                   font=("Segoe UI", 10), bd=0,
                                   highlightbackground=THEME["border"],
                                   highlightthickness=1, relief="flat",
                                   justify="center")
        self._econf_max.pack(side="left", ipady=5)
        self._setup_conf_entry(self._econf_max, self.conf_max)

        tk.Label(grp_filter, text="%", bg=THEME["bg2"],
                 fg=THEME["fg_muted"], font=("Segoe UI", 9)).pack(side="left", padx=(2, 12))

        # ── Nhóm sắp xếp & thao tác ─────────────────────────────────
        grp_action = tk.LabelFrame(
            self, text="  Sắp xếp & Thao tác  ", bg=THEME["bg2"], fg=THEME["fg_muted"],
            font=("Segoe UI", 8, "bold"), bd=1, relief="groove",
            highlightbackground=THEME["border"])
        grp_action.pack(fill="x", padx=20, pady=(0, 10))

        sort_group = tk.Frame(grp_action, bg=THEME["bg2"])
        sort_group.pack(side="left", padx=12, pady=8)
        tk.Label(sort_group, text="Sắp xếp theo:", bg=THEME["bg2"],
                 fg=THEME["fg_muted"], font=("Segoe UI", 9, "bold")).pack(
                     side="left", padx=(0, 8))
        self.cbo_sort = ttk.Combobox(
            sort_group, textvariable=self.sort_var, state="readonly", width=25,
            values=["Thời gian (Mới → Cũ)", "Thời gian (Cũ → Mới)",
                    "Độ chính xác (Cao → Thấp)", "Độ chính xác (Thấp → Cao)",
                    "Tên (A → Z)", "Tên (Z → A)"])
        self.cbo_sort.pack(side="left")
        self.cbo_sort.bind("<<ComboboxSelected>>", lambda e: self._ap_bo_loc())

        tk.Frame(grp_action, bg=THEME["border"], width=1).pack(
            side="left", fill="y", pady=6, padx=(8, 12))

        del_group = tk.Frame(grp_action, bg=THEME["bg2"])
        del_group.pack(side="left", pady=8)
        tk.Label(del_group, text="Thao tác:", bg=THEME["bg2"],
                 fg=THEME["fg_muted"], font=("Segoe UI", 9, "bold")).pack(
                     side="left", padx=(0, 8))
        tk.Button(del_group, text="Xóa đã chọn", bg=THEME["bg3"],
                  fg=THEME["red"], font=("Segoe UI", 9, "bold"), bd=0,
                  padx=10, pady=5, cursor="hand2",
                  activebackground=THEME["border"],
                  command=self._xoa_chon).pack(side="left", padx=(0, 6))
        tk.Button(del_group, text="Xóa tất cả", bg="#3b1f1f",
                  fg=THEME["red"], font=("Segoe UI", 9, "bold"), bd=0,
                  padx=10, pady=5, cursor="hand2",
                  activebackground="#5c2020",
                  command=self._xoa_tat_ca).pack(side="left")

        # ── Treeview ─────────────────────────────────────────────────
        cols = ("stt", "ten_sp", "thoi_gian", "do_chinh_xac")
        style = ttk.Style()
        style.theme_use("default")
        style.configure("LS.Treeview",
                        background=THEME["bg3"], foreground=THEME["fg"],
                        fieldbackground=THEME["bg3"], rowheight=34,
                        font=("Segoe UI", 10), borderwidth=0)
        style.configure("LS.Treeview.Heading",
                        background=THEME["bg"], foreground=THEME["fg_muted"],
                        font=("Segoe UI", 9, "bold"), relief="flat", borderwidth=0)
        style.map("LS.Treeview",
                  background=[("selected", THEME["accent"])],
                  foreground=[("selected", THEME["fg"])])
        style.map("LS.Treeview.Heading",
                  background=[("active", THEME["bg3"])])

        table_frame = tk.Frame(self, bg=THEME["border"], bd=1)
        table_frame.pack(fill="both", expand=True, padx=20, pady=(0, 6))

        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings",
                                  style="LS.Treeview", selectmode="extended")
        self.tree.heading("stt",          text="STT",            anchor="center")
        self.tree.heading("ten_sp",       text="Tên sản phẩm",   anchor="w")
        self.tree.heading("thoi_gian",    text="Thời gian quét", anchor="center")
        self.tree.heading("do_chinh_xac", text="Độ chính xác",   anchor="center")
        self.tree.column("stt",          width=55,  minwidth=45,  anchor="center", stretch=False)
        self.tree.column("ten_sp",       width=300, minwidth=150, anchor="w",      stretch=True)
        self.tree.column("thoi_gian",    width=190, minwidth=140, anchor="center", stretch=False)
        self.tree.column("do_chinh_xac", width=130, minwidth=100, anchor="center", stretch=False)

        sb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        self.tree.tag_configure("odd",  background=THEME["bg3"])
        self.tree.tag_configure("even", background="#1e222b")

        # Hủy chọn khi click vào vùng trống trong tree hoặc bất kỳ đâu trên panel
        def _deselect_if_empty_in_tree(ev):
            region = self.tree.identify_region(ev.x, ev.y)
            if region not in ("cell", "tree"):
                self.tree.selection_set([])
        self.tree.bind("<Button-1>", _deselect_if_empty_in_tree, add="+")

        # Click vào bất kỳ widget nào trên panel (ngoài tree) → hủy chọn + kiểm tra hoán đổi
        def _on_outside_click(ev):
            self.tree.selection_set([])
            self._kiem_tra_hoan_doi()

        def _bind_deselect_recursive(widget):
            if widget is self.tree or isinstance(widget, ttk.Scrollbar):
                return
            widget.bind("<Button-1>", _on_outside_click, add="+")
            for child in widget.winfo_children():
                _bind_deselect_recursive(child)

        # Bind trên chính tree để kiểm tra hoán đổi khi click vào bảng
        self.tree.bind("<Button-1>",
                       lambda ev: self._kiem_tra_hoan_doi(), add="+")

        self.after(100, lambda: _bind_deselect_recursive(self))

        # Thanh trạng thái
        self.lbl_status = tk.Label(self, text="", bg=THEME["bg2"],
                                   fg=THEME["fg_muted"], font=("Segoe UI", 9))
        self.lbl_status.pack(anchor="e", padx=20, pady=(0, 8))

    # ────────────────────────────────────────────────────────────────
    #  Setup từng loại Entry — KHÔNG dùng textvariable
    # ────────────────────────────────────────────────────────────────

    def _setup_search_entry(self, e: tk.Entry):
        """Ô tìm kiếm: chỉ chữ cái + dấu cách, có placeholder.
        Validate khi focus out: không cho ký tự không hợp lệ, hiển thị cảnh báo.
        Dùng dict _s để chia sẻ trạng thái is_ph với _reset_filters."""
        PH = "Tên sản phẩm..."
        _s = {"is_ph": True}
        e._ph_state = _s

        e.delete(0, "end")
        e.insert(0, PH)
        e.config(fg=THEME["fg_hint"])

        def _on_focus_in(_ev):
            if _s["is_ph"]:
                _s["is_ph"] = False
                e.delete(0, "end")
                e.config(fg=THEME["fg"])

        def _on_focus_out(_ev):
            txt = e.get().strip()
            if not txt:
                _s["is_ph"] = True
                e.delete(0, "end")
                e.insert(0, PH)
                e.config(fg=THEME["fg_hint"])
                self.search_var.set("")
            else:
                clean = "".join(c for c in txt if c.isalpha() or c.isspace())
                if clean != txt:
                    e.config(highlightbackground=THEME["red"], highlightcolor=THEME["red"])
                    from tkinter import messagebox
                    messagebox.showwarning(
                        "Ký tự không hợp lệ",
                        "Tên sản phẩm chỉ được chứa chữ cái và dấu cách.\n"
                        "Ký tự số và ký tự đặc biệt không được phép.",
                        parent=self)
                    e.config(highlightbackground=THEME["border"])
                    return
                e.config(highlightbackground=THEME["border"])
                self.search_var.set(txt)
                if not self._loading:
                    self._ap_bo_loc()

        def _on_key(_ev):
            if _s["is_ph"]:
                return
            txt = e.get()
            self.search_var.set(txt)
            if not self._loading:
                self._ap_bo_loc()

        e.bind("<FocusIn>",    _on_focus_in)
        e.bind("<FocusOut>",   _on_focus_out)
        e.bind("<KeyRelease>", _on_key)

    def _setup_date_entry(self, e: tk.Entry, var: tk.StringVar):
        """
        Ô ngày DD/MM/YYYY (không hiện dấu /):
          - Mask hiển thị: __/__/____ , gõ số điền vào từng vị trí
          - Tự thêm 0 khi gõ chữ số đầu tiên của DD hoặc MM mà > 3 (ngày) / > 1 (tháng)
          - Clamp: ngày ≤ max ngày của tháng, tháng ≤ 12
          - Xóa (BackSpace) lùi và xóa chữ số trước con trỏ
          - Hoán đổi tự động ngày_từ ↔ ngày_đến nếu nhập ngược chiều
        """
        import calendar as _cal
        MASK = "__/__/____"
        SLOTS = [0, 1, 3, 4, 6, 7, 8, 9]

        _s = {"is_ph": True}
        e._ph_state = _s

        def _show_ph():
            _s["is_ph"] = True
            e.delete(0, "end")
            e.insert(0, MASK)
            e.config(fg=THEME["fg_hint"])
            var.set("")

        def _is_complete(txt):
            return len(txt) == 10 and "_" not in txt

        def _buf(txt):
            return "".join(c for c in txt if c.isdigit())

        def _render(digits: str) -> str:
            d = digits.ljust(8, "_")
            return f"{d[0]}{d[1]}/{d[2]}{d[3]}/{d[4]}{d[5]}{d[6]}{d[7]}"

        def _clamp(digits: str) -> str:
            d = list(digits.ljust(8, "_"))
            if d[2].isdigit() and d[3].isdigit():
                mm = int(d[2] + d[3])
                if mm < 1:    d[2], d[3] = "0", "1"
                elif mm > 12: d[2], d[3] = "1", "2"
            elif d[2].isdigit() and d[2] > "1":
                d.insert(2, "0"); d = d[:8]

            if d[0].isdigit() and d[1].isdigit():
                dd = int(d[0] + d[1])
                try:
                    mm2 = int(d[2] + d[3]) if d[2].isdigit() and d[3].isdigit() else 1
                    yy2 = int("".join(d[4:8])) if all(x.isdigit() for x in d[4:8]) else 2000
                    max_d = _cal.monthrange(yy2, mm2)[1]
                except Exception:
                    max_d = 31
                if dd < 1:       d[0], d[1] = "0", "1"
                elif dd > max_d: d[0], d[1] = str(max_d).zfill(2)
            elif d[0].isdigit() and d[0] > "3":
                d.insert(0, "0"); d = d[:8]

            return "".join(d)

        def _on_focus_in(_ev):
            if _s["is_ph"]:
                _s["is_ph"] = False
                e.delete(0, "end")
                e.insert(0, MASK)
                e.config(fg=THEME["fg"])
                e.icursor(0)

        def _on_focus_out(_ev):
            from datetime import datetime
            txt = e.get()
            if not txt or txt == MASK or "_" in txt:
                if "_" in txt and txt != MASK:
                    var.set("")
                else:
                    _show_ph()
                    return
            else:
                try:
                    cur_date = datetime.strptime(txt, "%d/%m/%Y")
                    is_from = (e == self._efrom)

                    if is_from:
                        to_txt = self._eto.get()
                        if to_txt and "_" not in to_txt and to_txt != MASK:
                            try:
                                to_date = datetime.strptime(to_txt, "%d/%m/%Y")
                                if cur_date > to_date:
                                    # Hoán đổi: ngày_từ ↔ ngày_đến
                                    self._efrom.delete(0, "end")
                                    self._efrom.insert(0, to_txt)
                                    self._efrom._ph_state["is_ph"] = False
                                    self._efrom.config(fg=THEME["fg"])
                                    self.date_from.set(to_txt)

                                    self._eto.delete(0, "end")
                                    self._eto.insert(0, txt)
                                    self._eto._ph_state["is_ph"] = False
                                    self._eto.config(fg=THEME["fg"])
                                    self.date_to.set(txt)

                                    e.config(highlightbackground=THEME["border"])
                                    if not self._loading:
                                        self._ap_bo_loc()
                                    return
                            except ValueError:
                                pass
                    else:
                        from_txt = self._efrom.get()
                        if from_txt and "_" not in from_txt and from_txt != MASK:
                            try:
                                from_date = datetime.strptime(from_txt, "%d/%m/%Y")
                                if cur_date < from_date:
                                    # Hoán đổi: ngày_từ ↔ ngày_đến
                                    self._eto.delete(0, "end")
                                    self._eto.insert(0, from_txt)
                                    self._eto._ph_state["is_ph"] = False
                                    self._eto.config(fg=THEME["fg"])
                                    self.date_to.set(from_txt)

                                    self._efrom.delete(0, "end")
                                    self._efrom.insert(0, txt)
                                    self._efrom._ph_state["is_ph"] = False
                                    self._efrom.config(fg=THEME["fg"])
                                    self.date_from.set(txt)

                                    e.config(highlightbackground=THEME["border"])
                                    if not self._loading:
                                        self._ap_bo_loc()
                                    return
                            except ValueError:
                                pass

                    e.config(highlightbackground=THEME["border"])
                    var.set(txt)
                except ValueError:
                    pass

            if not self._loading:
                self._ap_bo_loc()

        def _on_key(ev):
            if _s["is_ph"]:
                return

            if ev.keysym == "BackSpace":
                cur = e.get()
                pos = e.index("insert")
                prev_slot = None
                for s in reversed(SLOTS):
                    if s < pos:
                        prev_slot = s; break
                if prev_slot is not None:
                    chars = list(cur)
                    chars[prev_slot] = "_"
                    new = "".join(chars)
                    e.delete(0, "end")
                    e.insert(0, new)
                    e.icursor(prev_slot)
                    var.set("" if "_" in new else new)
                    if not self._loading: self._ap_bo_loc()
                return "break"

            if ev.keysym in ("Delete", "Left", "Right", "Tab", "Home", "End",
                              "Escape", "Return"):
                return

            ch = ev.char
            if not ch or not ch.isdigit():
                return "break"

            cur = e.get()
            pos = e.index("insert")

            target = None
            for s in SLOTS:
                if s >= pos:
                    target = s; break
            if target is None:
                return "break"

            chars = list(cur)
            chars[target] = ch
            digits_new = _clamp(_buf("".join(chars)))
            new_val    = _render(digits_new)

            next_pos = len(new_val)
            for s in SLOTS:
                if s > target and new_val[s] == "_":
                    next_pos = s; break

            e.delete(0, "end")
            e.insert(0, new_val)
            e.icursor(next_pos)

            complete_val = new_val if "_" not in new_val else ""
            var.set(complete_val)
            if not self._loading: self._ap_bo_loc()
            return "break"

        e.bind("<FocusIn>",  _on_focus_in)
        e.bind("<FocusOut>", _on_focus_out)
        e.bind("<KeyPress>", _on_key)
        _show_ph()

    def _setup_conf_entry(self, e: tk.Entry, var: tk.StringVar):
        """Ô confidence 0–100: chặn ký tự không hợp lệ ngay khi nhập (chỉ cho phép
        số nguyên 0–100). Ký tự chữ cái, đặc biệt, dấu âm, dấu chấm đều bị
        chặn tại chỗ — không hiện hộp cảnh báo.
        Khi focus out: clamp về [0,100] và hoán đổi tự động nếu min > max."""
        e.insert(0, var.get())

        def _on_key_press(ev):
            """Chặn ký tự không hợp lệ ngay tại bàn phím — trả về 'break' để nuốt."""
            # Cho qua các phím điều hướng / chỉnh sửa không tạo ký tự
            if ev.keysym in ("BackSpace", "Delete", "Left", "Right",
                              "Home", "End", "Tab", "Escape", "Return"):
                return  # xử lý bình thường

            ch = ev.char
            # Chặn nếu không phải chữ số
            if not ch or not ch.isdigit():
                return "break"

            # Kiểm tra xem nếu thêm ch vào vị trí con trỏ thì có vượt 100 không
            cur     = e.get()
            sel     = e.selection_present()
            if sel:
                # Có vùng chọn: thay vùng chọn bằng ch
                i1 = e.index("sel.first")
                i2 = e.index("sel.last")
                preview = cur[:i1] + ch + cur[i2:]
            else:
                pos     = e.index("insert")
                preview = cur[:pos] + ch + cur[pos:]

            # Loại bỏ số 0 dẫn đầu (ví dụ "007" → không hợp lệ)
            if preview and preview != "0" and preview.startswith("0"):
                return "break"

            # Chặn nếu vượt quá 3 chữ số hoặc > 100
            if len(preview) > 3:
                return "break"
            try:
                if int(preview) > 100:
                    return "break"
            except ValueError:
                return "break"

            # Hợp lệ — cho qua
            return

        def _on_focus_out(_ev):
            cur = e.get().strip()

            # Ô trống → đặt về 0
            if not cur:
                var.set("0")
                e.delete(0, "end")
                e.insert(0, "0")
                if not self._loading:
                    self._ap_bo_loc()
                return

            # Clamp an toàn về [0, 100]
            try:
                v = max(0, min(100, int(cur)))
            except ValueError:
                v = 0

            e.delete(0, "end")
            e.insert(0, str(v))
            var.set(str(v))

            # Hoán đổi tự động nếu min > max
            try:
                conf_min = float(self.conf_min.get() or "0")
                conf_max = float(self.conf_max.get() or "100")
                if conf_min > conf_max:
                    conf_min, conf_max = conf_max, conf_min
                    self.conf_min.set(str(int(conf_min)))
                    self.conf_max.set(str(int(conf_max)))
                    self._econf_min.delete(0, "end")
                    self._econf_min.insert(0, str(int(conf_min)))
                    self._econf_max.delete(0, "end")
                    self._econf_max.insert(0, str(int(conf_max)))
            except ValueError:
                pass

            if not self._loading:
                self._ap_bo_loc()

        e.bind("<KeyPress>",  _on_key_press)
        e.bind("<FocusOut>",  _on_focus_out)

    # ────────────────────────────────────────────────────────────────
    #  Kiểm tra & hoán đổi tự động khi click bất kỳ đâu trong cửa sổ
    # ────────────────────────────────────────────────────────────────
    def _kiem_tra_hoan_doi(self):
        """Gọi khi người dùng click bất kỳ đâu trong panel.
        Nếu vế trái > vế phải ở Độ chính xác hoặc Thời gian quét → hoán đổi ngay."""
        changed = False

        # ── 1. Hoán đổi Độ chính xác ────────────────────────────────
        try:
            raw_min = self._econf_min.get().strip()
            raw_max = self._econf_max.get().strip()
            if raw_min and raw_max:
                v_min = int(raw_min)
                v_max = int(raw_max)
                if v_min > v_max:
                    # Hoán đổi giá trị
                    self.conf_min.set(str(v_max))
                    self.conf_max.set(str(v_min))
                    self._econf_min.delete(0, "end")
                    self._econf_min.insert(0, str(v_max))
                    self._econf_max.delete(0, "end")
                    self._econf_max.insert(0, str(v_min))
                    changed = True
        except ValueError:
            pass

        # ── 2. Hoán đổi Thời gian quét ──────────────────────────────
        from datetime import datetime
        MASK = "__/__/____"
        try:
            from_txt = self._efrom.get()
            to_txt   = self._eto.get()
            from_ok  = from_txt and "_" not in from_txt and from_txt != MASK
            to_ok    = to_txt   and "_" not in to_txt   and to_txt   != MASK
            if from_ok and to_ok:
                d_from = datetime.strptime(from_txt, "%d/%m/%Y")
                d_to   = datetime.strptime(to_txt,   "%d/%m/%Y")
                if d_from > d_to:
                    # Hoán đổi
                    self._efrom.delete(0, "end")
                    self._efrom.insert(0, to_txt)
                    self._efrom._ph_state["is_ph"] = False
                    self._efrom.config(fg=THEME["fg"])
                    self.date_from.set(to_txt)

                    self._eto.delete(0, "end")
                    self._eto.insert(0, from_txt)
                    self._eto._ph_state["is_ph"] = False
                    self._eto.config(fg=THEME["fg"])
                    self.date_to.set(from_txt)
                    changed = True
        except (ValueError, AttributeError):
            pass

        if changed and not self._loading:
            self._ap_bo_loc()

    # ────────────────────────────────────────────────────────────────
    #  Reset toàn bộ bộ lọc (cho nút Làm mới)
    # ────────────────────────────────────────────────────────────────
    def _reset_filters(self):
        """Đặt lại tất cả entry về trạng thái ban đầu + placeholder."""
        PH_NAME = "Tên sản phẩm..."
        MASK    = "__/__/____"

        self.search_var.set("")
        self._search_entry._ph_state["is_ph"] = True
        self._search_entry.delete(0, "end")
        self._search_entry.insert(0, PH_NAME)
        self._search_entry.config(fg=THEME["fg_hint"])

        self.date_from.set("")
        self._efrom._ph_state["is_ph"] = True
        self._efrom.delete(0, "end")
        self._efrom.insert(0, MASK)
        self._efrom.config(fg=THEME["fg_hint"])

        self.date_to.set("")
        self._eto._ph_state["is_ph"] = True
        self._eto.delete(0, "end")
        self._eto.insert(0, MASK)
        self._eto.config(fg=THEME["fg_hint"])

        self.conf_min.set("0")
        self._econf_min.delete(0, "end")
        self._econf_min.insert(0, "0")

        self.conf_max.set("100")
        self._econf_max.delete(0, "end")
        self._econf_max.insert(0, "100")

        self.sort_var.set("Thời gian (Mới → Cũ)")

    # ────────────────────────────────────────────────────────────────
    #  Tải dữ liệu
    # ────────────────────────────────────────────────────────────────
    def on_show(self):
        self.tai_lich_su()

    def tai_lich_su(self):
        self._loading = True
        try:
            from db import get_conn
            conn = get_conn()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, ten_sp, confidence, thoi_gian "
                "FROM lich_su ORDER BY thoi_gian DESC LIMIT 1000"
            )
            self._all_rows = cursor.fetchall()
            cursor.close(); conn.close()
        except Exception as ex:
            self._loading = False
            self.lbl_status.config(text=f"Lỗi: {ex}", fg=THEME["red"])
            return

        self._reset_filters()
        self._loading = False
        self._ap_bo_loc()

    # ────────────────────────────────────────────────────────────────
    #  Bộ lọc + Sắp xếp
    # ────────────────────────────────────────────────────────────────
    def _ap_bo_loc(self):
        if self._loading:
            return
        from datetime import datetime

        keyword = self.search_var.get().strip().lower()
        df_str  = self.date_from.get().strip()
        dt_str  = self.date_to.get().strip()

        try:
            c_min = float(self.conf_min.get() or "0") / 100.0
        except ValueError:
            c_min = 0.0
        try:
            c_max = float(self.conf_max.get() or "100") / 100.0
        except ValueError:
            c_max = 1.0

        c_min = max(0.0, min(c_min, 1.0))
        c_max = max(0.0, min(c_max, 1.0))
        if c_min > c_max:
            c_min, c_max = c_max, c_min

        def parse_date(s):
            try:
                return datetime.strptime(s, "%d/%m/%Y")
            except Exception:
                return None

        df = parse_date(df_str)
        dt = parse_date(dt_str)

        filtered = []
        for row in self._all_rows:
            _, ten_sp, conf, tg = row
            if keyword and not ten_sp.lower().startswith(keyword):
                continue
            conf_norm = conf / 100.0 if conf > 1.0 else conf
            if not (c_min <= conf_norm <= c_max):
                continue
            if df and tg.date() < df.date():
                continue
            if dt and tg.date() > dt.date():
                continue
            filtered.append(row)

        sort_mode = self.sort_var.get()
        if sort_mode == "Thời gian (Mới → Cũ)":
            filtered.sort(key=lambda r: r[3], reverse=True)
        elif sort_mode == "Thời gian (Cũ → Mới)":
            filtered.sort(key=lambda r: r[3])
        elif sort_mode == "Độ chính xác (Cao → Thấp)":
            filtered.sort(key=lambda r: r[2], reverse=True)
        elif sort_mode == "Độ chính xác (Thấp → Cao)":
            filtered.sort(key=lambda r: r[2])
        elif sort_mode == "Tên (A → Z)":
            filtered.sort(key=lambda r: r[1].lower())
        elif sort_mode == "Tên (Z → A)":
            filtered.sort(key=lambda r: r[1].lower(), reverse=True)

        self._hien_thi(filtered)

    # ────────────────────────────────────────────────────────────────
    #  Hiển thị bảng
    # ────────────────────────────────────────────────────────────────
    def _hien_thi(self, rows):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for i, (row_id, ten_sp, conf, tg) in enumerate(rows, 1):
            try:
                tg_str = tg.strftime("%H:%M %d/%m/%Y")
            except Exception:
                tg_str = str(tg)
            conf_pct = conf * 100.0 if conf <= 1.0 else conf
            conf_str = f"{conf_pct:.1f}%"
            tag = "odd" if i % 2 else "even"
            self.tree.insert("", "end", iid=str(row_id),
                             values=(i, ten_sp, tg_str, conf_str), tags=(tag,))
        self.lbl_status.config(
            text=f"Hiển thị {len(rows)} / {len(self._all_rows)} bản ghi",
            fg=THEME["fg_muted"])

    # ────────────────────────────────────────────────────────────────
    #  Xóa
    # ────────────────────────────────────────────────────────────────
    def _xoa_chon(self):
        from tkinter import messagebox
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo(
                "Chưa chọn bản ghi",
                "Vui lòng chọn ít nhất một bản ghi.\n"
                "  • Click đơn: chọn 1 hàng\n"
                "  • Ctrl+Click: thêm/bỏ từng hàng\n"
                "  • Shift+Click: chọn nhiều hàng liên tiếp",
                parent=self)
            return
        n = len(selected)
        if not messagebox.askyesno(
                "Xác nhận xóa",
                f"Xóa {n} bản ghi đã chọn?\nThao tác này không thể hoàn tác.",
                icon="warning", parent=self):
            return
        try:
            from db import get_conn
            conn = get_conn(); cursor = conn.cursor()
            ids = [int(iid) for iid in selected]
            cursor.executemany("DELETE FROM lich_su WHERE id = %s", [(i,) for i in ids])
            conn.commit(); cursor.close(); conn.close()
            self._all_rows = [r for r in self._all_rows if r[0] not in ids]
            self._ap_bo_loc()
            self.lbl_status.config(text=f"✓ Đã xóa {n} bản ghi", fg=THEME["green"])
        except Exception as ex:
            messagebox.showerror("Lỗi", str(ex), parent=self)

    def _xoa_tat_ca(self):
        from tkinter import messagebox
        if not messagebox.askyesno(
                "Cảnh báo",
                "Bạn có chắc muốn XÓA TOÀN BỘ lịch sử nhận diện?\n"
                "Hành động này không thể hoàn tác!",
                icon="warning", parent=self):
            return
        try:
            from db import get_conn
            conn = get_conn(); cursor = conn.cursor()
            cursor.execute("DELETE FROM lich_su")
            conn.commit(); cursor.close(); conn.close()
            self._all_rows = []
            self._hien_thi([])
            self.lbl_status.config(text="Đã xóa toàn bộ lịch sử.", fg=THEME["yellow"])
        except Exception as ex:
            messagebox.showerror("Lỗi", str(ex), parent=self)