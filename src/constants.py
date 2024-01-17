import pyray as raylib

SCREEN_WIDTH = raylib.get_screen_width()
SCREEN_HEIGHT = raylib.get_screen_height()
IMAGE_ZOOM = 1
LANE_WIDTH = 5
ROAD_COLOURS = {
    "primary": (1.0, 0, 0, 1.0),
    "secondary": (0, 1.0, 0, 1.0),
    "tertiary": (0, 0, 1.0, 1.0),
}
ROAD_LANES = {
    "primary": 4,
    "secondary": 2,
    "tertiary": 2,
}
ROAD_SPAWN_RATES = {
    "primary": 2,
    "secondary": 4,
    "tertiary": 8,
}
ROAD_SPEED_LIMITS = {
    "primary": 2,
    "secondary": 1.4,
    "tertiary": 1,
}
MOUSE_ZOOM_INCREMENT = 0.125