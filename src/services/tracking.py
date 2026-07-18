from __future__ import annotations

import json
import os
import time
import traceback
from math import asin, cos, radians, sin, sqrt
from pathlib import Path

from plyer import gps

from src.db.database import (
    configure_database,
    create_tables,
)
from src.db.run_repository import RunRepository
from src.domain.gps_point import GPSPoint
from src.services.tracking_state_store import (
    TrackingStateStore,
)


START_ACCURACY = 15.0
MAX_ACCURACY = 17.0
REQUIRED_GOOD_FIXES = 3

MIN_ROUTE_DISTANCE = 5.0
MAX_RUNNING_SPEED = 8.0


def optional_float(value) -> float | None:
    if value is None:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def calculate_distance(
    first: GPSPoint,
    second: GPSPoint,
) -> float:
    earth_radius = 6_371_000.0

    latitude_1 = radians(first.latitude)
    latitude_2 = radians(second.latitude)

    latitude_delta = radians(
        second.latitude - first.latitude
    )
    longitude_delta = radians(
        second.longitude - first.longitude
    )

    haversine = (
        sin(latitude_delta / 2.0) ** 2
        + cos(latitude_1)
        * cos(latitude_2)
        * sin(longitude_delta / 2.0) ** 2
    )

    return (
        earth_radius
        * 2.0
        * asin(sqrt(haversine))
    )


def main() -> None:
    raw_argument = os.environ.get(
        "PYTHON_SERVICE_ARGUMENT",
        "{}",
    )

    argument = json.loads(raw_argument)

    run_id = int(argument["run_id"])
    database_path = Path(argument["database_path"])
    state_path = Path(argument["state_path"])

    min_time = int(
        argument.get("min_time", 1000)
    )
    min_distance = float(
        argument.get("min_distance", 1.0)
    )

    state_store = TrackingStateStore(state_path)

    # У service свой Python-процесс,
    # поэтому SQLAlchemy нужно настроить ещё раз.
    configure_database(database_path)
    create_tables()

    repository = RunRepository()

    last_point: GPSPoint | None = None
    last_accepted_at: float | None = None

    good_fix_count = 0
    gps_ready = False

    print(
        "BACKGROUND TRACKING STARTED: "
        f"run_id={run_id}"
    )

    def on_location(**kwargs) -> None:
        nonlocal last_point
        nonlocal last_accepted_at
        nonlocal good_fix_count
        nonlocal gps_ready

        try:
            latitude = optional_float(
                kwargs.get("lat")
            )
            longitude = optional_float(
                kwargs.get("lon")
            )
            accuracy = optional_float(
                kwargs.get("accuracy")
            )

            if latitude is None or longitude is None:
                return

            if accuracy is None:
                print(
                    "BACKGROUND POINT REJECTED: "
                    "accuracy отсутствует"
                )
                return

            # Сначала ждём несколько стабильных GPS-фиксов.
            if not gps_ready:
                if accuracy > START_ACCURACY:
                    good_fix_count = 0
                    print(
                        "BACKGROUND GPS WAITING: "
                        f"accuracy={accuracy:.1f}"
                    )
                    return

                good_fix_count += 1

                print(
                    "BACKGROUND GOOD FIX: "
                    f"{good_fix_count}/"
                    f"{REQUIRED_GOOD_FIXES}"
                )

                if good_fix_count < REQUIRED_GOOD_FIXES:
                    return

                gps_ready = True

            if accuracy > MAX_ACCURACY:
                print(
                    "BACKGROUND POINT REJECTED: "
                    f"accuracy={accuracy:.1f}"
                )
                return

            point = GPSPoint(
                latitude=latitude,
                longitude=longitude,
                altitude=optional_float(
                    kwargs.get("altitude")
                ),
                speed=optional_float(
                    kwargs.get("speed")
                ),
                bearing=optional_float(
                    kwargs.get("bearing")
                ),
                accuracy=accuracy,
            )

            received_at = time.monotonic()

            if last_point is not None:
                distance = calculate_distance(
                    last_point,
                    point,
                )

                previous_accuracy = float(
                    last_point.accuracy or 0.0
                )

                required_distance = max(
                    MIN_ROUTE_DISTANCE,
                    max(
                        accuracy,
                        previous_accuracy,
                    ) * 0.5,
                )

                if distance < required_distance:
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
                        print(
                            "BACKGROUND POINT REJECTED: "
                            f"speed={calculated_speed:.1f}"
                        )
                        return

            repository.add_point(
                run_id=run_id,
                point=point,
            )

            last_point = point
            last_accepted_at = received_at

            print(
                "BACKGROUND GPS POINT SAVED: "
                f"run_id={run_id}, "
                f"lat={latitude}, "
                f"lon={longitude}, "
                f"accuracy={accuracy}"
            )

        except Exception as error:
            print(
                "BACKGROUND GPS ERROR: "
                f"{error}\n"
                f"{traceback.format_exc()}"
            )

    def on_status(
        status_type,
        status,
    ) -> None:
        print(
            "BACKGROUND GPS STATUS: "
            f"{status_type}: {status}"
        )

    try:
        gps.configure(
            on_location=on_location,
            on_status=on_status,
        )

        gps.start(
            minTime=min_time,
            minDistance=min_distance,
        )

        while True:
            state = state_store.read()

            if state is None:
                print(
                    "BACKGROUND SERVICE: "
                    "state-файл удалён"
                )
                break

            if not state.get("active", False):
                print(
                    "BACKGROUND SERVICE: "
                    "получена команда остановки"
                )
                break

            if int(state.get("run_id", -1)) != run_id:
                print(
                    "BACKGROUND SERVICE: "
                    "изменилась активная пробежка"
                )
                break

            time.sleep(1.0)

    except Exception as error:
        print(
            "BACKGROUND SERVICE ERROR: "
            f"{error}\n"
            f"{traceback.format_exc()}"
        )

    finally:
        try:
            gps.stop()
        except Exception:
            pass

        print(
            "BACKGROUND TRACKING STOPPED: "
            f"run_id={run_id}"
        )

        try:
            from jnius import autoclass

            python_service = autoclass(
                "org.kivy.android.PythonService"
            )

            if python_service.mService is not None:
                python_service.mService.stopSelf()

        except Exception:
            pass


if __name__ == "__main__":
    main()