from __future__ import annotations

import json
import os
import time
import traceback
from math import asin, cos, radians, sin, sqrt
from pathlib import Path
from typing import Any, Callable


print(
    "BACKGROUND MODULE LOADED",
    flush=True,
)


try:
    print(
        "BACKGROUND IMPORTS STARTED",
        flush=True,
    )

    from jnius import (
        PythonJavaClass,
        autoclass,
        java_method,
    )

    from src.db.database import (
        configure_database,
        create_tables,
    )
    from src.db.run_repository import RunRepository
    from src.domain.gps_point import GPSPoint
    from src.services.tracking_state_store import (
        TrackingStateStore,
    )

    print(
        "BACKGROUND IMPORTS COMPLETED",
        flush=True,
    )

except BaseException as error:
    print(
        "BACKGROUND IMPORT ERROR: "
        f"{type(error).__name__}: {error}",
        flush=True,
    )
    traceback.print_exc()
    time.sleep(3)
    raise


# Для первоначальной проверки допускаем
# относительно невысокую точность GPS.
START_ACCURACY = 50.0
MAX_ACCURACY = 100.0
REQUIRED_GOOD_FIXES = 1

# Минимальное перемещение между сохраняемыми точками.
MIN_ROUTE_DISTANCE = 2.0

# Максимальная допустимая скорость.
# 15 м/с — примерно 54 км/ч.
MAX_RUNNING_SPEED = 15.0

STATE_CHECK_INTERVAL_SECONDS = 1.0
STATE_FILE_WAIT_SECONDS = 5.0


def log(message: str) -> None:
    print(
        message,
        flush=True,
    )


def calculate_distance(
    first: GPSPoint,
    second: GPSPoint,
) -> float:
    """
    Вычисляет расстояние между GPS-точками
    по формуле гаверсинусов.

    Возвращает расстояние в метрах.
    """

    earth_radius = 6_371_000.0

    first_latitude = radians(
        first.latitude
    )
    second_latitude = radians(
        second.latitude
    )

    latitude_delta = radians(
        second.latitude - first.latitude
    )
    longitude_delta = radians(
        second.longitude - first.longitude
    )

    haversine = (
        sin(latitude_delta / 2.0) ** 2
        + cos(first_latitude)
        * cos(second_latitude)
        * sin(longitude_delta / 2.0) ** 2
    )

    # Защита от погрешности float.
    haversine = min(
        1.0,
        max(0.0, haversine),
    )

    angular_distance = 2.0 * asin(
        sqrt(haversine)
    )

    return earth_radius * angular_distance


def get_optional_location_value(
    location: Any,
    has_method_name: str,
    get_method_name: str,
) -> float | None:
    """
    Безопасно получает необязательное поле
    android.location.Location.
    """

    try:
        has_method = getattr(
            location,
            has_method_name,
        )

        if not has_method():
            return None

        get_method = getattr(
            location,
            get_method_name,
        )

        return float(
            get_method()
        )

    except BaseException:
        return None


def convert_android_location(
    location: Any,
) -> GPSPoint:
    """
    Преобразует android.location.Location
    в доменную модель GPSPoint.
    """

    latitude = float(
        location.getLatitude()
    )
    longitude = float(
        location.getLongitude()
    )

    altitude = get_optional_location_value(
        location,
        "hasAltitude",
        "getAltitude",
    )

    speed = get_optional_location_value(
        location,
        "hasSpeed",
        "getSpeed",
    )

    bearing = get_optional_location_value(
        location,
        "hasBearing",
        "getBearing",
    )

    accuracy = get_optional_location_value(
        location,
        "hasAccuracy",
        "getAccuracy",
    )

    return GPSPoint(
        latitude=latitude,
        longitude=longitude,
        altitude=altitude,
        speed=speed,
        bearing=bearing,
        accuracy=accuracy,
    )


