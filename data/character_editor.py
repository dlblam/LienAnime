# -*- coding: utf-8 -*-
"""
Character JS Editor
- Opens a JavaScript file containing an array of character objects.
- Search by character ID, edit the existing values, and save back to the same file.
- Keeps unrelated code and character records intact.
"""
import re
import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path

FIELDS = [
    ("name", "Tên nhân vật", "text"),
    ("title", "Anime / Tác phẩm", "text"),
    ("rarity", "Bậc thẻ (rarity)", "text"),
    ("element", "Thuộc tính (element)", "text"),
    ("power", "Power", "number"),
    ("stamina", "Stamina", "number"),
    ("mediaType", "Loại media", "text"),
    ("mediaExt", "Đuôi tệp", "text"),
    ("mediaUrl", "Đường dẫn ảnh / media", "text"),
    ("lore", "Lore / Câu nói", "multiline"),
]

def decode_js_string(raw):
    """Decode a double-quoted JS string using JSON-compatible escapes."""
    try:
        return json.loads(raw)
    except Exception:
        return raw[1:-1]

def encode_js_string(value):
    return json.dumps(value, ensure_ascii=False)

def find_object_spans(source):
    """Find top-level-ish { ... } object spans while respecting strings/comments."""
    spans = []
    depth = 0
    start = None
    i = 0
    quote = None
    escape = False
    line_comment = False
    block_comment = False
    while i < len(source):
        c = source[i]
        n = source[i+1] if i + 1 < len(source) else ""
        if line_comment:
            if c == "\n":
                line_comment = False
            i += 1
            continue
        if block_comment:
            if c == "*" and n == "/":
                block_comment = False
                i += 2
            else:
                i += 1
            continue
        if quote:
            if escape:
                escape = False
            elif c == "\\":
                escape = True
            elif c == quote:
                quote = None
            i += 1
            continue
        if c == "/" and n == "/":
            line_comment = True
            i += 2
            continue
        if c == "/" and n == "*":
            block_comment = True
            i += 2
            continue
        if c in ("'", '"', "`"):
            quote = c
            i += 1
            continue
        if c == "{":
            if depth == 0:
                start = i
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0 and start is not None:
                spans.append((start, i + 1))
                start = None
        i += 1
    return spans

def read_field(obj, key):
    # Strings use double quotes in the supplied file; also accept single quotes.
    pat = re.compile(r'(?m)(?<![\w$])' + re.escape(key) + r'\s*:\s*("(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|-?\d+(?:\.\d+)?|true|false|null)')
    m = pat.search(obj)
    if not m:
        return None
    token = m.group(1)
    if token.startswith('"'):
        return decode_js_string(token)
    if token.startswith("'"):
        # Simple conversion for single-quoted JS strings.
        body = token[1:-1].replace("\\'", "'").replace('\\\\', '\\')
        return body
    if token == "true":
        return True
    if token == "false":
        return False
    if token == "null":
        return None
    try:
        return int(token) if "." not in token else float(token)
    except ValueError:
        return token

def replace_field(obj, key, value, kind):
    pat = re.compile(r'(?m)(?<![\w$])(' + re.escape(key) + r'\s*:\s*)("(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|-?\d+(?:\.\d+)?|true|false|null)')
    if kind == "number":
        try:
            number = float(value.strip())
            replacement = str(int(number)) if number.is_integer() else str(number)
        except Exception:
            raise ValueError(f"Trường {key} phải là số.")
    else:
        replacement = encode_js_string(value)
    if pat.search(obj):
        return pat.sub(lambda m: m.group(1) + replacement, obj, count=1)
    # Add missing property immediately before closing brace.
    before = obj.rstrip()
    comma = "" if before.endswith("{") else ","
    indent_match = re.search(r"\n(\s*)\S", obj)
    indent = indent_match.group(1) if indent_match else "    "
    return before[:-1] + f'{comma}\n{indent}{key}: {replacement}\n' + before[-1] + obj[len(before):]

