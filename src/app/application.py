from pathlib import Path

from kivymd.app import MDApp
from ..ui.screens.rootLayout import RootLayout

class GPSTrackerApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    def build(self):
        return RootLayout()