class AndroidLocationListener(
    PythonJavaClass
):
    """
    Нативная реализация Android LocationListener.

    В конструктор PythonJavaClass нельзя передавать
    именованные аргументы. Поэтому обработчики
    устанавливаются отдельным методом configure().
    """

    __javainterfaces__ = [
        "android/location/LocationListener",
    ]

    # LocationListener — системный Android-интерфейс.
    __javacontext__ = "system"

    _on_location: (
        Callable[[Any], None] | None
    ) = None

    _on_status: (
        Callable[[str], None] | None
    ) = None

    def configure(
        self,
        on_location: Callable[[Any], None],
        on_status: Callable[[str], None],
    ) -> None:
        self._on_location = on_location
        self._on_status = on_status

        log(
            "BACKGROUND LOCATION LISTENER CONFIGURED"
        )

    def _emit_location(
        self,
        location: Any,
    ) -> None:
        if location is None:
            return

        callback = self._on_location

        if callback is None:
            log(
                "BACKGROUND LOCATION CALLBACK "
                "IS NOT CONFIGURED"
            )
            return

        try:
            callback(location)

        except BaseException as error:
            log(
                "BACKGROUND LOCATION CALLBACK ERROR: "
                f"{type(error).__name__}: {error}"
            )
            traceback.print_exc()

    @java_method(
        "(Landroid/location/Location;)V"
    )
    def onLocationChanged(
        self,
        location: Any,
    ) -> None:
        """
        Стандартный callback с одной Location.
        """

        self._emit_location(
            location
        )

    @java_method(
        "(Ljava/util/List;)V",
        name="onLocationChanged",
    )
    def onLocationChangedList(
        self,
        locations: Any,
    ) -> None:
        """
        Callback новых Android со списком Location.
        """

        if locations is None:
            return

        try:
            locations_count = int(
                locations.size()
            )

            for index in range(
                locations_count
            ):
                location = locations.get(
                    index
                )

                self._emit_location(
                    location
                )

        except BaseException as error:
            log(
                "BACKGROUND LOCATION LIST ERROR: "
                f"{type(error).__name__}: {error}"
            )
            traceback.print_exc()

    @java_method(
        "(Ljava/lang/String;)V"
    )
    def onProviderEnabled(
        self,
        provider: Any,
    ) -> None:
        callback = self._on_status

        if callback is None:
            return

        callback(
            f"provider enabled: {provider}"
        )

    @java_method(
        "(Ljava/lang/String;)V"
    )
    def onProviderDisabled(
        self,
        provider: Any,
    ) -> None:
        callback = self._on_status

        if callback is None:
            return

        callback(
            f"provider disabled: {provider}"
        )

    @java_method(
        "(Ljava/lang/String;"
        "ILandroid/os/Bundle;)V"
    )
    def onStatusChanged(
        self,
        provider: Any,
        status: int,
        extras: Any,
    ) -> None:
        del extras

        callback = self._on_status

        if callback is None:
            return

        callback(
            "provider status changed: "
            f"provider={provider}, "
            f"status={status}"
        )


def get_android_service_context() -> Any:
    """
    Получает Context текущего Python foreground service.
    """

    PythonService = autoclass(
        "org.kivy.android.PythonService"
    )

    for attempt in range(50):
        service_context = (
            PythonService.mService
        )

        if service_context is not None:
            return service_context

        if attempt % 10 == 0:
            log(
                "BACKGROUND WAITING FOR "
                "PYTHON SERVICE CONTEXT"
            )

        time.sleep(0.1)

    raise RuntimeError(
        "PythonService.mService "
        "не инициализирован"
    )


