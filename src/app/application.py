from pathlib import Path

from kivy.app import App

from ..ui.screens.rootLayout import RootLayout

class GPSTrackerApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    def build(self):
        return RootLayout()