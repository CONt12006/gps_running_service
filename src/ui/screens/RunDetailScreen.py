from __future__ import annotations

from math import log2

from kivy.clock import Clock
from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy_garden.mapview import MapMarker, MapView

from src.db.models import RunPoint, Runs
from src.db.run_repository import RunRepository
from src.ui.widgets.route_map_layer import RouteMapLayer
from src.ui.widgets.route_marker import RouteMarker


ACCENT_COLOR = (0.0, 0.82, 0.32, 1.0)
BACKGROUND_COLOR = (0.96, 0.96, 0.98, 1.0)
SECONDARY_TEXT_COLOR = (0.52, 0.52, 0.55, 1.0)


def format_duration(seconds: int) -> str:
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
    distance_km = max(0.0, distance_meters) / 1000

    return f"{distance_km:.2f}".replace(".", ",")


class RoundedCard(BoxLayout):
    def __init__(
        self,
        background_color=(1, 1, 1, 1),
        radius: float = 20,
        **kwargs,
    ):
        super().__init__(**kwargs)

        with self.canvas.before:
            self._background_color = Color(
                *background_color
            )

            self._background = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[dp(radius)],
            )

        self.bind(
            pos=self._update_background,
            size=self._update_background,
        )

    def _update_background(self, *_args) -> None:
        self._background.pos = self.pos
        self._background.size = self.size


class StatisticItem(BoxLayout):
    def __init__(
        self,
        icon: str,
        value: str,
        title: str,
        **kwargs,
    ):
        super().__init__(
            orientation="vertical",
            spacing=dp(3),
            **kwargs,
        )

        icon_label = Label(
            text=icon,
            font_size=sp(22),
            size_hint_y=None,
            height=dp(32),
        )

        value_label = Label(
            text=f"[b]{value}[/b]",
            markup=True,
            font_size=sp(18),
            color=(0.06, 0.06, 0.08, 1),
            size_hint_y=None,
            height=dp(28),
        )

        title_label = Label(
            text=title,
            font_size=sp(12),
            color=SECONDARY_TEXT_COLOR,
        )

        self.add_widget(icon_label)
        self.add_widget(value_label)
        self.add_widget(title_label)


