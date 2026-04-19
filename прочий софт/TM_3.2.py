import tkinter as tk
from tkinter import scrolledtext, messagebox
import pyautogui
import psutil
import GPUtil
import platform
import subprocess
import socket
import os
import re
import smtplib
import base64
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

# ========== НАСТРОЙКИ SMTP ==========
SMTP_SERVERS = {
    'gmail.com': ('smtp.gmail.com', 587),
    'yandex.ru': ('smtp.yandex.ru', 587),
    'yandex.com': ('smtp.yandex.com', 587),
    'mail.ru': ('smtp.mail.ru', 587),
    'rambler.ru': ('smtp.rambler.ru', 587),
    'outlook.com': ('smtp-mail.outlook.com', 587),
    'hotmail.com': ('smtp-mail.outlook.com', 587),
    'live.com': ('smtp-mail.outlook.com', 587),
    'yahoo.com': ('smtp.mail.yahoo.com', 587),
    'yahoo.fr': ('smtp.mail.yahoo.com', 587),
    'icloud.com': ('smtp.mail.me.com', 587),
    'me.com': ('smtp.mail.me.com', 587),
    'aol.com': ('smtp.aol.com', 587),
    'zoho.com': ('smtp.zoho.com', 587),
}

def get_smtp_server(email):
    domain = email.split('@')[-1].lower()
    if domain in SMTP_SERVERS:
        server, port = SMTP_SERVERS[domain]
        return server, port, None
    else:
        return None, None, f"Неизвестный домен: {domain}"

# ========== НАСТРОЙКА ЛОГИРОВАНИЯ ==========
LOG_DIR = "Logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

log_file = os.path.join(LOG_DIR, "ushatik.log")
log_handler = RotatingFileHandler(log_file, maxBytes=1_000_000, backupCount=1)
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
log_handler.setFormatter(log_formatter)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(log_handler)

def log_info(msg):
    logger.info(msg)
    print(f"[INFO] {msg}")

def log_warning(msg):
    logger.warning(msg)
    print(f"[WARN] {msg}")

def log_error(msg):
    logger.error(msg)
    print(f"[ERROR] {msg}")

# ========== КОНСТАНТЫ ==========
REPORT_DIR = "Reports"
if not os.path.exists(REPORT_DIR):
    os.makedirs(REPORT_DIR)

log_info("Программа запущена (Trouble Messenger 3.2)")

# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ДЛЯ ДИАГНОСТИКИ ==========
def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "Не определён"

def check_internet(host="google.com", timeout=3):
    try:
        start = datetime.now()
        subprocess.check_output(["ping", "-n", "1", host], timeout=timeout)
        delta = (datetime.now() - start).total_seconds() * 1000
        return True, round(delta, 1)
    except:
        return False, None

def get_gpu_info():
    try:
        gpus = GPUtil.getGPUs()
        if gpus:
            gpu = gpus[0]
            return gpu.name, gpu.driver
        else:
            return "Встроенная графика Intel", "Неизвестно"
    except:
        return "Не удалось определить", "Ошибка"

def get_system_info():
    info = {}
    info['os'] = f"{platform.system()} {platform.release()} ({platform.version()})"
    info['arch'] = platform.machine()
    info['cpu_model'] = platform.processor()
    info['cpu_cores'] = psutil.cpu_count(logical=True)
    info['cpu_phys'] = psutil.cpu_count(logical=False)
    info['cpu_freq'] = psutil.cpu_freq().current if psutil.cpu_freq() else 0
    info['cpu_percent'] = psutil.cpu_percent(interval=1)
    mem = psutil.virtual_memory()
    info['ram_total'] = round(mem.total / (1024**3), 1)
    info['ram_used'] = round(mem.used / (1024**3), 1)
    info['ram_percent'] = mem.percent
    disks = []
    for part in psutil.disk_partitions():
        try:
            usage = psutil.disk_usage(part.mountpoint)
            disks.append({
                'mount': part.mountpoint,
                'total': round(usage.total / (1024**3), 1),
                'free': round(usage.free / (1024**3), 1),
                'percent': usage.percent
            })
        except:
            continue
    info['disks'] = disks
    return info

