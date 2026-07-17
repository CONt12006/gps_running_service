from __future__ import annotations

from kivy.graphics import Color, Line
from kivy.metrics import dp
from kivy_garden.mapview import MapLayer, MapView


class RouteMapLayer(MapLayer):
    """
    Слой MapView, рисующий маршрут по GPS-координатам.

    route_points:
        [
            (latitude, longitude),
            (latitude, longitude),
            ...
        ]
    """

    def __init__(
        self,
        route_color: tuple[float, float, float, float] = (
            0.0,
            0.82,
            0.32,
            1.0,
        ),
        route_width: float = 4,
        **kwargs,
    ):
        super().__init__(**kwargs)

        self._map_view: MapView | None = None
        self._route_points: list[
            tuple[float, float]
        ] = []

        with self.canvas:
            self._route_color_instruction = Color(
                *route_color
            )

            self._route_line = Line(
                points=[],
                width=dp(route_width),
                joint="round",
                cap="round",
            )

    def set_map_view(
        self,
        map_view: MapView,
    ) -> None:
        self._map_view = map_view
        self.reposition()

    def set_route(
        self,
        points: list[tuple[float, float]],
    ) -> None:
        self._route_points = points
        self.reposition()

    def clear_route(self) -> None:
        self._route_points = []
        self._route_line.points = []

    def reposition(self) -> None:
        """
        MapView вызывает reposition при перемещении и масштабировании.
        Пересчитываем GPS-координаты в координаты экрана.
        """

        if self._map_view is None:
            return

        if len(self._route_points) < 2:
            self._route_line.points = []
            return

        canvas_points: list[float] = []

        for latitude, longitude in self._route_points:
            x, y = self._map_view.get_window_xy_from(
                latitude,
                longitude,
                self._map_view.zoom,
            )

            # Canvas слоя использует локальные координаты.
            canvas_points.extend([
                x - self.x,
                y - self.y,
            ])

        self._route_line.points = canvas_points