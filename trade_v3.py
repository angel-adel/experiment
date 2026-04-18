import tkinter as tk
from tkinter import ttk
import random
import json
import os

class MultiTraderSimulator:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("📈 Мультивалютный трейдер")
        self.root.geometry("750x850")
        self.root.configure(bg='#0a0f1c')
        
        # Данные акций
        self.stocks = {
            "Tech Corp": {
                "price": 100.0,
                "history": [100.0],
                "color": "#2ecc71",
                "volatility": 2.5,
                "sector": "IT"
            },
            "Green Energy": {
                "price": 50.0,
                "history": [50.0],
                "color": "#3498db",
                "volatility": 3.0,
                "sector": "Energy"
            },
            "Metal Industries": {
                "price": 75.0,
                "history": [75.0],
                "color": "#e74c3c",
                "volatility": 2.0,
                "sector": "Industrial"
            }
        }
        
        # Валюты
        self.usd_balance = 10000.0  # доллары
        self.rub_balance = 0.0       # рубли
        self.usd_rub_rate = 95.0     # курс USD/RUB
        
        # Портфель акций
        self.portfolio = {
            "Tech Corp": 0,
            "Green Energy": 0,
            "Metal Industries": 0
        }
        
        # Параметры генерации
        self.current_stock = "Tech Corp"
        self.is_running = True
        self.update_interval = 3000  # миллисекунды
        self.update_job = None
        
        # История курса валют
        self.rate_history = [95.0]
        
        # Создаём интерфейс
        self.setup_ui()
        
        # Загружаем сохранения
        self.load_data()
        
        # Запускаем обновление
        self.root.after(1000, self.first_update)
        
        self.root.mainloop()
    
    def setup_ui(self):
        # Основной фрейм
        main_frame = tk.Frame(self.root, bg='#0a0f1c')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Верхняя панель с балансом
        balance_frame = tk.Frame(main_frame, bg='#1a1a2e', relief=tk.RIDGE, bd=2)
        balance_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(balance_frame, text="💰 БАЛАНС", font=("Arial", 12, "bold"),
                 bg='#1a1a2e', fg='#aaa').grid(row=0, column=0, columnspan=2, pady=5)
        
        self.usd_label = tk.Label(balance_frame, text=f"USD: ${self.usd_balance:.2f}",
                                   font=("Arial", 16, "bold"), bg='#1a1a2e', fg='#2ecc71')
        self.usd_label.grid(row=1, column=0, padx=30, pady=5)
        
        self.rub_label = tk.Label(balance_frame, text=f"RUB: {self.rub_balance:.2f} ₽",
                                   font=("Arial", 16, "bold"), bg='#1a1a2e', fg='#f39c12')
        self.rub_label.grid(row=1, column=1, padx=30, pady=5)
        
        # Курс валют
        rate_frame = tk.Frame(main_frame, bg='#1a1a2e', relief=tk.RIDGE, bd=2)
        rate_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(rate_frame, text="💱 КУРС USD/RUB", font=("Arial", 10, "bold"),
                 bg='#1a1a2e', fg='#aaa').pack(side=tk.LEFT, padx=10)
        
        self.rate_label = tk.Label(rate_frame, text=f"{self.usd_rub_rate:.2f}",
                                    font=("Arial", 14, "bold"), bg='#1a1a2e', fg='#f39c12')
        self.rate_label.pack(side=tk.LEFT, padx=10)
        
        tk.Button(rate_frame, text="🔄 КОНВЕРТИРОВАТЬ USD→RUB", font=("Arial", 9),
                  bg='#34495e', fg='white', padx=10, command=self.convert_usd_to_rub).pack(side=tk.RIGHT, padx=5)
        tk.Button(rate_frame, text="🔄 КОНВЕРТИРОВАТЬ RUB→USD", font=("Arial", 9),
                  bg='#34495e', fg='white', padx=10, command=self.convert_rub_to_usd).pack(side=tk.RIGHT, padx=5)
        
        # График
        self.canvas = tk.Canvas(main_frame, width=680, height=250, bg='#1a1a2e', highlightthickness=0)
        self.canvas.pack(pady=10)
        
        # Выбор акции
        stock_frame = tk.Frame(main_frame, bg='#0a0f1c')
        stock_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(stock_frame, text="📊 ВЫБОР АКЦИИ:", font=("Arial", 10),
                 bg='#0a0f1c', fg='white').pack(side=tk.LEFT, padx=5)
        
        self.stock_var = tk.StringVar(value="Tech Corp")
        self.stock_menu = ttk.Combobox(stock_frame, textvariable=self.stock_var,
                                        values=list(self.stocks.keys()), width=20, state="readonly")
        self.stock_menu.pack(side=tk.LEFT, padx=5)
        self.stock_menu.bind("<<ComboboxSelected>>", self.change_stock)
        
        # Информация об акции
        self.stock_info = tk.Label(main_frame, text="", font=("Arial", 10),
                                    bg='#0a0f1c', fg='#aaa')
        self.stock_info.pack(pady=5)
        
        # Портфель акций
        portfolio_frame = tk.Frame(main_frame, bg='#1a1a2e', relief=tk.RIDGE, bd=2)
        portfolio_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(portfolio_frame, text="📈 ПОРТФЕЛЬ АКЦИЙ", font=("Arial", 12, "bold"),
                 bg='#1a1a2e', fg='#aaa').pack(pady=5)
        
        self.portfolio_labels = {}
        for i, stock in enumerate(self.stocks.keys()):
            frame = tk.Frame(portfolio_frame, bg='#1a1a2e')
            frame.pack(fill=tk.X, pady=2)
            
            color = self.stocks[stock]["color"]
            tk.Label(frame, text=f"{stock}:", font=("Arial", 10),
                     bg='#1a1a2e', fg=color).pack(side=tk.LEFT, padx=10)
            
            label = tk.Label(frame, text="0 шт", font=("Arial", 10, "bold"),
                              bg='#1a1a2e', fg='white')
            label.pack(side=tk.LEFT, padx=10)
            self.portfolio_labels[stock] = label
        
        # Торговая панель
        trade_frame = tk.Frame(main_frame, bg='#0a0f1c')
        trade_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(trade_frame, text="КОЛИЧЕСТВО:", font=("Arial", 10),
                 bg='#0a0f1c', fg='white').pack(side=tk.LEFT, padx=5)
        
        self.amount_entry = tk.Entry(trade_frame, font=("Arial", 14), width=8,
                                      justify='center', bg='#0a0a1a', fg='#f39c12',
                                      insertbackground='white')
        self.amount_entry.pack(side=tk.LEFT, padx=5)
        self.amount_entry.insert(0, "1")
        
        tk.Button(trade_frame, text="🟢 КУПИТЬ", font=("Arial", 11, "bold"),
                  bg='#2ecc71', fg='white', padx=15, pady=5,
                  command=self.buy_stock).pack(side=tk.LEFT, padx=5)
        
        tk.Button(trade_frame, text="🔴 ПРОДАТЬ", font=("Arial", 11, "bold"),
                  bg='#e74c3c', fg='white', padx=15, pady=5,
                  command=self.sell_stock).pack(side=tk.LEFT, padx=5)
        
        # Кнопки управления
        control_frame = tk.Frame(main_frame, bg='#0a0f1c')
        control_frame.pack(fill=tk.X, pady=5)
        
        tk.Button(control_frame, text="🔄 СБРОС", font=("Arial", 10),
                  bg='#e74c3c', fg='white', padx=15, command=self.reset_game).pack(side=tk.LEFT, padx=5)
        tk.Button(control_frame, text="⏸️ ПАУЗА", font=("Arial", 10),
                  bg='#f39c12', fg='white', padx=15, command=self.toggle_pause).pack(side=tk.LEFT, padx=5)
        tk.Button(control_frame, text="💾 СОХРАНИТЬ", font=("Arial", 10),
                  bg='#3498db', fg='white', padx=15, command=self.save_data).pack(side=tk.LEFT, padx=5)
        
        # Скорость обновления
        speed_frame = tk.Frame(main_frame, bg='#0a0f1c')
        speed_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(speed_frame, text="⚡ СКОРОСТЬ:", font=("Arial", 10),
                 bg='#0a0f1c', fg='white').pack(side=tk.LEFT, padx=5)
        
        self.speed_var = tk.IntVar(value=3)
        self.speed_scale = tk.Scale(speed_frame, from_=1, to=10, orient=tk.HORIZONTAL,
                                     variable=self.speed_var, length=150, bg='#0a0f1c',
                                     fg='white', highlightthickness=0,
                                     command=self.change_speed)
        self.speed_scale.pack(side=tk.LEFT, padx=5)
        
        tk.Label(speed_frame, text="сек", font=("Arial", 10),
                 bg='#0a0f1c', fg='white').pack(side=tk.LEFT)
        
        # Стартовый капитал
        start_frame = tk.Frame(main_frame, bg='#0a0f1c')
        start_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(start_frame, text="💰 СТАРТОВЫЙ КАПИТАЛ (USD):", font=("Arial", 10),
                 bg='#0a0f1c', fg='white').pack(side=tk.LEFT, padx=5)
        
        self.start_entry = tk.Entry(start_frame, font=("Arial", 10), width=10,
                                     bg='#0a0a1a', fg='#f39c12')
        self.start_entry.pack(side=tk.LEFT, padx=5)
        self.start_entry.insert(0, "10000")
        
        tk.Button(start_frame, text="🆕 НОВАЯ ИГРА", font=("Arial", 10),
                  bg='#27ae60', fg='white', padx=15, command=self.new_game).pack(side=tk.LEFT, padx=10)
        
        # Новости
        self.news_label = tk.Label(main_frame, text="📰 Добро пожаловать!",
                                    font=("Arial", 9), bg='#1a1a2e', fg='#ffd700',
                                    wraplength=700, justify='center')
        self.news_label.pack(fill=tk.X, pady=5)
        
        # Статус
        self.status_label = tk.Label(main_frame, text="📈 График обновляется каждые 3 секунды",
                                      font=("Arial", 8), bg='#0a0f1c', fg='#aaa')
        self.status_label.pack(pady=5)
    
    def generate_price(self, stock_name):
        """Генерация цены для конкретной акции"""
        stock = self.stocks[stock_name]
        price = stock["price"]
        
        # Случайное блуждание
        change = (random.random() - 0.5) * stock["volatility"]
        change += (random.random() - 0.5) * 0.5
        
        # Возврат к среднему
        if stock_name == "Tech Corp":
            change += (100 - price) * 0.03 / 100
        elif stock_name == "Green Energy":
            change += (50 - price) * 0.04 / 100
        else:
            change += (75 - price) * 0.02 / 100
        
        new_price = price * (1 + change / 100)
        
        # Ограничения
        if new_price < 10:
            new_price = 10
        if new_price > 500:
            new_price = 500
        
        stock["price"] = new_price
        stock["history"].append(new_price)
        if len(stock["history"]) > 50:
            stock["history"].pop(0)
        
        return new_price
    
    def generate_rate(self):
        """Генерация курса валют"""
        change = (random.random() - 0.5) * 1.5
        self.usd_rub_rate *= (1 + change / 100)
        
        if self.usd_rub_rate < 70:
            self.usd_rub_rate = 70
        if self.usd_rub_rate > 130:
            self.usd_rub_rate = 130
        
        self.rate_history.append(self.usd_rub_rate)
        if len(self.rate_history) > 50:
            self.rate_history.pop(0)
        
        self.rate_label.config(text=f"{self.usd_rub_rate:.2f}")
    
    def update_all_prices(self):
        """Обновление всех цен"""
        if not self.is_running:
            return
        
        # Обновляем цены акций
        for stock in self.stocks:
            self.generate_price(stock)
        
        # Обновляем курс валют
        self.generate_rate()
        
        # Случайные новости
        if random.random() < 0.05:
            news_type = random.choice(["good", "bad"])
            if news_type == "good":
                stock = random.choice(list(self.stocks.keys()))
                self.stocks[stock]["price"] *= 1.1
                self.news_label.config(text=f"📰 🟢 ХОРОШАЯ НОВОСТЬ! {stock} выросла на +10%")
                self.show_message(f"🟢 {stock} выросла на +10%", False)
            else:
                stock = random.choice(list(self.stocks.keys()))
                self.stocks[stock]["price"] *= 0.9
                self.news_label.config(text=f"📰 🔴 ПЛОХАЯ НОВОСТЬ! {stock} упала на -10%")
                self.show_message(f"🔴 {stock} упала на -10%", True)
        
        self.update_display()
        self.draw_chart()
    
    def update_display(self):
        """Обновление отображения"""
        # Обновляем баланс
        self.usd_label.config(text=f"USD: ${self.usd_balance:.2f}")
        self.rub_label.config(text=f"RUB: {self.rub_balance:.2f} ₽")
        
        # Обновляем портфель
        for stock, count in self.portfolio.items():
            self.portfolio_labels[stock].config(text=f"{count} шт")
        
        # Обновляем текущую акцию
        current = self.stocks[self.current_stock]
        self.stock_info.config(text=f"💰 Цена: ${current['price']:.2f} | Волатильность: {current['volatility']}")
    
    def draw_chart(self):
        """Отрисовка графика текущей акции"""
        self.canvas.delete("all")
        
        stock = self.stocks[self.current_stock]
        history = stock["history"]
        
        if len(history) < 2:
            return
        
        width = 670
        height = 240
        
        # Сетка
        for i in range(5):
            y = height - (i * height / 4)
            self.canvas.create_line(30, y, width, y, fill='#2c3e50', width=0.5)
        
        # Мин/макс
        min_price = min(history)
        max_price = max(history)
        price_range = max_price - min_price
        if price_range < 1:
            price_range = 1
        
        # Линия
        step_x = (width - 30) / (len(history) - 1)
        points = []
        for i, price in enumerate(history):
            x = 30 + i * step_x
            y = height - ((price - min_price) / price_range) * (height - 40) - 10
            points.append((x, y))
        
        for i in range(len(points) - 1):
            self.canvas.create_line(points[i][0], points[i][1], points[i+1][0], points[i+1][1],
                                     fill=stock["color"], width=2)
        
        # Точки
        for i, (x, y) in enumerate(points):
            if i % 5 == 0:
                self.canvas.create_oval(x-2, y-2, x+2, y+2, fill='#f39c12', outline='')
        
        # Подписи
        self.canvas.create_text(width-100, 20, text=f"Текущая: {stock['price']:.2f}",
                                 fill=stock["color"], font=("Arial", 9))
        self.canvas.create_text(40, 20, text=f"Мин: {min_price:.2f}",
                                 fill='#aaa', font=("Arial", 9))
        self.canvas.create_text(40, 35, text=f"Макс: {max_price:.2f}",
                                 fill='#aaa', font=("Arial", 9))
    
    def buy_stock(self):
        """Покупка акций"""
        try:
            amount = int(self.amount_entry.get())
            if amount <= 0:
                self.show_message("❌ Введите положительное число", True)
                return
            
            stock_name = self.current_stock
            price = self.stocks[stock_name]["price"]
            cost = amount * price
            
            if cost > self.usd_balance:
                self.show_message(f"❌ Недостаточно USD! Нужно ${cost:.2f}", True)
                return
            
            self.usd_balance -= cost
            self.portfolio[stock_name] += amount
            self.update_display()
            self.show_message(f"🟢 Куплено {amount} {stock_name} по ${price:.2f}", False)
        except ValueError:
            self.show_message("❌ Введите корректное число", True)
    
    def sell_stock(self):
        """Продажа акций"""
        try:
            amount = int(self.amount_entry.get())
            if amount <= 0:
                self.show_message("❌ Введите положительное число", True)
                return
            
            stock_name = self.current_stock
            price = self.stocks[stock_name]["price"]
            
            if amount > self.portfolio[stock_name]:
                self.show_message(f"❌ У вас только {self.portfolio[stock_name]} акций", True)
                return
            
            revenue = amount * price
            self.usd_balance += revenue
            self.portfolio[stock_name] -= amount
            self.update_display()
            self.show_message(f"🔴 Продано {amount} {stock_name} по ${price:.2f}", False)
        except ValueError:
            self.show_message("❌ Введите корректное число", True)
    
    def convert_usd_to_rub(self):
        """Конвертация долларов в рубли"""
        if self.usd_balance <= 0:
            self.show_message("❌ Нет долларов для конвертации", True)
            return
        
        amount = self.usd_balance
        rub_amount = amount * self.usd_rub_rate
        self.rub_balance += rub_amount
        self.usd_balance = 0
        self.update_display()
        self.show_message(f"💱 Конвертировано ${amount:.2f} → {rub_amount:.2f} ₽", False)
    
    def convert_rub_to_usd(self):
        """Конвертация рублей в доллары"""
        if self.rub_balance <= 0:
            self.show_message("❌ Нет рублей для конвертации", True)
            return
        
        amount = self.rub_balance
        usd_amount = amount / self.usd_rub_rate
        self.usd_balance += usd_amount
        self.rub_balance = 0
        self.update_display()
        self.show_message(f"💱 Конвертировано {amount:.2f} ₽ → ${usd_amount:.2f}", False)
    
    def change_stock(self, event=None):
        """Смена текущей акции"""
        self.current_stock = self.stock_var.get()
        self.draw_chart()
        self.update_display()
    
    def change_speed(self, val):
        """Изменение скорости обновления"""
        new_interval = int(float(val))
        self.update_interval = new_interval * 1000
        self.status_label.config(text=f"📈 График обновляется каждые {new_interval} секунды")
        
        if self.update_job is not None and self.is_running:
            self.root.after_cancel(self.update_job)
            self.update_job = self.root.after(self.update_interval, self.update_price)
    
    def toggle_pause(self):
        """Пауза"""
        self.is_running = not self.is_running
        self.show_message("⏸️ Рынок на паузе" if not self.is_running else "▶️ Рынок открыт", False)
    
    def reset_game(self):
        """Сброс игры"""
        self.usd_balance = 10000
        self.rub_balance = 0
        self.usd_rub_rate = 95
        self.portfolio = {stock: 0 for stock in self.stocks}
        
        for stock in self.stocks:
            if stock == "Tech Corp":
                self.stocks[stock]["price"] = 100
                self.stocks[stock]["history"] = [100]
            elif stock == "Green Energy":
                self.stocks[stock]["price"] = 50
                self.stocks[stock]["history"] = [50]
            else:
                self.stocks[stock]["price"] = 75
                self.stocks[stock]["history"] = [75]
        
        self.update_display()
        self.draw_chart()
        self.show_message("🔄 Игра сброшена", False)
    
    def new_game(self):
        """Новая игра с новым стартовым капиталом"""
        try:
            new_start = int(self.start_entry.get())
            if new_start < 100:
                new_start = 100
            if new_start > 1000000:
                new_start = 1000000
            
            self.usd_balance = new_start
            self.rub_balance = 0
            self.usd_rub_rate = 95
            self.portfolio = {stock: 0 for stock in self.stocks}
            
            for stock in self.stocks:
                if stock == "Tech Corp":
                    self.stocks[stock]["price"] = 100
                    self.stocks[stock]["history"] = [100]
                elif stock == "Green Energy":
                    self.stocks[stock]["price"] = 50
                    self.stocks[stock]["history"] = [50]
                else:
                    self.stocks[stock]["price"] = 75
                    self.stocks[stock]["history"] = [75]
            
            self.update_display()
            self.draw_chart()
            self.show_message(f"🆕 Новая игра! Стартовый капитал: ${new_start}", False)
        except ValueError:
            self.show_message("❌ Введите корректное число", True)
    
    def save_data(self):
        """Сохранение данных"""
        data = {
            "usd_balance": self.usd_balance,
            "rub_balance": self.rub_balance,
            "usd_rub_rate": self.usd_rub_rate,
            "portfolio": self.portfolio,
            "stock_prices": {name: stock["price"] for name, stock in self.stocks.items()}
        }
        with open("trader_save.json", "w") as f:
            json.dump(data, f)
        self.show_message("💾 Данные сохранены", False)
    
    def load_data(self):
        """Загрузка данных"""
        if os.path.exists("trader_save.json"):
            try:
                with open("trader_save.json", "r") as f:
                    data = json.load(f)
                self.usd_balance = data["usd_balance"]
                self.rub_balance = data["rub_balance"]
                self.usd_rub_rate = data["usd_rub_rate"]
                self.portfolio = data["portfolio"]
                for name, price in data["stock_prices"].items():
                    if name in self.stocks:
                        self.stocks[name]["price"] = price
                self.update_display()
                self.show_message("📁 Данные загружены", False)
            except:
                pass
    
    def show_message(self, msg, is_error):
        """Показать сообщение"""
        self.status_label.config(text=msg, fg='#ff6666' if is_error else '#aaa')
        self.root.after(2000, lambda: self.status_label.config(
            text=f"📈 График обновляется каждые {self.update_interval//1000} секунды", fg='#aaa'))
    
    def first_update(self):
        self.update_all_prices()
        self.update_job = self.root.after(self.update_interval, self.update_price)
    
    def update_price(self):
        self.update_all_prices()
        if self.is_running:
            self.update_job = self.root.after(self.update_interval, self.update_price)


if __name__ == "__main__":
    MultiTraderSimulator()
