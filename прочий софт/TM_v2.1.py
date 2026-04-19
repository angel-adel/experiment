import tkinter as tk
from tkinter import scrolledtext, messagebox, filedialog
import pyautogui
import psutil
import GPUtil
import platform
import subprocess
import socket
import os
import re
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
from PIL import Image

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

log_info("Программа запущена")

# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========
def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "Не определён"

def check_internet(host="google.com", port=80, timeout=3):
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

def save_report(description, mode):
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
        
        # Вставляем скриншот как base64
        import base64
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

# ========== ОСНОВНОЙ КЛАСС ==========
class TroubleMessenger:
    def __init__(self, root):
        self.root = root
        self.root.title("Trouble Messenger — Ушастик v2.0")
        self.root.geometry("500x500")
        self.root.resizable(False, False)
        
        tk.Label(root, text="Опишите проблему:", font=("Arial", 12)).pack(pady=10)
        self.description = scrolledtext.ScrolledText(root, height=10, width=60, font=("Arial", 10))
        self.description.pack(pady=5, padx=10)
        
        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=20)
        
        self.quick_btn = tk.Button(btn_frame, text="💾 Быстрый отчёт", command=self.quick_report,
                                   bg="#3498db", fg="white", font=("Arial", 10), width=15)
        self.quick_btn.pack(side=tk.LEFT, padx=5)
        
        self.extended_btn = tk.Button(btn_frame, text="🔬 Расширенный отчёт", command=self.extended_report,
                                      bg="#e67e22", fg="white", font=("Arial", 10), width=18)
        self.extended_btn.pack(side=tk.LEFT, padx=5)
        
        self.open_folder_btn = tk.Button(btn_frame, text="📂 Папка с отчётами", command=self.open_reports_folder,
                                         bg="#2ecc71", fg="white", font=("Arial", 10), width=15)
        self.open_folder_btn.pack(side=tk.LEFT, padx=5)
        
        self.status = tk.Label(root, text="Готов", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status.pack(side=tk.BOTTOM, fill=tk.X)
        
        log_info("Интерфейс программы загружен")
    
    def quick_report(self):
        log_info("Пользователь нажал кнопку 'Быстрый отчёт'")
        desc = self.description.get("1.0", tk.END).strip()
        save_report(desc, 'quick')
    
    def extended_report(self):
        log_info("Пользователь нажал кнопку 'Расширенный отчёт'")
        desc = self.description.get("1.0", tk.END).strip()
        save_report(desc, 'extended')
    
    def open_reports_folder(self):
        log_info("Пользователь открыл папку с отчётами")
        if os.path.exists(REPORT_DIR):
            os.startfile(REPORT_DIR)
        else:
            log_warning("Папка Reports не найдена")
            messagebox.showwarning("Нет папки", "Папка Reports ещё не создана. Сначала сохраните хотя бы один отчёт.")

def on_closing():
    log_info("Программа закрыта пользователем")
    root.destroy()

# ========== ЗАПУСК ==========
if __name__ == "__main__":
    root = tk.Tk()
    app = TroubleMessenger(root)
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()
