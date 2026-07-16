[app]

title = GPSTracker
package.name = gpstracker
package.domain = org.example

source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,atlas,json,ttf

version = 0.1

requirements = python3,kivy==2.3.1,kivymd==1.2.0,git+https://github.com/kivy/plyer.git,kivy_garden.mapview==1.0.6,requests==2.34.2,pillow==12.3.0

orientation = portrait
fullscreen = 0

android.permissions = INTERNET,ACCESS_COARSE_LOCATION,ACCESS_FINE_LOCATION