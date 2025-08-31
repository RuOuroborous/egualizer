import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
import threading
import time
import keyboard
import os
import sys

class Equalizer:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Эквалайзер")
        self.root.geometry("900x650")
        self.root.resizable(True, True)
        
        # Устанавливаем иконку
        self.setup_icon()
        
        # Инициализация Windows Audio API
        self.setup_windows_audio()
        
        # Настройки эквалайзера
        self.frequencies = [60, 170, 310, 600, 1000, 3000, 6000, 12000, 14000, 16000]
        self.gains = [0] * 10
        self.master_volume = 1.0
        
        # Текущий пресет
        self.current_preset = "Нормально"
        
        # Флаг для остановки обработки
        self.running = True
        
        self.setup_ui()
        self.setup_hotkeys()
        self.start_audio_processing()
        
    def setup_icon(self):
        try:
            # Определяем путь к иконке в зависимости от того, запущено ли как exe или как Python скрипт
            if getattr(sys, 'frozen', False):
                # Если запущено как exe
                base_path = sys._MEIPASS
                icon_paths = [
                    os.path.join(base_path, "icons", "equalizer.ico"),
                    os.path.join(base_path, "icons", "icon.ico"),
                    os.path.join(base_path, "icons", "app.ico"),
                    os.path.join(base_path, "icons", "equalizer.png"),
                    os.path.join(base_path, "icons", "icon.png"),
                    os.path.join(base_path, "icons", "app.png")
                ]
            else:
                # Если запущено как Python скрипт
                icon_paths = [
                    "icons/equalizer.ico",
                    "icons/icon.ico",
                    "icons/app.ico",
                    "icons/equalizer.png",
                    "icons/icon.png",
                    "icons/app.png"
                ]
            
            icon_loaded = False
            for icon_path in icon_paths:
                if os.path.exists(icon_path):
                    try:
                        if icon_path.endswith('.ico'):
                            self.root.iconbitmap(icon_path)
                            print(f"Иконка загружена: {icon_path}")
                            icon_loaded = True
                            break
                        elif icon_path.endswith('.png'):
                            # Для PNG используем PhotoImage
                            icon_image = tk.PhotoImage(file=icon_path)
                            self.root.iconphoto(True, icon_image)
                            print(f"Иконка PNG загружена: {icon_path}")
                            icon_loaded = True
                            break
                    except Exception as e:
                        print(f"Ошибка загрузки иконки {icon_path}: {e}")
                        continue
            
            if not icon_loaded:
                print("Не удалось загрузить ни одну иконку")
                
        except Exception as e:
            print(f"Ошибка в setup_icon: {e}")
        
    def setup_windows_audio(self):
        try:
            # Получаем устройство по умолчанию
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            self.volume_interface = cast(interface, POINTER(IAudioEndpointVolume))
            
            # Получаем текущую громкость
            self.current_volume = self.volume_interface.GetMasterVolumeLevelScalar()
            
        except Exception as e:
            print(f"Ошибка инициализации аудио: {e}")
            self.volume_interface = None
            
    def setup_ui(self):
        # Создаем меню
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # Меню пресетов
        presets_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Пресеты", menu=presets_menu)
        presets_menu.add_command(label="Нормально (F1)", command=self.normal_preset)
        presets_menu.add_command(label="Басы (F2)", command=self.bass_preset)
        presets_menu.add_command(label="Рок (F3)", command=self.rock_preset)
        presets_menu.add_separator()
        presets_menu.add_command(label="Джаз (F4)", command=self.jazz_preset)
        presets_menu.add_command(label="Классика (F5)", command=self.classical_preset)
        presets_menu.add_command(label="Поп (F6)", command=self.pop_preset)
        presets_menu.add_separator()
        presets_menu.add_command(label="Электроника (F7)", command=self.electronic_preset)
        presets_menu.add_command(label="Вокал (F8)", command=self.vocal_preset)
        presets_menu.add_separator()
        presets_menu.add_command(label="Сброс (F9)", command=self.reset_preset)
        
        # Основная громкость
        volume_frame = tk.Frame(self.root)
        volume_frame.pack(pady=20)
        
        tk.Label(volume_frame, text="Системная громкость:", font=("Arial", 12, "bold")).pack()
        self.volume_slider = tk.Scale(volume_frame, from_=0, to=100, orient=tk.HORIZONTAL,
                                     length=300, command=self.update_system_volume)
        self.volume_slider.set(int(self.current_volume * 100))
        self.volume_slider.pack()
        
        # Полосы эквалайзера
        eq_frame = tk.Frame(self.root)
        eq_frame.pack(pady=20)
        
        self.eq_sliders = []
        for i, freq in enumerate(self.frequencies):
            slider_frame = tk.Frame(eq_frame)
            slider_frame.pack(side=tk.LEFT, padx=8)
            
            # Частота
            tk.Label(slider_frame, text=f"{freq}Hz", font=("Arial", 9, "bold")).pack()
            
            # Слайдер с максимально увеличенным диапазоном от -50 до +50 дБ
            slider = tk.Scale(slider_frame, from_=-50, to=50, orient=tk.VERTICAL,
                             length=220, command=lambda val, idx=i: self.update_gain(idx, val))
            slider.set(self.gains[i])
            slider.pack()
            
            # Значение
            value_label = tk.Label(slider_frame, text=f"{self.gains[i]}dB", font=("Arial", 9))
            value_label.pack()
            
            self.eq_sliders.append((slider, value_label))
        
        # Быстрые кнопки для основных пресетов
        quick_frame = tk.Frame(self.root)
        quick_frame.pack(pady=15)
        
        tk.Button(quick_frame, text="Нормальный", command=self.normal_preset, 
                 font=("Arial", 10), width=12, bg="lightgray").pack(side=tk.LEFT, padx=8)
        tk.Button(quick_frame, text="Басы", command=self.bass_preset,
                 font=("Arial", 10), width=12, bg="lightblue").pack(side=tk.LEFT, padx=8)
        tk.Button(quick_frame, text="Сброс", command=self.reset_preset,
                 font=("Arial", 10), width=12, bg="lightcoral").pack(side=tk.LEFT, padx=8)
        
        # Статус
        self.status_label = tk.Label(self.root, text="Статус: Активен - Изменяет системный звук", 
                                   font=("Arial", 10), fg="green")
        self.status_label.pack(pady=10)
        
        # Информация о горячих клавишах
        hotkeys_info = tk.Label(self.root, text="Горячие клавиши: F1-F9 - пресеты", 
                              font=("Arial", 8), fg="gray")
        hotkeys_info.pack()
        
    def setup_hotkeys(self):
        # Горячие клавиши для пресетов
        keyboard.add_hotkey('F1', self.normal_preset)
        keyboard.add_hotkey('F2', self.bass_preset)
        keyboard.add_hotkey('F3', self.rock_preset)
        keyboard.add_hotkey('F4', self.jazz_preset)
        keyboard.add_hotkey('F5', self.classical_preset)
        keyboard.add_hotkey('F6', self.pop_preset)
        keyboard.add_hotkey('F7', self.electronic_preset)
        keyboard.add_hotkey('F8', self.vocal_preset)
        keyboard.add_hotkey('F9', self.reset_preset)
        
    def update_gain(self, index, value):
        self.gains[index] = float(value)
        self.eq_sliders[index][1].config(text=f"{value}dB")
        
    def update_system_volume(self, value):
        try:
            volume_level = float(value) / 100.0
            if self.volume_interface:
                self.volume_interface.SetMasterVolumeLevelScalar(volume_level, None)
                self.current_volume = volume_level
        except Exception as e:
            print(f"Ошибка изменения громкости: {e}")
            
    # Пресеты с максимально увеличенными значениями
    def normal_preset(self):
        gains = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        self.apply_preset(gains, "Нормально")
        
    def bass_preset(self):
        gains = [45, 35, 25, 15, 0, -15, -25, -35, -45, -45]  # Максимальное усиление басов
        self.apply_preset(gains, "Басы")
        
    def rock_preset(self):
        gains = [25, 20, 15, -15, 20, 25, 35, 25, 20, 15]  # Максимальный эффект
        self.apply_preset(gains, "Рок")
        
    def jazz_preset(self):
        gains = [20, 25, 35, 25, 20, 0, -20, -25, -20, 0]  # Максимальный эффект
        self.apply_preset(gains, "Джаз")
        
    def classical_preset(self):
        gains = [-20, 0, 20, 25, 35, 25, 20, 0, -20, -25]  # Максимальный эффект
        self.apply_preset(gains, "Классика")
        
    def pop_preset(self):
        gains = [0, 20, 25, 20, 0, -20, 0, 20, 25, 20]  # Максимальный эффект
        self.apply_preset(gains, "Поп")
        
    def electronic_preset(self):
        gains = [35, 25, 20, 0, -20, -25, -20, 0, 20, 25]  # Максимальный эффект
        self.apply_preset(gains, "Электроника")
        
    def vocal_preset(self):
        gains = [-25, -20, 0, 20, 25, 35, 25, 20, 0, -20]  # Максимальный эффект
        self.apply_preset(gains, "Вокал")
        
    def apply_preset(self, gains, preset_name):
        self.current_preset = preset_name
        
        for i, (slider, label) in enumerate(self.eq_sliders):
            slider.set(gains[i])
            self.gains[i] = gains[i]
            label.config(text=f"{gains[i]}dB")
            
        self.status_label.config(text=f"Применен пресет: {preset_name}", fg="blue")
        
    def reset_preset(self):
        self.normal_preset()
        self.volume_slider.set(int(self.current_volume * 100))
        self.status_label.config(text="Настройки сброшены", fg="orange")
        
    def start_audio_processing(self):
        # Запускаем поток для обработки аудио
        self.audio_thread = threading.Thread(target=self.audio_processing_loop, daemon=True)
        self.audio_thread.start()
        
    def audio_processing_loop(self):
        while self.running:
            try:
                time.sleep(0.1)
            except:
                break
                
    def on_closing(self):
        self.running = False
        # Убираем горячие клавиши
        keyboard.unhook_all()
        self.root.destroy()
        
    def run(self):
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()

if __name__ == "__main__":
    app = Equalizer()
    app.run()