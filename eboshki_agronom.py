import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
import json
import os
import math
import random
from datetime import datetime, timedelta

# Настройки оформления
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("green")

SAVE_FILE = "grow_tracker_save.json"

# Глобальный набор символов для "Гуру"
GURU_CHARS = (
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "abcdefghijklmnopqrstuvwxyz"
    "АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ"
    "абвгдеёжзийклмнопрстуфхцчшщъыьэюя"
    "0123456789"
)

class GrowTrackerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Grow Tracker Pro v3.5 - Guru Edition")
        self.geometry("1150x950")
        self.resizable(False, False)

        # Данные приложения
        self.plants_data = []
        self.current_plant_idx = 0
        
        # Списки объектов
        self.bugs = []
        self.bullets = []
        self.water_drops = []
        self.effects = []  
        
        # Переменные для динамики полива и реакции куста
        self.watering_active = False
        self.watering_timer = 0
        self.soil_moisture = 0.0
        self.animation_tick = 0

        self.load_data()
        self.setup_main_tabs()
        self.setup_guru_button()   # <- добавлено
        self.spawn_bug_loop()
        self.update_game_loop()

    # ------------------- Новая кнопка "Спросить гуру" -------------------
    def setup_guru_button(self):
        # Кнопка привязывается к правому нижнему углу окна
        self.guru_btn = ctk.CTkButton(
            self,
            text="❓ Спросить гуру",
            fg_color="#8e44ad",
            hover_color="#9b59b6",
            font=("Segoe UI", 14, "bold"),
            command=self.ask_guru,
            width=150,
            height=40
        )
        self.guru_btn.place(relx=1.0, rely=1.0, x=-20, y=-20, anchor='se')

    def ask_guru(self):
        """Генерирует случайную строку и показывает её в отдельном окне."""
        length = random.randint(3, 9)
        phrase = ''.join(random.choice(GURU_CHARS) for _ in range(length))
        
        # Создаём всплывающее окно
        popup = ctk.CTkToplevel(self)
        popup.title("Совет Гуру")
        popup.geometry("400x200")
        popup.resizable(False, False)
        popup.transient(self)  # всегда поверх главного окна
        popup.grab_set()       # модальность
        
        # Центрируем относительно главного окна
        x = self.winfo_x() + (self.winfo_width() - 400) // 2
        y = self.winfo_y() + (self.winfo_height() - 200) // 2
        popup.geometry(f"+{x}+{y}")
        
        # Большой текст
        label = ctk.CTkLabel(
            popup,
            text=phrase,
            font=("Segoe UI", 28, "bold"),
            text_color="#f1c40f"
        )
        label.pack(expand=True, padx=20, pady=20)
        
        # Кнопка закрытия
        btn_close = ctk.CTkButton(popup, text="Закрыть", width=100, command=popup.destroy)
        btn_close.pack(pady=(0, 20))

    # ------------------- Лунный календарь (без изменений) -------------------
    def calculate_moon_details(self, date):
        base_new_moon = datetime(2000, 1, 6)
        diff = date - base_new_moon
        days = diff.total_seconds() / 86400.0
        lunation = days / 29.530588853
        phase_pos = lunation % 1.0
        age = phase_pos * 29.53
        illum = (1.0 - math.cos(phase_pos * 2.0 * math.pi)) / 2.0 * 100.0
        
        if phase_pos < 0.03 or phase_pos > 0.97: emoji, name = "🌑", "Новолуние"
        elif phase_pos < 0.22: emoji, name = "🌒", "Растущий серп"
        elif phase_pos < 0.28: emoji, name = "🌓", "Первая четверть"
        elif phase_pos < 0.47: emoji, name = "🌔", "Растущая Луна"
        elif phase_pos < 0.53: emoji, name = "🌕", "Полнолуние"
        elif phase_pos < 0.72: emoji, name = "🌖", "Убывающая Луна"
        elif phase_pos < 0.78: emoji, name = "🌗", "Последняя четверть"
        else: emoji, name = "🌘", "Убывающий серп"
            
        return emoji, name, illum, age

    # ------------------- Загрузка / сохранение -------------------
    def load_data(self):
        if os.path.exists(SAVE_FILE):
            try:
                with open(SAVE_FILE, "r", encoding="utf-8") as f:
                    self.plants_data = json.load(f)
                # Убедимся, что у каждого растения есть поле events
                for plant in self.plants_data:
                    if "events" not in plant:
                        plant["events"] = []
                while len(self.plants_data) < 5:
                    self.plants_data.append(self.get_default_plant(len(self.plants_data)))
            except Exception:
                self.init_default_data()
        else:
            self.init_default_data()

    def get_default_plant(self, index):
        return {
            "name": f"Куст #{index + 1}",
            "stage": 0,
            "seed_date": datetime.now().strftime("%d.%m.%Y"),
            "cycle_days": 56,
            "last_watering": "Не отмечался",
            "turret_pos": None,
            "events": []   # новый список событий
        }

    def init_default_data(self):
        self.plants_data = [self.get_default_plant(i) for i in range(5)]
        self.save_data()

    def save_data(self):
        try:
            with open(SAVE_FILE, "w", encoding="utf-8") as f:
                json.dump(self.plants_data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Ошибка сохранения: {e}")

    # ------------------- Основные вкладки -------------------
    def setup_main_tabs(self):
        self.master_tabs = ctk.CTkTabview(self, segmented_button_fg_color="#1e272e")
        self.master_tabs.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.tab_garden = self.master_tabs.add("🌿 Моя Оранжерея & Защита")
        self.tab_moon = self.master_tabs.add("🌙 Лунный Календарь Гровера")
        
        self.setup_garden_ui()
        self.setup_moon_calendar_ui()

    # ------------------- Интерфейс оранжереи (с дневником) -------------------
    def setup_garden_ui(self):
        # Верхняя панель с переключателями растений
        self.top_frame = ctk.CTkFrame(self.tab_garden, height=60)
        self.top_frame.pack(fill="x", padx=15, pady=10)
        
        self.tabs = ctk.CTkSegmentedButton(
            self.top_frame, 
            values=[self.plants_data[i]["name"] for i in range(5)],
            command=self.switch_plant
        )
        self.tabs.pack(fill="both", expand=True, padx=10, pady=10)
        self.tabs.set(self.plants_data[0]["name"])

        # Основной контейнер (левая панель + канвас)
        self.main_container = ctk.CTkFrame(self.tab_garden, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True, padx=15, pady=5)

        # Левая панель управления
        self.left_panel = ctk.CTkFrame(self.main_container, width=300)
        self.left_panel.pack(side="left", fill="y", padx=(0, 10))

        ctk.CTkLabel(self.left_panel, text="Панель управления", font=("Segoe UI", 18, "bold")).pack(pady=10)

        # Имя
        name_frame = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        name_frame.pack(fill="x", padx=15, pady=5)
        self.name_entry = ctk.CTkEntry(name_frame, placeholder_text="Имя растения")
        self.name_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        ctk.CTkButton(name_frame, text="✏", width=40, command=self.update_plant_name).pack(side="right")

        # Дата посева
        date_frame = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        date_frame.pack(fill="x", padx=15, pady=5)
        self.date_entry = ctk.CTkEntry(date_frame, placeholder_text="ДД.ММ.ГГГГ")
        self.date_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        ctk.CTkButton(date_frame, text="Применить", width=80, command=self.update_seed_date).pack(side="right")

        # Кнопки стадий
        self.stage_buttons = []
        stages = [
            "Стадия 0: Посев", "Стадия 1: Прорастание", "Стадия 2: Вегетация",
            "Стадия 3: Активный куст", "Стадия 4: Привязка (LST)", "Стадия 5: Цветение"
        ]
        for idx, stage_text in enumerate(stages):
            btn = ctk.CTkButton(
                self.left_panel, text=stage_text, 
                fg_color="#27ae60" if idx == 0 else "#2c3e50",
                command=lambda i=idx: self.set_stage(i)
            )
            btn.pack(fill="x", padx=15, pady=3)
            self.stage_buttons.append(btn)

        # Цикл
        cycle_frame = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        cycle_frame.pack(fill="x", padx=15, pady=10)
        ctk.CTkLabel(cycle_frame, text="Срок (дней):").pack(side="left", padx=5)
        self.cycle_entry = ctk.CTkEntry(cycle_frame, width=60)
        self.cycle_entry.pack(side="left", padx=5)
        ctk.CTkButton(cycle_frame, text="Применить", command=self.update_cycle).pack(side="right", fill="x", expand=True)

        # Полив
        self.water_btn = ctk.CTkButton(self.left_panel, text="💦 Отметить Полив", fg_color="#2980b9", hover_color="#3498db", command=self.mark_watering)
        self.water_btn.pack(fill="x", padx=15, pady=5)

        # Информация о свете и луне
        emoji, phase_name, illum, _ = self.calculate_moon_details(datetime.now())
        self.light_label = ctk.CTkLabel(self.left_panel, text="Режим света: 18/6", font=("Segoe UI", 13, "bold"))
        self.light_label.pack(pady=2)
        self.moon_label = ctk.CTkLabel(self.left_panel, text=f"Луна сегодня: {emoji} {phase_name} ({int(illum)}%)", font=("Segoe UI", 12))
        self.moon_label.pack(pady=2)

        # Новая кнопка "Подрезка" (быстрое добавление события)
        ctk.CTkButton(self.left_panel, text="✂ Подрезка", fg_color="#8e44ad", hover_color="#9b59b6",
                      command=self.add_pruning_event).pack(fill="x", padx=15, pady=5)

        # Сброс
        ctk.CTkButton(self.left_panel, text="Сбросить все данные", fg_color="#c0392b", hover_color="#e74c3c",
                      command=self.reset_current_plant).pack(fill="x", padx=15, pady=(20, 10))

        # Канвас (справа)
        self.canvas_frame = ctk.CTkFrame(self.main_container)
        self.canvas_frame.pack(side="right", fill="both", expand=True)
        self.canvas = tk.Canvas(self.canvas_frame, bg="#a0e0ff", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True, padx=10, pady=10)
        self.canvas.bind("<Button-1>", self.squish_bug_lmb)
        self.canvas.bind("<Button-3>", self.place_turret_rmb)

        # Нижняя строка статуса
        self.bottom_frame = ctk.CTkFrame(self.tab_garden, height=40)
        self.bottom_frame.pack(fill="x", padx=15, pady=(0, 5))
        self.status_label = ctk.CTkLabel(self.bottom_frame, text="Загрузка...", font=("Segoe UI", 12))
        self.status_label.pack(side="left", padx=15, pady=5)
        self.progress_bar = ctk.CTkProgressBar(self.bottom_frame, progress_color="#2ecc71")
        self.progress_bar.pack(side="right", fill="x", expand=True, padx=15, pady=10)

        # ---------- НОВЫЙ ФРЕЙМ ДНЕВНИКА (внизу) ----------
        self.journal_frame = ctk.CTkFrame(self.tab_garden, fg_color="#1e272e")
        self.journal_frame.pack(fill="x", padx=15, pady=(0, 15))

        # Заголовок и кнопка добавления
        header = ctk.CTkFrame(self.journal_frame, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(header, text="📋 Дневник событий", font=("Segoe UI", 16, "bold")).pack(side="left")
        ctk.CTkButton(header, text="➕ Добавить событие", width=150, command=self.add_event_dialog).pack(side="right")

        # Прокручиваемый список событий
        self.journal_list = ctk.CTkScrollableFrame(self.journal_frame, height=150, fg_color="#2c3e50")
        self.journal_list.pack(fill="x", padx=10, pady=(0, 10))

        # Первоначальное обновление
        self.refresh_plant_ui()

    # ------------------- Дневник событий -------------------
    def refresh_journal(self):
        # Очищаем список
        for widget in self.journal_list.winfo_children():
            widget.destroy()

        plant = self.plants_data[self.current_plant_idx]
        events = plant.get("events", [])

        if not events:
            # Пустой дневник
            ctk.CTkLabel(self.journal_list, text="Нет записей", text_color="#7f8c8d", font=("Segoe UI", 12)).pack(pady=10)
            return

        # Сортируем по дате (новые сверху)
        try:
            events_sorted = sorted(events, key=lambda e: datetime.strptime(e.get("date", "01.01.2000"), "%d.%m.%Y"), reverse=True)
        except:
            events_sorted = events

        for ev in events_sorted:
            ev_type = ev.get("type", "Событие")
            ev_date = ev.get("date", "??.??.????")
            # Иконка в зависимости от типа
            icon_map = {
                "посев": "🌱",
                "росток": "🌿",
                "вега": "🌳",
                "подрезка": "✂️",
                "подвязка": "🪢",
                "цветение": "🌸",
                "сбор": "🍃",
                "полив": "💧"
            }
            icon = icon_map.get(ev_type.lower(), "📌")

            # Строка события
            row = ctk.CTkFrame(self.journal_list, fg_color="transparent")
            row.pack(fill="x", pady=2)

            lbl = ctk.CTkLabel(row, text=f"{icon} {ev_type}  –  {ev_date}", anchor="w", font=("Segoe UI", 12))
            lbl.pack(side="left", padx=5)

            # Кнопка удаления
            del_btn = ctk.CTkButton(row, text="✕", width=30, fg_color="#e74c3c", hover_color="#c0392b",
                                    command=lambda e=ev: self.delete_event(e))
            del_btn.pack(side="right", padx=5)

    def add_event(self, event_type, date_str=None):
        if date_str is None:
            date_str = datetime.now().strftime("%d.%m.%Y")
        # Проверка формата
        try:
            datetime.strptime(date_str, "%d.%m.%Y")
        except ValueError:
            messagebox.showerror("Ошибка", "Неверный формат даты! Используйте ДД.ММ.ГГГГ")
            return

        plant = self.plants_data[self.current_plant_idx]
        plant.setdefault("events", []).append({"type": event_type, "date": date_str})
        self.save_data()
        self.refresh_journal()

    def delete_event(self, event):
        plant = self.plants_data[self.current_plant_idx]
        if "events" in plant:
            plant["events"] = [e for e in plant["events"] if e != event]
            self.save_data()
            self.refresh_journal()

    def add_pruning_event(self):
        """Быстрая подрезка с сегодняшней датой"""
        self.add_event("Подрезка")

    def add_event_dialog(self):
        """Диалог добавления события с выбором типа и даты"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Добавить событие")
        dialog.geometry("350x200")
        dialog.resizable(False, False)

        ctk.CTkLabel(dialog, text="Тип события:", font=("Segoe UI", 13)).pack(pady=(15, 5))
        type_var = ctk.StringVar(value="Посев")
        types = ["Посев", "Росток", "Вега", "Подрезка", "Подвязка", "Цветение", "Сбор", "Полив", "Другое"]
        combo = ctk.CTkComboBox(dialog, values=types, variable=type_var)
        combo.pack(pady=5)

        ctk.CTkLabel(dialog, text="Дата (ДД.ММ.ГГГГ):", font=("Segoe UI", 13)).pack(pady=(10, 5))
        date_entry = ctk.CTkEntry(dialog, placeholder_text=datetime.now().strftime("%d.%m.%Y"))
        date_entry.pack(pady=5)

        def confirm():
            ev_type = type_var.get()
            ev_date = date_entry.get().strip()
            if not ev_date:
                ev_date = datetime.now().strftime("%d.%m.%Y")
            self.add_event(ev_type, ev_date)
            dialog.destroy()

        ctk.CTkButton(dialog, text="Добавить", command=confirm).pack(pady=15)

    # ------------------- Остальные методы (без изменений) -------------------
    def switch_plant(self, selected_name):
        for idx, plant in enumerate(self.plants_data):
            if plant["name"] == selected_name:
                self.current_plant_idx = idx
                break
        self.canvas.delete("game_bugs", "water_drops", "effects")
        self.bugs.clear()
        self.bullets.clear()
        self.water_drops.clear()
        self.effects.clear()
        self.watering_active = False
        self.soil_moisture = 0.0
        self.refresh_plant_ui()

    def refresh_plant_ui(self):
        plant = self.plants_data[self.current_plant_idx]
        self.name_entry.delete(0, tk.END)
        self.name_entry.insert(0, plant["name"])
        self.date_entry.delete(0, tk.END)
        self.date_entry.insert(0, plant["seed_date"])
        self.cycle_entry.delete(0, tk.END)
        self.cycle_entry.insert(0, str(plant["cycle_days"]))
        self.set_stage_buttons_highlight(plant["stage"])
        self.update_status_progress()
        self.redraw_plant()
        self.refresh_journal()

    def set_stage_buttons_highlight(self, active_idx):
        for idx, btn in enumerate(self.stage_buttons):
            if idx == active_idx: btn.configure(fg_color="#27ae60", hover_color="#2ecc71")
            else: btn.configure(fg_color="#2c3e50", hover_color="#34495e")

    def set_stage(self, stage_idx):
        self.plants_data[self.current_plant_idx]["stage"] = stage_idx
        self.set_stage_buttons_highlight(stage_idx)
        self.save_data()
        self.redraw_plant()

    def update_plant_name(self):
        new_name = self.name_entry.get().strip()
        if new_name:
            self.plants_data[self.current_plant_idx]["name"] = new_name
            self.tabs.configure(values=[p["name"] for p in self.plants_data])
            self.tabs.set(new_name)
            self.save_data()
            self.redraw_plant()

    def update_seed_date(self):
        new_date = self.date_entry.get().strip()
        try:
            datetime.strptime(new_date, "%d.%m.%Y")
            self.plants_data[self.current_plant_idx]["seed_date"] = new_date
            self.save_data()
            self.update_status_progress()
        except ValueError:
            messagebox.showerror("Ошибка", "Неверный формат даты!")

    def update_cycle(self):
        try:
            days = int(self.cycle_entry.get())
            if days > 0:
                self.plants_data[self.current_plant_idx]["cycle_days"] = days
                self.save_data()
                self.update_status_progress()
            else: raise ValueError
        except ValueError:
            messagebox.showerror("Ошибка", "Введите число дней больше 0.")

    def mark_watering(self):
        now_str = datetime.now().strftime("%d.%m.%Y %H:%M")
        self.plants_data[self.current_plant_idx]["last_watering"] = now_str
        # Добавляем событие полива в дневник
        self.add_event("Полив", datetime.now().strftime("%d.%m.%Y"))
        self.save_data()
        self.update_status_progress()
        self.watering_active = True
        self.watering_timer = 60
        self.soil_moisture = 1.0
        self.water_drops.clear()

    def update_status_progress(self):
        plant = self.plants_data[self.current_plant_idx]
        try:
            seed_dt = datetime.strptime(plant["seed_date"], "%d.%m.%Y")
            elapsed = max(0, (datetime.now() - seed_dt).days)
        except Exception: elapsed = 0

        cycle_days = plant["cycle_days"]
        progress = min(1.0, elapsed / cycle_days) if cycle_days > 0 else 0.0
        self.progress_bar.set(progress)
        self.status_label.configure(text=f"День {elapsed} из {cycle_days} | Последний полив: {plant['last_watering']}")

    def reset_current_plant(self):
        if messagebox.askyesno("Подтверждение", "Сбросить прогресс текущего куста?"):
            self.plants_data[self.current_plant_idx] = self.get_default_plant(self.current_plant_idx)
            self.save_data()
            self.refresh_plant_ui()

    # ------------------- Рисование растения (без изменений) -------------------
    def draw_leaf_cluster(self, x, y, size=12):
        for angle in [0, 45, 90, 135, 180, 225, 270, 315]:
            rad = math.radians(angle)
            lx = x + size * math.cos(rad)
            ly = y + size * math.sin(rad)
            self.canvas.create_polygon([x, y, lx, ly, x + (size//2)*math.cos(rad+0.4), y + (size//2)*math.sin(rad+0.4)], fill="#27ae60", outline="#1e8449", tags="plant")

    def draw_cannabis_bud(self, x, y, size=24):
        self.canvas.create_oval(x-size//1.3, y-size*1.3, x+size//1.3, y+size//1.5, fill="#196f3d", outline="#114f2c", tags="plant")
        random.seed(int(x + y))
        for _ in range(14):
            ox, oy = random.randint(-size//2, size//2), random.randint(-size, size//2)
            r = random.randint(5, 9)
            self.canvas.create_oval(x+ox-r, y+oy-r, x+ox+r, y+oy+r, fill="#229954", outline="#145a32", tags="plant")
        for angle in [-60, -30, 0, 30, 60, 135, 225]:
            rad = math.radians(angle)
            self.canvas.create_line(x, y - size//2, x + (size * 1.2) * math.cos(rad), y + (size * 1.2) * math.sin(rad), fill="#27ae60", width=2, tags="plant")
        for _ in range(12):
            hx1, hy1 = x + random.randint(-size//2, size//2), y + random.randint(-size, size//2)
            self.canvas.create_line(hx1, hy1, hx1 + random.randint(-8, 8), hy1 - random.randint(6, 12), fill="#e67e22", width=2, tags="plant")
        random.seed()

    def draw_roots_recursive(self, x, y, angle, length, depth, max_depth, color):
        if depth > max_depth or length < 3: return
        
        rad = math.radians(angle)
        x_end = x + length * math.sin(rad)
        y_end = y + length * math.cos(rad)
        
        if y_end < 570 and (220 + (y_end-400)*0.16) < x_end < (480 - (y_end-400)*0.16):
            self.canvas.create_line(x, y, x_end, y_end, fill=color, width=max(1, (max_depth-depth)), tags="plant")
            new_len = length * random.uniform(0.65, 0.85)
            self.draw_roots_recursive(x_end, y_end, angle - random.randint(15, 40), new_len, depth + 1, max_depth, color)
            self.draw_roots_recursive(x_end, y_end, angle + random.randint(15, 40), new_len, depth + 1, max_depth, color)

    def redraw_plant(self):
        self.canvas.delete("plant")
        plant = self.plants_data[self.current_plant_idx]
        stage = plant["stage"]

        self.canvas.create_text(350, 40, text=plant["name"].upper(), font=("Segoe UI", 24, "bold"), fill="#2c3e50", tags="plant")

        pot_top_y, pot_bot_y = 400, 590
        pot_left_x1, pot_right_x2 = 220, 480
        pot_bot_left, pot_bot_right = 250, 450

        r_col = int(92 - (92 - 44) * self.soil_moisture)
        g_col = int(58 - (58 - 26) * self.soil_moisture)
        b_col = int(33 - (33 - 12) * self.soil_moisture)
        soil_color = f"#{r_col:02x}{g_col:02x}{b_col:02x}"

        self.canvas.create_polygon([pot_left_x1+6, pot_top_y+2, pot_right_x2-6, pot_top_y+2, pot_bot_right-6, pot_bot_y-18, pot_bot_left+6, pot_bot_y-18], fill=soil_color, tags="plant")
        
        self.canvas.create_polygon([pot_bot_left+7, pot_bot_y-18, pot_bot_right-7, pot_bot_y-18, pot_bot_right-5, pot_bot_y-5, pot_bot_left+5, pot_bot_y-5], fill="#d35400", outline="#b34a00", tags="plant")
        for i in range(pot_bot_left+12, pot_bot_right-10, 10):
            self.canvas.create_oval(i-4, pot_bot_y-12, i+4, pot_bot_y-4, fill="#e67e22", outline="", tags="plant")

        if stage > 0:
            random.seed(1337)
            root_color = "#f5f5dc" if self.soil_moisture < 0.5 else "#e4e4b2"
            max_depth_level = min(2 + stage, 7)
            initial_length = 20 + stage * 7
            
            self.draw_roots_recursive(350, pot_top_y + 4, 0, initial_length, 1, max_depth_level, root_color)
            self.draw_roots_recursive(350, pot_top_y + 25, -35, initial_length * 0.8, 1, max_depth_level - 1, root_color)
            self.draw_roots_recursive(350, pot_top_y + 25, 35, initial_length * 0.8, 1, max_depth_level - 1, root_color)
            random.seed()

        self.canvas.create_polygon([pot_left_x1, pot_top_y, pot_right_x2, pot_top_y, pot_bot_right, pot_bot_y, pot_bot_left, pot_bot_y], fill="", outline="#d35400", width=6, tags="plant")
        self.canvas.create_rectangle(pot_left_x1-5, pot_top_y-10, pot_right_x2+5, pot_top_y+5, fill="#e67e22", outline="#d35400", width=2, tags="plant")

        wave = math.sin(self.animation_tick * 0.4) * 3.5 if self.watering_active else 0.0
        plant_base_x, plant_base_y = 350, pot_top_y + 5

        if stage == 0:
            self.canvas.create_oval(plant_base_x-5, plant_base_y+15, plant_base_x+5, plant_base_y+22, fill="#f39c12", tags="plant")
        elif stage == 1:
            self.canvas.create_line(plant_base_x, plant_base_y, plant_base_x + wave*0.3, plant_base_y-40, fill="#2ecc71", width=4, tags="plant")
            self.canvas.create_oval(plant_base_x-12 + wave*0.3, plant_base_y-48, plant_base_x + wave*0.3, plant_base_y-38, fill="#27ae60", tags="plant")
            self.canvas.create_oval(plant_base_x + wave*0.3, plant_base_y-48, plant_base_x+12 + wave*0.3, plant_base_y-38, fill="#27ae60", tags="plant")
        elif stage == 2:
            self.canvas.create_line(plant_base_x, plant_base_y, plant_base_x + wave*0.5, plant_base_y-120, fill="#2ecc71", width=6, tags="plant")
            self.canvas.create_line(plant_base_x, plant_base_y-50, plant_base_x-40 + wave*0.3, plant_base_y-80 + wave, fill="#2ecc71", width=4, tags="plant")
            self.canvas.create_line(plant_base_x, plant_base_y-80, plant_base_x+40 + wave*0.7, plant_base_y-110 + wave, fill="#2ecc71", width=4, tags="plant")
            self.draw_leaf_cluster(plant_base_x-40 + wave*0.3, plant_base_y-80 + wave, 14)
            self.draw_leaf_cluster(plant_base_x+40 + wave*0.7, plant_base_y-110 + wave, 14)
            self.draw_leaf_cluster(plant_base_x + wave*0.5, plant_base_y-120, 18)
        elif stage == 3:
            self.canvas.create_line(plant_base_x, plant_base_y, plant_base_x + wave*0.4, plant_base_y-160, fill="#27ae60", width=8, tags="plant")
            branches = [(-50, -60), (50, -90), (-60, -120), (60, -140)]
            for bx, by in branches:
                self.canvas.create_line(plant_base_x, plant_base_y + by + 40, plant_base_x + bx + wave, plant_base_y + by + wave*0.5, fill="#2ecc71", width=5, tags="plant")
                self.draw_leaf_cluster(plant_base_x + bx + wave, plant_base_y + by + wave*0.5, 16)
            self.draw_leaf_cluster(plant_base_x + wave*0.4, plant_base_y-160, 22)
        elif stage in [4, 5]:
            is_bloom = (stage == 5)
            self.canvas.create_line(plant_base_x, plant_base_y, plant_base_x, plant_base_y-50, fill="#27ae60", width=9, tags="plant")
            self.canvas.create_line(plant_base_x, plant_base_y-50, plant_base_x-130, plant_base_y-70 + wave*0.4, fill="#27ae60", width=8, tags="plant")
            
            sub_branches = [
                (320, plant_base_y - 53, 80),
                (290, plant_base_y - 58, 105),
                (260, plant_base_y - 62, 125),
                (230, plant_base_y - 66, 140)
            ]
            for start_x, start_y, height in sub_branches:
                self.canvas.create_line(start_x, start_y + wave*0.4, start_x, start_y - height + wave, fill="#2ecc71", width=5, tags="plant")
                if is_bloom:
                    self.draw_cannabis_bud(start_x, start_y - height + wave, 22)
                else:
                    self.draw_leaf_cluster(start_x, start_y - height + wave, 18)

            self.canvas.create_line(plant_base_x-100, plant_base_y-65, pot_left_x1+5, pot_top_y+15, fill="#e74c3c", width=3, tags="plant")
            self.canvas.create_oval(pot_left_x1, pot_top_y+10, pot_left_x1+10, pot_top_y+20, fill="#c0392b", outline="", tags="plant")

        if plant.get("turret_pos"):
            tx, ty = plant["turret_pos"]["x"], plant["turret_pos"]["y"]
            ammo = plant["turret_pos"].get("shots_left", 3)
            self.canvas.create_oval(tx-15, ty-15, tx+15, ty+15, fill="#34495e", outline="#1abc9c", width=2, tags="plant")
            self.canvas.create_line(tx, ty, tx, ty-25, fill="#1abc9c", width=6, tags="plant")
            self.canvas.create_text(tx, ty-35, text="⚫"*ammo, fill="#f1c40f", font=("Arial", 10, "bold"), tags="plant")

    # ------------------- Игровая механика (без изменений) -------------------
    def create_bug_splat_effect(self, x, y):
        particles = []
        for _ in range(25):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(2.5, 9.5)
            particles.append({
                'x': x, 'y': y,
                'vx': math.cos(angle) * speed,
                'vy': math.sin(angle) * speed,
                'size': random.randint(3, 8),
                'color': random.choice(["#c0392b", "#962d22", "#e74c3c", "#d35400", "#27ae60", "#196f3d"])
            })
        self.effects.append({
            'x': x, 'y': y,
            'particles': particles,
            'radius': 3,
            'lifetime': 16
        })

    def place_turret_rmb(self, event):
        plant = self.plants_data[self.current_plant_idx]
        if plant.get("turret_pos") is None:
            plant["turret_pos"] = {"x": event.x, "y": event.y, "shots_left": 3, "cooldown": 0}
            self.save_data()
            self.redraw_plant()

    def squish_bug_lmb(self, event):
        clicked_bug = None
        for bug in self.bugs:
            dist = math.sqrt((event.x - bug['x'])**2 + (event.y - bug['y'])**2)
            if dist < 25:
                clicked_bug = bug
                break
        if clicked_bug:
            self.create_bug_splat_effect(clicked_bug['x'], clicked_bug['y'])
            self.bugs.remove(clicked_bug)

    def spawn_bug_loop(self):
        if len(self.bugs) < 5:
            bx = random.randint(50, 650)
            by = random.randint(60, 320)
            self.bugs.append({'x': bx, 'y': by, 'angle': random.uniform(0, 2*math.pi)})
        self.after(random.randint(2500, 4500), self.spawn_bug_loop)

    def update_game_loop(self):
        self.canvas.delete("game_bugs", "water_drops", "effects")
        self.animation_tick += 1
        
        plant = self.plants_data[self.current_plant_idx]
        t_pos = plant.get("turret_pos")

        # Полив и высыхание
        if self.watering_active:
            if self.watering_timer > 10:
                for _ in range(3):
                    drop_x = random.randint(200, 500)
                    drop_y = random.randint(30, 100)
                    self.water_drops.append({'x': drop_x, 'y': drop_y, 'speed': random.randint(8, 14), 'len': random.randint(12, 22)})
            
            active_drops = []
            for drop in self.water_drops:
                drop['y'] += drop['speed']
                self.canvas.create_line(drop['x'], drop['y'], drop['x'], drop['y'] + drop['len'], fill="#3498db", width=2, tags="water_drops")
                if drop['y'] < 415: active_drops.append(drop)
            self.water_drops = active_drops
            
            self.watering_timer -= 1
            if self.watering_timer <= 0:
                self.watering_active = False
            self.redraw_plant()
        else:
            if self.soil_moisture > 0.0:
                self.soil_moisture -= 0.005
                if self.soil_moisture < 0: self.soil_moisture = 0.0
                self.redraw_plant()

        # Эффекты
        active_effects = []
        for fx in self.effects:
            fx['lifetime'] -= 1
            fx['radius'] += 2.5
            self.canvas.create_oval(fx['x'] - fx['radius'], fx['y'] - fx['radius'], fx['x'] + fx['radius'], fx['y'] + fx['radius'], fill="", outline="#962d22", width=2, tags="effects")
            
            for p in fx['particles']:
                p['x'] += p['vx']
                p['y'] += p['vy']
                p_size = max(1, p['size'] - (16 - fx['lifetime']) // 3)
                self.canvas.create_oval(p['x'] - p_size, p['y'] - p_size, p['x'] + p_size, p['y'] + p_size, fill=p['color'], outline="", tags="effects")
            if fx['lifetime'] > 0: active_effects.append(fx)
        self.effects = active_effects

        # Жуки
        for bug in self.bugs:
            bug['angle'] += random.uniform(-0.3, 0.3)
            bug['x'] += math.cos(bug['angle']) * 2.3
            bug['y'] += math.sin(bug['angle']) * 2.3
            if bug['x'] < 20 or bug['x'] > 680: bug['angle'] = math.pi - bug['angle']
            if bug['y'] < 40 or bug['y'] > 360: bug['angle'] = -bug['angle']

            x, y = bug['x'], bug['y']
            self.canvas.create_line(x-12, y-4, x+12, y+4, fill="#1a252f", width=2, tags="game_bugs")
            self.canvas.create_line(x-12, y, x+12, y, fill="#1a252f", width=2, tags="game_bugs")
            self.canvas.create_line(x-12, y+4, x+12, y-4, fill="#1a252f", width=2, tags="game_bugs")
            self.canvas.create_oval(x-8, y-6, x+8, y+6, fill="#7d6608", outline="#424949", width=1.5, tags="game_bugs")
            self.canvas.create_oval(x-3, y-9, x+3, y-4, fill="#1a252f", tags="game_bugs")

        # Турель
        if t_pos and self.bugs:
            if "cooldown" not in t_pos: t_pos["cooldown"] = 0
            if t_pos["cooldown"] > 0: t_pos["cooldown"] -= 1
            elif t_pos.get("shots_left", 0) > 0:
                target = self.bugs[0]
                tx, ty = t_pos["x"], t_pos["y"]
                bullet_id = self.canvas.create_line(tx, ty-20, tx, ty-35, fill="#f1c40f", width=4)
                dx, dy = target['x'] - tx, target['y'] - ty
                dist = math.sqrt(dx**2 + dy**2)
                if dist > 0:
                    self.bullets.append({'id': bullet_id, 'x': tx, 'y': ty-25, 'mx': (dx / dist) * 16, 'my': (dy / dist) * 16})
                    t_pos["shots_left"] -= 1
                    t_pos["cooldown"] = 9
                    self.redraw_plant()
                    if t_pos["shots_left"] <= 0:
                        plant["turret_pos"] = None
                        self.save_data()
                        self.redraw_plant()
                        t_pos = None

        keep_bullets = []
        for b in self.bullets:
            self.canvas.move(b['id'], b['mx'], b['my'])
            b['x'] += b['mx']
            b['y'] += b['my']
            
            hit = False
            for bug in self.bugs:
                if math.sqrt((b['x'] - bug['x'])**2 + (b['y'] - bug['y'])**2) < 22:
                    self.canvas.delete(b['id'])
                    self.create_bug_splat_effect(bug['x'], bug['y'])
                    if bug in self.bugs: self.bugs.remove(bug)
                    hit = True
                    break
            if not hit:
                if 0 < b['x'] < 800 and 0 < b['y'] < 800: keep_bullets.append(b)
                else: self.canvas.delete(b['id'])
        self.bullets = keep_bullets

        self.after(50, self.update_game_loop)

    # ------------------- Лунный календарь (без изменений) -------------------
    def setup_moon_calendar_ui(self):
        ctk.CTkLabel(self.tab_moon, text="Лунный Посевной Календарь на 30 дней", font=("Segoe UI", 22, "bold"), text_color="#2ecc71").pack(pady=15)
        self.moon_scroll = ctk.CTkScrollableFrame(self.tab_moon, width=1100, height=680)
        self.moon_scroll.pack(fill="both", expand=True, padx=20, pady=10)
        
        headers_frame = ctk.CTkFrame(self.moon_scroll, fg_color="#1e2d1f", height=35)
        headers_frame.pack(fill="x", pady=5, padx=5)
        headers_frame.pack_propagate(False)
        
        ctk.CTkLabel(headers_frame, text="Дата", font=("Segoe UI", 13, "bold"), width=140, anchor="w").pack(side="left", padx=15)
        ctk.CTkLabel(headers_frame, text="Фаза Луны", font=("Segoe UI", 13, "bold"), width=220, anchor="w").pack(side="left", padx=15)
        ctk.CTkLabel(headers_frame, text="Освещенность", font=("Segoe UI", 13, "bold"), width=120, anchor="w").pack(side="left", padx=15)
        ctk.CTkLabel(headers_frame, text="Рекомендация по уходу за растениями", font=("Segoe UI", 13, "bold"), anchor="w").pack(side="left", padx=15)
        
        start_date = datetime.now()
        weekdays_ru = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
        
        for i in range(30):
            target_date = start_date + timedelta(days=i)
            emoji, phase_name, illum, age = self.calculate_moon_details(target_date)
            date_str = f"{target_date.strftime('%d.%m.%Y')} ({weekdays_ru[target_date.weekday()]})"
            
            row_bg = "#2c3e50" if i % 2 == 0 else "#242424"
            row = ctk.CTkFrame(self.moon_scroll, fg_color=row_bg, height=55)
            row.pack(fill="x", pady=4, padx=5)
            row.pack_propagate(False)
            
            ctk.CTkLabel(row, text=date_str, width=140, font=("Segoe UI", 12, "bold"), anchor="w").pack(side="left", padx=15)
            ctk.CTkLabel(row, text=f"{emoji} {phase_name}", width=220, anchor="w").pack(side="left", padx=15)
            ctk.CTkLabel(row, text=f"{illum:.1f}%", width=120, anchor="w").pack(side="left", padx=15)
            
            if "Новолуние" in phase_name or "Полнолуние" in phase_name:
                tip = "❌ Стрессовый день. Запрещены пересадки, обрезки и тренировки. Дайте кустам отдохнуть."
                color = "#e74c3c"
            elif "Растущая" in phase_name or "Растущий" in phase_name or "Первая" in phase_name:
                tip = "🌱 Прекрасно для вегетации, пикирования, клонирования и обильного полива водой."
                color = "#2ecc71"
            else:
                tip = "🪵 Отлично для тренировок (LST/дефолиации), внесения удобрений и борьбы с вредителями."
                color = "#f1c40f"
                
            lbl = ctk.CTkTextbox(row, fg_color="transparent", text_color=color, font=("Segoe UI", 12), border_width=0, activate_scrollbars=False, wrap="word", height=45)
            lbl.insert("1.0", tip)
            lbl.configure(state="disabled")
            lbl.pack(side="left", padx=15, fill="both", expand=True)


if __name__ == "__main__":
    app = GrowTrackerApp()
    app.mainloop()
    
######################\\\\\\\\\\\\\\\\\\\сделано с помощью нейронок и мощных бошек\\\ Asp710 ### !!!СОЗДАНО ИСКЛЮЧИТЕЛЬНО В РАЗВЛЕКАТЕЛЬНОМ ХАРАКТЕРЕ!!!