class RunDetailScreen(Screen):
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

        self._run_id: int | None = None
        self._run: Runs | None = None
        self._points: list[RunPoint] = []

        self._start_marker: MapMarker | None = None
        self._finish_marker: MapMarker | None = None

        self._build_ui()

    def _build_ui(self) -> None:
        root = BoxLayout(
            orientation="vertical",
            padding=(dp(16), dp(10), dp(16), dp(94)),
            spacing=dp(12),
        )

        with root.canvas.before:
            Color(*BACKGROUND_COLOR)

            self._root_background = RoundedRectangle(
                pos=root.pos,
                size=root.size,
            )

        root.bind(
            pos=self._update_root_background,
            size=self._update_root_background,
        )

        root.add_widget(self._create_header())

        self._map_card = RoundedCard(
            orientation="vertical",
            size_hint_y=0.60,
            padding=dp(3),
            radius=22,
        )

        self._map_view = MapView(
            zoom=15,
            lat=55.7558,
            lon=37.6173,
        )

        self._route_layer = RouteMapLayer()
        self._route_layer.set_map_view(self._map_view)

        self._map_view.bind(
            lat=self._on_map_changed,
            lon=self._on_map_changed,
            zoom=self._on_map_changed,
        )

        def _on_map_changed(self, *_args) -> None:
            Clock.schedule_once(
                lambda *_: self._route_layer.reposition(),
                0,
            )

        self._map_view.add_layer(
            self._route_layer,
            mode="scatter",
        )

        self._map_card.add_widget(self._map_view)
        root.add_widget(self._map_card)

        self._information_card = RoundedCard(
            orientation="vertical",
            size_hint_y=None,
            height=dp(225),
            padding=(dp(18), dp(14)),
            spacing=dp(10),
            radius=20,
        )

        self._title_label = Label(
            text="[b]Тренировка[/b]",
            markup=True,
            font_size=sp(23),
            color=(0.05, 0.05, 0.07, 1),
            halign="left",
            valign="middle",
            size_hint_y=None,
            height=dp(38),
        )

        self._title_label.bind(
            size=self._set_text_size,
        )

        self._date_label = Label(
            text="",
            font_size=sp(14),
            color=SECONDARY_TEXT_COLOR,
            halign="left",
            valign="middle",
            size_hint_y=None,
            height=dp(26),
        )

        self._date_label.bind(
            size=self._set_text_size,
        )

        self._statistics = BoxLayout(
            orientation="horizontal",
            spacing=dp(6),
        )

        self._information_card.add_widget(
            self._title_label
        )
        self._information_card.add_widget(
            self._date_label
        )
        self._information_card.add_widget(
            self._statistics
        )

        root.add_widget(self._information_card)
        self.add_widget(root)

    def _create_header(self) -> BoxLayout:
        header = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(54),
            spacing=dp(10),
        )

        back_button = Button(
            text="‹",
            font_size=sp(38),
            size_hint=(None, None),
            size=(dp(52), dp(52)),
            background_normal="",
            background_down="",
            background_color=(0, 0, 0, 0),
            color=(0.05, 0.05, 0.07, 1),
        )

        back_button.bind(
            on_release=lambda *_: self.go_back()
        )

        title = Label(
            text="[b]Маршрут[/b]",
            markup=True,
            font_size=sp(24),
            color=(0.05, 0.05, 0.07, 1),
            halign="left",
            valign="middle",
        )

        title.bind(
            size=self._set_text_size,
        )

        header.add_widget(back_button)
        header.add_widget(title)

        return header

    def set_run(
        self,
        run_id: int,
    ) -> None:
        """
        Вызывается перед открытием экрана.

        Запоминаем id, загружаем данные и отрисовываем маршрут.
        """

        self._run_id = run_id
        self.reload_data()

    def reload_data(self) -> None:
        if self._run_id is None:
            return

        try:
            self._run = self._repository.get_run(
                self._run_id
            )

            self._points = (
                self._repository.get_run_points(
                    self._run_id
                )
            )

        except Exception as error:
            print(
                "Не удалось загрузить тренировку:",
                error,
            )

            self._run = None
            self._points = []

        self._update_information()

        # Даём MapView завершить создание размеров.
        Clock.schedule_once(
            self._update_map,
            0,
        )

    def _update_information(self) -> None:
        self._statistics.clear_widgets()

        if self._run is None:
            self._title_label.text = (
                "[b]Тренировка не найдена[/b]"
            )
            self._date_label.text = ""
            return

        self._title_label.text = (
            f"[b]{format_distance(self._run.distance)} км — Бег[/b]"
        )

        self._date_label.text = (
            self._run.started_at.strftime(
                "%d.%m.%Y  •  %H:%M"
            )
        )

        self._statistics.add_widget(
            StatisticItem(
                icon="📍",
                value=(
                    f"{format_distance(self._run.distance)} км"
                ),
                title="Расстояние",
            )
        )

        self._statistics.add_widget(
            StatisticItem(
                icon="⏱",
                value=format_duration(
                    self._run.duration
                ),
                title="Время",
            )
        )

        self._statistics.add_widget(
            StatisticItem(
                icon="⚡",
                value=(
                    f"{self._run.avg_speed:.1f}"
                    .replace(".", ",")
                    + " км/ч"
                ),
                title="Ср. скорость",
            )
        )

        self._statistics.add_widget(
            StatisticItem(
                icon="●",
                value=str(len(self._points)),
                title="GPS-точек",
            )
        )

    def _on_map_changed(self, *_args) -> None:
        Clock.schedule_once(
            lambda *_: self._route_layer.reposition(),
            0,
        )

    def _update_map(self, *_args) -> None:
        self._remove_markers()

        coordinates = [
            (
                point.latitude,
                point.longitude,
            )
            for point in self._points
        ]

        self._route_layer.set_route(
            coordinates
        )

        if not coordinates:
            return

        start_latitude, start_longitude = (
            coordinates[0]
        )

        self._start_marker = RouteMarker(
            lat=start_latitude,
            lon=start_longitude,
            marker_color=ACCENT_COLOR,
            text="S",
        )

        self._map_view.add_marker(
            self._start_marker
        )

        if len(coordinates) > 1:
            finish_latitude, finish_longitude = (
                coordinates[-1]
            )

            self._finish_marker = RouteMarker(
                lat=finish_latitude,
                lon=finish_longitude,
                marker_color=(0.95, 0.20, 0.20, 1),
                text="F",
            )

            self._map_view.add_marker(
                self._finish_marker
            )

        self._fit_route(coordinates)

        # После смены центра и zoom линию нужно пересчитать.
        Clock.schedule_once(
            lambda *_: self._route_layer.reposition(),
            0.1,
        )

    def _fit_route(
        self,
        coordinates: list[
            tuple[float, float]
        ],
    ) -> None:
        """
        Центрирует карту на маршруте и подбирает примерный zoom.
        """

        latitudes = [
            latitude
            for latitude, _ in coordinates
        ]

        longitudes = [
            longitude
            for _, longitude in coordinates
        ]

        minimum_latitude = min(latitudes)
        maximum_latitude = max(latitudes)
        minimum_longitude = min(longitudes)
        maximum_longitude = max(longitudes)

        center_latitude = (
            minimum_latitude + maximum_latitude
        ) / 2

        center_longitude = (
            minimum_longitude + maximum_longitude
        ) / 2

        self._map_view.center_on(
            center_latitude,
            center_longitude,
        )

        latitude_span = (
            maximum_latitude - minimum_latitude
        )

        longitude_span = (
            maximum_longitude - minimum_longitude
        )

        maximum_span = max(
            latitude_span,
            longitude_span,
        )

        if maximum_span <= 0.0005:
            zoom = 17
        elif maximum_span <= 0.002:
            zoom = 16
        elif maximum_span <= 0.005:
            zoom = 15
        elif maximum_span <= 0.01:
            zoom = 14
        elif maximum_span <= 0.03:
            zoom = 13
        elif maximum_span <= 0.08:
            zoom = 12
        elif maximum_span <= 0.2:
            zoom = 11
        else:
            zoom = 10

        self._map_view.zoom = zoom

    def _remove_markers(self) -> None:
        if self._start_marker is not None:
            self._map_view.remove_marker(
                self._start_marker
            )
            self._start_marker = None

        if self._finish_marker is not None:
            self._map_view.remove_marker(
                self._finish_marker
            )
            self._finish_marker = None

    def go_back(self) -> None:
        if self.manager is not None:
            self.manager.current = "progress"

    def _update_root_background(
        self,
        instance,
        _value,
    ) -> None:
        self._root_background.pos = instance.pos
        self._root_background.size = instance.size

    @staticmethod
    def _set_text_size(
        label: Label,
        size: tuple[float, float],
    ) -> None:
        label.text_size = size