import os
import shutil
import ctypes
import tempfile
import sys
import json
from pystray import Icon, MenuItem, Menu
from PIL import Image, ImageDraw
# ==============================
#  Seasonal tray icons
# ==============================

def create_halloween_icon():
    """Создаёт иконку-тыкву для Хэллоуина"""
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    draw.ellipse((8, 12, 56, 52), fill=(255, 120, 0))
    draw.arc((8, 12, 56, 52), start=0, end=180, fill=(230, 100, 0), width=2)
    draw.arc((8, 12, 56, 52), start=180, end=360, fill=(230, 100, 0), width=2)
    draw.line((32, 12, 32, 52), fill=(230, 100, 0), width=2)
    draw.line((20, 16, 20, 48), fill=(230, 100, 0), width=1)
    draw.line((44, 16, 44, 48), fill=(230, 100, 0), width=1)
    draw.polygon([(22, 28), (28, 20), (34, 28)], fill="black")
    draw.polygon([(30, 28), (36, 20), (42, 28)], fill="black")
    draw.arc((20, 32, 44, 48), start=0, end=180, fill="black", width=3)
    draw.rectangle((26, 38, 30, 44), fill="white")
    draw.rectangle((34, 38, 38, 44), fill="white")
    draw.rectangle((30, 6, 34, 16), fill=(50, 180, 50))
    draw.polygon([(30, 6), (24, 2), (28, 6)], fill=(50, 180, 50))
    return img

def create_christmas_icon():
    """Создаёт иконку-ёлочку для Нового года и Рождества"""
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    draw.polygon([(32, 52), (12, 32), (52, 32)], fill=(34, 139, 34))
    draw.polygon([(32, 40), (18, 26), (46, 26)], fill=(50, 205, 50))
    draw.polygon([(32, 28), (24, 18), (40, 18)], fill=(60, 220, 60))
    draw.rectangle((28, 52, 36, 58), fill=(139, 69, 19))
    draw.polygon([(32, 8), (34, 12), (38, 12), (35, 15), (36, 19), (32, 17), (28, 19), (29, 15), (26, 12), (30, 12)], fill=(255, 215, 0))
    
    decorations = [(20, 34, 3, 255, 0, 0), (44, 34, 3, 255, 0, 0),
                   (26, 24, 2, 255, 165, 0), (38, 24, 2, 255, 165, 0),
                   (32, 44, 3, 255, 215, 0), (19, 26, 2, 255, 0, 0),
                   (45, 26, 2, 255, 0, 0)]
    for x, y, r, R, G, B in decorations:
        draw.ellipse((x - r, y - r, x + r, y + r), fill=(R, G, B))
    
    for x in range(18, 48, 4):
        draw.line((x, 32, x + 2, 34), fill=(255, 215, 0), width=1)
    return img

def get_active_event():
    """Определяет активный ивент по текущей дате"""
    now = datetime.now()
    month = now.month
    day = now.day
    if (month == 10 and day >= 30) or (month == 11 and day <= 3):
        return "halloween"
    elif (month == 12 and day >= 10) or (month == 1 and day <= 10):
        return "newyear"
    return None

def is_event_active(event_name):
    return get_active_event() == event_name

import threading
import time
from datetime import datetime
import subprocess
import tkinter as tk
import random
import winreg

# ==============================
#  Блокировка повторного запуска
# ==============================
MUTEX_NAME = "CleaneyTrayAppMutex_SingleInstance_2024"

def check_single_instance():
    try:
        mutex = ctypes.windll.kernel32.CreateMutexW(None, False, MUTEX_NAME)
        if ctypes.windll.kernel32.GetLastError() == 183:
            return False, None
        return True, mutex
    except Exception as e:
        print(f"Ошибка проверки экземпляра: {e}")
        return True, None

def show_already_running_notification():
    try:
        hwnd = ctypes.windll.user32.FindWindowW(None, "Cleaney")
        if hwnd:
            ctypes.windll.user32.ShowWindow(hwnd, 5)
            ctypes.windll.user32.SetForegroundWindow(hwnd)
        title = "Cleaney"
        message = "Приложение уже запущено и работает в системном трее"
        try:
            from winotify import Notification, audio
            toast = Notification(app_id=title, title=title, msg=message, duration="short")
            toast.set_audio(audio.Default, loop=False)
            toast.show()
        except ImportError:
            ps_script = f'''
            [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType=WindowsRuntime] | Out-Null
            [Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType=WindowsRuntime] | Out-Null
            $x = New-Object Windows.Data.Xml.Dom.XmlDocument
            $x.LoadXml('<toast><visual><binding template="ToastGeneric"><text>{title}</text><text>{message}</text></binding></visual></toast>')
            [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("{title}").Show([Windows.UI.Notifications.ToastNotification]::new($x))
            '''
            subprocess.Popen(["powershell", "-WindowStyle", "Hidden", "-Command", ps_script],
                           creationflags=subprocess.CREATE_NO_WINDOW)
    except Exception as e:
        print(f"Ошибка показа уведомления: {e}")

is_first_instance, mutex_handle = check_single_instance()
if not is_first_instance:
    show_already_running_notification()
    sys.exit(0)

# ==============================
#  Пути
# ==============================
def get_app_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

def get_config_path():
    return os.path.join(get_app_dir(), 'cleaner_config.json')

# ==============================
#  Языки
# ==============================
LANGUAGES = {
    "ru": {
        "name": "Русский", "app_name": "Cleaney", "startup_msg": "Запущен. Кликните по иконке в трее",
        "already_running": "Приложение уже запущено и работает в системном трее", "cleaned": "Очищено",
        "recycle_cleaned": "Корзина очищена", "temp_cleaned": "TEMP очищен", "temp_cleaned_msg": "TEMP очищен ({} объектов)",
        "error_recycle": "Корзина: {}", "error_temp": "TEMP: {}", "done": "Готово", "cleaned_all": "TEMP и корзина очищены",
        "auto_clean": "Автоочистка", "auto_cleaned": "Очищено: {}", "auto_enabled": "Автоочистка ВКЛ. Каждые {}",
        "auto_disabled": "Автоочистка ВЫКЛ", "interval_changed": "Очистка каждые ", "error_input": "Введите число больше 0",
        "menu_clear_all": "Очистить всё", "menu_clear_recycle": "Очистить корзину", "menu_clear_temp": "Очистить TEMP",
        "menu_settings": "Настройки", "menu_exit": "Выход", "settings_title": "Cleaney — Настройки",
        "quick_actions": "⚡ БЫСТРЫЕ ДЕЙСТВИЯ", "btn_all": "🧹 Всё", "btn_recycle": "🗑 Корзина",
        "btn_temp": "📁 TEMP", "auto_cleanup": "🤖 АВТООЧИСТКА", "enable_auto": "Включить автоочистку",
        "clean_temp": "Очищать TEMP", "clean_recycle": "Очищать корзину", "enable_ram": "Очищать RAM",
        "interval": "⏱️ ИНТЕРВАЛ", "every": "Каждые:", "min": "мин", "hour": "час", "day": "дн",
        "minutes": "мин", "hours": "ч", "days": "дн", "status": "📊 СТАТУС", "auto_status": "Автоочистка:",
        "on": "ВКЛ ●", "off": "ВЫКЛ ●", "last": "Последняя очистка:", "never": "никогда", "close": "Закрыть",
        "preset_30min": "30 мин", "preset_1h": "1 ч", "preset_6h": "6 ч", "preset_12h": "12 ч", "preset_1d": "1 дн",
        "startup": "🚀 АВТОЗАГРУЗКА", "enable_startup": "Запускать при старте Windows", "startup_enabled": "Автозагрузка ВКЛ",
        "startup_disabled": "Автозагрузка ВЫКЛ", "skipped": "занято", "btn_ram": "🧠 RAM",
        "ram_cleaned": "Оперативная память очищена", "ram_freed": "Освобождено ~{} МБ", "error_ram": "RAM: {}",
        "clean_ram": "Очищать RAM", "menu_clear_ram": "Очистить RAM", "about": "О программе", "customize": "Кастомизация",
        "theme_saved": "Тема применена", "col_name": "Имя", "col_from": "Из папки",
    },
    "en": {
        "name": "English", "app_name": "Cleaney", "startup_msg": "Started. Click the tray icon",
        "already_running": "Application is already running in the system tray", "cleaned": "Cleaned",
        "recycle_cleaned": "Recycle bin cleaned", "temp_cleaned": "TEMP cleaned", "temp_cleaned_msg": "TEMP cleaned ({} items)",
        "error_recycle": "Recycle bin: {}", "error_temp": "TEMP: {}", "done": "Done", "cleaned_all": "TEMP and recycle bin cleaned",
        "auto_clean": "Auto Cleanup", "auto_cleaned": "Cleaned: {}", "auto_enabled": "Auto cleanup ON. Every {}",
        "auto_disabled": "Auto cleanup OFF", "interval_changed": "Cleanup every ", "error_input": "Enter a number greater than 0",
        "menu_clear_all": "Clear All", "menu_clear_recycle": "Clear Recycle Bin", "menu_clear_temp": "Clear TEMP",
        "menu_settings": "Settings", "menu_exit": "Exit", "settings_title": "Cleaney — Settings",
        "quick_actions": "⚡ QUICK ACTIONS", "btn_all": "🧹 All", "btn_recycle": "🗑 Recycle", "btn_temp": "📁 TEMP",
        "auto_cleanup": "🤖 AUTO CLEANUP", "enable_auto": "Enable auto cleanup", "clean_temp": "Clean TEMP",
        "clean_recycle": "Clean recycle bin", "enable_ram": "Clean RAM", "interval": "⏱️ INTERVAL",
        "every": "Every:", "min": "min", "hour": "hr", "day": "day", "minutes": "min", "hours": "hr", "days": "day",
        "status": "📊 STATUS", "auto_status": "Auto cleanup:", "on": "ON ●", "off": "OFF ●",
        "last": "Last cleanup:", "never": "never", "close": "Close", "preset_30min": "30 min", "preset_1h": "1 hr",
        "preset_6h": "6 hr", "preset_12h": "12 hr", "preset_1d": "1 day", "startup": "🚀 AUTOSTART",
        "enable_startup": "Run at Windows startup", "startup_enabled": "Autostart ON", "startup_disabled": "Autostart OFF",
        "skipped": "in use", "btn_ram": "🧠 RAM", "ram_cleaned": "RAM cleaned", "ram_freed": "Freed ~{} MB",
        "error_ram": "RAM: {}", "clean_ram": "Clean RAM", "menu_clear_ram": "Clear RAM",
        "about": "About", "customize": "Customize", "theme_saved": "Theme applied", "col_name": "Name", "col_from": "From folder",
    }
}

