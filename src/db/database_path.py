from pathlib import Path

from kivy.utils import platform


def get_database_path() -> Path:
    if platform == "android":
        from android.storage import app_storage_path

        storage_directory = Path(app_storage_path())
    else:
        storage_directory = (
            Path(__file__).resolve().parents[2]
            / "data"
        )

    storage_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    return storage_directory / "gpstracker.db"