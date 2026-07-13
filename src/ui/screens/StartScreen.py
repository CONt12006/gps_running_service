from kivy.uix.screenmanager import Screen
from kivy.uix.floatlayout import FloatLayout
from kivy_garden.mapview import MapView, MapMarker, MapSource


class StartScreen(Screen):
    """Класс создает основной экран с картой"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        layout = FloatLayout()

        map_source = MapSource(
            url="https://tile.openstreetmap.org/{z}/{x}/{y}.png",
            cache_key="osm",
            min_zoom=0,
            max_zoom=19,
            attribution="© OpenStreetMap contributors",
        )

        self.map_view = MapView(
            map_source=map_source,
            lat=55.7558,
            lon=37.6173,
            zoom=10,
            size_hint=(1, 1),
            pos_hint={"x": 0, "y": 0},
        )

        self.user_marker = MapMarker(
            lat=55.7558,
            lon=37.6173,
        )

        self.map_view.add_marker(self.user_marker)



        layout.add_widget(self.map_view)

        self.add_widget(layout)