current_lang = "ru"

def tr(key, *args):
    text = LANGUAGES[current_lang].get(key, LANGUAGES["ru"].get(key, key))
    return text.format(*args) if args else text

# ==============================
#  темки
# ==============================
THEME_PRESETS = {
    "dark": {"label": "Main theme", "bg": "#1e1e2e", "bg2": "#2a2a3d", "bg3": "#313145", "fg": "#cdd6f4", "fg2": "#a6adc8", "accent": "#89b4fa", "btn_bg": "#313145", "btn_hover": "#45475a", "danger": "#f38ba8", "success": "#a6e3a1", "warning": "#fab387", "separator": "#45475a", "entry_bg": "#181825", "event_only": False},
    "deeper": {"label": "🌑 Moonlit Night", "bg": "#0d0d17", "bg2": "#16162a", "bg3": "#1e1e35", "fg": "#e2e8f0", "fg2": "#94a3b8", "accent": "#60a5fa", "btn_bg": "#1e1e35", "btn_hover": "#2d2d4a", "danger": "#fb7185", "success": "#86efac", "warning": "#fdba74", "separator": "#2d2d4a", "entry_bg": "#080812", "event_only": False},
    "purple": {"label": "💜 Purple", "bg": "#1a1025", "bg2": "#241535", "bg3": "#2e1a45", "fg": "#e9d8fd", "fg2": "#b794f4", "accent": "#c084fc", "btn_bg": "#2e1a45", "btn_hover": "#3d2260", "danger": "#f87171", "success": "#86efac", "warning": "#fbbf24", "separator": "#3d2260", "entry_bg": "#110b1c", "event_only": False},
    "green": {"label": "🌿 Green", "bg": "#0f1f15", "bg2": "#162a1c", "bg3": "#1e3525", "fg": "#d1fae5", "fg2": "#6ee7b7", "accent": "#34d399", "btn_bg": "#1e3525", "btn_hover": "#274a32", "danger": "#f87171", "success": "#6ee7b7", "warning": "#fcd34d", "separator": "#274a32", "entry_bg": "#091410", "event_only": False},
    "pink": {"label": "🌸 Pink", "bg": "#1f1020", "bg2": "#2b1530", "bg3": "#381a40", "fg": "#fce7f3", "fg2": "#f9a8d4", "accent": "#f472b6", "btn_bg": "#381a40", "btn_hover": "#4d2257", "danger": "#fb7185", "success": "#86efac", "warning": "#fbbf24", "separator": "#4d2257", "entry_bg": "#140b16", "event_only": False},
    "newyear": {"label": "🎄 New Year", "bg": "#0f172a", "bg2": "#0a1628", "bg3": "#1d3557", "fg": "#e0f2fe", "fg2": "#93c5fd", "accent": "#22c55e", "btn_bg": "#1d3557", "btn_hover": "#2a4b75", "danger": "#ef4444", "success": "#22c55e", "warning": "#facc15", "separator": "#2a4b75", "entry_bg": "#0b1220", "event_only": True, "event_name": "newyear"},
    "halloween": {"label": "🎃 Halloween", "bg": "#140d0a", "bg2": "#22140f", "bg3": "#2f1c14", "fg": "#ffedd5", "fg2": "#fdba74", "accent": "#f97316", "btn_bg": "#2f1c14", "btn_hover": "#47281d", "danger": "#ef4444", "success": "#84cc16", "warning": "#f59e0b", "separator": "#47281d", "entry_bg": "#0f0907", "event_only": True, "event_name": "halloween"},
}

def get_active_event_theme():
    active_event = get_active_event()
    if active_event in ["halloween", "newyear"]:
        return active_event
    return None

def should_show_theme(theme_name, theme_data):
    if theme_data.get("event_only", False):
        expected_event = theme_data.get("event_name")
        return expected_event == get_active_event()
    return True

# Определяем тему при запуске
active_event_theme = get_active_event_theme()
current_theme_name = active_event_theme if active_event_theme else "dark"

THEME = {
    "bg": "#1e1e2e", "bg2": "#2a2a3d", "bg3": "#313145", "fg": "#cdd6f4", "fg2": "#a6adc8",
    "accent": "#89b4fa", "btn_bg": "#313145", "btn_hover": "#45475a", "danger": "#f38ba8",
    "success": "#a6e3a1", "warning": "#fab387", "separator": "#45475a", "entry_bg": "#181825",
}

def T():
    return THEME

# ==============================
#  Эффект снегопада для окна настроек
# ==============================

