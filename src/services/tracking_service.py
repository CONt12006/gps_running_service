from datetime import datetime

from math import asin, cos, radians, sin, sqrt

from src.db.run_repository import RunRepository
from src.domain.gps_point import GPSPoint


class TrackingService:
    def __init__(self, repository: RunRepository) -> None:
        self._repository = repository
        self._current_run_id: int | None = None
        self._started_at: datetime | None = None
        self._last_point: GPSPoint | None = None
        self._distance_meters = 0.0
        self._points_count = 0
        self._is_paused = False

    def _is_running(self) -> bool:
        return self._current_run_id is not None
    
    def is_paused(self) -> bool:
        return self._is_paused
    
    def _calculate_distance(self, first: GPSPoint, second: GPSPoint) -> float:
        earth_radius_meters = 6_371_000

        latitude_1 = radians(first.latitude)
        latitude_2 = radians(second.latitude)

        latitude_delta = radians(
            second.latitude - first.latitude
        )
        longitude_delta = radians(
            second.longitude - first.longitude
        )

        haversine = (
            sin(latitude_delta / 2) ** 2
            + cos(latitude_1)
            * cos(latitude_2)
            * sin(longitude_delta / 2) ** 2
        )

        angular_distance = 2 * asin(
            sqrt(haversine)
        )

        return earth_radius_meters * angular_distance


    def _is_point_acceptable(
        self,
        point: GPSPoint,
    ) -> bool:
        if point.accuracy is not None and point.accuracy > 50:
            return False

        return True
    

    def handle_gps_point(self, point: GPSPoint) -> bool:
        if not self._is_running:
            return False

        if self._is_paused:
            return False

        if not self._is_point_acceptable(point):
            return False

        if self._last_point is not None:
            segment_distance = self._calculate_distance(
                self._last_point,
                point,
            )

            self._distance_meters += segment_distance

        self._repository.add_point(
            run_id=self._current_run_id,
            point=point,
        )

        self._last_point = point
        self._points_count += 1

        return True


    def _duration_seconds(self) -> int:
        return int((datetime.now() - self._started_at).total_seconds())

    def _average_speed_kmh(self) -> float:
        if self._duration_seconds() == 0:
            return 0
        return (self._distance_meters / 1000) / (self._duration_seconds() / 3600)


    def start_running(self):
        self._started_at = datetime.now()
        run_id = self._repository.create_run(self._started_at)

        self._current_run_id = run_id
        self._started_at = self._started_at
        self._last_point = None
        self._distance_meters = 0.0
        self._points_count = 0
        self._is_paused = False

        return run_id
    
    def pause_running(self):
        self._is_paused = True
        self._last_point = None
    
    def resume_running(self):
        self._is_paused = False
        self._last_point = None

    
    def finish_running(self):
        self._repository.finish_run(
            self._current_run_id,
            self._distance_meters,
            self._duration_seconds(),
            self._average_speed_kmh(),
            datetime.now()
        )
        
        self._reset()


    def _reset(self) -> None:
        self._current_run_id = None
        self._started_at = None
        self._last_point = None
        self._distance_meters = 0.0
        self._points_count = 0
        self._is_paused = False

    