def check_location_permissions(
    service_context: Any,
) -> None:
    """
    Проверяет разрешения на геолокацию.

    Разрешения должны быть запрошены
    из основной Activity до запуска service.
    """

    PackageManager = autoclass(
        "android.content.pm.PackageManager"
    )

    fine_permission = (
        service_context.checkSelfPermission(
            "android.permission."
            "ACCESS_FINE_LOCATION"
        )
    )

    coarse_permission = (
        service_context.checkSelfPermission(
            "android.permission."
            "ACCESS_COARSE_LOCATION"
        )
    )

    fine_granted = (
        fine_permission
        == PackageManager.PERMISSION_GRANTED
    )

    coarse_granted = (
        coarse_permission
        == PackageManager.PERMISSION_GRANTED
    )

    log(
        "BACKGROUND PERMISSIONS: "
        f"fine={fine_granted}, "
        f"coarse={coarse_granted}"
    )

    if not fine_granted and not coarse_granted:
        raise PermissionError(
            "Нет разрешения "
            "ACCESS_FINE_LOCATION или "
            "ACCESS_COARSE_LOCATION"
        )


def acquire_wake_lock(
    service_context: Any,
) -> Any:
    """
    Захватывает PARTIAL_WAKE_LOCK, чтобы CPU
    продолжал работать при выключенном экране.
    """

    Context = autoclass(
        "android.content.Context"
    )

    PowerManager = autoclass(
        "android.os.PowerManager"
    )

    power_manager = (
        service_context.getSystemService(
            Context.POWER_SERVICE
        )
    )

    if power_manager is None:
        raise RuntimeError(
            "Не удалось получить PowerManager"
        )

    wake_lock = power_manager.newWakeLock(
        PowerManager.PARTIAL_WAKE_LOCK,
        "GPSTracker:BackgroundTracking",
    )

    wake_lock.setReferenceCounted(False)
    wake_lock.acquire()

    log(
        "BACKGROUND WAKE LOCK ACQUIRED"
    )

    return wake_lock


def release_wake_lock(
    wake_lock: Any,
) -> None:
    if wake_lock is None:
        return

    try:
        if wake_lock.isHeld():
            wake_lock.release()

        log(
            "BACKGROUND WAKE LOCK RELEASED"
        )

    except BaseException as error:
        log(
            "BACKGROUND WAKE LOCK RELEASE ERROR: "
            f"{type(error).__name__}: {error}"
        )
        traceback.print_exc()


def start_location_updates(
    service_context: Any,
    listener: AndroidLocationListener,
    min_time: int,
    min_distance: float,
) -> Any:
    """
    Подписывает listener на доступные
    Android-провайдеры геолокации.
    """

    Context = autoclass(
        "android.content.Context"
    )

    LocationManager = autoclass(
        "android.location.LocationManager"
    )

    Looper = autoclass(
        "android.os.Looper"
    )

    location_manager = (
        service_context.getSystemService(
            Context.LOCATION_SERVICE
        )
    )

    if location_manager is None:
        raise RuntimeError(
            "Не удалось получить LocationManager"
        )

    main_looper = (
        Looper.getMainLooper()
    )

    providers = [
        LocationManager.GPS_PROVIDER,
        LocationManager.NETWORK_PROVIDER,
    ]

    started_providers: list[str] = []

    for provider in providers:
        try:
            provider_enabled = bool(
                location_manager.isProviderEnabled(
                    provider
                )
            )

            log(
                "BACKGROUND PROVIDER: "
                f"{provider}, "
                f"enabled={provider_enabled}"
            )

            if not provider_enabled:
                continue

            location_manager.requestLocationUpdates(
                provider,
                int(min_time),
                float(min_distance),
                listener,
                main_looper,
            )

            started_providers.append(
                str(provider)
            )

            log(
                "BACKGROUND PROVIDER STARTED: "
                f"{provider}"
            )

        except BaseException as error:
            log(
                "BACKGROUND PROVIDER START ERROR: "
                f"provider={provider}, "
                f"{type(error).__name__}: {error}"
            )
            traceback.print_exc()

    if not started_providers:
        raise RuntimeError(
            "Не удалось запустить ни одного "
            "провайдера геолокации"
        )

    log(
        "BACKGROUND LOCATION UPDATES STARTED: "
        f"{started_providers}"
    )

    return location_manager