class SettingsSnowEffect:
    def __init__(self, parent):
        self.parent = parent
        self.snowflakes = []
        self.running = True
        self.width = parent.winfo_width()
        self.height = parent.winfo_height()
        
        self.canvas = tk.Canvas(parent, bg='', highlightthickness=0, bd=0, takefocus=0)
        self.canvas.place(x=0, y=0, relwidth=1, relheight=1)
        self.canvas.lower()
        
        self.create_snowflakes()
        self.animate()
        
        self.parent.bind("<Configure>", self.on_resize)
    
    def create_snowflakes(self):
        if not self.running:
            return
        for flake in self.snowflakes:
            self.canvas.delete(flake['id'])
        self.snowflakes = []
        
        snow_count = 120 if self.width > 500 else 80
        for _ in range(snow_count):
            x = random.randint(0, max(1, self.width))
            y = random.randint(0, max(1, self.height))
            size = random.randint(2, 5)
            speed = random.uniform(0.5, 1.8)
            opacity = random.randint(100, 220)
            color = f'#{opacity:02x}{opacity:02x}{opacity:02x}'
            
            flake = self.canvas.create_oval(x, y, x + size, y + size, fill=color, outline='', tags='snowflake')
            self.snowflakes.append({
                'id': flake, 'speed': speed, 'size': size, 'x': x,
                'drift': random.uniform(-0.5, 0.5), 'drift_pos': random.uniform(0, 6.28)
            })
    
    def animate(self):
        if not self.running or not self.canvas.winfo_exists():
            return
        
        for flake in self.snowflakes:
            flake['drift_pos'] += 0.03
            drift_x = flake['drift'] * 0.3 * flake['drift_pos']
            self.canvas.move(flake['id'], drift_x, flake['speed'])
            coords = self.canvas.coords(flake['id'])
            
            if coords and coords[1] > self.height + 20:
                new_x = random.randint(0, max(1, self.width))
                new_y = -20
                self.canvas.coords(flake['id'], new_x, new_y, new_x + flake['size'], new_y + flake['size'])
            elif coords and (coords[0] < -50 or coords[2] > self.width + 50):
                new_x = random.randint(0, max(1, self.width))
                self.canvas.coords(flake['id'], new_x, flake['y'], new_x + flake['size'], flake['y'] + flake['size'])
        
        self.parent.after(40, self.animate)
    
    def stop(self):
        self.running = False
        if self.canvas and self.canvas.winfo_exists():
            self.canvas.destroy()
    
    def on_resize(self, event):
        self.width = event.width
        self.height = event.height
        if self.running:
            self.create_snowflakes()

# ==============================
#  Снежинки (старый класс для совместимости)
# ==============================

class SnowEffect:
    def __init__(self, parent, width=1400, height=900):
        self.canvas = tk.Canvas(parent, bg="", highlightthickness=0, bd=0)
        self.canvas.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.width = width
        self.height = height
        self.snowflakes = []
        for _ in range(90):
            x = random.randint(0, width)
            y = random.randint(0, height)
            size = random.randint(2, 6)
            speed = random.uniform(1, 3)
            flake = self.canvas.create_oval(x, y, x + size, y + size, fill="white", outline="")
            self.snowflakes.append((flake, speed, size))
        self.animate()

    def animate(self):
        for flake, speed, size in self.snowflakes:
            self.canvas.move(flake, 0, speed)
            coords = self.canvas.coords(flake)
            if coords and coords[1] > self.height:
                new_x = random.randint(0, self.width)
                self.canvas.coords(flake, new_x, -10, new_x + size, -10 + size)
        self.canvas.after(33, self.animate)

# ==============================
#  Конфиг
# ==============================
CONFIG_FILE = get_config_path()

DEFAULT_CONFIG = {
    "auto_clear_enabled": False, "auto_clear_interval": 3600, "auto_clear_temp": True,
    "auto_clear_recycle": True, "auto_clear_ram": False, "last_clear_time": None,
    "last_ram_clear_time": None, "last_ram_freed": 0, "language": "ru", "startup_enabled": False, "theme": "dark",
}

config = DEFAULT_CONFIG.copy()

def load_config():
    global config, current_lang, current_theme_name, THEME
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
                config.update(loaded)
                if "language" in loaded:
                    current_lang = loaded["language"]
                if "startup_enabled" not in config:
                    config["startup_enabled"] = False
                if "last_ram_clear_time" not in config:
                    config["last_ram_clear_time"] = None
                if "last_ram_freed" not in config:
                    config["last_ram_freed"] = 0
                
                active_event_theme = get_active_event_theme()
                if active_event_theme:
                    current_theme_name = active_event_theme
                    preset = THEME_PRESETS[current_theme_name]
                    for k in THEME:
                        if k in preset and k not in ["event_only", "event_name"]:
                            THEME[k] = preset[k]
                elif "theme" in loaded:
                    theme_key = loaded["theme"]
                    if theme_key == "red":
                        theme_key = "pink"
                    if theme_key in THEME_PRESETS:
                        current_theme_name = theme_key
                        preset = THEME_PRESETS[current_theme_name]
                        for k in THEME:
                            if k in preset and k not in ["event_only", "event_name"]:
                                THEME[k] = preset[k]
    except Exception as e:
        print(f"Ошибка загрузки: {e}")

def save_config():
    try:
        config_dir = os.path.dirname(CONFIG_FILE)
        if config_dir and not os.path.exists(config_dir):
            os.makedirs(config_dir, exist_ok=True)
        theme_to_save = config.get("theme", "dark")
        if get_active_event_theme():
            theme_to_save = "dark"
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump({**config, "theme": theme_to_save}, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Ошибка сохранения: {e}")
        return False

# ==============================
#  Автозагрузка
# ==============================
def set_autostart(enabled):
    try:
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        app_name = "Cleaney"
        if getattr(sys, 'frozen', False):
            app_path = f'"{sys.executable}"'
        else:
            app_path = f'"{sys.executable}" "{os.path.abspath(__file__)}"'
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as key:
            if enabled:
                winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, app_path)
            else:
                try:
                    winreg.DeleteValue(key, app_name)
                except FileNotFoundError:
                    pass
        config["startup_enabled"] = enabled
        save_config()
        return True
    except:
        return False

def is_autostart_enabled():
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_READ) as key:
            winreg.QueryValueEx(key, "Cleaney")
            return True
    except:
        return False

def sync_autostart_from_registry():
    reg_state = is_autostart_enabled()
    if config.get("startup_enabled", False) != reg_state:
        config["startup_enabled"] = reg_state
        save_config()
    return reg_state

def apply_startup_settings():
    current_state = is_autostart_enabled()
    desired_state = config.get("startup_enabled", False)
    if current_state != desired_state:
        set_autostart(desired_state)
    return desired_state

# ==============================
#  Очистка RAM
# ==============================
def clear_ram_func(silent=False):
    try:
        import psutil
        before = psutil.virtual_memory().available // (1024 * 1024)
        process_count = 0
        for proc in psutil.process_iter(['pid']):
            try:
                PROCESS_SET_QUOTA = 0x0100
                PROCESS_QUERY_INFORMATION = 0x0400
                PROCESS_VM_OPERATION = 0x0008
                access = PROCESS_SET_QUOTA | PROCESS_QUERY_INFORMATION | PROCESS_VM_OPERATION
                handle = ctypes.windll.kernel32.OpenProcess(access, False, proc.info['pid'])
                if handle:
                    if ctypes.windll.psapi.EmptyWorkingSet(handle):
                        process_count += 1
                    ctypes.windll.kernel32.CloseHandle(handle)
            except:
                pass

        class SYSTEM_MEMORY_LIST_COMMAND(ctypes.Structure):
            _fields_ = [("Command", ctypes.c_ulong)]
        cmd = SYSTEM_MEMORY_LIST_COMMAND(4)
        try:
            ctypes.windll.ntdll.NtSetSystemInformation(80, ctypes.byref(cmd), ctypes.sizeof(cmd))
            standby_cleared = True
        except:
            standby_cleared = False

        after = psutil.virtual_memory().available // (1024 * 1024)
        freed = max(0, after - before)
        config["last_ram_clear_time"] = datetime.now().isoformat()
        config["last_ram_freed"] = freed
        save_config()

        if not silent:
            details = []
            if process_count > 0:
                details.append(f"процессов: {process_count}")
            if standby_cleared:
                details.append("кэш очищен")
            notify(tr("cleaned"), tr("ram_freed", freed) + (f" ({', '.join(details)})" if details else ""), "info")
        return True
    except Exception as e:
        if not silent:
            notify(tr("cleaned"), tr("error_ram", str(e)), "error")
        return False

# ==============================
#  Остальная очистка
# ==============================
def clear_recycle_bin_func(silent=False):
    try:
        ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, 0x07)
        if not silent:
            notify(tr("cleaned"), tr("recycle_cleaned"), "info")
        return True
    except Exception as e:
        if not silent:
            notify(tr("cleaned"), tr("error_recycle", str(e)), "error")
        return False

def is_file_locked(path):
    try:
        with open(path, 'r+b'):
            pass
        return False
    except:
        return True

def safe_delete_file(path):
    if is_file_locked(path):
        return False
    try:
        os.unlink(path)
        return True
    except:
        return False

def safe_delete_dir(path):
    try:
        for root, dirs, files in os.walk(path):
            for f in files:
                if is_file_locked(os.path.join(root, f)):
                    return False
        shutil.rmtree(path)
        return True
    except:
        return False