class CharacterEditor(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Character JS Editor")
        self.geometry("900x760")
        self.minsize(760, 620)
        self.path = None
        self.source = ""
        self.current_span = None
        self.current_id = None
        self.widgets = {}
        self._build_ui()
        self.set_status("Mở tệp JavaScript để bắt đầu.")

    def _build_ui(self):
        self.configure(bg="#101827")
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("TFrame", background="#101827")
        style.configure("TLabel", background="#101827", foreground="#e8eef8", font=("Segoe UI", 10))
        style.configure("Header.TLabel", font=("Segoe UI", 17, "bold"), foreground="#ffffff")
        style.configure("Hint.TLabel", foreground="#aab8cc")
        style.configure("TButton", font=("Segoe UI", 10), padding=(10, 7))
        style.configure("TEntry", padding=6)
        style.configure("TCombobox", padding=6)

        outer = ttk.Frame(self, padding=18)
        outer.pack(fill="both", expand=True)
        ttk.Label(outer, text="CHARACTER JS EDITOR", style="Header.TLabel").pack(anchor="w")
        ttk.Label(outer, text="Nhập ID để tải dữ liệu hiện tại, chỉnh sửa rồi lưu trực tiếp vào tệp JS.", style="Hint.TLabel").pack(anchor="w", pady=(3, 14))

        file_row = ttk.Frame(outer)
        file_row.pack(fill="x", pady=(0, 12))
        self.file_label = ttk.Label(file_row, text="Chưa chọn tệp", style="Hint.TLabel")
        self.file_label.pack(side="left", fill="x", expand=True)
        ttk.Button(file_row, text="📂 Chọn tệp JS", command=self.choose_file).pack(side="right")
        ttk.Button(file_row, text="Mở charactersSSS.js", command=self.open_default).pack(side="right", padx=(0, 8))

        search = ttk.Frame(outer)
        search.pack(fill="x", pady=(0, 12))
        ttk.Label(search, text="ID nhân vật:", width=14).pack(side="left")
        self.id_var = tk.StringVar()
        self.id_entry = ttk.Entry(search, textvariable=self.id_var, width=22)
        self.id_entry.pack(side="left", padx=(0, 8))
        self.id_entry.bind("<Return>", lambda _e: self.load_character())
        ttk.Button(search, text="Tải dữ liệu theo ID", command=self.load_character).pack(side="left")
        ttk.Button(search, text="Danh sách ID", command=self.show_ids).pack(side="left", padx=(8, 0))

        name_search = ttk.Frame(outer)
        name_search.pack(fill="x", pady=(0, 12))
        ttk.Label(name_search, text="Tên nhân vật:", width=14).pack(side="left")
        self.name_var = tk.StringVar()
        self.name_entry = ttk.Entry(name_search, textvariable=self.name_var)
        self.name_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.name_entry.bind("<Return>", lambda _e: self.search_by_name())
        ttk.Button(name_search, text="Tìm tên", command=self.search_by_name).pack(side="left")
        ttk.Label(name_search, text="Có thể tìm một phần tên", style="Hint.TLabel").pack(side="left", padx=(8, 0))

        self.form = ttk.Frame(outer)
        self.form.pack(fill="both", expand=True)
        self.form.columnconfigure(1, weight=1)
        for row, (key, label, kind) in enumerate(FIELDS):
            ttk.Label(self.form, text=label).grid(row=row, column=0, sticky="nw", padx=(0, 14), pady=6)
            if kind == "multiline":
                widget = tk.Text(self.form, height=5, wrap="word", font=("Segoe UI", 10),
                                 bg="#182438", fg="#f3f6fb", insertbackground="white",
                                 relief="flat", padx=8, pady=7, undo=True)
                widget.grid(row=row, column=1, sticky="nsew", pady=6)
                self.form.rowconfigure(row, weight=1)
            else:
                widget = ttk.Entry(self.form)
                widget.grid(row=row, column=1, sticky="ew", pady=6)
            self.widgets[key] = widget

        buttons = ttk.Frame(outer)
        buttons.pack(fill="x", pady=(14, 8))
        ttk.Button(buttons, text="Lưu thay đổi vào tệp", command=self.save_character).pack(side="left")
        ttk.Button(buttons, text="Hoàn tác / tải lại ID", command=self.load_character).pack(side="left", padx=8)
        ttk.Button(buttons, text="Xóa trắng biểu mẫu", command=self.clear_form).pack(side="left")
        self.status = ttk.Label(outer, text="", style="Hint.TLabel")
        self.status.pack(anchor="w", pady=(6, 0))

    def set_status(self, text):
        self.status.configure(text=text)

    def choose_file(self):
        filename = filedialog.askopenfilename(
            title="Chọn tệp JavaScript chứa dữ liệu nhân vật",
            filetypes=[("JavaScript", "*.js"), ("Tất cả tệp", "*.*")]
        )
        if filename:
            self.open_file(Path(filename))

    def open_default(self):
        candidates = [Path.cwd() / "charactersSSS.js", Path(__file__).resolve().parent / "charactersSSS.js"]
        for candidate in candidates:
            if candidate.exists():
                self.open_file(candidate)
                return
        self.choose_file()

    def open_file(self, path):
        try:
            source = path.read_text(encoding="utf-8-sig")
        except Exception as exc:
            messagebox.showerror("Không mở được tệp", str(exc))
            return
        spans = find_object_spans(source)
        if not spans:
            messagebox.showerror("Không tìm thấy dữ liệu", "Không tìm thấy các object { ... } trong tệp.")
            return
        self.path = path
        self.source = source
        self.spans = spans
        self.file_label.configure(text=str(path))
        self.set_status(f"Đã mở tệp • {len(spans)} object được quét.")
        self.load_character()

    def get_object(self, character_id):
        for start, end in self.spans:
            obj = self.source[start:end]
            if str(read_field(obj, "id")) == character_id:
                return (start, end, obj)
        return None

    def load_character(self):
        if not self.path:
            self.set_status("Hãy chọn tệp JS trước.")
            return
        character_id = self.id_var.get().strip()
        if not character_id:
            self.set_status("Nhập ID, ví dụ SSS1.")
            return
        found = self.get_object(character_id)
        if not found:
            self.current_span = None
            self.current_id = None
            messagebox.showwarning("Không tìm thấy ID", f"Không có nhân vật mang ID: {character_id}")
            self.set_status(f"Không tìm thấy ID {character_id}.")
            return
        start, end, obj = found
        self.current_span = (start, end)
        self.current_id = character_id
        for key, _label, kind in FIELDS:
            value = read_field(obj, key)
            widget = self.widgets[key]
            if kind == "multiline":
                widget.delete("1.0", "end")
                widget.insert("1.0", "" if value is None else str(value))
            else:
                widget.delete(0, "end")
                widget.insert(0, "" if value is None else str(value))
        name = read_field(obj, "name") or "(chưa có tên)"
        self.set_status(f"Đã tải {character_id} — {name}. Chỉnh sửa xong hãy bấm Lưu.")

    def clear_form(self):
        for _key, _label, kind in FIELDS:
            widget = self.widgets[_key]
            if kind == "multiline":
                widget.delete("1.0", "end")
            else:
                widget.delete(0, "end")
        self.set_status("Đã xóa nội dung trên biểu mẫu; tệp chưa bị thay đổi.")

    def get_widget_value(self, key, kind):
        widget = self.widgets[key]
        if kind == "multiline":
            return widget.get("1.0", "end-1c")
        return widget.get().strip()

    def save_character(self):
        if not self.path or not self.current_id or not self.current_span:
            messagebox.showwarning("Chưa có nhân vật", "Hãy mở tệp và tải một nhân vật bằng ID trước.")
            return
        start, end = self.current_span
        obj = self.source[start:end]
        try:
            for key, _label, kind in FIELDS:
                value = self.get_widget_value(key, kind)
                obj = replace_field(obj, key, value, kind)
        except ValueError as exc:
            messagebox.showerror("Dữ liệu không hợp lệ", str(exc))
            return
        if str(read_field(obj, "id")) != self.current_id:
            messagebox.showerror("Lỗi an toàn", "ID của nhân vật bị thay đổi ngoài dự kiến. Không lưu.")
            return
        new_source = self.source[:start] + obj + self.source[end:]
        if not messagebox.askyesno("Xác nhận lưu", f"Lưu thay đổi của {self.current_id} vào:\n{self.path}\n\nNên tạo bản sao lưu trước khi chỉnh sửa lần đầu. Tiếp tục?"):
            return
        try:
            # Create a one-time backup alongside the source file.
            backup = self.path.with_suffix(self.path.suffix + ".bak")
            if not backup.exists():
                backup.write_text(self.source, encoding="utf-8")
            self.path.write_text(new_source, encoding="utf-8")
        except Exception as exc:
            messagebox.showerror("Lưu thất bại", str(exc))
            return
        self.source = new_source
        self.spans = find_object_spans(self.source)
        found = self.get_object(self.current_id)
        if found:
            self.current_span = (found[0], found[1])
        self.set_status(f"Đã lưu thành công {self.current_id}. Bản sao lưu: {self.path.name}.bak")
        messagebox.showinfo("Đã lưu", f"Đã cập nhật nhân vật {self.current_id}.\nTệp: {self.path}")

    def search_by_name(self):
        if not self.path:
            messagebox.showinfo("Chưa mở tệp", "Hãy mở tệp JS trước.")
            return
        query = self.name_var.get().strip()
        if not query:
            messagebox.showinfo("Thiếu tên", "Nhập tên nhân vật hoặc một phần tên để tìm.")
            return
        query_fold = query.casefold()
        matches = []
        for start, end in self.spans:
            obj = self.source[start:end]
            name = read_field(obj, "name")
            character_id = read_field(obj, "id")
            if name is not None and query_fold in str(name).strip().casefold():
                matches.append({
                    "id": str(character_id or ""),
                    "name": str(name).strip(),
                    "title": str(read_field(obj, "title") or ""),
                    "start": start,
                    "end": end,
                })
        if not matches:
            messagebox.showinfo("Không tìm thấy", f"Không tìm thấy nhân vật có tên chứa: {query}")
            self.set_status(f"Không tìm thấy tên phù hợp với “{query}”.")
            return
        if len(matches) == 1:
            self.id_var.set(matches[0]["id"])
            self.load_character()
            self.set_status(f"Tìm thấy duy nhất: {matches[0]['name']} ({matches[0]['id']}).")
            return
        # Duplicate/partial-name matches: let the user choose the exact ID.
        win = tk.Toplevel(self)
        win.title("Chọn nhân vật / ID")
        win.geometry("620x420")
        win.transient(self)
        win.grab_set()
        ttk.Label(
            win,
            text=f"Tìm thấy {len(matches)} nhân vật khớp với “{query}”. Chọn đúng nhân vật để tải dữ liệu:",
            padding=12,
            wraplength=580
        ).pack(anchor="w")
        frame = ttk.Frame(win, padding=(12, 0, 12, 12))
        frame.pack(fill="both", expand=True)
        columns = ("id", "name", "title")
        tree = ttk.Treeview(frame, columns=columns, show="headings", selectmode="browse")
        tree.heading("id", text="ID đề xuất")
        tree.heading("name", text="Tên nhân vật")
        tree.heading("title", text="Anime / Tác phẩm")
        tree.column("id", width=100, stretch=False)
        tree.column("name", width=190)
        tree.column("title", width=260)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        for index, item in enumerate(matches):
            tree.insert("", "end", iid=str(index), values=(item["id"], item["name"], item["title"]))
        if matches:
            tree.selection_set("0")
            tree.focus("0")
        ttk.Label(win, text="ID được đề xuất dựa trên dữ liệu trong tệp; hãy chọn đúng dòng.", padding=(12, 0, 12, 8), style="Hint.TLabel").pack(anchor="w")
        buttons = ttk.Frame(win, padding=(12, 0, 12, 12))
        buttons.pack(fill="x")
        def choose_match(_event=None):
            selected = tree.selection()
            if not selected:
                messagebox.showwarning("Chưa chọn", "Hãy chọn một nhân vật trong danh sách.", parent=win)
                return
            item = matches[int(selected[0])]
            self.id_var.set(item["id"])
            self.load_character()
            win.destroy()
        ttk.Button(buttons, text="Tải nhân vật đã chọn", command=choose_match).pack(side="right")
        ttk.Button(buttons, text="Hủy", command=win.destroy).pack(side="right", padx=(0, 8))
        tree.bind("<Double-Button-1>", choose_match)
        self.set_status(f"Có {len(matches)} kết quả. Chọn ID chính xác trong danh sách.")

    def show_ids(self):
        if not self.path:
            messagebox.showinfo("Danh sách ID", "Hãy mở tệp JS trước.")
            return
        ids = []
        for start, end in self.spans:
            value = read_field(self.source[start:end], "id")
            if value is not None:
                ids.append(str(value))
        win = tk.Toplevel(self)
        win.title("Danh sách ID nhân vật")
        win.geometry("360x500")
        ttk.Label(win, text=f"Tìm thấy {len(ids)} ID — nhấp đúp để tải", padding=10).pack(anchor="w")
        frame = ttk.Frame(win, padding=(10, 0, 10, 10))
        frame.pack(fill="both", expand=True)
        listing = tk.Listbox(frame, font=("Consolas", 11), bg="#182438", fg="#f3f6fb",
                             selectbackground="#315b91", relief="flat")
        scroll = ttk.Scrollbar(frame, orient="vertical", command=listing.yview)
        listing.configure(yscrollcommand=scroll.set)
        listing.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        for item in ids:
            listing.insert("end", item)
        def choose(_event=None):
            selection = listing.curselection()
            if selection:
                self.id_var.set(listing.get(selection[0]))
                self.load_character()
                win.destroy()
        listing.bind("<Double-Button-1>", choose)

if __name__ == "__main__":
    app = CharacterEditor()
    app.mainloop()
