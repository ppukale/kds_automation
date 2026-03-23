"""Mobile page objects — one module per tablet AUT."""

from pages.mobile.bombardier_page import BombardierPage
from pages.mobile.expo_page import ExpoPage
from pages.mobile.gunner_page import GunnerPage
from pages.mobile.pilot_page import PilotPage
from pages.mobile.wingman_page import WingmanPage

__all__ = [
    "BombardierPage",
    "ExpoPage",
    "GunnerPage",
    "PilotPage",
    "WingmanPage",
]
