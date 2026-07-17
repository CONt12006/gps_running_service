from datetime import datetime

from sqlalchemy import select, delete, func

from src.db.database import SessionLocal
from src.db.models import Runs, RunPoint
from src.domain.gps_point import GPSPoint


class RunRepository:
    def __init__(self):
        pass

    def create_run(self, started_at: datetime | None = None) -> int:
        """Создать новую пробежку и вернуть её id"""
        with SessionLocal() as session:
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
        with SessionLocal() as session:
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
                session.refresh()
                raise

    
    def finish_run(self, run_id: int, distance: float, duration: int, avg_speed: float, finished_at: datetime | None = None):
        """Завершить пробежку и сохранить итоговые показатели"""
        with SessionLocal() as session:
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
        with SessionLocal() as session:
            run = session.get(Runs, run_id)

            return run


    def get_all_runs(self) -> list[Runs]:
        """Получить все пробежки."""

        with SessionLocal() as session:
            statement = (
                select(Runs)
                .order_by(Runs.started_at.desc())
            )

            return list(
                session.scalars(statement).all()
            )


    def get_finished_runs(self) -> list[Runs]:
        """Получить только завершённые пробежки."""

        with SessionLocal() as session:
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
        with SessionLocal() as session:
            statement = (
                select(RunPoint)
                .where(RunPoint.run_id == run_id)
                .order_by(RunPoint.recorded_at.asc())
            )

        return list(
            session.scalars(statement).all()
        )


    def delete_run(self, run_id: int) -> None:
        """Удалить пробежку"""
        with SessionLocal() as session:
            try:
                run = session.get(Runs, run_id)

                session.delete(run)
                session.commit()
                session.refresh()

            except Exception:
                session.rollback()
                raise

    def count_runs(self) -> int:
        with SessionLocal() as session:
            statement = select(
                func.count(Runs.id)
            )

            result = session.scalar(statement)

            return int(result or 0)
        
    def delete_all_runs(self) -> None:
        with SessionLocal() as session:
            try:
                session.execute(
                    delete(Runs)
                )

                session.commit()

            except Exception:
                session.rollback()
                raise