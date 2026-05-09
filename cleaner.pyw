import os
import shutil
import ctypes
import tempfile
import sys
import json
from pystray import Icon, MenuItem, Menu
from PIL import Image, ImageDraw
import threading
import time
from datetime import datetime
import subprocess
import tkinter as tk
import winreg

# ==============================
#  даша путешественица, хуй пойми где я бля
# ==============================

# ==============================
#  Блокировка повторного запуска
# ==============================
MUTEX_NAME = "CleaneyTrayAppMutex_SingleInstance_2024"

def check_single_instance():
    """Проверяет, не запущено ли уже приложение"""
    try:
        # Пытаемся создать мьютекс если нет то хуёво)
        mutex = ctypes.windll.kernel32.CreateMutexW(None, False, MUTEX_NAME)
        if ctypes.windll.kernel32.GetLastError() == 183:
            #  - приложение уже запущено
            return False, None
        return True, mutex
    except Exception as e:
        print(f"Ошибка проверки экземпляра: {e}")
        return True, None

def show_already_running_notification():
    """Показывает уведомление, что приложение уже запущено"""
    try:
        #  найти существующее окно и активировать его
        hwnd = ctypes.windll.user32.FindWindowW(None, "Cleaney")
        if hwnd:
            ctypes.windll.user32.ShowWindow(hwnd, 5)  # SW_SHOW
            ctypes.windll.user32.SetForegroundWindow(hwnd)
        
        # Показываем уведомление 
        title = "Cleaney"
        message = "Приложение уже запущено и работает в системном трее"
        
        #  winotify
        try:
            from winotify import Notification, audio
            toast = Notification(app_id=title, title=title, msg=message, duration="short")
            toast.set_audio(audio.Default, loop=False)
            toast.show()
        except ImportError:
            # Альтернативный способ через PowerShell
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

# ==============================
#  Проверка перед запуском
# ==============================
is_first_instance, mutex_handle = check_single_instance()
if not is_first_instance:
    # Приложение уже запущено
    show_already_running_notification()
    sys.exit(0)

# ==============================
#  бля чё?
# ==============================
def get_app_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))

def get_config_path():
    return os.path.join(get_app_dir(), 'cleaner_config.json')