def clear_temp_func(silent=False):
    temp_dir = tempfile.gettempdir()
    deleted = errors = skipped = 0
    try:
        for name in os.listdir(temp_dir):
            path = os.path.join(temp_dir, name)
            try:
                if os.path.isfile(path) or os.path.islink(path):
                    if safe_delete_file(path):
                        deleted += 1
                    else:
                        skipped += 1
                elif os.path.isdir(path):
                    if safe_delete_dir(path):
                        deleted += 1
                    else:
                        skipped += 1
            except:
                errors += 1
        msg = tr("temp_cleaned_msg", deleted)
        if skipped:
            msg += f" ({tr('skipped')}: {skipped})"
        if errors:
            msg += f", errors: {errors}"
        if not silent:
            notify(tr("cleaned"), msg, "info")
        return True
    except Exception as e:
        if not silent:
            notify(tr("cleaned"), tr("error_temp", str(e)), "error")
        return False

def do_clear_all():
    def clear():
        clear_temp_func(silent=True)
        clear_recycle_bin_func(silent=True)
        if config.get("auto_clear_ram", False):
            clear_ram_func(silent=True)
        config["last_clear_time"] = datetime.now().isoformat()
        save_config()
        notify(tr("done"), tr("cleaned_all"), "info")
    threading.Thread(target=clear, daemon=True).start()

def do_clear_recycle():
    threading.Thread(target=clear_recycle_bin_func, daemon=True).start()

def do_clear_temp():
    threading.Thread(target=clear_temp_func, daemon=True).start()

def do_clear_ram():
    threading.Thread(target=clear_ram_func, daemon=True).start()

# ==============================
#  Авто-очистка
# ==============================
timer_running = False
timer_thread = None
timer_reset_event = threading.Event()

def auto_clear_worker():
    global timer_running
    while timer_running:
        interval = config['auto_clear_interval']
        timer_reset_event.clear()
        timer_reset_event.wait(timeout=interval)
        if not timer_running or timer_reset_event.is_set():
            continue
        if not config['auto_clear_enabled']:
            continue
        parts = []
        if config['auto_clear_temp']:
            clear_temp_func(silent=True)
            parts.append("TEMP")
        if config['auto_clear_recycle']:
            clear_recycle_bin_func(silent=True)
            parts.append(tr("menu_clear_recycle").lower())
        if config.get('auto_clear_ram', False):
            clear_ram_func(silent=True)
            parts.append("RAM")
        if parts:
            config['last_clear_time'] = datetime.now().isoformat()
            save_config()
            notify(tr("auto_clean"), tr("auto_cleaned", ', '.join(parts)), "info")

def start_auto_clear():
    global timer_thread, timer_running
    if not timer_running and config['auto_clear_enabled']:
        timer_running = True
        timer_reset_event.clear()
        timer_thread = threading.Thread(target=auto_clear_worker, daemon=True)
        timer_thread.start()

def stop_auto_clear():
    global timer_running
    timer_running = False
    timer_reset_event.set()

def reset_auto_clear_timer():
    timer_reset_event.set()

def fmt_interval(secs):
    if secs < 3600:
        return f"{secs // 60} {tr('minutes')}"
    elif secs < 86400:
        return f"{secs // 3600} {tr('hours')}"
    return f"{secs // 86400} {tr('days')}"

# ==============================
#  Иконка трея
# ==============================
def create_tray_image():
    active_event = get_active_event()
    if active_event == "halloween":
        return create_halloween_icon()
    if active_event == "newyear":
        return create_christmas_icon()
    
    img = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle((18, 20, 46, 54), radius=6, fill=(70, 70, 70))
    draw.rectangle((16, 14, 48, 22), fill=(120, 120, 120))
    draw.rectangle((28, 8, 36, 14), fill=(120, 120, 120))
    for x in range(24, 44, 6):
        draw.line((x, 26, x, 50), fill=(200, 200, 200), width=2)
    if config['auto_clear_enabled']:
        draw.ellipse((50, 50, 60, 60), fill=(0, 220, 100, 200))
    return img

# ==============================
#  Луна (сокращённая версия)
# ==============================
def _render_moon_pil(w, h):
    from PIL import Image as PilImage, ImageDraw as PilDraw
    img = PilImage.new("RGB", (w, h), (8, 8, 20))
    draw = PilDraw.Draw(img)
    for i in range(h):
        r = int(8 + 7 * i / h)
        g = int(8 + 12 * i / h)
        b = int(20 + 30 * i / h)
        draw.line([(0, i), (w, i)], fill=(r, g, b))
    moon_r = int(min(w, h) * 0.20)
    moon_cx, moon_cy = int(w * 0.65), int(h * 0.28)
    draw.ellipse([moon_cx - moon_r, moon_cy - moon_r, moon_cx + moon_r, moon_cy + moon_r], fill=(195, 215, 240))
    return img

def draw_moon_on_canvas(canvas, w, h, bg_color):
    import math
    canvas.configure(bg=bg_color)
    canvas.delete("all")
    for i in range(h):
        r = int(8 + 7 * i / h)
        g = int(8 + 12 * i / h)
        b = int(20 + 30 * i / h)
        canvas.create_line(0, i, w, i, fill=f"#{r:02x}{g:02x}{b:02x}")
    moon_r = min(w, h) * 0.22
    moon_cx, moon_cy = w * 0.65, h * 0.30
    canvas.create_oval(moon_cx - moon_r, moon_cy - moon_r, moon_cx + moon_r, moon_cy + moon_r, fill="#c3d7f0", outline="#ddeeff", width=1)
    for cx_off, cy_off, cr in [(0.28, -0.18, 0.10), (-0.22, 0.22, 0.07), (0.08, 0.28, 0.055)]:
        ccx = moon_cx + cx_off * moon_r * 2
        ccy = moon_cy + cy_off * moon_r * 2
        cr_r = cr * moon_r * 2
        canvas.create_oval(ccx - cr_r, ccy - cr_r, ccx + cr_r, ccy + cr_r, fill="#9ab5cc", outline="")
    water_y = h * 0.70
    canvas.create_rectangle(0, water_y, w, h, fill="#06090f", outline="")
    tx, ty_base = w * 0.27, water_y
    trunk_h = h * 0.09
    canvas.create_rectangle(tx - 2, ty_base - trunk_h, tx + 2, ty_base, fill="#040810", outline="")

# ==============================
#  Theme
# ==============================
_overlay_open = False

