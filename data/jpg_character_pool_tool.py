import os
import re
import json
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk


class JPGCharacterPoolTool:
    """Generate CHARACTER_POOL entries for JPG/JPEG files without renaming them."""

    def __init__(self, root):
        self.root = root
        self.root.title("JPG Character Pool Generator")
        self.root.geometry("900x720")
        self.root.minsize(780, 620)

        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        self.folder_path = tk.StringVar()
        self.asset_folder_var = tk.StringVar(value="cards")
        self.prefix_var = tk.StringVar(value="VIP")
        self.start_id_var = tk.StringVar(value="1")
        self.rarity_var = tk.StringVar(value="VIP")
        self.element_var = tk.StringVar(value="Hỏa")
        self.power_var = tk.StringVar(value="1000")
        self.stamina_var = tk.StringVar(value="100")
        self.title_var = tk.StringVar(value="Liên Anime")
        self.lore_var = tk.StringVar(value="Con Trai Của Quỷ Vương")

        self.create_widgets()

    def create_widgets(self):
        main = ttk.Frame(self.root, padding=15)
        main.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            main,
            text="TẠO CHARACTER_POOL TỪ ẢNH JPG/JPEG",
            font=("Arial", 15, "bold"),
        ).pack(anchor=tk.W, pady=(0, 5))
        ttk.Label(
            main,
            text="Chỉ tạo dữ liệu và đường dẫn assets; không đổi tên, di chuyển hoặc xóa ảnh gốc.",
        ).pack(anchor=tk.W, pady=(0, 12))

        folder_frame = ttk.LabelFrame(main, text="1. Thư mục chứa ảnh JPG/JPEG trên máy", padding=10)
        folder_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Entry(folder_frame, textvariable=self.folder_path).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8)
        )
        ttk.Button(folder_frame, text="Chọn thư mục…", command=self.browse_folder).pack(side=tk.RIGHT)

        config = ttk.LabelFrame(main, text="2. Cấu hình thẻ và đường dẫn assets", padding=10)
        config.pack(fill=tk.X, pady=(0, 10))
        config.columnconfigure(1, weight=1)
        config.columnconfigure(3, weight=1)

        fields = [
            ("Tiền tố ID:", self.prefix_var, 0, 0),
            ("Số ID bắt đầu:", self.start_id_var, 0, 2),
            ("Rarity:", self.rarity_var, 1, 0),
            ("Element:", self.element_var, 1, 2),
            ("Power:", self.power_var, 2, 0),
            ("Stamina:", self.stamina_var, 2, 2),
            ("Title mặc định:", self.title_var, 3, 0),
            ("Lore mặc định:", self.lore_var, 3, 2),
        ]
        for label, var, row, col in fields:
            ttk.Label(config, text=label).grid(row=row, column=col, sticky=tk.W, padx=5, pady=5)
            ttk.Entry(config, textvariable=var, width=24).grid(
                row=row, column=col + 1, sticky="ew", padx=5, pady=5
            )

        ttk.Label(config, text="Thư mục trong assets/cards/:").grid(
            row=4, column=0, sticky=tk.W, padx=5, pady=5
        )
        ttk.Entry(config, textvariable=self.asset_folder_var).grid(
            row=4, column=1, columnspan=3, sticky="ew", padx=5, pady=5
        )
        ttk.Label(
            config,
            text="Ví dụ nhập: event1  →  assets/cards/event1/ten-anh.jpg",
            foreground="#555555",
        ).grid(row=5, column=0, columnspan=4, sticky=tk.W, padx=5, pady=(0, 3))

        buttons = ttk.Frame(main)
        buttons.pack(fill=tk.X, pady=(0, 10))
        ttk.Button(buttons, text="Tạo dữ liệu", command=self.generate_data).pack(
            side=tk.LEFT, ipadx=12, ipady=4
        )
        ttk.Button(buttons, text="Sao chép kết quả", command=self.copy_to_clipboard).pack(
            side=tk.LEFT, padx=8, ipadx=8, ipady=4
        )
        ttk.Button(buttons, text="Lưu thành file JS…", command=self.save_output).pack(
            side=tk.RIGHT, ipadx=8, ipady=4
        )

        output_frame = ttk.LabelFrame(main, text="3. Kết quả const CHARACTER_POOL", padding=10)
        output_frame.pack(fill=tk.BOTH, expand=True)
        self.output_text = scrolledtext.ScrolledText(
            output_frame, wrap=tk.NONE, font=("Consolas", 10), undo=True
        )
        self.output_text.pack(fill=tk.BOTH, expand=True)

    def browse_folder(self):
        selected = filedialog.askdirectory(title="Chọn thư mục chứa ảnh JPG/JPEG")
        if selected:
            self.folder_path.set(selected)

    @staticmethod
    def js_string(value):
        # JSON string quoting is compatible with ordinary JavaScript string literals.
        return json.dumps(str(value), ensure_ascii=False)

    def generate_data(self):
        folder = self.folder_path.get().strip()
        if not folder or not os.path.isdir(folder):
            messagebox.showerror("Lỗi", "Vui lòng chọn thư mục ảnh hợp lệ.")
            return

        prefix = self.prefix_var.get().strip()
        asset_folder = self.asset_folder_var.get().strip().replace("\\", "/").strip("/")
        if not prefix:
            messagebox.showerror("Lỗi", "Tiền tố ID không được để trống.")
            return
        if not asset_folder:
            messagebox.showerror("Lỗi", "Vui lòng nhập thư mục nằm sau assets/cards/.")
            return
        if any(part in (".", "..") for part in asset_folder.split("/")):
            messagebox.showerror("Lỗi", "Đường dẫn thư mục assets không được chứa . hoặc ..")
            return

        try:
            start_id = int(self.start_id_var.get())
            power = int(self.power_var.get())
            stamina = int(self.stamina_var.get())
        except ValueError:
            messagebox.showerror("Lỗi", "Số ID bắt đầu, Power và Stamina phải là số nguyên.")
            return

        try:
            filenames = sorted(
                name for name in os.listdir(folder)
                if os.path.isfile(os.path.join(folder, name))
                and os.path.splitext(name)[1].lower() in (".jpg", ".jpeg")
            )
        except OSError as exc:
            messagebox.showerror("Lỗi", f"Không thể đọc thư mục: {exc}")
            return

        if not filenames:
            messagebox.showwarning("Không có ảnh", "Không tìm thấy ảnh .jpg hoặc .jpeg trong thư mục.")
            return

        rarity = self.rarity_var.get().strip()
        element = self.element_var.get().strip()
        title = self.title_var.get().strip()
        lore = self.lore_var.get().strip()

        lines = ["const CHARACTER_POOL = ["]
        for index, filename in enumerate(filenames):
            card_id = f"{prefix}{start_id + index}"
            stem = os.path.splitext(filename)[0]
            media_url = f"assets/cards/{asset_folder}/{filename}".replace("\\", "/")
            item = {
                "id": card_id,
                "name": stem,
                "title": title,
                "rarity": rarity,
                "element": element,
                "power": power,
                "stamina": stamina,
                "mediaType": "image",
                "mediaExt": "jpg" if filename.lower().endswith(".jpg") else "jpeg",
                "mediaUrl": media_url,
                "lore": lore,
            }
            lines.append("  {")
            for key in ("id", "name", "title", "rarity", "element"):
                lines.append(f"    {key}: {self.js_string(item[key])},")
            lines.append(f"    power: {item['power']},")
            lines.append(f"    stamina: {item['stamina']},")
            for key in ("mediaType", "mediaExt", "mediaUrl"):
                lines.append(f"    {key}: {self.js_string(item[key])},")
            lines.append(f"    lore: {self.js_string(item['lore'])}")
            lines.append("  }" + ("," if index < len(filenames) - 1 else ""))

        lines.append("];")
        result = "\n".join(lines)
        self.output_text.delete("1.0", tk.END)
        self.output_text.insert(tk.END, result)
        messagebox.showinfo(
            "Hoàn thành",
            f"Đã tạo dữ liệu cho {len(filenames)} ảnh JPG/JPEG.\n"
            "Tên và vị trí các file ảnh gốc được giữ nguyên.",
        )

    def copy_to_clipboard(self):
        content = self.output_text.get("1.0", tk.END).strip()
        if not content:
            messagebox.showwarning("Chưa có dữ liệu", "Hãy tạo dữ liệu trước khi sao chép.")
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(content)
        self.root.update()
        messagebox.showinfo("Thành công", "Đã sao chép kết quả vào clipboard.")

    def save_output(self):
        content = self.output_text.get("1.0", tk.END).strip()
        if not content:
            messagebox.showwarning("Chưa có dữ liệu", "Hãy tạo dữ liệu trước khi lưu.")
            return
        path = filedialog.asksaveasfilename(
            title="Lưu dữ liệu JavaScript",
            defaultextension=".js",
            filetypes=[("JavaScript", "*.js"), ("Text", "*.txt"), ("All files", "*.*")],
            initialfile="character_pool.js",
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as file:
                file.write(content + "\n")
        except OSError as exc:
            messagebox.showerror("Lỗi", f"Không thể lưu file: {exc}")
            return
        messagebox.showinfo("Đã lưu", f"Đã lưu dữ liệu tại:\n{path}")


if __name__ == "__main__":
    root = tk.Tk()
    app = JPGCharacterPoolTool(root)
    root.mainloop()
