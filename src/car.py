from constants import *
import pyray as raylib

class Car:
    def __init__(self, lane):
        self.lane = lane
        self.position = 0

    def draw(self):
        pos = raylib.vector2_lerp(self.lane.start_pos, self.lane.end_pos, self.position)
        raylib.draw_circle(int(pos.x), int(pos.y), LANE_WIDTH*0.8, raylib.RED)