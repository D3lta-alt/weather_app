"""
WeatherPeek - Nepal District Weather App
Flow: Intro Loading -> District Picker -> Fetch Loading -> Weather Result
"""
import os 
import threading
import requests
from datetime import datetime

# Disable multitouch red-dot simulation (Ctrl+click / right-click)
from kivy.config import Config
Config.set("input", "mouse", "mouse,disable_multitouch")

from dotenv import load_dotenv
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.graphics import Color, RoundedRectangle, Rectangle, Ellipse, Line
from kivy.core.window import Window
from kivy.metrics import dp

# ── Config ────────────────────────────────────────────────────────────────────
load_dotenv()

API_KEY = os.getenv("WEATHER_API_KEY")

if not API_KEY:
    raise ValueError("WEATHER_API_KEY not found in .env file")

Window.clearcolor = (0.08, 0.12, 0.22, 1)

# ── All 77 Nepal Districts ────────────────────────────────────────────────────
NEPAL_DISTRICTS = [
    "Achham", "Arghakhanchi", "Baglung", "Baitadi", "Bajhang", "Bajura",
    "Banke", "Bara", "Bardiya", "Bhaktapur", "Bhojpur", "Chitwan",
    "Dadeldhura", "Dailekh", "Dang", "Darchula", "Dhading", "Dhankuta",
    "Dhanusha", "Dolakha", "Dolpa", "Doti", "Gorkha", "Gulmi", "Humla",
    "Ilam", "Jajarkot", "Jhapa", "Jumla", "Kailali", "Kalikot",
    "Kanchanpur", "Kapilvastu", "Kaski", "Kathmandu", "Kavrepalanchok",
    "Khotang", "Lalitpur", "Lamjung", "Mahottari", "Makwanpur", "Manang",
    "Morang", "Mugu", "Mustang", "Myagdi", "Nawalpur", "Nuwakot",
    "Okhaldhunga", "Palpa", "Panchthar", "Parasi", "Parbat", "Parsa",
    "Pyuthan", "Ramechhap", "Rasuwa", "Rautahat", "Rolpa",
    "Rukum Eastern", "Rukum Western", "Rupandehi", "Salyan",
    "Sankhuwasabha", "Saptari", "Sarlahi", "Sindhuli", "Sindhupalchok",
    "Siraha", "Solukhumbu", "Sunsari", "Surkhet", "Syangja", "Tanahun",
    "Taplejung", "Terhathum", "Udayapur",
]

# ── Responsive helpers ────────────────────────────────────────────────────────
def sw(frac):
    return Window.width * frac

def sh(frac):
    return Window.height * frac

def fs(frac):
    return max(dp(10), min(Window.width * frac, dp(60)))

def weather_color(code):
    if code in range(1000, 1001): return (0.20, 0.55, 0.92, 1)
    if code in range(1003, 1010): return (0.35, 0.45, 0.65, 1)
    if code in range(1063, 1100): return (0.25, 0.35, 0.55, 1)
    if code in range(1100, 1200): return (0.55, 0.55, 0.65, 1)
    if code in range(1200, 1300): return (0.45, 0.60, 0.80, 1)
    return (0.15, 0.20, 0.40, 1)