# ==============================
#  Смена язычка
# ==============================
LANGUAGES = {
    "ru": {
        "name": "Русский",
        "app_name": "Cleaney",
        "startup_msg": "Запущен. Кликните по иконке в трее",
        "already_running": "Приложение уже запущено и работает в системном трее",
        "cleaned": "Очищено",
        "recycle_cleaned": "Корзина очищена",
        "temp_cleaned": "TEMP очищен",
        "temp_cleaned_msg": "TEMP очищен ({} объектов)",
        "error_recycle": "Корзина: {}",
        "error_temp": "TEMP: {}",
        "done": "Готово",
        "cleaned_all": "TEMP и корзина очищены",
        "auto_clean": "Автоочистка",
        "auto_cleaned": "Очищено: {}",
        "auto_enabled": "Автоочистка ВКЛ. Каждые {}",
        "auto_disabled": "Автоочистка ВЫКЛ",
        "interval_changed": "Очистка каждые ",
        "error_input": "Введите число больше 0",
        "menu_clear_all": "Очистить всё",
        "menu_clear_recycle": "Очистить корзину",
        "menu_clear_temp": "Очистить TEMP",
        "menu_settings": "Настройки",
        "menu_exit": "Выход",
        "settings_title": "Cleaney — Настройки",
        "quick_actions": "⚡ БЫСТРЫЕ ДЕЙСТВИЯ",
        "btn_all": "🧹 Всё",
        "btn_recycle": "🗑 Корзина",
        "btn_temp": "📁 TEMP",
        "auto_cleanup": "🤖 АВТООЧИСТКА",
        "enable_auto": "Включить автоочистку",
        "clean_temp": "Очищать TEMP",
        "clean_recycle": "Очищать корзину",
        "enable_ram": "Очищать RAM",
        "interval": "⏱️ ИНТЕРВАЛ",
        "every": "Каждые:",
        "min": "мин",
        "hour": "час",
        "day": "дн",
        "minutes": "мин",
        "hours": "ч",
        "days": "дн",
        "status": "📊 СТАТУС",
        "auto_status": "Автоочистка:",
        "on": "ВКЛ ●",
        "off": "ВЫКЛ ●",
        "last": "Последняя очистка:",
        "never": "никогда",
        "close": "Закрыть",
        "preset_30min": "30 мин",
        "preset_1h": "1 ч",
        "preset_6h": "6 ч",
        "preset_12h": "12 ч",
        "preset_1d": "1 дн",
        "startup": "🚀 АВТОЗАГРУЗКА",
        "enable_startup": "Запускать при старте Windows",
        "startup_enabled": "Автозагрузка ВКЛ",
        "startup_disabled": "Автозагрузка ВЫКЛ",
        "skipped": "занято",
        "btn_ram": "🧠 RAM",
        "ram_cleaned": "Оперативная память очищена",
        "ram_freed": "Освобождено ~{} МБ",
        "error_ram": "RAM: {}",
        "clean_ram": "Очищать RAM",
        "menu_clear_ram": "Очистить RAM",
        "about": "О программе",
    },
    "en": {
        "name": "English",
        "app_name": "Cleaney",
        "startup_msg": "Started. Click the tray icon",
        "already_running": "Application is already running in the system tray",
        "cleaned": "Cleaned",
        "recycle_cleaned": "Recycle bin cleaned",
        "temp_cleaned": "TEMP cleaned",
        "temp_cleaned_msg": "TEMP cleaned ({} items)",
        "error_recycle": "Recycle bin: {}",
        "error_temp": "TEMP: {}",
        "done": "Done",
        "cleaned_all": "TEMP and recycle bin cleaned",
        "auto_clean": "Auto Cleanup",
        "auto_cleaned": "Cleaned: {}",
        "auto_enabled": "Auto cleanup ON. Every {}",
        "auto_disabled": "Auto cleanup OFF",
        "interval_changed": "Cleanup every ",
        "error_input": "Enter a number greater than 0",
        "menu_clear_all": "Clear All",
        "menu_clear_recycle": "Clear Recycle Bin",
        "menu_clear_temp": "Clear TEMP",
        "menu_settings": "Settings",
        "menu_exit": "Exit",
        "settings_title": "Cleaney — Settings",
        "quick_actions": "⚡ QUICK ACTIONS",
        "btn_all": "🧹 All",
        "btn_recycle": "🗑 Recycle",
        "btn_temp": "📁 TEMP",
        "auto_cleanup": "🤖 AUTO CLEANUP",
        "enable_auto": "Enable auto cleanup",
        "clean_temp": "Clean TEMP",
        "clean_recycle": "Clean recycle bin",
        "enable_ram": "Clean RAM",
        "interval": "⏱️ INTERVAL",
        "every": "Every:",
        "min": "min",
        "hour": "hr",
        "day": "day",
        "minutes": "min",
        "hours": "hr",
        "days": "day",
        "status": "📊 STATUS",
        "auto_status": "Auto cleanup:",
        "on": "ON ●",
        "off": "OFF ●",
        "last": "Last cleanup:",
        "never": "never",
        "close": "Close",
        "preset_30min": "30 min",
        "preset_1h": "1 hr",
        "preset_6h": "6 hr",
        "preset_12h": "12 hr",
        "preset_1d": "1 day",
        "startup": "🚀 AUTOSTART",
        "enable_startup": "Run at Windows startup",
        "startup_enabled": "Autostart ON",
        "startup_disabled": "Autostart OFF",
        "skipped": "in use",
        "btn_ram": "🧠 RAM",
        "ram_cleaned": "RAM cleaned",
        "ram_freed": "Freed ~{} MB",
        "error_ram": "RAM: {}",
        "clean_ram": "Clean RAM",
        "menu_clear_ram": "Clear RAM",
        "about": "About",
    }
}

current_lang = "ru"

def tr(key, *args):
    text = LANGUAGES[current_lang].get(key, LANGUAGES["ru"].get(key, key))
    if args:
        return text.format(*args)
    return text

