import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
from datetime import datetime, timedelta

# --- КОНФИГУРАЦИЯ ---
DATA_FILE = "scripts_data.json"
CONFIG_FILE = "config.json"

class TimerWindow(tk.Toplevel):
    """Окно таймеров"""
    def __init__(self, parent, add_timer_callback):
        super().__init__(parent)
        self.title("Таймеры")
        self.geometry("400x300")
        self.add_timer_callback = add_timer_callback
        self.timers = []
        
        tk.Label(self, text="Управление таймерами", font=("Arial", 12, "bold")).pack(pady=10)
        
        frame = tk.Frame(self)
        frame.pack(fill=tk.BOTH, expand=True, padx=10)
        
        self.timer_listbox = tk.Listbox(frame, font=("Arial", 10))
        self.timer_listbox.pack(fill=tk.BOTH, expand=True)
        
        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=10)
        
        tk.Button(btn_frame, text="➕ Добавить таймер", command=self.add_timer_dialog).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="❌ Удалить", command=self.remove_timer).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="❌ Закрыть", command=self.destroy).pack(side=tk.RIGHT, padx=5)
        
        self.update_timer_display()
        self.start_timer_loop()

    def add_timer_dialog(self):
        dialog = tk.Toplevel(self)
        dialog.title("Новый таймер")
        dialog.geometry("300x150")
        
        tk.Label(dialog, text="Название:").pack(pady=5)
        name_entry = tk.Entry(dialog)
        name_entry.pack(pady=5)
        
        tk.Label(dialog, text="Минут до конца:").pack(pady=5)
        time_entry = tk.Entry(dialog)
        time_entry.pack(pady=5)
        
        def save():
            name = name_entry.get() or "Таймер"
            try:
                minutes = int(time_entry.get())
                end_time = datetime.now() + timedelta(minutes=minutes)
                self.timers.append({"name": name, "end_time": end_time})
                self.update_timer_display()
                dialog.destroy()
            except ValueError:
                messagebox.showerror("Ошибка", "Введите число минут")
        
        tk.Button(dialog, text="OK", command=save).pack(pady=10)

    def remove_timer(self):
        selection = self.timer_listbox.curselection()
        if selection:
            self.timers.pop(selection[0])
            self.update_timer_display()

    def update_timer_display(self):
        self.timer_listbox.delete(0, tk.END)
        for t in self.timers:
            self.timer_listbox.insert(tk.END, f"{t['name']} - {t['end_time'].strftime('%H:%M')}")

    def start_timer_loop(self):
        self.check_timers()
        self.after(1000, self.start_timer_loop)

    def check_timers(self):
        now = datetime.now()
        for t in self.timers[:]:
            if now >= t['end_time']:
                messagebox.showinfo("Время!", f"Таймер '{t['name']}': ДОМОЙ! 🏠")
                self.timers.remove(t)
                self.update_timer_display()
        self.update_timer_display()

class SettingsWindow(tk.Toplevel):
    def __init__(self, parent, config, save_callback):
        super().__init__(parent)
        self.title("Настройки")
        self.geometry("400x300")
        self.config = config
        self.save_callback = save_callback
        
        tk.Label(self, text="Основные настройки", font=("Arial", 12, "bold")).pack(pady=10)
        
        tk.Label(self, text="Размер шрифта кнопок:").pack(anchor=tk.W, padx=20)
        self.font_size = tk.Spinbox(self, from_=8, to=20, width=5)
        self.font_size.set(config.get('font_size', 10))
        self.font_size.pack(anchor=tk.W, padx=20)
        
        tk.Label(self, text="Отступы между кнопками:").pack(anchor=tk.W, padx=20, pady=(10,0))
        self.padding = tk.Spinbox(self, from_=2, to=20, width=5)
        self.padding.set(config.get('padding', 5))
        self.padding.pack(anchor=tk.W, padx=20)
        
        tk.Button(self, text="💾 Сохранить", command=self.save).pack(pady=20)
        tk.Button(self, text="❌ Закрыть", command=self.destroy).pack()

    def save(self):
        self.config['font_size'] = int(self.font_size.get())
        self.config['padding'] = int(self.padding.get())
        self.save_callback(self.config)
        messagebox.showinfo("Успех", "Настройки сохранены!")
        self.destroy()

class ScriptonizerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Скриптонайзер v.2.0 (Personal)")
        self.root.geometry("800x600")
        
        # Загрузка настроек
        self.config = self.load_config()
        self.scripts = self.load_scripts()
        
        # Состояния
        self.hover_hide_mode = False
        self.mini_mode = False
        self.mini_window = None
        
        self.setup_ui()
        self.apply_config()
        
        # Привязка событий для режима скрытия
        self.root.bind("<Enter>", self.on_enter)
        self.root.bind("<Leave>", self.on_leave)

    def setup_ui(self):
        # --- ВЕРХНЯЯ ПАНЕЛЬ (ФИКСИРОВАННАЯ) ---
        self.top_bar = tk.Frame(self.root, bg="#333333", height=50)
        self.top_bar.pack(fill=tk.X, side=tk.TOP)
        self.top_bar.pack_propagate(False)
        
        # Кнопки панели (круглые через padding и шрифт)
        btn_style = {"bg": "#555555", "fg": "white", "font": ("Arial", 10, "bold"), "width": 3, "relief": tk.FLAT}
        
        tk.Button(self.top_bar, text="⚙️", command=self.open_settings, **btn_style).pack(side=tk.LEFT, padx=5, pady=10)
        tk.Button(self.top_bar, text="📝", command=self.open_editor, **btn_style).pack(side=tk.LEFT, padx=5, pady=10)
        tk.Button(self.top_bar, text="⏱️", command=self.open_timers, **btn_style).pack(side=tk.LEFT, padx=5, pady=10)
        
        # Поиск
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(self.top_bar, textvariable=self.search_var, width=20)
        self.search_entry.pack(side=tk.LEFT, padx=10, pady=10)
        self.search_entry.bind('<KeyRelease>', self.filter_scripts)
        
        # Справа
        tk.Button(self.top_bar, text="📌", command=self.toggle_topmost, **btn_style).pack(side=tk.RIGHT, padx=5, pady=10)
        tk.Button(self.top_bar, text="👁️", command=self.toggle_hover_hide, **btn_style).pack(side=tk.RIGHT, padx=5, pady=10)
        tk.Button(self.top_bar, text="➖", command=self.toggle_mini_mode, **btn_style).pack(side=tk.RIGHT, padx=5, pady=10)
        tk.Button(self.top_bar, text="➕", command=self.add_script, bg="#4CAF50", fg="white", font=("Arial", 10, "bold"), width=3, relief=tk.FLAT).pack(side=tk.RIGHT, padx=5, pady=10)
        
        # --- ОБЛАСТЬ СКРИПТОВ (ДИНАМИЧЕСКАЯ) ---
        self.scripts_frame = tk.Frame(self.root, bg="#f0f0f0")
        self.scripts_frame.pack(fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(self.scripts_frame, bg="#f0f0f0", highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.scripts_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg="#f0f0f0")
        
        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.refresh_scripts()

    def apply_config(self):
        font_size = self.config.get('font_size', 10)
        self.script_font = ("Arial", font_size, "bold")
        self.padding = self.config.get('padding', 5)

    def create_script_button(self, name, text, color, index):
        btn_frame = tk.Frame(self.scrollable_frame, bg=color, relief=tk.RAISED, borderwidth=1)
        btn_frame.pack(fill=tk.X, pady=self.padding, padx=5)
        
        # Динамическая кнопка
        btn = tk.Button(btn_frame, text=f"📋 {name}", command=lambda t=text: self.copy_to_clipboard(t),
                       bg=color, fg="white" if color in ["black", "blue", "purple", "red"] else "black",
                       font=self.script_font, anchor=tk.W, padx=10, pady=5)
        btn.pack(fill=tk.X, side=tk.LEFT, expand=True)
        
        tk.Button(btn_frame, text="✏️", command=lambda: self.edit_script(index), width=3, bg="#FF9800", fg="white", relief=tk.FLAT).pack(side=tk.RIGHT, padx=2)
        tk.Button(btn_frame, text="🗑️", command=lambda: self.delete_script(index), width=3, bg="#f44336", fg="white", relief=tk.FLAT).pack(side=tk.RIGHT, padx=2)
def copy_to_clipboard(self, text):
    import pyautogui
    import time
    
    # Копируем в буфер
    self.root.clipboard_clear()
    self.root.clipboard_append(text)
    self.root.update()
    
    # Небольшая пауза, чтобы буфер успел обновиться
    time.sleep(0.1)
    
    # Эмулируем нажатие Ctrl+V для вставки
    pyautogui.hotkey('ctrl', 'v')
    # --- РЕЖИМЫ ---
    def toggle_topmost(self):
        is_top = self.root.attributes('-topmost')
        self.root.attributes('-topmost', not is_top)
        messagebox.showinfo("Инфо", "Поверх окон: " + ("ВКЛ" if not is_top else "ВЫКЛ"))

    def toggle_hover_hide(self):
        self.hover_hide_mode = not self.hover_hide_mode
        if self.hover_hide_mode:
            self.root.attributes('-alpha', 0.05)  # Почти невидимое
            messagebox.showinfo="Режим призрака", "Наведи мышь на окно, чтобы увидеть его. Убери - скроется."
        else:
            self.root.attributes('-alpha', 1.0)

    def on_enter(self, event):
        if self.hover_hide_mode:
            self.root.attributes('-alpha', 1.0)

    def on_leave(self, event):
        if self.hover_hide_mode:
            # Проверка, чтобы не скрыть, если мышь ушла на дочернее окно
            self.root.after(500, lambda: self.root.attributes('-alpha', 0.05) if self.hover_hide_mode else None)

    def toggle_mini_mode(self):
        if self.mini_mode:
            # Вернуть
            if self.mini_window:
                self.mini_window.destroy()
            self.root.deiconify()
            self.mini_mode = False
        else:
            # Скрыть
            self.root.withdraw()
            self.mini_mode = True
            self.create_mini_window()

    def create_mini_window(self):
        self.mini_window = tk.Toplevel()
        self.mini_window.title("Скрипты")
        self.mini_window.geometry("150x50+100+100")
        self.mini_window.attributes('-topmost', True)
        
        tk.Button(self.mini_window, text="Вернуть скрипты", command=self.toggle_mini_mode, 
                 bg="#2196F3", fg="white", font=("Arial", 10, "bold")).pack(fill=tk.BOTH, expand=True)
        
        self.mini_window.protocol("WM_DELETE_WINDOW", self.toggle_mini_mode)

    # --- СКРИПТЫ ---
    def add_script(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Добавить скрипт")
        dialog.geometry("500x400")
        dialog.attributes('-topmost', True)
        
        tk.Label(dialog, text="Имя:").pack(anchor=tk.W, padx=10, pady=(10,0))
        name_entry = tk.Entry(dialog)
        name_entry.pack(fill=tk.X, padx=10)
        
        tk.Label(dialog, text="Цвет (red, green, blue, white, black, orange):").pack(anchor=tk.W, padx=10, pady=(10,0))
        color_entry = tk.Entry(dialog)
        color_entry.insert(0, "white")
        color_entry.pack(fill=tk.X, padx=10)
        
        tk.Label(dialog, text="Текст:").pack(anchor=tk.W, padx=10, pady=(10,0))
        text_area = tk.Text(dialog, height=10)
        text_area.pack(fill=tk.BOTH, expand=True, padx=10)
        
        def save():
            name = name_entry.get()
            color = color_entry.get()
            text = text_area.get('1.0', tk.END).strip()
            if name and text:
                self.scripts.append({"name": name, "text": text, "color": color})
                self.save_scripts()
                self.refresh_scripts()
                dialog.destroy()
            else:
                messagebox.showwarning("Ошибка", "Заполните имя и текст")
        
        tk.Button(dialog, text="Сохранить", command=save, bg="#4CAF50", fg="white").pack(pady=10)

    def edit_script(self, index):
        script = self.scripts[index]
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Редактор: {script['name']}")
        dialog.geometry("500x400")
        
        text_area = tk.Text(dialog)
        text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text_area.insert('1.0', script['text'])
        
        def save():
            self.scripts[index]['text'] = text_area.get('1.0', tk.END).strip()
            self.save_scripts()
            self.refresh_scripts()
            dialog.destroy()
        
        tk.Button(dialog, text="Сохранить", command=save, bg="#4CAF50", fg="white").pack(pady=10)

    def delete_script(self, index):
        if messagebox.askyesno("Удалить?", "Удалить этот скрипт?"):
            del self.scripts[index]
            self.save_scripts()
            self.refresh_scripts()

    def filter_scripts(self, event=None):
        query = self.search_var.get().lower()
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        for i, s in enumerate(self.scripts):
            if query in s['name'].lower() or query in s['text'].lower():
                self.create_script_button(s['name'], s['text'], s['color'], i)

    def refresh_scripts(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        for i, s in enumerate(self.scripts):
            self.create_script_button(s['name'], s['text'], s['color'], i)

    # --- РЕДАКТОР / TXT ---
    def open_editor(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Редактор скриптов (TXT)")
        dialog.geometry("600x400")
        
        text_area = tk.Text(dialog)
        text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Загрузка в формат TXT
        txt_content = ""
        for s in self.scripts:
            txt_content += f"=== {s['name']} | {s['color']} ===\n{s['text']}\n\n"
        text_area.insert('1.0', txt_content)
        
        def save_txt():
            content = text_area.get('1.0', tk.END)
            # Парсинг обратно (упрощенный)
            messagebox.showinfo("Инфо", "Для сохранения используйте 'Экспорт'. Здесь только просмотр.")
        
        def export_txt():
            filepath = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("TXT", "*.txt")])
            if filepath:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(text_area.get('1.0', tk.END))
                messagebox.showinfo("Успех", "Экспортировано!")
        
        def import_txt():
            filepath = filedialog.askopenfilename(filetypes=[("TXT", "*.txt")])
            if filepath:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                # Простой парсер
                new_scripts = []
                blocks = content.split('===')
                for block in blocks:
                    if not block.strip(): continue
                    try:
                        header, body = block.split('\n', 1)
                        name_color = header.strip().split('|')
                        name = name_color[0].strip()
                        color = name_color[1].strip() if len(name_color) > 1 else "white"
                        new_scripts.append({"name": name, "text": body.strip(), "color": color})
                    except:
                        continue
                if new_scripts:
                    self.scripts = new_scripts
                    self.save_scripts()
                    self.refresh_scripts()
                    dialog.destroy()
                    messagebox.showinfo("Успех", "Импортировано!")
        
        btn_frame = tk.Frame(dialog)
        btn_frame.pack(fill=tk.X, padx=10, pady=5)
        tk.Button(btn_frame, text="📥 Импорт TXT", command=import_txt).pack(side=tk.LEFT)
        tk.Button(btn_frame, text="📤 Экспорт TXT", command=export_txt).pack(side=tk.LEFT)
        tk.Button(btn_frame, text="💾 На рабочий стол", command=lambda: self.save_to_desktop(text_area.get('1.0', tk.END))).pack(side=tk.LEFT)
        tk.Button(btn_frame, text="❌ Закрыть", command=dialog.destroy).pack(side=tk.RIGHT)

    def save_to_desktop(self, text):
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        path = os.path.join(desktop, "scripts_backup.txt")
        with open(path, 'w', encoding='utf-8') as f:
            f.write(text)
        messagebox.showinfo("Готово", f"Сохранено: {path}")

    def open_timers(self):
        TimerWindow(self.root, None)

    def open_settings(self):
        SettingsWindow(self.root, self.config, self.save_config)

    # --- СОХРАНЕНИЕ ---
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

    def save_config(self, config):
    self.config = config
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        self.apply_config()
        self.refresh_scripts()
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось сохранить настройки: {e}")

def load_config(self):
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Ошибка загрузки конфига: {e}")
            return {}
    return {}
if __name__ == "__main__":
    root = tk.Tk()
    app = ScriptonizerApp(root)
    root.mainloop()
