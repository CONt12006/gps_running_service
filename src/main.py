from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, NoTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.gridlayout import GridLayout


class AlarmListScreen(Screen):
    """Главный экран — список будильников."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        
        # Заголовок
        header = Label(
            text="Мои будильники",
            font_size=32,
            bold=True,
            size_hint=(1, 0.15)
        )
        layout.add_widget(header)
        
        # Список будильников
        self.alarms_layout = BoxLayout(orientation='vertical', spacing=5, size_hint=(1, 0.6))
        self.alarms_layout.add_widget(Label(
            text="Пока нет будильников",
            font_size=20,
            color=(0.5, 0.5, 0.5, 1)
        ))
        layout.add_widget(self.alarms_layout)
        
        # Кнопка "Добавить будильник"
        add_btn = Button(
            text="+ Добавить будильник",
            font_size=25,
            size_hint=(1, 0.15),
            background_color=(0.2, 0.6, 1, 1),
            background_normal=''
        )
        add_btn.bind(on_press=self.go_to_add_screen)
        layout.add_widget(add_btn)
        
        # Кнопка "Тест звонка"
        test_btn = Button(
            text="🔔 Тест звонка будильника",
            font_size=20,
            size_hint=(1, 0.1),
            background_color=(1, 0.5, 0, 1),
            background_normal=''
        )
        test_btn.bind(on_press=self.trigger_alarm)
        layout.add_widget(test_btn)
        
        self.add_widget(layout)
    
    def go_to_add_screen(self, instance):
        """Переход на экран добавления будильника."""
        # Мгновенный переход без анимации
        self.manager.transition = NoTransition()
        self.manager.current = 'add_alarm'
    
    def trigger_alarm(self, instance):
        """Имитация срабатывания будильника."""
        # Мгновенный переход без анимации
        self.manager.transition = NoTransition()
        self.manager.current = 'alarm_ringing'
    
    def add_alarm_to_list(self, time_str, label_text):
        """Добавляет новый будильник в список."""
        # Если это первый будильник — удаляем заглушку
        if len(self.alarms_layout.children) == 1:
            self.alarms_layout.clear_widgets()
        
        # Создаем строку будильника
        alarm_row = BoxLayout(size_hint=(1, None), height=60, spacing=10)
        
        time_label = Label(
            text=time_str,
            font_size=28,
            bold=True,
            size_hint=(0.4, 1)
        )
        
        name_label = Label(
            text=label_text,
            font_size=20,
            size_hint=(0.6, 1)
        )
        
        alarm_row.add_widget(time_label)
        alarm_row.add_widget(name_label)
        
        self.alarms_layout.add_widget(alarm_row)


class AddAlarmScreen(Screen):
    """Экран создания нового будильника."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        
        # Заголовок
        header = Label(
            text="Новый будильник",
            font_size=32,
            bold=True,
            size_hint=(1, 0.15)
        )
        layout.add_widget(header)
        
        # Поле ввода времени
        layout.add_widget(Label(text="Время (ЧЧ:ММ):", font_size=20, size_hint=(1, 0.1)))
        self.time_input = TextInput(
            hint_text="07:30",
            multiline=False,
            font_size=30,
            size_hint=(1, 0.15)
        )
        layout.add_widget(self.time_input)
        
        # Поле ввода названия
        layout.add_widget(Label(text="Название:", font_size=20, size_hint=(1, 0.1)))
        self.name_input = TextInput(
            hint_text="На работу",
            multiline=False,
            font_size=25,
            size_hint=(1, 0.15)
        )
        layout.add_widget(self.name_input)
        
        # Дни недели
        layout.add_widget(Label(text="Дни недели:", font_size=20, size_hint=(1, 0.1)))
        days_layout = GridLayout(cols=7, spacing=5, size_hint=(1, 0.2))
        self.day_buttons = []
        for day in ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']:
            btn = Button(text=day, font_size=18)
            btn.bind(on_press=self.toggle_day)
            self.day_buttons.append(btn)
            days_layout.add_widget(btn)
        layout.add_widget(days_layout)
        
        # Кнопки управления
        buttons_layout = BoxLayout(orientation='horizontal', spacing=10, size_hint=(1, 0.15))
        
        cancel_btn = Button(
            text="Отмена",
            font_size=22,
            background_color=(0.5, 0.5, 0.5, 1),
            background_normal=''
        )
        cancel_btn.bind(on_press=self.go_back)
        
        save_btn = Button(
            text="Сохранить",
            font_size=22,
            background_color=(0.2, 0.8, 0.2, 1),
            background_normal=''
        )
        save_btn.bind(on_press=self.save_alarm)
        
        buttons_layout.add_widget(cancel_btn)
        buttons_layout.add_widget(save_btn)
        layout.add_widget(buttons_layout)
        
        self.add_widget(layout)
    
    def toggle_day(self, instance):
        """Переключение дня недели (вкл/выкл)."""
        if instance.background_color == [0.2, 0.6, 1, 1]:
            instance.background_color = (0.3, 0.3, 0.3, 1)
        else:
            instance.background_color = (0.2, 0.6, 1, 1)
    
    def go_back(self, instance):
        """Возврат назад без сохранения."""
        # Мгновенный переход без анимации
        self.manager.transition = NoTransition()
        self.manager.current = 'alarm_list'
        # Очищаем поля
        self.time_input.text = ""
        self.name_input.text = ""
    
    def save_alarm(self, instance):
        """Сохраняем будильник и возвращаемся."""
        time_str = self.time_input.text.strip() or "07:30"
        name_str = self.name_input.text.strip() or "Будильник"
        
        # Получаем список экранов и передаем данные
        alarm_list_screen = self.manager.get_screen('alarm_list')
        alarm_list_screen.add_alarm_to_list(time_str, name_str)
        
        # Возвращаемся назад
        # Мгновенный переход без анимации
        self.manager.transition = NoTransition()
        self.manager.current = 'alarm_list'
        
        # Очищаем поля
        self.time_input.text = ""
        self.name_input.text = ""


