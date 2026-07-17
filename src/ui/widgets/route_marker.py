from kivy.graphics import Color, Ellipse
from kivy.metrics import dp
from kivy.uix.label import Label
from kivy_garden.mapview import MapMarker


class RouteMarker(MapMarker):
    def __init__(
        self,
        marker_color: tuple[
            float,
            float,
            float,
            float,
        ],
        text: str,
        **kwargs,
    ):
        super().__init__(**kwargs)

        self.size_hint = (None, None)
        self.size = (dp(36), dp(36))
        self.anchor_x = 0.5
        self.anchor_y = 0.5

        with self.canvas:
            Color(*marker_color)

            self._circle = Ellipse(
                pos=self.pos,
                size=self.size,
            )

        self.bind(
            pos=self._update_circle,
            size=self._update_circle,
        )

        self._label = Label(
            text=text,
            bold=True,
            color=(1, 1, 1, 1),
            font_size=dp(15),
            pos=self.pos,
            size=self.size,
        )

        self.add_widget(self._label)

        self.bind(
            pos=self._update_label,
            size=self._update_label,
        )

    def _update_circle(self, *_args) -> None:
        self._circle.pos = self.pos
        self._circle.size = self.size

    def _update_label(self, *_args) -> None:
        self._label.pos = self.pos
        self._label.size = self.size