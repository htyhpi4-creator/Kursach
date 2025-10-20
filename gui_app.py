import os
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

from map_manager import MapManager, MAX_POINTS
from point import MapPoint


class FilterDialog(simpledialog.Dialog):
    CRITERIA_MAP = {
        "Поверхня": "surface",
        "Півкуля широти": "hem_lat",
        "Півкуля довготи": "hem_lon"
    }

    def body(self, master):
        self._body_master = master

        ttk.Label(master, text="Критерій:").grid(row=0, column=0, sticky="w")
        self.criteria = ttk.Combobox(master, values=list(self.CRITERIA_MAP.keys()), state="readonly")
        self.criteria.current(0)
        self.criteria.grid(row=0, column=1, pady=5, padx=5)
        self.criteria.bind("<<ComboboxSelected>>", self._on_criteria_change)

        ttk.Label(master, text="Значення:").grid(row=1, column=0, sticky="w")
        self.value_widget = ttk.Combobox(master, values=["материк", "острів", "океан", "озеро"], state="readonly")
        self.value_widget.current(0)
        self.value_widget.grid(row=1, column=1, pady=5, padx=5)
        return self.criteria

    def _on_criteria_change(self, event=None):
        crit_human = self.criteria.get()
        crit = self.CRITERIA_MAP[crit_human]

        try:
            self.value_widget.destroy()
        except Exception:
            pass

        parent = self._body_master
        if crit == "surface":
            self.value_widget = ttk.Combobox(parent, values=["материк", "острів", "океан", "озеро"], state="readonly")
        elif crit == "hem_lat":
            self.value_widget = ttk.Combobox(parent, values=["N", "S"], state="readonly")
        elif crit == "hem_lon":
            self.value_widget = ttk.Combobox(parent, values=["E", "W"], state="readonly")
        else:
            self.value_widget = ttk.Entry(parent)
        self.value_widget.grid(row=1, column=1, pady=5, padx=5)

    def apply(self):
        crit_human = self.criteria.get()
        crit_machine = self.CRITERIA_MAP[crit_human]
        value = self.value_widget.get().strip()
        self.result = (crit_machine, value)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Курсова робота: Точки на мапі")
        self.geometry("1000x700")
        self.minsize(900, 600)

        self._setup_styles()

        self.manager = MapManager()
        self._tag_to_point = {}
        self._hover_tag = None
        self._is_reversed = False

        if not os.path.exists('locations.txt'):
            messagebox.showwarning("Увага",
                                   "Файл 'locations.txt' не знайдено. Будуть використовуватись підстановки для назв місць.")

        self._listbox_ids = []
        self._tree_iid_to_point_id = {}
        self._tree_order_iids = []
        self.create_widgets()
        self.update_points_list()

        self.points_tree.bind('<Up>', lambda e: self._move_selection(-1))
        self.points_tree.bind('<Down>', lambda e: self._move_selection(1))
        self.bind('<Delete>', lambda e: self._trigger_delete_selected())
        self.bind('<Insert>', lambda e: self.add_point())
        self.bind('<Control-s>', lambda e: self.sort_points())

    def _setup_styles(self):
        style = ttk.Style(self)
        try:
            style.theme_use('clam')
        except Exception:
            pass
        base_font = ("Segoe UI", 10)
        heading_font = ("Segoe UI", 12, "bold")
        style.configure("TLabel", font=base_font)
        style.configure("TButton", font=base_font, padding=6)
        style.configure("TEntry", font=base_font)
        style.configure("TCombobox", font=base_font)
        style.configure("Treeview", font=("Consolas", 10), rowheight=24)
        style.configure("Treeview.Heading", font=heading_font)
        style.configure("TLabelframe.Label", font=heading_font)

    def create_widgets(self):
        menubar = tk.Menu(self)
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="Вихід", command=self.quit)
        menubar.add_cascade(label="Файл", menu=filemenu)

        actionmenu = tk.Menu(menubar, tearoff=0)
        actionmenu.add_command(label="Створити набір...", command=self.generate_points)
        actionmenu.add_command(label="Додати точку...", command=self.add_point)
        actionmenu.add_command(label="Редагувати вибрану...", command=self.edit_selected)
        actionmenu.add_command(label="Видалити вибрану", command=self.remove_selected)
        actionmenu.add_command(label="Сортувати за місцем", command=self.sort_points)
        actionmenu.add_command(label="Фільтрувати", command=self.filter_points)

        actionmenu.add_separator()
        actionmenu.add_command(label="Показати зворотно", command=self.show_reverse)
        actionmenu.add_command(label="Показати по №", command=self.show_point_by_order)
        menubar.add_cascade(label="Дії", menu=actionmenu)

        self.config(menu=menubar)

        header = ttk.Frame(self, padding=(14, 12))
        header.pack(fill=tk.X)
        title_lbl = ttk.Label(header, text="Курсова робота — Точки на мапі", font=("Segoe UI", 18, "bold"))
        subtitle_lbl = ttk.Label(header, text="", foreground="#555")
        title_lbl.pack(anchor="w")
        subtitle_lbl.pack(anchor="w")

        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        list_frame = ttk.LabelFrame(left_frame, text="Список точок")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        columns = ("order", "id", "location", "surface")
        self.points_tree = ttk.Treeview(list_frame, columns=columns, show="headings", selectmode="browse")
        self.points_tree.heading("order", text="№")
        self.points_tree.heading("id", text="ID")
        self.points_tree.heading("location", text="Місце")
        self.points_tree.heading("surface", text="Поверхня")
        self.points_tree.column("order", width=50, stretch=False, anchor="center")
        self.points_tree.column("id", width=60, stretch=False, anchor="center")
        self.points_tree.column("location", width=260, stretch=True, anchor="w")
        self.points_tree.column("surface", width=120, stretch=False, anchor="center")
        self.points_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.points_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.points_tree.configure(yscrollcommand=scrollbar.set)

        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=False)

        controls_frame = ttk.LabelFrame(right_frame, text="Управління", width=300)
        controls_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        ttk.Button(controls_frame, text="Створити набір", command=self.generate_points).pack(fill=tk.X, pady=3)
        ttk.Button(controls_frame, text="Додати точку", command=self.add_point).pack(fill=tk.X, pady=3)
        ttk.Button(controls_frame, text="Редагувати точку", command=self.edit_selected).pack(fill=tk.X, pady=3)
        ttk.Button(controls_frame, text="Видалити вибрану", command=self.remove_selected).pack(fill=tk.X, pady=3)
        ttk.Separator(controls_frame).pack(fill=tk.X, pady=6)
        ttk.Button(controls_frame, text="Сортувати за місцем", command=self.sort_points).pack(fill=tk.X, pady=3)
        ttk.Button(controls_frame, text="Фільтрувати...", command=self.filter_points).pack(fill=tk.X, pady=3)
        ttk.Button(controls_frame, text="Показати зворотно", command=self.show_reverse).pack(fill=tk.X, pady=3)
        ttk.Button(controls_frame, text="Показати по №", command=self.show_point_by_order).pack(fill=tk.X, pady=3)

        map_frame = ttk.LabelFrame(right_frame, text="Карта")
        map_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=(5, 10))

        map_header_frame = ttk.Frame(map_frame)
        map_header_frame.pack(fill=tk.X, padx=5, pady=(5, 0))
        self.land_percentage_label = ttk.Label(map_header_frame, text="На суші: 0.00%", font=("Segoe UI", 10, "bold"))
        self.land_percentage_label.pack(side=tk.RIGHT)

        self.map_canvas = tk.Canvas(map_frame, width=360, height=360, bg='#fafafa', highlightthickness=0)
        self.map_canvas.pack(fill=tk.BOTH, expand=True)

        legend_frame = ttk.Frame(right_frame)
        legend_frame.pack(side=tk.TOP, fill=tk.X, pady=(0, 10), padx=5)
        ttk.Label(legend_frame, text="Легенда:").pack(side=tk.LEFT, padx=(0, 6))
        ttk.Label(legend_frame, text="● Суша (материк/острів)", foreground="#2e7d32").pack(side=tk.LEFT, padx=4)
        ttk.Label(legend_frame, text="● Океан", foreground="#1565c0").pack(side=tk.LEFT, padx=4)
        ttk.Label(legend_frame, text="● Озеро", foreground="#00838f").pack(side=tk.LEFT, padx=4)

        self.status_bar = ttk.Label(self, text="", anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=5)

        self.map_canvas.bind("<Configure>", lambda e: self.draw_map())
        self.map_canvas.bind("<Motion>", self._on_canvas_motion)
        self.map_canvas.bind("<Leave>", lambda e: self._clear_hover())
        self.map_canvas.bind("<Button-1>", self._on_canvas_click)

    def update_points_list(self, points_to_display=None):
        for iid in self.points_tree.get_children():
            self.points_tree.delete(iid)
        self._tree_iid_to_point_id.clear()
        self._tree_order_iids.clear()

        if points_to_display is None:
            pts = self.manager.get_all_points_list()
            if self._is_reversed:
                pts = list(reversed(pts))
            mode_full = True
        else:
            pts = list(points_to_display)
            mode_full = False

        for idx, p in enumerate(pts, start=1):
            iid = f"row-{p.id}"
            values = (idx, p.id, p.location_name, p.surface)
            self.points_tree.insert("", tk.END, iid=iid, values=values)
            self._tree_iid_to_point_id[iid] = p.id
            self._tree_order_iids.append(iid)

        total_created = MapPoint.get_instance_count()
        total_active = self.manager.get_active_count()
        land_perc = MapPoint.get_land_percentage_from_list(self.manager.get_all_points_list())
        self.status_bar.config(
            text=f"Всього створено: {total_created} | В списку: {total_active} | На суші: {land_perc:.2f}%")

        self.land_percentage_label.config(text=f"На суші: {land_perc:.2f}%")

        self.draw_map()

    def generate_points(self):
        num = simpledialog.askinteger("Створення набору", f"Введіть кількість точок (1-{MAX_POINTS}):", minvalue=1,
                                      maxvalue=MAX_POINTS)
        if num is None:
            return
        created = self.manager.fill_random_points(num, reset_ids=True)
        messagebox.showinfo("Успіх", f"Створено {created} випадкових точок.")
        self.update_points_list()

    def add_point(self):
        if self.manager.get_active_count() >= MAX_POINTS:
            messagebox.showwarning("Ліміт", f"Неможливо додати більше {MAX_POINTS} точок.")
            return

        if messagebox.askyesno("Ручне введення", "Бажаєте ввести дані точки вручну?"):
            loc = simpledialog.askstring("Місце", "Введіть назву місця:")
            if loc is None:
                messagebox.showwarning("Скасовано", "Назва не введена.")
                return
            try:
                lat = simpledialog.askfloat("Широта", "Введіть широту (0-90):", minvalue=0.0, maxvalue=90.0)
                lat_hem = simpledialog.askstring("Півкуля широти", "N або S:")
                lon = simpledialog.askfloat("Довгота", "Введіть довготу (0-180):", minvalue=0.0, maxvalue=180.0)
                lon_hem = simpledialog.askstring("Півкуля довготи", "E або W:")
            except Exception:
                messagebox.showwarning("Скасовано", "Некоректні або неповні дані.")
                return

            if None in (lat, lon, lat_hem, lon_hem):
                messagebox.showwarning("Скасовано", "Некоректні або неповні дані.")
                return
            lat_hem = lat_hem.upper();
            lon_hem = lon_hem.upper()
            if lat_hem not in ('N', 'S') or lon_hem not in ('E', 'W'):
                messagebox.showwarning("Скасовано", "Півкулі повинні бути N/S і E/W.")
                return
            manual = {'location': loc, 'lat': lat, 'lat_hem': lat_hem, 'lon': lon, 'lon_hem': lon_hem}
            try:
                p = self.manager.add_point(manual)
            except ValueError as e:
                messagebox.showerror("Помилка", str(e))
                return
            messagebox.showinfo("Успіх", f"Додано точку (ID {p.id}).")
        else:
            try:
                p = self.manager.add_point()
            except ValueError as e:
                messagebox.showerror("Помилка", str(e))
                return
            messagebox.showinfo("Успіх", f"Додано нову випадкову точку (ID {p.id}).")
        self.update_points_list()

    def remove_selected(self):
        sel = self.points_tree.selection()
        if not sel:
            messagebox.showwarning("Помилка", "Будь ласка, виберіть точку для видалення.")
            return
        iid = sel[0]
        point_id = self._tree_iid_to_point_id.get(iid)
        if point_id is None:
            messagebox.showerror("Помилка", "Не вдалося визначити ID вибраної точки.")
            return

        if messagebox.askyesno("Підтвердження", f"Ви впевнені, що хочете видалити точку з ID {point_id}?"):
            ok = self.manager.remove_point_by_id(point_id)
            if ok:
                messagebox.showinfo("Успіх", f"Точку з ID {point_id} видалено.")
            else:
                messagebox.showerror("Помилка", f"Точку з ID {point_id} не знайдено.")
            self.update_points_list()

    def edit_selected(self):
        sel = self.points_tree.selection()
        if not sel:
            messagebox.showwarning("Помилка", "Виберіть точку для редагування.")
            return
        iid = sel[0]
        point_id = self._tree_iid_to_point_id.get(iid)
        if point_id is None:
            messagebox.showerror("Помилка", "Не вдалося визначити ID вибраної точки.")
            return
        p = self.manager.get_point_by_id(point_id)
        if p is None:
            messagebox.showerror("Помилка", "Точку не знайдено.")
            return
        lat = simpledialog.askfloat("Широта", "Введіть широту (0-90):", initialvalue=p.latitude, minvalue=0.0,
                                    maxvalue=90.0)
        lat_hem = simpledialog.askstring("Півкуля широти", "N або S:", initialvalue=p.latitude_hemisphere)
        lon = simpledialog.askfloat("Довгота", "Введіть довготу (0-180):", initialvalue=p.longitude, minvalue=0.0,
                                    maxvalue=180.0)
        lon_hem = simpledialog.askstring("Півкуля довготи", "E або W:", initialvalue=p.longitude_hemisphere)
        if None in (lat, lon, lat_hem, lon_hem):
            return
        try:
            p.update_coordinates(lat, lat_hem.upper(), lon, lon_hem.upper())
            if messagebox.askyesno("Редагувати назву", "Бажаєте змінити назву місця?"):
                newloc = simpledialog.askstring("Нова назва", "Введіть нову назву:", initialvalue=p.location_name)
                if newloc:
                    p.set_location_name(newloc)
            messagebox.showinfo("Успіх", "Точка оновлена.")
            self.update_points_list()
        except ValueError as e:
            messagebox.showerror("Помилка", str(e))

    def sort_points(self):
        self.manager.sort_by_location_name()
        self.update_points_list()
        messagebox.showinfo("Успіх", "Список відсортовано за назвою місця.")

    def filter_points(self):
        dlg = FilterDialog(self, title="Фільтр")
        if not getattr(dlg, 'result', None):
            return
        key, val = dlg.result
        if not val:
            messagebox.showwarning("Пусто", "Значення фільтра не введене.")
            return
        results = self.manager.filter_by(key, val)
        if not results:
            messagebox.showinfo("Результат", "Точок за заданим фільтром не знайдено.")
            return
        self.update_points_list(results)

    def show_reverse(self):
        self._is_reversed = not self._is_reversed
        self.update_points_list()
        status_text = "Зворотний порядок" if self._is_reversed else "Нормальний порядок"
        messagebox.showinfo("Порядок списку", f": {status_text}")

    def show_point_by_order(self):
        total = self.manager.get_active_count()
        if total == 0:
            messagebox.showinfo("Інфо", "Список порожній.")
            return
        num = simpledialog.askinteger("Показати точку", f"Введіть порядковий номер (1..{total}):", minvalue=1,
                                      maxvalue=total)
        if num is None:
            return
        p = self.manager.get_point_by_index(num - 1)
        if p is None:
            messagebox.showerror("Помилка", "Точка з таким порядковим номером не знайдено.")
            return
        info = f"Порядковий номер: {num}\nID: {p.id}\n{p}"
        messagebox.showinfo(f"Точка №{num}", info)

    def _move_selection(self, delta):
        size = len(self._tree_order_iids)
        if size == 0:
            return
        sel = self.points_tree.selection()
        if not sel:
            idx = 0 if delta >= 0 else size - 1
        else:
            current_iid = sel[0]
            try:
                cur_index = self._tree_order_iids.index(current_iid)
            except ValueError:
                cur_index = 0
            idx = cur_index + delta
            idx = max(0, min(size - 1, idx))
        new_iid = self._tree_order_iids[idx]
        self.points_tree.selection_set(new_iid)
        self.points_tree.focus(new_iid)
        self.points_tree.see(new_iid)

    def _trigger_delete_selected(self):
        self.remove_selected()

    def _latlon_to_canvas(self, lat, lat_hem, lon, lon_hem, width, height):
        lon_val = lon if lon_hem == 'E' else -lon
        lat_val = lat if lat_hem == 'N' else -lat
        x = (lon_val + 180.0) / 360.0 * width
        y = (90.0 - lat_val) / 180.0 * height
        return x, y

    def _draw_sphere(self, cx, cy, radius, base_color, tags=()):
        shadow = self._darker(base_color, 0.35)
        main_id = self.map_canvas.create_oval(cx - radius, cy - radius, cx + radius, cy + radius,
                                              fill=base_color, outline=shadow, width=1.5, tags=tags)
        hl_radius = max(2, int(radius * 0.55))
        highlight_color = self._lighter(base_color, 0.55)
        highlight_id = self.map_canvas.create_oval(cx - hl_radius, cy - hl_radius,
                                                   cx - hl_radius / 3, cy - hl_radius / 3,
                                                   fill=highlight_color, outline="", tags=tags)
        return highlight_id

    def _hex_to_rgb(self, color):
        if color.startswith('#'):
            color = color[1:]
            return tuple(int(color[i:i + 2], 16) for i in (0, 2, 4))
        r, g, b = self.winfo_rgb(color)
        return (r // 256, g // 256, b // 256)

    def _rgb_to_hex(self, rgb):
        r, g, b = rgb
        return f"#{r:02x}{g:02x}{b:02x}"

    def _lighter(self, color, factor):
        r, g, b = self._hex_to_rgb(color)
        r = int(r + (255 - r) * factor)
        g = int(g + (255 - g) * factor)
        b = int(b + (255 - b) * factor)
        return self._rgb_to_hex((min(255, r), min(255, g), min(255, b)))

    def _darker(self, color, factor):
        r, g, b = self._hex_to_rgb(color)
        r = int(r * (1 - factor))
        g = int(g * (1 - factor))
        b = int(b * (1 - factor))
        return self._rgb_to_hex((max(0, r), max(0, g), max(0, b)))

    def _clear_hover(self):
        if self._hover_tag:
            try:
                for item in self.map_canvas.find_withtag(self._hover_tag):
                    self.map_canvas.itemconfigure(item, width=1.5)
            except Exception:
                pass
            self._hover_tag = None

    def _on_canvas_motion(self, event):
        current = self.map_canvas.find_withtag("current")
        if not current:
            self._clear_hover()
            return
        tags = self.map_canvas.gettags(current[0])
        point_tags = [t for t in tags if t.startswith("point-")]
        if not point_tags:
            self._clear_hover()
            return
        tag = point_tags[0]
        if tag == self._hover_tag:
            return
        self._clear_hover()
        try:
            for item in self.map_canvas.find_withtag(tag):
                self.map_canvas.itemconfigure(item, width=3)
        except Exception:
            pass
        self._hover_tag = tag

    def _on_canvas_click(self, event):
        clicked = self.map_canvas.find_withtag("current")
        if not clicked:
            return
        tags = self.map_canvas.gettags(clicked[0])
        tag = next((t for t in tags if t.startswith("point-")), None)
        if not tag:
            return
        point = self._tag_to_point.get(tag)
        if not point:
            return
        info = f"ID: {point.id}\n{point}"
        messagebox.showinfo("Точка", info)

    def draw_map(self):
        try:
            self.map_canvas.delete("all")
        except Exception:
            return
        self._tag_to_point.clear()
        w = int(self.map_canvas.winfo_width()) or 480
        h = int(self.map_canvas.winfo_height()) or 480

        grid_color = "#e0e0e0"
        for lon_deg in range(-180, 181, 30):
            x = (lon_deg + 180) / 360 * w
            dash = () if lon_deg % 60 == 0 else (2, 3)
            self.map_canvas.create_line(x, 0, x, h, fill=grid_color, dash=dash)
        for lat_deg in range(-90, 91, 15):
            y = (90 - lat_deg) / 180 * h
            dash = () if lat_deg % 30 == 0 else (2, 3)
            self.map_canvas.create_line(0, y, w, y, fill=grid_color, dash=dash)

        for p in self.manager.get_all_points_list():
            x, y = self._latlon_to_canvas(p.latitude, p.latitude_hemisphere, p.longitude, p.longitude_hemisphere, w, h)
            r = 9
            if p.surface in ('материк', 'острів'):
                base = '#2e7d32'
            elif p.surface == 'океан':
                base = '#1565c0'
            else:
                base = '#00838f'
            tag = f"point-{p.id}"
            self._tag_to_point[tag] = p
            self._draw_sphere(x, y, r, base, tags=("point", tag))
            self.map_canvas.create_text(x + r + 3, y, text=str(p.id), anchor='w', font=("Arial", 8))

        lx, ly = 8, 8
        self.map_canvas.create_rectangle(lx - 3, ly - 3, lx + 180, ly + 84, outline='', fill='#d0d0d0')
        self.map_canvas.create_rectangle(lx - 4, ly - 4, lx + 176, ly + 80, outline='#bdbdbd', fill='#ffffff')
        self.map_canvas.create_oval(lx + 6, ly + 10, lx + 18, ly + 22, fill='#2e7d32', outline='')
        self.map_canvas.create_text(lx + 26, ly + 16, text="Суша (материк/острів)", anchor='w', font=("Arial", 8))
        self.map_canvas.create_oval(lx + 6, ly + 28, lx + 18, ly + 40, fill='#1565c0', outline='')
        self.map_canvas.create_text(lx + 26, ly + 34, text="Океан", anchor='w', font=("Arial", 8))
        self.map_canvas.create_oval(lx + 6, ly + 46, lx + 18, ly + 58, fill='#00838f', outline='')
        self.map_canvas.create_text(lx + 26, ly + 52, text="Озеро", anchor='w', font=("Arial", 8))


if __name__ == "__main__":
    app = App()
    app.mainloop()