from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Iterable

from kivy.clock import Clock
from kivy.graphics import Color, Line, RoundedRectangle
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget

from src.db.models import Runs
from src.db.run_repository import RunRepository
from src.ui.screens.RunDetailScreen import RunDetailScreen


MONTH_NAMES = {
    1: "янв.",
    2: "февр.",
    3: "март",
    4: "апр.",
    5: "май",
    6: "июнь",
    7: "июль",
    8: "авг.",
    9: "сент.",
    10: "окт.",
    11: "нояб.",
    12: "дек.",
}


def format_duration(seconds: int) -> str:
    """Преобразовать секунды в формат ЧЧ:ММ:СС."""

    seconds = max(0, int(seconds))

    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    remaining_seconds = seconds % 60

    return (
        f"{hours:02d}:"
        f"{minutes:02d}:"
        f"{remaining_seconds:02d}"
    )


def format_distance(distance_meters: float) -> str:
    """Преобразовать метры в километры."""

    distance_km = max(0.0, distance_meters) / 1000

    return f"{distance_km:.2f}".replace(".", ",")


class RoundedPanel(BoxLayout):
    """BoxLayout с белым скруглённым фоном."""

    def __init__(
        self,
        background_color=(1, 1, 1, 1),
        radius: float = 18,
        **kwargs,
    ):
        super().__init__(**kwargs)

        self._background_color = background_color
        self._radius = dp(radius)

        with self.canvas.before:
            self._color_instruction = Color(
                *self._background_color
            )

            self._background = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[self._radius],
            )

        self.bind(
            pos=self._update_background,
            size=self._update_background,
        )

    def _update_background(self, *_args) -> None:
        self._background.pos = self.pos
        self._background.size = self.size


class PeriodButton(Button):
    """Кнопка выбора периода: недели или месяцы."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.background_normal = ""
        self.background_down = ""
        self.font_size = sp(16)
        self.color = (0.08, 0.08, 0.1, 1)
        self.size_hint_y = None
        self.height = dp(46)

        self.set_selected(False)

    def set_selected(self, selected: bool) -> None:
        if selected:
            self.background_color = (
                1,
                1,
                1,
                1,
            )
            self.bold = True
        else:
            self.background_color = (
                0.90,
                0.90,
                0.93,
                1,
            )
            self.bold = False


class MonthlyChart(Widget):
    """
    Простой график количества пробежек по месяцам.

    values:
        [
            ("дек.", 0),
            ("янв.", 2),
            ...
        ]
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.values: list[tuple[str, int]] = []

        self.bind(
            pos=self._schedule_redraw,
            size=self._schedule_redraw,
        )

    def set_values(
        self,
        values: list[tuple[str, int]],
    ) -> None:
        self.values = values
        self._schedule_redraw()

    def _schedule_redraw(self, *_args) -> None:
        Clock.unschedule(self._redraw)
        Clock.schedule_once(self._redraw, 0)

    def _redraw(self, *_args) -> None:
        self.canvas.clear()
        self.clear_widgets()

        if not self.values:
            return

        left_padding = dp(12)
        right_padding = dp(12)
        top_padding = dp(35)
        bottom_padding = dp(52)

        chart_width = (
            self.width
            - left_padding
            - right_padding
        )

        chart_height = (
            self.height
            - top_padding
            - bottom_padding
        )

        if chart_width <= 0 or chart_height <= 0:
            return

        values_count = len(self.values)
        cell_width = chart_width / values_count
        bar_width = min(dp(54), cell_width * 0.62)

        maximum_value = max(
            (value for _, value in self.values),
            default=0,
        )

        maximum_value = max(maximum_value, 1)

        for index, (month_name, value) in enumerate(
            self.values
        ):
            center_x = (
                self.x
                + left_padding
                + cell_width * index
                + cell_width / 2
            )

            bar_height = (
                chart_height
                * value
                / maximum_value
            )

            if value > 0:
                bar_height = max(bar_height, dp(8))

            bar_x = center_x - bar_width / 2
            bar_y = self.y + bottom_padding

            with self.canvas:
                Color(
                    0.05,
                    0.78,
                    0.37,
                    1,
                )

                RoundedRectangle(
                    pos=(bar_x, bar_y),
                    size=(bar_width, bar_height),
                    radius=[dp(12)],
                )

            value_label = Label(
                text=str(value),
                font_size=sp(13),
                color=(0.05, 0.78, 0.37, 1),
                size_hint=(None, None),
                size=(cell_width, dp(24)),
                pos=(
                    center_x - cell_width / 2,
                    bar_y + max(bar_height, dp(5)) + dp(5),
                ),
                halign="center",
                valign="middle",
            )

            value_label.text_size = value_label.size
            self.add_widget(value_label)

            month_label = Label(
                text=month_name,
                font_size=sp(13),
                color=(0.10, 0.10, 0.12, 1),
                size_hint=(None, None),
                size=(cell_width, dp(35)),
                pos=(
                    center_x - cell_width / 2,
                    self.y + dp(8),
                ),
                halign="center",
                valign="middle",
            )

            month_label.text_size = month_label.size
            self.add_widget(month_label)