def open_customize_overlay(parent_window):
    global THEME, current_theme_name, _overlay_open
    if _overlay_open:
        return
    _overlay_open = True

    t = T()
    overlay_active = [True]

    parent_window.update_idletasks()
    px, py = parent_window.winfo_x(), parent_window.winfo_y()
    pw, ph = parent_window.winfo_width(), parent_window.winfo_height()

    backdrop = tk.Toplevel(parent_window)
    backdrop.overrideredirect(True)
    backdrop.attributes("-alpha", 0.0)
    backdrop.configure(bg="#000000")
    backdrop.geometry(f"{pw}x{ph}+{px}+{py}")
    backdrop.transient(parent_window)

    panel = tk.Toplevel(parent_window)
    panel.overrideredirect(True)
    panel.configure(bg=t["bg2"])
    panel.config(highlightbackground=t["separator"], highlightthickness=1)
    panel.transient(parent_window)

    PANEL_W, PANEL_H = 420, 510

    def close_overlay(skip_animation=False):
        global _overlay_open
        _overlay_open = False
        if not overlay_active[0]:
            return
        overlay_active[0] = False
        for w in (panel, backdrop):
            try:
                w.destroy()
            except:
                pass

    def on_panel_destroy(e=None):
        global _overlay_open
        _overlay_open = False
        overlay_active[0] = False

    panel.bind("<Destroy>", on_panel_destroy)
    backdrop.bind("<Destroy>", on_panel_destroy)
    backdrop.bind("<Button-1>", lambda e: close_overlay())

    cx, cy = px + pw // 2 - PANEL_W // 2, py + ph // 2 - PANEL_H // 2
    panel.geometry(f"{PANEL_W}x{PANEL_H}+{cx}+{cy+30}")

    hdr = tk.Frame(panel, bg=t["bg3"], pady=12)
    hdr.pack(fill="x")
    tk.Label(hdr, text="🎨  Theme", font=("Segoe UI", 12, "bold"), bg=t["bg3"], fg=t["accent"]).pack(side="left", padx=16)
    tk.Button(hdr, text="✕", font=("Segoe UI", 10), bg=t["bg3"], fg=t["fg2"], relief="flat", cursor="hand2", padx=8, bd=0, command=close_overlay, activebackground=t["btn_hover"], activeforeground=t["fg"]).pack(side="right", padx=10)
    tk.Frame(panel, bg=t["separator"], height=1).pack(fill="x")

    body = tk.Frame(panel, bg=t["bg2"], padx=20, pady=16)
    body.pack(fill="both", expand=True)
    tk.Label(body, text="Select a theme.", font=("Segoe UI", 8, "bold"), bg=t["bg2"], fg=t["fg2"]).pack(anchor="w", pady=(0, 12))

    grid = tk.Frame(body, bg=t["bg2"])
    grid.pack(fill="x")

    selected_var = [current_theme_name]
    card_refs = {}

    def apply_preset(name):
        global THEME, current_theme_name, settings_window
        selected_var[0] = name
        current_theme_name = name
        preset = THEME_PRESETS[name]
        for k in THEME:
            if k in preset and k not in ["event_only", "event_name"]:
                THEME[k] = preset[k]
        for n, card in card_refs.items():
            try:
                pd = THEME_PRESETS[n]
                card.config(highlightbackground=pd["accent"] if n == name else pd["separator"])
            except:
                pass
        theme_to_save = "dark" if get_active_event_theme() else name
        config["theme"] = theme_to_save
        save_config()
        close_overlay(skip_animation=True)
        if settings_window:
            try:
                settings_window.destroy()
            except:
                pass
            settings_window = None
        root_tk.after(150, open_settings)

    col_count, row_frame = 0, None
    for theme_name, theme_data in THEME_PRESETS.items():
        if not should_show_theme(theme_name, theme_data):
            continue
        if col_count % 2 == 0:
            row_frame = tk.Frame(grid, bg=t["bg2"])
            row_frame.pack(fill="x", pady=5)

        CARD_W, CARD_H = 178, 72
        card = tk.Frame(row_frame, bg=theme_data["bg2"], highlightthickness=2, highlightbackground=theme_data["accent"] if theme_name == current_theme_name else theme_data["separator"], cursor="hand2", width=CARD_W, height=CARD_H)
        card.pack(side="left", padx=(0, 10) if col_count % 2 == 0 else 0)
        card.pack_propagate(False)
        card_refs[theme_name] = card

        inner = tk.Frame(card, bg=theme_data["bg2"], padx=10, pady=8)
        inner.pack(fill="both", expand=True)
        lbl = tk.Label(inner, text=theme_data["label"], font=("Segoe UI", 10, "bold"), bg=theme_data["bg2"], fg=theme_data["fg"])
        lbl.pack(anchor="w")
        dots_frame = tk.Frame(inner, bg=theme_data["bg2"])
        dots_frame.pack(anchor="w", pady=(5, 0))
        for color_key in ["accent", "success", "danger", "warning"]:
            dot = tk.Canvas(dots_frame, width=14, height=14, bg=theme_data["bg2"], highlightthickness=0)
            dot.pack(side="left", padx=2)
            dot.create_oval(1, 1, 13, 13, fill=theme_data[color_key], outline="")

        def bind_card(c, inner_f, lbl_w, dots_f, n):
            td = THEME_PRESETS[n]
            def on_enter(e): c.config(highlightbackground=td["accent"])
            def on_leave(e): c.config(highlightbackground=td["accent"] if selected_var[0] == n else td["separator"])
            def on_click(e): apply_preset(n)
            for w in [c, inner_f, lbl_w, dots_f]:
                w.bind("<Enter>", on_enter)
                w.bind("<Leave>", on_leave)
                w.bind("<Button-1>", on_click)
        bind_card(card, inner, lbl, dots_frame, theme_name)
        col_count += 1

    tk.Frame(body, bg=t["separator"], height=1).pack(fill="x", pady=12)
    
    active_event = get_active_event()
    if active_event:
        event_messages = {"halloween": "🎃 Boo! Happy Halloween!/Бу!с Хэллуином! 🎃", "newyear": "🎄 Happy New Year!/С новым годом! 🎄"}
        tk.Label(body, text=event_messages.get(active_event, ""), font=("Segoe UI", 9, "bold"), bg=t["bg2"], fg=t["warning"]).pack(anchor="w", pady=(0, 8))

    tk.Label(body, text=" Added threads, fixed minor bugs, kept RAM clearing(useless). ", font=("Segoe UI", 8), bg=t["bg2"], fg=t["fg2"]).pack(anchor="w")
    tk.Frame(panel, bg=t["separator"], height=1).pack(fill="x")
    footer = tk.Frame(panel, bg=t["bg3"], pady=10)
    footer.pack(fill="x")
    tk.Button(footer, text=tr("close"), font=("Segoe UI", 9), bg=t["btn_bg"], fg=t["fg"], relief="flat", cursor="hand2", padx=24, pady=6, command=close_overlay, activebackground=t["btn_hover"], activeforeground=t["fg"]).pack()

    backdrop.attributes("-alpha", 0.5)
    panel.lift()

# ==============================
#  Трей
# ==============================
popup_window = None
popup_lock = threading.Lock()
popup_creating = False
last_click_time = 0

def close_popup():
    global popup_window, popup_creating
    with popup_lock:
        if popup_window:
            try:
                popup_window.destroy()
            except:
                pass
            popup_window = None
        popup_creating = False

def safe_quit(icon=None, item=None):
    global timer_running, settings_window, popup_window, tray_icon, root_tk, mutex_handle
    timer_running = False
    if settings_window:
        try:
            settings_window.destroy()
        except:
            pass
        settings_window = None
    if popup_window:
        try:
            popup_window.destroy()
        except:
            pass
        popup_window = None
    if tray_icon:
        try:
            tray_icon.stop()
        except:
            pass
    if root_tk:
        try:
            root_tk.destroy()
        except:
            pass
    if mutex_handle:
        try:
            ctypes.windll.kernel32.ReleaseMutex(mutex_handle)
            ctypes.windll.kernel32.CloseHandle(mutex_handle)
        except:
            pass
    sys.exit(0)

def show_tray_popup(icon=None, item=None):
    global popup_window, last_click_time, popup_creating
    now = time.time()
    if now - last_click_time < 0.5:
        return
    last_click_time = now
    with popup_lock:
        if popup_creating or popup_window is not None:
            close_popup()
            return
        popup_creating = True

    def build():
        global popup_window, popup_creating, root_tk
        try:
            t = T()
            class POINT(ctypes.Structure):
                _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]
            pt = POINT()
            ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
            cx, cy = pt.x, pt.y

            win = tk.Toplevel(root_tk)
            with popup_lock:
                if not popup_creating:
                    win.destroy()
                    return
                popup_window = win

            win.overrideredirect(True)
            win.attributes("-topmost", True)
            win.attributes("-alpha", 0.97)
            win.configure(bg=t["bg2"])
            win.config(highlightbackground=t["separator"], highlightthickness=1)

            def add_item(icon_text, label, command, color=None):
                fg = color or t["fg"]
                row = tk.Frame(win, bg=t["bg2"], cursor="hand2")
                row.pack(fill="x")
                inner = tk.Frame(row, bg=t["bg2"], padx=14, pady=7)
                inner.pack(fill="x")
                ico_lbl = tk.Label(inner, text=icon_text, font=("Segoe UI", 10), bg=t["bg2"], fg=fg, width=2, anchor="w")
                ico_lbl.pack(side="left")
                txt_lbl = tk.Label(inner, text=label, font=("Segoe UI", 10), bg=t["bg2"], fg=fg, anchor="w")
                txt_lbl.pack(side="left", padx=(4, 0))

                def on_enter(e):
                    row.configure(bg=t["btn_hover"])
                    inner.configure(bg=t["btn_hover"])
                    ico_lbl.configure(bg=t["btn_hover"])
                    txt_lbl.configure(bg=t["btn_hover"])

                def on_leave(e):
                    row.configure(bg=t["bg2"])
                    inner.configure(bg=t["bg2"])
                    ico_lbl.configure(bg=t["bg2"])
                    txt_lbl.configure(bg=t["bg2"])

                def on_click(e):
                    close_popup()
                    if command:
                        threading.Thread(target=lambda: (time.sleep(0.05), command()), daemon=True).start()

                for w in (row, inner, ico_lbl, txt_lbl):
                    w.bind("<Enter>", on_enter)
                    w.bind("<Leave>", on_leave)
                    w.bind("<Button-1>", on_click)

            add_item("🧹", tr("menu_clear_all"), do_clear_all)
            add_item("🗑", tr("menu_clear_recycle"), do_clear_recycle)
            add_item("📁", tr("menu_clear_temp"), do_clear_temp)
            tk.Frame(win, bg=t["separator"], height=1).pack(fill="x", padx=8, pady=2)
            add_item("⚙️", tr("menu_settings"), lambda: open_settings())
            tk.Frame(win, bg=t["separator"], height=1).pack(fill="x", padx=8, pady=2)
            add_item("🚪", tr("menu_exit"), lambda: safe_quit(), color=t["danger"])

            win.update_idletasks()
            w, h = win.winfo_reqwidth(), win.winfo_reqheight()
            sw, sh = win.winfo_screenwidth(), win.winfo_screenheight()
            x, y = min(cx, sw - w - 4), max(cy - h - 4, 4)
            win.geometry(f"{w}x{h}+{x}+{y}")
            win.bind("<FocusOut>", lambda e: win.after(100, close_popup))
            win.after(100, lambda: win.focus_force())

            def on_closing():
                with popup_lock:
                    global popup_window
                    popup_window = None
                    popup_creating = False
                win.destroy()
            win.protocol("WM_DELETE_WINDOW", on_closing)
        except Exception as e:
            print(f"Popup error: {e}")
            with popup_lock:
                popup_window = None
                popup_creating = False

    root_tk.after(0, build)

