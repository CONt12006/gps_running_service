from typing import Callable

from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button


class BottomNavigation(BoxLayout):
    """Класс создаёт нижнее меню из кнопок"""
    def __init__(
        self,
        on_tab_selected: Callable[[str], None],
        **kwargs
    ):
        super().__init__(**kwargs)

        self.orientation = "horizontal"
        self.padding = [0, 0, 0, 0]        
        self.spacing = 0

        self.on_tab_selected = on_tab_selected

        self.add_widget(self._create_nav_button("Прогресс", "progress"))
        self.add_widget(self._create_nav_button("Начать", "start"))
        self.add_widget(self._create_nav_button("Настройки", "settings"))

    def _create_nav_button(self, text: str, screen_name: str) -> Button:
        button = Button(
            text=text,
            font_size=dp(14),
            background_normal="",
            background_color=(1, 1, 1, 1),
            color=(0.5, 0.5, 0.5, 1),
        )

        button.bind(
            on_press=lambda button: self.on_tab_selected(screen_name)
        )

        return button