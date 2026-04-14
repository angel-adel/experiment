import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import calendar
import os
import shutil
import subprocess
import sys

class WorkTimeTracker:
    def __init__(self, root):
        self.root = root
        self.root.title("Учет рабочего времени - от Димы (полная версия)")
        self.root.geometry("1200x700")
        
        self.editing_id = None
        
        # Проверяем и устанавливаем win32print для печати
        self.print_available = self.check_print_support()
        
        # Инициализация БД
        self.init_database()
        
        # Создаем интерфейс
        self.create_widgets()
    
    def check_print_support(self):
        """Проверяем поддержку печати с диалогом"""
        try:
            import win32print
            return True
        except ImportError:
            return False
    
    def install_print_support(self):
        """Устанавливаем поддержку печати"""
        try:
            import subprocess
            subprocess.run([sys.executable, '-m', 'pip', 'install', 'pywin32'], 
                         capture_output=True, text=True)
            messagebox.showinfo("Успех", 
                               "Библиотека для печати установлена.\n"
                               "Перезапустите программу для использования печати.")
            return True
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось установить:\n{e}")
            return False
        
    def init_database(self):
        """Создаем базу данных"""
        self.conn = sqlite3.connect('worktime.db')
        self.cursor = self.conn.cursor()
        
        # Таблица сотрудников
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                position TEXT,
                tab_number TEXT UNIQUE
            )
        ''')
        
        # Таблица смен
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS shifts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER,
                date TEXT,
                shift_type TEXT,
                hours REAL,
                FOREIGN KEY (employee_id) REFERENCES employees (id)
            )
        ''')
        
        self.conn.commit()
        
    def create_widgets(self):
        """Создаем элементы интерфейса"""
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Вкладка 1: Сотрудники
        self.employees_frame = ttk.Frame(notebook)
        notebook.add(self.employees_frame, text='👥 Сотрудники')
        self.create_employees_tab()
        
        # Вкладка 2: График
        self.schedule_frame = ttk.Frame(notebook)
        notebook.add(self.schedule_frame, text='📅 График')
        self.create_schedule_tab()
        
        # Вкладка 3: Табель
        self.timesheet_frame = ttk.Frame(notebook)
        notebook.add(self.timesheet_frame, text='📋 Табель')
        self.create_timesheet_tab()
        
    def create_employees_tab(self):
        """Вкладка сотрудников"""
        control_frame = ttk.Frame(self.employees_frame)
        control_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Label(control_frame, text="ФИО:").pack(side='left', padx=5)
        self.emp_name = ttk.Entry(control_frame, width=30)
        self.emp_name.pack(side='left', padx=5)
        
        ttk.Label(control_frame, text="Должность:").pack(side='left', padx=5)
        self.emp_position = ttk.Entry(control_frame, width=25)
        self.emp_position.pack(side='left', padx=5)
        
        ttk.Label(control_frame, text="Таб.№:").pack(side='left', padx=5)
        self.emp_tab = ttk.Entry(control_frame, width=10)
        self.emp_tab.pack(side='left', padx=5)
        
        ttk.Button(control_frame, text="➕ Добавить", command=self.add_employee).pack(side='left', padx=5)
        ttk.Button(control_frame, text="🗑 Удалить", command=self.delete_employee).pack(side='left', padx=5)
        
        columns = ('id', 'name', 'position', 'tab_number')
        self.emp_tree = ttk.Treeview(self.employees_frame, columns=columns, show='headings')
        
        self.emp_tree.heading('id', text='ID')
        self.emp_tree.heading('name', text='ФИО')
        self.emp_tree.heading('position', text='Должность')
        self.emp_tree.heading('tab_number', text='Таб.номер')
        
        self.emp_tree.column('id', width=50)
        self.emp_tree.column('name', width=250)
        self.emp_tree.column('position', width=200)
        self.emp_tree.column('tab_number', width=100)
        
        self.emp_tree.bind('<Double-1>', self.edit_employee)
        self.emp_tree.pack(fill='both', expand=True, padx=10, pady=10)
        
        ttk.Label(self.employees_frame, 
                 text="💡 Двойной клик по строке для редактирования", 
                 font=('Arial', 9), foreground='gray').pack(pady=5)
        
        # Панель архивации
        self.create_backup_panel()
        
    def create_backup_panel(self):
        """Панель резервного копирования"""
        backup_frame = ttk.LabelFrame(self.employees_frame, text="💾 Архив (резервное копирование)")
        backup_frame.pack(fill='x', padx=10, pady=5)
        
        btn_frame = ttk.Frame(backup_frame)
        btn_frame.pack(pady=5)
        
        ttk.Button(btn_frame, text="📀 Создать архив БД", command=self.backup_database).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="🔄 Восстановить из архива", command=self.restore_database).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="📂 Показать архивы", command=self.show_backups).pack(side='left', padx=5)
        
        self.backup_label = ttk.Label(backup_frame, text="", font=('Arial', 8), foreground='green')
        self.backup_label.pack(pady=2)
        
    def backup_database(self):
        """Создать резервную копию базы данных"""
        backup_dir = "Архивы"
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        
        timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        backup_name = f"worktime_{timestamp}.db"
        backup_path = os.path.join(backup_dir, backup_name)
        
        try:
            self.conn.close()
            shutil.copy2('worktime.db', backup_path)
            self.conn = sqlite3.connect('worktime.db')
            self.cursor = self.conn.cursor()
            
            self.backup_label.config(text=f"✅ Архив создан: {backup_name}", foreground='green')
            messagebox.showinfo("Успех", f"Резервная копия создана:\n{backup_path}")
        except Exception as e:
            self.backup_label.config(text=f"❌ Ошибка: {e}", foreground='red')
            messagebox.showerror("Ошибка", f"Не удалось создать архив:\n{e}")
            self.conn = sqlite3.connect('worktime.db')
            self.cursor = self.conn.cursor()
            
    def restore_database(self):
        """Восстановить базу из архива"""
        file_path = filedialog.askopenfilename(
            title="Выберите файл архива для восстановления",
            filetypes=[("База данных SQLite", "*.db"), ("Все файлы", "*.*")],
            initialdir="Архивы"
        )
        
        if not file_path:
            return
        
        confirm = messagebox.askyesno(
            "Восстановление", 
            "ВНИМАНИЕ! Текущие данные будут заменены данными из архива.\n\n"
            "Создать резервную копию текущих данных перед восстановлением?"
        )
        
        if confirm:
            self.backup_database()
        
        try:
            self.conn.close()
            shutil.copy2(file_path, 'worktime.db')
            self.conn = sqlite3.connect('worktime.db')
            self.cursor = self.conn.cursor()
            
            self.refresh_employees()
            self.backup_label.config(text=f"✅ Восстановлено из: {os.path.basename(file_path)}", foreground='blue')
            messagebox.showinfo("Успех", "База данных восстановлена!\nПереключитесь на другую вкладку и обратно для обновления.")
        except Exception as e:
            self.backup_label.config(text=f"❌ Ошибка: {e}", foreground='red')
            messagebox.showerror("Ошибка", f"Не удалось восстановить:\n{e}")
            self.conn = sqlite3.connect('worktime.db')
            self.cursor = self.conn.cursor()
            
    def show_backups(self):
        """Показать список архивов"""
        backup_dir = "Архивы"
        if not os.path.exists(backup_dir):
            messagebox.showinfo("Архивы", "Папка с архивами ещё не создана.\nСначала создайте резервную копию.")
            return
        
        backups = [f for f in os.listdir(backup_dir) if f.endswith('.db')]
        if not backups:
            messagebox.showinfo("Архивы", "Нет сохранённых архивов.")
            return
        
        backups.sort(reverse=True)
        
        list_window = tk.Toplevel(self.root)
        list_window.title("Список архивов")
        list_window.geometry("500x400")
        
        ttk.Label(list_window, text="Доступные резервные копии:", font=('Arial', 10, 'bold')).pack(pady=10)
        
        listbox = tk.Listbox(list_window, width=60, height=15)
        listbox.pack(padx=10, pady=5, fill='both', expand=True)
        
        for backup in backups:
            file_path = os.path.join(backup_dir, backup)
            size = os.path.getsize(file_path) / 1024
            listbox.insert('end', f"{backup}  ({size:.1f} КБ)")
        
        ttk.Label(list_window, text=f"Всего: {len(backups)} архивов", font=('Arial', 8)).pack(pady=5)
        ttk.Button(list_window, text="Закрыть", command=list_window.destroy).pack(pady=10)
        
    def add_employee(self):
        name = self.emp_name.get()
        position = self.emp_position.get()
        tab_num = self.emp_tab.get()
        
        if not name or not tab_num:
            messagebox.showwarning("Внимание", "Заполните ФИО и табельный номер!")
            return
        
        if self.editing_id:
            self.cursor.execute(
                'UPDATE employees SET name=?, position=?, tab_number=? WHERE id=?',
                (name, position, tab_num, self.editing_id)
            )
            self.conn.commit()
            messagebox.showinfo("Успех", "Данные сотрудника обновлены!")
            self.editing_id = None
        else:
            try:
                self.cursor.execute(
                    'INSERT INTO employees (name, position, tab_number) VALUES (?, ?, ?)',
                    (name, position, tab_num)
                )
                self.conn.commit()
                messagebox.showinfo("Успех", "Сотрудник добавлен!")
            except sqlite3.IntegrityError:
                messagebox.showerror("Ошибка", "Сотрудник с таким табельным номером уже существует!")
        
        self.emp_name.delete(0, 'end')
        self.emp_position.delete(0, 'end')
        self.emp_tab.delete(0, 'end')
        self.refresh_employees()
            
    def delete_employee(self):
        selected = self.emp_tree.selection()
        if not selected:
            messagebox.showwarning("Внимание", "Выберите сотрудника для удаления!")
            return
        
        item = self.emp_tree.item(selected[0])
        emp_id = item['values'][0]
        emp_name = item['values'][1]
        
        confirm = messagebox.askyesno("Подтверждение", 
                                     f"Удалить сотрудника '{emp_name}'?\n\n⚠️ Все данные о сменах также будут удалены!")
        
        if confirm:
            self.cursor.execute('DELETE FROM shifts WHERE employee_id = ?', (emp_id,))
            self.cursor.execute('DELETE FROM employees WHERE id = ?', (emp_id,))
            self.conn.commit()
            messagebox.showinfo("Успех", "Сотрудник удалён!")
            self.refresh_employees()
            
    def edit_employee(self, event):
        selected = self.emp_tree.selection()
        if not selected:
            return
        
        item = self.emp_tree.item(selected[0])
        emp_id = item['values'][0]
        
        self.emp_name.delete(0, 'end')
        self.emp_name.insert(0, item['values'][1])
        self.emp_position.delete(0, 'end')
        self.emp_position.insert(0, item['values'][2])
        self.emp_tab.delete(0, 'end')
        self.emp_tab.insert(0, item['values'][3])
        
        self.editing_id = emp_id
        
        messagebox.showinfo("Редактирование", 
                           "Измените данные и нажмите '➕ Добавить' для сохранения")
        
    def refresh_employees(self):
        for item in self.emp_tree.get_children():
            self.emp_tree.delete(item)
        
        self.cursor.execute('SELECT * FROM employees')
        for row in self.cursor.fetchall():
            self.emp_tree.insert('', 'end', values=row)
        
    def create_schedule_tab(self):
        control_frame = ttk.Frame(self.schedule_frame)
        control_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Label(control_frame, text="Месяц:").pack(side='left', padx=5)
        self.month_var = tk.StringVar(value=str(datetime.now().month))
        month_combo = ttk.Combobox(control_frame, textvariable=self.month_var, 
                                   values=[str(i) for i in range(1, 13)], width=5)
        month_combo.pack(side='left', padx=5)
        
        ttk.Label(control_frame, text="Год:").pack(side='left', padx=5)
        self.year_var = tk.StringVar(value=str(datetime.now().year))
        year_combo = ttk.Combobox(control_frame, textvariable=self.year_var,
                                  values=[str(y) for y in range(2024, 2030)], width=7)
        year_combo.pack(side='left', padx=5)
        
        ttk.Button(control_frame, text="📅 Загрузить график", 
                  command=self.load_schedule).pack(side='left', padx=10)
        
        ttk.Button(control_frame, text="💾 Сохранить", 
                  command=self.save_schedule).pack(side='left', padx=5)
        
        legend_frame = ttk.Frame(self.schedule_frame)
        legend_frame.pack(fill='x', padx=10, pady=5)
        
        colors = [
            ('#90EE90', 'Я - Явка'),
            ('#FFD700', 'Б - Больничный'),
            ('#FFA07A', 'ОТ - Отпуск'),
            ('#87CEEB', 'НД - Неявка'),
            ('white', 'В - Выходной'),
            ('#FF6B6B', 'УВ - Уволен')
        ]
        
        for color, text in colors:
            frame = ttk.Frame(legend_frame)
            frame.pack(side='left', padx=10)
            canvas = tk.Canvas(frame, width=20, height=20, bg=color)
            canvas.pack(side='left')
            ttk.Label(frame, text=text).pack(side='left', padx=5)
        
        schedule_frame = ttk.Frame(self.schedule_frame)
        schedule_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        h_scroll = ttk.Scrollbar(schedule_frame, orient='horizontal')
        v_scroll = ttk.Scrollbar(schedule_frame, orient='vertical')
        
        columns = ('emp',) + tuple(str(i) for i in range(1, 32))
        self.schedule_tree = ttk.Treeview(schedule_frame, columns=columns, 
                                          show='headings', yscrollcommand=v_scroll.set,
                                          xscrollcommand=h_scroll.set, height=20)
        
        h_scroll.config(command=self.schedule_tree.xview)
        v_scroll.config(command=self.schedule_tree.yview)
        
        self.schedule_tree.heading('emp', text='Сотрудник')
        for i in range(1, 32):
            self.schedule_tree.heading(str(i), text=str(i))
            self.schedule_tree.column(str(i), width=45, anchor='center')
        
        self.schedule_tree.column('emp', width=300)
        
        self.schedule_tree.grid(row=0, column=0, sticky='nsew')
        v_scroll.grid(row=0, column=1, sticky='ns')
        h_scroll.grid(row=1, column=0, sticky='ew')
        
        schedule_frame.grid_rowconfigure(0, weight=1)
        schedule_frame.grid_columnconfigure(0, weight=1)
        
        self.schedule_tree.tag_configure('shift_Я', background='#90EE90')
        self.schedule_tree.tag_configure('shift_В', background='white')
        self.schedule_tree.tag_configure('shift_ОТ', background='#FFA07A')
        self.schedule_tree.tag_configure('shift_Б', background='#FFD700')
        self.schedule_tree.tag_configure('shift_НД', background='#87CEEB')
        self.schedule_tree.tag_configure('shift_УВ', background='#FF6B6B')
        self.schedule_tree.tag_configure('shift_', background='white')
        
        self.schedule_tree.bind('<Button-3>', self.on_right_click)
        
        self.current_month = datetime.now().month
        self.current_year = datetime.now().year
        
    def load_schedule(self):
        try:
            self.current_month = int(self.month_var.get())
            self.current_year = int(self.year_var.get())
        except:
            messagebox.showerror("Ошибка", "Неверный формат месяца или года!")
            return
        
        for item in self.schedule_tree.get_children():
            self.schedule_tree.delete(item)
        
        days_in_month = calendar.monthrange(self.current_year, self.current_month)[1]
        
        self.cursor.execute('SELECT id, name, position, tab_number FROM employees')
        employees = self.cursor.fetchall()
        
        if not employees:
            messagebox.showinfo("Инфо", "Сначала добавьте сотрудников!")
            return
        
        for emp in employees:
            emp_id, name, position, tab_num = emp
            emp_display = f"{name} (таб. {tab_num})"
            
            shifts = {}
            self.cursor.execute('''
                SELECT date, shift_type FROM shifts 
                WHERE employee_id = ? AND date LIKE ?
            ''', (emp_id, f"{self.current_year}-{self.current_month:02d}%"))
            
            for shift in self.cursor.fetchall():
                day = int(shift[0].split('-')[2])
                shifts[day] = shift[1]
            
            values = [emp_display]
            for day in range(1, 32):
                if day <= days_in_month and day in shifts:
                    values.append(shifts[day])
                else:
                    values.append('')
            
            self.schedule_tree.insert('', 'end', values=values)
        
        self.apply_colors()
        messagebox.showinfo("Успех", f"Загружено {len(employees)} сотрудников")
        
    def apply_colors(self):
        for item in self.schedule_tree.get_children():
            values = self.schedule_tree.item(item)['values']
            shifts_count = {}
            for day_idx in range(1, len(values)):
                shift = values[day_idx]
                if shift and shift != '':
                    shifts_count[shift] = shifts_count.get(shift, 0) + 1
            
            if shifts_count:
                main_shift = max(shifts_count, key=shifts_count.get)
                tag = f'shift_{main_shift}'
                self.schedule_tree.item(item, tags=(tag,))
            else:
                self.schedule_tree.item(item, tags=('shift_',))
    
    def on_right_click(self, event):
        item = self.schedule_tree.identify_row(event.y)
        column = self.schedule_tree.identify_column(event.x)
        
        if not item or not column:
            return
        
        col_num = int(column[1:])
        
        if col_num == 1:
            return
        
        day = col_num - 1
        
        days_in_month = calendar.monthrange(self.current_year, self.current_month)[1]
        if day < 1 or day > days_in_month:
            return
        
        self.show_shift_menu(item, column, day)
        
    def show_shift_menu(self, item, column, day):
        menu = tk.Menu(self.root, tearoff=0)
        
        shifts = ['Я', 'В', 'ОТ', 'Б', 'НД', 'УВ', '']
        for shift in shifts:
            label = shift if shift else 'Очистить'
            menu.add_command(
                label=label, 
                command=lambda s=shift, it=item, d=day: self.set_shift(it, d, s)
            )
        
        menu.post(self.root.winfo_pointerx(), self.root.winfo_pointery())
        
    def set_shift(self, item, day, shift_type):
        values = list(self.schedule_tree.item(item)['values'])
        if day < len(values):
            values[day] = shift_type
            self.schedule_tree.item(item, values=values)
        
        self.apply_colors()
        
    def save_schedule(self):
        saved_count = 0
        
        for item in self.schedule_tree.get_children():
            values = self.schedule_tree.item(item)['values']
            emp_display = values[0]
            
            tab_num = emp_display.split('(таб. ')[1].replace(')', '') if '(таб. ' in emp_display else ''
            
            self.cursor.execute('SELECT id FROM employees WHERE tab_number = ?', (tab_num,))
            result = self.cursor.fetchone()
            if not result:
                continue
            
            emp_id = result[0]
            
            for day in range(1, 32):
                if day < len(values):
                    shift_type = values[day]
                    if shift_type:
                        hours = 8 if shift_type == 'Я' else 0
                        date = f"{self.current_year}-{self.current_month:02d}-{day:02d}"
                        
                        self.cursor.execute('''
                            SELECT id FROM shifts 
                            WHERE employee_id = ? AND date = ?
                        ''', (emp_id, date))
                        
                        existing = self.cursor.fetchone()
                        
                        if existing:
                            self.cursor.execute('''
                                UPDATE shifts SET shift_type = ?, hours = ?
                                WHERE employee_id = ? AND date = ?
                            ''', (shift_type, hours, emp_id, date))
                        else:
                            self.cursor.execute('''
                                INSERT INTO shifts (employee_id, date, shift_type, hours)
                                VALUES (?, ?, ?, ?)
                            ''', (emp_id, date, shift_type, hours))
                        
                        saved_count += 1
        
        self.conn.commit()
        messagebox.showinfo("Успех", f"Сохранено {saved_count} записей!")
    
    def create_timesheet_tab(self):
        control_frame = ttk.Frame(self.timesheet_frame)
        control_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Label(control_frame, text="Месяц:").pack(side='left', padx=5)
        self.ts_month_var = tk.StringVar(value=str(datetime.now().month))
        month_combo = ttk.Combobox(control_frame, textvariable=self.ts_month_var, 
                                   values=[str(i) for i in range(1, 13)], width=5)
        month_combo.pack(side='left', padx=5)
        
        ttk.Label(control_frame, text="Год:").pack(side='left', padx=5)
        self.ts_year_var = tk.StringVar(value=str(datetime.now().year))
        year_combo = ttk.Combobox(control_frame, textvariable=self.ts_year_var,
                                  values=[str(y) for y in range(2024, 2030)], width=7)
        year_combo.pack(side='left', padx=5)
        
        ttk.Button(control_frame, text="📋 Сформировать табель", 
                  command=self.generate_timesheet).pack(side='left', padx=10)
        
        ttk.Button(control_frame, text="💾 Экспорт в Excel", 
                  command=self.export_to_excel).pack(side='left', padx=5)
        
        ttk.Button(control_frame, text="🖨️ Печать", 
                  command=self.print_timesheet).pack(side='left', padx=5)
        
        preview_frame = ttk.LabelFrame(self.timesheet_frame, text="Предпросмотр")
        preview_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.timesheet_text = tk.Text(preview_frame, font=('Courier New', 10))
        self.timesheet_text.pack(fill='both', expand=True, padx=5, pady=5)
        
        scrollbar = ttk.Scrollbar(self.timesheet_text, command=self.timesheet_text.yview)
        scrollbar.pack(side='right', fill='y')
        self.timesheet_text.config(yscrollcommand=scrollbar.set)
    
    def generate_timesheet(self):
        try:
            month = int(self.ts_month_var.get())
            year = int(self.ts_year_var.get())
        except:
            messagebox.showerror("Ошибка", "Неверный формат месяца или года!")
            return
        
        self.timesheet_text.delete('1.0', 'end')
        
        header = f"ТАБЕЛЬ учета рабочего времени\n"
        header += f"Месяц: {month:02d}/{year}\n"
        header += "=" * 100 + "\n\n"
        
        self.timesheet_text.insert('1.0', header)
        
        self.cursor.execute('SELECT id, name, tab_number, position FROM employees ORDER BY name')
        employees = self.cursor.fetchall()
        
        if not employees:
            messagebox.showinfo("Инфо", "Нет сотрудников в базе!")
            return
        
        line_num = 1
        total_days = 0
        total_hours = 0
        
        for emp in employees:
            emp_id, name, tab_num, position = emp
            
            self.cursor.execute('''
                SELECT shift_type, hours FROM shifts 
                WHERE employee_id = ? AND date LIKE ?
            ''', (emp_id, f"{year}-{month:02d}%"))
            
            shifts = self.cursor.fetchall()
            
            days_worked = sum(1 for s in shifts if s[0] == 'Я')
            hours_worked = sum(s[1] for s in shifts if s[0] == 'Я')
            sick_days = sum(1 for s in shifts if s[0] == 'Б')
            vacation_days = sum(1 for s in shifts if s[0] == 'ОТ')
            
            line = f"{line_num:3}. {name:<30} Таб.№:{tab_num:<6} "
            line += f"Я:{days_worked:2}д/{hours_worked:3}ч "
            line += f"Б:{sick_days:2}д ОТ:{vacation_days:2}д\n"
            
            self.timesheet_text.insert('end', line)
            
            total_days += days_worked
            total_hours += hours_worked
            line_num += 1
        
        footer = "\n" + "=" * 100 + "\n"
        footer += f"ИТОГО: {line_num-1} сотрудников, {total_days} явочных дней, {total_hours} часов\n"
        footer += "=" * 100 + "\n\n"
        footer += "Руководитель: ___________________    Дата: ___________\n\n"
        footer += "Ответственное лицо: _______________    Дата: ___________\n"
        
        self.timesheet_text.insert('end', footer)
        
        messagebox.showinfo("Успех", "Табель сформирован!")
    
    def export_to_excel(self):
        try:
            from openpyxl import Workbook
        except ImportError:
            messagebox.showerror("Ошибка", "Установите openpyxl: pip install openpyxl")
            return
        
        try:
            month = int(self.ts_month_var.get())
            year = int(self.ts_year_var.get())
        except:
            messagebox.showerror("Ошибка", "Неверный формат месяца или года!")
            return
        
        wb = Workbook()
        ws = wb.active
        ws.title = f"Табель {month:02d}-{year}"
        
        headers = ['№', 'ФИО', 'Таб.№', 'Должность', 'Явка (дней)', 
                  'Явка (часов)', 'Больничный', 'Отпуск', 'Примечание']
        ws.append(headers)
        
        self.cursor.execute('SELECT id, name, tab_number, position FROM employees ORDER BY name')
        employees = self.cursor.fetchall()
        
        line_num = 1
        for emp in employees:
            emp_id, name, tab_num, position = emp
            
            self.cursor.execute('''
                SELECT shift_type, hours FROM shifts 
                WHERE employee_id = ? AND date LIKE ?
            ''', (emp_id, f"{year}-{month:02d}%"))
            
            shifts = self.cursor.fetchall()
            
            days_worked = sum(1 for s in shifts if s[0] == 'Я')
            hours_worked = sum(s[1] for s in shifts if s[0] == 'Я')
            sick_days = sum(1 for s in shifts if s[0] == 'Б')
            vacation_days = sum(1 for s in shifts if s[0] == 'ОТ')
            
            ws.append([line_num, name, tab_num, position, days_worked, 
                      hours_worked, sick_days, vacation_days, ''])
            
            line_num += 1
        
        filename = f"Табель_{year}_{month:02d}.xlsx"
        wb.save(filename)
        
        messagebox.showinfo("Успех", f"Табель экспортирован в файл:\n{filename}")
    
    def print_timesheet(self):
        """Печать текущего табеля с диалогом выбора принтера"""
        content = self.timesheet_text.get('1.0', 'end')
        if not content.strip():
            messagebox.showwarning("Внимание", "Сначала сформируйте табель!")
            return
        
        # Проверяем наличие поддержки печати
        if not self.print_available:
            result = messagebox.askyesno(
                "Требуется установка",
                "Для печати с выбором принтера необходимо установить компоненты.\n\n"
                "Установить сейчас? (потребуется интернет)"
            )
            if result:
                if self.install_print_support():
                    self.print_available = self.check_print_support()
                    if self.print_available:
                        messagebox.showinfo("Готово", "Перезапустите программу для печати.")
                return
            else:
                # Запасной вариант - открыть в блокноте
                temp_file = os.path.join(os.getenv('TEMP'), 'timesheet_print.txt')
                with open(temp_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                os.startfile(temp_file)
                messagebox.showinfo("Печать", 
                                   "Открыт временный файл. Нажмите Ctrl+P, выберите принтер и распечатайте.\n\n"
                                   "Файл будет удалён через 1 минуту.")
                self.root.after(60000, lambda: os.remove(temp_file) if os.path.exists(temp_file) else None)
                return
        
        # Основной вариант с диалогом выбора принтера
        try:
            import win32print
            import win32ui
            
            # Создаём временный файл
            temp_file = os.path.join(os.getenv('TEMP'), 'timesheet_print.txt')
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Показываем диалог выбора принтера
            printer_name = None
            try:
                dlg = win32ui.CreatePrintDialog()
                dlg.DoModal()
                printer_info = dlg.GetPrinterDevice()
                if printer_info:
                    printer_name = printer_info[2]
            except:
                pass
            
            if not printer_name:
                # Берём принтер по умолчанию
                printer_name = win32print.GetDefaultPrinter()
                if not printer_name:
                    messagebox.showerror("Ошибка", "Принтер не найден!")
                    return
            
            # Печатаем
            with open(temp_file, 'r', encoding='utf-8') as f:
                text = f.read()
            
            hprinter = win32print.OpenPrinter(printer_name)
            try:
                win32print.StartDocPrinter(hprinter, 1, ("Табель рабочего времени", None, "RAW"))
                win32print.StartPagePrinter(hprinter)
                win32print.WritePrinter(hprinter, text.encode('cp1251', errors='replace'))
                win32print.EndPagePrinter(hprinter)
                win32print.EndDocPrinter(hprinter)
            finally:
                win32print.ClosePrinter(hprinter)
            
            # Удаляем временный файл
            os.remove(temp_file)
            
            messagebox.showinfo("Успех", f"Документ отправлен на печать:\n{printer_name}")
            
        except Exception as e:
            messagebox.showerror("Ошибка печати", f"Не удалось распечатать:\n{e}")
            # Запасной вариант
            temp_file = os.path.join(os.getenv('TEMP'), 'timesheet_print.txt')
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(content)
            os.startfile(temp_file)
            messagebox.showinfo("Печать", 
                               "Открыт временный файл. Нажмите Ctrl+P, выберите принтер и распечатайте.")

def main():
    root = tk.Tk()
    app = WorkTimeTracker(root)
    root.mainloop()

if __name__ == "__main__":
    main()
