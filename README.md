# gps_running_service

## Архитектура проекта

```text
gps_tracker_app/
├── main.py
├── buildozer.spec
├── requirements.txt
├── README.md
│
└── src/
    ├── app/
    │   ├── __init__.py
    │   ├── application.py
    │   ├── config.py
    │   └── constants.py
    │
    ├── assets/
    │   ├── icons/
    │   │   ├── gps.png
    │   │   ├── layers.png
    │   │   ├── start.png
    │   │   ├── stop.png
    │   │   └── settings.png
    │   │
    │   ├── fonts/
    │   │   └── Roboto-Regular.ttf
    │   │
    │   └── images/
    │       └── app_logo.png
    │
    ├── domain/
    │   ├── __init__.py
    │   ├── gps_point.py
    │   ├── workout.py
    │   └── workout_stats.py
    │
    ├── services/
    │   ├── __init__.py
    │   ├── gps_service.py
    │   ├── workout_service.py
    │   ├── distance_service.py
    │   ├── pace_service.py
    │   └── timer_service.py
    │
    ├── platform_api/
    │   ├── __init__.py
    │   ├── permissions.py
    │   ├── android_permissions.py
    │   └── ios_permissions.py
    │
    ├── storage/
    │   ├── __init__.py
    │   ├── database.py
    │   ├── workout_repository.py
    │   └── migrations.py
    │
    ├── ui/
    │   ├── __init__.py
    │   │
    │   ├── screens/
    │   │   ├── __init__.py
    │   │   ├── tracker_screen.py
    │   │   ├── history_screen.py
    │   │   ├── workout_detail_screen.py
    │   │   └── settings_screen.py
    │   │
    │   ├── widgets/
    │   │   ├── __init__.py
    │   │   ├── bottom_bar.py
    │   │   ├── circle_button.py
    │   │   ├── stats_panel.py
    │   │   ├── map_widget.py
    │   │   └── route_layer.py
    │   │
    │   └── kv/
    │       ├── tracker_screen.kv
    │       ├── history_screen.kv
    │       ├── settings_screen.kv
    │       └── widgets.kv
    │
    └── utils/
        ├── __init__.py
        ├── geo.py
        ├── time_utils.py
        └── formatters.py
```

### Основные директории

| Директория      | Назначение                                                                        |
| --------------- | --------------------------------------------------------------------------------- |
| `app/`          | Общая настройка приложения: конфиг, константы, запуск главного класса приложения. |
| `assets/`       | Статические файлы: иконки, шрифты, изображения.                                   |
| `domain/`       | Основные сущности проекта: GPS-точка, тренировка, статистика тренировки.          |
| `services/`     | Бизнес-логика: работа с GPS, расчёт дистанции, темпа, времени и тренировок.       |
| `platform_api/` | Работа с платформенными возможностями Android/iOS: разрешения, GPS-доступ.        |
| `storage/`      | Работа с базой данных, сохранение тренировок, миграции.                           |
| `ui/`           | Пользовательский интерфейс: экраны, виджеты и `.kv`-разметка Kivy.                |
| `utils/`        | Вспомогательные функции: георасчёты, форматирование времени, утилиты.             |

### Точка входа

Главная точка входа в приложение — файл `main.py`.

Он запускает основной класс приложения, который находится в `app/application.py`.

```python
from app.application import MyApp

if __name__ == "__main__":
    MyApp().run()
```
# 📝 Conventional Commits

В проекте используется соглашение **Conventional Commits**.

## Основные типы коммитов

| Тип | Назначение | Когда использовать |
|------|------------|--------------------|
| **feat** | ✨ Новая функциональность | Добавление новой возможности для пользователя (аналог **MINOR** в SemVer). |
| **fix** | 🐛 Исправление ошибки | Исправление бага (аналог **PATCH** в SemVer). |
| **docs** | 📚 Документация | Изменения только в документации (`README.md`, комментарии, Wiki и т.п.). |
| **style** | 🎨 Форматирование кода | Пробелы, отступы, переносы строк, форматирование без изменения логики программы. |
| **refactor** | ♻️ Рефакторинг | Улучшение структуры кода без исправления багов и добавления новой функциональности. |
| **perf** | ⚡ Оптимизация | Улучшение производительности приложения. |
| **test** | ✅ Тесты | Добавление или изменение тестов. |
| **build** | 📦 Сборка | Изменения системы сборки, зависимостей, Docker, Gradle, Maven, npm, pip и т.д. |
| **ci** | 🚀 CI/CD | Изменения в GitHub Actions, GitLab CI, Jenkins Pipeline и других CI/CD-конфигурациях. |
| **chore** | 🔧 Служебные изменения | Обновление конфигурации, версий библиотек, `.gitignore`, настроек проекта и других изменений, не влияющих на исходный код приложения. |
| **revert** | ⏪ Откат | Отмена (откат) предыдущего коммита. |

---

## Примеры

```text
feat: add GPS tracking service
fix: handle GPS permission denial
docs: update installation guide
style: format code with black
refactor: simplify screen initialization
perf: optimize map rendering
test: add unit tests for GPS service
build: update Kivy dependencies
ci: add GitHub Actions workflow
chore: update .gitignore
revert: revert "feat: add offline maps"
```