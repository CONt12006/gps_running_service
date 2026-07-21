from datetime import datetime

from sqlalchemy import select, delete, func

from math import asin, cos, radians, sin, sqrt

from src.db.database import get_session
from src.db.models import Runs, RunPoint
from src.domain.gps_point import GPSPoint


class RunRepository:
    def __init__(self):
        pass

    def create_run(self, started_at: datetime | None = None) -> int:
        """Создать новую пробежку и вернуть её id"""
        with get_session() as session:
            try:
                run = Runs(started_at = started_at or datetime.now())
                session.add(run)
                session.commit()
                session.refresh(run)

                return run.id
            
            except Exception:
                session.rollback()
                raise

    
    def add_point(self, run_id: int, point: GPSPoint) -> int:
        """Добавить GPS-точку к пробежке"""
        with get_session() as session:
            try:
                run_point = RunPoint(
                    run_id = run_id,
                    latitude = point.latitude,
                    longitude = point.longitude,
                    altitude = point.altitude,
                    speed = point.speed,
                    bearing = point.bearing,
                    accuracy = point.accuracy
                )
                session.add(run_point)
                session.commit()
                session.refresh(run_point)

                return run_point.id
            
            except Exception:
                session.rollback()
                raise

    
    def finish_run(self, run_id: int, distance: float, duration: int, avg_speed: float, finished_at: datetime | None = None):
        """Завершить пробежку и сохранить итоговые показатели"""
        with get_session() as session:
            try:
                run = session.get(Runs, run_id)

                run.finished_at = finished_at or datetime.now()
                run.distance = distance
                run.duration = duration
                run.avg_speed = avg_speed

                session.commit()
            
            except Exception:
                session.rollback()
                raise

    
    def get_run(self, run_id: int):
        """Получить пробежку по id"""
        with get_session() as session:
            run = session.get(Runs, run_id)

            return run


    def get_all_runs(self) -> list[Runs]:
        """Получить все пробежки."""

        with get_session() as session:
            statement = (
                select(Runs)
                .order_by(Runs.started_at.desc())
            )

            return list(
                session.scalars(statement).all()
            )


    def get_finished_runs(self) -> list[Runs]:
        """Получить только завершённые пробежки."""

        with get_session() as session:
            statement = (
                select(Runs)
                .where(Runs.finished_at.is_not(None))
                .order_by(Runs.started_at.desc())
            )

            runs = list(
                session.scalars(statement).all()
            )

            for run in runs:
                session.expunge(run)

            return runs

    def get_run_points(self, run_id: int) -> list[RunPoint]:
        """Получить точки конкретной пробежки"""
        with get_session() as session:
            statement = (
                select(RunPoint)
                .where(RunPoint.run_id == run_id)
                .order_by(RunPoint.id.asc())
            )

            return list(
                session.scalars(statement).all()
            )


    def get_run_points_after_id(
        self,
        run_id: int,
        last_point_id: int,
    ) -> list[RunPoint]:
        """
        Возвращает только точки, которые UI
        ещё не отобразил.
        """

        with get_session() as session:
            statement = (
                select(RunPoint)
                .where(
                    RunPoint.run_id == run_id,
                    RunPoint.id > last_point_id,
                )
                .order_by(RunPoint.id.asc())
            )

            points = list(
                session.scalars(statement).all()
            )

            for point in points:
                session.expunge(point)

            return points
        

    def finalize_run_from_points(
        self,
        run_id: int,
        finished_at: datetime | None = None,
    ) -> None:
        completed_at = finished_at or datetime.now()

        with get_session() as session:
            try:
                run = session.get(Runs, run_id)

                if run is None:
                    raise ValueError(
                        f"Пробежка id={run_id} не найдена"
                    )

                statement = (
                    select(RunPoint)
                    .where(RunPoint.run_id == run_id)
                    .order_by(RunPoint.id.asc())
                )

                points = list(
                    session.scalars(statement).all()
                )

                distance_meters = 0.0

                for first, second in zip(
                    points,
                    points[1:],
                ):
                    distance_meters += (
                        self._calculate_distance(
                            first.latitude,
                            first.longitude,
                            second.latitude,
                            second.longitude,
                        )
                    )

                duration_seconds = max(
                    0,
                    int(
                        (
                            completed_at
                            - run.started_at
                        ).total_seconds()
                    ),
                )

                if duration_seconds == 0:
                    average_speed_kmh = 0.0
                else:
                    average_speed_kmh = (
                        (distance_meters / 1000.0)
                        / (duration_seconds / 3600.0)
                    )

                run.finished_at = completed_at
                run.distance = distance_meters
                run.duration = duration_seconds
                run.avg_speed = average_speed_kmh

                session.commit()

            except Exception:
                session.rollback()
                raise

    def delete_run(self, run_id: int) -> None:
        with get_session() as session:
            try:
                run = session.get(
                    Runs,
                    run_id,
                )

                if run is None:
                    return

                session.delete(run)
                session.commit()

            except Exception:
                session.rollback()
                raise

    def count_runs(self) -> int:
        with get_session() as session:
            statement = select(
                func.count(Runs.id)
            )

            result = session.scalar(statement)

            return int(result or 0)
        
    def delete_all_runs(self) -> None:
        with get_session() as session:
            try:
                session.execute(
                    delete(Runs)
                )

                session.commit()

            except Exception:
                session.rollback()
                raise


    @staticmethod
    def _calculate_distance(
        latitude_1: float,
        longitude_1: float,
        latitude_2: float,
        longitude_2: float,
    ) -> float:
        earth_radius = 6_371_000.0

        lat_1 = radians(latitude_1)
        lat_2 = radians(latitude_2)

        latitude_delta = radians(
            latitude_2 - latitude_1
        )
        longitude_delta = radians(
            longitude_2 - longitude_1
        )

        haversine = (
            sin(latitude_delta / 2.0) ** 2
            + cos(lat_1)
            * cos(lat_2)
            * sin(longitude_delta / 2.0) ** 2
        )

        return (
            earth_radius
            * 2.0
            * asin(sqrt(haversine))
        )