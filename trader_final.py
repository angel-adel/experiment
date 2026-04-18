import tkinter as tk
from tkinter import ttk
import random
import json
import os
from datetime import datetime

class MultiTraderSimulator:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("📈 Мультивалютный трейдер - 22 акции")
        self.root.geometry("900x800")
        self.root.configure(bg='#0a0f1c')
        
        # ----- ДАННЫЕ АКЦИЙ (22 штуки) -----
        self.stocks_data = [
            # IT сектор
            {"name": "Tech Corp", "price": 100, "sector": "IT", "volatility": 2.5, "color": "#2ecc71"},
            {"name": "LogiTech", "price": 220, "sector": "IT", "volatility": 3.2, "color": "#1abc9c"},
            {"name": "SoftDev", "price": 85, "sector": "IT", "volatility": 2.8, "color": "#27ae60"},
            {"name": "DataCore", "price": 145, "sector": "IT", "volatility": 3.0, "color": "#2ecc71"},
            {"name": "CyberSys", "price": 190, "sector": "IT", "volatility": 3.5, "color": "#58d68d"},
            
            # Нефтегаз
            {"name": "Lukoil", "price": 320, "sector": "Oil&Gas", "volatility": 2.2, "color": "#f1c40f"},
            {"name": "Gazprom", "price": 150, "sector": "Oil&Gas", "volatility": 2.0, "color": "#95a5a6"},
            {"name": "Rosneft", "price": 280, "sector": "Oil&Gas", "volatility": 2.3, "color": "#f39c12"},
            {"name": "Surgut", "price": 45, "sector": "Oil&Gas", "volatility": 2.5, "color": "#e67e22"},
            {"name": "Tatneft", "price": 210, "sector": "Oil&Gas", "volatility": 2.1, "color": "#f1c40f"},
            
            # Энергетика
            {"name": "Green Energy", "price": 50, "sector": "Energy", "volatility": 3.0, "color": "#3498db"},
            {"name": "RusHydro", "price": 35, "sector": "Energy", "volatility": 2.5, "color": "#5dade2"},
            {"name": "InterRAO", "price": 28, "sector": "Energy", "volatility": 2.8, "color": "#85c1e9"},
            {"name": "Rosatom", "price": 95, "sector": "Energy", "volatility": 2.0, "color": "#3498db"},
            
            # Промышленность
            {"name": "Metal Industries", "price": 75, "sector": "Industrial", "volatility": 2.0, "color": "#e74c3c"},
            {"name": "Nornickel", "price": 420, "sector": "Industrial", "volatility": 2.8, "color": "#e74c3c"},
            {"name": "Severstal", "price": 185, "sector": "Industrial", "volatility": 2.3, "color": "#ec7063"},
            {"name": "MMK", "price": 55, "sector": "Industrial", "volatility": 2.4, "color": "#e74c3c"},
            
            # Финансы
            {"name": "Minfin", "price": 180, "sector": "Finance", "volatility": 1.8, "color": "#9b59b6"},
            {"name": "Sberbank", "price": 125, "sector": "Finance", "volatility": 2.2, "color": "#a569bd"},
            {"name": "VTB", "price": 18, "sector": "Finance", "volatility": 2.5, "color": "#bb8fce"},
            {"name": "AlfaBank", "price": 95, "sector": "Finance", "volatility": 2.0, "color": "#9b59b6"}
        ]
        
        # Преобразуем в словари для быстрого доступа
        self.stocks = {}
        self.portfolio = {}
        for s in self.stocks_data:
            self.stocks[s["name"]] = {
                "price": s["price"],
                "history": [s["price"]],
                "color": s["color"],
                "volatility": s["volatility"],
                "sector": s["sector"]
            }
            self.portfolio[s["name"]] = 0
        
        # Валюты
        self.usd_balance = 10000.0
        self.rub_balance = 0.0
        self.usd_rub_rate = 95.0
        self.rate_history = [95.0]
        
        # Параметры
        self.current_stock = "Tech Corp"
        self.is_running = True
        self.update_interval = 3000
        self.update_job = None
        
        # Поиск и фильтр
        self.search_var = tk.StringVar()
        self.sector_var = tk.StringVar(value="all")
        self.sectors = sorted(list(set([s["sector"] for s in self.stocks_data])))
        
        # Создаём интерфейс
        self.setup_ui()
        
        # Загружаем сохранения
        self.load_data()
        
        # Запускаем обновление
        self.root.after(1000, self.first_update)
        
        self.root.mainloop()
    
    def setup_ui(self):
        # Основной фрейм с прокруткой
        main_canvas = tk.Canvas(self.root, bg='#0a0f1c', highlightthickness=0)
        scrollbar = tk.Scrollbar(self.root, orient="vertical", command=main_canvas.yview)
        self.scrollable_frame = tk.Frame(main_canvas, bg='#0a0f1c')
        
        self.scrollable_frame.bind("<Configure>", lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all")))
        main_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        main_canvas.configure(yscrollcommand=scrollbar.set)
        
        main_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # --- Баланс ---
        balance_frame = tk.Frame(self.scrollable_frame, bg='#1a1a2e', relief=tk.RIDGE, bd=2)
        balance_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(balance_frame, text="💰 БАЛАНС", font=("Arial", 12, "bold"),
                 bg='#1a1a2e', fg='#aaa').pack(pady=5)
        
        balance_inner = tk.Frame(balance_frame, bg='#1a1a2e')
        balance_inner.pack()
        
        self.usd_label = tk.Label(balance_inner, text=f"USD: ${self.usd_balance:.2f}",
                                   font=("Arial", 18, "bold"), bg='#1a1a2e', fg='#2ecc71')
        self.usd_label.pack(side=tk.LEFT, padx=30)
        
        self.rub_label = tk.Label(balance_inner, text=f"RUB: {self.rub_balance:.2f} ₽",
                                   font=("Arial", 18, "bold"), bg='#1a1a2e', fg='#f39c12')
        self.rub_label.pack(side=tk.LEFT, padx=30)
        
        # --- Курс валют ---
        rate_frame = tk.Frame(self.scrollable_frame, bg='#1a1a2e', relief=tk.RIDGE, bd=2)
        rate_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(rate_frame, text="💱 КУРС USD/RUB", font=("Arial", 10, "bold"),
                 bg='#1a1a2e', fg='#aaa').pack(side=tk.LEFT, padx=10)
        
        self.rate_label = tk.Label(rate_frame, text=f"{self.usd_rub_rate:.2f}",
                                    font=("Arial", 16, "bold"), bg='#1a1a2e', fg='#f39c12')
        self.rate_label.pack(side=tk.LEFT, padx=10)
        
        tk.Button(rate_frame, text="💱 USD → RUB", font=("Arial", 9),
                  bg='#9b59b6', fg='white', padx=10, command=self.convert_usd_to_rub).pack(side=tk.RIGHT, padx=5)
        tk.Button(rate_frame, text="💱 RUB → USD", font=("Arial", 9),
                  bg='#9b59b6', fg='white', padx=10, command=self.convert_rub_to_usd).pack(side=tk.RIGHT, padx=5)
        
        # --- График ---
        self.canvas = tk.Canvas(self.scrollable_frame, width=850, height=250, bg='#1a1a2e', highlightthickness=0)
        self.canvas.pack(pady=10)
        
        # --- Поиск и фильтр ---
        search_frame = tk.Frame(self.scrollable_frame, bg='#0a0f1c')
        search_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(search_frame, text="🔍 ПОИСК:", font=("Arial", 9),
                 bg='#0a0f1c', fg='white').pack(side=tk.LEFT, padx=5)
        
        self.search_entry = tk.Entry(search_frame, textvariable=self.search_var, width=20,
                                      bg='#0a0a1a', fg='#f39c12', insertbackground='white')
        self.search_entry.pack(side=tk.LEFT, padx=5)
        self.search_var.trace('w', lambda *a: self.update_stock_list())
        
        tk.Label(search_frame, text="СЕКТОР:", font=("Arial", 9),
                 bg='#0a0f1c', fg='white').pack(side=tk.LEFT, padx=10)
        
        self.sector_combo = ttk.Combobox(search_frame, textvariable=self.sector_var,
                                          values=["all"] + self.sectors, width=15, state="readonly")
        self.sector_combo.pack(side=tk.LEFT, padx=5)
        self.sector_combo.bind("<<ComboboxSelected>>", lambda e: self.update_stock_list())
        
        # --- Список акций (кнопки) ---
        self.stock_frame = tk.Frame(self.scrollable_frame, bg='#1a1a2e', relief=tk.RIDGE, bd=2)
        self.stock_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.stock_buttons_frame = tk.Frame(self.stock_frame, bg='#1a1a2e')
        self.stock_buttons_frame.pack(pady=5)
        
        # --- Портфель ---
        portfolio_frame = tk.Frame(self.scrollable_frame, bg='#1a1a2e', relief=tk.RIDGE, bd=2)
        portfolio_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(portfolio_frame, text="📈 ПОРТФЕЛЬ АКЦИЙ", font=("Arial", 10, "bold"),
                 bg='#1a1a2e', fg='#aaa').pack(pady=5)
        
        self.portfolio_text = tk.Text(portfolio_frame, height=8, width=80,
                                       bg='#0a0a1a', fg='#2ecc71', font=("Arial", 9),
                                       relief=tk.FLAT, wrap=tk.WORD)
        self.portfolio_text.pack(padx=10, pady=5)
        
        # --- Торговая панель ---
        trade_frame = tk.Frame(self.scrollable_frame, bg='#0a0f1c')
        trade_frame.pack(fill=tk.X, padx=10, pady=10)
        
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
        
        # --- Кнопки управления ---
        control_frame = tk.Frame(self.scrollable_frame, bg='#0a0f1c')
        control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Button(control_frame, text="🔄 СБРОС", font=("Arial", 10),
                  bg='#e74c3c', fg='white', padx=15, command=self.reset_game).pack(side=tk.LEFT, padx=5)
        tk.Button(control_frame, text="⏸️ ПАУЗА", font=("Arial", 10),
                  bg='#f39c12', fg='white', padx=15, command=self.toggle_pause).pack(side=tk.LEFT, padx=5)
        tk.Button(control_frame, text="💾 СОХРАНИТЬ", font=("Arial", 10),
                  bg='#3498db', fg='white', padx=15, command=self.save_data).pack(side=tk.LEFT, padx=5)
        
        # --- Скорость обновления ---
        speed_frame = tk.Frame(self.scrollable_frame, bg='#0a0f1c')
        speed_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(speed_frame, text="⚡ СКОРОСТЬ ОБНОВЛЕНИЯ:", font=("Arial", 10),
                 bg='#0a0f1c', fg='white').pack(side=tk.LEFT, padx=5)
        
        self.speed_var = tk.IntVar(value=3)
        self.speed_scale = tk.Scale(speed_frame, from_=1, to=10, orient=tk.HORIZONTAL,
                                     variable=self.speed_var, length=200, bg='#0a0f1c',
                                     fg='white', highlightthickness=0,
                                     command=self.change_speed)
        self.speed_scale.pack(side=tk.LEFT, padx=5)
        
        tk.Label(speed_frame, text="сек", font=("Arial", 10),
                 bg='#0a0f1c', fg='white').pack(side=tk.LEFT)
        
        self.speed_status = tk.Label(speed_frame, text="(3 сек)", font=("Arial", 9),
                                      bg='#0a0f1c', fg='#aaa')
        self.speed_status.pack(side=tk.LEFT, padx=10)
        
        # --- Стартовый капитал ---
        start_frame = tk.Frame(self.scrollable_frame, bg='#0a0f1c')
        start_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(start_frame, text="💰 СТАРТОВЫЙ КАПИТАЛ (USD):", font=("Arial", 10),
                 bg='#0a0f1c', fg='white').pack(side=tk.LEFT, padx=5)
        
        self.start_entry = tk.Entry(start_frame, font=("Arial", 10), width=10,
                                     bg='#0a0a1a', fg='#f39c12')
        self.start_entry.pack(side=tk.LEFT, padx=5)
        self.start_entry.insert(0, "10000")
        
        tk.Button(start_frame, text="🆕 НОВАЯ ИГРА", font=("Arial", 10),
                  bg='#27ae60', fg='white', padx=15, command=self.new_game).pack(side=tk.LEFT, padx=10)
        
        # --- Новости ---
        self.news_label = tk.Label(self.scrollable_frame, text="📰 Добро пожаловать!",
                                    font=("Arial", 9), bg='#1a1a2e', fg='#ffd700',
                                    wraplength=850, justify='center')
        self.news_label.pack(fill=tk.X, padx=10, pady=5)
        
        # --- Статус ---
        self.status_label = tk.Label(self.scrollable_frame, text="📈 График обновляется каждые 3 секунды",
                                      font=("Arial", 8), bg='#0a0f1c', fg='#aaa')
        self.status_label.pack(pady=5)
        
        # Начальное обновление списка акций
        self.update_stock_list()
        self.update_portfolio_display()
    
    def update_stock_list(self):
        """Обновление списка кнопок акций с учётом поиска и фильтра"""
        for widget in self.stock_buttons_frame.winfo_children():
            widget.destroy()
        
        search_text = self.search_var.get().lower()
        sector = self.sector_var.get()
        
        filtered = [s for s in self.stocks_data if
                    (search_text in s["name"].lower()) and
                    (sector == "all" or s["sector"] == sector)]
        
        row_frame = None
        for i, stock in enumerate(filtered):
            if i % 4 == 0:
                row_frame = tk.Frame(self.stock_buttons_frame, bg='#1a1a2e')
                row_frame.pack(pady=2)
            
            color = self.stocks[stock["name"]]["color"]
            btn = tk.Button(row_frame, text=stock["name"], font=("Arial", 9),
                           bg='#2c3e50', fg='white', padx=8, pady=3,
                           command=lambda n=stock["name"]: self.change_stock(n))
            btn.pack(side=tk.LEFT, padx=2)
            
            if self.current_stock == stock["name"]:
                btn.config(bg=color, activebackground=color)
    
    def update_portfolio_display(self):
        """Обновление отображения портфеля"""
        self.portfolio_text.delete(1.0, tk.END)
        has_stocks = False
        for name, count in self.portfolio.items():
            if count > 0:
                has_stocks = True
                color = self.stocks[name]["color"]
                value = count * self.stocks[name]["price"]
                self.portfolio_text.insert(tk.END, f"{name}: {count} шт (${value:.2f})\n", f"color_{name}")
                self.portfolio_text.tag_config(f"color_{name}", foreground=color)
        if not has_stocks:
            self.portfolio_text.insert(tk.END, "📭 Портфель пуст. Купите акции!")
    
    def generate_price(self, stock_name):
        """Генерация цены для акции"""
        stock = self.stocks[stock_name]
        price = stock["price"]
        
        change = (random.random() - 0.5) * stock["volatility"]
        change += (random.random() - 0.5) * 0.5
        
        # Возврат к средней цене
        avg_price = next(s["price"] for s in self.stocks_data if s["name"] == stock_name)
        change += (avg_price - price) * 0.02 / 100
        
        new_price = price * (1 + change / 100)
        if new_price < 5:
            new_price = 5
        if new_price > 1000:
            new_price = 1000
        
        stock["price"] = new_price
        stock["history"].append(new_price)
        if len(stock["history"]) > 50:
            stock["history"].pop(0)
        
        return new_price
    
    def generate_rate(self):
        """Генерация курса валют"""
        change = (random.random() - 0.5) * 1.5
        self.usd_rub_rate *= (1 + change / 100)
        if self.usd_rub_rate < 60:
            self.usd_rub_rate = 60
        if self.usd_rub_rate > 140:
            self.usd_rub_rate = 140
        
        self.rate_history.append(self.usd_rub_rate)
        if len(self.rate_history) > 50:
            self.rate_history.pop(0)
        self.rate_label.config(text=f"{self.usd_rub_rate:.2f}")
    
    def update_all_prices(self):
        """Обновление всех цен и новостей"""
        if not self.is_running:
            return
        
        for stock_name in self.stocks:
            self.generate_price(stock_name)
        self.generate_rate()
        
        # Новости по секторам
        if random.random() < 0.05:
            sectors = list(set([s["sector"] for s in self.stocks_data]))
            random_sector = random.choice(sectors)
            sector_stocks = [s for s in self.stocks_data if s["sector"] == random_sector]
            random_stock = random.choice(sector_stocks)
            
            if random.random() < 0.5:
                self.stocks[random_stock["name"]]["price"] *= 1.1
                self.news_label.config(text=f"📰 🟢 ХОРОШАЯ НОВОСТЬ! {random_stock['name']} ({random_sector}) выросла на +10%")
                self.show_message(f"🟢 {random_stock['name']} выросла на +10%", False)
            else:
                self.stocks[random_stock["name"]]["price"] *= 0.9
                self.news_label.config(text=f"📰 🔴 ПЛОХАЯ НОВОСТЬ! {random_stock['name']} ({random_sector}) упала на -10%")
                self.show_message(f"🔴 {random_stock['name']} упала на -10%", True)
        
        self.update_display()
        self.draw_chart()
    
    def update_display(self):
        """Обновление отображения"""
        self.usd_label.config(text=f"USD: ${self.usd_balance:.2f}")
        self.rub_label.config(text=f"RUB: {self.rub_balance:.2f} ₽")
        self.update_portfolio_display()
        
        # Обновляем информацию о текущей акции
        current = self.stocks[self.current_stock]
        self.root.title(f"📈 {self.current_stock} - ${current['price']:.2f} | Мультивалютный трейдер")
    
    def draw_chart(self):
        """Отрисовка графика"""
        self.canvas.delete("all")
        
        stock = self.stocks[self.current_stock]
        history = stock["history"]
        
        if len(history) < 2:
            return
        
        width = 840
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
        self.canvas.create_text(width-100, 40, text=f"{stock['sector']}",
                                 fill='#aaa', font=("Arial", 8))
    
    def buy_stock(self):
        """Покупка акций"""
        try:
            amount = int(self.amount_entry.get())
            if amount <= 0:
                self.show_message("❌ Введите положительное число", True)
                return
            
            price = self.stocks[self.current_stock]["price"]
            cost = amount * price
            
            if cost > self.usd_balance:
                self.show_message(f"❌ Недостаточно USD! Нужно ${cost:.2f}", True)
                return
            
            self.usd_balance -= cost
            self.portfolio[self.current_stock] += amount
            self.update_display()
            self.show_message(f"🟢 Куплено {amount} {self.current_stock} по ${price:.2f}", False)
        except ValueError:
            self.show_message("❌ Введите корректное число", True)
    
    def sell_stock(self):
        """Продажа акций"""
        try:
            amount = int(self.amount_entry.get())
            if amount <= 0:
                self.show_message("❌ Введите положительное число", True)
                return
            
            if amount > self.portfolio[self.current_stock]:
                self.show_message(f"❌ У вас только {self.portfolio[self.current_stock]} акций", True)
                return
            
            price = self.stocks[self.current_stock]["price"]
            revenue = amount * price
            self.usd_balance += revenue
            self.portfolio[self.current_stock] -= amount
            self.update_display()
            self.show_message(f"🔴 Продано {amount} {self.current_stock} по ${price:.2f}", False)
        except ValueError:
            self.show_message("❌ Введите корректное число", True)
    
    def convert_usd_to_rub(self):
        if self.usd_balance <= 0:
            self.show_message("❌ Нет долларов для конвертации", True)
            return
        rub_amount = self.usd_balance * self.usd_rub_rate
        self.rub_balance += rub_amount
        self.usd_balance = 0
        self.update_display()
        self.show_message(f"💱 Конвертировано ${self.usd_balance:.2f} → {rub_amount:.2f} ₽", False)
    
    def convert_rub_to_usd(self):
        if self.rub_balance <= 0:
            self.show_message("❌ Нет рублей для конвертации", True)
            return
        usd_amount = self.rub_balance / self.usd_rub_rate
        self.usd_balance += usd_amount
        self.rub_balance = 0
        self.update_display()
        self.show_message(f"💱 Конвертировано {self.rub_balance:.2f} ₽ → ${usd_amount:.2f}", False)
    
    def change_stock(self, stock_name):
        """Смена текущей акции"""
        self.current_stock = stock_name
        self.draw_chart()
        self.update_stock_list()
        self.update_display()
    
    def change_speed(self, val):
        """Изменение скорости обновления"""
        new_interval = int(float(val))
        self.update_interval = new_interval * 1000
        self.speed_status.config(text=f"({new_interval} сек)")
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
        
        for s in self.stocks_data:
            self.stocks[s["name"]]["price"] = s["price"]
            self.stocks[s["name"]]["history"] = [s["price"]]
            self.portfolio[s["name"]] = 0
        
        self.rate_history = [95]
        self.update_display()
        self.draw_chart()
        self.update_stock_list()
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
            
            for s in self.stocks_data:
                self.stocks[s["name"]]["price"] = s["price"]
                self.stocks[s["name"]]["history"] = [s["price"]]
                self.portfolio[s["name"]] = 0
            
            self.rate_history = [95]
            self.update_display()
            self.draw_chart()
            self.update_stock_list()
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
            "stock_prices": {name: self.stocks[name]["price"] for name in self.stocks},
            "stock_histories": {name: self.stocks[name]["history"] for name in self.stocks}
        }
        with open("trader_multi_22_save.json", "w") as f:
            json.dump(data, f)
        self.show_message("💾 Данные сохранены", False)
    
    def load_data(self):
        """Загрузка данных"""
        if os.path.exists("trader_multi_22_save.json"):
            try:
                with open("trader_multi_22_save.json", "r") as f:
                    data = json.load(f)
                self.usd_balance = data["usd_balance"]
                self.rub_balance = data["rub_balance"]
                self.usd_rub_rate = data["usd_rub_rate"]
                self.portfolio = data["portfolio"]
                for name, price in data["stock_prices"].items():
                    if name in self.stocks:
                        self.stocks[name]["price"] = price
                        self.stocks[name]["history"] = data["stock_histories"].get(name, [price])
                self.update_display()
                self.draw_chart()
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
