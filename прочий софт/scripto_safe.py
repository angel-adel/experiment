import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import json
import os
import sys

DATA_FILE = "scripts_data.json"

class ScriptonizerSafe:
    def __init__(self, root):
        self.root = root
        self.root.title("Скриптонайзер")
        self.root.geometry("650x450")
        
        # Запрещаем изменять прозрачность и топ-окна
        self.root.attributes('-alpha', 1.0)
        self.root.attributes('-topmost', False)
        
        self.scripts = self.load_scripts()
        self.setup_ui()
    
    def setup_ui(self):
        # Панель поиска и добавления
        top_frame = tk.Frame(self.root)
        top_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(top_frame, text="🔍 Поиск:").pack(side=tk.LEFT, padx=5)
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(top_frame, textvariable=self.search_var, width=40)
        self.search_entry.pack(side=tk.LEFT, padx=5)
        self.search_entry.bind('<KeyRelease>', self.filter_scripts)
        
        tk.Button(top_frame, text="➕ Добавить скрипт", command=self.add_script,
                 bg="#4CAF50", fg="white").pack(side=tk.RIGHT, padx=5)
        
        # Область со скриптами
        self.canvas_frame = tk.Frame(self.root)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.canvas = tk.Canvas(self.canvas_frame)
        scrollbar = tk.Scrollbar(self.canvas_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas)
        
        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Нижняя панель с настройками
        bottom_frame = tk.Frame(self.root)
        bottom_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Button(bottom_frame, text="⚙️ Редактировать скрипты", command=self.open_editor,
                 bg="#2196F3", fg="white").pack(side=tk.LEFT, padx=5)
        tk.Button(bottom_frame, text="💾 Экспорт на рабочий стол", command=self.export_to_desktop,
                 bg="#FF9800", fg="white").pack(side=tk.LEFT, padx=5)
        tk.Button(bottom_frame, text="📂 Импорт", command=self.import_scripts,
                 bg="#9C27B0", fg="white").pack(side=tk.LEFT, padx=5)
        tk.Button(bottom_frame, text="❌ Выход", command=self.root.quit,
                 bg="#f44336", fg="white").pack(side=tk.RIGHT, padx=5)
        
        self.refresh_scripts()
    
    def refresh_scripts(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        for script in self.scripts:
            self.create_script_button(script)
    
    def create_script_button(self, script):
        name = script['name']
        color = script.get('color', '#f0f0f0')
        
        btn_frame = tk.Frame(self.scrollable_frame, bg=color, relief=tk.RAISED, bd=1)
        btn_frame.pack(fill=tk.X, pady=3, padx=5)
        
        btn = tk.Button(btn_frame, text=name, bg=color,
                       font=("Arial", 10),
                       anchor="w", justify=tk.LEFT,
                       command=lambda t=script['text']: self.copy_to_clipboard(t))
        btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=5)
        
        # Кнопка редактирования
        edit_btn = tk.Button(btn_frame, text="✏️", width=3,
                            command=lambda i=self.scripts.index(script): self.edit_script(i))
        edit_btn.pack(side=tk.RIGHT, padx=2, pady=2)
        
        # Кнопка удаления
        del_btn = tk.Button(btn_frame, text="🗑️", width=3, bg="#ffcccc",
                           command=lambda i=self.scripts.index(script): self.delete_script(i))
        del_btn.pack(side=tk.RIGHT, padx=2, pady=2)
    
    def filter_scripts(self, event=None):
        search_text = self.search_var.get().lower()
        
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        for script in self.scripts:
            if search_text in script['name'].lower() or search_text in script['text'].lower():
                self.create_script_button(script)
    
    def copy_to_clipboard(self, text):
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.root.update()
        messagebox.showinfo("Готово", "Текст скопирован в буфер обмена!\n\nНажмите Ctrl+V для вставки.")
    
    def add_script(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Добавить скрипт")
        dialog.geometry("500x450")
        dialog.transient(self.root)
        dialog.grab_set()
        
        tk.Label(dialog, text="Название скрипта:").pack(anchor=tk.W, padx=10, pady=(10,0))
        name_entry = tk.Entry(dialog, width=50)
        name_entry.pack(fill=tk.X, padx=10)
        
        tk.Label(dialog, text="Текст скрипта:").pack(anchor=tk.W, padx=10, pady=(10,0))
        text_area = tk.Text(dialog, height=15)
        text_area.pack(fill=tk.BOTH, expand=True, padx=10)
        
        tk.Label(dialog, text="Цвет фона:").pack(anchor=tk.W, padx=10, pady=(10,0))
        color_var = tk.StringVar(value="#f0f0f0")
        colors = ["#f0f0f0", "#ffcccc", "#ccffcc", "#ccccff", "#ffffcc", "#ffccff"]
        color_combo = ttk.Combobox(dialog, textvariable=color_var, values=colors, state="readonly")
        color_combo.pack(anchor=tk.W, padx=10)
        
        def save():
            name = name_entry.get().strip()
            text = text_area.get('1.0', tk.END).strip()
            if name and text:
                self.scripts.append({
                    "name": name,
                    "text": text,
                    "color": color_var.get()
                })
                self.save_scripts()
                self.refresh_scripts()
                dialog.destroy()
            else:
                messagebox.showwarning("Ошибка", "Заполните название и текст")
        
        tk.Button(dialog, text="Сохранить", command=save,
                 bg="#4CAF50", fg="white").pack(pady=10)
    
    def edit_script(self, index):
        script = self.scripts[index]
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Редактировать: {script['name']}")
        dialog.geometry("500x450")
        dialog.transient(self.root)
        dialog.grab_set()
        
        tk.Label(dialog, text="Название:").pack(anchor=tk.W, padx=10, pady=(10,0))
        name_entry = tk.Entry(dialog, width=50)
        name_entry.insert(0, script['name'])
        name_entry.pack(fill=tk.X, padx=10)
        
        tk.Label(dialog, text="Текст:").pack(anchor=tk.W, padx=10, pady=(10,0))
        text_area = tk.Text(dialog, height=15)
        text_area.insert('1.0', script['text'])
        text_area.pack(fill=tk.BOTH, expand=True, padx=10)
        
        tk.Label(dialog, text="Цвет фона:").pack(anchor=tk.W, padx=10, pady=(10,0))
        color_var = tk.StringVar(value=script.get('color', '#f0f0f0'))
        colors = ["#f0f0f0", "#ffcccc", "#ccffcc", "#ccccff", "#ffffcc", "#ffccff"]
        color_combo = ttk.Combobox(dialog, textvariable=color_var, values=colors, state="readonly")
        color_combo.pack(anchor=tk.W, padx=10)
        
        def save():
            self.scripts[index]['name'] = name_entry.get().strip()
            self.scripts[index]['text'] = text_area.get('1.0', tk.END).strip()
            self.scripts[index]['color'] = color_var.get()
            self.save_scripts()
            self.refresh_scripts()
            dialog.destroy()
        
        tk.Button(dialog, text="Сохранить", command=save,
                 bg="#4CAF50", fg="white").pack(pady=10)
    
    def delete_script(self, index):
        if messagebox.askyesno("Удаление", f"Удалить скрипт '{self.scripts[index]['name']}'?"):
            self.scripts.pop(index)
            self.save_scripts()
            self.refresh_scripts()
    
    def open_editor(self):
        if not self.scripts:
            messagebox.showinfo("Инфо", "Нет скриптов для редактирования")
            return
        self.refresh_scripts()
        messagebox.showinfo("Редактор", "Скрипты можно редактировать прямо на главном экране\n\n"
                                      "✏️ — редактировать\n"
                                      "🗑️ — удалить")
    
    def export_to_desktop(self):
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        path = os.path.join(desktop, "scripts_backup.json")
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.scripts, f, ensure_ascii=False, indent=2)
        messagebox.showinfo("Успех", f"Скрипты сохранены:\n{path}")
    
    def import_scripts(self):
        filepath = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if filepath:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    imported = json.load(f)
                self.scripts.extend(imported)
                self.save_scripts()
                self.refresh_scripts()
                messagebox.showinfo("Успех", f"Импортировано {len(imported)} скриптов")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось импортировать:\n{e}")
    
    def save_scripts(self):
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.scripts, f, ensure_ascii=False, indent=2)
    
    def load_scripts(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        return []

if __name__ == "__main__":
    root = tk.Tk()
    app = ScriptonizerSafe(root)
    root.mainloop()