class AlarmRingingScreen(Screen):
    """Экран срабатывания будильника."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        
        # Большой заголовок
        layout.add_widget(Label(
            text="🔔",
            font_size=100,
            size_hint=(1, 0.3)
        ))
        
        layout.add_widget(Label(
            text="Подъем!",
            font_size=50,
            bold=True,
            size_hint=(1, 0.2)
        ))
        
        layout.add_widget(Label(
            text="07:30 — На работу",
            font_size=25,
            color=(0.7, 0.7, 0.7, 1),
            size_hint=(1, 0.15)
        ))
        
        # Кнопка "Отложить"
        snooze_btn = Button(
            text="Отложить (5 мин)",
            font_size=25,
            size_hint=(1, 0.15),
            background_color=(1, 0.7, 0, 1),
            background_normal=''
        )
        snooze_btn.bind(on_press=self.snooze)
        layout.add_widget(snooze_btn)
        
        # Кнопка "Отключить"
        dismiss_btn = Button(
            text="Отключить",
            font_size=25,
            size_hint=(1, 0.15),
            background_color=(0.8, 0.2, 0.2, 1),
            background_normal=''
        )
        dismiss_btn.bind(on_press=self.dismiss)
        layout.add_widget(dismiss_btn)
        
        self.add_widget(layout)
    
    def snooze(self, instance):
        """Отложить будильник."""
        print("Будильник отложен на 5 минут")
        # Мгновенный переход без анимации
        self.manager.transition = NoTransition()
        self.manager.current = 'alarm_list'
    
    def dismiss(self, instance):
        """Отключить будильник."""
        print("Будильник отключен")
        # Мгновенный переход без анимации
        self.manager.transition = NoTransition()
        self.manager.current = 'alarm_list'


class AlarmApp(App):
    def build(self):
        # Создаем менеджер экранов
        sm = ScreenManager()
        
        # Устанавливаем NoTransition как переход по умолчанию
        sm.transition = NoTransition()
        
        # Добавляем экраны с именами
        sm.add_widget(AlarmListScreen(name='alarm_list'))
        sm.add_widget(AddAlarmScreen(name='add_alarm'))
        sm.add_widget(AlarmRingingScreen(name='alarm_ringing'))
        
        return sm


if __name__ == '__main__':
    AlarmApp().run()





"""
from kivy.app import App
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button

from kivy_garden.mapview import MapView, MapMarker, MapSource
from plyer import gps


Window.fullscreen = True


class MyApp(App):
    def build(self):
        self.follow_user = True
        self.last_latitude = None
        self.last_longitude = None

        main_layout = BoxLayout(
            orientation="vertical"
        )

        source = MapSource(
            url="https://tile.openstreetmap.org/{z}/{x}/{y}.png",
            cache_key="osm",
            min_zoom=0,
            max_zoom=19,
            attribution="© OpenStreetMap contributors"
        )

        self.map_view = MapView(
            map_source=source,
            lat=55.7558,
            lon=37.6176,
            zoom=15
        )

        self.user_marker = MapMarker(
            lat=55.7558,
            lon=37.6176
        )

        self.map_view.add_marker(self.user_marker)

        bottom_menu = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=70
        )

        progress_button = Button(text="Прогресс")
        self.start_button = Button(text="Не следить")
        settings_button = Button(text="Настройки")

        self.start_button.bind(
            on_release=self.toggle_tracking
        )

        bottom_menu.add_widget(progress_button)
        bottom_menu.add_widget(self.start_button)
        bottom_menu.add_widget(settings_button)

        main_layout.add_widget(self.map_view)
        main_layout.add_widget(bottom_menu)

        return main_layout

    def on_start(self):
        try:
            gps.configure(
                on_location=self.on_location,
                on_status=self.on_gps_status
            )

            gps.start(
                minTime=1000,
                minDistance=1
            )

        except NotImplementedError:
            print("GPS не поддерживается на этой платформе")

    def on_location(self, **kwargs):
        latitude = kwargs.get("lat")
        longitude = kwargs.get("lon")

        if latitude is None or longitude is None:
            return

        Clock.schedule_once(
            lambda dt: self.update_position(
                latitude,
                longitude
            )
        )

    def update_position(self, latitude, longitude):
        self.last_latitude = latitude
        self.last_longitude = longitude

        self.user_marker.lat = latitude
        self.user_marker.lon = longitude

        if self.follow_user:
            self.map_view.center_on(
                latitude,
                longitude
            )

    def toggle_tracking(self, button):
        self.follow_user = not self.follow_user

        if self.follow_user:
            button.text = "Не следить"

            if (
                self.last_latitude is not None
                and self.last_longitude is not None
            ):
                self.map_view.center_on(
                    self.last_latitude,
                    self.last_longitude
                )
        else:
            button.text = "Следить"

    def on_gps_status(self, status_type, status_message):
        print(
            "GPS:",
            status_type,
            status_message
        )

    def on_stop(self):
        try:
            gps.stop()
        except NotImplementedError:
            pass


MyApp().run()
"""