# ═══════════════════════════════════════════════════════════════════════════════
# SCREEN 1 — Intro Loading (cartoon + animation, no API call yet)
# ═══════════════════════════════════════════════════════════════════════════════
class IntroScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._build_ui()

    def _build_ui(self):
        layout = FloatLayout()
        with layout.canvas.before:
            Color(0.08, 0.14, 0.32, 1)
            self._bg = Rectangle(size=Window.size, pos=(0, 0))
        layout.bind(size=lambda w, s: setattr(self._bg, "size", s))

        title = Label(
            text="WeatherPeek",
            font_size=fs(0.09), bold=True, color=(1, 1, 1, 1),
            size_hint=(1, None), height=sh(0.08),
            pos_hint={"center_x": 0.5, "top": 0.93},
        )
        subtitle = Label(
            text="Nepal District Weather",
            font_size=fs(0.042), color=(0.75, 0.88, 1.0, 0.8),
            size_hint=(1, None), height=sh(0.05),
            pos_hint={"center_x": 0.5, "top": 0.84},
        )

        cartoon_size = min(sw(0.65), sh(0.38))
        self.cartoon = CartoonWidget(
            size_hint=(None, None), size=(cartoon_size, cartoon_size),
            pos_hint={"center_x": 0.5, "center_y": 0.53},
        )

        self.loading_label = Label(
            text="Peeking into the clouds...",
            font_size=fs(0.042), color=(0.75, 0.88, 1.0, 1),
            size_hint=(1, None), height=sh(0.05),
            pos_hint={"center_x": 0.5, "top": 0.28},
        )
        self.dots_label = Label(
            text="* o o",
            font_size=fs(0.048), color=(0.5, 0.75, 1.0, 1),
            size_hint=(1, None), height=sh(0.05),
            pos_hint={"center_x": 0.5, "top": 0.21},
        )

        layout.add_widget(title)
        layout.add_widget(subtitle)
        layout.add_widget(self.cartoon)
        layout.add_widget(self.loading_label)
        layout.add_widget(self.dots_label)
        self.add_widget(layout)

    def on_enter(self):
        self._start_animations()
        # Show intro for 2 seconds then go to district picker
        Clock.schedule_once(self._go_to_picker, 2.2)

    def _start_animations(self):
        bob_up   = Animation(y=self.cartoon.y + dp(12), duration=0.9, t="in_out_sine")
        bob_down = Animation(y=self.cartoon.y,           duration=0.9, t="in_out_sine")
        bob_up.bind(on_complete=lambda *a: bob_down.start(self.cartoon))
        bob_down.bind(on_complete=lambda *a: bob_up.start(self.cartoon))
        bob_up.start(self.cartoon)
        self._dot_state = 0
        Clock.schedule_interval(self._cycle_dots, 0.55)

    def _cycle_dots(self, dt):
        patterns = ["* o o", "o * o", "o o *", "o * o"]
        self._dot_state = (self._dot_state + 1) % len(patterns)
        self.dots_label.text = patterns[self._dot_state]

    def _go_to_picker(self, dt):
        Clock.unschedule(self._cycle_dots)
        Animation.cancel_all(self.cartoon)
        self.manager.current = "picker"


