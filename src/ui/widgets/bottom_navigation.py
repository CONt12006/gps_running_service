from typing import Callable

from kivy.graphics import Color, Rectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout

from kivymd.uix.label import MDIcon, MDLabel
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.anchorlayout import AnchorLayout


ACTIVE_COLOR = (0.0, 0.82, 0.32, 1)
INACTIVE_COLOR = (0.55, 0.55, 0.55, 1)


class NavigationTab(ButtonBehavior, BoxLayout):
    def __init__(
        self,
        icon: str,
        text: str,
        screen_name: str,
        on_tab_selected: Callable[[str], None],
        **kwargs,
    ):
        super().__init__(**kwargs)

        self.screen_name = screen_name
        self.on_tab_selected = on_tab_selected

        # Иконка сверху, надпись снизу
        self.orientation = "vertical"
        self.spacing = 0
        self.padding = [0, dp(7), 0, dp(5)]

        # Отдельная область для центрирования иконки
        icon_container = AnchorLayout(
            anchor_x="center",
            anchor_y="center",
            size_hint=(1, 0.62),
        )

        self.icon_widget = MDIcon(
            icon=icon,
            theme_text_color="Custom",
            text_color=INACTIVE_COLOR,
            font_size=dp(26),

            # Сам значок имеет небольшой фиксированный размер,
            # а AnchorLayout ставит его по центру
            size_hint=(None, None),
            size=(dp(36), dp(36)),
            halign="center",
            valign="middle",
        )

        self.icon_widget.text_size = self.icon_widget.size

        icon_container.add_widget(self.icon_widget)

        # Отдельная область для центрирования подписи
        label_container = AnchorLayout(
            anchor_x="center",
            anchor_y="center",
            size_hint=(1, 0.38),
        )

        self.label_widget = MDLabel(
            text=text,
            theme_text_color="Custom",
            text_color=INACTIVE_COLOR,
            font_size=dp(12),

            size_hint=(1, 1),
            halign="center",
            valign="middle",
        )

        self.label_widget.bind(
            size=self._update_label_text_size,
        )

        label_container.add_widget(self.label_widget)

        self.add_widget(icon_container)
        self.add_widget(label_container)

    def _update_label_text_size(
        self,
        label: MDLabel,
        size: tuple[float, float],
    ) -> None:
        label.text_size = size

    def on_press(self) -> None:
        self.on_tab_selected(self.screen_name)

    def set_active(self, active: bool) -> None:
        color = ACTIVE_COLOR if active else INACTIVE_COLOR

        self.icon_widget.text_color = color
        self.label_widget.text_color = color


class BottomNavigation(BoxLayout):
    def __init__(
        self,
        on_tab_selected: Callable[[str], None],
        **kwargs,
    ):
        super().__init__(**kwargs)

        self.on_tab_selected = on_tab_selected

        self.orientation = "horizontal"
        self.padding = 0
        self.spacing = 0

        self.size_hint_y = None
        self.height = dp(82)

        # Белый непрозрачный фон всей нижней панели
        with self.canvas.before:
            self.background_color = Color(1, 1, 1, 1)

            self.background_rectangle = Rectangle(
                pos=self.pos,
                size=self.size,
            )

        self.bind(
            pos=self._update_background,
            size=self._update_background,
        )

        self.tabs: dict[str, NavigationTab] = {}

        self._add_tab(
            icon="chart-bar",
            text="Прогресс",
            screen_name="progress",
        )

        self._add_tab(
            icon="home-outline",
            text="Главная",
            screen_name="main",
        )

        self._add_tab(
            icon="cog-outline",
            text="Настройки",
            screen_name="settings",
        )

        self.set_active_tab("start")

    def _add_tab(
        self,
        icon: str,
        text: str,
        screen_name: str,
    ) -> None:
        tab = NavigationTab(
            icon=icon,
            text=text,
            screen_name=screen_name,
            on_tab_selected=self._handle_tab_selected,
        )

        self.tabs[screen_name] = tab
        self.add_widget(tab)

    def _handle_tab_selected(self, screen_name: str) -> None:
        self.set_active_tab(screen_name)
        self.on_tab_selected(screen_name)

    def set_active_tab(self, screen_name: str) -> None:
        for name, tab in self.tabs.items():
            tab.set_active(name == screen_name)

    def _update_background(self, *args) -> None:
        self.background_rectangle.pos = self.pos
        self.background_rectangle.size = self.size