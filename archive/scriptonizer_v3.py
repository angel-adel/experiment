import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import json
import os
import pyautogui
import time
from datetime import datetime, timedelta
import winsound

# --- КОНФИГУРАЦИЯ ---
DATA_FILE = "scripts_data.json"
CONFIG_FILE = "config.json"

# ==================== ОКНО УПРАВЛЕНИЯ ГРУППАМИ ====================
class GroupManagerWindow(tk.Toplevel):
    def __init__(self, parent, groups, save_callback):
        super().__init__(parent)
        self.title("Управление группами")
        self.geometry("600x400")
        self.groups = groups if groups else []
        self.save_callback = save_callback
        
        btn_frame = tk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Button(btn_frame, text="➕", width=3, command=self.add_group, bg="#4CAF50").pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="❌", width=3, command=self.delete_group, bg="#f44336").pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="⭐", width=3, command=self.toggle_favorite, bg="#FFD700").pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="✏️", width=3, command=self.rename_group).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="🔼", width=3, command=lambda: self.move_group(-1)).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="🔽", width=3, command=lambda: self.move_group(1)).pack(side=tk.LEFT, padx=2)
        
        list_frame = tk.Frame(self)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.listbox = tk.Listbox(list_frame, font=("Arial", 11), selectmode=tk.SINGLE)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=scrollbar.set)
        
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.refresh_list()
        tk.Button(self, text="Изменить группу", command=self.save_and_close).pack(pady=10)
    
    def refresh_list(self):
        self.listbox.delete(0, tk.END)
        for g in self.groups:
            star = "⭐ " if g.get('favorite', False) else ""
            self.listbox.insert(tk.END, f"{star}{g['name']}")
    
    def add_group(self):
        name = simpledialog.askstring("Новая группа", "Введите название:")
        if name:
            self.groups.append({"name": name, "favorite": False, "scripts": []})
            self.refresh_list()
    
    def delete_group(self):
        sel = self.listbox.curselection()
        if sel:
            if messagebox.askyesno("Удалить", "Удалить группу?"):
                self.groups.pop(sel[0])
                self.refresh_list()
    
    def toggle_favorite(self):
        sel = self.listbox.curselection()
        if sel:
            idx = sel[0]
            self.groups[idx]['favorite'] = not self.groups[idx].get('favorite', False)
            self.refresh_list()
    
    def rename_group(self):
        sel = self.listbox.curselection()
        if sel:
            idx = sel[0]
            new_name = simpledialog.askstring("Переименовать", "Новое название:", initialvalue=self.groups[idx]['name'])
            if new_name:
                self.groups[idx]['name'] = new_name
                self.refresh_list()
    
    def move_group(self, direction):
        sel = self.listbox.curselection()
        if sel:
            idx = sel[0]
            new_idx = idx + direction
            if 0 <= new_idx < len(self.groups):
                self.groups[idx], self.groups[new_idx] = self.groups[new_idx], self.groups[idx]
                self.refresh_list()
                self.listbox.selection_set(new_idx)
    
    def save_and_close(self):
        self.save_callback(self.groups)
        self.destroy()

