from kivy.uix.screenmanager import Screen
from kivy.clock import Clock
from kivy.utils import platform
from kivy.uix.floatlayout import FloatLayout
from kivy_garden.mapview import MapView, MapMarker, MapSource
from kivy_garden.mapview.geojson import GeoJsonMapLayer

from src.domain.gps_point import GPSPoint
from src.services.gps_service import GPSService
from tracking_service import TrackingService
from src.db.run_repository import RunRepository

from ..widgets.bottom_start import BottomStart

from math import atan2, cos, radians, sin, sqrt

from time import perf_counter

from pathlib import Path

from src.platform_api.android_tracking_service import (
    AndroidTrackingServiceController,
)
from src.services.tracking_state_store import (
    TrackingStateStore,
)


class StartScreen(Screen):
    """Основной экран с картой и управлением GPS-трекингом."""

    def __init__(self, repository: RunRepository, data_directory: Path, **kwargs):
        super().__init__(**kwargs)

        self.is_tracking = False

        self._run_repository = repository
        self._data_directory = Path(data_directory)
        self._database_path = (self._data_directory / "gpstracker.db")
        self._tracking_state_store = TrackingStateStore(self._data_directory / "tracking_state.json")

        self._android_service = (AndroidTrackingServiceController())

        self._tracking_service = TrackingService(
            repository=self._run_repository,
        )

        self._active_run_id: int | None = None
        self._last_loaded_point_id = 0
        self._background_poll_event = None
        self._is_finishing = False

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
            cache_key="osm_https_v2",
            min_zoom=0,
            max_zoom=19,
            tile_size=256,
            image_ext="png",
            attribution="© OpenStreetMap contributors",
        )

        self.map_view = MapView(
            lat=55.7558,
            lon=37.6173,
            zoom=10,
            size_hint=(1, 1),
            pos_hint={"x": 0, "y": 0},
        )

        self.map_view.map_source = map_source

        print(
            "MAP SOURCE:",
            self.map_view.map_source.url,
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

        Clock.schedule_once(self._restore_background_tracking, 0)


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

        if self.is_tracking or self._is_finishing:
            return

        if platform == "android":
            self.on_gps_status(
                "Проверяем разрешения для фонового GPS"
            )

            self._android_service.request_permissions(
                on_granted=lambda: Clock.schedule_once(
                    lambda _dt: (
                        self._start_android_tracking()
                    ),
                    0,
                ),
                on_denied=lambda message: (
                    Clock.schedule_once(
                        lambda _dt: (
                            self.on_gps_status(message)
                        ),
                        0,
                    )
                ),
            )

            return

        # Старое поведение для ПК и других платформ.
        run_id = self._tracking_service.start_running()

        self._active_run_id = run_id
        self._prepare_new_route(run_id)

        self.gps_service.start(
            min_time=1000,
            min_distance=1,
        )


    def _prepare_new_route(
        self,
        run_id: int,
    ) -> None:
        print(
            f"Началась пробежка: run_id={run_id}"
        )

        self.route_points.clear()
        self.route_coordinates.clear()
        self.clear_route()

        self.good_fix_count = 0
        self.gps_ready = False
        self.last_accepted_at = None
        self.last_display_point = None

        self._last_loaded_point_id = 0

        self.is_tracking = True
        self.start_button.disabled = False
        self.start_button.text = "Остановить"


    def _start_android_tracking(self) -> None:
        if self.is_tracking or self._is_finishing:
            return

        run_id = self._run_repository.create_run()

        min_time = 1000
        min_distance = 1.0

        self._tracking_state_store.begin(
            run_id=run_id,
            database_path=self._database_path,
            min_time=min_time,
            min_distance=min_distance,
        )

        try:
            self._android_service.start(
                run_id=run_id,
                database_path=self._database_path,
                state_path=(
                    self._tracking_state_store.path
                ),
                min_time=min_time,
                min_distance=min_distance,
            )

        except Exception as error:
            self._tracking_state_store.clear()
            self._run_repository.delete_run(run_id)

            self.on_gps_status(
                "Не удалось запустить "
                f"foreground service: {error}"
            )
            return

        self._active_run_id = run_id

        self._prepare_new_route(run_id)
        self._start_background_polling()

        self.on_gps_status(
            "Фоновая запись маршрута запущена"
        )

    def stop_tracking(self) -> None:
        if not self.is_tracking:
            return

        if self._is_finishing:
            return

        if platform == "android":
            run_id = self._active_run_id

            if run_id is None:
                self._reset_tracking_ui()
                return

            self._is_finishing = True
            self.start_button.disabled = True
            self.start_button.text = "Завершаем..."

            self._tracking_state_store.request_stop(
                run_id
            )

            Clock.schedule_once(
                lambda _dt: (
                    self._finish_android_tracking(
                        run_id
                    )
                ),
                1.5,
            )

            return

        # Старое поведение не на Android.
        self.is_tracking = False

        self.gps_service.stop()
        self._tracking_service.finish_running()

        self._active_run_id = None
        self.start_button.text = "Начать"


    def _finish_android_tracking(
        self,
        run_id: int,
    ) -> None:
        try:
            try:
                self._android_service.stop()
            except Exception as error:
                self.on_gps_status(
                    "Ошибка остановки service: "
                    f"{error}"
                )

            self._poll_background_points()

            self._run_repository.finalize_run_from_points(
                run_id
            )

        except Exception as error:
            self.on_gps_status(
                f"Ошибка завершения пробежки: {error}"
            )

        finally:
            self._tracking_state_store.clear()
            self._stop_background_polling()
            self._reset_tracking_ui()


    def _reset_tracking_ui(self) -> None:
        self.is_tracking = False
        self._is_finishing = False
        self._active_run_id = None

        self.start_button.disabled = False
        self.start_button.text = "Начать"


    def on_gps_location(self, point: GPSPoint) -> None:
        """
        Получает GPS-точку от GPSService.

        TrackingService проверяет и сохраняет точку.
        Если точка принята, обновляем карту.
        """

        print(
            f"RAW GPS POINT: "
            f"lat={point.latitude}, "
            f"lon={point.longitude}, "
            f"accuracy={point.accuracy}"
        )

        if not self.is_tracking:
            return

        accepted = self._tracking_service.handle_gps_point(
            point
        )

        if not accepted:
            return

        self._update_map(point)


    def _update_map(self, point: GPSPoint) -> None:
        """
        Добавляет принятую GPS-точку в отображаемый маршрут
        и обновляет маркер пользователя.
        """

        self.route_points.append(point)

        display_point = self.smooth_display_point(
            point
        )

        self.route_coordinates.append(
            [
                float(display_point.longitude),
                float(display_point.latitude),
            ]
        )

        self.update_user_marker(
            display_point
        )

        self.update_route()

        accuracy_text = (
            f"{point.accuracy:.1f} м"
            if point.accuracy is not None
            else "неизвестна"
        )

        print(
            f"GPS POINT ACCEPTED: "
            f"points={len(self.route_points)}, "
            f"accuracy={accuracy_text}"
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


    def _start_background_polling(self) -> None:
        self._stop_background_polling()

        self._background_poll_event = (
            Clock.schedule_interval(
                self._poll_background_points,
                1.0,
            )
        )

        self._poll_background_points()


    def _stop_background_polling(self) -> None:
        if self._background_poll_event is None:
            return

        self._background_poll_event.cancel()
        self._background_poll_event = None


    def _poll_background_points(
        self,
        _dt=0,
    ) -> None:
        if platform != "android":
            return

        run_id = self._active_run_id

        if run_id is None:
            return

        try:
            points = (
                self._run_repository
                .get_run_points_after_id(
                    run_id=run_id,
                    last_point_id=(
                        self._last_loaded_point_id
                    ),
                )
            )

        except Exception as error:
            self.on_gps_status(
                "Ошибка чтения фоновых точек: "
                f"{error}"
            )
            return

        for model in points:
            self._last_loaded_point_id = model.id

            point = GPSPoint(
                latitude=model.latitude,
                longitude=model.longitude,
                altitude=model.altitude,
                speed=model.speed,
                bearing=model.bearing,
                accuracy=model.accuracy,
            )

            self._update_map(point)


    def _restore_background_tracking(
        self,
        _dt=0,
    ) -> None:
        if platform != "android":
            return

        state = self._tracking_state_store.read()

        if not state:
            return

        if not state.get("active", False):
            return

        try:
            run_id = int(state["run_id"])
        except (
            KeyError,
            TypeError,
            ValueError,
        ):
            self._tracking_state_store.clear()
            return

        run = self._run_repository.get_run(run_id)

        if run is None:
            self._tracking_state_store.clear()
            return

        if run.finished_at is not None:
            self._tracking_state_store.clear()
            return

        self._active_run_id = run_id
        self.is_tracking = True

        self.start_button.text = "Остановить"

        self._load_existing_route(run_id)
        self._start_background_polling()

        self.on_gps_status(
            "Активная пробежка восстановлена"
        )


    def _load_existing_route(
        self,
        run_id: int,
    ) -> None:
        self.route_points.clear()
        self.route_coordinates.clear()
        self.clear_route()

        self.last_display_point = None
        self._last_loaded_point_id = 0

        points = self._run_repository.get_run_points(
            run_id
        )

        last_display_point: GPSPoint | None = None

        for model in points:
            point = GPSPoint(
                latitude=model.latitude,
                longitude=model.longitude,
                altitude=model.altitude,
                speed=model.speed,
                bearing=model.bearing,
                accuracy=model.accuracy,
            )

            self.route_points.append(point)

            last_display_point = (
                self.smooth_display_point(point)
            )

            self.route_coordinates.append(
                [
                    float(
                        last_display_point.longitude
                    ),
                    float(
                        last_display_point.latitude
                    ),
                ]
            )

            self._last_loaded_point_id = model.id

        if last_display_point is not None:
            self.update_user_marker(
                last_display_point
            )

        self.update_route()