# ═══════════════════════════════════════════════════════════════════════════════
# SCREEN 2 — District Picker
# ═══════════════════════════════════════════════════════════════════════════════
class PickerScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._dropdown_visible = False
        self._selected_btn     = None
        self._row_h            = dp(48)
        self._div_h            = dp(1)
        self._build_ui()

    def _build_ui(self):
        # ── Outer BoxLayout: fills screen, dark blue ──────────────────────
        outer = BoxLayout(orientation="vertical")
        with outer.canvas.before:
            Color(0.08, 0.14, 0.32, 1)
            self._bg = Rectangle(size=Window.size, pos=outer.pos)
        outer.bind(
            size=lambda w, s: setattr(self._bg, "size", s),
            pos=lambda w, p: setattr(self._bg, "pos", p),
        )

        # ── Top spacer (pushes content to centre) ─────────────────────────
        self.top_spacer = BoxLayout(size_hint_y=None, height=sh(0.30))

        # ── Title ─────────────────────────────────────────────────────────
        self.title_label = Label(
            text="Search Your District",
            font_size=fs(0.06), bold=True, color=(1, 1, 1, 1),
            size_hint=(1, None), height=dp(50),
            halign="center", valign="middle",
        )
        self.title_label.bind(size=lambda w, s: setattr(w, "text_size", s))

        # ── Search input row (white box, full-width with padding) ──────────
        search_h = dp(48)
        search_row = BoxLayout(
            size_hint=(1, None), height=search_h,
            padding=[sw(0.06), 0, sw(0.06), 0],
        )
        self.search_input = TextInput(
            hint_text="Type to search district...",
            font_size=fs(0.040),
            foreground_color=(0.08, 0.10, 0.20, 1),
            hint_text_color=(0.50, 0.55, 0.68, 1),
            background_color=(1, 1, 1, 1),
            background_normal="",
            background_active="",
            cursor_color=(0.22, 0.51, 0.89, 1),
            multiline=False,
            padding=[dp(14), dp(10)],
            size_hint=(1, 1),
        )
        self.search_input.bind(focus=self._on_focus)
        self.search_input.bind(text=self._on_text_change)
        self.search_input.bind(on_text_validate=self._on_enter)
        search_row.add_widget(self.search_input)

        # ── Dropdown list (hidden until focused) ───────────────────────────
        visible_rows = 7
        list_h = self._row_h * visible_rows + self._div_h * (visible_rows - 1)

        list_row = BoxLayout(
            size_hint=(1, None), height=list_h,
            padding=[sw(0.06), 0, sw(0.06), 0],
        )
        self.list_wrapper = BoxLayout(size_hint=(1, 1))
        with self.list_wrapper.canvas.before:
            Color(1, 1, 1, 1)
            self.list_wrapper._bg = Rectangle(
                size=self.list_wrapper.size, pos=self.list_wrapper.pos
            )
        self.list_wrapper.bind(
            size=lambda w, s: setattr(w._bg, "size", s),
            pos=lambda w, p: setattr(w._bg, "pos", p),
        )

        self.results_scroll = ScrollView(
            size_hint=(1, 1),
            do_scroll_x=False,
            bar_width=dp(5),
            bar_color=(0.45, 0.60, 0.90, 1),
            bar_inactive_color=(0.65, 0.72, 0.88, 0.5),
            scroll_type=["bars", "content"],
            scroll_distance=dp(15),
            scroll_timeout=250,
        )
        self.results_layout = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            spacing=0, padding=[0, 0],
        )
        self.results_layout.bind(
            minimum_height=self.results_layout.setter("height")
        )
        self.results_scroll.add_widget(self.results_layout)
        self.list_wrapper.add_widget(self.results_scroll)
        list_row.add_widget(self.list_wrapper)

        # ── No-result label ───────────────────────────────────────────────
        self.no_result_label = Label(
            text="No district found",
            font_size=fs(0.038), color=(0.85, 0.20, 0.20, 1),
            size_hint=(1, None), height=dp(40),
            halign="center", valign="middle",
            opacity=0,
        )

        # ── Bottom spacer ─────────────────────────────────────────────────
        bottom_spacer = BoxLayout()

        # ── Stacking order ────────────────────────────────────────────────
        outer.add_widget(self.top_spacer)
        outer.add_widget(self.title_label)
        outer.add_widget(search_row)
        outer.add_widget(list_row)          # hidden initially via list_row height=0
        outer.add_widget(self.no_result_label)
        outer.add_widget(bottom_spacer)
        self.add_widget(outer)

        # Hide list row until focused
        self._list_row     = list_row
        self._list_row.height = 0          # zero height = invisible + takes no space
        self._list_row.opacity = 0
        self._list_row.disabled = True

        self._populate(NEPAL_DISTRICTS)

    # ── Show dropdown when search box is tapped ───────────────────────────
    def _on_focus(self, instance, focused):
        if focused and not self._dropdown_visible:
            self._dropdown_visible    = True
            visible_rows              = 7
            list_h = self._row_h * visible_rows + self._div_h * (visible_rows - 1)
            self._list_row.height     = list_h
            self._list_row.opacity    = 1
            self._list_row.disabled   = False
            # Shrink top spacer so everything fits
            self.top_spacer.height    = sh(0.08)

    def on_enter(self):
        self.search_input.text        = ""
        self._dropdown_visible        = False
        self._list_row.height         = 0
        self._list_row.opacity        = 0
        self._list_row.disabled       = True
        self.top_spacer.height        = sh(0.30)
        self._populate(NEPAL_DISTRICTS)

    def _on_text_change(self, instance, value):
        query    = value.strip().lower()
        filtered = NEPAL_DISTRICTS if query == "" else [
            d for d in NEPAL_DISTRICTS if query in d.lower()
        ]
        self._populate(filtered)
        if not self._dropdown_visible:
            self._on_focus(instance, True)

    def _populate(self, districts):
        self.results_layout.clear_widgets()
        self._selected_btn = None

        if not districts:
            self.no_result_label.opacity = 1
            return
        self.no_result_label.opacity = 0

        for i, district in enumerate(districts):
            btn = Button(
                text=district,
                font_size=fs(0.038),
                color=(0.08, 0.10, 0.22, 1),
                halign="left",
                background_color=(1, 1, 1, 1),
                background_normal="",
                background_down="",
                size_hint_y=None, height=self._row_h,
                padding=[dp(16), 0],
            )
            btn.district_name = district

            def _on_press(b, *a):
                if self._selected_btn and self._selected_btn != b:
                    self._selected_btn.background_color = (1, 1, 1, 1)
                    self._selected_btn.color = (0.08, 0.10, 0.22, 1)
                b.background_color = (0.22, 0.51, 0.89, 1)
                b.color = (1, 1, 1, 1)
                self._selected_btn = b

            btn.bind(on_press=_on_press)
            btn.bind(on_release=self._on_district_selected)
            self.results_layout.add_widget(btn)

            if i < len(districts) - 1:
                div = BoxLayout(size_hint_y=None, height=self._div_h)
                with div.canvas.before:
                    Color(0.87, 0.89, 0.93, 1)
                    div._rect = Rectangle(size=div.size, pos=div.pos)
                div.bind(
                    size=lambda w, s: setattr(w._rect, "size", s),
                    pos=lambda w, p: setattr(w._rect, "pos", p),
                )
                self.results_layout.add_widget(div)

    def _on_enter(self, instance):
        query    = instance.text.strip().lower()
        filtered = NEPAL_DISTRICTS if query == "" else [
            d for d in NEPAL_DISTRICTS if query in d.lower()
        ]
        if filtered:
            app = App.get_running_app()
            app.selected_district = filtered[0]
            self.search_input.unbind(text=self._on_text_change)
            self.search_input.text = filtered[0]
            self.search_input.bind(text=self._on_text_change)
            Clock.schedule_once(lambda dt: setattr(self.manager, "current", "fetch_loading"), 0.3)

    def _on_district_selected(self, btn):
        district = btn.district_name
        # Show the chosen district in the search box before navigating
        self.search_input.unbind(text=self._on_text_change)
        self.search_input.text = district
        self.search_input.bind(text=self._on_text_change)
        # Navigate after a short pause so the user sees the selection
        app = App.get_running_app()
        app.selected_district = district
        Clock.schedule_once(lambda dt: setattr(self.manager, "current", "fetch_loading"), 0.3)


