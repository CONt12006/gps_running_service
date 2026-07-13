from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.screenmanager import ScreenManager, NoTransition

from .StartScreen import StartScreen

from ..widgets.bottom_navigation import BottomNavigation

class RootLayout(FloatLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.screen_manager = ScreenManager(
            transition=NoTransition(),
            size_hint=(1, 1),
            pos_hint={"x": 0, "y": 0},
        )

        self.screen_manager.add_widget(StartScreen(name = "start"))

        self.screen_manager.current = "start"

        self.bottom_navigation = BottomNavigation(
            on_tab_selected=self.switch_screen,
            size_hint=(1, None),
            height=90,
            pos_hint={"x": 0, "y": 0},
        )

        self.add_widget(self.screen_manager)
        self.add_widget(self.bottom_navigation)

    def switch_screen(self, screen_name: str) -> None:
        self.screen_manager.current = screen_name