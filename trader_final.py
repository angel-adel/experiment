import tkinter as tk
from tkinter import ttk
import random
import json
import os
from datetime import datetime

class UltimateTraderSimulator:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("📈 Трейдер - RSI + Турнир")
        self.root.geometry("950x900")
        self.root.configure(bg='#0a0f1c')
        
        # ... (здесь те же 22 акции, что и раньше) ...
        self.stocks_data = [...]
        # ... (инициализация stocks, portfolio и т.д.) ...
        
        # RSI
        self.current_rsi = 50
        
        # Турнир
        self.daily_score = 0
        self.daily_moves = 0
        self.best_daily_score = 0
        self.weekly_score = 0
        self.weekly_moves = 0
        self.best_weekly_score = 0
        self.tournament_mode = "daily"
        self.tournament_active = False
        
        self.load_records()
        self.setup_ui()
        # ... остальной код ...
    
    def calculate_rsi(self, prices, period=14):
        if len(prices) < period + 1:
            return 50
        gains = 0
        losses = 0
        for i in range(-period, 0):
            change = prices[i] - prices[i-1]
            if change > 0:
                gains += change
            else:
                losses -= change
        avg_gain = gains / period
        avg_loss = losses / period
        if avg_loss == 0:
            return 100
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))
    
    def update_rsi(self):
        stock = self.stocks[self.current_stock]
        self.current_rsi = self.calculate_rsi(stock["history"])
        self.rsi_label.config(text=f"RSI(14): {self.current_rsi:.1f}")
        
        if self.current_rsi > 70:
            self.rsi_label.config(fg='#e74c3c')
            self.rsi_signal.config(text="📉 ПЕРЕКУПЛЕНО! ПОРА ПРОДАВАТЬ", fg='#e74c3c')
        elif self.current_rsi < 30:
            self.rsi_label.config(fg='#2ecc71')
            self.rsi_signal.config(text="📈 ПЕРЕПРОДАНО! ПОРА ПОКУПАТЬ", fg='#2ecc71')
        else:
            self.rsi_label.config(fg='#f39c12')
            self.rsi_signal.config(text="⚖️ НЕЙТРАЛЬНО", fg='#f39c12')
    
    def update_tournament(self, profit):
        if not self.tournament_active:
            return
        
        if self.tournament_mode == "daily":
            self.daily_score += profit
            self.daily_moves += 1
            if self.daily_moves >= 50:
                self.end_tournament()
        else:
            self.weekly_score += profit
            self.weekly_moves += 1
            if self.weekly_moves >= 250:
                self.end_tournament()
        self.update_tournament_display()
    
    def end_tournament(self):
        self.tournament_active = False
        final_score = self.daily_score if self.tournament_mode == "daily" else self.weekly_score
        best_score = self.best_daily_score if self.tournament_mode == "daily" else self.best_weekly_score
        
        if final_score > best_score:
            if self.tournament_mode == "daily":
                self.best_daily_score = final_score
            else:
                self.best_weekly_score = final_score
            self.save_records()
            self.show_message(f"🏆 НОВЫЙ РЕКОРД! {final_score:.0f} очков! 🏆", False)
        else:
            self.show_message(f"🏁 ТУРНИР ЗАВЕРШЁН! Результат: {final_score:.0f} очков. Рекорд: {best_score:.0f}", False)
        self.update_tournament_display()
    
    def start_tournament(self, mode):
        self.tournament_active = True
        self.tournament_mode = mode
        if mode == "daily":
            self.daily_score = 0
            self.daily_moves = 0
            self.show_message("🏆 ДНЕВНОЙ ТУРНИР НАЧАТ! 50 ходов", False)
        else:
            self.weekly_score = 0
            self.weekly_moves = 0
            self.show_message("🏆 НЕДЕЛЬНЫЙ ТУРНИР НАЧАТ! 250 ходов", False)
        self.update_tournament_display()
    
    def update_tournament_display(self):
        if self.tournament_active:
            if self.tournament_mode == "daily":
                text = f"📅 ДНЕВНОЙ: {self.daily_score:.0f} очков (ход {self.daily_moves}/50)"
            else:
                text = f"📆 НЕДЕЛЬНЫЙ: {self.weekly_score:.0f} очков (ход {self.weekly_moves}/250)"
        else:
            text = "⚡ ТУРНИР НЕ АКТИВЕН"
        self.tournament_status.config(text=text)
        self.best_daily_label.config(text=f"🏆 Дневной: {self.best_daily_score:.0f}")
        self.best_weekly_label.config(text=f"🏆 Недельный: {self.best_weekly_score:.0f}")
    
    def load_records(self):
        if os.path.exists("trader_records.json"):
            try:
                with open("trader_records.json", "r") as f:
                    data = json.load(f)
                self.best_daily_score = data.get("best_daily_score", 0)
                self.best_weekly_score = data.get("best_weekly_score", 0)
            except:
                pass
    
    def save_records(self):
        with open("trader_records.json", "w") as f:
            json.dump({
                "best_daily_score": self.best_daily_score,
                "best_weekly_score": self.best_weekly_score
            }, f)
