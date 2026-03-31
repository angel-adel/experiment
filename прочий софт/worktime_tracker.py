import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
import calendar

class WorkTimeTracker:
    def __init__(self, root):
        self.root = root
        self.root.title("Учет рабочего времени - от Димы")
        self.root.geometry("1200x700")
        
        # Инициализация БД
        self.editing_id = None
        self.init_database()
        
        # Создаем интерфейс
        self.create_widgets()
        
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
        # Вкладки
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
        # Панель управления
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
        
        # Таблица сотрудников
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
        
        # Двойной клик для редактирования
        self.emp_tree.bind('<Double-1>', self.edit_employee)
        
        self.emp_tree.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Подсказка
        ttk.Label(self.employees_frame, 
                 text="💡 Двойной клик по строке для редактирования", 
                 font=('Arial', 9), foreground='gray').pack(pady=5)
        
        self.refresh_employees()
        
    def add_employee(self):
        """Добавить сотрудника"""
        name = self.emp_name.get()
        position = self.emp_position.get()
        tab_num = self.emp_tab.get()
        
        if not name or not tab_num:
            messagebox.showwarning("Внимание", "Заполните ФИО и табельный номер!")
            return
        
        # Если редактируем - обновляем запись
        if hasattr(self, 'editing_id') and self.editing_id:
            self.cursor.execute(
                'UPDATE employees SET name=?, position=?, tab_number=? WHERE id=?',
                (name, position, tab_num, self.editing_id)
            )
            self.conn.commit()
            messagebox.showinfo("Успех", "Данные сотрудника обновлены!")
            self.editing_id = None
        else:
            # Иначе добавляем нового
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
        """Удалить сотрудника"""
        selected = self.emp_tree.selection()
        if not selected:
            messagebox.showwarning("Внимание", "Выберите сотрудника для удаления!")
            return
        
        # Получаем данные выбранного сотрудника
        item = self.emp_tree.item(selected[0])
        emp_id = item['values'][0]
        emp_name = item['values'][1]
        
        # Подтверждение
        confirm = messagebox.askyesno("Подтверждение", 
                                     f"Удалить сотрудника '{emp_name}'?\n\n"
                                     f"⚠️ Все данные о сменах также будут удалены!")
        
        if confirm:
            # Удаляем сначала смены, потом сотрудника
            self.cursor.execute('DELETE FROM shifts WHERE employee_id = ?', (emp_id,))
            self.cursor.execute('DELETE FROM employees WHERE id = ?', (emp_id,))
            self.conn.commit()
            messagebox.showinfo("Успех", "Сотрудник удалён!")
            self.refresh_employees()
            
    def edit_employee(self, event):
        """Редактирование сотрудника (двойной клик)"""
        selected = self.emp_tree.selection()
        if not selected:
            return
        
        item = self.emp_tree.item(selected[0])
        emp_id = item['values'][0]
        
        # Заполняем поля текущими данными
        self.emp_name.delete(0, 'end')
        self.emp_name.insert(0, item['values'][1])
        self.emp_position.delete(0, 'end')
        self.emp_position.insert(0, item['values'][2])
        self.emp_tab.delete(0, 'end')
        self.emp_tab.insert(0, item['values'][3])
        
        # Сохраняем ID для обновления
        self.editing_id = emp_id
        
        messagebox.showinfo("Редактирование", 
                           "Измените данные и нажмите '➕ Добавить' для сохранения")
        
    def refresh_employees(self):
        """Обновить список сотрудников"""
        for item in self.emp_tree.get_children():
            self.emp_tree.delete(item)
        
        self.cursor.execute('SELECT * FROM employees')
        for row in self.cursor.fetchall():
            self.emp_tree.insert('', 'end', values=row)
    def create_schedule_tab(self):
        """Вкладка графика"""
        # Выбор месяца
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
        
        # Легенда
        legend_frame = ttk.Frame(self.schedule_frame)
        legend_frame.pack(fill='x', padx=10, pady=5)
        
        colors = [
            ('#90EE90', 'Я - Явка'),
            ('#FFD700', 'Б - Больничный'),
            ('#FFA07A', 'ОТ - Отпуск'),
            ('#87CEEB', 'НД - Неявка'),
            ('white', 'В - Выходной')
        ]
        
        for color, text in colors:
            frame = ttk.Frame(legend_frame)
            frame.pack(side='left', padx=10)
            canvas = tk.Canvas(frame, width=20, height=20, bg=color)
            canvas.pack(side='left')
            ttk.Label(frame, text=text).pack(side='left', padx=5)
        
        # Сетка графика
        schedule_frame = ttk.Frame(self.schedule_frame)
        schedule_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Создаем скроллбары
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
        
        # Привязка события изменения ячейки
        self.schedule_tree.bind('<Double-1>', self.on_cell_double_click)
        
        # Типы смен и их цвета
        self.shift_types = {
            '': 'white',
            'Я': '#90EE90',      # светло-зеленый
            'В': 'white',         # белый
            'ОТ': '#FFA07A',      # светло-красный
            'Б': '#FFD700',       # желтый
            'НД': '#87CEEB',      # голубой
            'УВ': '#FF6B6B'       # красный (уволен)
        }
        
        self.current_month = datetime.now().month
        self.current_year = datetime.now().year
        
    def load_schedule(self):
        """Загрузить график сотрудников"""
        try:
            self.current_month = int(self.month_var.get())
            self.current_year = int(self.year_var.get())
        except:
            messagebox.showerror("Ошибка", "Неверный формат месяца или года!")
            return
        
        # Очищаем таблицу
        for item in self.schedule_tree.get_children():
            self.schedule_tree.delete(item)
        
        # Получаем количество дней в месяце
        days_in_month = calendar.monthrange(self.current_year, self.current_month)[1]
        
        # Загружаем сотрудников
        self.cursor.execute('SELECT id, name, position, tab_number FROM employees')
        employees = self.cursor.fetchall()
        
        if not employees:
            messagebox.showinfo("Инфо", "Сначала добавьте сотрудников!")
            return
        
        # Создаем строки для каждого сотрудника
        for emp in employees:
            emp_id, name, position, tab_num = emp
            emp_display = f"{name} (таб. {tab_num})"
            
            # Загружаем существующие смены
            shifts = {}
            self.cursor.execute('''
                SELECT date, shift_type, hours FROM shifts 
                WHERE employee_id = ? AND date LIKE ?
            ''', (emp_id, f"{self.current_year}-{self.current_month:02d}%"))
            
            for shift in self.cursor.fetchall():
                day = int(shift[0].split('-')[2])
                shifts[day] = (shift[1], shift[2])
            
            # Создаем значения для строки
            values = [emp_display]
            for day in range(1, 32):
                if day <= days_in_month and day in shifts:
                    values.append(shifts[day][0])  # тип смены
                else:
                    values.append('')
            
            item_id = self.schedule_tree.insert('', 'end', values=values, tags=(str(emp_id),))
            
            # Применяем цвета
            for day in range(1, 32):
                if day <= days_in_month:
                    shift_type = values[day] if day < len(values) else ''
                    color = self.shift_types.get(shift_type, 'white')
                    self.schedule_tree.item(item_id, tags=(str(emp_id),))
        
        # Применяем цвета после вставки
        self.apply_colors()
        
        messagebox.showinfo("Успех", f"Загружено {len(employees)} сотрудников")
        
    def apply_colors(self):
        """Применить цветовую заливку к ячейкам"""
        for item in self.schedule_tree.get_children():
            values = self.schedule_tree.item(item)['values']
            for day in range(1, 32):
                if day < len(values):
                    shift_type = values[day]
                    color = self.shift_types.get(shift_type, 'white')
                    # Сохраняем цвет в тегах
                    tags = self.schedule_tree.item(item)['tags']
                    self.schedule_tree.item(item, tags=tags)
    
    def on_cell_double_click(self, event):
        """Обработка двойного клика по ячейке"""
        region = self.schedule_tree.identify("region", event.x, event.y)
        if region != "cell":
            return
        
        item = self.schedule_tree.identify_row(event.y)
        column = self.schedule_tree.identify_column(event.x)
        
        if not item or not column:
            return
        
        # Получаем номер дня (колонка)
        col_num = int(column.replace('#', ''))
        if col_num == 1:  # первая колонка - имя
            return
        
        # Показываем меню выбора смены
        self.show_shift_menu(item, column, col_num)
        
    def show_shift_menu(self, item, column, day):
        """Показать меню выбора типа смены"""
        menu = tk.Menu(self.root, tearoff=0)
        
        shifts = ['Я', 'В', 'ОТ', 'Б', 'НД', 'УВ', '']
        for shift in shifts:
            color = self.shift_types.get(shift, 'white')
            menu.add_command(label=f"{shift if shift else 'Очистить'}", 
                           command=lambda s=shift: self.set_shift(item, column, day, s))
        
        menu.post(self.root.winfo_pointerx(), self.root.winfo_pointery())
        
    def set_shift(self, item, column, day, shift_type):
        """Установить тип смены"""
        # Обновляем значение в таблице
        values = list(self.schedule_tree.item(item)['values'])
        if day < len(values):
            values[day] = shift_type
            self.schedule_tree.item(item, values=values)
        
        # Применяем цвет
        self.apply_colors()
        
    def save_schedule(self):
        """Сохранить график в базу данных"""
        saved_count = 0
        
        for item in self.schedule_tree.get_children():
            values = self.schedule_tree.item(item)['values']
            emp_display = values[0]
            
            # Извлекаем табельный номер
            tab_num = emp_display.split('(таб. ')[1].replace(')', '') if '(таб. ' in emp_display else ''
            
            # Находим сотрудника в БД
            self.cursor.execute('SELECT id FROM employees WHERE tab_number = ?', (tab_num,))
            result = self.cursor.fetchone()
            if not result:
                continue
            
            emp_id = result[0]
            
            # Сохраняем смены
            for day in range(1, 32):
                if day < len(values):
                    shift_type = values[day]
                    if shift_type:  # если не пустая ячейка
                        # Определяем часы (пока ставим 8 для явки, 0 для остальных)
                        hours = 8 if shift_type == 'Я' else 0
                        
                        date = f"{self.current_year}-{self.current_month:02d}-{day:02d}"
                        
                        # Проверяем, есть ли уже запись
                        self.cursor.execute('''
                            SELECT id FROM shifts 
                            WHERE employee_id = ? AND date = ?
                        ''', (emp_id, date))
                        
                        existing = self.cursor.fetchone()
                        
                        if existing:
                            # Обновляем
                            self.cursor.execute('''
                                UPDATE shifts SET shift_type = ?, hours = ?
                                WHERE employee_id = ? AND date = ?
                            ''', (shift_type, hours, emp_id, date))
                        else:
                            # Добавляем
                            self.cursor.execute('''
                                INSERT INTO shifts (employee_id, date, shift_type, hours)
                                VALUES (?, ?, ?, ?)
                            ''', (emp_id, date, shift_type, hours))
                        
                        saved_count += 1
        
        self.conn.commit()
        messagebox.showinfo("Успех", f"Сохранено {saved_count} записей!")
def main():
    root = tk.Tk()
    app = WorkTimeTracker(root)
    root.mainloop()

if __name__ == "__main__":
    main()