# ═══════════════════════════════════════════════════════════════════════════════
# SCREEN 3 — Fetch Loading (cartoon again while API call runs)
# ═══════════════════════════════════════════════════════════════════════════════
class FetchLoadingScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._build_ui()

    def _build_ui(self):
        layout = FloatLayout()
        with layout.canvas.before:
            Color(0.08, 0.14, 0.32, 1)
            self._bg = Rectangle(size=Window.size, pos=(0, 0))
        layout.bind(size=lambda w, s: setattr(self._bg, "size", s))

        self.title_label = Label(
            text="Fetching weather...",
            font_size=fs(0.07), bold=True, color=(1, 1, 1, 1),
            size_hint=(1, None), height=sh(0.08),
            pos_hint={"center_x": 0.5, "top": 0.93},
            halign="center", valign="middle",
        )
        self.title_label.bind(size=lambda w, s: setattr(w, "text_size", s))

        cartoon_size = min(sw(0.65), sh(0.38))
        self.cartoon = CartoonWidget(
            size_hint=(None, None), size=(cartoon_size, cartoon_size),
            pos_hint={"center_x": 0.5, "center_y": 0.53},
        )

        self.status_label = Label(
            text="Connecting to weather service...",
            font_size=fs(0.038), color=(0.75, 0.88, 1.0, 1),
            size_hint=(1, None), height=sh(0.05),
            pos_hint={"center_x": 0.5, "top": 0.28},
            halign="center", valign="middle",
        )
        self.status_label.bind(size=lambda w, s: setattr(w, "text_size", s))

        self.dots_label = Label(
            text="* o o",
            font_size=fs(0.048), color=(0.5, 0.75, 1.0, 1),
            size_hint=(1, None), height=sh(0.05),
            pos_hint={"center_x": 0.5, "top": 0.21},
        )

        layout.add_widget(self.title_label)
        layout.add_widget(self.cartoon)
        layout.add_widget(self.status_label)
        layout.add_widget(self.dots_label)
        self.add_widget(layout)

    def on_enter(self):
        app = App.get_running_app()
        district = getattr(app, "selected_district", "Kathmandu")
        self.title_label.text = f"Getting weather for\n{district}..."
        self._start_animations()
        self._fetch_weather(district)

    def _start_animations(self):
        bob_up   = Animation(y=self.cartoon.y + dp(12), duration=0.9, t="in_out_sine")
        bob_down = Animation(y=self.cartoon.y,           duration=0.9, t="in_out_sine")
        bob_up.bind(on_complete=lambda *a: bob_down.start(self.cartoon))
        bob_down.bind(on_complete=lambda *a: bob_up.start(self.cartoon))
        bob_up.start(self.cartoon)
        self._dot_state = 0
        Clock.schedule_interval(self._cycle_dots, 0.55)

    def _cycle_dots(self, dt):
        patterns = ["* o o", "o * o", "o o *", "o * o"]
        self._dot_state = (self._dot_state + 1) % len(patterns)
        self.dots_label.text = patterns[self._dot_state]

    def _fetch_weather(self, district):
        url = (
            f"https://api.weatherapi.com/v1/forecast.json"
            f"?key={API_KEY}&q={district},Nepal&days=3&aqi=yes"
        )
        threading.Thread(target=self._do_fetch, args=(url,), daemon=True).start()

    def _do_fetch(self, url):
        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            Clock.schedule_once(lambda dt: self._on_success(data), 0)
        except Exception as exc:
            Clock.schedule_once(lambda dt: self._on_error(str(exc)), 0)

    def _on_success(self, data):
        App.get_running_app().weather_data = data
        Clock.schedule_once(lambda dt: self._go_to_weather(), 0.6)

    def _on_error(self, msg):
        self.status_label.text = f"Error: {msg}"
        self.dots_label.text = "Go back and try again"
        Clock.unschedule(self._cycle_dots)
        Animation.cancel_all(self.cartoon)

    def _go_to_weather(self):
        Clock.unschedule(self._cycle_dots)
        Animation.cancel_all(self.cartoon)
        self.manager.current = "weather"


