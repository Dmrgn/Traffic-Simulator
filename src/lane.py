import random
import sys
import pyray as raylib

import car
import road
from constants import *
from globals import geocode, roads as global_roads, camera

class Lane:
    def __init__(self, road_piece, start_pos, end_pos):
        self.id = random.randint(0, sys.maxsize*2)
        self.road_piece = road_piece
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.next_lane = None # lane one to the left if it exists
        self.previous_lane = None # lane one to the right if it exists
        self.next_piece_lane = None # lane one forwards if it exists
        self.previous_piece_lane = None # lane one backwards if it exists
        self.cars = []
        # connections is a list of pairs of connecting lanes from other road pieces along with
        # the percentage of the length of this lane in which the connecting lane is located
        self.connections = set()
        self.hovered = False
    
    def update(self):
        # list of the indexes of cars to remove
        cars_to_remove = []
        for i in range(len(self.cars)):
            self.road_piece.has_been_visited = True
            self.cars[i].position += 0.3/self.road_piece.length
            if self.cars[i].position > 1:
                cars_to_remove.append(i)
                if self.next_piece_lane is not None:
                    self.next_piece_lane.cars.append(car.Car(self.next_piece_lane))
                else:
                    possible_connections = []
                    for connection in list(self.connections):
                        if abs(connection.from_position - self.cars[i].position) < LANE_WIDTH/self.road_piece.length:
                            possible_connections.append(connection)
                    if len(possible_connections) > 0:
                        connection = random.choice(possible_connections)
                        connection.to_lane.cars.append(car.Car(connection.to_lane))
                        connection.to_lane.cars[-1].position = connection.to_position
        for x in reversed(cars_to_remove):
            self.cars.pop(x)
        if raylib.check_collision_point_line(raylib.get_screen_to_world_2d(raylib.get_mouse_position(), camera), self.start_pos, self.end_pos, int(LANE_WIDTH/2)):
            self.hovered = True
            if raylib.is_mouse_button_pressed(raylib.MouseButton.MOUSE_BUTTON_LEFT):
                self.cars.append(car.Car(self))
        else:
            self.hovered = False

    # draw to road texture
    def draw(self):
        # trans_start_pos = raylib.Vector2(self.start_pos.x, IMAGE_SIZE/2 - (self.start_pos.y - IMAGE_SIZE/2))
        trans_start_pos = raylib.vector2_subtract(self.start_pos, road.Road.texture_pos)
        # trans_end_pos = raylib.Vector2(self.end_pos.x, IMAGE_SIZE/2 - (self.end_pos.y - IMAGE_SIZE/2))
        trans_end_pos = raylib.vector2_subtract(self.end_pos, road.Road.texture_pos)

        raylib.draw_line_ex(trans_start_pos, trans_end_pos, LANE_WIDTH*1.2, raylib.GRAY)
        raylib.draw_line_ex(trans_start_pos, trans_end_pos, LANE_WIDTH*0.8, raylib.DARKGRAY)
    
    # draw cars to screen
    def draw_cars(self):
        for i in range(len(self.cars)):
            self.cars[i].draw()

    # draw debug to screen
    def draw_debug(self):
        if self.hovered:    
            # for p in self.road_piece.road.pieces:
            #     for l in p.lanes:
            #         raylib.draw_line_ex(l.start_pos, l.end_pos, LANE_WIDTH*2, raylib.PINK)
            raylib.draw_line_ex(self.start_pos, self.end_pos, LANE_WIDTH*1.2, raylib.RED)
            raylib.draw_line_ex(self.start_pos, self.end_pos, LANE_WIDTH*0.8, raylib.BROWN)
            # if self.next_piece_lane is not None:
            #     raylib.draw_line_ex(self.next_piece_lane.start_pos, self.next_piece_lane.end_pos, LANE_WIDTH*2.5, raylib.GREEN)
            # if self.previous_piece_lane is not None:
            #     raylib.draw_line_ex(self.previous_piece_lane.start_pos, self.previous_piece_lane.end_pos, LANE_WIDTH*2, raylib.RED)
            raylib.draw_circle(int(self.road_piece.start_pos.x), int(self.road_piece.start_pos.y), 20, raylib.PURPLE)
            raylib.draw_circle(int(self.road_piece.end_pos.x), int(self.road_piece.end_pos.y), 20, raylib.ORANGE)
            # raylib.draw_circle(int(self.start_pos.x), int(self.start_pos.y), 10, raylib.BLUE)
            # raylib.draw_circle(int(self.end_pos.x), int(self.end_pos.y), 10, raylib.RED)
            raylib.draw_circle(int(self.road_piece.road.start_pos.x), int(self.road_piece.road.start_pos.y), 10, raylib.BLUE)
            raylib.draw_circle(int(self.road_piece.road.end_pos.x), int(self.road_piece.road.end_pos.y), 10, raylib.RED)
            # for connection in self.connections:
            #     raylib.draw_line_ex(connection.to_lane.start_pos, connection.to_lane.end_pos, LANE_WIDTH*2, raylib.BLUE)
            # for p in self.road_piece.road.pieces:
            #     raylib.draw_line_ex(p.start_pos, p.end_pos, LANE_WIDTH*self.road_piece.num_lanes*2, raylib.BLUE)

            pos = raylib.get_screen_to_world_2d(raylib.Vector2(10, 10), camera)
            raylib.draw_text(str(id(self.road_piece)), int(pos.x), int(pos.y), 15, raylib.BLACK)
            pos = raylib.get_screen_to_world_2d(raylib.Vector2(10, 750), camera)
            raylib.draw_text("Road Piece Index: "+str(self.road_piece.road.pieces.index(self.road_piece)), int(pos.x), int(pos.y), 15, raylib.BLACK)
            for i in range(len(self.connections)):
                pos = raylib.get_screen_to_world_2d(raylib.Vector2(10, 50 + 30*i), camera)
                raylib.draw_text(str(list(self.connections)[i].to_position), int(pos.x), int(pos.y), 15, raylib.BLACK)
                pos = raylib.get_screen_to_world_2d(raylib.Vector2(50, 50 + 30*i), camera)
                raylib.draw_text(":"+str(id(list(self.connections)[i].to_lane.road_piece)), int(pos.x), int(pos.y), 15, raylib.BLACK)

    
class Connection:
    # pair containing a lane and a corresponding position on that lane
    def __init__(self, from_lane, to_lane, from_position, to_position):
        self.from_lane = from_lane
        self.to_lane = to_lane
        self.from_position = from_position
        self.to_position = to_position
    # functions which allow us to use lanes in a set data structure
    def __eq__(self, __value):
        return __value.__hash__() == self.__hash__()
    def __hash__(self):
        return hash(str(self.from_lane.id)+str(self.to_lane.id)+str(self.from_position)+str(self.to_position))