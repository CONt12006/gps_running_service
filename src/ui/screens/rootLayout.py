from kivy.metrics import dp
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.screenmanager import NoTransition, ScreenManager

from src.db.run_repository import RunRepository
from src.ui.screens.StartScreen import StartScreen
from src.ui.screens.ProgressScreen import ProgressScreen
from src.ui.screens.RunDetailScreen import RunDetailScreen
from src.ui.screens.SettingsScreen import SettingsScreen
from src.ui.widgets.bottom_navigation import BottomNavigation


class RootLayout(FloatLayout):
    def __init__(
        self,
        run_repository: RunRepository,
        **kwargs,
    ):
        super().__init__(**kwargs)

        self._run_repository = run_repository

        self.screen_manager = ScreenManager(
            transition=NoTransition(),
            size_hint=(1, 1),
            pos_hint={
                "x": 0,
                "y": 0,
            },
        )

        self.screen_manager.add_widget(
            StartScreen(
                name="main",
                repository=self._run_repository,
            )
        )

        self.screen_manager.add_widget(
            ProgressScreen(
                name="progress",
                repository=self._run_repository,
            )
        )

        self.screen_manager.add_widget(
            RunDetailScreen(
                name="run_detail",
                repository=self._run_repository,
            )
        )

        self.screen_manager.add_widget(
            SettingsScreen(
                name="settings",
                repository=self._run_repository,
            )
        )

        self.screen_manager.current = "main"

        self.bottom_navigation = BottomNavigation(
            on_tab_selected=self.switch_screen,
            size_hint=(1, None),
            height=dp(90),
            pos_hint={
                "x": 0,
                "y": 0,
            },
        )

        self.add_widget(self.screen_manager)
        self.add_widget(self.bottom_navigation)

    def switch_screen(
        self,
        screen_name: str,
    ) -> None:
        if not self.screen_manager.has_screen(screen_name):
            print(
                f"Экран с именем {screen_name!r} не найден"
            )
            return

        self.screen_manager.current = screen_name