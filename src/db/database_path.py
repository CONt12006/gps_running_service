from pathlib import Path

from kivy.app import App


def get_database_path() -> Path:
    app = App.get_running_app()

    if app is None:
        raise RuntimeError(
            "Приложение ещё не запущено: "
            "невозможно определить путь к базе"
        )

    data_directory = Path(app.user_data_dir)

    data_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    return data_directory / "gpstracker.db"