def get_top_processes(n=10):
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info']):
        try:
            pinfo = proc.info
            cpu = pinfo['cpu_percent'] or 0
            mem = round(pinfo['memory_info'].rss / (1024**2), 1) if pinfo['memory_info'] else 0
            processes.append({
                'name': pinfo['name'],
                'pid': pinfo['pid'],
                'cpu': cpu,
                'mem': mem
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    processes.sort(key=lambda x: x['cpu'], reverse=True)
    return processes[:n]

def take_screenshot():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"screenshot_{timestamp}.png"
    screenshot = pyautogui.screenshot()
    screenshot.save(filename)
    log_info(f"Скриншот создан: {filename}")
    return filename

def get_last_log_lines(n=30):
    log_file_path = os.path.join(LOG_DIR, "ushatik.log")
    if not os.path.exists(log_file_path):
        return "Лог-файл ещё не создан."
    try:
        with open(log_file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        last_lines = lines[-n:] if len(lines) > n else lines
        return ''.join(last_lines)
    except Exception as e:
        return f"Ошибка чтения лога: {e}"

# ========== ПОСТРОЕНИЕ HTML-ОТЧЁТОВ ==========
def build_html_report(description, screenshot_path, mode='quick'):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    local_ip = get_local_ip()
    
    basic_info = f"""
    <li><strong>ОС:</strong> {platform.system()} {platform.release()}</li>
    <li><strong>Разрядность:</strong> {platform.machine()}</li>
    <li><strong>Разрешение экрана:</strong> {pyautogui.size().width}x{pyautogui.size().height}</li>
    <li><strong>Локальный IP:</strong> {local_ip}</li>
    <li><strong>Время:</strong> {timestamp}</li>
    """
    
    if mode == 'quick':
        html = f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><title>Быстрый отчёт</title>
<style>
    body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
    .container {{ max-width: 800px; margin: auto; background: white; padding: 20px; border-radius: 8px; }}
    h1 {{ color: #c0392b; }}
    .info {{ background: #f0f0f0; padding: 15px; border-radius: 8px; margin: 15px 0; }}
    .screenshot {{ text-align: center; margin: 20px 0; }}
    img {{ max-width: 100%; border: 1px solid #ccc; border-radius: 4px; }}
</style>
</head>
<body>
<div class="container">
    <h1>🐞 Быстрый отчёт о проблеме</h1>
    <h2>📝 Описание</h2>
    <div class="info">{description}</div>
    <h2>💻 Система</h2>
    <ul>{basic_info}</ul>
    <h2>📸 Скриншот</h2>
    <div class="screenshot"><img src="{screenshot_path}" alt="Скриншот"></div>
    <hr><p style="text-align:center;">Отправьте этот файл на почту: adel.angel2026@gmail.com</p>
</div>
</body>
</html>"""
    else:
        internet, ping = check_internet()
        gpu_name, gpu_driver = get_gpu_info()
        sys = get_system_info()
        top_proc = get_top_processes(10)
        
        net_html = f"<li><strong>Интернет:</strong> {'✅ есть' if internet else '❌ нет'}"
        if internet and ping:
            net_html += f" (ping {ping} мс)"
        net_html += f"</li><li><strong>Локальный IP:</strong> {local_ip}</li>"
        
        gpu_html = f"<li><strong>Модель:</strong> {gpu_name}</li><li><strong>Драйвер:</strong> {gpu_driver}</li>"
        
        sys_html = f"""
        <li><strong>ОС:</strong> {sys['os']} ({sys['arch']})</li>
        <li><strong>Процессор:</strong> {sys['cpu_model']}</li>
        <li><strong>Ядер:</strong> {sys['cpu_phys']} физических / {sys['cpu_cores']} логических</li>
        <li><strong>Частота:</strong> {sys['cpu_freq']:.0f} МГц</li>
        <li><strong>Загрузка CPU:</strong> {sys['cpu_percent']}%</li>
        <li><strong>ОЗУ:</strong> {sys['ram_used']} ГБ / {sys['ram_total']} ГБ ({sys['ram_percent']}%)</li>
        """
        
        disks_html = ""
        for d in sys['disks']:
            disks_html += f"<li>{d['mount']}: {d['free']} ГБ свободно из {d['total']} ГБ ({d['percent']}% занято)</li>"
        
        proc_html = "<table border='1' cellpadding='5'><tr><th>Процесс</th><th>CPU</th><th>Память (МБ)</th><th>PID</th></tr>"
        for p in top_proc:
            proc_html += f"<tr><td>{p['name']}</td><td>{p['cpu']:.1f}%</td><td>{p['mem']}</td><td>{p['pid']}</td></tr>"
        proc_html += "</table>"
        
        html = f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><title>Расширенный отчёт</title>
<style>
    body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
    .container {{ max-width: 1000px; margin: auto; background: white; padding: 20px; border-radius: 8px; }}
    h1 {{ color: #c0392b; }} h2 {{ color: #333; }}
    .info {{ background: #f0f0f0; padding: 15px; border-radius: 8px; margin: 15px 0; }}
    .screenshot {{ text-align: center; margin: 20px 0; }}
    img {{ max-width: 100%; border: 1px solid #ccc; border-radius: 4px; }}
    table {{ border-collapse: collapse; width: 100%; margin: 10px 0; }}
    th, td {{ padding: 8px; text-align: left; }}
</style>
</head>
<body>
<div class="container">
    <h1>🔬 Расширенный отчёт о проблеме</h1>
    <h2>📝 Описание</h2>
    <div class="info">{description}</div>
    <h2>🌐 Сеть</h2>
    <ul>{net_html}</ul>
    <h2>🎮 Видеокарта</h2>
    <ul>{gpu_html}</ul>
    <h2>💻 Система (анонимно)</h2>
    <ul>{sys_html}</ul>
    <h2>💾 Диски</h2>
    <ul>{disks_html}</ul>
    <h2>⚙️ Топ-10 процессов по CPU</h2>
    {proc_html}
    <h2>📸 Скриншот</h2>
    <div class="screenshot"><img src="{screenshot_path}" alt="Скриншот"></div>
    <hr><p style="text-align:center;">Отправьте этот файл на почту: adel.angel2026@gmail.com</p>
</div>
</body>
</html>"""
    
    return html

def save_offline_report(description, mode):
    if not description.strip():
        log_warning("Попытка сохранить отчёт с пустым описанием")
        messagebox.showwarning("Внимание", "Опишите проблему!")
        return None
    
    screenshot_file = None
    try:
        screenshot_file = take_screenshot()
        html_content = build_html_report(description, screenshot_file, mode)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{'quick' if mode == 'quick' else 'extended'}_report_{timestamp}.html"
        filepath = os.path.join(REPORT_DIR, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        with open(screenshot_file, "rb") as img_f:
            img_data = base64.b64encode(img_f.read()).decode()
            with open(filepath, 'r', encoding='utf-8') as f:
                html = f.read()
            html = html.replace(screenshot_file, f"data:image/png;base64,{img_data}")
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html)
        
        log_info(f"Отчёт сохранён: {filepath} (режим {mode})")
        messagebox.showinfo("Успех", f"Отчёт сохранён:\n{filepath}")
        return filepath
    except Exception as e:
        log_error(f"Ошибка сохранения отчёта: {str(e)}")
        messagebox.showerror("Ошибка", f"Не удалось сохранить отчёт:\n{str(e)}")
        return None
    finally:
        if screenshot_file and os.path.exists(screenshot_file):
            os.remove(screenshot_file)
            log_info(f"Временный скриншот удалён: {screenshot_file}")

# ========== ОТПРАВКА ПО ПОЧТЕ (С ЛОГАМИ) ==========
def send_email(from_email, password, to_emails, cc_email, description, screenshot_path, smtp_server, smtp_port):
    try:
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = ', '.join(to_emails)
        msg['Cc'] = cc_email
        msg['Subject'] = f"Trouble Report от {cc_email} ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})"

        # Принудительно создаём лог-файл, если его нет
        log_file_path = os.path.join(LOG_DIR, "ushatik.log")
        if not os.path.exists(log_file_path):
            with open(log_file_path, 'w', encoding='utf-8') as f:
                f.write("=== Лог-файл создан автоматически ===\n")
            log_info("Лог-файл не существовал, создан новый.")

        # Принудительно читаем последние 30 строк (с запасом)
        try:
            with open(log_file_path, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
            last_lines = all_lines[-30:] if len(all_lines) >= 30 else all_lines
            last_log = ''.join(last_lines)
            if not last_log.strip():
                last_log = "(Лог пуст)"
        except Exception as e:
            last_log = f"(Ошибка чтения лога: {e})"
        
        body = f"""Отчёт от сотрудника: {cc_email}
Дата и время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Описание проблемы:
{description}

--- Последние события из лога (30 строк) ---
{last_log}

---
Скриншот и полный лог-файл во вложениях.
"""
        msg.attach(MIMEText(body, 'plain', 'utf-8'))

        # Вложение: скриншот
        with open(screenshot_path, 'rb') as f:
            img = MIMEImage(f.read(), name=os.path.basename(screenshot_path))
            msg.attach(img)
        
        # Вложение: лог-файл
        if os.path.exists(log_file_path):
            with open(log_file_path, 'rb') as f:
                log_content = f.read().decode('utf-8', errors='replace')
                log_attachment = MIMEText(log_content, 'plain', 'utf-8')
                log_attachment.add_header('Content-Disposition', 'attachment', filename='ushatik.log')
                msg.attach(log_attachment)
            log_info("Лог-файл прикреплён к письму")
        else:
            log_warning("Лог-файл не найден, вложение не добавлено")

        all_recipients = to_emails + [cc_email]
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(from_email, password)
            server.send_message(msg, from_addr=from_email, to_addrs=all_recipients)
        
        log_info(f"Письмо отправлено: от {from_email}, кому {', '.join(to_emails)}, копия {cc_email}")
        return True
    except Exception as e:
        log_error(f"Ошибка отправки письма: {str(e)}")
        raise e

def send_report_by_email(description, mode, from_email, password, to_emails, cc_email):
    if not description.strip():
        log_warning("Попытка отправить письмо с пустым описанием")
        messagebox.showwarning("Внимание", "Опишите проблему!")
        return False
    
    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', from_email):
        messagebox.showwarning("Ошибка", "Некорректный email отправителя")
        return False
    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', cc_email):
        messagebox.showwarning("Ошибка", "Некорректный ваш email")
        return False
    
    to_list = [email.strip() for email in to_emails.split(',') if email.strip()]
    for email in to_list:
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            messagebox.showwarning("Ошибка", f"Некорректный email разработчика: {email}")
            return False
    
    smtp_server, smtp_port, error = get_smtp_server(from_email)
    if smtp_server is None:
        messagebox.showerror("Ошибка", f"Не удалось определить SMTP сервер для {from_email}\n{error}")
        return False
    
    screenshot_file = None
    try:
        screenshot_file = take_screenshot()
        send_email(from_email, password, to_list, cc_email, description, screenshot_file, smtp_server, smtp_port)
        messagebox.showinfo("Успех", "Письмо отправлено!")
        log_info(f"Письмо успешно отправлено (режим {mode})")
        return True
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось отправить письмо:\n{str(e)}")
        return False
    finally:
        if screenshot_file and os.path.exists(screenshot_file):
            os.remove(screenshot_file)
            log_info(f"Временный скриншот удалён: {screenshot_file}")

# ========== ОСНОВНОЙ КЛАСС ПРОГРАММЫ ==========
class TroubleMessenger:
    def __init__(self, root):
        self.root = root
        self.root.title("Trouble Messenger 3.2 — Ушастик")
        self.root.geometry("550x600")
        self.root.resizable(False, False)
        
        tk.Label(root, text="Опишите проблему:", font=("Arial", 12)).pack(pady=10)
        self.description = scrolledtext.ScrolledText(root, height=8, width=60, font=("Arial", 10))
        self.description.pack(pady=5, padx=10)
        
        tk.Label(root, text="Ваш технический email (от кого идёт отправка):", font=("Arial", 10)).pack(pady=(10,0))
        self.from_email = tk.Entry(root, width=50, font=("Arial", 10))
        self.from_email.pack(pady=5)
        
        tk.Label(root, text="Пароль приложения:", font=("Arial", 10)).pack(pady=(5,0))
        self.password = tk.Entry(root, width=50, font=("Arial", 10), show="*")
        self.password.pack(pady=5)
        
        tk.Label(root, text="Кому отправить (разработчики):", font=("Arial", 10)).pack(pady=(10,0))
        self.to_developers = tk.Entry(root, width=50, font=("Arial", 10))
        self.to_developers.pack(pady=5)
        tk.Label(root, text="Можно несколько через запятую", font=("Arial", 8), fg="gray").pack()
        
        tk.Label(root, text="Ваш email (копия себе):", font=("Arial", 10)).pack(pady=(10,0))
        self.user_email = tk.Entry(root, width=50, font=("Arial", 10))
        self.user_email.pack(pady=5)
        
        self.stealth_var = tk.BooleanVar(value=False)
        self.stealth_check = tk.Checkbutton(root, text="Сворачивать окно перед скриншотом (тихий режим)",
                                            variable=self.stealth_var)
        self.stealth_check.pack(pady=10)
        
        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=10)
        
        self.quick_btn = tk.Button(btn_frame, text="💾 Быстрый отчёт", command=self.quick_report,
                                   bg="#3498db", fg="white", font=("Arial", 10), width=14)
        self.quick_btn.pack(side=tk.LEFT, padx=5)
        
        self.extended_btn = tk.Button(btn_frame, text="🔬 Расширенный отчёт", command=self.extended_report,
                                      bg="#e67e22", fg="white", font=("Arial", 10), width=16)
        self.extended_btn.pack(side=tk.LEFT, padx=5)
        
        self.email_btn = tk.Button(btn_frame, text="📧 Отправить по почте", command=self.email_report,
                                   bg="#c0392b", fg="white", font=("Arial", 10), width=16)
        self.email_btn.pack(side=tk.LEFT, padx=5)
        
        self.folder_btn = tk.Button(btn_frame, text="📂 Папка с отчётами", command=self.open_reports_folder,
                                    bg="#2ecc71", fg="white", font=("Arial", 10), width=16)
        self.folder_btn.pack(side=tk.LEFT, padx=5)
        
        self.status = tk.Label(root, text="Готов", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status.pack(side=tk.BOTTOM, fill=tk.X)
        
        log_info("Интерфейс программы загружен (Trouble Messenger 3.2)")
    
    def minimize_window(self):
        self.root.iconify()
        self.root.update()
    
    def restore_window(self):
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
        self.root.update()
    
    def quick_report(self):
        log_info("Пользователь нажал 'Быстрый отчёт'")
        desc = self.description.get("1.0", tk.END).strip()
        if self.stealth_var.get():
            self.minimize_window()
        save_offline_report(desc, 'quick')
        if self.stealth_var.get():
            self.restore_window()
    
    def extended_report(self):
        log_info("Пользователь нажал 'Расширенный отчёт'")
        desc = self.description.get("1.0", tk.END).strip()
        if self.stealth_var.get():
            self.minimize_window()
        save_offline_report(desc, 'extended')
        if self.stealth_var.get():
            self.restore_window()
    
    def email_report(self):
        log_info("Пользователь нажал 'Отправить по почте'")
        desc = self.description.get("1.0", tk.END).strip()
        from_email = self.from_email.get().strip()
        password = self.password.get().strip()
        to_emails = self.to_developers.get().strip()
        cc_email = self.user_email.get().strip()
        
        if not from_email or not password or not to_emails or not cc_email:
            messagebox.showwarning("Внимание", "Заполните все поля для отправки по почте!")
            return
        
        if self.stealth_var.get():
            self.minimize_window()
        send_report_by_email(desc, 'email', from_email, password, to_emails, cc_email)
        if self.stealth_var.get():
            self.restore_window()
    
    def open_reports_folder(self):
        log_info("Пользователь открыл папку с отчётами")
        if os.path.exists(REPORT_DIR):
            os.startfile(REPORT_DIR)
        else:
            messagebox.showwarning("Нет папки", "Папка Reports ещё не создана. Сначала сохраните хотя бы один отчёт.")

def on_closing():
    log_info("Программа закрыта пользователем")
    root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = TroubleMessenger(root)
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()
