from datetime import datetime

from sqlalchemy import Integer, ForeignKey, DateTime, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base


class Runs(Base):
    __tablename__ = "runs"

    id: Mapped[int] = mapped_column(Integer, primary_key = True, autoincrement=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)
    finished_at: Mapped[datetime] = mapped_column(DateTime, nullable = True, default = None)
    distance: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    duration: Mapped[int] = mapped_column(Integer, nullable=False, default=0.0)
    avg_speed: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    point: Mapped[list["RunPoint"]] = relationship(back_populates = "run", cascade="all, delete-orphan", passive_deletes=True)


class RunPoint(Base):
    __tablename__ = "run_points"

    id: Mapped[int] = mapped_column(Integer, primary_key = True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("runs.id", ondelete="CASCADE"), nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)    
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    altitude: Mapped[float | None] = mapped_column(Float, nullable = True, default=None)
    speed: Mapped[float | None] = mapped_column(Float, nullable = True, default=None)
    bearing: Mapped[float | None] = mapped_column(Float, nullable = True, default=None)
    accuracy: Mapped[float | None] = mapped_column(Float, nullable = True, default=None)

    run: Mapped["Runs"] = relationship(back_populates = "point")