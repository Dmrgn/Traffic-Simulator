import pyray as raylib

IMAGE_SIZE = 1000
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
MOUSE_ZOOM_INCREMENT = 0.125
DRAW_OVERLAY = False