def stop_location_updates(
    location_manager: Any,
    listener: AndroidLocationListener | None,
) -> None:
    if location_manager is None:
        return

    if listener is None:
        return

    try:
        location_manager.removeUpdates(
            listener
        )

        log(
            "BACKGROUND LOCATION UPDATES STOPPED"
        )

    except BaseException as error:
        log(
            "BACKGROUND LOCATION STOP ERROR: "
            f"{type(error).__name__}: {error}"
        )
        traceback.print_exc()


def stop_android_service(
    service_context: Any,
) -> None:
    """
    Останавливает Java-часть foreground service.
    """

    if service_context is None:
        return

    try:
        log(
            "BACKGROUND STOPPING JAVA SERVICE"
        )

        # Даём logcat получить последние строки.
        time.sleep(0.2)

        service_context.stopSelf()

    except BaseException as error:
        log(
            "BACKGROUND STOP SELF ERROR: "
            f"{type(error).__name__}: {error}"
        )
        traceback.print_exc()


def read_tracking_state(
    state_store: TrackingStateStore,
) -> dict[str, Any] | None:
    try:
        state = state_store.read()

        if state is None:
            return None

        if not isinstance(
            state,
            dict,
        ):
            raise TypeError(
                "tracking_state должен быть словарём"
            )

        return state

    except BaseException as error:
        log(
            "BACKGROUND STATE READ ERROR: "
            f"{type(error).__name__}: {error}"
        )
        traceback.print_exc()

        return None


def mark_tracking_inactive(
    state_path: Path,
    run_id: int,
) -> None:
    """
    При фатальной ошибке помечает текущую пробежку
    неактивной, если run_id не изменился.
    """

    try:
        if not state_path.exists():
            return

        with state_path.open(
            "r",
            encoding="utf-8",
        ) as state_file:
            state = json.load(
                state_file
            )

        if not isinstance(
            state,
            dict,
        ):
            return

        state_run_id = int(
            state.get(
                "run_id",
                -1,
            )
        )

        if state_run_id != run_id:
            return

        state["active"] = False

        temporary_path = (
            state_path.with_suffix(
                state_path.suffix + ".tmp"
            )
        )

        with temporary_path.open(
            "w",
            encoding="utf-8",
        ) as state_file:
            json.dump(
                state,
                state_file,
                ensure_ascii=False,
                indent=2,
            )

            state_file.write("\n")
            state_file.flush()

            os.fsync(
                state_file.fileno()
            )

        temporary_path.replace(
            state_path
        )

        log(
            "BACKGROUND STATE MARKED INACTIVE"
        )

    except BaseException as error:
        log(
            "BACKGROUND STATE UPDATE ERROR: "
            f"{type(error).__name__}: {error}"
        )
        traceback.print_exc()


