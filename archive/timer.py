import tkinter as tk
from tkinter import messagebox, simpledialog
from datetime import datetime, timedelta
import winsound
import json
import os

CONFIG_FILE = "timer_config.json"

class SimpleTimer:
    def __init__(self, root):
        self.root = root
        self.root.title("Таймер смены")
        self.root.geometry("400x200")
        self.root.resizable(False, False)
        
        self.remaining_seconds = 0
        self.is_running = False
        self.timer_id = None
        
        # Загрузка настроек
        self.config = self.load_config()
        
        self.setup_ui()
        
        # Если есть сохранённое время — загружаем
        if self.config.get('remaining_seconds', 0) > 0:
            self.remaining_seconds = self.config['remaining_seconds']
            self.is_running = True
            self.update_display()
            self.start_timer()
    
    def setup_ui(self):
        # Заголовок
        self.title_label = tk.Label(self.root, text="Осталось работать", 
                                   font=("Arial", 14, "bold"))
        self.title_label.pack(pady=10)
        
        # Таймер (большими цифрами)
        self.time_label = tk.Label(self.root, text="00:00:00", 
                                  font=("Courier New", 48, "bold"),
                                  fg="black")
        self.time_label.pack(pady=10)
        
        # Кнопки
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=15)
        
        tk.Button(btn_frame, text="⚙️ Настройки", command=self.open_settings,
                 width=12, height=2).pack(side=tk.LEFT, padx=10)
        
        tk.Button(btn_frame, text="➖ Свернуть", command=self.minimize,
                 width=12, height=2).pack(side=tk.LEFT, padx=10)
        
        tk.Button(btn_frame, text="❌ Выход", command=self.exit_app,
                 width=12, height=2, bg="#f44336", fg="white").pack(side=tk.LEFT, padx=10)
    
    def update_display(self):
        """Обновление отображения времени"""
        if self.remaining_seconds <= 0:
            self.time_label.config(text="ДОМОЙ!", fg="red")
            self.title_label.config(text="")
            # Звуковой сигнал
            if self.config.get('sound', True):
                for _ in range(3):
                    winsound.MessageBeep()
            messagebox.showinfo("⏰ Время!", "Смена окончена! ДОМОЙ! 🏠")
            return
        
        hours = self.remaining_seconds // 3600
        minutes = (self.remaining_seconds % 3600) // 60
        seconds = self.remaining_seconds % 60
        
        time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        self.time_label.config(text=time_str, fg="black")
    
    def start_timer(self):
        """Запуск таймера"""
        if self.remaining_seconds > 0:
            self.remaining_seconds -= 1
            self.update_display()
            self.save_config()
            self.timer_id = self.root.after(1000, self.start_timer)
    
    def open_settings(self):
        """Открытие настроек"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Настройки таймера")
        dialog.geometry("300x150")
        dialog.resizable(False, False)
        
        tk.Label(dialog, text="Окончание работы в", font=("Arial", 10)).pack(pady=5)
        
        # Часы и минуты
        time_frame = tk.Frame(dialog)
        time_frame.pack(pady=10)
        
        tk.Label(time_frame, text="Часы:").pack(side=tk.LEFT, padx=5)
        hours_spin = tk.Spinbox(time_frame, from_=0, to=23, width=5)
        hours_spin.delete(0, tk.END)
        hours_spin.insert(0, str(self.config.get('hours', 0)))
        hours_spin.pack(side=tk.LEFT, padx=5)
        
        tk.Label(time_frame, text="Мин:").pack(side=tk.LEFT, padx=5)
        mins_spin = tk.Spinbox(time_frame, from_=0, to=59, width=5)
        mins_spin.delete(0, tk.END)
        mins_spin.insert(0, str(self.config.get('minutes', 0)))
        mins_spin.pack(side=tk.LEFT, padx=5)
        
        # Звук
        sound_var = tk.BooleanVar(value=self.config.get('sound', True))
        tk.Checkbutton(dialog, text="Звуковое уведомление", variable=sound_var).pack(pady=5)
        
        def save_settings():
            try:
                hours = int(hours_spin.get())
                minutes = int(mins_spin.get())
                
                # Рассчитываем время до окончания
                now = datetime.now()
                end_time = now.replace(hour=hours, minute=minutes, second=0)
                
                # Если время уже прошло — ставим на завтра
                if end_time <= now:
                    end_time += timedelta(days=1)
                
                delta = end_time - now
                self.remaining_seconds = int(delta.total_seconds())
                
                self.config['hours'] = hours
                self.config['minutes'] = minutes
                self.config['sound'] = sound_var.get()
                
                self.is_running = True
                self.update_display()
                self.start_timer()
                self.save_config()
                
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Ошибка", f"Неверные данные: {e}")
        
        btn_frame = tk.Frame(dialog)
        btn_frame.pack(pady=10)
        
        tk.Button(btn_frame, text="✓ OK", command=save_settings, 
                 bg="#4CAF50", fg="white", width=10).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text="✗ Отмена", command=dialog.destroy, 
                 bg="#f44336", fg="white", width=10).pack(side=tk.LEFT, padx=10)
    
    def minimize(self):
        """Свернуть окно"""
        self.root.iconify()
    
    def exit_app(self):
        """Выход из программы"""
        if messagebox.askyesno("Выход", "Закрыть таймер?"):
            if self.timer_id:
                self.root.after_cancel(self.timer_id)
            self.save_config()
            self.root.destroy()
    
    def save_config(self):
        """Сохранение настроек"""
        self.config['remaining_seconds'] = self.remaining_seconds
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)
    
    def load_config(self):
        """Загрузка настроек"""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {'hours': 0, 'minutes': 0, 'sound': True, 'remaining_seconds': 0}
        return {'hours': 0, 'minutes': 0, 'sound': True, 'remaining_seconds': 0}

if __name__ == "__main__":
    root = tk.Tk()
    app = SimpleTimer(root)
    root.mainloop()
