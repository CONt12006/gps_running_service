# GPS Tracker

Мобильное Android-приложение для записи пробежек, фонового GPS-трекинга, построения маршрутов и просмотра истории тренировок.

> **Статус проекта:** приложение проходит закрытое тестирование в Google Play перед публичной публикацией.

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Kivy](https://img.shields.io/badge/Kivy-2.3.1-4A4A4A)](https://kivy.org/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-D71F00?logo=sqlalchemy&logoColor=white)](https://www.sqlalchemy.org/)
[![SQLite](https://img.shields.io/badge/SQLite-local-003B57?logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![Android](https://img.shields.io/badge/Android-8.0%2B-3DDC84?logo=android&logoColor=white)](https://www.android.com/)
[![Release](https://img.shields.io/github/v/release/CONt12006/gps_running_service)](https://github.com/CONt12006/gps_running_service/releases/latest)
[![Google Play](https://img.shields.io/badge/Google_Play-Closed_Testing-orange?logo=googleplay&logoColor=white)](#)

---

## Скачать приложение

GPS Tracker сейчас проходит **закрытое тестирование в Google Play** перед публичным релизом.

Для установки тестовой версии вручную доступен APK на странице последнего GitHub Release:

[![Скачать APK](https://img.shields.io/badge/Android-Скачать_APK-3DDC84?style=for-the-badge&logo=android&logoColor=white)](https://github.com/CONt12006/gps_running_service/releases/latest)

**Текущая версия:** `v0.1.0`

### Требования

- Android 8.0 или новее;
- доступ к геолокации;
- включённая геолокация на устройстве;
- для GitHub APK — разрешение на установку приложений из сторонних источников.

---

## О проекте

**GPS Tracker** — самостоятельное Android-приложение для записи беговых тренировок и GPS-маршрутов, разработанное на Python с использованием Kivy/KivyMD.

Приложение получает координаты устройства, отображает текущее положение на карте, записывает маршрут в фоновом режиме и сохраняет историю тренировок в локальной SQLite-базе данных.

Проект построен с разделением UI, бизнес-логики, persistence и платформозависимого Android-кода. Фоновый трекинг реализован через Android `LocationManager`, foreground service и WakeLock.

Приложение находится на этапе закрытого тестирования в Google Play перед публичной публикацией.
