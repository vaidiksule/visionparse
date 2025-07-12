# from django.apps import AppConfig
from tailwind.apps import TailwindConfig

class ThemeConfig(TailwindConfig):
    name = 'theme'
    verbose_name = "Theme"