# ==============================
# кфг
# ==============================
CONFIG_FILE = get_config_path()

DEFAULT_CONFIG = {
    "auto_clear_enabled": False,
    "auto_clear_interval": 3600,
    "auto_clear_temp": True,
    "auto_clear_recycle": True,
    "auto_clear_ram": False,
    "last_clear_time": None,
    "last_ram_clear_time": None,
    "last_ram_freed": 0,
    "language": "ru",
    "startup_enabled": False
}

config = DEFAULT_CONFIG.copy()

# ==============================
# темка)
# ==============================
THEME = {
    "bg": "#1e1e2e",
    "bg2": "#2a2a3d",
    "bg3": "#313145",
    "fg": "#cdd6f4",
    "fg2": "#a6adc8",
    "accent": "#89b4fa",
    "btn_bg": "#313145",
    "btn_hover": "#45475a",
    "danger": "#f38ba8",
    "success": "#a6e3a1",
    "warning": "#fab387",
    "separator": "#45475a",
    "entry_bg": "#181825",
}

def T():
    return THEME

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
            ps = f"""
[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType=WindowsRuntime]|Out-Null
[Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType=WindowsRuntime]|Out-Null
$x=New-Object Windows.Data.Xml.Dom.XmlDocument
$x.LoadXml('<toast><visual><binding template="ToastGeneric"><text>{st}</text><text>{sm}</text></binding></visual></toast>')
[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("{tr('app_name')}").Show([Windows.UI.Notifications.ToastNotification]::new($x))
"""
            subprocess.Popen(["powershell", "-WindowStyle", "Hidden", "-Command", ps],
                           creationflags=subprocess.CREATE_NO_WINDOW)
        threading.Thread(target=show, daemon=True).start()

# ==============================
#  Конфиг
# ==============================
def load_config():
    global config, current_lang
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
        else:
            save_config()
    except Exception as e:
        print(f"Ошибка загрузки: {e}")

def save_config():
    try:
        config_dir = os.path.dirname(CONFIG_FILE)
        if config_dir and not os.path.exists(config_dir):
            os.makedirs(config_dir, exist_ok=True)
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Ошибка сохранения: {e}")
        return False

# ==============================
#  Автозагрузка
# ==============================
def get_startup_key_path():
    return r"Software\Microsoft\Windows\CurrentVersion\Run"

def set_autostart(enabled):
    try:
        key_path = get_startup_key_path()
        app_name = "Cleaney"
        
        if getattr(sys, 'frozen', False):
            exe_path = sys.executable
            app_path = f'"{exe_path}"'
        else:
            exe_path = sys.executable
            script_path = os.path.abspath(__file__)
            app_path = f'"{exe_path}" "{script_path}"'
        
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
    except Exception as e:
        return False