def main() -> None:
    log(
        "BACKGROUND ENTRYPOINT STARTED"
    )

    raw_argument = os.environ.get(
        "PYTHON_SERVICE_ARGUMENT",
        "",
    )

    log(
        "BACKGROUND ARGUMENT: "
        f"{raw_argument!r}"
    )

    if not raw_argument:
        raise RuntimeError(
            "PYTHON_SERVICE_ARGUMENT отсутствует"
        )

    try:
        argument = json.loads(
            raw_argument
        )

    except json.JSONDecodeError as error:
        raise RuntimeError(
            "Некорректный JSON в "
            "PYTHON_SERVICE_ARGUMENT"
        ) from error

    if not isinstance(
        argument,
        dict,
    ):
        raise RuntimeError(
            "PYTHON_SERVICE_ARGUMENT "
            "должен содержать JSON-объект"
        )

    required_fields = {
        "run_id",
        "database_path",
        "state_path",
    }

    missing_fields = (
        required_fields
        - set(argument.keys())
    )

    if missing_fields:
        raise RuntimeError(
            "Не переданы параметры service: "
            f"{sorted(missing_fields)}"
        )

    run_id = int(
        argument["run_id"]
    )

    database_path = Path(
        argument["database_path"]
    )

    state_path = Path(
        argument["state_path"]
    )

    min_time = int(
        argument.get(
            "min_time",
            1000,
        )
    )

    min_distance = float(
        argument.get(
            "min_distance",
            1.0,
        )
    )

    log(
        "BACKGROUND PARAMETERS OK: "
        f"run_id={run_id}, "
        f"database={database_path}, "
        f"state={state_path}, "
        f"min_time={min_time}, "
        f"min_distance={min_distance}"
    )

    state_store = TrackingStateStore(
        state_path
    )

    # Foreground service работает в отдельном
    # Python-процессе, поэтому БД настраивается снова.
    configure_database(
        database_path
    )

    create_tables()

    repository = RunRepository()

    log(
        "BACKGROUND DATABASE CONFIGURED"
    )

    service_context: Any = None
    wake_lock: Any = None
    location_manager: Any = None

    listener: (
        AndroidLocationListener | None
    ) = None

    fatal_error = False

    last_point: GPSPoint | None = None
    last_accepted_at: float | None = None

    good_fix_count = 0
    gps_ready = False

    def handle_provider_status(
        status: str,
    ) -> None:
        log(
            "BACKGROUND GPS STATUS: "
            f"{status}"
        )

    def handle_android_location(
        android_location: Any,
    ) -> None:
        nonlocal last_point
        nonlocal last_accepted_at
        nonlocal good_fix_count
        nonlocal gps_ready

        try:
            point = convert_android_location(
                android_location
            )

            accuracy = point.accuracy

            log(
                "BACKGROUND RAW LOCATION: "
                f"lat={point.latitude}, "
                f"lon={point.longitude}, "
                f"accuracy={accuracy}, "
                f"speed={point.speed}"
            )

            if accuracy is None:
                log(
                    "BACKGROUND POINT REJECTED: "
                    "accuracy отсутствует"
                )
                return

            if not gps_ready:
                if accuracy > START_ACCURACY:
                    good_fix_count = 0

                    log(
                        "BACKGROUND GPS WAITING: "
                        f"accuracy={accuracy:.1f}, "
                        f"required<="
                        f"{START_ACCURACY:.1f}"
                    )
                    return

                good_fix_count += 1

                log(
                    "BACKGROUND GOOD FIX: "
                    f"{good_fix_count}/"
                    f"{REQUIRED_GOOD_FIXES}"
                )

                if (
                    good_fix_count
                    < REQUIRED_GOOD_FIXES
                ):
                    return

                gps_ready = True

                log(
                    "BACKGROUND GPS READY"
                )

            if accuracy > MAX_ACCURACY:
                log(
                    "BACKGROUND POINT REJECTED: "
                    f"accuracy={accuracy:.1f}"
                )
                return

            received_at = time.monotonic()

            if last_point is not None:
                distance = calculate_distance(
                    last_point,
                    point,
                )

                previous_accuracy = float(
                    last_point.accuracy
                    or 0.0
                )

                required_distance = max(
                    MIN_ROUTE_DISTANCE,
                    max(
                        accuracy,
                        previous_accuracy,
                    )
                    * 0.5,
                )

                if distance < required_distance:
                    log(
                        "BACKGROUND POINT SKIPPED: "
                        f"distance={distance:.1f}, "
                        f"required="
                        f"{required_distance:.1f}"
                    )
                    return

                if last_accepted_at is not None:
                    elapsed = (
                        received_at
                        - last_accepted_at
                    )

                    if elapsed <= 0:
                        return

                    calculated_speed = (
                        distance / elapsed
                    )

                    if (
                        calculated_speed
                        > MAX_RUNNING_SPEED
                    ):
                        log(
                            "BACKGROUND POINT REJECTED: "
                            "calculated_speed="
                            f"{calculated_speed:.1f} m/s"
                        )
                        return

            repository.add_point(
                run_id=run_id,
                point=point,
            )

            last_point = point
            last_accepted_at = received_at

            log(
                "BACKGROUND GPS POINT SAVED: "
                f"run_id={run_id}, "
                f"lat={point.latitude}, "
                f"lon={point.longitude}, "
                f"accuracy={accuracy}"
            )

        except BaseException as error:
            log(
                "BACKGROUND GPS CALLBACK ERROR: "
                f"{type(error).__name__}: {error}"
            )
            traceback.print_exc()

    try:
        service_context = (
            get_android_service_context()
        )

        log(
            "BACKGROUND SERVICE CONTEXT READY"
        )

        check_location_permissions(
            service_context
        )

        wake_lock = acquire_wake_lock(
            service_context
        )

        # ВАЖНО:
        # PythonJavaClass создаётся без аргументов.
        listener = AndroidLocationListener()

        listener.configure(
            handle_android_location,
            handle_provider_status,
        )

        log(
            "BACKGROUND LOCATION LISTENER CREATED"
        )

        location_manager = (
            start_location_updates(
                service_context=service_context,
                listener=listener,
                min_time=min_time,
                min_distance=min_distance,
            )
        )

        log(
            "BACKGROUND TRACKING STARTED: "
            f"run_id={run_id}"
        )

        missing_state_started_at: (
            float | None
        ) = None

        while True:
            state = read_tracking_state(
                state_store
            )

            if state is None:
                if missing_state_started_at is None:
                    missing_state_started_at = (
                        time.monotonic()
                    )

                    log(
                        "BACKGROUND STATE FILE "
                        "NOT FOUND, WAITING"
                    )

                missing_duration = (
                    time.monotonic()
                    - missing_state_started_at
                )

                if (
                    missing_duration
                    >= STATE_FILE_WAIT_SECONDS
                ):
                    log(
                        "BACKGROUND SERVICE STOP: "
                        "state-файл отсутствует"
                    )
                    break

                time.sleep(
                    STATE_CHECK_INTERVAL_SECONDS
                )
                continue

            missing_state_started_at = None

            active = bool(
                state.get(
                    "active",
                    False,
                )
            )

            state_run_id = int(
                state.get(
                    "run_id",
                    -1,
                )
            )

            if not active:
                log(
                    "BACKGROUND SERVICE STOP: "
                    "active=false"
                )
                break

            if state_run_id != run_id:
                log(
                    "BACKGROUND SERVICE STOP: "
                    "run_id changed: "
                    f"state={state_run_id}, "
                    f"service={run_id}"
                )
                break

            time.sleep(
                STATE_CHECK_INTERVAL_SECONDS
            )

    except BaseException as error:
        fatal_error = True

        log(
            "BACKGROUND FATAL ERROR: "
            f"{type(error).__name__}: {error}"
        )
        traceback.print_exc()

        # Даём logcat время получить traceback.
        time.sleep(1.0)

    finally:
        stop_location_updates(
            location_manager=location_manager,
            listener=listener,
        )

        release_wake_lock(
            wake_lock
        )

        if fatal_error:
            mark_tracking_inactive(
                state_path=state_path,
                run_id=run_id,
            )

        log(
            "BACKGROUND TRACKING STOPPED: "
            f"run_id={run_id}, "
            f"fatal_error={fatal_error}"
        )

        stop_android_service(
            service_context
        )


if __name__ == "__main__":
    log(
        "BACKGROUND CALLING MAIN"
    )

    try:
        main()

    except BaseException as error:
        log(
            "BACKGROUND UNHANDLED ERROR: "
            f"{type(error).__name__}: {error}"
        )
        traceback.print_exc()
        time.sleep(3)
        raise