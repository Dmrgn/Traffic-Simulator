import pyray as raylib

import overpass
from constants import *
from globals import geocode

class Light:
    signal_length = 600
    def __init__(self, overpass_object):
        y_offset, x_offset = overpass.geocode_offset(geocode, (overpass_object["lat"], overpass_object["lon"]))
        self.pos = raylib.Vector2(x_offset*2, y_offset*2)
        self.lanes = []
        self.direction = "both"
        if "traffic_signals:direction" in overpass_object["tags"]:
            if overpass_object["tags"]["traffic_signals:direction"] == "backward":
                self.direction = "backward"
            elif overpass_object["tags"]["traffic_signals:direction"] == "forward":
                self.direction = "forward"
    def update(self):
        for i in range(len(self.lanes)):
            position = self.lanes[i]["pos"]
            lane = self.lanes[i]["lane"]
            self.lanes[i]["duration"] -= 60*raylib.get_frame_time()
            if self.lanes[i]["duration"] < 0:
                self.lanes[i]["duration"] = Light.signal_length
                if self.lanes[i]["state"] == "red":
                    self.lanes[i]["state"] = "green"
                else:
                    self.lanes[i]["state"] = "red"
    def draw(self):
        for i in range(len(self.lanes)):
            position = self.lanes[i]["pos"]
            lane = self.lanes[i]["lane"]
            pos = raylib.vector2_lerp(lane.start_pos, lane.end_pos, position)
            start_pos = raylib.vector2_add(pos, raylib.vector2_scale(lane.road_piece.normal, LANE_WIDTH/2))
            end_pos = raylib.vector2_add(pos, raylib.vector2_scale(lane.road_piece.normal, -LANE_WIDTH/2))
            raylib.draw_line_ex(start_pos, end_pos, LANE_WIDTH/3, raylib.RED if self.lanes[i]["state"] == "red" else raylib.GREEN)