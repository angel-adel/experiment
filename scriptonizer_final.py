import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import json
import os
import pyautogui
import time

# --- КОНФИГУРАЦИЯ ---
DATA_FILE = "scripts_data.json"

class ScriptonizerLite:
    def __init__(self, root):
        self.root = root
        self.root.title("Скриптонайзер Lite")
        self.root.geometry("700x500")
        
        self.scripts = self.load_scripts()
        self.mini_mode = False
        self.mini_window = None
        self.hidden_mode = False
        
        self.setup_ui()
    
    def setup_ui(self):
        # Верхняя панель с кнопками
        top_frame = tk.Frame(self.root, bg="#f0f0f0")
        top_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 1. Настройки (сведения)
        tk.Button(top_frame, text="⚙️", width=4, height=2, 
                 command=self.show_about).pack(side=tk.LEFT, padx=2)
        
        # 2. Скрыть (полупрозрачность)
        tk.Button(top_frame, text="👁️", width=4, height=2, 
                 command=self.toggle_hide).pack(side=tk.LEFT, padx=2)
        
        # 3. Свернуть в мини-кнопку
        tk.Button(top_frame, text="➖", width=4, height=2, 
                 command=self.minimize_to_button).pack(side=tk.LEFT, padx=2)
        
        # 4. Редактор скриптов
        tk.Button(top_frame, text="📝", width=4, height=2, 
                 command=self.open_editor).pack(side=tk.LEFT, padx=2)
        
        # 5. Поиск (кнопка + поле)
        tk.Button(top_frame, text="🔍", width=3, height=2, 
                 command=self.focus_search).pack(side=tk.LEFT, padx=5)
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(top_frame, textvariable=self.search_var, width=25)
        self.search_entry.pack(side=tk.LEFT, padx=5)
        self.search_entry.bind('<KeyRelease>', self.filter_scripts)
        
        # 6. Добавить скрипт
        tk.Button(top_frame, text="➕", width=4, height=2, 
                 bg="#4CAF50", fg="white", command=self.add_script).pack(side=tk.RIGHT, padx=2)
        
        # Область скриптов
        self.scripts_frame = tk.Frame(self.root)
        self.scripts_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.canvas = tk.Canvas(self.scripts_frame)
        scrollbar = tk.Scrollbar(self.scripts_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas)
        
        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.refresh_scripts()
    
    def refresh_scripts(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        for script in self.scripts:
            self.create_script_button(script)
    
    def create_script_button(self, script):
        color = script.get('color', 'white')
        name = script['name']
        
        # Динамическая ширина
        btn_width = max(15, min(50, len(name) + 4))
        
        btn = tk.Button(self.scrollable_frame, text=name, bg=color,
                       fg="white" if color in ["black", "blue", "purple", "red"] else "black",
                       font=("Arial", 10, "bold"),
                       width=btn_width,
                       command=lambda t=script['text']: self.copy_to_clipboard(t))
        btn.pack(pady=5, padx=5)
    
    def filter_scripts(self, event=None):
        search_text = self.search_var.get().lower()
        
        # Очищаем текущие кнопки
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        # Показываем только подходящие
        for script in self.scripts:
            if search_text in script['name'].lower() or search_text in script['text'].lower():
                self.create_script_button(script)
    
    def focus_search(self):
        self.search_entry.focus()
        self.search_entry.select_all()
    
    def copy_to_clipboard(self, text):
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.root.update()
        time.sleep(0.1)
        
        # Копируем в буфер (без авто-вставки для надёжности)
        messagebox.showinfo("Готово", "Текст скопирован в буфер!\nНажмите Ctrl+V для вставки")
    
    # === КНОПКИ ===
    
    def show_about(self):
        messagebox.showinfo("Скриптонайзер Lite", 
                           "Версия 1.0\n\n"
                           "Персональная программа для работы со скриптами\n\n"
                           "Функции:\n"
                           "• Добавление и редактирование скриптов\n"
                           "• Быстрое копирование в буфер\n"
                           "• Скрытие окна\n"
                           "• Сворачивание в мини-кнопку\n"
                           "• Поиск по скриптам\n\n"
                           "© 2026")
    
    def toggle_hide(self):
        self.hidden_mode = not self.hidden_mode
        if self.hidden_mode:
            self.root.attributes('-alpha', 0.1)  # Почти невидимое
        else:
            self.root.attributes('-alpha', 1.0)  # Видимое
    
    def minimize_to_button(self):
        if self.mini_mode:
            # Вернуть окно
            if self.mini_window:
                self.mini_window.destroy()
            self.root.deiconify()
            self.mini_mode = False
        else:
            # Скрыть окно, показать мини-кнопку
            self.root.withdraw()
            self.mini_mode = True
            self.create_mini_button()
    
    def create_mini_button(self):
        self.mini_window = tk.Toplevel()
        self.mini_window.title("Скрипты")
        self.mini_window.geometry("150x60+100+100")
        self.mini_window.attributes('-topmost', True)
        
        # Кнопка "Вернуть скрипты"
        btn = tk.Button(self.mini_window, text="Вернуть\nскрипты", 
                       command=self.minimize_to_button,
                       bg="#FF9800", fg="white",
                       font=("Arial", 10, "bold"),
                       width=15, height=2)
        btn.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.mini_window.protocol("WM_DELETE_WINDOW", self.minimize_to_button)
    
    def open_editor(self):
        if not self.scripts:
            messagebox.showinfo("Инфо", "Нет скриптов для редактирования")
            return
        
        editor = tk.Toplevel(self.root)
        editor.title("Редактор скриптов")
        editor.geometry("650x500")
        
        # 4 кнопки СВЕРХУ (как на скрине)
        top_btn_frame = tk.Frame(editor)
        top_btn_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Button(top_btn_frame, text="Вставить скрипты", command=self.import_scripts).pack(side=tk.LEFT, padx=5)
        tk.Button(top_btn_frame, text="Скопировать в буфер", command=self.copy_all_scripts).pack(side=tk.LEFT, padx=5)
        tk.Button(top_btn_frame, text="Добавить скрипт", command=self.add_script).pack(side=tk.LEFT, padx=5)
        tk.Button(top_btn_frame, text="На раб.стол", command=self.export_to_desktop).pack(side=tk.LEFT, padx=5)
        
        # Список скриптов
        list_frame = tk.Frame(editor)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.editor_listbox = tk.Listbox(list_frame, font=("Arial", 10))
        scrollbar = tk.Scrollbar(list_frame, orient="vertical", command=self.editor_listbox.yview)
        self.editor_listbox.configure(yscrollcommand=scrollbar.set)
        
        self.editor_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        for s in self.scripts:
            self.editor_listbox.insert(tk.END, s['name'])
        
        # 2 кнопки СНИЗУ (перед управлением таймером/группами)
        mid_btn_frame = tk.Frame(editor)
        mid_btn_frame.pack(fill=tk.X, padx=10, pady=5)
        
        def delete_selected():
            sel = self.editor_listbox.curselection()
            if sel:
                if messagebox.askyesno("Удалить", f"Удалить скрипт '{self.scripts[sel[0]]['name']}'?"):
                    self.scripts.pop(sel[0])
                    self.save_scripts()
                    self.editor_listbox.delete(sel[0])
                    self.refresh_scripts()
        
        def edit_selected():
            sel = self.editor_listbox.curselection()
            if sel:
                self.edit_script(sel[0])
        
        tk.Button(mid_btn_frame, text="🗑️ Удалить", command=delete_selected, 
                 bg="#f44336", fg="white", width=12).pack(side=tk.LEFT, padx=5)
        tk.Button(mid_btn_frame, text="✏️ Редактировать", command=edit_selected, width=15).pack(side=tk.LEFT, padx=5)
        
        # Управление таймером и группами (в самом низу)
        bottom_btn_frame = tk.Frame(editor)
        bottom_btn_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Button(bottom_btn_frame, text="Управление таймером", command=self.open_timer_manager).pack(side=tk.LEFT, padx=5)
        tk.Button(bottom_btn_frame, text="Управление группами", command=self.open_group_manager).pack(side=tk.RIGHT, padx=5)
        
        # Кнопка закрытия
        tk.Button(editor, text="❌ Закрыть", command=editor.destroy).pack(pady=5)
    
    def edit_script(self, index):
        script = self.scripts[index]
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Редактировать: {script['name']}")
        dialog.geometry("500x400")
        
        tk.Label(dialog, text="Имя:").pack(anchor=tk.W, padx=10, pady=(10,0))
        name_entry = tk.Entry(dialog)
        name_entry.insert(0, script['name'])
        name_entry.pack(fill=tk.X, padx=10)
        
        tk.Label(dialog, text="Текст:").pack(anchor=tk.W, padx=10, pady=(10,0))
        text_area = tk.Text(dialog, height=10)
        text_area.insert('1.0', script['text'])
        text_area.pack(fill=tk.BOTH, expand=True, padx=10)
        
        tk.Label(dialog, text="Цвет:").pack(anchor=tk.W, padx=10, pady=(10,0))
        color_var = tk.StringVar(value=script.get('color', 'white'))
        colors = ["white", "red", "green", "blue", "yellow", "orange", "purple", "black"]
        color_combo = ttk.Combobox(dialog, textvariable=color_var, values=colors, state="readonly")
        color_combo.pack(anchor=tk.W, padx=10)
        
        def save():
            self.scripts[index]['name'] = name_entry.get()
            self.scripts[index]['text'] = text_area.get('1.0', tk.END).strip()
            self.scripts[index]['color'] = color_var.get()
            self.save_scripts()
            self.refresh_scripts()
            dialog.destroy()
        
        tk.Button(dialog, text="Сохранить", command=save, 
                 bg="#4CAF50", fg="white").pack(pady=10)
    
    def add_script(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Добавить скрипт")
        dialog.geometry("500x450")
        
        # Имя скрипта
        tk.Label(dialog, text="Имя скрипта:").pack(anchor=tk.W, padx=10, pady=(10,0))
        name_entry = tk.Entry(dialog)
        name_entry.pack(fill=tk.X, padx=10)
        
        # Тело скрипта
        tk.Label(dialog, text="Тело скрипта:").pack(anchor=tk.W, padx=10, pady=(10,0))
        text_area = tk.Text(dialog, height=15)
        text_area.pack(fill=tk.BOTH, expand=True, padx=10)
        
        # Цвет
        tk.Label(dialog, text="Цвет:").pack(anchor=tk.W, padx=10, pady=(10,0))
        color_var = tk.StringVar(value="white")
        colors = ["white", "red", "green", "blue", "yellow", "orange", "purple", "black"]
        color_combo = ttk.Combobox(dialog, textvariable=color_var, values=colors, state="readonly")
        color_combo.pack(anchor=tk.W, padx=10)
        color_combo.current(0)
        
        # Кнопки Сохранить/Отмена (как на скрине)
        btn_frame = tk.Frame(dialog)
        btn_frame.pack(fill=tk.X, pady=10)
        
        def save():
            name = name_entry.get()
            text = text_area.get('1.0', tk.END).strip()
            color = color_var.get()
            
            if name and text:
                self.scripts.append({"name": name, "text": text, "color": color})
                self.save_scripts()
                self.refresh_scripts()
                dialog.destroy()
                messagebox.showinfo("Успех", "Скрипт добавлен!")
            else:
                messagebox.showwarning("Ошибка", "Заполните все поля")
        
        tk.Button(btn_frame, text="Сохранить", command=save, 
                 bg="#4CAF50", fg="white", width=20).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text="Отмена", command=dialog.destroy, 
                 bg="#f44336", fg="white", width=20).pack(side=tk.LEFT, padx=10)
    
    def copy_all_scripts(self):
        text = "\n".join([f"=== {s['name']} ===\n{s['text']}\n" for s in self.scripts])
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        messagebox.showinfo("Успех", "Все скрипты скопированы!")
    
    def import_scripts(self):
        filepath = filedialog.askopenfilename(filetypes=[("TXT files", "*.txt"), ("JSON files", "*.json")])
        if filepath:
            try:
                if filepath.endswith('.json'):
                    with open(filepath, 'r', encoding='utf-8') as f:
                        imported = json.load(f)
                    self.scripts.extend(imported)
                else:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    blocks = content.split('===')
                    for block in blocks:
                        if not block.strip():
                            continue
                        try:
                            header, body = block.split('\n', 1)
                            parts = header.strip().split('|')
                            name = parts[0].strip()
                            color = parts[1].strip() if len(parts) > 1 else 'white'
                            self.scripts.append({"name": name, "text": body.strip(), "color": color})
                        except:
                            continue
                
                self.save_scripts()
                self.refresh_scripts()
                messagebox.showinfo("Успех", "Скрипты импортированы!")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось импортировать: {e}")
    
    def export_to_desktop(self):
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        path = os.path.join(desktop, "scripts.txt")
        with open(path, 'w', encoding='utf-8') as f:
            for s in self.scripts:
                color = s.get('color', 'white')
                f.write(f"=== {s['name']} | {color} ===\n{s['text']}\n\n")
        messagebox.showinfo("Успех", f"Сохранено: {path}")
    
    def open_timer_manager(self):
        messagebox.showinfo("Таймер", "Функция управления таймером\n(будет добавлена позже)")
    
    def open_group_manager(self):
        messagebox.showinfo("Группы", "Функция управления группами\n(будет добавлена позже)")
    
    # === СОХРАНЕНИЕ ===
    
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
    app = ScriptonizerLite(root)
    root.mainloop()
