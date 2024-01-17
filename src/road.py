import overpass
import pyray as raylib

from constants import *
from globals import geocode, roads as global_roads, camera
from road_piece import RoadPiece

class Road:
    x_min = 1e10
    y_min = 1e10
    x_max = -1e10
    y_max = -1e10
    texture = None
    texture_pos = None
    texture_size = None
    dead_end_nodes = [] # list of nodes that only have 1 connection and can be considered entraces or exits to the simulation
    def create_road_texture():
        Road.texture_pos = raylib.Vector2(Road.x_min, Road.y_min)
        Road.texture_size = raylib.Vector2(Road.x_max - Road.x_min, Road.y_max - Road.y_min)
        Road.texture = raylib.load_render_texture(int(Road.texture_size.x), int(Road.texture_size.y))

        raylib.begin_texture_mode(Road.texture)
        raylib.clear_background(raylib.Color(0, 0, 0, 0))

        for road in global_roads:
            road.draw()

        raylib.end_texture_mode()

    def __init__(self, road_type, overpass_object = None, _points = None):
        self.pieces = []
        self.is_one_way = False
        self.road_type = road_type
        self.num_lanes = ROAD_LANES[self.road_type]
        self.id = overpass_object["id"]
        self.connecting_nodes = {}
        self.is_dead_end = {"start": True, "end": True}
        # collect a list of the geometry points which make up this road
        points = []
        if overpass_object is None:
            for point in _points:
                points.append(point)
                if point.x < Road.x_min: Road.x_min = point.x
                if point.y < Road.y_min: Road.y_min = point.y
                if point.x > Road.x_max: Road.x_max = point.x
                if point.y > Road.y_max: Road.y_max = point.y
        else:
            for point in overpass_object["geometry"]:
                y_offset, x_offset = overpass.geocode_offset(geocode, (point["lat"], point["lon"]))
                pos = raylib.Vector2(x_offset*2, y_offset*2)
                points.append(pos)
                if pos.x < Road.x_min: Road.x_min = pos.x
                if pos.y < Road.y_min: Road.y_min = pos.y
                if pos.x > Road.x_max: Road.x_max = pos.x
                if pos.y > Road.y_max: Road.y_max = pos.y
        self.start_pos = raylib.Vector2(points[0].x, points[0].y)
        self.end_pos = raylib.Vector2(points[-1].x, points[-1].y)
        if "oneway" in overpass_object["tags"]:
            if overpass_object["tags"]["oneway"] == "yes":
                self.is_one_way = True
        for i in range(len(points) - 1):
            # create this road piece with starting and ending point and the specified lanes
            self.pieces.append(RoadPiece(self, points[i], points[i+1]))
            # if this is not the first piece
            # we need to add the previous piece to the road
            if len(self.pieces) > 1:
                self.pieces[-1].previous_piece = self.pieces[-2]
                self.pieces[-2].next_piece = self.pieces[-1]

    # make lanes in this road piece line up with neighbouring pieces
    def create_connections(self):
        for i in range(len(self.pieces)):
            self.pieces[i].set_adjacent_piece_lanes()
    
    # adds the passed road to this road as road pieces and removes
    # the passed road from the global roads list
    def merge_road(self, road_data):
        # road data is in the form: 
        # {"my_type":"start" or "end", "other_type":"start" or "end", "pos":Vector2, "road": Road}
        # move all road pieces from the other road to this road
        for i in range(len(road_data["road"].pieces)):
            # first change the reference to the parent road to be a reference to this road
            piece = road_data["road"].pieces.pop()
            piece.road = self
            self.pieces.append(piece)
        # change the node locations
        transformations = {
            "startstart": [road_data["road"].end_pos, self.end_pos],
            "startend": [road_data["road"].start_pos, self.end_pos],
            "endstart": [self.start_pos, road_data["road"].end_pos],
            "endend": [self.start_pos, road_data["road"].start_pos],
        }
        transformation = transformations[road_data["my_type"]+road_data["other_type"]]
        self.start_pos = transformation[0]
        self.end_pos = transformation[1]
        # remove the reference to the other road from the global roads object
        if not road_data["road"] in global_roads:
            print("not here:")
            print(road_data["road"])
        else:
            global_roads.remove(road_data["road"])

    # updates self.is_dead_end and self.connecting_nodes based on neighbouring roads
    def find_connecting_roads(self):
        self.connecting_nodes = {"start":[], "end":[]}
        my_nodes = [
            {"type":"start", "pos":self.start_pos, "road":self}, 
            {"type":"end", "pos":self.end_pos, "road":self}]
        for r in global_roads:
            if r is self: continue
            other_nodes = [
                {"my_type":None, "other_type":"start", "pos":r.start_pos, "road": r}, 
                {"my_type":None, "other_type":"end", "pos":r.end_pos, "road": r}]
            for my_node in my_nodes:
                for piece in r.pieces:
                    if (raylib.vector_2distance(my_node["pos"], piece.start_pos) < LANE_WIDTH/10 
                        or raylib.vector_2distance(my_node["pos"], piece.end_pos) < LANE_WIDTH/10 
                        or raylib.check_collision_point_line(my_node["pos"], piece.start_pos, piece.end_pos, LANE_WIDTH)):
                        self.is_dead_end[my_node["type"]] = False
                for other_node in other_nodes:
                    if raylib.vector_2distance(my_node["pos"], other_node["pos"]) < LANE_WIDTH/10:
                        self.is_dead_end[my_node["type"]] = False
                        if r.num_lanes == self.num_lanes:
                            other_node["my_type"] = my_node["type"]
                            self.connecting_nodes[my_node["type"]].append(other_node)
        for node in my_nodes:
            if self.is_dead_end[node["type"]]:
                Road.dead_end_nodes.append(node)

    # check if we can merge with any connecting roads
    def contract_connecting_roads(self):
        # make a list of roads connecting to the start and end nodes
        my_nodes = [
            {"type":"start", "pos":self.start_pos}, 
            {"type":"end", "pos":self.end_pos}]
        # recalculate connecting roads
        self.find_connecting_roads()
        for my_node in my_nodes:
            # if there is only one connected road to this node, then add that road as road pieces to this road
            if len(self.connecting_nodes[my_node["type"]]) == 1:
                self.merge_road(self.connecting_nodes[my_node["type"]][0])
    
    # not used for now
    # might be a problem calling find_connecting_roads twice because it adds duplicates to self.dead_end_nodes
    # def simplify_intersections(self):
    #     # sort road pieces based on their distance from this road's start positions
    #     # e.g index 0 of road pieces should be the road piece that is closest to the start position of this road
    #     self.pieces = sorted(self.pieces, key=lambda x: raylib.vector_2distance(raylib.vector2_scale(raylib.vector2_add(x.start_pos, x.end_pos), 1/2), self.start_pos))
    #     # recalculate connecting nodes (they could have changed since contract_connecting_roads)
    #     self.find_connecting_roads()
    #     has_merged_road_pieces = True
    #     while has_merged_road_pieces:
    #         has_merged_road_pieces = False
    #         if len(self.connecting_nodes["start"]) > 1: # in theory this should never be 1 because 2 road intersections should have been contracted in the previous step
    #             # if the first road piece is small enough so that it may be confusing when we create intersections later
    #             if self.pieces[0].length < 4*LANE_WIDTH:
    #                 if len(self.pieces) > 1: # if there is another piece to merge with, otherwise we're fucked
    #                     self.pieces[0].merge_road_piece(self.pieces[1])
    #                     has_merged_road_pieces = True
    #         if len(self.connecting_nodes["end"]) > 1:
    #             if self.pieces[-1].length < 4*LANE_WIDTH:
    #                 if len(self.pieces) > 1: # if there is another piece to merge with, otherwise we're screwed
    #                     self.pieces[-1].merge_road_piece(self.pieces[-2])
    #                     has_merged_road_pieces = True
    
    def update(self):
        for i in range(len(self.pieces)):
            self.pieces[i].update()

    def draw(self):
        for i in range(len(self.pieces)):
            self.pieces[i].draw()

    def draw_cars(self):
        for i in range(len(self.pieces)):
            self.pieces[i].draw_cars()
    
    def draw_debug(self):
        for i in range(len(self.pieces)):
            self.pieces[i].draw_debug()