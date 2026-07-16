from kivy.uix.screenmanager import Screen
from kivy.uix.floatlayout import FloatLayout
from kivy_garden.mapview import MapView, MapMarker, MapSource

from src.domain.gps_point import GPSPoint
from src.services.gps_service import GPSService

from ..widgets.bottom_start import BottomStart


class StartScreen(Screen):
    """Основной экран с картой и управлением GPS-трекингом."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Показывает, идёт ли сейчас запись маршрута
        self.is_tracking = False

        # Здесь временно хранятся полученные GPS-точки
        self.route_points: list[GPSPoint] = []

        # Создаём один GPSService для этого экрана
        self.gps_service = GPSService(
            on_location=self.on_gps_location,
            on_status=self.on_gps_status,
        )

        # Общий контейнер экрана
        layout = FloatLayout()

        map_source = MapSource(
            url="https://tile.openstreetmap.org/{z}/{x}/{y}.png",
            cache_key="osm",
            min_zoom=0,
            max_zoom=19,
            attribution="© OpenStreetMap contributors",
        )

        # Создаём карту
        self.map_view = MapView(
            map_source=map_source,
            lat=55.7558,
            lon=37.6173,
            zoom=10,
            size_hint=(1, 1),
            pos_hint={"x": 0, "y": 0},
        )

        # Создаём маркер текущего положения
        self.user_marker = MapMarker(
            lat=55.7558,
            lon=37.6173,
        )

        # Добавляем маркер на карту
        self.map_view.add_marker(self.user_marker)

        # Создаём кнопку запуска GPS
        self.start_button = BottomStart(
            pos_hint={
                "center_x": 0.5,
                "y": 0.15,
            },
        )

        # При нажатии вызываем on_start_button_press
        self.start_button.bind(
            on_press=self.on_start_button_press,
        )

        # Сначала добавляем карту
        layout.add_widget(self.map_view)

        # Затем кнопку, чтобы она находилась поверх карты
        layout.add_widget(self.start_button)

        # Добавляем общий контейнер на экран
        self.add_widget(layout)

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

    def start_tracking(self) -> None:
        """Начинает запись GPS-маршрута."""

        print("Начинаем GPS-трекинг")

        # Очищаем точки от предыдущей тренировки
        self.route_points.clear()

        # Ставим флаг, что запись маршрута началась
        self.is_tracking = True

        # Меняем текст кнопки
        self.start_button.text = "Остановить"

        # Запускаем GPSService
        self.gps_service.start(
            min_time=1000,
            min_distance=1,
        )

    def stop_tracking(self) -> None:
        """Останавливает запись GPS-маршрута."""

        print("Останавливаем GPS-трекинг")

        # Останавливаем GPS
        self.gps_service.stop()

        # Ставим флаг, что запись завершена
        self.is_tracking = False

        # Возвращаем текст кнопки
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

        if not self.is_tracking:
            return

        # Сохраняем точку маршрута
        self.route_points.append(point)

        print(
            "Получена GPS-точка: "
            f"lat={point.lat}, "
            f"lon={point.lon}, "
            f"accuracy={point.accuracy}"
        )

        # Перемещаем маркер
        self.user_marker.lat = point.lat
        self.user_marker.lon = point.lon

        # Центрируем карту на новой координате
        self.map_view.center_on(
            point.lat,
            point.lon,
        )

    def on_gps_status(self, message: str) -> None:
        """
        Вызывается GPSService, когда нужно сообщить
        состояние GPS или ошибку.
        """

        print(f"GPS STATUS: {message}")

    def on_leave(self, *args) -> None:
        """
        Вызывается Kivy, когда пользователь уходит с экрана.

        Останавливаем GPS, чтобы он не продолжал работать
        в фоне после ухода с экрана.
        """

        if self.is_tracking:
            self.stop_tracking()