# ═══════════════════════════════════════════════════════════════════════════════
# SCREEN 4 — Weather Result
# ═══════════════════════════════════════════════════════════════════════════════
class WeatherScreen(Screen):
    def on_enter(self):
        self.clear_widgets()
        self._build_ui(App.get_running_app().weather_data)

    def _build_ui(self, data):
        current  = data["current"]
        location = data["location"]
        forecast = data["forecast"]["forecastday"]
        cond     = current["condition"]
        bg_col   = weather_color(cond["code"])

        root = FloatLayout()
        with root.canvas.before:
            Color(*bg_col)
            self._bg = Rectangle(size=Window.size, pos=(0, 0))
        root.bind(size=lambda w, s: setattr(self._bg, "size", s))

        scroll = ScrollView(
            size_hint=(1, 1), do_scroll_x=False,
        )
        pad = sw(0.05)
        inner = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            padding=[pad, sh(0.07), pad, pad],
            spacing=sw(0.035),
        )
        inner.bind(minimum_height=inner.setter("height"))

        # ── Header ───────────────────────────────────────────────────────
        inner.add_widget(self._spacer(sh(0.015)))
        inner.add_widget(self._label(
            f"{location['name']}, {location['country']}",
            fs(0.042), (0.85, 0.95, 1, 0.9)
        ))
        inner.add_widget(self._label(
            f"{current['temp_c']:.0f}\u00b0C",
            fs(0.20), (1, 1, 1, 1), bold=True
        ))
        inner.add_widget(self._label(cond["text"],        fs(0.052), (1, 1, 1, 0.85)))
        inner.add_widget(self._label(
            f"Feels like {current['feelslike_c']:.0f}\u00b0C", fs(0.038), (1, 1, 1, 0.70)
        ))
        inner.add_widget(self._spacer(sh(0.01)))

        # ── Current Conditions ───────────────────────────────────────────
        inner.add_widget(self._section_title("Current Conditions"))
        inner.add_widget(self._detail_card([
            ("Humidity",    f"{current['humidity']}%"),
            ("Wind",        f"{current['wind_kph']} km/h {current['wind_dir']}"),
            ("Visibility",  f"{current['vis_km']} km"),
            ("Pressure",    f"{current['pressure_mb']} mb"),
            ("Cloud Cover", f"{current['cloud']}%"),
            ("Precip",      f"{current['precip_mm']} mm"),
            ("UV Index",    str(current.get("uv", "N/A"))),
            ("Dew Point",   f"{current.get('dewpoint_c', 'N/A')}C"),
        ], bg_col))

        # ── Air Quality ──────────────────────────────────────────────────
        aqi = current.get("air_quality", {})
        if aqi:
            inner.add_widget(self._section_title("Air Quality"))
            inner.add_widget(self._detail_card([
                ("PM2.5", f"{aqi.get('pm2_5', 0):.1f} ug/m3"),
                ("PM10",  f"{aqi.get('pm10',  0):.1f} ug/m3"),
                ("CO",    f"{aqi.get('co',    0):.1f} ug/m3"),
                ("NO2",   f"{aqi.get('no2',   0):.1f} ug/m3"),
                ("O3",    f"{aqi.get('o3',    0):.1f} ug/m3"),
                ("SO2",   f"{aqi.get('so2',   0):.1f} ug/m3"),
            ], bg_col))

        # ── 3-Day Forecast ───────────────────────────────────────────────
        inner.add_widget(self._section_title("3-Day Forecast"))
        for day in forecast:
            inner.add_widget(self._forecast_row(day, bg_col))

        # ── Sun & Moon ───────────────────────────────────────────────────
        astro = forecast[0]["astro"]
        inner.add_widget(self._section_title("Sun & Moon"))
        inner.add_widget(self._detail_card([
            ("Sunrise",    astro["sunrise"]),
            ("Sunset",     astro["sunset"]),
            ("Moonrise",   astro["moonrise"]),
            ("Moonset",    astro["moonset"]),
            ("Moon Phase", astro["moon_phase"]),
        ], bg_col))

        # ── Footer ───────────────────────────────────────────────────────
        now = datetime.now().strftime("%d %b %Y  %H:%M")
        inner.add_widget(self._spacer(sh(0.01)))
        inner.add_widget(self._label(f"Last updated: {now}", fs(0.028), (1, 1, 1, 0.45)))
        inner.add_widget(self._spacer(sh(0.03)))

        # ── "Change District" button (inside scroll, at the bottom) ──────
        back_btn = Button(
            text="Change District",
            font_size=fs(0.036),
            color=(1, 1, 1, 1),
            background_color=(0.22, 0.51, 0.89, 1),
            background_normal="",
            background_down="",
            size_hint_y=None, height=sh(0.07),
        )
        back_btn.bind(on_release=self._go_back)
        inner.add_widget(back_btn)
        inner.add_widget(self._spacer(sh(0.04)))

        scroll.add_widget(inner)
        root.add_widget(scroll)
        self.add_widget(root)

    def _go_back(self, *args):
        self.manager.current = "picker"

    # ── Helpers ──────────────────────────────────────────────────────────────
    def _spacer(self, h):
        return BoxLayout(size_hint_y=None, height=h)

    def _label(self, text, font_size, color, bold=False):
        lbl = Label(
            text=text, font_size=font_size, color=color, bold=bold,
            size_hint_y=None, height=font_size * 1.7,
            halign="center", valign="middle",
        )
        lbl.bind(size=lambda w, s: setattr(w, "text_size", s))
        return lbl

    def _section_title(self, text):
        lbl = Label(
            text=text.upper(), font_size=fs(0.030),
            color=(1, 1, 1, 0.55), bold=True,
            size_hint_y=None, height=fs(0.030) * 2.0,
            halign="left", valign="middle",
        )
        lbl.bind(size=lambda w, s: setattr(w, "text_size", s))
        return lbl

    def _detail_card(self, items, bg_col):
        row_h = sh(0.048)
        pad   = sw(0.04)
        card  = BoxLayout(
            orientation="vertical", size_hint_y=None,
            padding=[pad, pad * 0.6, pad, pad * 0.6],
            spacing=sh(0.006),
        )
        r, g, b, _ = bg_col
        with card.canvas.before:
            Color(min(r + 0.08, 1), min(g + 0.08, 1), min(b + 0.08, 1), 0.55)
            card._rect = RoundedRectangle(size=card.size, pos=card.pos, radius=[dp(14)])
        card.bind(
            size=lambda w, s: setattr(w._rect, "size", s),
            pos=lambda w, p: setattr(w._rect, "pos", p),
        )
        fsize = fs(0.033)
        for label, value in items:
            row = BoxLayout(orientation="horizontal", size_hint_y=None, height=row_h)
            lbl = Label(text=label, font_size=fsize, color=(1, 1, 1, 0.70),
                        halign="left", valign="middle")
            lbl.bind(size=lambda w, s: setattr(w, "text_size", s))
            val = Label(text=value, font_size=fsize, color=(1, 1, 1, 0.95),
                        bold=True, halign="right", valign="middle")
            val.bind(size=lambda w, s: setattr(w, "text_size", s))
            row.add_widget(lbl)
            row.add_widget(val)
            card.add_widget(row)
        card.height = len(items) * row_h + len(items) * sh(0.006) + pad * 1.2
        return card

    def _forecast_row(self, day_data, bg_col):
        date_str = datetime.strptime(day_data["date"], "%Y-%m-%d").strftime("%A, %d %b")
        d        = day_data["day"]
        r, g, b, _ = bg_col
        row_h    = sh(0.13)
        pad      = sw(0.04)
        fsize    = fs(0.033)

        row = BoxLayout(
            orientation="horizontal", size_hint_y=None, height=row_h,
            padding=[pad, pad * 0.4, pad, pad * 0.4],
        )
        with row.canvas.before:
            Color(min(r + 0.05, 1), min(g + 0.05, 1), min(b + 0.12, 1), 0.45)
            row._rect = RoundedRectangle(size=row.size, pos=row.pos, radius=[dp(12)])
        row.bind(
            size=lambda w, s: setattr(w._rect, "size", s),
            pos=lambda w, p: setattr(w._rect, "pos", p),
        )

        left = BoxLayout(orientation="vertical", spacing=dp(2))
        dl = Label(text=date_str, font_size=fsize, color=(1, 1, 1, 0.90),
                   halign="left", valign="middle", bold=True,
                   size_hint_y=None, height=fsize * 1.6)
        dl.bind(size=lambda w, s: setattr(w, "text_size", s))
        cl = Label(text=d["condition"]["text"], font_size=fsize * 0.85,
                   color=(1, 1, 1, 0.60), halign="left", valign="middle",
                   size_hint_y=None, height=fsize * 1.4)
        cl.bind(size=lambda w, s: setattr(w, "text_size", s))
        left.add_widget(dl)
        left.add_widget(cl)

        right = Label(
            text=f"H:{d['maxtemp_c']:.0f}\u00b0C  L:{d['mintemp_c']:.0f}\u00b0C",
            font_size=fsize, color=(1, 1, 1, 0.90),
            halign="right", valign="middle", bold=True, size_hint_x=0.42,
        )
        right.bind(size=lambda w, s: setattr(w, "text_size", s))
        row.add_widget(left)
        row.add_widget(right)
        return row


