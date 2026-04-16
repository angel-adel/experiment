import tkinter as tk
from tkinter import scrolledtext, messagebox
import pyautogui
from datetime import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import os
import re
import base64
from PIL import Image, ImageTk
import io

# ========== НАСТРОЙКИ SMTP (только сервер и порт, всё остальное вводит сотрудник) ==========
SMTP_SERVER = "smtp.gmail.com"      # Поменяй под свой сервер: smtp.mail.ru, smtp.yandex.ru и т.д.
SMTP_PORT = 587
# ===========================================================================================

# Встроенная иконка "Красный куб"
RED_CUBE_ICON_BASE64 = """
iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAADsMAAA7DAcdvqGQAAAAZdEVYdFNvZnR3YXJlAHBhaW50Lm5ldCA0LjAuMTM0A1t6AAAAJXRFWHRkYXRlOmNyZWF0ZQAyMDIyLTAxLTAxVDAwOjAwOjAwKzAwOjAwaG2FkQAAACV0RVh0ZGF0ZTptb2RpZnkAMjAyMi0wMS0wMVQwMDowMDowMCswMDowMMo0m+MAAAAZdEVYdFNvZnR3YXJlAHd3dy5pbmtzY2FwZS5vcmeb7jwaAAADHUlEQVRYhe2Wv2sUQRTHPzN7e3uXwEWKQIIQFBTBNhBbsbAPIhZqYxUb/wn/AhFBCBZWYpVKUIiF2FhYWFgIilYKamMREXKJxeXd7e7M9M/l7pLcXS6JkAtDHu+++b6ZN/PmzVtBZmbGGGOMGTnDwM+UQ+CHZqM1YAd4ALwA9oA9jUZrwDRhD3gAvGw02lOiCKC7P1qT0Xjf2i5Tyo6U8iHwDngOTKV5WQy4D3wHpspU1Gg0Xknp2SrnA28D9wBN6y5xN8BHIECj0Vhb4OcCcB84B2wA14ATYz0LWOvGvgeuk3Ub7AGvgO9Ae5y8cQK8Ah4DZ4CfgW9ACqwBO1LKxWkF1h3gBfAhAxy4BbyWUqZLHWBlCbgPPJZSvkgp/0opX0spf3h+pem8B+4BN6WUb6SUv6WUv6WUv6SUv6WUv6WUvz2X7kn3PI/0vFGSX9JzPU/0XK/neaLn1klyE6SUm1LKzZxQ0k1JKY/n3UQp5aYkxZRSbqbUewG4LqU8k1LmUspcSplLKXMpZS6lzKWUuZQyLwi9AIjjOF4AtjxjUeAZEItjqYoimjWmhE3P2A3DWASgM4pgIwxjEQDdMIxFADphGAeA7iiKRQB6URSPtYt+GMYiAL0oikeBvSiKR4G9KIpHgb0oikeBvSiKR4G9KIpHgb0oikeBvSiKR4G9KIpHgb0oikeBvSiKR4G9KIpHgb0oikeBvSiKR4G9KIpHgb0oikeBvSiKR4G9KIpHgb0oikeBvSiKR4G9KIpHgb0oikeBvSiKR4G9KIpHgb0oikeBvSiKR4G9KIpHgb0oikeBvSiKR4G9KIpHgb0oikeBvSiKR4G9KIpHgb0oikeBvSiKR4G9KIpHgb0oikeBvSiKR4G9KIpHgb0oikeBvSiKR4G9KIpHgb0oikeBvSiKR4G9KIpHgb0oikeBvSiKR4G9KIpHgb0oikeBvSiKR4H/AHktiFq3LJ6hAAAAAElFTkSuQmCC
"""

def get_red_cube_icon(size=(32, 32)):
    img_data = base64.b64decode(RED_CUBE_ICON_BASE64)
    img = Image.open(io.BytesIO(img_data))
    img = img.resize(size, Image.Resampling.LANCZOS)
    return ImageTk.PhotoImage(img)

