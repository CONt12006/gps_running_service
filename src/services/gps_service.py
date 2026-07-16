"""
Общая идея GPS_service
GPSService
├── запускает GPS
├── останавливает GPS
├── просит разрешения на Android
├── получает координаты от телефона
├── превращает их в GPSPoint
└── отдаёт координаты экрану
"""
from typing import Callable

from kivy.clock import mainthread
from kivy.utils import platform
from plyer import gps

from ..domain.gps_point import GPSPoint


class GPSService:
    """
    on_location — это функция, которой GPSService передаёт новую GPS-точку, 
    когда получает координаты от телефона.
    То есть сам сервис получает координаты, создаёт GPSPoint, а потом вызывает:

    on_status — это функция, которой сервис передаёт текст о состоянии GPS.
    """
    def __init__(self, on_location: Callable[[GPSPoint], None], on_status: Callable[[str], None] | None = None):
        # Функция, передаваемая от экрана, которую должен выполнить GPSService
        self.on_location = on_location

        # Функция, которую экран передаёт в GPSService, чтобы сервис мог сообщать экрану текстовый статус
        self.on_status = on_status

        self._min_time = 1000
        self._min_distance = 1
        self._is_running = False


    def start(self, min_time: int = 1000, min_distance: int = 1) -> None:
        """Запускает получение координат"""
        self._min_time = min_time
        self._min_distance = min_distance

        if platform == "android":
            self._request_android_permissions()
            return
        
        self._start_gps()


    def stop(self):
        """Останавливает получение координат"""
        if not self._is_running:
            return
        
        try:
            gps.stop()
            self._is_running = False
            self._emit_status(f"GPS остановлен")
        except Exception as error:
            self._emit_status(f"Ошибка остановки GPS: {error}")

    def _request_android_permissions(self) -> None:
        """Просит доступ к GPS на Android"""
        try:
            from android.permissions import (
                Permission,
                check_permission,
                request_permissions,
            )

            has_coarse = check_permission(
                Permission.ACCESS_COARSE_LOCATION
            )
            has_fine = check_permission(
                Permission.ACCESS_FINE_LOCATION
            )

            if has_coarse or has_fine:
                self._emit_status("Разрешение на геолокацию уже есть")
                self._start_gps()
                return

            request_permissions(
                [
                    Permission.ACCESS_COARSE_LOCATION,
                    Permission.ACCESS_FINE_LOCATION,
                ],
                self._on_android_permissions_result,
            )

        except Exception as error:
            self._emit_status(f"Ошибка запроса Android permissions: {error}")


    def _on_android_permissions_result(self, permissions: list[str], grant_results: list[bool]):
        """обрабатывает ответ пользователя"""
        permission_result = dict(zip(permissions, grant_results))

        coarse_granted = permission_result.get(
            "android.permission.ACCESS_COARSE_LOCATION",
            False,
        )

        fine_granted = permission_result.get(
            "android.permission.ACCESS_FINE_LOCATION",
            False,
        )

        if (not coarse_granted and not fine_granted):
            self._emit_status("Пользователь запретил доступ к местоположению")
            return

        if fine_granted:
            self._emit_status("Разрешено точное местоположение")
        else:
            self._emit_status("Разрешено только примерное местоположение")

        self._start_gps()


    def _start_gps(self) -> None:
        """Реально запускает plyer.gps."""

        if self._is_running:
            self._emit_status("GPS уже запущен")
            return

        try:
            gps.configure(
                on_location=self._on_location,
                on_status=self._on_status,
            )

            gps.start(
                minTime=self._min_time,
                minDistance=self._min_distance,
            )

            self._is_running = True
            self._emit_status("GPS запущен")

        except NotImplementedError:
            self._emit_status(
                "GPS не поддерживается на этой платформе"
            )

        except Exception as error:
            self._emit_status(
                f"Ошибка запуска GPS: {error}"
            )

    def _on_location(self, **kwargs):
        """Принимает координаты от телефона"""
        lat = kwargs.get("lat")
        lon = kwargs.get("lon")

        if lat is None or lon is None:
            self._emit_status(f"GPS вернул данные без lat/lon: {kwargs}")
            return

        point = GPSPoint(
            lat=float(lat),
            lon=float(lon),
            altitude=self._to_optional_float(kwargs.get("altitude")),
            speed=self._to_optional_float(kwargs.get("speed")),
            bearing=self._to_optional_float(kwargs.get("bearing")),
            accuracy=self._to_optional_float(kwargs.get("accuracy")),
        )

        self._emit_location(point)

    def _on_status(self, status_type, status):
        """принимает статус GPS"""
        self._emit_status(f"{status_type}: {status}")



    def _to_optional_float(self, value) -> float | None:
        """безопасно приводит значения к float"""
        if value is None:
            return None

        try:
            return float(value)
        except (TypeError, ValueError):
            return None


    @mainthread
    def _emit_location(self, point: GPSPoint) -> None:
        """отдаёт GPSPoint экрану"""
        self.on_location(point)


    @mainthread
    def _emit_status(self, message: str) -> None:
        """Отдаёт текстовый статус экрану."""

        if self.on_status is not None:
            self.on_status(message)