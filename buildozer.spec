[app]

title = GPSTracker
package.name = gpstracker
package.domain = org.example

source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,atlas,json,ttf

version = 0.1

requirements = python3,kivy==2.3.1,kivymd==1.2.0,plyer==2.1.0,kivy_garden.mapview==1.0.6,requests==2.34.2,openssl,pillow==12.3.0,sqlalchemy==2.0.51
orientation = portrait
fullscreen = 0

android.permissions = INTERNET,ACCESS_COARSE_LOCATION,ACCESS_FINE_LOCATION