class TroubleReporter:
    def __init__(self, root):
        self.root = root
        self.root.title("Trouble Tracker — Красный куб")
        self.root.geometry("550x600")
        self.root.resizable(False, False)

        # Иконка
        self.root.iconphoto(False, get_red_cube_icon())

        # Поле: от какого email отправляем (логин)
        tk.Label(root, text="🔐 Ваш технический email (от кого идёт отправка):", font=("Arial", 10, "bold")).pack(pady=(10,0))
        self.from_email = tk.Entry(root, width=50, font=("Arial", 10))
        self.from_email.pack(pady=5)
        tk.Label(root, text="Пример: robot@company.com", font=("Arial", 8), fg="gray").pack()

        # Поле: пароль приложения
        tk.Label(root, text="🔑 Пароль приложения (не обычный пароль):", font=("Arial", 10, "bold")).pack(pady=(5,0))
        self.password = tk.Entry(root, width=50, font=("Arial", 10), show="*")
        self.password.pack(pady=5)

        # Поле: кому отправить (разработчики)
        tk.Label(root, text="📧 Кому отправить (разработчики):", font=("Arial", 10, "bold")).pack(pady=(10,0))
        self.to_developers = tk.Entry(root, width=50, font=("Arial", 10))
        self.to_developers.pack(pady=5)
        tk.Label(root, text="Можно несколько через запятую: dev1@company.com, dev2@company.com", font=("Arial", 8), fg="gray").pack()

        # Поле: копия себе (email сотрудника)
        tk.Label(root, text="📋 Ваш email (копия себе):", font=("Arial", 10, "bold")).pack(pady=(10,0))
        self.user_email = tk.Entry(root, width=50, font=("Arial", 10))
        self.user_email.pack(pady=5)
        tk.Label(root, text="ivanov@company.com", font=("Arial", 8), fg="gray").pack()

        # Поле: описание проблемы
        tk.Label(root, text="📝 Опишите проблему:", font=("Arial", 12, "bold")).pack(pady=(10,0))
        self.description = scrolledtext.ScrolledText(root, height=8, width=60, font=("Arial", 10))
        self.description.pack(pady=5, padx=10)

        # Кнопка отправки
        self.send_btn = tk.Button(root, text="📸 Сделать скрин и отправить", command=self.take_screenshot_and_send,
                                  bg="#c0392b", fg="white", font=("Arial", 12, "bold"), height=2)
        self.send_btn.pack(pady=15)

        # Статус
        self.status = tk.Label(root, text="Готов", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status.pack(side=tk.BOTTOM, fill=tk.X)

    def update_status(self, msg):
        self.status.config(text=msg)
        self.root.update()

    def is_valid_email(self, email):
        return re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email) is not None

    def validate_emails_list(self, emails_str):
        """Проверяет список email'ов через запятую"""
        emails = [e.strip() for e in emails_str.split(',') if e.strip()]
        for email in emails:
            if not self.is_valid_email(email):
                return False, email
        return True, emails

    def take_screenshot_and_send(self):
        # Собираем данные из полей
        from_email = self.from_email.get().strip()
        password = self.password.get().strip()
        to_developers_str = self.to_developers.get().strip()
        user_email = self.user_email.get().strip()
        desc = self.description.get("1.0", tk.END).strip()

        # Валидация
        if not from_email:
            messagebox.showwarning("Внимание", "Введите email отправителя!")
            return
        if not password:
            messagebox.showwarning("Внимание", "Введите пароль приложения!")
            return
        if not to_developers_str:
            messagebox.showwarning("Внимание", "Введите email разработчиков (кому отправить)!")
            return
        if not user_email:
            messagebox.showwarning("Внимание", "Введите ваш email для копии!")
            return
        if not desc:
            messagebox.showwarning("Внимание", "Опишите проблему!")
            return

        # Проверяем корректность email'ов
        if not self.is_valid_email(from_email):
            messagebox.showwarning("Внимание", f"Некорректный email отправителя: {from_email}")
            return
        if not self.is_valid_email(user_email):
            messagebox.showwarning("Внимание", f"Некорректный ваш email: {user_email}")
            return

        valid, to_emails = self.validate_emails_list(to_developers_str)
        if not valid:
            messagebox.showwarning("Внимание", f"Некорректный email разработчика: {to_emails}")
            return

        # Блокируем кнопку
        self.send_btn.config(state=tk.DISABLED, text="Отправляю...")
        self.update_status("Делаю скриншот...")

        screenshot_filename = None
        try:
            # Скриншот
            screenshot = pyautogui.screenshot()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_filename = f"screenshot_{timestamp}.png"
            screenshot.save(screenshot_filename)

            # Отправка
            self.update_status("Отправляю письмо...")
            self.send_email(from_email, password, to_emails, user_email, desc, screenshot_filename)

            self.update_status("✅ Готово!")
            messagebox.showinfo("Успех", f"Отправлено!\nРазработчикам: {to_developers_str}\nКопия вам: {user_email}")
            
            # Очищаем поля (кроме технических — они могут сохраняться между отправками)
            self.description.delete("1.0", tk.END)
            self.user_email.delete(0, tk.END)
            # from_email и password не очищаем, чтобы не вводить заново

        except Exception as e:
            self.update_status("❌ Ошибка")
            messagebox.showerror("Ошибка", str(e))
        finally:
            if screenshot_filename and os.path.exists(screenshot_filename):
                os.remove(screenshot_filename)
            self.send_btn.config(state=tk.NORMAL, text="📸 Сделать скрин и отправить")

    def send_email(self, from_email, password, to_emails, cc_email, description, screenshot_path):
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = ', '.join(to_emails)
        msg['Cc'] = cc_email
        msg['Subject'] = f"Trouble Report от {cc_email} ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})"

        body = f"""Отчёт от сотрудника: {cc_email}
Дата и время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Описание проблемы:
{description}

---
Скриншот проблемы во вложении.
"""
        msg.attach(MIMEText(body, 'plain', 'utf-8'))

        with open(screenshot_path, 'rb') as f:
            img = MIMEImage(f.read(), name=os.path.basename(screenshot_path))
            msg.attach(img)

        # Отправляем (разработчики + копия сотруднику)
        all_recipients = to_emails + [cc_email]
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(from_email, password)
            server.send_message(msg, from_addr=from_email, to_addrs=all_recipients)

# Запуск
if __name__ == "__main__":
    root = tk.Tk()
    app = TroubleReporter(root)
    root.mainloop()