# ═══════════════════════════════════════════════════════════════════════════════
# Cartoon Widget (shared by IntroScreen and FetchLoadingScreen)
# ═══════════════════════════════════════════════════════════════════════════════
class CartoonWidget(FloatLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(size=self._redraw, pos=self._redraw)

    def _redraw(self, *args):
        self.canvas.clear()
        W    = self.width
        cx   = self.center_x
        base = self.y + W * 0.04
        s    = W / 220.0

        def p(val):
            return val * s

        with self.canvas:
            Color(0.85, 0.90, 1.0, 0.95)
            Ellipse(pos=(cx - p(95), base + p(130)), size=(p(130), p(70)))
            Ellipse(pos=(cx - p(60), base + p(145)), size=(p(90),  p(55)))
            Ellipse(pos=(cx - p(75), base + p(120)), size=(p(80),  p(50)))
            Color(1.0, 1.0, 1.0, 1.0)
            Ellipse(pos=(cx + p(10), base + p(140)), size=(p(100), p(55)))
            Ellipse(pos=(cx + p(30), base + p(152)), size=(p(70),  p(45)))
            Ellipse(pos=(cx - p(5),  base + p(128)), size=(p(65),  p(42)))
            Color(0.25, 0.52, 0.96, 1)
            RoundedRectangle(pos=(cx - p(28), base + p(40)),  size=(p(56), p(80)),  radius=[p(12)])
            Color(0.95, 0.30, 0.30, 1)
            RoundedRectangle(pos=(cx - p(28), base + p(108)), size=(p(56), p(16)),  radius=[p(6)])
            RoundedRectangle(pos=(cx + p(6),  base + p(84)),  size=(p(14), p(32)),  radius=[p(5)])
            Color(0.25, 0.52, 0.96, 1)
            RoundedRectangle(pos=(cx - p(58), base + p(80)),  size=(p(32), p(14)),  radius=[p(7)])
            RoundedRectangle(pos=(cx - p(58), base + p(94)),  size=(p(14), p(36)),  radius=[p(7)])
            RoundedRectangle(pos=(cx + p(26), base + p(72)),  size=(p(32), p(14)),  radius=[p(7)])
            Color(0.95, 0.78, 0.55, 1)
            Ellipse(pos=(cx - p(64), base + p(126)), size=(p(22), p(22)))
            Ellipse(pos=(cx + p(44), base + p(68)),  size=(p(20), p(20)))
            Color(0.95, 0.78, 0.55, 1)
            RoundedRectangle(pos=(cx - p(12), base + p(120)), size=(p(24), p(20)),  radius=[p(8)])
            Color(0.95, 0.78, 0.55, 1)
            Ellipse(pos=(cx - p(32), base + p(132)), size=(p(64), p(62)))
            Color(0.18, 0.28, 0.55, 1)
            RoundedRectangle(pos=(cx - p(40), base + p(183)), size=(p(80), p(10)),  radius=[p(4)])
            RoundedRectangle(pos=(cx - p(26), base + p(193)), size=(p(52), p(42)),  radius=[p(8)])
            Color(0.95, 0.30, 0.30, 1)
            RoundedRectangle(pos=(cx - p(26), base + p(193)), size=(p(52), p(8)),   radius=[p(3)])
            Color(1, 1, 1, 1)
            Ellipse(pos=(cx - p(22), base + p(156)), size=(p(18), p(18)))
            Ellipse(pos=(cx + p(4),  base + p(156)), size=(p(18), p(18)))
            Color(0.10, 0.10, 0.30, 1)
            Ellipse(pos=(cx - p(17), base + p(161)), size=(p(10), p(10)))
            Ellipse(pos=(cx + p(8),  base + p(161)), size=(p(10), p(10)))
            Color(0, 0, 0, 1)
            Ellipse(pos=(cx - p(15), base + p(165)), size=(p(6), p(6)))
            Ellipse(pos=(cx + p(10), base + p(165)), size=(p(6), p(6)))
            Color(1, 1, 1, 0.9)
            Ellipse(pos=(cx - p(13), base + p(168)), size=(p(4), p(4)))
            Ellipse(pos=(cx + p(13), base + p(168)), size=(p(4), p(4)))
            Color(0.45, 0.28, 0.10, 1)
            Line(points=[cx - p(22), base + p(177), cx - p(12), base + p(181)], width=max(1, p(2.5)))
            Line(points=[cx + p(4),  base + p(181), cx + p(22), base + p(177)], width=max(1, p(2.5)))
            Color(0.60, 0.25, 0.15, 1)
            Ellipse(pos=(cx - p(8), base + p(146)), size=(p(16), p(10)))
            Color(0.95, 0.55, 0.55, 1)
            Ellipse(pos=(cx - p(6), base + p(147)), size=(p(12), p(7)))
            Color(0.18, 0.25, 0.45, 1)
            RoundedRectangle(pos=(cx - p(26), base + p(10)), size=(p(20), p(34)), radius=[p(6)])
            RoundedRectangle(pos=(cx + p(6),  base + p(10)), size=(p(20), p(34)), radius=[p(6)])
            Color(0.20, 0.16, 0.12, 1)
            RoundedRectangle(pos=(cx - p(30), base),        size=(p(26), p(14)), radius=[p(5)])
            RoundedRectangle(pos=(cx + p(4),  base),        size=(p(26), p(14)), radius=[p(5)])


# ═══════════════════════════════════════════════════════════════════════════════
# App
# ═══════════════════════════════════════════════════════════════════════════════
class WeatherPeekApp(App):
    weather_data      = None
    selected_district = "Kathmandu"

    def build(self):
        self.title = "WeatherPeek Nepal"
        sm = ScreenManager(transition=FadeTransition(duration=0.5))
        sm.add_widget(IntroScreen(name="intro"))
        sm.add_widget(PickerScreen(name="picker"))
        sm.add_widget(FetchLoadingScreen(name="fetch_loading"))
        sm.add_widget(WeatherScreen(name="weather"))
        sm.current = "intro"
        return sm


if __name__ == "__main__":
    WeatherPeekApp().run()