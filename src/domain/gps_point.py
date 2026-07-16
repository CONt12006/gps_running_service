from dataclasses import dataclass


@dataclass(frozen=True)
class GPSPoint:
    """Класс GPS точки"""
    latitude: float                 # ширина
    longitude: float                # долгота 
    altitude: float | None = None   # высота над уровнем моря
    speed: float | None = None      # скорость
    bearing: float | None = None    # азимут(направление движения пользователя)
    accuracy: float | None = None   # точность измерений