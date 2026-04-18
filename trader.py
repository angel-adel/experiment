import tkinter as tk
from tkinter import ttk
import random
import math

class TraderSimulator:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("📈 Симулятор трейдера")
        self.root.geometry("650x750")
        self.root.configure(bg='#0a0f1c')
        self.root.resizable(False, False)
        
        # Переменные
        self.balance = 10000
        self.shares = 0
        self.start_capital = 10000
        self.current_price = 100.0
        self.price_history = [100.0]
        self.is_running = True
        self.last_price = 100.0
        
        # Параметры генерации
        self.trend_cycle = 0
        self.trend_strength = 0
        self.current_trend = "floating"
        self.volatility = 2
        
        # Скорость обновления (в секундах)
        self.update_interval = 3000  # миллисекунды, по умолчанию 3 сек
        self.update_job = None
        
        # Создаём интерфейс
        self.setup_ui()
        
        # Запускаем обновление цены
        self.root.after(1000, self.first_update)
        
        self.root.mainloop()
    
    def setup_ui(self):
        # График
        self.canvas = tk.Canvas(self.root, width=580, height=260, bg='#1a1a2e', highlightthickness=0)
        self.canvas.pack(pady=10)
        
        # Информация об акции
        price_frame = tk.Frame(self.root, bg='#0f0f1a')
        price_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(price_frame, text="📈 АКЦИЯ TECH CORP", font=("Arial", 14, "bold"), 
                 bg='#0f0f1a', fg='white').pack(side=tk.LEFT)
        
        self.price_label = tk.Label(price_frame, text="100.00", font=("Arial", 24, "bold"),
                                     bg='#0f0f1a', fg='#f39c12')
        self.price_label.pack(side=tk.RIGHT)
        
        self.change_label = tk.Label(price_frame, text="+0.00", font=("Arial", 14),
                                      bg='#0f0f1a', fg='#2ecc71')
        self.change_label.pack(side=tk.RIGHT, padx=10)
        
        # Портфель
        portfolio_frame = tk.Frame(self.root, bg='#1a1a2e', relief=tk.RIDGE, bd=2)
        portfolio_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(portfolio_frame, text="💰 БАЛАНС", font=("Arial", 10), 
                 bg='#1a1a2e', fg='#aaa').grid(row=0, column=0, padx=30, pady=5)
        tk.Label(portfolio_frame, text="📊 АКЦИЙ", font=("Arial", 10), 
                 bg='#1a1a2e', fg='#aaa').grid(row=0, column=1, padx=30, pady=5)
        tk.Label(portfolio_frame, text="💎 КАПИТАЛ", font=("Arial", 10), 
                 bg='#1a1a2e', fg='#aaa').grid(row=0, column=2, padx=30, pady=5)
        
        self.balance_label = tk.Label(portfolio_frame, text="10000", font=("Arial", 16, "bold"),
                                       bg='#1a1a2e', fg='#2ecc71')
        self.balance_label.grid(row=1, column=0, padx=30, pady=5)
        
        self.shares_label = tk.Label(portfolio_frame, text="0", font=("Arial", 16, "bold"),
                                      bg='#1a1a2e', fg='#f39c12')
        self.shares_label.grid(row=1, column=1, padx=30, pady=5)
        
        self.capital_label = tk.Label(portfolio_frame, text="10000", font=("Arial", 16, "bold"),
                                       bg='#1a1a2e', fg='#2ecc71')
        self.capital_label.grid(row=1, column=2, padx=30, pady=5)
        
        # Торговая панель
        trade_frame = tk.Frame(self.root, bg='#0f0f1a')
        trade_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(trade_frame, text="КОЛИЧЕСТВО АКЦИЙ:", font=("Arial", 10),
                 bg='#0f0f1a', fg='white').pack()
        
        self.amount_entry = tk.Entry(trade_frame, font=("Arial", 16), width=10,
                                      justify='center', bg='#0a0a1a', fg='#f39c12',
                                      insertbackground='white')
        self.amount_entry.pack(pady=5)
        self.amount_entry.insert(0, "1")
        
        btn_frame = tk.Frame(trade_frame, bg='#0f0f1a')
        btn_frame.pack(pady=10)
        
        tk.Button(btn_frame, text="🟢 КУПИТЬ", font=("Arial", 12, "bold"),
                  bg='#2ecc71', fg='white', padx=25, pady=8,
                  command=self.buy_shares).pack(side=tk.LEFT, padx=10)
        
        tk.Button(btn_frame, text="🔴 ПРОДАТЬ", font=("Arial", 12, "bold"),
                  bg='#e74c3c', fg='white', padx=25, pady=8,
                  command=self.sell_shares).pack(side=tk.LEFT, padx=10)
        
        # Кнопки управления
        control_frame = tk.Frame(self.root, bg='#0f0f1a')
        control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Button(control_frame, text="🔄 СБРОС", font=("Arial", 10, "bold"),
                  bg='#e74c3c', fg='white', padx=20, pady=5,
                  command=self.reset_game).pack(side=tk.LEFT, padx=5)
        
        tk.Button(control_frame, text="⏸️ ПАУЗА", font=("Arial", 10, "bold"),
                  bg='#f39c12', fg='white', padx=20, pady=5,
                  command=self.toggle_pause).pack(side=tk.LEFT, padx=5)
        
        # Регулировка скорости
        speed_frame = tk.Frame(self.root, bg='#0f0f1a')
        speed_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(speed_frame, text="⚡ СКОРОСТЬ ОБНОВЛЕНИЯ:", font=("Arial", 10),
                 bg='#0f0f1a', fg='white').pack(side=tk.LEFT, padx=5)
        
        self.speed_var = tk.IntVar(value=3)
        self.speed_scale = tk.Scale(speed_frame, from_=1, to=10, orient=tk.HORIZONTAL,
                                     variable=self.speed_var, length=150, bg='#0f0f1a',
                                     fg='white', highlightthickness=0,
                                     command=self.change_speed)
        self.speed_scale.pack(side=tk.LEFT, padx=5)
        
        tk.Label(speed_frame, text="сек", font=("Arial", 10),
                 bg='#0f0f1a', fg='white').pack(side=tk.LEFT)
        
        self.speed_status = tk.Label(speed_frame, text="(3 сек)", font=("Arial", 9),
                                      bg='#0f0f1a', fg='#aaa')
        self.speed_status.pack(side=tk.LEFT, padx=10)
        
        # Стартовый капитал
        start_frame = tk.Frame(self.root, bg='#0f0f1a')
        start_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(start_frame, text="💰 СТАРТОВЫЙ КАПИТАЛ:", font=("Arial", 10),
                 bg='#0f0f1a', fg='white').pack(side=tk.LEFT, padx=5)
        
        self.start_entry = tk.Entry(start_frame, font=("Arial", 12), width=10,
                                     bg='#0a0a1a', fg='#f39c12', insertbackground='white')
        self.start_entry.pack(side=tk.LEFT, padx=5)
        self.start_entry.insert(0, "10000")
        
        tk.Button(start_frame, text="🆕 НОВАЯ ИГРА", font=("Arial", 10, "bold"),
                  bg='#27ae60', fg='white', padx=15, pady=5,
                  command=self.new_game).pack(side=tk.LEFT, padx=10)
        
        # Новости
        self.news_label = tk.Label(self.root, text="📰 Добро пожаловать! Покупай дёшево, продавай дорого.",
                                    font=("Arial", 10), bg='#1a1a2e', fg='#ffd700',
                                    wraplength=600, justify='center')
        self.news_label.pack(fill=tk.X, padx=10, pady=10)
        
        # Статус
        self.status_label = tk.Label(self.root, text="📈 График обновляется каждую секунду",
                                      font=("Arial", 9), bg='#0a0f1c', fg='#aaa')
        self.status_label.pack(pady=5)
    
    def change_speed(self, val):
        """Изменение скорости обновления графика"""
        new_interval = int(float(val))
        self.update_interval = new_interval * 1000
        self.speed_status.config(text=f"({new_interval} сек)")
        
        # Перезапускаем таймер с новой скоростью
        if self.is_running and self.update_job is not None:
            self.root.after_cancel(self.update_job)
            self.update_job = self.root.after(self.update_interval, self.update_price)
        
        self.show_message(f"⚡ Скорость обновления: {new_interval} секунд", False)
    
    def generate_price(self):
        if not self.is_running:
            return
        
        # Меняем тренд каждые 30-70 шагов
        self.trend_cycle += 1
        if self.trend_cycle > random.randint(30, 70):
            self.trend_cycle = 0
            rand = random.random()
            if rand < 0.33:
                self.current_trend = "up"
                self.trend_strength = 0.3 + random.random() * 0.4
                self.news_label.config(text="📈 РЫНОК РАСТЁТ! БЫЧИЙ ТРЕНД")
            elif rand < 0.66:
                self.current_trend = "down"
                self.trend_strength = -0.3 - random.random() * 0.4
                self.news_label.config(text="📉 РЫНОК ПАДАЕТ! МЕДВЕЖИЙ ТРЕНД")
            else:
                self.current_trend = "floating"
                self.trend_strength = 0
                self.news_label.config(text="🟡 РЫНОК В БОКОВИКЕ")
        
        # Случайные новости (5% шанс)
        if random.random() < 0.05:
            if random.random() < 0.5:
                spike = 5 + random.random() * 10
                self.current_price *= (1 + spike / 100)
                self.news_label.config(text=f"📰 🟢 ХОРОШАЯ НОВОСТЬ! Акция выросла на +{spike:.1f}%")
                self.show_message(f"🟢 Акция выросла на +{spike:.1f}%", False)
            else:
                drop = 5 + random.random() * 10
                self.current_price *= (1 - drop / 100)
                self.news_label.config(text=f"📰 🔴 ПЛОХАЯ НОВОСТЬ! Акция упала на -{drop:.1f}%")
                self.show_message(f"🔴 Акция упала на -{drop:.1f}%", True)
        
        # Основное изменение цены
        change = (random.random() - 0.5) * self.volatility
        change += self.trend_strength * 0.5
        change += (100 - self.current_price) * 0.05 / 100
        
        self.current_price *= (1 + change / 100)
        
        # Ограничения
        if self.current_price < 10:
            self.current_price = 10
        if self.current_price > 500:
            self.current_price = 500
        
        # Обновляем историю
        self.price_history.append(self.current_price)
        if len(self.price_history) > 50:
            self.price_history.pop(0)
        
        self.update_ui()
        self.draw_chart()
    
    def update_ui(self):
        # Обновляем цену
        self.price_label.config(text=f"{self.current_price:.2f}")
        
        # Обновляем изменение
        change_pct = ((self.current_price - self.last_price) / self.last_price * 100)
        change_val = self.current_price - self.last_price
        if change_pct > 0:
            self.change_label.config(text=f"▲ +{change_val:.2f} (+{change_pct:.2f}%)", fg='#2ecc71')
        elif change_pct < 0:
            self.change_label.config(text=f"▼ {change_val:.2f} ({change_pct:.2f}%)", fg='#e74c3c')
        else:
            self.change_label.config(text="0.00 (0%)", fg='#aaa')
        
        self.last_price = self.current_price
        
        # Обновляем портфель
        self.balance_label.config(text=f"{int(self.balance)}")
        self.shares_label.config(text=f"{self.shares}")
        total_capital = self.balance + (self.shares * self.current_price)
        self.capital_label.config(text=f"{int(total_capital)}")
    
    def draw_chart(self):
        self.canvas.delete("all")
        if len(self.price_history) < 2:
            return
        
        width = 570
        height = 250
        
        # Рисуем сетку
        for i in range(5):
            y = height - (i * height / 4)
            self.canvas.create_line(30, y, width, y, fill='#2c3e50', width=0.5)
        
        # Находим min/max
        min_price = min(self.price_history)
        max_price = max(self.price_history)
        price_range = max_price - min_price
        if price_range < 1:
            price_range = 1
        
        # Рисуем линию
        step_x = (width - 30) / (len(self.price_history) - 1)
        points = []
        for i, price in enumerate(self.price_history):
            x = 30 + i * step_x
            y = height - ((price - min_price) / price_range) * (height - 40) - 10
            points.append((x, y))
        
        for i in range(len(points) - 1):
            self.canvas.create_line(points[i][0], points[i][1], points[i+1][0], points[i+1][1],
                                     fill='#2ecc71', width=2)
        
        # Рисуем точки
        for i, (x, y) in enumerate(points):
            if i % 5 == 0:
                self.canvas.create_oval(x-2, y-2, x+2, y+2, fill='#f39c12', outline='')
        
        # Текущая цена
        self.canvas.create_text(width-80, 20, text=f"Текущая: {self.current_price:.2f}",
                                 fill='#2ecc71', font=("Arial", 9))
        self.canvas.create_text(40, 20, text=f"Мин: {min_price:.2f}",
                                 fill='#aaa', font=("Arial", 9))
        self.canvas.create_text(40, 35, text=f"Макс: {max_price:.2f}",
                                 fill='#aaa', font=("Arial", 9))
    
    def buy_shares(self):
        try:
            amount = int(self.amount_entry.get())
            if amount <= 0:
                self.show_message("❌ Введите положительное число", True)
                return
            
            cost = amount * self.current_price
            if cost > self.balance:
                self.show_message(f"❌ Недостаточно средств! Нужно {cost:.2f}", True)
                return
            
            self.balance -= cost
            self.shares += amount
            self.update_ui()
            self.show_message(f"🟢 Куплено {amount} акций по {self.current_price:.2f}", False)
        except ValueError:
            self.show_message("❌ Введите корректное число", True)
    
    def sell_shares(self):
        try:
            amount = int(self.amount_entry.get())
            if amount <= 0:
                self.show_message("❌ Введите положительное число", True)
                return
            
            if amount > self.shares:
                self.show_message(f"❌ У вас только {self.shares} акций", True)
                return
            
            revenue = amount * self.current_price
            self.balance += revenue
            self.shares -= amount
            self.update_ui()
            self.show_message(f"🔴 Продано {amount} акций по {self.current_price:.2f}", False)
        except ValueError:
            self.show_message("❌ Введите корректное число", True)
    
    def reset_game(self):
        self.balance = self.start_capital
        self.shares = 0
        self.current_price = 100
        self.price_history = [100]
        self.last_price = 100
        self.trend_cycle = 0
        self.trend_strength = 0
        self.current_trend = "floating"
        self.update_ui()
        self.draw_chart()
        self.show_message("🔄 Игра сброшена", False)
        self.news_label.config(text="📰 Рынок перезапущен. Начинайте торговлю!")
    
    def new_game(self):
        try:
            new_start = int(self.start_entry.get())
            if new_start < 100:
                new_start = 100
            if new_start > 1000000:
                new_start = 1000000
            self.start_capital = new_start
            self.balance = self.start_capital
            self.shares = 0
            self.current_price = 100
            self.price_history = [100]
            self.last_price = 100
            self.trend_cycle = 0
            self.trend_strength = 0
            self.current_trend = "floating"
            self.update_ui()
            self.draw_chart()
            self.show_message(f"🆕 Новая игра! Стартовый капитал: {self.start_capital}", False)
            self.news_label.config(text="📰 Добро пожаловать! Покупай дёшево, продавай дорого!")
        except ValueError:
            self.show_message("❌ Введите корректное число", True)
    
    def toggle_pause(self):
        self.is_running = not self.is_running
        self.show_message("⏸️ Рынок на паузе" if not self.is_running else "▶️ Рынок открыт", False)
    
    def show_message(self, msg, is_error):
        self.status_label.config(text=msg, fg='#ff6666' if is_error else '#aaa')
        self.root.after(2000, lambda: self.status_label.config(
            text="📈 График обновляется каждую секунду", fg='#aaa'))
    
    def first_update(self):
        self.generate_price()
        self.update_job = self.root.after(self.update_interval, self.update_price)
    
    def update_price(self):
        self.generate_price()
        if self.is_running:
            self.update_job = self.root.after(self.update_interval, self.update_price)


if __name__ == "__main__":
    TraderSimulator()
