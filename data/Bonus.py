import os
import re
import tkinter as tk
from tkinter import filedialog, messagebox


class PlaceholderEntry(tk.Entry):

  def __init__(self, master=None, placeholder="", *args, **kwargs):
    super().__init__(master, *args, **kwargs)
    self.placeholder = placeholder
    self.placeholder_color = "grey"
    self.default_fg_color = self["fg"] if self["fg"] else "black"

    self.bind("<FocusIn>", self._clear_placeholder)
    self.bind("<FocusOut>", self._add_placeholder)

    self._add_placeholder()

  def _clear_placeholder(self, e):
    if self.get() == self.placeholder:
      self.delete(0, tk.END)
      self.config(fg=self.default_fg_color)

  def _add_placeholder(self, e=None):
    if not self.get():
      self.insert(0, self.placeholder)
      self.config(fg=self.placeholder_color)

  def get_value(self):
    val = super().get()
    if val == self.placeholder:
      return ""
    return val


class CharacterToolApp:

  def __init__(self, root):
    self.root = root
    self.root.title(
        "Tool Thêm Nhân Vật JS (Auto ID & MediaUrl Manager)[cite: 1]"
    )
    self.root.geometry("650x750")

    self.file_path = ""
    self.fields_data = {}
    self.entries = {}
    self.characters_list = []  # Lưu toàn bộ danh sách nhân vật đã parse

    # --- Phần chọn file ---
    top_frame = tk.Frame(root, padx=10, pady=10)
    top_frame.pack(fill=tk.X)

    self.btn_select = tk.Button(
        top_frame,
        text="Chọn File JS",
        command=self.select_file,
        bg="#4CAF50",
        fg="white",
        font=("Arial", 10, "bold"),
    )
    self.btn_select.pack(side=tk.LEFT, padx=5)

    self.lbl_file = tk.Label(
        top_frame, text="Chưa chọn file nào", fg="gray", anchor="w"
    )
    self.lbl_file.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

    # --- Phần Form nhập thông số (Scrollable Canvas) ---
    self.container = tk.Frame(root)
    self.container.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

    self.canvas = tk.Canvas(self.container)
    self.scrollbar = tk.Scrollbar(
        self.container, orient="vertical", command=self.canvas.yview
    )
    self.form_frame = tk.Frame(self.canvas)

    self.form_frame.bind(
        "<Configure>",
        lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
    )
    self.canvas.create_window((0, 0), window=self.form_frame, anchor="nw")
    self.canvas.configure(yscrollcommand=self.scrollbar.set)

    self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # --- Phần nút bấm lưu ---
    bottom_frame = tk.Frame(root, padx=10, pady=10)
    bottom_frame.pack(fill=tk.X)

    self.btn_save = tk.Button(
        bottom_frame,
        text="Thêm Nhân Vật Vào File",
        command=self.save_character,
        bg="#2196F3",
        fg="white",
        font=("Arial", 11, "bold"),
        state=tk.DISABLED,
    )
    self.btn_save.pack(fill=tk.X, padx=5)

  def select_file(self):
    file_path = filedialog.askopenfilename(
        title="Chọn file JavaScript", filetypes=[("JavaScript Files", "*.js")]
    )
    if file_path:
      self.file_path = file_path
      self.lbl_file.config(text=os.path.basename(file_path), fg="black")
      self.parse_js_file()

  def parse_js_file(self):
    try:
      with open(self.file_path, "r", encoding="utf-8") as f:
        content = f.read()

      # Tìm tất cả các đối tượng nhân vật trong file JS để lấy nhân vật cuối và nhân vật đầu
      matches = list(re.finditer(r"\{\s*([^}]+)\s*\}", content))
      if not matches:
        messagebox.showerror(
            "Lỗi",
            "Không tìm thấy cấu trúc nhân vật mẫu nào trong file JS này!",
        )
        return

      # Lấy đối tượng đầu tiên để làm mẫu các trường (keys)
      first_obj_str = matches[0].group(1)
      pattern = re.compile(
          r"([a-zA-Z0-9_]+)\s*:\s*(?:\"([^\"]*)\"|'([^']*)'|([0-9.]+))"
      )
      self.fields_data = {}
      for m in pattern.finditer(first_obj_str):
        key = m.group(1)
        val = (
            m.group(2)
            if m.group(2) is not None
            else (m.group(3) if m.group(3) is not None else m.group(4))
        )
        self.fields_data[key] = val

      # Lấy đối tượng cuối cùng để tính toán ID tự động tiếp theo
      last_obj_str = matches[-1].group(1)
      last_id_match = re.search(r"id\s*:\s*[\"']([^\"']+)[\"']", last_obj_str)
      next_id_suggestion = ""
      if last_id_match:
        last_id = last_id_match.group(1)
        # Tách chữ và số của ID (Ví dụ: VIP65 -> prefix: VIP, num: 65)
        num_match = re.search(r"(\d+)$", last_id)
        if num_match:
          prefix = last_id[: num_match.start()]
          number = int(num_match.group(1))
          next_id_suggestion = f"{prefix}{number + 1}"
        else:
          next_id_suggestion = last_id + "_new"
      else:
        next_id_suggestion = "ID1"

      # Cập nhật gợi ý cho ID nếu trường id tồn tại
      if "id" in self.fields_data:
        self.fields_data["id"] = next_id_suggestion

      self.build_form()
      self.btn_save.config(state=tk.NORMAL)
    except Exception as e:
      messagebox.showerror("Lỗi", f"Không thể đọc file: {str(e)}")

  def build_form(self):
    for widget in self.form_frame.winfo_children():
      widget.destroy()
    self.entries.clear()

    tk.Label(
        self.form_frame,
        text=(
            "Nhập thông tin nhân vật mới (ID tự động tăng, mediaUrl tự động"
            " theo rarity):"
        ),
        font=("Arial", 10, "italic"),
        fg="#555",
    ).pack(anchor="w", pady=5)

    for key, default_val in self.fields_data.items():
      row_frame = tk.Frame(self.form_frame, pady=3)
      row_frame.pack(fill=tk.X, anchor="w")

      lbl = tk.Label(row_frame, text=f"{key}:", width=15, anchor="w")
      lbl.pack(side=tk.LEFT)

      # Nếu là trường mediaUrl, thiết kế đặc biệt để tự động cập nhật dựa vào rarity và tên file người dùng nhập
      if key == "mediaUrl":
        sub_frame = tk.Frame(row_frame)
        sub_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Ô nhập tên tệp media do người dùng tự gõ (ví dụ: VIP66.mp4 hoặc char.jpg)
        file_entry = PlaceholderEntry(
            sub_frame, placeholder="Ví dụ: VIP66.mp4", width=25
        )
        file_entry.pack(side=tk.LEFT, padx=(0, 5))

        # Label hiển thị kết quả động của mediaUrl
        url_preview_lbl = tk.Label(
            sub_frame, text=f"Gợi ý: {default_val}", fg="blue", anchor="w"
        )
        url_preview_lbl.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.entries[key] = {
            "type": "mediaUrl",
            "file_entry": file_entry,
            "preview_lbl": url_preview_lbl,
            "default": default_val,
        }

        # Bind sự kiện để cập nhật preview khi rarity thay đổi hoặc tên file thay đổi
        file_entry.bind(
            "<KeyRelease>", lambda e: self.update_media_url_preview()
        )
      else:
        entry = PlaceholderEntry(
            row_frame, placeholder=str(default_val), width=50
        )
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.entries[key] = entry
        # Nếu là trường rarity, theo dõi để cập nhật mediaUrl động
        if key == "rarity":
          entry.bind("<KeyRelease>", lambda e: self.update_media_url_preview())

  def update_media_url_preview(self):
    # Lấy giá trị rarity hiện tại (hoặc placeholder nếu trống)
    rarity_widget = self.entries.get("rarity")
    rarity_val = ""
    if rarity_widget and not isinstance(rarity_widget, dict):
      rarity_val = rarity_widget.get_value()
      if not rarity_val:
        rarity_val = rarity_widget.placeholder

    media_dict = self.entries.get("mediaUrl")
    if media_dict and isinstance(media_dict, dict):
      file_val = media_dict["file_entry"].get_value()
      if not file_val:
        file_val = "filename.mp4"  # Tên file mặc định tạm thời

      if rarity_val:
        dynamic_url = f"assets/cards/{rarity_val}/{file_val}"
      else:
        dynamic_url = f"assets/cards/VIP/{file_val}"

      media_dict["preview_lbl"].config(text=f"Gợi ý: {dynamic_url}")

  def save_character(self):
    if not self.file_path:
      return

    new_char = {}
    for key, widget in self.entries.items():
      if key == "mediaUrl":
        # Xử lý riêng cho mediaUrl ghép từ rarity và tên file người dùng nhập
        file_val = widget["file_entry"].get_value()
        if not file_val:
          file_val = widget["file_entry"].placeholder

        rarity_widget = self.entries.get("rarity")
        rarity_val = ""
        if rarity_widget and not isinstance(rarity_widget, dict):
          rarity_val = rarity_widget.get_value()
          if not rarity_val:
            rarity_val = rarity_widget.placeholder

        if not rarity_val:
          rarity_val = "VIP"

        new_char[key] = f"assets/cards/{rarity_val}/{file_val}"
      else:
        val = widget.get_value()
        if not val:
          val = widget.placeholder
        new_char[key] = val

    try:
      with open(self.file_path, "r", encoding="utf-8") as f:
        content = f.read()

      # Định dạng đối tượng mới theo chuẩn JavaScript
      obj_lines = ["  {"]
      for k, v in new_char.items():
        if v.isdigit() or (
            v.replace(".", "", 1).isdigit() and v.count(".") < 2
        ):
          obj_lines.append(f"    {k}: {v},")
        else:
          obj_lines.append(f'    {k}: "{v}",')
      obj_lines.append("  },")
      new_obj_str = "\n".join(obj_lines)

      # Chèn trước dấu đóng mảng cuối cùng '];'
      last_bracket_idx = content.rfind("]")
      if last_bracket_idx != -1:
        updated_content = (
            content[:last_bracket_idx]
            + new_obj_str
            + "\n"
            + content[last_bracket_idx:]
        )
        with open(self.file_path, "w", encoding="utf-8") as f:
          f.write(updated_content)
        messagebox.showinfo(
            "Thành công", "Đã thêm nhân vật mới vào file JS thành công![cite: 1]"
        )
        # Tải lại file để tự động cập nhật ID tiếp theo cho lần nhập kế tiếp
        self.parse_js_file()
      else:
        messagebox.showerror(
            "Lỗi", "Không tìm thấy dấu đóng mảng ']' trong file JS."
        )
    except Exception as e:
      messagebox.showerror("Lỗi khi ghi file", str(e))


if __name__ == "__main__":
  root = tk.Tk()
  app = CharacterToolApp(root)
  root.mainloop()