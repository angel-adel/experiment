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
        
        ttk.Button(control_frame, text="Загрузить", command=self.load_schedule).pack(side='left', padx=10)
        
        # Сетка графика
        schedule_frame = ttk.Frame(self.schedule_frame)
        schedule_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Создаем скроллбары
        h_scroll = ttk.Scrollbar(schedule_frame, orient='horizontal')
        v_scroll = ttk.Scrollbar(schedule_frame, orient='vertical')
        
        columns = ('emp',) + tuple(str(i) for i in range(1, 32))
        self.schedule_tree = ttk.Treeview(schedule_frame, columns=columns, 
                                          show='headings', yscrollcommand=v_scroll.set,
                                          xscrollcommand=h_scroll.set)
        
        h_scroll.config(command=self.schedule_tree.xview)
        v_scroll.config(command=self.schedule_tree.yview)
        
        self.schedule_tree.heading('emp', text='Сотрудник')
        for i in range(1, 32):
            self.schedule_tree.heading(str(i), text=str(i))
            self.schedule_tree.column(str(i), width=40)
        
        self.schedule_tree.column('emp', width=250)
        
        self.schedule_tree.grid(row=0, column=0, sticky='nsew')
        v_scroll.grid(row=0, column=1, sticky='ns')
        h_scroll.grid(row=1, column=0, sticky='ew')
        
        schedule_frame.grid_rowconfigure(0, weight=1)
        schedule_frame.grid_columnconfigure(0, weight=1)
        
        # Типы смен
        self.shift_types = ['Я', 'В', 'ОТ', 'Б', 'НД', '']    
    def load_schedule(self):
        """Загрузить график"""
        messagebox.showinfo("Инфо", "Здесь будет загрузка графика!\nПока просто прототип.")
        # Здесь будет логика загрузки
        
    def create_timesheet_tab(self):
        """Вкладка табеля"""
        ttk.Label(self.timesheet_frame, 
                 text="Здесь будет автоматическая генерация табеля",
                 font=('Arial', 12)).pack(pady=50)
        
        ttk.Button(self.timesheet_frame, text="Сформировать табель", 
                  command=self.generate_timesheet).pack(pady=10)
        
    def generate_timesheet(self):
        """Сгенерировать табель"""
        messagebox.showinfo("Инфо", "Табель будет сформирован здесь!")

def main():
    root = tk.Tk()
    app = WorkTimeTracker(root)
    root.mainloop()

if __name__ == "__main__":
    main()
