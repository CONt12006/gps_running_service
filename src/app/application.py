from kivymd.app import MDApp

from src.db.database import create_tables
from src.db.run_repository import RunRepository
from src.ui.screens.rootLayout import RootLayout


class GPSTrackerApp(MDApp):
    def build(self) -> RootLayout:
        create_tables()

        run_repository = RunRepository()

        return RootLayout(
            run_repository=run_repository,
        )