def is_autostart_enabled():
    try:
        key_path = get_startup_key_path()
        app_name = "Cleaney"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ) as key:
            winreg.QueryValueEx(key, app_name)
            return True
    except FileNotFoundError:
        return False
    except Exception:
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
#  Улучшенная очистка RAM
# ==============================
def clear_ram_func(silent=False):
    """
    Реальная очистка RAM:
    1. Очищает рабочие наборы ВСЕХ процессов
    2. Очищает системный кэш (standby list)
    3. Показывает реально освобождённый объём памяти
    """
    try:
        import psutil
        
        # Замеряем память ДО очистки
        before = psutil.virtual_memory().available // (1024 * 1024)
        
        # Получаем список всех процессов и очищаем их рабочие наборы
        process_count = 0
        for proc in psutil.process_iter(['pid']):
            try:
                # Открываем процесс с правами на изменение рабочего набора
                PROCESS_SET_QUOTA = 0x0100
                PROCESS_QUERY_INFORMATION = 0x0400
                PROCESS_VM_OPERATION = 0x0008
                access = PROCESS_SET_QUOTA | PROCESS_QUERY_INFORMATION | PROCESS_VM_OPERATION
                
                handle = ctypes.windll.kernel32.OpenProcess(access, False, proc.info['pid'])
                if handle:
                    # Очищаем рабочий набор процесса
                    if ctypes.windll.psapi.EmptyWorkingSet(handle):
                        process_count += 1
                    ctypes.windll.kernel32.CloseHandle(handle)
            except:
                pass
        
        # Очищаем системный файловый кэш (standby list)
        class SYSTEM_MEMORY_LIST_COMMAND(ctypes.Structure):
            _fields_ = [("Command", ctypes.c_ulong)]
        
        # 4 = MemoryPurgeStandbyList (очистка standby списка)
        cmd = SYSTEM_MEMORY_LIST_COMMAND(4)
        ntdll = ctypes.windll.ntdll
        
        try:
            # Пробуем очистить standby list
            ntdll.NtSetSystemInformation(80, ctypes.byref(cmd), ctypes.sizeof(cmd))
            standby_cleared = True
        except:
            standby_cleared = False
        
        # Замеряем память ПОСЛЕ очистки
        after = psutil.virtual_memory().available // (1024 * 1024)
        freed = max(0, after - before)
        
        # Сохраняем статистику
        config["last_ram_clear_time"] = datetime.now().isoformat()
        config["last_ram_freed"] = freed
        save_config()
        
        # Формируем сообщение с деталями
        if not silent:
            details = []
            if process_count > 0:
                details.append(f"процессов: {process_count}")
            if standby_cleared:
                details.append(f"кэш очищен")
            
            detail_str = f" ({', '.join(details)})" if details else ""
            notify(tr("cleaned"), f"{tr('ram_freed', freed)}{detail_str}", "info")
        
        return True
        
    except ImportError:
        # Если psutil не установлен - пробуем хотя бы базовую очистку
        try:
            # Базовый метод через EmptyWorkingSet для текущего процесса
            ctypes.windll.psapi.EmptyWorkingSet(ctypes.windll.kernel32.GetCurrentProcess())
            
            freed = 0
            config["last_ram_clear_time"] = datetime.now().isoformat()
            config["last_ram_freed"] = freed
            save_config()
            
            if not silent:
                notify(tr("cleaned"), tr("ram_cleaned") + " (maybe?)", "info")
            return True
        except Exception as e:
            if not silent:
                notify(tr("cleaned"), tr("error_ram", str(e)), "error")
            return False
            
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
    except (IOError, OSError, PermissionError):
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
                fpath = os.path.join(root, f)
                if is_file_locked(fpath):
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
# авто-очистка
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

        if not timer_running:
            break
        if timer_reset_event.is_set():
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
    else:
        return f"{secs // 86400} {tr('days')}"

# ==============================
# иконка (icon)
# ==============================
def create_tray_image():
    img = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    body = (70, 70, 70)
    lid = (120, 120, 120)
    line = (200, 200, 200)
    draw.rounded_rectangle((18, 20, 46, 54), radius=6, fill=body)
    draw.rectangle((16, 14, 48, 22), fill=lid)
    draw.rectangle((28, 8, 36, 14), fill=lid)
    for x in range(24, 44, 6):
        draw.line((x, 26, x, 50), fill=line, width=2)
    if config['auto_clear_enabled']:
        draw.ellipse((50, 50, 60, 60), fill=(0, 220, 100, 200))
    return img

