from kivy.uix.screenmanager import Screen
from kivy.uix.floatlayout import FloatLayout
from kivy_garden.mapview import MapView, MapMarker, MapSource
from kivy_garden.mapview.geojson import GeoJsonMapLayer

from src.domain.gps_point import GPSPoint
from src.services.gps_service import GPSService
from src.services.tracking_service import TrackingService
from src.db.run_repository import RunRepository

from ..widgets.bottom_start import BottomStart

from math import atan2, cos, radians, sin, sqrt

from time import perf_counter


class StartScreen(Screen):
    """Основной экран с картой и управлением GPS-трекингом."""

    def __init__(self, repository: RunRepository, **kwargs):
        super().__init__(**kwargs)

        self.is_tracking = False

        self._run_repository = repository

        self._tracking_service = TrackingService(
            repository=self._run_repository,
        )

        # Фильтрация GPS
        self.max_accuracy = 17.0
        self.start_accuracy = 15.0
        self.required_good_fixes = 3
        self.min_route_point_distance = 5.0
        self.max_running_speed = 8.0

        # Состояние GPS-фильтра
        self.good_fix_count = 0
        self.gps_ready = False
        self.last_accepted_at: float | None = None

        # Сглаживание отображаемого маршрута
        self.smoothing_alpha = 0.35
        self.last_display_point: GPSPoint | None = None

        # Данные маршрута
        self.route_points: list[GPSPoint] = []
        self.route_coordinates: list[list[float]] = []

        # Маркер создадим после первой принятой точки
        self.user_marker: MapMarker | None = None

        self.gps_service = GPSService(
            on_location=self.on_gps_location,
            on_status=self.on_gps_status,
        )

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

        self.route_layer = GeoJsonMapLayer()

        self.route_layer.geojson = {
            "type": "FeatureCollection",
            "features": [],
        }

        self.map_view.add_layer(self.route_layer)

        self.start_button = BottomStart(
            pos_hint={
                "center_x": 0.5,
                "y": 0.15,
            },
        )

        self.start_button.bind(
            on_press=self.on_start_button_press,
        )

        layout.add_widget(self.map_view)
        layout.add_widget(self.start_button)

        self.add_widget(layout)


    def update_route(self) -> None:
        if len(self.route_coordinates) < 2:
            return

        started_at = perf_counter()

        self.route_layer.geojson = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {
                        "stroke": "#2196F3",
                        "stroke-width": 3,
                        "stroke-opacity": 1,
                    },
                    "geometry": {
                        "type": "LineString",
                        "coordinates": self.route_coordinates,
                    },
                }
            ],
        }

        elapsed_ms = (perf_counter() - started_at) * 1000

        print(
            f"ROUTE REDRAW: "
            f"points={len(self.route_coordinates)}, "
            f"time={elapsed_ms:.2f} ms"
        )


    def clear_route(self) -> None:
        self.route_layer.geojson = {
            "type": "FeatureCollection",
            "features": [],
        }


    def has_acceptable_accuracy(self, point: GPSPoint) -> bool:
        if point.accuracy is None:
            return True

        return point.accuracy <= self.max_accuracy
    

    def calculate_distance(
        self,
        first: GPSPoint,
        second: GPSPoint,
    ) -> float:
        earth_radius = 6_371_000.0

        lat1 = radians(first.latitude)
        lon1 = radians(first.longitude)

        lat2 = radians(second.latitude)
        lon2 = radians(second.longitude)

        delta_lat = lat2 - lat1
        delta_lon = lon2 - lon1

        a = (
            sin(delta_lat / 2) ** 2
            + cos(lat1)
            * cos(lat2)
            * sin(delta_lon / 2) ** 2
        )

        c = 2 * atan2(
            sqrt(a),
            sqrt(1 - a),
        )

        return earth_radius * c
    

    def is_far_enough_from_previous(
        self,
        point: GPSPoint,
    ) -> bool:
        if not self.route_points:
            return True

        previous_point = self.route_points[-1]

        distance = self.calculate_distance(
            previous_point,
            point,
        )

        current_accuracy = float(point.accuracy or 0.0)
        previous_accuracy = float(previous_point.accuracy or 0.0)

        accuracy_based_distance = (
            max(current_accuracy, previous_accuracy) * 0.5
        )

        required_distance = max(
            self.min_route_point_distance,
            accuracy_based_distance,
        )

        if distance < required_distance:
            print(
                f"GPS POINT REJECTED: "
                f"distance={distance:.1f} м, "
                f"required={required_distance:.1f} м"
            )
            return False

        return True
    

    def has_acceptable_speed(
        self,
        point: GPSPoint,
        received_at: float,
    ) -> bool:
        if not self.route_points:
            return True

        if self.last_accepted_at is None:
            return True

        previous_point = self.route_points[-1]

        distance = self.calculate_distance(
            previous_point,
            point,
        )

        elapsed_seconds = received_at - self.last_accepted_at

        if elapsed_seconds <= 0:
            return False

        calculated_speed = distance / elapsed_seconds

        if calculated_speed > self.max_running_speed:
            print(
                f"GPS POINT REJECTED: "
                f"speed={calculated_speed:.1f} м/с, "
                f"distance={distance:.1f} м, "
                f"time={elapsed_seconds:.2f} с"
            )
            return False

        return True
    

    def is_valid_route_point(
        self,
        point: GPSPoint,
        received_at: float,
    ) -> bool:
        if not self.has_stable_gps_fix(point):
            return False

        if not self.is_far_enough_from_previous(point):
            return False

        if not self.has_acceptable_speed(point, received_at):
            return False

        return True
    

    def smooth_display_point(
        self,
        point: GPSPoint,
    ) -> GPSPoint:
        previous = self.last_display_point

        if previous is None:
            self.last_display_point = point
            return point

        alpha = self.smoothing_alpha

        smoothed_point = GPSPoint(
            latitude=(
                previous.latitude
                + alpha * (point.latitude - previous.latitude)
            ),
            longitude=(
                previous.longitude
                + alpha * (point.longitude - previous.longitude)
            ),
            altitude=point.altitude,
            speed=point.speed,
            bearing=point.bearing,
            accuracy=point.accuracy,
        )

        self.last_display_point = smoothed_point

        return smoothed_point
            

    def on_start_button_press(self, button) -> None:
        """
        Вызывается при нажатии кнопки.

        Если GPS не запущен — запускаем.
        Если GPS уже работает — останавливаем.
        """

        if self.is_tracking:
            self.stop_tracking()
        else:
            self.start_tracking()


    def has_stable_gps_fix(self, point: GPSPoint) -> bool:
        accuracy = point.accuracy

        if accuracy is None:
            print("GPS POINT REJECTED: accuracy отсутствует")
            return False

        # После получения стабильного сигнала используем обычный порог
        if self.gps_ready:
            if accuracy > self.max_accuracy:
                print(
                    f"GPS POINT REJECTED: "
                    f"accuracy={accuracy:.1f} м, "
                    f"максимум={self.max_accuracy:.1f} м"
                )
                return False

            return True

        # Перед началом записи требуем более качественные точки
        if accuracy > self.start_accuracy:
            self.good_fix_count = 0

            print(
                f"GPS WAITING: "
                f"accuracy={accuracy:.1f} м, "
                f"нужно <= {self.start_accuracy:.1f} м"
            )
            return False

        self.good_fix_count += 1

        print(
            f"GPS GOOD FIX: "
            f"{self.good_fix_count}/{self.required_good_fixes}, "
            f"accuracy={accuracy:.1f} м"
        )

        if self.good_fix_count < self.required_good_fixes:
            return False

        self.gps_ready = True
        print("GPS READY: начинаем записывать маршрут")

        return True


    def start_tracking(self) -> None:
        """Начинает запись GPS-маршрута."""

        run_id = self._tracking_service.start_running()

        print("Начинаем GPS-трекинг")
        print(f"Пробежка началась: run_id={run_id}")

        self.route_points.clear()
        self.route_coordinates.clear()
        self.clear_route()

        self.good_fix_count = 0
        self.gps_ready = False
        self.last_accepted_at = None
        self.last_display_point = None

        self.is_tracking = True
        self.start_button.text = "Остановить"

        self.gps_service.start(
            min_time=1000,
            min_distance=1,
        )

        print("GPS: ожидание стабильного сигнала")

    def stop_tracking(self) -> None:
        """Останавливает запись GPS-маршрута."""

        print("Останавливаем GPS-трекинг")

        self.is_tracking = False
        self.gps_service.stop()
        self._tracking_service.finish_running()
        self.start_button.text = "Начать"

        print(
            f"GPS-трекинг завершён. "
            f"Получено точек: {len(self.route_points)}"
        )

    def on_gps_location(self, point: GPSPoint) -> None:
        """
        Вызывается GPSService каждый раз,
        когда приходит новая GPS-точка.
        """

        print(
            f"RAW GPS POINT: "
            f"lat={point.latitude}, "
            f"lon={point.longitude}, "
            f"accuracy={point.accuracy}"
        )

        accepted = self._tracking_service.handle_gps_point(
            point
        )

        if accepted:
            self._update_map(point)

        if not self.is_tracking:
            return

        received_at = perf_counter()

        if not self.is_valid_route_point(
            point,
            received_at,
        ):
            return

        # Сохраняем настоящую принятую точку
        self.route_points.append(point)
        self.last_accepted_at = received_at

        # Сглаживаем только координату для линии
        display_point = self.smooth_display_point(point)

        self.route_coordinates.append([
            float(display_point.longitude),
            float(display_point.latitude),
        ])

        self.update_user_marker(display_point)
        self.update_route()

        print(
            f"GPS POINT ACCEPTED: "
            f"points={len(self.route_points)}, "
            f"accuracy={point.accuracy:.1f} м"
        )


    def update_user_marker(self, point: GPSPoint) -> None:
        if self.user_marker is None:
            self.user_marker = MapMarker(
                lat=point.latitude,
                lon=point.longitude,
            )

            self.map_view.add_marker(self.user_marker)
        else:
            self.user_marker.lat = point.latitude
            self.user_marker.lon = point.longitude

        self.map_view.center_on(
            point.latitude,
            point.longitude,
        )

    def on_gps_status(self, message: str) -> None:
        """
        Вызывается GPSService, когда нужно сообщить
        состояние GPS или ошибку.
        """

        print(f"GPS STATUS: {message}")

    def on_leave(self, *args) -> None:
        pass