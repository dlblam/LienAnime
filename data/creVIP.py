import os
import re
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk

class CharacterPoolTool:
    def __init__(self, root):
        self.root = root
        self.root.title("Character Pool Generator & Renamer")
        self.root.geometry("850x680")
        self.root.minsize(750, 600)
        
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        self.folder_path = tk.StringVar()
        self.prefix_var = tk.StringVar(value="VIP")
        self.rarity_var = tk.StringVar(value="VIP")
        self.start_id_var = tk.IntVar(value=1)
        self.element_var = tk.StringVar(value="Hỏa")
        self.power_var = tk.IntVar(value=1000)
        self.stamina_var = tk.IntVar(value=100)
        self.title_var = tk.StringVar(value="Liên Anime")
        self.lore_var = tk.StringVar(value="Con Trai Của Quỷ Vương")
        self.rename_files_var = tk.BooleanVar(value=True)

        self.create_widgets()

    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)

        title_label = ttk.Label(main_frame, text="Tạo Dữ Liệu CHARACTER_POOL & Đổi Tên File Tự Động", font=("Arial", 14, "bold"))
        title_label.pack(anchor=tk.W, pady=(0, 10))

        # Folder Selection Frame
        folder_frame = ttk.LabelFrame(main_frame, text="1. Chọn Thư Mục Chứa Video/Ảnh", padding="10")
        folder_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Entry(folder_frame, textvariable=self.folder_path, width=70).pack(side=tk.LEFT, padx=(0, 5), expand=True, fill=tk.X)
        ttk.Button(folder_frame, text="Chọn Thư Mục...", command=self.browse_folder).pack(side=tk.RIGHT)

        # Config Frame
        config_frame = ttk.LabelFrame(main_frame, text="2. Cấu Hình Thuộc Tính Thẻ", padding="10")
        config_frame.pack(fill=tk.X, pady=(0, 10))

        config_frame.columnconfigure(1, weight=1)
        config_frame.columnconfigure(3, weight=1)

        ttk.Label(config_frame, text="Chữ cái ID (tiền tố):").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(config_frame, textvariable=self.prefix_var, width=15).grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)

        ttk.Label(config_frame, text="Số bắt đầu ID:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(config_frame, textvariable=self.start_id_var, width=15).grid(row=0, column=3, sticky=tk.W, padx=5, pady=5)

        ttk.Label(config_frame, text="Rarity:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(config_frame, textvariable=self.rarity_var, width=15).grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)

        ttk.Label(config_frame, text="Element:").grid(row=1, column=2, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(config_frame, textvariable=self.element_var, width=15).grid(row=1, column=3, sticky=tk.W, padx=5, pady=5)

        ttk.Label(config_frame, text="Power:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(config_frame, textvariable=self.power_var, width=15).grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)

        ttk.Label(config_frame, text="Stamina:").grid(row=2, column=2, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(config_frame, textvariable=self.stamina_var, width=15).grid(row=2, column=3, sticky=tk.W, padx=5, pady=5)

        ttk.Label(config_frame, text="Title mặc định:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(config_frame, textvariable=self.title_var, width=25).grid(row=3, column=1, sticky=tk.W, padx=5, pady=5)

        ttk.Label(config_frame, text="Lore mặc định:").grid(row=3, column=2, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(config_frame, textvariable=self.lore_var, width=25).grid(row=3, column=3, sticky=tk.W, padx=5, pady=5)

        ttk.Checkbutton(config_frame, text="Tự động đổi tên file trong thư mục thành ID tương ứng", variable=self.rename_files_var).grid(row=4, column=0, columnspan=4, sticky=tk.W, padx=5, pady=(10, 0))

        # Action Button
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Button(btn_frame, text="🚀 Tạo Dữ Liệu & Đổi Tên File", command=self.generate_data).pack(side=tk.LEFT, ipady=5, ipadx=10)
        ttk.Button(btn_frame, text="📋 Sao chép kết quả", command=self.copy_to_clipboard).pack(side=tk.RIGHT, ipady=5, ipadx=10)

        # Output Text Area
        output_frame = ttk.LabelFrame(main_frame, text="3. Kết Quả (const CHARACTER_POOL)", padding="10")
        output_frame.pack(fill=tk.BOTH, expand=True)

        self.output_text = scrolledtext.ScrolledText(output_frame, wrap=tk.WORD, font=("Consolas", 10))
        self.output_text.pack(fill=tk.BOTH, expand=True)

    def browse_folder(self):
        dir_selected = filedialog.askdirectory()
        if dir_selected:
            self.folder_path.set(dir_selected)

    def generate_data(self):
        folder = self.folder_path.get().strip()
        if not folder or not os.path.isdir(folder):
            messagebox.showerror("Lỗi", "Vui lòng chọn thư mục hợp lệ chứa file media!")
            return

        prefix = self.prefix_var.get().strip()
        try:
            start_id = int(self.start_id_var.get())
            power = int(self.power_var.get())
            stamina = int(self.stamina_var.get())
        except ValueError:
            messagebox.showerror("Lỗi", "Số bắt đầu ID, Power, Stamina phải là số nguyên!")
            return

        rarity = self.rarity_var.get().strip()
        element = self.element_var.get().strip()
        default_title = self.title_var.get().strip()
        default_lore = self.lore_var.get().strip()
        rename_files = self.rename_files_var.get()

        valid_extensions = ['.mp4', '.png', '.jpg', '.jpeg', '.webm', '.gif']
        
        try:
            files = sorted(os.listdir(folder))
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể đọc thư mục: {e}")
            return

        media_files = [f for f in files if os.path.isfile(os.path.join(folder, f)) and os.path.splitext(f)[1].lower() in valid_extensions]

        if not media_files:
            messagebox.showwarning("Cảnh báo", "Không tìm thấy file media hợp lệ trong thư mục đã chọn!")
            return

        pool_lines = ["const CHARACTER_POOL = ["]
        
        current_id_num = start_id
        renamed_count = 0
        file_actions = []

        for filename in media_files:
            old_path = os.path.join(folder, filename)
            ext_with_dot = os.path.splitext(filename)[1].lower()
            media_ext = ext_with_dot.lstrip('.')
            
            media_type = "video" if media_ext in ['mp4', 'webm', 'mov'] else "image"
            
            name_without_ext = os.path.splitext(filename)[0]
            clean_name = re.sub(r'(?i)mp4', '', name_without_ext).strip('-_ ')
            if not clean_name:
                clean_name = name_without_ext

            card_id = f"{prefix}{current_id_num}"

            folder_name_last = os.path.basename(os.path.normpath(folder))
            media_url = f"assets/cards/{folder_name_last}/{card_id}.{media_ext}"

            item_dict = {
                "id": card_id,
                "name": clean_name,
                "title": default_title,
                "rarity": rarity,
                "element": element,
                "power": power,
                "stamina": stamina,
                "mediaType": media_type,
                "mediaExt": media_ext,
                "mediaUrl": media_url,
                "lore": default_lore
            }

            new_filename = f"{card_id}.{media_ext}"
            new_path = os.path.join(folder, new_filename)

            file_actions.append((old_path, new_path, item_dict))
            current_id_num += 1

        for old_path, new_path, item in file_actions:
            if rename_files and old_path != new_path:
                try:
                    if os.path.exists(new_path) and old_path.lower() != new_path.lower():
                        os.remove(new_path)
                    os.rename(old_path, new_path)
                    renamed_count += 1
                except Exception as e:
                    print(f"Error renaming {old_path} to {new_path}: {e}")

            obj_str = "  {\n"
            obj_str += f'    id: "{item["id"]}",\n'
            obj_str += f'    name: "{item["name"]}",\n'
            obj_str += f'    title: "{item["title"]}",\n'
            obj_str += f'    rarity: "{item["rarity"]}",\n'
            obj_str += f'    element: "{item["element"]}",\n'
            obj_str += f'    power: {item["power"]},\n'
            obj_str += f'    stamina: {item["stamina"]},\n'
            obj_str += f'    mediaType: "{item["mediaType"]}",\n'
            obj_str += f'    mediaExt: "{item["mediaExt"]}",\n'
            obj_str += f'    mediaUrl: "{item["mediaUrl"]}",\n'
            obj_str += f'    lore: "{item["lore"]}"\n'
            obj_str += "  },"
            pool_lines.append(obj_str)

        pool_lines.append("];")
        final_result = "\n".join(pool_lines)

        self.output_text.delete("1.0", tk.END)
        self.output_text.insert(tk.END, final_result)

        msg = f"Đã xử lý thành công {len(file_actions)} file!"
        if rename_files:
            msg += f" Đã đổi tên {renamed_count} file thành công."
        messagebox.showinfo("Hoàn thành", msg)

    def copy_to_clipboard(self):
        text_content = self.output_text.get("1.0", tk.END).strip()
        if not text_content:
            messagebox.showwarning("Cảnh báo", "Không có nội dung để sao chép!")
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(text_content)
        messagebox.showinfo("Thành công", "Đã sao chép chuỗi dữ liệu vào clipboard!")

if __name__ == "__main__":
    root = tk.Tk()
    app = CharacterPoolTool(root)
    root.mainloop()