# ==============================
# трей кастомный
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
    # Освобождаем мьютекс
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
        if popup_creating:
            return
        if popup_window is not None:
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

            def add_separator():
                tk.Frame(win, bg=t["separator"], height=1).pack(fill="x", padx=8, pady=2)

            def add_item(icon_text, label, command, color=None):
                fg = color if color else t["fg"]
                row = tk.Frame(win, bg=t["bg2"], cursor="hand2")
                row.pack(fill="x")
                inner = tk.Frame(row, bg=t["bg2"], padx=14, pady=7)
                inner.pack(fill="x")
                ico_lbl = tk.Label(inner, text=icon_text, font=("Segoe UI", 10),
                                 bg=t["bg2"], fg=fg, width=2, anchor="w")
                ico_lbl.pack(side="left")
                txt_lbl = tk.Label(inner, text=label, font=("Segoe UI", 10),
                                 bg=t["bg2"], fg=fg, anchor="w")
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
                        def execute():
                            time.sleep(0.05)
                            command()
                        threading.Thread(target=execute, daemon=True).start()
                
                for w in (row, inner, ico_lbl, txt_lbl):
                    w.bind("<Enter>", on_enter)
                    w.bind("<Leave>", on_leave)
                    w.bind("<Button-1>", on_click)

            add_item("🧹", tr("menu_clear_all"), do_clear_all)
            add_item("🗑", tr("menu_clear_recycle"), do_clear_recycle)
            add_item("📁", tr("menu_clear_temp"), do_clear_temp)
            add_separator()
            add_item("⚙️", tr("menu_settings"), lambda: open_settings())
            add_separator()
            add_item("🚪", tr("menu_exit"), lambda: safe_quit(), color=t["danger"])

            win.update_idletasks()
            w = win.winfo_reqwidth()
            h = win.winfo_reqheight()
            sw = win.winfo_screenwidth()
            sh = win.winfo_screenheight()
            x = min(cx, sw - w - 4)
            y = max(cy - h - 4, 4)
            win.geometry(f"{w}x{h}+{x}+{y}")
            
            def on_focus_out(e):
                win.after(100, close_popup)
            
            win.bind("<FocusOut>", on_focus_out)
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
# язык
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
#  переключалки
# ==============================
class Switch(tk.Canvas):
    def __init__(self, parent, initial_state=False, command=None, theme_colors=None):
        self.width = 50
        self.height = 26
        self.radius = self.height // 2
        self.state = initial_state
        self.command = command
        self.colors = theme_colors or T()
        
        super().__init__(parent, width=self.width, height=self.height,
                        bg=self.colors["bg2"], highlightthickness=0, cursor="hand2")
        
        self.bind("<Button-1>", self.toggle)
        self.draw()
    
    def draw(self):
        self.delete("all")
        
        if self.state:
            bg_color = self.colors["accent"]
            knob_color = "#ffffff"
        else:
            bg_color = self.colors["btn_bg"]
            knob_color = self.colors["fg2"]
        
        self.create_oval(0, 0, self.height, self.height, fill=bg_color, outline="")
        self.create_oval(self.width - self.height, 0, self.width, self.height, fill=bg_color, outline="")
        self.create_rectangle(self.height//2, 0, self.width - self.height//2, self.height, fill=bg_color, outline="")
        
        if self.state:
            knob_x = self.width - self.height + 2
        else:
            knob_x = 2
        
        self.create_oval(knob_x, 2, knob_x + self.height - 4, self.height - 2,
                        fill=knob_color, outline="", width=0)
    
    def toggle(self, event=None):
        self.state = not self.state
        self.draw()
        if self.command:
            self.command(self.state)
    
    def set_state(self, state):
        self.state = state
        self.draw()
    
    def update_colors(self, new_colors):
        self.colors = new_colors
        self.draw()

# ==============================
#  настройки
# ==============================
settings_window = None
settings_widgets = []
settings_widgets_button = []
settings_dynamic_widgets = []
unit_btns = []
preset_btns = []
cur_unit = 0

def update_ui_language():
    global settings_window
    if not settings_window:
        return
    try:
        if not settings_window.winfo_exists():
            return
    except:
        return
    
    settings_window.title(tr("settings_title"))
    
    for widget, text_key in settings_widgets:
        try:
            if widget and widget.winfo_exists():
                widget.config(text=tr(text_key))
        except:
            pass
    
    for widget, text_key, is_button in settings_widgets_button:
        try:
            if widget and widget.winfo_exists() and is_button:
                widget.config(text=tr(text_key))
        except:
            pass

    for widget, text_fn in settings_dynamic_widgets:
        try:
            if widget and widget.winfo_exists():
                widget.config(text=text_fn())
        except:
            pass

def open_settings(icon=None, item=None):
    global settings_window, settings_widgets, settings_widgets_button, unit_btns, preset_btns, cur_unit
    
    if settings_window is not None:
        try:
            if settings_window.winfo_exists():
                settings_window.lift()
                settings_window.focus_force()
                return
        except:
            settings_window = None
    
    def build():
        global settings_window, settings_widgets, settings_widgets_button, settings_dynamic_widgets, unit_btns, preset_btns, cur_unit
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
        width = root.winfo_width()
        height = root.winfo_height()
        x = (root.winfo_screenwidth() // 2) - (width // 2)
        y = (root.winfo_screenheight() // 2) - (height // 2)
        root.geometry(f'{width}x{height}+{x}+{y}')

        try:
            root.update()
            hwnd = ctypes.windll.user32.GetParent(root.winfo_id())
            val = ctypes.c_int(1)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(val), ctypes.sizeof(val))
        except:
            pass

        header = tk.Frame(root, bg=t["bg2"], pady=14)
        header.pack(fill="x")
        
        title_label = tk.Label(header, text=f"🧹  {tr('app_name')}", font=("Segoe UI", 15, "bold"),
                               bg=t["bg2"], fg=t["accent"])
        title_label.pack(side="left", padx=20)
        settings_widgets.append((title_label, "app_name"))
        
        langs = list(LANGUAGES.keys())

        lang_btn = tk.Button(header,
                           text=LANGUAGES[current_lang]["name"],
                           font=("Segoe UI", 9), bg=t["btn_bg"], fg=t["fg"],
                           activebackground=t["btn_hover"], activeforeground=t["fg"],
                           relief="flat", cursor="hand2", padx=10, pady=5, bd=0)
        lang_btn.pack(side="right", padx=4)
        
        def toggle_language():
            next_lang = langs[(langs.index(current_lang) + 1) % len(langs)]
            change_language(next_lang)
            lang_btn.config(text=LANGUAGES[next_lang]["name"])
        
        lang_btn.config(command=toggle_language)
        settings_dynamic_widgets.append((lang_btn, lambda: LANGUAGES[current_lang]["name"]))
        
        tk.Frame(root, bg=t["separator"], height=1).pack(fill="x")
        
        content = tk.Frame(root, bg=t["bg"], padx=20, pady=10)
        content.pack(fill="both", expand=True)
        
        # БЫСТРЫЕ ДЕЙСТВИЯ
        label_quick = tk.Label(content, text=tr("quick_actions"), font=("Segoe UI", 9, "bold"),
                               bg=t["bg"], fg=t["fg2"])
        label_quick.pack(anchor="w", pady=(0, 8))
        settings_widgets.append((label_quick, "quick_actions"))
        
        btn_frame = tk.Frame(content, bg=t["bg"])
        btn_frame.pack(fill="x", pady=(0, 15))
        
        def make_button(parent, text, color, cmd):
            btn = tk.Button(parent, text=text, font=("Segoe UI", 9, "bold"),
                          bg=color, fg="white", relief="flat", cursor="hand2",
                          padx=18, pady=7, bd=0, command=cmd)
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
        
        # АВТОЗАГРУЗКА
        label_startup = tk.Label(content, text=tr("startup"), font=("Segoe UI", 9, "bold"),
                                 bg=t["bg"], fg=t["fg2"])
        label_startup.pack(anchor="w", pady=(10, 8))
        settings_widgets.append((label_startup, "startup"))
        
        startup_frame = tk.Frame(content, bg=t["bg2"], pady=10)
        startup_frame.pack(fill="x", pady=2)
        
        startup_state = sync_autostart_from_registry()
        
        def on_startup_changed(state):
            set_autostart(state)
            if state:
                notify(tr("auto_clean"), tr("startup_enabled"), "info")
            else:
                notify(tr("auto_clean"), tr("startup_disabled"), "info")
        
        startup_switch = Switch(startup_frame, initial_state=startup_state, 
                               command=on_startup_changed, theme_colors=t)
        startup_switch.pack(side="right", padx=12)
        
        startup_label = tk.Label(startup_frame, text=tr("enable_startup"), font=("Segoe UI", 10),
                                 bg=t["bg2"], fg=t["fg"])
        startup_label.pack(side="left", padx=12)
        settings_widgets.append((startup_label, "enable_startup"))
        
        tk.Frame(content, bg=t["separator"], height=1).pack(fill="x", pady=5)
        
        # АВТООЧИСТКА
        label_auto = tk.Label(content, text=tr("auto_cleanup"), font=("Segoe UI", 9, "bold"),
                              bg=t["bg"], fg=t["fg2"])
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
            if status_text_ref:
                try:
                    if config["auto_clear_enabled"]:
                        status_text_ref.config(text=tr("on"), fg=t["success"])
                    else:
                        status_text_ref.config(text=tr("off"), fg=t["danger"])
                except:
                    pass
            global tray_icon
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
            
            lbl = tk.Label(row, text=tr(label_text), font=("Segoe UI", 10),
                          bg=t["bg2"], fg=t["fg"])
            lbl.pack(side="left", padx=12)
            settings_widgets.append((lbl, label_text))
            
            switch = Switch(row, initial_state=initial_state, command=callback, theme_colors=t)
            switch.pack(side="right", padx=12)
            
            return switch
        
        switches_frame = tk.Frame(content, bg=t["bg"])
        switches_frame.pack(fill="x")
        
        switch_auto = create_switch_row(switches_frame, "enable_auto", auto_state, on_auto_changed)
        switch_temp = create_switch_row(switches_frame, "clean_temp", temp_state, on_temp_changed)
        switch_recycle = create_switch_row(switches_frame, "clean_recycle", recycle_state, on_recycle_changed)
        switch_ram = create_switch_row(switches_frame, "enable_ram", ram_state, on_ram_changed)
        
        tk.Frame(content, bg=t["separator"], height=1).pack(fill="x", pady=10)
        
        # ИНТЕРВАЛ
        label_interval = tk.Label(content, text=tr("interval"), font=("Segoe UI", 9, "bold"),
                                  bg=t["bg"], fg=t["fg2"])
        label_interval.pack(anchor="w", pady=(0, 8))
        settings_widgets.append((label_interval, "interval"))
        
        interval_frame = tk.Frame(content, bg=t["bg2"], pady=10)
        interval_frame.pack(fill="x", pady=2)
        
        label_every = tk.Label(interval_frame, text=tr("every"), font=("Segoe UI", 10),
                               bg=t["bg2"], fg=t["fg"])
        label_every.pack(side="left", padx=12)
        settings_widgets.append((label_every, "every"))
        
        interval_val = tk.StringVar()
        cur_secs = config["auto_clear_interval"]
        if cur_secs % 86400 == 0:
            cur_unit = 2
            cur_val = cur_secs // 86400
        elif cur_secs % 3600 == 0:
            cur_unit = 1
            cur_val = cur_secs // 3600
        else:
            cur_unit = 0
            cur_val = max(1, cur_secs // 60)
        
        interval_val.set(str(cur_val))
        
        entry = tk.Entry(interval_frame, textvariable=interval_val, width=6,
                       font=("Segoe UI", 10), bg=t["entry_bg"], fg=t["fg"],
                       insertbackground=t["fg"], relief="flat", bd=3)
        entry.pack(side="left", padx=5)
        
        units = ["min", "hour", "day"]
        multipliers = [60, 3600, 86400]
        
        def set_unit(idx):
            global cur_unit
            cur_unit = idx
            for i, btn in enumerate(unit_btns):
                try:
                    if btn and btn.winfo_exists():
                        if i == idx:
                            btn.config(bg=t["accent"], fg="white")
                        else:
                            btn.config(bg=t["btn_bg"], fg=t["fg"])
                except:
                    pass
        
        for idx, unit_key in enumerate(units):
            unit_text = tr(unit_key)
            btn = tk.Button(interval_frame, text=unit_text, font=("Segoe UI", 9),
                          bg=t["accent"] if idx == cur_unit else t["btn_bg"],
                          fg="white" if idx == cur_unit else t["fg"],
                          relief="flat", cursor="hand2", padx=10, pady=3,
                          command=lambda i=idx: set_unit(i))
            btn.pack(side="left", padx=2)
            unit_btns.append(btn)
            settings_widgets_button.append((btn, unit_key, False))
        
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
        
        apply_btn = tk.Button(interval_frame, text="✓", font=("Segoe UI", 12, "bold"),
                            bg=t["success"], fg="white", relief="flat",
                            cursor="hand2", padx=12, pady=3, command=apply_interval)
        apply_btn.pack(side="left", padx=8)
        
        presets_frame = tk.Frame(content, bg=t["bg"])
        presets_frame.pack(fill="x", pady=(8, 0))
        
        presets = [(30, 60, "preset_30min"), (1, 3600, "preset_1h"),
                  (6, 3600, "preset_6h"), (12, 3600, "preset_12h"),
                  (1, 86400, "preset_1d")]
        
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
            
            btn = tk.Button(presets_frame, text=tr(text_key), font=("Segoe UI", 9),
                          bg=t["btn_bg"], fg=t["fg"], relief="flat",
                          cursor="hand2", padx=10, pady=4, command=set_preset)
            btn.pack(side="left", padx=(0, 6))
            preset_btns.append(btn)
            settings_widgets_button.append((btn, text_key, True))
        
        tk.Frame(content, bg=t["separator"], height=1).pack(fill="x", pady=10)
        
        # СТАТУС
        status_frame = tk.Frame(content, bg=t["bg2"], pady=10, padx=15)
        status_frame.pack(fill="x", pady=5)
        
        status_title = tk.Label(status_frame, text=tr("status"), font=("Segoe UI", 9, "bold"),
                                bg=t["bg2"], fg=t["accent"])
        status_title.pack(anchor="w", pady=(0, 8))
        settings_widgets.append((status_title, "status"))
        
        auto_row = tk.Frame(status_frame, bg=t["bg2"])
        auto_row.pack(fill="x", pady=3)
        
        auto_label = tk.Label(auto_row, text=tr("auto_status"), font=("Segoe UI", 10),
                             bg=t["bg2"], fg=t["fg"])
        auto_label.pack(side="left")
        settings_widgets.append((auto_label, "auto_status"))
        
        status_text = tk.Label(auto_row, 
                              text=tr("on") if config["auto_clear_enabled"] else tr("off"),
                              font=("Segoe UI", 10, "bold"),
                              bg=t["bg2"], 
                              fg=t["success"] if config["auto_clear_enabled"] else t["danger"])
        status_text.pack(side="left", padx=(10, 0))
        status_text_ref = status_text
        settings_dynamic_widgets.append((status_text, lambda: tr("on") if config["auto_clear_enabled"] else tr("off")))
        
        last_row = tk.Frame(status_frame, bg=t["bg2"])
        last_row.pack(fill="x", pady=3)
        
        last_label = tk.Label(last_row, text=tr("last"), font=("Segoe UI", 10),
                             bg=t["bg2"], fg=t["fg"])
        last_label.pack(side="left")
        settings_widgets.append((last_label, "last"))
        
        last_time_raw = config["last_clear_time"]
        if last_time_raw:
            try:
                last_time = datetime.fromisoformat(last_time_raw).strftime("%d.%m.%Y %H:%M:%S")
            except:
                last_time = last_time_raw
        else:
            last_time = tr("never")
        
        last_value = tk.Label(last_row, text=last_time, font=("Segoe UI", 10),
                             bg=t["bg2"], fg=t["fg2"])
        last_value.pack(side="left", padx=(10, 0))
        if not last_time_raw:
            settings_dynamic_widgets.append((last_value, lambda: tr("never")))
        
        footer = tk.Frame(root, bg=t["bg2"], pady=10)
        footer.pack(fill="x", side="bottom")
        
        def close_settings():
            global settings_window
            settings_window = None
            root.destroy()
        
        close_btn = tk.Button(footer, text=tr("close"), font=("Segoe UI", 9),
                            bg=t["btn_bg"], fg=t["fg"], relief="flat",
                            cursor="hand2", padx=25, pady=6, command=close_settings)
        close_btn.pack()
        settings_widgets_button.append((close_btn, "close", True))
        
        root.protocol("WM_DELETE_WINDOW", close_settings)
    
    root_tk.after(0, build)

# ==============================
# 📋 трей
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
# не дай бог сука не запуститься!!!
# ==============================
if __name__ == "__main__":
    # Уже проверили в начале файла, что приложение не запущено
    load_config()
    apply_startup_settings()

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
    root_tk.mainloop()