from datetime import datetime

from sqlalchemy import Integer, ForeignKey, DateTime, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base


class Runs(Base):
    __tablename__ = "runs"

    id: Mapped[int] = mapped_column(Integer, primary_key = True, autoincrement=True)
    started_at: Mapped[datetime] = mapped_column(DateTime)
    finished_at: Mapped[datetime] = mapped_column(DateTime)
    distance: Mapped[float] = mapped_column(Float)
    duration: Mapped[int] = mapped_column(Integer)
    avg_speed: Mapped[float] = mapped_column(Float)

    point: Mapped[list["RunPoint"]] = relationship(back_populates = "run")


class RunPoint(Base):
    __tablename__ = "run_points"

    id: Mapped[int] = mapped_column(Integer, primary_key = True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("runs.id"))
    latitude: Mapped[float] = mapped_column(Float)    
    longitude: Mapped[float] = mapped_column(Float)
    altitude: Mapped[float | None] = mapped_column(Float, nullable = True)
    speed: Mapped[float | None] = mapped_column(Float, nullable = True)
    bearing: Mapped[float | None] = mapped_column(Float, nullable = True)
    accuracy: Mapped[float | None] = mapped_column(Float, nullable = True)

    run: Mapped["Runs"] = relationship(back_populates = "point")