# ==================== ОКНО УПРАВЛЕНИЯ ТАЙМЕРАМИ ====================
class TimerManagerWindow(tk.Toplevel):
    def __init__(self, parent, timers, save_callback):
        super().__init__(parent)
        self.title("Управления профилями таймера")
        self.geometry("600x500")
        self.timers = timers if timers else []
        self.save_callback = save_callback
        self.current_profile = None
        
        top_frame = tk.Frame(self)
        top_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Button(top_frame, text="🔄", width=3, command=self.reset_timer, bg="#ff9800").pack(side=tk.LEFT, padx=2)
        tk.Button(top_frame, text="➕", width=3, command=self.add_profile, bg="#4CAF50").pack(side=tk.LEFT, padx=2)
        
        self.profiles_frame = tk.Frame(self)
        self.profiles_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.profile_notebook = ttk.Notebook(self.profiles_frame)
        self.profile_notebook.pack(fill=tk.X)
        self.profile_notebook.bind("<<NotebookTabChanged>>", self.on_profile_change)
        
        name_frame = tk.Frame(self)
        name_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(name_frame, text="Имя профиля:").pack(side=tk.LEFT)
        self.profile_name = tk.Entry(name_frame)
        self.profile_name.pack(fill=tk.X, expand=True, padx=5)
        tk.Button(name_frame, text="❌", command=self.delete_profile, bg="#f44336").pack(side=tk.RIGHT)
        
        events_frame = tk.Frame(self)
        events_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        tk.Label(events_frame, text="События:", font=("Arial", 10, "bold")).pack(anchor=tk.W)
        
        self.events_listbox = tk.Listbox(events_frame, font=("Arial", 10), height=10)
        events_scrollbar = ttk.Scrollbar(events_frame, orient="vertical", command=self.events_listbox.yview)
        self.events_listbox.configure(yscrollcommand=events_scrollbar.set)
        
        self.events_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        events_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        add_event_frame = tk.Frame(self)
        add_event_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(add_event_frame, text="Уведомление").pack(side=tk.LEFT)
        tk.Label(add_event_frame, text="За:").pack(side=tk.LEFT, padx=(10,0))
        self.notify_minutes = tk.Spinbox(add_event_frame, from_=1, to=120, width=5)
        self.notify_minutes.delete(0, tk.END)
        self.notify_minutes.insert(0, "15")
        self.notify_minutes.pack(side=tk.LEFT)
        tk.Label(add_event_frame, text="мин.").pack(side=tk.LEFT)
        
        tk.Button(add_event_frame, text="❌", command=self.delete_event, bg="#f44336").pack(side=tk.RIGHT, padx=2)
        tk.Button(add_event_frame, text="Добавить уведомление", command=self.add_event).pack(side=tk.RIGHT, padx=5)
        
        tk.Button(self, text="Добавить событие", command=self.add_event_dialog, bg="#2196F3", fg="white").pack(pady=10)
        
        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text="💾 Сохранить", command=self.save_and_close, bg="#4CAF50", fg="white", width=15).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text="❌ Закрыть", command=self.destroy, width=15).pack(side=tk.LEFT, padx=10)
        
        self.refresh_profiles()
    
    def refresh_profiles(self):
        for widget in self.profile_notebook.winfo_children():
            widget.destroy()
        
        for i, timer in enumerate(self.timers):
            frame = tk.Frame(self.profile_notebook)
            self.profile_notebook.add(frame, text=timer.get('name', f'Таймер {i+1}'))
        
        if self.timers:
            self.profile_notebook.select(0)
            self.current_profile = 0
            self.load_profile_events()
    
    def on_profile_change(self, event):
        self.current_profile = self.profile_notebook.index(self.profile_notebook.select())
        self.load_profile_events()
    
    def load_profile_events(self):
        if self.current_profile is not None and self.current_profile < len(self.timers):
            timer = self.timers[self.current_profile]
            self.profile_name.delete(0, tk.END)
            self.profile_name.insert(0, timer.get('name', ''))
            
            self.events_listbox.delete(0, tk.END)
            for event in timer.get('events', []):
                time_str = event.get('time', '12:00')
                notify = event.get('notify', 15)
                self.events_listbox.insert(tk.END, f"⏰ {time_str} | Уведомление за {notify} мин.")
    
    def add_profile(self):
        name = simpledialog.askstring("Новый профиль", "Имя профиля:")
        if name:
            self.timers.append({"name": name, "events": []})
            self.refresh_profiles()
            self.profile_notebook.select(len(self.timers) - 1)
            self.current_profile = len(self.timers) - 1
    
    def delete_profile(self):
        if self.current_profile is not None and self.timers:
            if messagebox.askyesno("Удалить", "Удалить профиль таймера?"):
                self.timers.pop(self.current_profile)
                self.current_profile = None
                self.refresh_profiles()
    
    def add_event_dialog(self):
        dialog = tk.Toplevel(self)
        dialog.title("Добавить событие")
        dialog.geometry("300x200")
        
        tk.Label(dialog, text="Время (ЧЧ:ММ):").pack(pady=5)
        time_entry = tk.Entry(dialog)
        time_entry.insert(0, "12:00")
        time_entry.pack(pady=5)
        
        tk.Label(dialog, text="Уведомить за (мин):").pack(pady=5)
        notify_entry = tk.Spinbox(dialog, from_=1, to=60)
        notify_entry.delete(0, tk.END)
        notify_entry.insert(0, "15")
        notify_entry.pack(pady=5)
        
        def save():
            try:
                t = time_entry.get()
                notify = int(notify_entry.get())
                if self.current_profile is not None:
                    self.timers[self.current_profile]['events'].append({
                        "time": t,
                        "notify": notify
                    })
                    self.load_profile_events()
                    dialog.destroy()
            except:
                messagebox.showerror("Ошибка", "Неверные данные")
        
        tk.Button(dialog, text="OK", command=save).pack(pady=10)
    
    def add_event(self):
        if self.current_profile is not None:
            t = "12:00"
            notify = int(self.notify_minutes.get())
            self.timers[self.current_profile]['events'].append({
                "time": t,
                "notify": notify
            })
            self.load_profile_events()
    
    def delete_event(self):
        sel = self.events_listbox.curselection()
        if sel and self.current_profile is not None:
            self.timers[self.current_profile]['events'].pop(sel[0])
            self.load_profile_events()
    
    def reset_timer(self):
        messagebox.showinfo("Таймер", "Сброс таймера")
    
    def save_and_close(self):
        for i, timer in enumerate(self.timers):
            timer['name'] = self.timers[i].get('name', f'Таймер {i+1}')
        
        self.save_callback(self.timers)
        messagebox.showinfo("Успех", "Таймеры сохранены!")
        self.destroy()