class RunItem(RoundedPanel):
    """Одна строка тренировки в истории."""

    def __init__(
        self,
        run: Runs,
        on_press=None,
        **kwargs,
    ):
        super().__init__(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(118),
            padding=(dp(14), dp(12)),
            spacing=dp(12),
            radius=16,
            **kwargs,
        )

        self.run = run
        self._on_press_callback = on_press

        icon_box = BoxLayout(
            size_hint=(None, 1),
            width=dp(56),
            padding=(0, dp(12)),
        )

        icon = Label(
            text="🏃",
            font_size=sp(28),
            color=(0.05, 0.78, 0.37, 1),
        )

        icon_box.add_widget(icon)
        self.add_widget(icon_box)

        information = BoxLayout(
            orientation="vertical",
            spacing=dp(3),
        )

        distance_label = Label(
            text=(
                f"[b]{format_distance(run.distance)} км[/b]"
            ),
            markup=True,
            font_size=sp(20),
            color=(0.05, 0.05, 0.06, 1),
            halign="left",
            valign="middle",
            size_hint_y=None,
            height=dp(30),
        )

        distance_label.bind(
            size=lambda instance, value: setattr(
                instance,
                "text_size",
                value,
            )
        )

        activity_label = Label(
            text="Бег",
            font_size=sp(18),
            color=(0.08, 0.08, 0.10, 1),
            halign="left",
            valign="middle",
            size_hint_y=None,
            height=dp(28),
        )

        activity_label.bind(
            size=lambda instance, value: setattr(
                instance,
                "text_size",
                value,
            )
        )

        details_label = Label(
            text=(
                f"{format_duration(run.duration)}    "
                f"{format_distance(run.distance)} км    "
                f"{run.avg_speed:.1f} км/ч"
            ).replace(".", ","),
            font_size=sp(13),
            color=(0.55, 0.55, 0.58, 1),
            halign="left",
            valign="middle",
            size_hint_y=None,
            height=dp(26),
        )

        details_label.bind(
            size=lambda instance, value: setattr(
                instance,
                "text_size",
                value,
            )
        )

        information.add_widget(distance_label)
        information.add_widget(activity_label)
        information.add_widget(details_label)

        self.add_widget(information)

        right_column = BoxLayout(
            orientation="vertical",
            size_hint=(None, 1),
            width=dp(105),
            padding=(0, dp(4)),
        )

        run_date = run.started_at.strftime(
            "%d.%m.%Y"
        )

        date_label = Label(
            text=run_date,
            font_size=sp(14),
            color=(0.55, 0.55, 0.58, 1),
            halign="right",
            valign="top",
        )

        date_label.bind(
            size=lambda instance, value: setattr(
                instance,
                "text_size",
                value,
            )
        )

        arrow_label = Label(
            text="›",
            font_size=sp(34),
            color=(0.85, 0.85, 0.87, 1),
            halign="right",
        )

        right_column.add_widget(date_label)
        right_column.add_widget(arrow_label)

        self.add_widget(right_column)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            if self._on_press_callback is not None:
                self._on_press_callback(self.run)

            return True

        return super().on_touch_down(touch)


