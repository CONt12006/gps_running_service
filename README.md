<p align="center">
  <a href="README.md"><img alt="English" src="https://img.shields.io/badge/English-1f6feb?style=for-the-badge"></a>
  <a href="README.ru.md"><img alt="Русский" src="https://img.shields.io/badge/%D0%A0%D1%83%D1%81%D1%81%D0%BA%D0%B8%D0%B9-555555?style=for-the-badge"></a>
</p>

# GPS Tracker

An Android app for recording runs, background GPS tracking, drawing routes and browsing workout history.

> **Project status:** the app is in closed testing on Google Play ahead of its public release.

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Kivy](https://img.shields.io/badge/Kivy-2.3.1-4A4A4A)](https://kivy.org/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-D71F00?logo=sqlalchemy&logoColor=white)](https://www.sqlalchemy.org/)
[![SQLite](https://img.shields.io/badge/SQLite-local-003B57?logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![Android](https://img.shields.io/badge/Android-8.0%2B-3DDC84?logo=android&logoColor=white)](https://www.android.com/)
[![Release](https://img.shields.io/github/v/release/CONt12006/gps_running_service)](https://github.com/CONt12006/gps_running_service/releases/latest)
[![Google Play](https://img.shields.io/badge/Google_Play-Closed_Testing-orange?logo=googleplay&logoColor=white)](#)

---

## Download

GPS Tracker is currently in **closed testing on Google Play** ahead of its public release.

To install the test build manually, an APK is available on the latest GitHub Release page:

[![Download APK](https://img.shields.io/badge/Android-Download_APK-3DDC84?style=for-the-badge&logo=android&logoColor=white)](https://github.com/CONt12006/gps_running_service/releases/latest)

**Current version:** `v0.1.0`

### Requirements

- Android 8.0 or newer;
- location permission;
- location turned on on the device;
- for the GitHub APK: permission to install apps from unknown sources.

---

## About

**GPS Tracker** is a standalone Android app for recording running workouts and GPS routes, built in Python with Kivy/KivyMD.

The app gets the device's coordinates, shows the current position on a map, records the route in the background and stores workout history in a local SQLite database.

The project separates the UI, business logic, persistence and platform-specific Android code. Background tracking uses Android `LocationManager`, a foreground service and a WakeLock.

The app is in closed testing on Google Play ahead of its public release.