# ==================== ОСНОВНОЕ ПРИЛОЖЕНИЕ ====================
class ScriptonizerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Скриптонайзер v.3.1")
        self.root.geometry("800x600")
        
        self.config = self.load_config()
        self.scripts = self.load_scripts()
        self.groups = self.load_groups()
        self.timers = self.load_timers()
        
        self.hover_hide = False
        self.fixed_size = False
        self.drag_mode = False
        self.drag_start_idx = None
        
        self.setup_ui()
        self.apply_config()
        self.start_timers()
    
    def setup_ui(self):
        self.top_frame = tk.Frame(self.root, bg="#e0e0e0")
        self.top_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.buttons = {}
        
        self.buttons['settings'] = tk.Button(self.top_frame, text="⚙️", width=4, height=2, command=self.open_settings)
        self.buttons['hide'] = tk.Button(self.top_frame, text="👁️", width=4, height=2, command=self.toggle_hide)
        self.buttons['drag'] = tk.Button(self.top_frame, text="↔️", width=4, height=2, command=self.toggle_drag)
        self.buttons['fix'] = tk.Button(self.top_frame, text="🔒", width=4, height=2, command=self.toggle_fixed)
        self.buttons['editor'] = tk.Button(self.top_frame, text="📝", width=4, height=2, command=self.open_editor)
        self.buttons['timer'] = tk.Button(self.top_frame, text="⏱️", width=4, height=2, command=self.open_timer_manager, bg="#ff9800")
        self.buttons['search'] = tk.Button(self.top_frame, text="🔍", width=4, height=2, command=self.focus_search)
        
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(self.top_frame, textvariable=self.search_var, width=20)
        self.search_entry.bind('<KeyRelease>', self.filter_scripts)
        
        self.filter_var = tk.StringVar(value="Все")
        self.filter_combo = ttk.Combobox(self.top_frame, textvariable=self.filter_var, values=["Все"], state="readonly", width=12)
        self.filter_combo.current(0)
        self.filter_combo.bind('<<ComboboxSelected>>', self.filter_scripts)
        
        self.buttons['add'] = tk.Button(self.top_frame, text="➕", width=4, height=2, bg="#4CAF50", fg="white", command=self.add_script)
        
        self.update_buttons_visibility()
        self.update_filter_combo()
        
        self.scripts_frame = tk.Frame(self.root)
        self.scripts_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.canvas = tk.Canvas(self.scripts_frame)
        scrollbar = ttk.Scrollbar(self.scripts_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas)
        
        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.refresh_scripts()
    
    def update_buttons_visibility(self):
        for btn in self.buttons.values():
            btn.pack_forget()
        self.search_entry.pack_forget()
        self.filter_combo.pack_forget()
        
        if self.config.get('show_editor', True):
            self.buttons['settings'].pack(side=tk.LEFT, padx=2)
        
        if self.config.get('show_hide', True):
            self.buttons['hide'].pack(side=tk.LEFT, padx=2)
        
        if self.config.get('drag_drop', False):
            self.buttons['drag'].pack(side=tk.LEFT, padx=2)
        
        self.buttons['fix'].pack(side=tk.LEFT, padx=2)
        
        if self.config.get('show_editor', True):
            self.buttons['editor'].pack(side=tk.LEFT, padx=2)
        
        if self.config.get('show_timer', False) and self.timers:
            self.buttons['timer'].pack(side=tk.LEFT, padx=2)
        
        if self.config.get('show_search', True):
            self.buttons['search'].pack(side=tk.LEFT, padx=2)
            self.search_entry.pack(side=tk.LEFT, padx=5)
        
        self.filter_combo.pack(side=tk.LEFT, padx=5)
        
        if self.config.get('show_add', True):
            self.buttons['add'].pack(side=tk.RIGHT, padx=2)
    
    def apply_config(self):
        if self.config.get('always_on_top', False):
            self.root.attributes('-topmost', True)
    
    def refresh_scripts(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        spacing = self.config.get('btn_spacing', 5)
        rounding = self.config.get('rounding', 15)
        
        filter_val = self.filter_var.get()
        scripts_to_show = self.scripts
        
        if filter_val != "Все":
            scripts_to_show = [s for s in self.scripts if s.get('group') == filter_val or s.get('color') == filter_val]
        
        for i, script in enumerate(scripts_to_show):
            self.create_script_button(script, spacing, rounding, i)
    
    def create_script_button(self, script, spacing, rounding, index):
        color = script.get('color', 'white')
        name = script['name']
        
        # Динамическая ширина кнопки
        btn_width = max(15, min(50, len(name) + 4))
        
        btn = tk.Button(self.scrollable_frame, text=name, bg=color,
                       fg="white" if color in ["black", "blue", "purple", "red"] else "black",
                       font=("Arial", 10, "bold"),
                       width=btn_width,
                       anchor=tk.CENTER,
                       command=lambda t=script['text']: self.copy_and_paste(t))
        btn.pack(pady=spacing, padx=5)
        
        if self.drag_mode:
            btn.bind("<Button-1>", lambda e, idx=self.scripts.index(script): self.start_drag(idx))
            btn.bind("<B1-Motion>", lambda e, idx=self.scripts.index(script): self.drag(idx))
    
    def copy_and_paste(self, text):
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.root.update()
        time.sleep(0.1)
        
        if self.config.get('copy_to_buffer', True):
            try:
                pyautogui.hotkey('ctrl', 'v', interval=0.1)
            except Exception as e:
                print(f"Ошибка вставки: {e}")
    
    def filter_scripts(self, event=None):
        self.refresh_scripts()
    
    def update_filter_combo(self):
        values = ["Все"]
        colors = set(s.get('color', 'white') for s in self.scripts)
        values.extend(colors)
        if self.config.get('use_groups', False):
            groups = [g['name'] for g in self.groups]
            values.extend(groups)
        
        self.filter_combo['values'] = values
        if "Все" in values:
            self.filter_combo.current(0)
    
    def open_settings(self):
        SettingsWindow(self.root, self.config, self.save_config)
    
    def toggle_hide(self):
        self.hover_hide = not self.hover_hide
        if self.hover_hide:
            self.root.attributes('-alpha', 0.1)
        else:
            self.root.attributes('-alpha', 1.0)
    
    def toggle_drag(self):
        self.drag_mode = not self.drag_mode
        messagebox.showinfo("Drag&Drop", f"Режим перетаскивания: {'ВКЛ' if self.drag_mode else 'ВЫКЛ'}")
        self.refresh_scripts()
    
    def toggle_fixed(self):
        self.fixed_size = not self.fixed_size
        if self.fixed_size:
            self.root.resizable(False, False)
            self.root.update_idletasks()
            width = self.root.winfo_width()
            height = self.root.winfo_height()
            self.root.geometry(f"{width}x{height}")
        else:
            self.root.resizable(True, True)
    
    def open_editor(self):
        editor = tk.Toplevel(self.root)
        editor.title("Редактор скриптов")
        editor.geometry("650x500")
        
        btn_frame1 = tk.Frame(editor)
        btn_frame1.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Button(btn_frame1, text="Вставить скрипты", command=self.import_scripts).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame1, text="Скопировать в буфер", command=self.copy_all_scripts).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame1, text="Добавить скрипт", command=self.add_script).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame1, text="На раб.стол", command=self.export_to_desktop).pack(side=tk.LEFT, padx=5)
        
        list_frame = tk.Frame(editor)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.editor_listbox = tk.Listbox(list_frame, font=("Arial", 10))
        self.editor_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        for s in self.scripts:
            self.editor_listbox.insert(tk.END, s['name'])
        
        control_frame = tk.Frame(editor)
        control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        def delete_selected():
            sel = self.editor_listbox.curselection()
            if sel:
                if messagebox.askyesno("Удалить", f"Удалить скрипт '{self.scripts[sel[0]]['name']}'?"):
                    self.scripts.pop(sel[0])
                    self.save_scripts()
                    self.editor_listbox.delete(sel[0])
                    self.refresh_scripts()
                    self.update_filter_combo()
        
        def edit_selected():
            sel = self.editor_listbox.curselection()
            if sel:
                self.edit_script(sel[0])
        
        tk.Button(control_frame, text="🗑️ Удалить", command=delete_selected, bg="#f44336", fg="white").pack(side=tk.LEFT, padx=5)
        tk.Button(control_frame, text="✏️ Редактировать", command=edit_selected).pack(side=tk.LEFT, padx=5)
        
        btn_frame2 = tk.Frame(editor)
        btn_frame2.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Button(btn_frame2, text="Управление таймером", command=self.open_timer_manager).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame2, text="Управление группами", command=self.open_group_manager).pack(side=tk.RIGHT, padx=5)
    
    def edit_script(self, index):
        script = self.scripts[index]
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Редактировать: {script['name']}")
        dialog.geometry("600x450")
        
        tk.Label(dialog, text="Имя:").pack(anchor=tk.W, padx=10, pady=(10,0))
        name_entry = tk.Entry(dialog)
        name_entry.insert(0, script['name'])
        name_entry.pack(fill=tk.X, padx=10)
        
        tk.Label(dialog, text="Текст:").pack(anchor=tk.W, padx=10, pady=(10,0))
        text_area = tk.Text(dialog, height=15)
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
            self.update_filter_combo()
            dialog.destroy()
        
        tk.Button(dialog, text="Сохранить", command=save, bg="#4CAF50", fg="white").pack(pady=10)
    
    def open_timer_manager(self):
        TimerManagerWindow(self.root, self.timers, self.save_timers)
    
    def open_group_manager(self):
        GroupManagerWindow(self.root, self.groups, self.save_groups)
    
    def focus_search(self):
        self.search_entry.focus()
    
    def add_script(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Добавить скрипт")
        dialog.geometry("600x450")
        
        tk.Label(dialog, text="Имя скрипта:").pack(anchor=tk.W, padx=10, pady=(10,0))
        name_entry = tk.Entry(dialog)
        name_entry.pack(fill=tk.X, padx=10)
        
        tk.Label(dialog, text="Тело скрипта:").pack(anchor=tk.W, padx=10, pady=(10,0))
        text_area = tk.Text(dialog, height=15)
        text_area.pack(fill=tk.BOTH, expand=True, padx=10)
        
        tk.Label(dialog, text="Цвет:").pack(anchor=tk.W, padx=10, pady=(10,0))
        color_var = tk.StringVar(value="white")
        colors = ["white", "red", "green", "blue", "yellow", "orange", "purple", "black"]
        color_combo = ttk.Combobox(dialog, textvariable=color_var, values=colors, state="readonly")
        color_combo.pack(anchor=tk.W, padx=10)
        color_combo.current(0)
        
        if self.config.get('use_groups', False) and self.groups:
            tk.Label(dialog, text="Группа:").pack(anchor=tk.W, padx=10, pady=(10,0))
            group_var = tk.StringVar(value="")
            group_names = [""] + [g['name'] for g in self.groups]
            group_combo = ttk.Combobox(dialog, textvariable=group_var, values=group_names, state="readonly")
            group_combo.pack(anchor=tk.W, padx=10)
        else:
            group_var = None
        
        btn_frame = tk.Frame(dialog)
        btn_frame.pack(fill=tk.X, pady=10)
        
        def save():
            name = name_entry.get()
            text = text_area.get('1.0', tk.END).strip()
            color = color_var.get()
            
            if name and text:
                script = {"name": name, "text": text, "color": color}
                if group_var and group_var.get():
                    script['group'] = group_var.get()
                
                if self.config.get('add_at_end', True):
                    self.scripts.append(script)
                else:
                    self.scripts.insert(0, script)
                
                self.save_scripts()
                self.refresh_scripts()
                self.update_filter_combo()
                dialog.destroy()
            else:
                messagebox.showwarning("Ошибка", "Заполните все поля")
        
        tk.Button(btn_frame, text="Сохранить", command=save, bg="#4CAF50", fg="white", width=20).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text="Отмена", command=dialog.destroy, bg="#f44336", fg="white", width=20).pack(side=tk.LEFT, padx=10)
    
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
                self.update_filter_combo()
                messagebox.showinfo("Успех", "Скрипты импортированы!")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось импортировать: {e}")
    
    def export_to_desktop(self):
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        path = os.path.join(desktop, "scripts.txt")
        with open(path, 'w', encoding='utf-8') as f:
            for s in self.scripts:
                color = s.get('color', 'white')
                group = s.get('group', '')
                extra = f" | {group}" if group else ""
                f.write(f"=== {s['name']} | {color}{extra} ===\n{s['text']}\n\n")
        messagebox.showinfo("Успех", f"Сохранено: {path}")
    
    def start_drag(self, idx):
        self.drag_start_idx = idx
    
    def drag(self, idx):
        if self.drag_start_idx is not None and self.drag_start_idx != idx:
            self.scripts[self.drag_start_idx], self.scripts[idx] = self.scripts[idx], self.scripts[self.drag_start_idx]
            self.drag_start_idx = idx
            self.refresh_scripts()
            self.save_scripts()
    
    def start_timers(self):
        self.check_timers()
        self.root.after(1000, self.start_timers)
    
    def check_timers(self):
        now = datetime.now()
        for timer in self.timers:
            for event in timer.get('events', []):
                try:
                    event_time = datetime.strptime(event['time'], '%H:%M').time()
                    event_dt = datetime.combine(now.date(), event_time)
                    notify_before = timedelta(minutes=event.get('notify', 15))
                    notify_time = event_dt - notify_before
                    
                    if abs((now - notify_time).total_seconds()) < 1:
                        if self.config.get('timer_sound', True):
                            winsound.MessageBeep()
                        messagebox.showinfo(f"⏰ {timer['name']}", f"Событие: {event['time']}\nУведомление!")
                except:
                    pass
    
    def save_config(self, config):
        self.config = config
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        self.apply_config()
        self.update_buttons_visibility()
        self.refresh_scripts()
    
    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
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
    
    def save_groups(self, groups):
        self.groups = groups
        with open('groups.json', 'w', encoding='utf-8') as f:
            json.dump(groups, f, ensure_ascii=False, indent=2)
        self.update_filter_combo()
    
    def load_groups(self):
        if os.path.exists('groups.json'):
            try:
                with open('groups.json', 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def save_timers(self, timers):
        self.timers = timers
        with open('timers.json', 'w', encoding='utf-8') as f:
            json.dump(timers, f, ensure_ascii=False, indent=2)
        self.update_buttons_visibility()
    
    def load_timers(self):
        if os.path.exists('timers.json'):
            try:
                with open('timers.json', 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        return []

# ==================== ОКНО НАСТРОЕК ====================
class SettingsWindow(tk.Toplevel):
    def __init__(self, parent, config, save_callback):
        super().__init__(parent)
        self.title("Настройки")
        self.geometry("550x600")
        self.config = config
        self.save_callback = save_callback
        
        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        tab_main = tk.Frame(notebook)
        notebook.add(tab_main, text="Основные")
        self.setup_main_tab(tab_main)
        
        tab_extra = tk.Frame(notebook)
        notebook.add(tab_extra, text="Дополнительные")
        self.setup_extra_tab(tab_extra)
        
        tab_about = tk.Frame(notebook)
        notebook.add(tab_about, text="О приложении")
        self.setup_about_tab(tab_about)
        
        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text="💾 Сохранить", command=self.save, bg="#4CAF50", fg="white", width=15).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text="❌ Закрыть", command=self.destroy, width=15).pack(side=tk.LEFT, padx=10)
    
    def setup_main_tab(self, parent):
        tk.Label(parent, text="Межстрочный интервал (px)", font=("Arial", 10, "bold")).pack(anchor=tk.W, padx=10, pady=(10,0))
        self.line_spacing = tk.Scale(parent, from_=0, to=20, orient=tk.HORIZONTAL, length=450)
        self.line_spacing.set(self.config.get('line_spacing', 5))
        self.line_spacing.pack(anchor=tk.W, padx=10)
        
        tk.Label(parent, text="Межкнопочный интервал (px)", font=("Arial", 10, "bold")).pack(anchor=tk.W, padx=10, pady=(10,0))
        self.btn_spacing = tk.Scale(parent, from_=0, to=20, orient=tk.HORIZONTAL, length=450)
        self.btn_spacing.set(self.config.get('btn_spacing', 5))
        self.btn_spacing.pack(anchor=tk.W, padx=10)
        
        tk.Label(parent, text="Закругление кнопок (px)", font=("Arial", 10, "bold")).pack(anchor=tk.W, padx=10, pady=(10,0))
        self.rounding = tk.Scale(parent, from_=0, to=30, orient=tk.HORIZONTAL, length=450)
        self.rounding.set(self.config.get('rounding', 15))
        self.rounding.pack(anchor=tk.W, padx=10)
        
        tk.Label(parent, text="Скорость прокрутки", font=("Arial", 10, "bold")).pack(anchor=tk.W, padx=10, pady=(10,0))
        self.scroll_speed = tk.Scale(parent, from_=1, to=10, orient=tk.HORIZONTAL, length=450)
        self.scroll_speed.set(self.config.get('scroll_speed', 5))
        self.scroll_speed.pack(anchor=tk.W, padx=10)
        
        self.copy_to_buffer = tk.BooleanVar(value=self.config.get('copy_to_buffer', True))
        tk.Checkbutton(parent, text="Вставлять скрипт в буфер обмена", variable=self.copy_to_buffer).pack(anchor=tk.W, padx=10, pady=5)
        
        self.show_toggle = tk.BooleanVar(value=self.config.get('show_toggle', True))
        tk.Checkbutton(parent, text="Кнопка смены состояния", variable=self.show_toggle).pack(anchor=tk.W, padx=10, pady=5)
        
        self.always_on_top = tk.BooleanVar(value=self.config.get('always_on_top', False))
        tk.Checkbutton(parent, text="Поверх всех окон", variable=self.always_on_top).pack(anchor=tk.W, padx=10, pady=5)
        
        self.drag_drop = tk.BooleanVar(value=self.config.get('drag_drop', False))
        tk.Checkbutton(parent, text="Drag&Drop (перетаскивание кнопок)", variable=self.drag_drop).pack(anchor=tk.W, padx=10, pady=5)
    
    def setup_extra_tab(self, parent):
        canvas = tk.Canvas(parent)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas)
        
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        tk.Label(scroll_frame, text="=== КНОПКИ ИНТЕРФЕЙСА ===", font=("Arial", 10, "bold")).pack(anchor=tk.W, padx=10, pady=(10,0))
        
        self.show_hide = tk.BooleanVar(value=self.config.get('show_hide', True))
        tk.Checkbutton(scroll_frame, text="Кнопка 'Скрыть'", variable=self.show_hide).pack(anchor=tk.W, padx=10)
        
        self.show_add = tk.BooleanVar(value=self.config.get('show_add', True))
        tk.Checkbutton(scroll_frame, text="Кнопка быстрого добавления", variable=self.show_add).pack(anchor=tk.W, padx=10)
        self.add_at_end = tk.BooleanVar(value=self.config.get('add_at_end', True))
        tk.Checkbutton(scroll_frame, text="Вставлять новый скрипт в конце", variable=self.add_at_end).pack(anchor=tk.W, padx=20)
        
        self.show_search = tk.BooleanVar(value=self.config.get('show_search', True))
        tk.Checkbutton(scroll_frame, text="Кнопка поиска скрипта", variable=self.show_search).pack(anchor=tk.W, padx=10)
        
        self.show_hints = tk.BooleanVar(value=self.config.get('show_hints', True))
        tk.Checkbutton(scroll_frame, text="Подсказка с телом скрипта", variable=self.show_hints).pack(anchor=tk.W, padx=10)
        
        self.show_editor = tk.BooleanVar(value=self.config.get('show_editor', True))
        tk.Checkbutton(scroll_frame, text="Кнопка редактора скриптов", variable=self.show_editor).pack(anchor=tk.W, padx=10)
        
        tk.Label(scroll_frame, text="=== ГРУППИРОВКА ===", font=("Arial", 10, "bold")).pack(anchor=tk.W, padx=10, pady=(20,0))
        
        self.use_groups = tk.BooleanVar(value=self.config.get('use_groups', False))
        tk.Checkbutton(scroll_frame, text="Применять группы", variable=self.use_groups).pack(anchor=tk.W, padx=10)
        
        tk.Label(scroll_frame, text="Кол-во групп во всплывающем списке:").pack(anchor=tk.W, padx=10, pady=(5,0))
        self.groups_in_popup = tk.Spinbox(scroll_frame, from_=3, to=20, width=10)
        self.groups_in_popup.delete(0, tk.END)
        self.groups_in_popup.insert(0, str(self.config.get('groups_in_popup', 5)))
        self.groups_in_popup.pack(padx=20)
        
        self.show_fav_groups = tk.BooleanVar(value=self.config.get('show_fav_groups', False))
        tk.Checkbutton(scroll_frame, text="Показывать избранные группы", variable=self.show_fav_groups).pack(anchor=tk.W, padx=10)
        tk.Label(scroll_frame, text="Кол-во избранных групп:").pack(anchor=tk.W, padx=10)
        self.fav_groups_count = tk.Spinbox(scroll_frame, from_=3, to=20, width=10)
        self.fav_groups_count.delete(0, tk.END)
        self.fav_groups_count.insert(0, str(self.config.get('fav_groups_count', 3)))
        self.fav_groups_count.pack(padx=20)
        
        self.search_hidden = tk.BooleanVar(value=self.config.get('search_hidden', False))
        tk.Checkbutton(scroll_frame, text="Искать по скрытым группам", variable=self.search_hidden).pack(anchor=tk.W, padx=10)
        
        tk.Label(scroll_frame, text="=== ТАЙМЕР И СКРЫТИЕ ===", font=("Arial", 10, "bold")).pack(anchor=tk.W, padx=10, pady=(30,0))
        
        self.show_timer = tk.BooleanVar(value=self.config.get('show_timer', False))
        tk.Checkbutton(scroll_frame, text="Отображать таймер", variable=self.show_timer).pack(anchor=tk.W, padx=10)
        
        tk.Label(scroll_frame, text="Время отображения уведомления (сек):").pack(anchor=tk.W, padx=10, pady=(10,0))
        self.timer_notify_time = tk.Spinbox(scroll_frame, from_=5, to=60, width=10)
        self.timer_notify_time.delete(0, tk.END)
        self.timer_notify_time.insert(0, str(self.config.get('timer_notify_time', 10)))
        self.timer_notify_time.pack(padx=20)
        
        self.timer_sound = tk.BooleanVar(value=self.config.get('timer_sound', True))
        tk.Checkbutton(scroll_frame, text="Звук уведомлений", variable=self.timer_sound).pack(anchor=tk.W, padx=10)
        
        self.show_autoshow = tk.BooleanVar(value=self.config.get('show_autoshow', True))
        tk.Checkbutton(scroll_frame, text="Отображать кнопку автоскрытия", variable=self.show_autoshow).pack(anchor=tk.W, padx=10, pady=(10,0))
        
        self.hide_zone = tk.BooleanVar(value=self.config.get('hide_zone', True))
        tk.Checkbutton(scroll_frame, text="Скрытие зоны", variable=self.hide_zone).pack(anchor=tk.W, padx=10)
        
        tk.Label(scroll_frame, text="Непрозрачность зоны:").pack(anchor=tk.W, padx=10, pady=(10,0))
        self.zone_opacity = tk.Scale(scroll_frame, from_=10, to=100, orient=tk.HORIZONTAL, length=400)
        self.zone_opacity.set(self.config.get('zone_opacity', 50))
        self.zone_opacity.pack(anchor=tk.W, padx=10)
        
        tk.Label(scroll_frame, text="").pack(pady=30)
    
    def setup_about_tab(self, parent):
        tk.Label(parent, text="Скриптонайзер v.3.1", font=("Arial", 16, "bold")).pack(pady=20)
        tk.Label(parent, text="Персональная версия", font=("Arial", 10)).pack()
        tk.Label(parent, text="© 2026", font=("Arial", 8)).pack(pady=20)
        tk.Label(parent, text="Создано для удобной работы с шаблонами", font=("Arial", 9)).pack(pady=10)
    
    def save(self):
        config = {
            'line_spacing': self.line_spacing.get(),
            'btn_spacing': self.btn_spacing.get(),
            'rounding': self.rounding.get(),
            'scroll_speed': self.scroll_speed.get(),
            'copy_to_buffer': self.copy_to_buffer.get(),
            'show_toggle': self.show_toggle.get(),
            'always_on_top': self.always_on_top.get(),
            'drag_drop': self.drag_drop.get(),
            'show_hide': self.show_hide.get(),
            'show_add': self.show_add.get(),
            'add_at_end': self.add_at_end.get(),
            'show_search': self.show_search.get(),
            'show_hints': self.show_hints.get(),
            'show_editor': self.show_editor.get(),
            'use_groups': self.use_groups.get(),
            'groups_in_popup': int(self.groups_in_popup.get()),
            'show_fav_groups': self.show_fav_groups.get(),
            'fav_groups_count': int(self.fav_groups_count.get()),
            'search_hidden': self.search_hidden.get(),
            'show_timer': self.show_timer.get(),
            'timer_notify_time': int(self.timer_notify_time.get()),
            'timer_sound': self.timer_sound.get(),
            'show_autoshow': self.show_autoshow.get(),
            'hide_zone': self.hide_zone.get(),
            'zone_opacity': self.zone_opacity.get()
        }
        self.save_callback(config)
        messagebox.showinfo("Успех", "Настройки сохранены!")
        self.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = ScriptonizerApp(root)
    root.mainloop()
