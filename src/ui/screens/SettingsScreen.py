from __future__ import annotations

from collections.abc import Callable

from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.metrics import dp, sp
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.modalview import ModalView
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget

from src.db.run_repository import RunRepository


APP_VERSION = "0.1.0"

BACKGROUND_COLOR = (0.96, 0.96, 0.98, 1.0)
CARD_COLOR = (1.0, 1.0, 1.0, 1.0)
PRIMARY_TEXT_COLOR = (0.06, 0.06, 0.08, 1.0)
SECONDARY_TEXT_COLOR = (0.50, 0.50, 0.54, 1.0)
DIVIDER_COLOR = (0.89, 0.89, 0.92, 1.0)
DANGER_COLOR = (0.92, 0.20, 0.22, 1.0)


class RoundedCard(BoxLayout):
    """Белая карточка со скруглёнными углами."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        with self.canvas.before:
            self._background_color = Color(*CARD_COLOR)

            self._background = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[dp(18)],
            )

        self.bind(
            pos=self._update_background,
            size=self._update_background,
        )

    def _update_background(self, *_args) -> None:
        self._background.pos = self.pos
        self._background.size = self.size


class Divider(Widget):
    """Разделительная линия между строками карточки."""

    def __init__(self, **kwargs):
        super().__init__(
            size_hint_y=None,
            height=dp(1),
            **kwargs,
        )

        with self.canvas:
            Color(*DIVIDER_COLOR)

            self._line = Rectangle(
                pos=self.pos,
                size=self.size,
            )

        self.bind(
            pos=self._update_line,
            size=self._update_line,
        )

    def _update_line(self, *_args) -> None:
        self._line.pos = self.pos
        self._line.size = self.size


class SettingRow(ButtonBehavior, BoxLayout):
    """Одна строка экрана настроек."""

    def __init__(
        self,
        icon: str,
        title: str,
        value: str = "",
        danger: bool = False,
        on_selected: Callable[[], None] | None = None,
        **kwargs,
    ):
        super().__init__(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(64),
            spacing=dp(10),
            padding=(
                dp(14),
                dp(6),
                dp(14),
                dp(6),
            ),
            **kwargs,
        )

        self._on_selected = on_selected
        self._danger = danger

        row_color = (
            DANGER_COLOR
            if danger
            else PRIMARY_TEXT_COLOR
        )

        self._icon_label = Label(
            text=icon,
            font_size=sp(21),
            color=row_color,
            size_hint=(None, 1),
            width=dp(38),
            halign="center",
            valign="middle",
        )

        self._icon_label.bind(
            size=self._set_text_size,
        )

        self._title_label = Label(
            text=title,
            font_size=sp(16),
            color=row_color,
            halign="left",
            valign="middle",
        )

        self._title_label.bind(
            size=self._set_text_size,
        )

        self._value_label = Label(
            text=value,
            font_size=sp(15),
            color=SECONDARY_TEXT_COLOR,
            size_hint=(None, 1),
            width=dp(100),
            halign="right",
            valign="middle",
        )

        self._value_label.bind(
            size=self._set_text_size,
        )

        self.add_widget(self._icon_label)
        self.add_widget(self._title_label)
        self.add_widget(self._value_label)

    @property
    def value(self) -> str:
        return self._value_label.text

    @value.setter
    def value(self, new_value: str) -> None:
        self._value_label.text = new_value

    def on_release(self) -> None:
        if self._on_selected is not None:
            self._on_selected()

    @staticmethod
    def _set_text_size(
        label: Label,
        size: tuple[float, float],
    ) -> None:
        label.text_size = size


class SectionTitle(Label):
    """Заголовок раздела."""

    def __init__(self, **kwargs):
        super().__init__(
            size_hint_y=None,
            height=dp(42),
            font_size=sp(13),
            bold=True,
            color=SECONDARY_TEXT_COLOR,
            halign="left",
            valign="bottom",
            **kwargs,
        )

        self.bind(
            size=self._set_text_size,
        )

    @staticmethod
    def _set_text_size(
        label: Label,
        size: tuple[float, float],
    ) -> None:
        label.text_size = size


class SettingsScreen(Screen):
    def __init__(
        self,
        repository: RunRepository,
        **kwargs,
    ):
        super().__init__(**kwargs)

        self._repository = repository

        self._build_ui()

    def _build_ui(self) -> None:
        self._root = BoxLayout(
            orientation="vertical",
            padding=(
                dp(18),
                dp(14),
                dp(18),
                dp(90),
            ),
            spacing=dp(8),
        )

        with self._root.canvas.before:
            self._background_color = Color(
                *BACKGROUND_COLOR
            )

            self._background = Rectangle(
                pos=self._root.pos,
                size=self._root.size,
            )

        self._root.bind(
            pos=self._update_background,
            size=self._update_background,
        )

        title = Label(
            text="[b]Настройки[/b]",
            markup=True,
            font_size=sp(26),
            color=PRIMARY_TEXT_COLOR,
            size_hint_y=None,
            height=dp(58),
            halign="left",
            valign="middle",
        )

        title.bind(
            size=self._set_text_size,
        )

        self._root.add_widget(title)

        scroll = ScrollView(
            do_scroll_x=False,
            bar_width=dp(3),
        )

        content = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            spacing=dp(8),
            padding=(0, 0, 0, dp(24)),
        )

        content.bind(
            minimum_height=content.setter("height"),
        )

        # -------------------------
        # Данные
        # -------------------------

        content.add_widget(
            SectionTitle(
                text="ДАННЫЕ",
            )
        )

        data_card = RoundedCard(
            orientation="vertical",
            size_hint_y=None,
            height=dp(129),
        )

        self._runs_count_row = SettingRow(
            icon="🏃",
            title="Сохранено тренировок",
            value="0",
        )

        delete_row = SettingRow(
            icon="🗑",
            title="Очистить историю",
            danger=True,
            on_selected=self._show_delete_confirmation,
        )

        data_card.add_widget(
            self._runs_count_row
        )

        data_card.add_widget(
            Divider(
                size_hint_x=None,
                width=dp(290),
                pos_hint={"right": 0.97},
            )
        )

        data_card.add_widget(delete_row)

        content.add_widget(data_card)

        # -------------------------
        # О приложении
        # -------------------------

        content.add_widget(
            SectionTitle(
                text="О ПРИЛОЖЕНИИ",
            )
        )

        application_card = RoundedCard(
            orientation="vertical",
            size_hint_y=None,
            height=dp(64),
        )

        version_row = SettingRow(
            icon="ℹ",
            title="Версия",
            value=APP_VERSION,
        )

        application_card.add_widget(
            version_row
        )

        content.add_widget(application_card)

        scroll.add_widget(content)

        self._root.add_widget(scroll)
        self.add_widget(self._root)

    def on_pre_enter(self, *_args) -> None:
        """
        Каждый раз при открытии экрана заново
        считаем количество тренировок.
        """

        self.refresh_runs_count()

    def refresh_runs_count(self) -> None:
        try:
            count = self._repository.count_runs()

        except Exception as error:
            print(
                "Ошибка подсчёта тренировок:",
                error,
            )

            count = 0

        self._runs_count_row.value = str(count)

    def _show_delete_confirmation(self) -> None:
        modal = ModalView(
            size_hint=(0.88, None),
            height=dp(260),
            auto_dismiss=False,
            background_color=(0, 0, 0, 0.45),
        )

        card = RoundedCard(
            orientation="vertical",
            padding=dp(20),
            spacing=dp(12),
        )

        title = Label(
            text="[b]Удалить все тренировки?[/b]",
            markup=True,
            font_size=sp(20),
            color=PRIMARY_TEXT_COLOR,
            size_hint_y=None,
            height=dp(40),
        )

        message = Label(
            text=(
                "Все тренировки, маршруты и GPS-точки "
                "будут удалены.\n"
                "Это действие нельзя отменить."
            ),
            font_size=sp(14),
            color=SECONDARY_TEXT_COLOR,
            halign="center",
            valign="middle",
        )

        message.bind(
            size=self._set_text_size,
        )

        buttons = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(50),
            spacing=dp(12),
        )

        cancel_button = Button(
            text="Отмена",
            font_size=sp(15),
            color=PRIMARY_TEXT_COLOR,
            background_normal="",
            background_down="",
            background_color=(
                0.90,
                0.90,
                0.93,
                1.0,
            ),
        )

        delete_button = Button(
            text="Удалить",
            font_size=sp(15),
            color=(1, 1, 1, 1),
            background_normal="",
            background_down="",
            background_color=DANGER_COLOR,
        )

        cancel_button.bind(
            on_release=lambda *_: modal.dismiss()
        )

        delete_button.bind(
            on_release=lambda *_: self._delete_all_runs(
                modal
            )
        )

        buttons.add_widget(cancel_button)
        buttons.add_widget(delete_button)

        card.add_widget(title)
        card.add_widget(message)
        card.add_widget(buttons)

        modal.add_widget(card)
        modal.open()

    def _delete_all_runs(
        self,
        modal: ModalView,
    ) -> None:
        try:
            self._repository.delete_all_runs()

        except Exception as error:
            print(
                "Ошибка удаления тренировок:",
                error,
            )

            return

        self.refresh_runs_count()
        modal.dismiss()

    def _update_background(
        self,
        *_args,
    ) -> None:
        self._background.pos = self._root.pos
        self._background.size = self._root.size

    @staticmethod
    def _set_text_size(
        label: Label,
        size: tuple[float, float],
    ) -> None:
        label.text_size = size