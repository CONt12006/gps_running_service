from pathlib import Path

from kivymd.app import MDApp

from src.db.database import configure_database, create_tables
from src.db.run_repository import RunRepository
from src.ui.screens.rootLayout import RootLayout


class GPSTrackerApp(MDApp):
    def build(self) -> RootLayout:
        data_directory = Path(self.user_data_dir)

        data_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        database_path = (
            data_directory
            / "gpstracker.db"
        )

        configure_database(database_path)
        create_tables()

        run_repository = RunRepository()

        return RootLayout(
            run_repository=run_repository,
            data_directory=data_directory,
        )