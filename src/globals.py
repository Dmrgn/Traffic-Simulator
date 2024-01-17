import pyray as raylib

geocode = (43.699950, -79.431111)
roads = []
lights = []
buildings = []
time = 6
paused = False
lanes = {} # maps the id of a connection to its object
camera = raylib.Camera2D()