class ProgressScreen(Screen):
    def __init__(
        self,
        repository: RunRepository | None = None,
        **kwargs,
    ):
        super().__init__(**kwargs)

        self._repository = (
            repository
            if repository is not None
            else RunRepository()
        )

        self._current_period = "months"
        self._runs: list[Runs] = []

        self._build_ui()

    def _build_ui(self) -> None:
        self.clear_widgets()

        root = BoxLayout(
            orientation="vertical",
            padding=(
                dp(18),
                dp(12),
                dp(18),
                dp(8),
            ),
            spacing=dp(12),
        )

        with root.canvas.before:
            Color(
                0.96,
                0.96,
                0.98,
                1,
            )

            root._background = RoundedRectangle(
                pos=root.pos,
                size=root.size,
                radius=[0],
            )

        root.bind(
            pos=lambda instance, value: setattr(
                instance._background,
                "pos",
                value,
            ),
            size=lambda instance, value: setattr(
                instance._background,
                "size",
                value,
            ),
        )

        header = self._create_header()
        root.add_widget(header)

        scroll = ScrollView(
            do_scroll_x=False,
            bar_width=dp(3),
        )

        self._content = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            spacing=dp(14),
            padding=(0, 0, 0, dp(100)),
        )

        self._content.bind(
            minimum_height=self._content.setter(
                "height"
            )
        )

        self._chart_panel = self._create_chart_panel()
        self._content.add_widget(self._chart_panel)

        self._summary_container = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            spacing=dp(10),
        )

        self._summary_container.bind(
            minimum_height=self._summary_container.setter(
                "height"
            )
        )

        self._content.add_widget(
            self._summary_container
        )

        self._runs_container = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            spacing=dp(10),
        )

        self._runs_container.bind(
            minimum_height=self._runs_container.setter(
                "height"
            )
        )

        self._content.add_widget(
            self._runs_container
        )

        scroll.add_widget(self._content)
        root.add_widget(scroll)

        self.add_widget(root)

    def _create_header(self) -> BoxLayout:
        header = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(58),
            spacing=dp(8),
        )

        title = Label(
            text="[b]Прогресс[/b]",
            markup=True,
            font_size=sp(25),
            color=(0.05, 0.05, 0.07, 1),
            halign="left",
            valign="middle",
        )

        title.bind(
            size=lambda instance, value: setattr(
                instance,
                "text_size",
                value,
            )
        )

        header.add_widget(title)

        period_panel = RoundedPanel(
            orientation="horizontal",
            size_hint=(None, None),
            size=(dp(220), dp(46)),
            spacing=dp(2),
            padding=dp(2),
            radius=14,
            background_color=(
                0.90,
                0.90,
                0.93,
                1,
            ),
        )

        self._weeks_button = PeriodButton(
            text="Недели"
        )

        self._months_button = PeriodButton(
            text="Месяцы"
        )

        self._weeks_button.bind(
            on_release=lambda *_: self._set_period(
                "weeks"
            )
        )

        self._months_button.bind(
            on_release=lambda *_: self._set_period(
                "months"
            )
        )

        period_panel.add_widget(
            self._weeks_button
        )

        period_panel.add_widget(
            self._months_button
        )

        header.add_widget(period_panel)

        self._update_period_buttons()

        return header

    def _create_chart_panel(self) -> RoundedPanel:
        panel = RoundedPanel(
            orientation="vertical",
            size_hint_y=None,
            height=dp(410),
            padding=(
                dp(14),
                dp(14),
                dp(14),
                dp(12),
            ),
            spacing=dp(8),
        )

        statistics_icons = Label(
            text=(
                "🏃      🏅      📍      "
                "⏱      🔥      🏃"
            ),
            font_size=sp(23),
            color=(0.35, 0.35, 0.37, 1),
            size_hint_y=None,
            height=dp(50),
        )

        panel.add_widget(statistics_icons)

        self._chart = MonthlyChart()
        panel.add_widget(self._chart)

        chart_title = Label(
            text="[b]Активности[/b]",
            markup=True,
            font_size=sp(17),
            color=(0.06, 0.06, 0.08, 1),
            size_hint_y=None,
            height=dp(34),
        )

        panel.add_widget(chart_title)

        return panel

    def on_pre_enter(self, *_args) -> None:
        self.reload_data()

    def reload_data(self) -> None:
        try:
            self._runs = (
                self._repository.get_finished_runs()
            )
        except Exception as error:
            print(
                "Не удалось загрузить статистику:",
                error,
            )

            self._runs = []

        self._update_chart()
        self._update_summary()
        self._update_runs_list()

    def _set_period(
        self,
        period: str,
    ) -> None:
        if period not in {"weeks", "months"}:
            return

        self._current_period = period
        self._update_period_buttons()
        self._update_chart()

    def _update_period_buttons(self) -> None:
        self._weeks_button.set_selected(
            self._current_period == "weeks"
        )

        self._months_button.set_selected(
            self._current_period == "months"
        )

    def _update_chart(self) -> None:
        if self._current_period == "months":
            values = self._build_month_statistics()
        else:
            values = self._build_week_statistics()

        self._chart.set_values(values)

    def _build_month_statistics(
        self,
    ) -> list[tuple[str, int]]:
        now = datetime.now()

        months: list[tuple[int, int]] = []

        year = now.year
        month = now.month

        for _ in range(8):
            months.append((year, month))

            month -= 1

            if month == 0:
                month = 12
                year -= 1

        months.reverse()

        counters: dict[
            tuple[int, int],
            int,
        ] = defaultdict(int)

        for run in self._runs:
            key = (
                run.started_at.year,
                run.started_at.month,
            )

            counters[key] += 1

        return [
            (
                MONTH_NAMES[month_number],
                counters[(year_number, month_number)],
            )
            for year_number, month_number in months
        ]

    def _build_week_statistics(
        self,
    ) -> list[tuple[str, int]]:
        now = datetime.now()
        current_year, current_week, _ = (
            now.isocalendar()
        )

        weeks: list[tuple[int, int]] = []

        week = current_week
        year = current_year

        for _ in range(8):
            weeks.append((year, week))

            week -= 1

            if week <= 0:
                year -= 1
                week = datetime(
                    year,
                    12,
                    28,
                ).isocalendar().week

        weeks.reverse()

        counters: dict[
            tuple[int, int],
            int,
        ] = defaultdict(int)

        for run in self._runs:
            run_year, run_week, _ = (
                run.started_at.isocalendar()
            )

            counters[(run_year, run_week)] += 1

        return [
            (
                f"{week_number} нед.",
                counters[(year_number, week_number)],
            )
            for year_number, week_number in weeks
        ]

    def _update_summary(self) -> None:
        self._summary_container.clear_widgets()

        total_runs = len(self._runs)

        total_distance = sum(
            run.distance
            for run in self._runs
        )

        total_duration = sum(
            run.duration
            for run in self._runs
        )

        average_speed = (
            sum(
                run.avg_speed
                for run in self._runs
            )
            / total_runs
            if total_runs > 0
            else 0.0
        )

        now = datetime.now()

        title = Label(
            text=(
                f"[b]{MONTH_NAMES[now.month]} "
                f"{now.year} г.[/b]"
            ),
            markup=True,
            font_size=sp(21),
            color=(0.05, 0.05, 0.07, 1),
            halign="left",
            valign="middle",
            size_hint_y=None,
            height=dp(38),
        )

        title.bind(
            size=lambda instance, value: setattr(
                instance,
                "text_size",
                value,
            )
        )

        self._summary_container.add_widget(title)

        summary = RoundedPanel(
            orientation="vertical",
            size_hint_y=None,
            height=dp(108),
            padding=(
                dp(16),
                dp(12),
            ),
            spacing=dp(8),
        )

        first_line = Label(
            text=(
                f"[b]🏃 {total_runs} тренировок[/b]"
            ),
            markup=True,
            font_size=sp(18),
            color=(0.06, 0.06, 0.08, 1),
            halign="left",
            valign="middle",
        )

        first_line.bind(
            size=lambda instance, value: setattr(
                instance,
                "text_size",
                value,
            )
        )

        second_line = Label(
            text=(
                f"⏱ {format_duration(total_duration)}    "
                f"📍 {format_distance(total_distance)} км    "
                f"⚡ {average_speed:.1f} км/ч"
            ).replace(".", ","),
            font_size=sp(14),
            color=(0.47, 0.47, 0.50, 1),
            halign="left",
            valign="middle",
        )

        second_line.bind(
            size=lambda instance, value: setattr(
                instance,
                "text_size",
                value,
            )
        )

        summary.add_widget(first_line)
        summary.add_widget(second_line)

        self._summary_container.add_widget(summary)

    def _update_runs_list(self) -> None:
        self._runs_container.clear_widgets()

        if not self._runs:
            empty_label = Label(
                text=(
                    "Пока нет завершённых тренировок"
                ),
                font_size=sp(16),
                color=(0.50, 0.50, 0.53, 1),
                size_hint_y=None,
                height=dp(100),
            )

            self._runs_container.add_widget(
                empty_label
            )

            return

        for run in self._runs:
            item = RunItem(
                run=run,
                on_press=self._open_run,
            )

            self._runs_container.add_widget(item)

    def _open_run(self, run: Runs) -> None:
        if self.manager is None:
            return

        detail_screen: RunDetailScreen = (
            self.manager.get_screen("run_detail")
        )

        detail_screen.set_run(run.id)
        self.manager.current = "run_detail"