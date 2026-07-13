from kivy.app import App
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button

from kivy_garden.mapview import MapView, MapMarker, MapSource
from plyer import gps


Window.fullscreen = True


class MyApp(App):
    def build(self):
        self.follow_user = True
        self.last_latitude = None
        self.last_longitude = None

        main_layout = BoxLayout(
            orientation="vertical"
        )

        source = MapSource(
            url="https://tile.openstreetmap.org/{z}/{x}/{y}.png",
            cache_key="osm",
            min_zoom=0,
            max_zoom=19,
            attribution="© OpenStreetMap contributors"
        )

        self.map_view = MapView(
            map_source=source,
            lat=55.7558,
            lon=37.6176,
            zoom=15
        )

        self.user_marker = MapMarker(
            lat=55.7558,
            lon=37.6176
        )

        self.map_view.add_marker(self.user_marker)

        bottom_menu = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=70
        )

        progress_button = Button(text="Прогресс")
        self.start_button = Button(text="Не следить")
        settings_button = Button(text="Настройки")

        self.start_button.bind(
            on_release=self.toggle_tracking
        )

        bottom_menu.add_widget(progress_button)
        bottom_menu.add_widget(self.start_button)
        bottom_menu.add_widget(settings_button)

        main_layout.add_widget(self.map_view)
        main_layout.add_widget(bottom_menu)

        return main_layout

    def on_start(self):
        try:
            gps.configure(
                on_location=self.on_location,
                on_status=self.on_gps_status
            )

            gps.start(
                minTime=1000,
                minDistance=1
            )

        except NotImplementedError:
            print("GPS не поддерживается на этой платформе")

    def on_location(self, **kwargs):
        latitude = kwargs.get("lat")
        longitude = kwargs.get("lon")

        if latitude is None or longitude is None:
            return

        Clock.schedule_once(
            lambda dt: self.update_position(
                latitude,
                longitude
            )
        )

    def update_position(self, latitude, longitude):
        self.last_latitude = latitude
        self.last_longitude = longitude

        self.user_marker.lat = latitude
        self.user_marker.lon = longitude

        if self.follow_user:
            self.map_view.center_on(
                latitude,
                longitude
            )

    def toggle_tracking(self, button):
        self.follow_user = not self.follow_user

        if self.follow_user:
            button.text = "Не следить"

            if (
                self.last_latitude is not None
                and self.last_longitude is not None
            ):
                self.map_view.center_on(
                    self.last_latitude,
                    self.last_longitude
                )
        else:
            button.text = "Следить"

    def on_gps_status(self, status_type, status_message):
        print(
            "GPS:",
            status_type,
            status_message
        )

    def on_stop(self):
        try:
            gps.stop()
        except NotImplementedError:
            pass


MyApp().run()