# ==============================
#  Смена языка
# ==============================
def change_language(lang_code):
    global current_lang
    current_lang = lang_code
    config["language"] = lang_code
    save_config()
    if settings_window is not None:
        try:
            if settings_window.winfo_exists():
                update_ui_language()
        except:
            pass

# ==============================
#  Switch-виджет
# ==============================
class Switch(tk.Canvas):
    def __init__(self, parent, initial_state=False, command=None, theme_colors=None):
        self.width, self.height = 50, 26
        self.radius = self.height // 2
        self.state = initial_state
        self.command = command
        self.colors = theme_colors or T()
        super().__init__(parent, width=self.width, height=self.height, bg=self.colors["bg2"], highlightthickness=0, cursor="hand2")
        self.bind("<Button-1>", self.toggle)
        self.draw()

    def draw(self):
        self.delete("all")
        if self.state:
            bg_color, knob_color = self.colors["accent"], "#ffffff"
        else:
            bg_color, knob_color = self.colors["btn_bg"], self.colors["fg2"]
        self.create_oval(0, 0, self.height, self.height, fill=bg_color, outline="")
        self.create_oval(self.width - self.height, 0, self.width, self.height, fill=bg_color, outline="")
        self.create_rectangle(self.height // 2, 0, self.width - self.height // 2, self.height, fill=bg_color, outline="")
        knob_x = self.width - self.height + 2 if self.state else 2
        self.create_oval(knob_x, 2, knob_x + self.height - 4, self.height - 2, fill=knob_color, outline="", width=0)

    def toggle(self, event=None):
        self.state = not self.state
        self.draw()
        if self.command:
            self.command(self.state)

    def set_state(self, state):
        self.state = state
        self.draw()

# ==============================
#  Окно настроек
# ==============================
settings_window = None
settings_widgets = []
settings_widgets_button = []
settings_dynamic_widgets = []
unit_btns = []
preset_btns = []
cur_unit = 0
snow_effect = None

def update_ui_language():
    global settings_window
    if not settings_window or not settings_window.winfo_exists():
        return
    settings_window.title(tr("settings_title"))
    for widget, text_key in settings_widgets:
        try:
            if widget and widget.winfo_exists():
                widget.config(text=tr(text_key))
        except:
            pass
    for widget, text_key, _ in settings_widgets_button:
        try:
            if widget and widget.winfo_exists():
                widget.config(text=tr(text_key))
        except:
            pass
    for widget, text_fn in settings_dynamic_widgets:
        try:
            if widget and widget.winfo_exists():
                widget.config(text=text_fn())
        except:
            pass

# ==============================
#  Уведомления
# ==============================
try:
    from winotify import Notification, audio
    def notify(title, message, icon_type="info"):
        def show():
            toast = Notification(app_id=tr("app_name"), title=title, msg=message, duration="short")
            toast.set_audio(audio.Default, loop=False)
            toast.show()
        threading.Thread(target=show, daemon=True).start()
except ImportError:
    def notify(title, message, icon_type="info"):
        def show():
            st = title.replace('"', "'").replace('<', '').replace('>', '')
            sm = message.replace('"', "'").replace('<', '').replace('>', '')
            ps = f'''
[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType=WindowsRuntime]|Out-Null
[Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType=WindowsRuntime]|Out-Null
$x=New-Object Windows.Data.Xml.Dom.XmlDocument
$x.LoadXml('<toast><visual><binding template="ToastGeneric"><text>{st}</text><text>{sm}</text></binding></visual></toast>')
[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("{tr('app_name')}").Show([Windows.UI.Notifications.ToastNotification]::new($x))
'''
            subprocess.Popen(["powershell", "-WindowStyle", "Hidden", "-Command", ps], creationflags=subprocess.CREATE_NO_WINDOW)
        threading.Thread(target=show, daemon=True).start()

def open_settings(icon=None, item=None):
    global settings_window, settings_widgets, settings_widgets_button, unit_btns, preset_btns, cur_unit, snow_effect

    if settings_window is not None:
        try:
            if settings_window.winfo_exists():
                settings_window.lift()
                settings_window.focus_force()
                return
        except:
            settings_window = None

    def build():
        global settings_window, settings_widgets, settings_widgets_button, settings_dynamic_widgets, unit_btns, preset_btns, cur_unit, snow_effect
        t = T()

        settings_widgets = []
        settings_widgets_button = []
        settings_dynamic_widgets = []
        unit_btns = []
        preset_btns = []

        root = tk.Toplevel(root_tk)
        settings_window = root
        root.title(tr("settings_title"))
        root.geometry("460x750")
        root.resizable(False, False)
        root.configure(bg=t["bg"])

        root.update_idletasks()
        width, height = root.winfo_width(), root.winfo_height()
        x = (root.winfo_screenwidth() // 2) - (width // 2)
        y = (root.winfo_screenheight() // 2) - (height // 2)
        root.geometry(f'{width}x{height}+{x}+{y}')

        # Header
        header = tk.Frame(root, bg=t["bg2"], pady=14)
        header.pack(fill="x")
        title_label = tk.Label(header, text=f"🧹  {tr('app_name')}", font=("Segoe UI", 15, "bold"), bg=t["bg2"], fg=t["accent"])
        title_label.pack(side="left", padx=20)
        settings_widgets.append((title_label, "app_name"))

        langs = list(LANGUAGES.keys())
        lang_btn = tk.Button(header, text=LANGUAGES[current_lang]["name"], font=("Segoe UI", 9), bg=t["btn_bg"], fg=t["fg"], activebackground=t["btn_hover"], activeforeground=t["fg"], relief="flat", cursor="hand2", padx=10, pady=5, bd=0)
        lang_btn.pack(side="right", padx=4)

        def toggle_language():
            next_lang = langs[(langs.index(current_lang) + 1) % len(langs)]
            change_language(next_lang)
            lang_btn.config(text=LANGUAGES[next_lang]["name"])
        lang_btn.config(command=toggle_language)
        settings_dynamic_widgets.append((lang_btn, lambda: LANGUAGES[current_lang]["name"]))

        customize_btn = tk.Button(header, text="🎨", font=("Segoe UI", 11), bg=t["btn_bg"], fg=t["accent"], activebackground=t["btn_hover"], activeforeground=t["accent"], relief="flat", cursor="hand2", padx=8, pady=5, bd=0, command=lambda: open_customize_overlay(root))
        customize_btn.pack(side="right", padx=4)

        tk.Frame(root, bg=t["separator"], height=1).pack(fill="x")

        # Снегопад для новогоднего периода
        if get_active_event() == "newyear":
            def add_snow():
                global snow_effect
                if snow_effect:
                    snow_effect.stop()
                snow_effect = SettingsSnowEffect(root)
            root.after(200, add_snow)

        # Луна для темы deeper
        _moon_photo_ref = []
        if current_theme_name == "deeper":
            def _place_moon(event=None):
                if _moon_photo_ref:
                    return
                try:
                    cw, ch = root.winfo_width(), root.winfo_height()
                    if cw < 10 or ch < 10:
                        return
                    moon_img = _render_moon_pil(cw, ch)
                    from PIL import ImageTk
                    photo = ImageTk.PhotoImage(moon_img)
                    _moon_photo_ref.append(photo)
                    lbl = tk.Label(root, image=photo, bd=0, highlightthickness=0)
                    lbl.place(x=0, y=0, relwidth=1, relheight=1)
                    lbl.lower()
                except Exception as e:
                    print(f"Moon render error: {e}")
            root.after(50, _place_moon)

        content = tk.Frame(root, bg=t["bg"], padx=20, pady=10)
        content.pack(fill="both", expand=True)

        # Быстрые действия
        label_quick = tk.Label(content, text=tr("quick_actions"), font=("Segoe UI", 9, "bold"), bg=t["bg"], fg=t["fg2"])
        label_quick.pack(anchor="w", pady=(0, 8))
        settings_widgets.append((label_quick, "quick_actions"))

        btn_frame = tk.Frame(content, bg=t["bg"])
        btn_frame.pack(fill="x", pady=(0, 15))

        def make_button(parent, text, color, cmd):
            btn = tk.Button(parent, text=text, font=("Segoe UI", 9, "bold"), bg=color, fg="white", relief="flat", cursor="hand2", padx=18, pady=7, bd=0, command=cmd)
            btn.pack(side="left", padx=(0, 10))
            return btn

        btn_all = make_button(btn_frame, tr("btn_all"), t["accent"], do_clear_all)
        btn_recycle = make_button(btn_frame, tr("btn_recycle"), t["warning"], do_clear_recycle)
        btn_temp = make_button(btn_frame, tr("btn_temp"), t["fg2"], do_clear_temp)
        btn_ram = make_button(btn_frame, tr("btn_ram"), "#7c6f9f", do_clear_ram)

        settings_widgets_button.append((btn_all, "btn_all", True))
        settings_widgets_button.append((btn_recycle, "btn_recycle", True))
        settings_widgets_button.append((btn_temp, "btn_temp", True))
        settings_widgets_button.append((btn_ram, "btn_ram", True))

        tk.Frame(content, bg=t["separator"], height=1).pack(fill="x", pady=5)

        # Автозагрузка
        label_startup = tk.Label(content, text=tr("startup"), font=("Segoe UI", 9, "bold"), bg=t["bg"], fg=t["fg2"])
        label_startup.pack(anchor="w", pady=(10, 8))
        settings_widgets.append((label_startup, "startup"))

        startup_frame = tk.Frame(content, bg=t["bg2"], pady=10)
        startup_frame.pack(fill="x", pady=2)
        startup_state = sync_autostart_from_registry()

        def on_startup_changed(state):
            set_autostart(state)
            notify(tr("auto_clean"), tr("startup_enabled") if state else tr("startup_disabled"), "info")

        startup_switch = Switch(startup_frame, initial_state=startup_state, command=on_startup_changed, theme_colors=t)
        startup_switch.pack(side="right", padx=12)
        startup_label = tk.Label(startup_frame, text=tr("enable_startup"), font=("Segoe UI", 10), bg=t["bg2"], fg=t["fg"])
        startup_label.pack(side="left", padx=12)
        settings_widgets.append((startup_label, "enable_startup"))

        tk.Frame(content, bg=t["separator"], height=1).pack(fill="x", pady=5)

        # Автоочистка
        label_auto = tk.Label(content, text=tr("auto_cleanup"), font=("Segoe UI", 9, "bold"), bg=t["bg"], fg=t["fg2"])
        label_auto.pack(anchor="w", pady=(10, 8))
        settings_widgets.append((label_auto, "auto_cleanup"))

        auto_state = config["auto_clear_enabled"]
        temp_state = config["auto_clear_temp"]
        recycle_state = config["auto_clear_recycle"]
        ram_state = config.get("auto_clear_ram", False)
        status_text_ref = None

        def on_auto_changed(state):
            nonlocal auto_state, status_text_ref
            auto_state = state
            config["auto_clear_enabled"] = state
            save_config()
            if state:
                start_auto_clear()
                notify(tr("auto_clean"), tr("auto_enabled", fmt_interval(config['auto_clear_interval'])), "info")
            else:
                stop_auto_clear()
                notify(tr("auto_clean"), tr("auto_disabled"), "warning")
            if status_text_ref and status_text_ref.winfo_exists():
                status_text_ref.config(text=tr("on") if state else tr("off"), fg=t["success"] if state else t["danger"])
            if tray_icon:
                tray_icon.icon = create_tray_image()

        def on_temp_changed(state):
            nonlocal temp_state
            temp_state = state
            config["auto_clear_temp"] = state
            save_config()

        def on_recycle_changed(state):
            nonlocal recycle_state
            recycle_state = state
            config["auto_clear_recycle"] = state
            save_config()

        def on_ram_changed(state):
            nonlocal ram_state
            ram_state = state
            config["auto_clear_ram"] = state
            save_config()

        def create_switch_row(parent, label_text, initial_state, callback):
            row = tk.Frame(parent, bg=t["bg2"])
            row.pack(fill="x", pady=4)
            lbl = tk.Label(row, text=tr(label_text), font=("Segoe UI", 10), bg=t["bg2"], fg=t["fg"])
            lbl.pack(side="left", padx=12)
            settings_widgets.append((lbl, label_text))
            sw = Switch(row, initial_state=initial_state, command=callback, theme_colors=t)
            sw.pack(side="right", padx=12)
            return sw

        switches_frame = tk.Frame(content, bg=t["bg"])
        switches_frame.pack(fill="x")
        create_switch_row(switches_frame, "enable_auto", auto_state, on_auto_changed)
        create_switch_row(switches_frame, "clean_temp", temp_state, on_temp_changed)
        create_switch_row(switches_frame, "clean_recycle", recycle_state, on_recycle_changed)
        create_switch_row(switches_frame, "enable_ram", ram_state, on_ram_changed)

        tk.Frame(content, bg=t["separator"], height=1).pack(fill="x", pady=10)

        # Интервал
        label_interval = tk.Label(content, text=tr("interval"), font=("Segoe UI", 9, "bold"), bg=t["bg"], fg=t["fg2"])
        label_interval.pack(anchor="w", pady=(0, 8))
        settings_widgets.append((label_interval, "interval"))

        interval_frame = tk.Frame(content, bg=t["bg2"], pady=10)
        interval_frame.pack(fill="x", pady=2)
        label_every = tk.Label(interval_frame, text=tr("every"), font=("Segoe UI", 10), bg=t["bg2"], fg=t["fg"])
        label_every.pack(side="left", padx=12)
        settings_widgets.append((label_every, "every"))

        interval_val = tk.StringVar()
        cur_secs = config["auto_clear_interval"]
        if cur_secs % 86400 == 0:
            cur_unit, cur_val = 2, cur_secs // 86400
        elif cur_secs % 3600 == 0:
            cur_unit, cur_val = 1, cur_secs // 3600
        else:
            cur_unit, cur_val = 0, max(1, cur_secs // 60)
        interval_val.set(str(cur_val))

        entry = tk.Entry(interval_frame, textvariable=interval_val, width=6, font=("Segoe UI", 10), bg=t["entry_bg"], fg=t["fg"], insertbackground=t["fg"], relief="flat", bd=3)
        entry.pack(side="left", padx=5)

        units, multipliers = ["min", "hour", "day"], [60, 3600, 86400]

        def set_unit(idx):
            global cur_unit
            cur_unit = idx
            for i, btn in enumerate(unit_btns):
                try:
                    if btn and btn.winfo_exists():
                        btn.config(bg=t["accent"] if i == idx else t["btn_bg"], fg="white" if i == idx else t["fg"])
                except:
                    pass

        for idx, unit_key in enumerate(units):
            btn = tk.Button(interval_frame, text=tr(unit_key), font=("Segoe UI", 9), bg=t["accent"] if idx == cur_unit else t["btn_bg"], fg="white" if idx == cur_unit else t["fg"], relief="flat", cursor="hand2", padx=10, pady=3, command=lambda i=idx: set_unit(i))
            btn.pack(side="left", padx=2)
            unit_btns.append(btn)
            settings_widgets_button.append((btn, unit_key, True))

        def apply_interval():
            try:
                val = float(interval_val.get())
                if val <= 0:
                    raise ValueError
                secs = int(val * multipliers[cur_unit])
                config["auto_clear_interval"] = secs
                save_config()
                if config["auto_clear_enabled"]:
                    reset_auto_clear_timer()
                notify(tr("interval_changed"), fmt_interval(secs), "info")
            except:
                notify(tr("auto_clean"), tr("error_input"), "error")

        apply_btn = tk.Button(interval_frame, text="✓", font=("Segoe UI", 12, "bold"), bg=t["success"], fg="white", relief="flat", cursor="hand2", padx=12, pady=3, command=apply_interval)
        apply_btn.pack(side="left", padx=8)

        presets_frame = tk.Frame(content, bg=t["bg"])
        presets_frame.pack(fill="x", pady=(8, 0))
        presets = [(30, 60, "preset_30min"), (1, 3600, "preset_1h"), (6, 3600, "preset_6h"), (12, 3600, "preset_12h"), (1, 86400, "preset_1d")]

        for val, mult, text_key in presets:
            def set_preset(v=val, m=mult, tk_key=text_key):
                secs = v * m
                config["auto_clear_interval"] = secs
                save_config()
                if config["auto_clear_enabled"]:
                    reset_auto_clear_timer()
                if m == 60:
                    set_unit(0)
                elif m == 3600:
                    set_unit(1)
                else:
                    set_unit(2)
                interval_val.set(str(v))
                notify(tr("interval_changed"), fmt_interval(secs), "info")

            btn = tk.Button(presets_frame, text=tr(text_key), font=("Segoe UI", 9), bg=t["btn_bg"], fg=t["fg"], relief="flat", cursor="hand2", padx=10, pady=4, command=set_preset)
            btn.pack(side="left", padx=(0, 6))
            preset_btns.append(btn)
            settings_widgets_button.append((btn, text_key, True))

        tk.Frame(content, bg=t["separator"], height=1).pack(fill="x", pady=10)

        # Статус
        status_frame = tk.Frame(content, bg=t["bg2"], pady=10, padx=15)
        status_frame.pack(fill="x", pady=5)
        status_title = tk.Label(status_frame, text=tr("status"), font=("Segoe UI", 9, "bold"), bg=t["bg2"], fg=t["accent"])
        status_title.pack(anchor="w", pady=(0, 8))
        settings_widgets.append((status_title, "status"))

        auto_row = tk.Frame(status_frame, bg=t["bg2"])
        auto_row.pack(fill="x", pady=3)
        auto_label = tk.Label(auto_row, text=tr("auto_status"), font=("Segoe UI", 10), bg=t["bg2"], fg=t["fg"])
        auto_label.pack(side="left")
        settings_widgets.append((auto_label, "auto_status"))

        status_text = tk.Label(auto_row, text=tr("on") if config["auto_clear_enabled"] else tr("off"), font=("Segoe UI", 10, "bold"), bg=t["bg2"], fg=t["success"] if config["auto_clear_enabled"] else t["danger"])
        status_text.pack(side="left", padx=(10, 0))
        status_text_ref = status_text
        settings_dynamic_widgets.append((status_text, lambda: tr("on") if config["auto_clear_enabled"] else tr("off")))

        last_row = tk.Frame(status_frame, bg=t["bg2"])
        last_row.pack(fill="x", pady=3)
        last_label = tk.Label(last_row, text=tr("last"), font=("Segoe UI", 10), bg=t["bg2"], fg=t["fg"])
        last_label.pack(side="left")
        settings_widgets.append((last_label, "last"))

        last_time_raw = config["last_clear_time"]
        last_time = tr("never")
        if last_time_raw:
            try:
                last_time = datetime.fromisoformat(last_time_raw).strftime("%d.%m.%Y %H:%M:%S")
            except:
                last_time = last_time_raw
        last_value = tk.Label(last_row, text=last_time, font=("Segoe UI", 10), bg=t["bg2"], fg=t["fg2"])
        last_value.pack(side="left", padx=(10, 0))

        # Footer
        footer = tk.Frame(root, bg=t["bg2"], pady=10)
        footer.pack(fill="x", side="bottom")

        def close_settings():
            global settings_window, snow_effect
            if snow_effect:
                snow_effect.stop()
                snow_effect = None
            settings_window = None
            root.destroy()

        close_btn = tk.Button(footer, text=tr("close"), font=("Segoe UI", 9), bg=t["btn_bg"], fg=t["fg"], relief="flat", cursor="hand2", padx=25, pady=6, command=close_settings)
        close_btn.pack()
        settings_widgets_button.append((close_btn, "close", True))

        root.protocol("WM_DELETE_WINDOW", close_settings)

    root_tk.after(0, build)

# ==============================
#  Трей
# ==============================
tray_icon = None
root_tk = None

def build_tray_menu():
    return Menu(
        MenuItem('Открыть меню', show_tray_popup, default=True),
        MenuItem(tr("menu_settings"), open_settings),
        Menu.SEPARATOR,
        MenuItem(tr("menu_exit"), lambda: safe_quit())
    )

# ==============================
#  Фоновая проверка смены ивента
# ==============================
last_event_state = None

def check_event_change():
    global last_event_state, current_theme_name, THEME, settings_window, snow_effect
    
    while True:
        time.sleep(60)
        current_event = get_active_event()
        
        if current_event != last_event_state:
            last_event_state = current_event
            
            if current_event:
                current_theme_name = current_event
                preset = THEME_PRESETS[current_theme_name]
                for k in THEME:
                    if k in preset and k not in ["event_only", "event_name"]:
                        THEME[k] = preset[k]
                event_names = {"halloween": "🎃 Хэллоуин", "newyear": "🎄 Новый год"}
                notify("Сезонный ивент!", f"{event_names.get(current_event, '')} активирован! 🎉", "info")
                
                # Закрываем окно настроек для обновления темы и снега
                if settings_window:
                    try:
                        if settings_window.winfo_exists():
                            settings_window.destroy()
                            settings_window = None
                            root_tk.after(500, open_settings)
                    except:
                        pass
            else:
                saved_theme = config.get("theme", "dark")
                if saved_theme in THEME_PRESETS:
                    current_theme_name = saved_theme
                    preset = THEME_PRESETS[current_theme_name]
                    for k in THEME:
                        if k in preset and k not in ["event_only", "event_name"]:
                            THEME[k] = preset[k]
                notify("Сезонный ивент завершён", "Возвращение к обычной теме", "info")
                
                if settings_window:
                    try:
                        if settings_window.winfo_exists():
                            settings_window.destroy()
                            settings_window = None
                            root_tk.after(500, open_settings)
                    except:
                        pass
            
            if tray_icon:
                tray_icon.icon = create_tray_image()

# ==============================
#  Запуск
# ==============================
if __name__ == "__main__":
    load_config()
    apply_startup_settings()
    last_event_state = get_active_event()

    root_tk = tk.Tk()
    root_tk.withdraw()

    def show_startup_notification():
        time.sleep(1)
        notify(tr("app_name"), tr("startup_msg"), "info")
    threading.Thread(target=show_startup_notification, daemon=True).start()

    if config['auto_clear_enabled']:
        start_auto_clear()
    
    tray_icon = Icon(tr("app_name"), create_tray_image(), menu=build_tray_menu())

    def update_icon_loop():
        while True:
            time.sleep(60)
            if tray_icon:
                tray_icon.icon = create_tray_image()
    threading.Thread(target=update_icon_loop, daemon=True).start()
    threading.Thread(target=tray_icon.run, daemon=True).start()
    threading.Thread(target=check_event_change, daemon=True).start()
    
    root_tk.mainloop()
